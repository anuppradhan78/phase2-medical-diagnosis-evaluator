"""Tests for LLM-as-Judge evaluator."""

import pytest
from unittest.mock import Mock, patch

from src.judge_evaluator import (
    JudgeEvaluator,
    create_judge_evaluator,
    SAFETY_JUDGE_PROMPT,
    CLINICAL_QUALITY_JUDGE_PROMPT
)


class TestJudgeEvaluator:
    """Tests for JudgeEvaluator class."""
    
    @patch('anthropic.Anthropic')
    def test_initialization_anthropic(self, mock_anthropic):
        """Test initializing with Anthropic."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            evaluator = JudgeEvaluator(
                judge_model="claude-3-5-sonnet-20241022",
                judge_provider="anthropic"
            )
            assert evaluator.judge_provider == "anthropic"
    
    @patch('openai.OpenAI')
    def test_initialization_openai(self, mock_openai):
        """Test initializing with OpenAI."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            evaluator = JudgeEvaluator(
                judge_model="gpt-4o",
                judge_provider="openai"
            )
            assert evaluator.judge_provider == "openai"
    
    def test_initialization_missing_api_key(self):
        """Test that missing API key raises error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                JudgeEvaluator(judge_provider="anthropic")
    
    @patch('anthropic.Anthropic')
    def test_judge_safety_success(self, mock_anthropic_class):
        """Test successful safety evaluation."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''{
            "safety_score": 4,
            "reasoning": "Good safety considerations",
            "concerns": ["Minor concern"],
            "strengths": ["Appropriate urgency"]
        }'''
        mock_client.messages.create.return_value = mock_response
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            evaluator = JudgeEvaluator(judge_provider="anthropic")
            evaluator.client = mock_client
            
            case = {
                "patient_presentation": "Chest pain",
                "relevant_history": "HTN",
                "lab_results": {"troponin": "2.5"}
            }
            
            diagnosis = {
                "primary_diagnosis": "STEMI",
                "reasoning": "Elevated troponin"
            }
            
            result = evaluator.judge_safety(case, diagnosis)
            
            assert result["safety_score"] == 4
            assert "reasoning" in result
            assert "concerns" in result
    
    @patch('anthropic.Anthropic')
    def test_judge_quality_success(self, mock_anthropic_class):
        """Test successful quality evaluation."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''{
            "quality_score": 5,
            "reasoning": "Excellent diagnosis",
            "diagnostic_accuracy": "Correct",
            "reasoning_quality": "Sound",
            "suggestions": []
        }'''
        mock_client.messages.create.return_value = mock_response
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            evaluator = JudgeEvaluator(judge_provider="anthropic")
            evaluator.client = mock_client
            
            case = {
                "patient_presentation": "Chest pain",
                "relevant_history": "HTN",
                "lab_results": {"troponin": "2.5"},
                "expert_diagnosis": "STEMI",
                "expert_reasoning": "Classic presentation"
            }
            
            diagnosis = {
                "primary_diagnosis": "STEMI",
                "reasoning": "Elevated troponin with chest pain"
            }
            
            result = evaluator.judge_quality(case, diagnosis)
            
            assert result["quality_score"] == 5
            assert "diagnostic_accuracy" in result
    
    @patch('anthropic.Anthropic')
    def test_judge_safety_invalid_score(self, mock_anthropic_class):
        """Test handling of invalid safety score."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock response with invalid score
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"safety_score": 10}'  # Invalid
        mock_client.messages.create.return_value = mock_response
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            evaluator = JudgeEvaluator(judge_provider="anthropic")
            evaluator.client = mock_client
            
            case = {"patient_presentation": "Test"}
            diagnosis = {"primary_diagnosis": "Test"}
            
            with patch('time.sleep'):  # Mock sleep
                result = evaluator.judge_safety(case, diagnosis, max_retries=1)
            
            # Should return default score on failure
            assert result["safety_score"] == 3
            assert "error" in result
    
    def test_parse_judge_response_json(self):
        """Test parsing JSON response."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('anthropic.Anthropic'):
                evaluator = JudgeEvaluator(judge_provider="anthropic")
                
                response = '{"safety_score": 4, "reasoning": "Good"}'
                result = evaluator._parse_judge_response(response)
                
                assert result["safety_score"] == 4
                assert result["reasoning"] == "Good"
    
    def test_parse_judge_response_markdown(self):
        """Test parsing JSON from markdown code block."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('anthropic.Anthropic'):
                evaluator = JudgeEvaluator(judge_provider="anthropic")
                
                response = '```json\n{"safety_score": 5}\n```'
                result = evaluator._parse_judge_response(response)
                
                assert result["safety_score"] == 5
    
    def test_format_lab_results(self):
        """Test formatting lab results."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('anthropic.Anthropic'):
                evaluator = JudgeEvaluator(judge_provider="anthropic")
                
                labs = {"troponin": "2.5", "ECG": "ST elevation"}
                formatted = evaluator._format_lab_results(labs)
                
                assert "troponin" in formatted
                assert "2.5" in formatted


class TestFactoryFunction:
    """Tests for factory function."""
    
    @patch('anthropic.Anthropic')
    def test_create_judge_evaluator(self, mock_anthropic):
        """Test factory function creates evaluator."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            evaluator = create_judge_evaluator()
            assert isinstance(evaluator, JudgeEvaluator)


class TestPromptTemplates:
    """Tests for prompt templates."""
    
    def test_safety_prompt_exists(self):
        """Test that safety prompt template exists."""
        assert SAFETY_JUDGE_PROMPT is not None
        assert "safety" in SAFETY_JUDGE_PROMPT.lower()
    
    def test_quality_prompt_exists(self):
        """Test that quality prompt template exists."""
        assert CLINICAL_QUALITY_JUDGE_PROMPT is not None
        assert "quality" in CLINICAL_QUALITY_JUDGE_PROMPT.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
