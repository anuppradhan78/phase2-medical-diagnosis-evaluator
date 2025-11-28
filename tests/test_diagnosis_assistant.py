"""Tests for Diagnosis Assistant."""

import pytest
from unittest.mock import Mock, patch

from src.diagnosis_assistant import (
    DiagnosisResponse,
    DiagnosisAssistant,
    create_diagnosis_assistant
)
from src.config import ModelConfig


class TestDiagnosisResponse:
    """Tests for DiagnosisResponse model."""
    
    def test_valid_diagnosis_response(self):
        """Test creating a valid DiagnosisResponse."""
        response = DiagnosisResponse(
            primary_diagnosis="Acute Myocardial Infarction",
            differential_diagnoses=["STEMI", "Unstable Angina", "Pericarditis"],
            reasoning="Patient presents with chest pain and elevated troponin",
            confidence=0.85
        )
        
        assert response.primary_diagnosis == "Acute Myocardial Infarction"
        assert len(response.differential_diagnoses) == 3
        assert response.confidence == 0.85
    
    def test_confidence_validation(self):
        """Test confidence must be between 0 and 1."""
        # Valid confidence
        DiagnosisResponse(
            primary_diagnosis="Test",
            reasoning="Test",
            confidence=0.5
        )
        
        # Invalid confidence
        with pytest.raises(ValueError):
            DiagnosisResponse(
                primary_diagnosis="Test",
                reasoning="Test",
                confidence=1.5
            )


class TestDiagnosisAssistant:
    """Tests for DiagnosisAssistant."""
    
    def test_initialization_openai(self):
        """Test initializing with OpenAI provider."""
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o"
        )
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            assistant = DiagnosisAssistant(config)
            assert assistant.provider == "openai"
            assert assistant.model_name == "gpt-4o"
    
    def test_initialization_missing_api_key(self):
        """Test that missing API key raises error."""
        config = ModelConfig(
            provider="openai",
            model_name="gpt-4o"
        )
        
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                DiagnosisAssistant(config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
