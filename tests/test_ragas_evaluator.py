"""Tests for Ragas evaluator."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ragas_evaluator import (
    RagasEvaluator,
    create_ragas_evaluator,
    format_diagnosis_for_ragas
)


class TestRagasEvaluator:
    """Tests for RagasEvaluator class."""
    
    def test_initialization(self):
        """Test initializing evaluator."""
        evaluator = RagasEvaluator()
        assert evaluator is not None
    
    @patch('src.ragas_evaluator.evaluate')
    @patch('src.ragas_evaluator.Dataset')
    def test_evaluate_with_ragas_success(self, mock_dataset, mock_evaluate):
        """Test successful Ragas evaluation."""
        # Mock dataset creation
        mock_dataset_instance = Mock()
        mock_dataset.from_dict.return_value = mock_dataset_instance
        
        # Mock evaluation results
        mock_evaluate.return_value = {
            "faithfulness": 0.85,
            "answer_relevancy": 0.90,
            "context_precision": 0.88,
            "context_recall": 0.82
        }
        
        evaluator = RagasEvaluator()
        
        results = evaluator.evaluate_with_ragas(
            questions=["Patient with chest pain"],
            answers=["Diagnosis: STEMI"],
            contexts=[["History: HTN", "Labs: Troponin 2.5"]],
            ground_truths=["STEMI"]
        )
        
        assert results["faithfulness"] == 0.85
        assert results["answer_relevancy"] == 0.90
        assert results["context_precision"] == 0.88
        assert results["context_recall"] == 0.82
    
    def test_evaluate_with_ragas_mismatched_lengths(self):
        """Test that mismatched input lengths returns error."""
        evaluator = RagasEvaluator()
        
        results = evaluator.evaluate_with_ragas(
            questions=["Q1", "Q2"],
            answers=["A1"],  # Wrong length
            contexts=[["C1"], ["C2"]],
            ground_truths=["GT1", "GT2"]
        )
        
        # Should return error in results
        assert "error" in results
        assert results["faithfulness"] == 0.0
    
    @patch('src.ragas_evaluator.evaluate')
    @patch('src.ragas_evaluator.Dataset')
    def test_evaluate_with_ragas_handles_empty_contexts(self, mock_dataset, mock_evaluate):
        """Test handling of empty contexts."""
        mock_dataset_instance = Mock()
        mock_dataset.from_dict.return_value = mock_dataset_instance
        
        # Create mock metric with name attribute
        mock_metric = Mock()
        mock_metric.name = "faithfulness"
        
        mock_evaluate.return_value = {
            "faithfulness": 0.5
        }
        
        evaluator = RagasEvaluator()
        
        results = evaluator.evaluate_with_ragas(
            questions=["Question"],
            answers=["Answer"],
            contexts=[[]],  # Empty context
            ground_truths=["Truth"],
            metrics=[mock_metric]
        )
        
        # Should handle empty context gracefully
        assert "faithfulness" in results
        assert results["faithfulness"] == 0.5
    
    @patch('src.ragas_evaluator.evaluate')
    @patch('src.ragas_evaluator.Dataset')
    def test_evaluate_with_ragas_error_handling(self, mock_dataset, mock_evaluate):
        """Test error handling in evaluation."""
        mock_dataset.from_dict.side_effect = Exception("Ragas error")
        
        evaluator = RagasEvaluator()
        
        results = evaluator.evaluate_with_ragas(
            questions=["Question"],
            answers=["Answer"],
            contexts=[["Context"]],
            ground_truths=["Truth"]
        )
        
        # Should return default scores on error
        assert "error" in results
        assert results["faithfulness"] == 0.0
        assert results["answer_relevancy"] == 0.0
    
    @patch('src.ragas_evaluator.evaluate')
    @patch('src.ragas_evaluator.Dataset')
    def test_compute_faithfulness(self, mock_dataset, mock_evaluate):
        """Test computing faithfulness score."""
        mock_dataset_instance = Mock()
        mock_dataset.from_dict.return_value = mock_dataset_instance
        
        mock_evaluate.return_value = {
            "faithfulness": 0.92
        }
        
        evaluator = RagasEvaluator()
        
        score = evaluator.compute_faithfulness(
            answers=["Diagnosis: STEMI"],
            contexts=[["History: HTN"]]
        )
        
        assert score == 0.92
    
    @patch('src.ragas_evaluator.evaluate')
    @patch('src.ragas_evaluator.Dataset')
    def test_compute_answer_relevancy(self, mock_dataset, mock_evaluate):
        """Test computing answer relevancy score."""
        mock_dataset_instance = Mock()
        mock_dataset.from_dict.return_value = mock_dataset_instance
        
        mock_evaluate.return_value = {
            "answer_relevancy": 0.88
        }
        
        evaluator = RagasEvaluator()
        
        score = evaluator.compute_answer_relevancy(
            questions=["Patient with chest pain"],
            answers=["Diagnosis: STEMI"]
        )
        
        assert score == 0.88
    
    @patch('src.ragas_evaluator.evaluate')
    @patch('src.ragas_evaluator.Dataset')
    def test_compute_context_metrics(self, mock_dataset, mock_evaluate):
        """Test computing context precision and recall."""
        mock_dataset_instance = Mock()
        mock_dataset.from_dict.return_value = mock_dataset_instance
        
        mock_evaluate.return_value = {
            "context_precision": 0.85,
            "context_recall": 0.80
        }
        
        evaluator = RagasEvaluator()
        
        results = evaluator.compute_context_metrics(
            questions=["Patient with chest pain"],
            contexts=[["History: HTN", "Labs: Troponin 2.5"]],
            ground_truths=["STEMI"]
        )
        
        assert results["context_precision"] == 0.85
        assert results["context_recall"] == 0.80


class TestFactoryFunction:
    """Tests for factory function."""
    
    def test_create_ragas_evaluator(self):
        """Test factory function creates evaluator."""
        evaluator = create_ragas_evaluator()
        assert isinstance(evaluator, RagasEvaluator)


class TestFormatDiagnosisForRagas:
    """Tests for format_diagnosis_for_ragas function."""
    
    def test_format_diagnosis_complete_case(self):
        """Test formatting a complete diagnosis case."""
        case = {
            "patient_presentation": "58-year-old male with chest pain",
            "relevant_history": "HTN, DM, smoking",
            "lab_results": {
                "troponin": "2.5 ng/mL",
                "ECG": "ST elevation"
            },
            "expert_diagnosis": "STEMI",
            "expert_reasoning": "Elevated troponin with ST elevation"
        }
        
        diagnosis_response = {
            "primary_diagnosis": "Acute MI",
            "reasoning": "Patient presents with typical chest pain and elevated cardiac markers"
        }
        
        formatted = format_diagnosis_for_ragas(case, diagnosis_response)
        
        assert formatted["question"] == "58-year-old male with chest pain"
        assert "Acute MI" in formatted["answer"]
        assert len(formatted["contexts"]) == 2  # History and labs
        assert "STEMI" in formatted["ground_truth"]
    
    def test_format_diagnosis_missing_fields(self):
        """Test formatting with missing fields."""
        case = {
            "patient_presentation": "Chest pain"
        }
        
        diagnosis_response = {
            "primary_diagnosis": "Unknown"
        }
        
        formatted = format_diagnosis_for_ragas(case, diagnosis_response)
        
        assert formatted["question"] == "Chest pain"
        assert "Unknown" in formatted["answer"]
        assert len(formatted["contexts"]) == 0  # No history or labs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
