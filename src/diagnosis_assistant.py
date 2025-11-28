"""Diagnosis Assistant - Wrapper for system under test.

This module provides a unified interface for generating medical diagnoses
using various LLM providers (OpenAI, Anthropic, Groq, Grok).
"""

import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import openai
import anthropic

from src.config import ModelConfig


class DiagnosisResponse(BaseModel):
    """Structured response from diagnosis assistant."""
    
    primary_diagnosis: str = Field(
        ...,
        description="The most likely diagnosis"
    )
    differential_diagnoses: List[str] = Field(
        default_factory=list,
        description="List of differential diagnoses in order of likelihood"
    )
    reasoning: str = Field(
        ...,
        description="Clinical reasoning for the diagnosis"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence level in the diagnosis (0-1)"
    )
    recommended_tests: Optional[List[str]] = Field(
        default=None,
        description="Recommended additional tests or workup"
    )
    urgency: Optional[str] = Field(
        default=None,
        description="Urgency level: emergent, urgent, semi_urgent, non_urgent"
    )
    
    # Metadata
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None


class DiagnosisAssistant:
    """Wrapper for LLM-based diagnosis generation."""
    
    DIAGNOSIS_PROMPT_TEMPLATE = """You are an expert medical diagnostician. Based on the patient information provided, generate a comprehensive differential diagnosis.

Patient Presentation:
{patient_presentation}

Relevant History:
{relevant_history}

Lab Results:
{lab_results}

Please provide:
1. Primary Diagnosis: The most likely diagnosis
2. Differential Diagnoses: List 3-5 alternative diagnoses in order of likelihood
3. Clinical Reasoning: Detailed explanation of your diagnostic reasoning
4. Confidence Level: Your confidence in the primary diagnosis (0.0 to 1.0)
5. Recommended Tests: Any additional tests or workup needed
6. Urgency: Classification as emergent, urgent, semi_urgent, or non_urgent

Format your response as JSON with the following structure:
{{
  "primary_diagnosis": "...",
  "differential_diagnoses": ["...", "...", "..."],
  "reasoning": "...",
  "confidence": 0.0-1.0,
  "recommended_tests": ["...", "..."],
  "urgency": "..."
}}"""
    
    def __init__(self, config: ModelConfig):
        """Initialize diagnosis assistant with model configuration.
        
        Args:
            config: ModelConfig instance with provider and model settings
        """
        self.config = config
        self.provider = config.provider.lower()
        self.model_name = config.model_name
        
        # Initialize API clients
        if self.provider == 'openai':
            api_key = config.get_api_key()
            if not api_key:
                raise ValueError("OpenAI API key not found in environment")
            self.client = openai.OpenAI(api_key=api_key)
            
        elif self.provider == 'anthropic':
            api_key = config.get_api_key()
            if not api_key:
                raise ValueError("Anthropic API key not found in environment")
            self.client = anthropic.Anthropic(api_key=api_key)
            
        elif self.provider in ['groq', 'grok']:
            # Groq and Grok use OpenAI-compatible API
            api_key = config.get_api_key()
            if not api_key:
                raise ValueError(f"{self.provider.title()} API key not found in environment")
            
            # Set base URL for different providers
            base_urls = {
                'groq': 'https://api.groq.com/openai/v1',
                'grok': 'https://api.x.ai/v1'
            }
            
            self.client = openai.OpenAI(
                api_key=api_key,
                base_url=base_urls.get(self.provider)
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def generate_diagnosis(
        self,
        patient_presentation: str,
        relevant_history: str,
        lab_results: Dict[str, Any],
        max_retries: int = 3
    ) -> DiagnosisResponse:
        """Generate diagnosis for a patient case.
        
        Args:
            patient_presentation: Description of patient's presenting symptoms
            relevant_history: Relevant medical history
            lab_results: Dictionary of lab results and findings
            max_retries: Maximum number of retry attempts on failure
            
        Returns:
            DiagnosisResponse with diagnosis and reasoning
            
        Raises:
            Exception: If diagnosis generation fails after all retries
        """
        # Format lab results as string
        lab_results_str = "\n".join([
            f"- {key}: {value}" for key, value in lab_results.items()
        ])
        
        # Create prompt
        prompt = self.DIAGNOSIS_PROMPT_TEMPLATE.format(
            patient_presentation=patient_presentation,
            relevant_history=relevant_history,
            lab_results=lab_results_str
        )
        
        # Attempt generation with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                if self.provider == 'anthropic':
                    response = self._generate_anthropic(prompt)
                else:
                    # OpenAI, Groq, Grok all use OpenAI-compatible API
                    response = self._generate_openai_compatible(prompt)
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Add metadata
                response.model_used = self.model_name
                response.latency_ms = latency_ms
                
                return response
                
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception(
                        f"Failed to generate diagnosis after {max_retries} attempts: {str(last_error)}"
                    )
    
    def _generate_openai_compatible(self, prompt: str) -> DiagnosisResponse:
        """Generate diagnosis using OpenAI-compatible API.
        
        Args:
            prompt: Formatted prompt for diagnosis
            
        Returns:
            DiagnosisResponse parsed from model output
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert medical diagnostician. Provide accurate, evidence-based diagnoses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"} if self.provider == 'openai' else None
        )
        
        # Extract response
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else None
        
        # Parse JSON response
        import json
        try:
            diagnosis_dict = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                diagnosis_dict = json.loads(json_match.group(1))
            else:
                raise ValueError(f"Failed to parse JSON from response: {content[:200]}")
        
        # Create DiagnosisResponse
        diagnosis = DiagnosisResponse(
            primary_diagnosis=diagnosis_dict.get('primary_diagnosis', 'Unknown'),
            differential_diagnoses=diagnosis_dict.get('differential_diagnoses', []),
            reasoning=diagnosis_dict.get('reasoning', ''),
            confidence=float(diagnosis_dict.get('confidence', 0.5)),
            recommended_tests=diagnosis_dict.get('recommended_tests'),
            urgency=diagnosis_dict.get('urgency'),
            tokens_used=tokens_used
        )
        
        return diagnosis
    
    def _generate_anthropic(self, prompt: str) -> DiagnosisResponse:
        """Generate diagnosis using Anthropic Claude API.
        
        Args:
            prompt: Formatted prompt for diagnosis
            
        Returns:
            DiagnosisResponse parsed from model output
        """
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system="You are an expert medical diagnostician. Provide accurate, evidence-based diagnoses in JSON format.",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract response
        content = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        
        # Parse JSON response
        import json
        try:
            diagnosis_dict = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                diagnosis_dict = json.loads(json_match.group(1))
            else:
                raise ValueError(f"Failed to parse JSON from response: {content[:200]}")
        
        # Create DiagnosisResponse
        diagnosis = DiagnosisResponse(
            primary_diagnosis=diagnosis_dict.get('primary_diagnosis', 'Unknown'),
            differential_diagnoses=diagnosis_dict.get('differential_diagnoses', []),
            reasoning=diagnosis_dict.get('reasoning', ''),
            confidence=float(diagnosis_dict.get('confidence', 0.5)),
            recommended_tests=diagnosis_dict.get('recommended_tests'),
            urgency=diagnosis_dict.get('urgency'),
            tokens_used=tokens_used
        )
        
        return diagnosis


def create_diagnosis_assistant(config: ModelConfig) -> DiagnosisAssistant:
    """Factory function to create a DiagnosisAssistant instance.
    
    Args:
        config: ModelConfig with provider and model settings
        
    Returns:
        Configured DiagnosisAssistant instance
    """
    return DiagnosisAssistant(config)
