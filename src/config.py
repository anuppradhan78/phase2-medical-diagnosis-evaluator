"""Configuration management for Medical Diagnosis Evaluator.

This module provides YAML-based configuration with Pydantic validation
and environment variable overrides.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

import yaml
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv


class ModelConfig(BaseModel):
    """Configuration for the LLM model being evaluated."""
    
    provider: str = Field(
        ...,
        description="LLM provider (openai, anthropic, groq, grok, fireworks)"
    )
    model_name: str = Field(
        ...,
        description="Specific model name (e.g., gpt-4o, claude-3-5-sonnet-20241022)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=2000,
        gt=0,
        description="Maximum tokens in response"
    )
    api_key_env: Optional[str] = Field(
        default=None,
        description="Environment variable name for API key"
    )
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is supported."""
        valid_providers = {'openai', 'anthropic', 'groq', 'grok', 'fireworks'}
        if v.lower() not in valid_providers:
            raise ValueError(
                f"Provider must be one of {valid_providers}, got '{v}'"
            )
        return v.lower()
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variable."""
        if self.api_key_env:
            return os.getenv(self.api_key_env)
        
        # Default environment variable names
        default_keys = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'groq': 'GROQ_API_KEY',
            'grok': 'GROK_API_KEY',
            'fireworks': 'FIREWORKS_API_KEY'
        }
        
        env_var = default_keys.get(self.provider)
        if env_var:
            return os.getenv(env_var)
        
        return None


class EvalConfig(BaseModel):
    """Configuration for evaluation run."""
    
    # Model configuration
    model: ModelConfig = Field(
        ...,
        description="Configuration for the model being evaluated"
    )
    
    # Judge model configuration
    judge_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Model to use as judge for safety/quality evaluation"
    )
    judge_provider: str = Field(
        default="anthropic",
        description="Provider for judge model"
    )
    
    # Dataset configuration
    golden_dataset_path: str = Field(
        default="data/golden_dataset.json",
        description="Path to golden dataset JSON file"
    )
    
    # Output configuration
    output_dir: str = Field(
        default="./eval_results",
        description="Directory for evaluation outputs"
    )
    
    # LangSmith configuration
    langsmith_project: str = Field(
        default="medical-diagnosis-eval",
        description="LangSmith project name"
    )
    langsmith_api_key_env: str = Field(
        default="LANGSMITH_API_KEY",
        description="Environment variable for LangSmith API key"
    )
    
    # Metric thresholds
    min_accuracy: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum required clinical accuracy"
    )
    min_faithfulness: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Minimum required faithfulness score"
    )
    min_safety_score: float = Field(
        default=4.0,
        ge=1.0,
        le=5.0,
        description="Minimum required safety score (1-5)"
    )
    max_cost_per_query: float = Field(
        default=0.10,
        gt=0.0,
        description="Maximum allowed cost per query in USD"
    )
    max_p95_latency: float = Field(
        default=3000.0,
        gt=0.0,
        description="Maximum allowed p95 latency in milliseconds"
    )
    
    # Evaluation options
    subset_size: Optional[int] = Field(
        default=None,
        description="Number of cases to evaluate (None = all)"
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose logging"
    )
    
    @field_validator('golden_dataset_path', 'output_dir')
    @classmethod
    def validate_paths(cls, v: str) -> str:
        """Ensure paths are properly formatted."""
        return str(Path(v))
    
    def get_langsmith_api_key(self) -> Optional[str]:
        """Get LangSmith API key from environment."""
        return os.getenv(self.langsmith_api_key_env)


def load_config_from_yaml(yaml_path: str) -> EvalConfig:
    """Load configuration from YAML file with environment variable overrides.
    
    Args:
        yaml_path: Path to YAML configuration file
        
    Returns:
        EvalConfig instance with loaded configuration
        
    Raises:
        FileNotFoundError: If YAML file doesn't exist
        ValueError: If YAML is invalid or required fields are missing
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Load YAML file
    yaml_file = Path(yaml_path)
    if not yaml_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
    
    with open(yaml_file, 'r') as f:
        config_dict = yaml.safe_load(f)
    
    if not config_dict:
        raise ValueError(f"Empty or invalid YAML file: {yaml_path}")
    
    # Apply environment variable overrides
    config_dict = _apply_env_overrides(config_dict)
    
    # Create and validate config
    try:
        config = EvalConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")
    
    return config


def _apply_env_overrides(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration.
    
    Environment variables follow the pattern:
    - EVAL_<SECTION>_<KEY> for top-level keys
    - EVAL_MODEL_<KEY> for model keys
    
    Args:
        config_dict: Configuration dictionary from YAML
        
    Returns:
        Updated configuration dictionary
    """
    # Override model fields
    if 'model' in config_dict:
        model_overrides = {
            'provider': os.getenv('EVAL_MODEL_PROVIDER'),
            'model_name': os.getenv('EVAL_MODEL_NAME'),
            'temperature': os.getenv('EVAL_MODEL_TEMPERATURE'),
            'max_tokens': os.getenv('EVAL_MODEL_MAX_TOKENS'),
        }
        
        for key, value in model_overrides.items():
            if value is not None:
                # Convert types as needed
                if key == 'temperature':
                    value = float(value)
                elif key == 'max_tokens':
                    value = int(value)
                config_dict['model'][key] = value
    
    # Override top-level fields
    top_level_overrides = {
        'judge_model': os.getenv('EVAL_JUDGE_MODEL'),
        'golden_dataset_path': os.getenv('EVAL_DATASET_PATH'),
        'output_dir': os.getenv('EVAL_OUTPUT_DIR'),
        'langsmith_project': os.getenv('LANGSMITH_PROJECT'),
        'min_accuracy': os.getenv('MIN_ACCURACY'),
        'min_faithfulness': os.getenv('MIN_FAITHFULNESS'),
        'min_safety_score': os.getenv('MIN_SAFETY_SCORE'),
        'max_cost_per_query': os.getenv('MAX_COST_PER_QUERY'),
        'max_p95_latency': os.getenv('MAX_P95_LATENCY'),
        'verbose': os.getenv('EVAL_VERBOSE'),
    }
    
    for key, value in top_level_overrides.items():
        if value is not None:
            # Convert types as needed
            if key in ['min_accuracy', 'min_faithfulness', 'min_safety_score', 
                      'max_cost_per_query', 'max_p95_latency']:
                value = float(value)
            elif key == 'verbose':
                value = value.lower() in ('true', '1', 'yes')
            config_dict[key] = value
    
    return config_dict


def save_config_to_yaml(config: EvalConfig, yaml_path: str) -> None:
    """Save configuration to YAML file.
    
    Args:
        config: EvalConfig instance to save
        yaml_path: Path where YAML file should be saved
    """
    yaml_file = Path(yaml_path)
    yaml_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict
    config_dict = config.model_dump()
    
    # Write to YAML
    with open(yaml_file, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
