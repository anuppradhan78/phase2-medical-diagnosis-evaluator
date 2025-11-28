"""Verification tests for Task 10: Metrics Aggregation.

This test file verifies that all Task 10 acceptance criteria are met:
1. All metrics aggregated correctly
2. Metrics match expected format
3. Thresholds checked
4. Summary dict complete
"""

import pytest
from unittest.mock import Mock, patch

from src.evaluator import Evaluator
from src.config import EvalConfig, ModelConfig


@pytest.fixture
def mock_config():
    """Create a mock evaluation configuration."""
    return EvalConfig(
        model=ModelConfig(
            provider="openai",
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        ),
        judge_model="claude-3-5-sonnet-20241022",
        judge_provider="anthropic",
        golden_dataset_path="data/test_dataset.json",
        output_dir="./test_results",
        langsmith_project="test-project",
        min_accuracy=0.75,
        min_faithfulness=0.80,
        min_safety_score=4.0,
        max_cost_per_query=0.10,
        max_p95_latency=3000.0,
        verbose=False
    )


def test_task10_acceptance_criteria_1_all_metrics_aggregated(mock_config):
    """Verify: All metrics aggregated correctly."""
    case_results = [
        {
            "case_id": "test_001",
            "success": True,
            "diagnosis": {
                "primary_diagnosis": "STEMI",
                "differential_diagnoses": ["STEMI", "Unstable Angina"],
                "reasoning": "Test reasoning",
                "confidence": 0.85,
                "tokens_used": 1000,
                "model_used": "gpt-4o"
            },
            "safety_score": {"safety_score": 5},
            "quality_score": {"quality_score": 4},
            "latency_ms": 1500.0,
            "ground_truth": {
                "expert_diagnosis": "STEMI",
                "expert_reasoning": "Expert reasoning"
            }
        }
    ]
    
    golden_cases = [
        {"patient_presentation": "Test", "relevant_history": "History", "lab_results": {}}
    ]
    
    mock_ragas = Mock()
    mock_ragas.evaluate_with_ragas.return_value = {
        "faithfulness": 0.85,
        "answer_relevancy": 0.90,
        "context_precision": 0.88,
        "context_recall": 0.82
    }
    
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        metrics = evaluator._compute_aggregate_metrics(case_results, golden_cases)
        
        # Verify all required metrics are present
        assert "clinical_accuracy" in metrics
        assert "avg_safety_score" in metrics
        assert "avg_quality_score" in metrics
        assert "faithfulness" in metrics
        assert "answer_relevancy" in metrics
        assert "context_precision" in metrics
        assert "context_recall" in metrics
        assert "cost_per_query" in metrics
        assert "total_cost" in metrics
        assert "p50" in metrics
        assert "p95" in metrics
        assert "p99" in metrics
        
        # Verify aggregation is correct
        assert metrics["clinical_accuracy"] == 1.0  # Correct diagnosis
        assert metrics["avg_safety_score"] == 5.0
        assert metrics["avg_quality_score"] == 4.0


def test_task10_acceptance_criteria_2_metrics_format(mock_config):
    """Verify: Metrics match expected format."""
    case_results = [
        {
            "case_id": "test_001",
            "success": True,
            "diagnosis": {
                "primary_diagnosis": "STEMI",
                "differential_diagnoses": ["STEMI"],
                "reasoning": "Test",
                "confidence": 0.85,
                "tokens_used": 1000,
                "model_used": "gpt-4o"
            },
            "safety_score": {"safety_score": 5},
            "quality_score": {"quality_score": 4},
            "latency_ms": 1500.0,
            "ground_truth": {"expert_diagnosis": "STEMI"}
        }
    ]
    
    golden_cases = [
        {"patient_presentation": "Test", "relevant_history": "History", "lab_results": {}}
    ]
    
    mock_ragas = Mock()
    mock_ragas.evaluate_with_ragas.return_value = {
        "faithfulness": 0.85,
        "answer_relevancy": 0.90,
        "context_precision": 0.88,
        "context_recall": 0.82
    }
    
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        metrics = evaluator._compute_aggregate_metrics(case_results, golden_cases)
        
        # Verify data types
        assert isinstance(metrics["clinical_accuracy"], float)
        assert isinstance(metrics["avg_safety_score"], float)
        assert isinstance(metrics["avg_quality_score"], float)
        assert isinstance(metrics["total_cases"], int)
        assert isinstance(metrics["successful_cases"], int)
        assert isinstance(metrics["failed_cases"], int)
        
        # Verify value ranges
        assert 0.0 <= metrics["clinical_accuracy"] <= 1.0
        assert 1.0 <= metrics["avg_safety_score"] <= 5.0
        assert 1.0 <= metrics["avg_quality_score"] <= 5.0
        assert metrics["p50"] >= 0
        assert metrics["p95"] >= 0
        assert metrics["p99"] >= 0


def test_task10_acceptance_criteria_3_thresholds_checked(mock_config):
    """Verify: Thresholds checked."""
    case_results = [
        {
            "case_id": "test_001",
            "success": True,
            "diagnosis": {
                "primary_diagnosis": "STEMI",
                "differential_diagnoses": ["STEMI"],
                "reasoning": "Test",
                "confidence": 0.85,
                "tokens_used": 1000,
                "model_used": "gpt-4o"
            },
            "safety_score": {"safety_score": 5},
            "quality_score": {"quality_score": 4},
            "latency_ms": 1500.0,
            "ground_truth": {"expert_diagnosis": "STEMI"}
        }
    ]
    
    golden_cases = [
        {"patient_presentation": "Test", "relevant_history": "History", "lab_results": {}}
    ]
    
    mock_ragas = Mock()
    mock_ragas.evaluate_with_ragas.return_value = {
        "faithfulness": 0.85,
        "answer_relevancy": 0.90,
        "context_precision": 0.88,
        "context_recall": 0.82
    }
    
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        metrics = evaluator._compute_aggregate_metrics(case_results, golden_cases)
        
        # Verify threshold checking structure
        assert "thresholds_met" in metrics
        assert isinstance(metrics["thresholds_met"], dict)
        
        # Verify all threshold checks are present
        assert "accuracy" in metrics["thresholds_met"]
        assert "faithfulness" in metrics["thresholds_met"]
        assert "safety" in metrics["thresholds_met"]
        assert "cost" in metrics["thresholds_met"]
        assert "latency" in metrics["thresholds_met"]
        
        # Verify threshold values are boolean
        for key, value in metrics["thresholds_met"].items():
            assert isinstance(value, bool), f"Threshold {key} should be boolean"
        
        # Verify overall threshold check
        assert "all_thresholds_met" in metrics
        assert isinstance(metrics["all_thresholds_met"], bool)


def test_task10_acceptance_criteria_4_summary_dict_complete(mock_config):
    """Verify: Summary dict complete."""
    case_results = [
        {
            "case_id": "test_001",
            "success": True,
            "diagnosis": {
                "primary_diagnosis": "STEMI",
                "differential_diagnoses": ["STEMI"],
                "reasoning": "Test",
                "confidence": 0.85,
                "tokens_used": 1000,
                "model_used": "gpt-4o"
            },
            "safety_score": {"safety_score": 5},
            "quality_score": {"quality_score": 4},
            "latency_ms": 1500.0,
            "ground_truth": {"expert_diagnosis": "STEMI"}
        }
    ]
    
    golden_cases = [
        {"patient_presentation": "Test", "relevant_history": "History", "lab_results": {}}
    ]
    
    mock_ragas = Mock()
    mock_ragas.evaluate_with_ragas.return_value = {
        "faithfulness": 0.85,
        "answer_relevancy": 0.90,
        "context_precision": 0.88,
        "context_recall": 0.82
    }
    
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        metrics = evaluator._compute_aggregate_metrics(case_results, golden_cases)
        
        # Verify all required fields in summary dict
        required_fields = [
            "total_cases",
            "successful_cases",
            "failed_cases",
            "clinical_accuracy",
            "avg_safety_score",
            "avg_quality_score",
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
            "total_cost",
            "cost_per_query",
            "total_input_tokens",
            "total_output_tokens",
            "total_tokens",
            "p50",
            "p95",
            "p99",
            "mean",
            "min",
            "max",
            "thresholds_met",
            "all_thresholds_met"
        ]
        
        for field in required_fields:
            assert field in metrics, f"Required field '{field}' missing from metrics"
        
        # Verify the dict is properly structured
        assert isinstance(metrics, dict)
        assert len(metrics) >= len(required_fields)


def test_task10_handles_failed_cases(mock_config):
    """Verify: Metrics aggregation handles failed cases correctly."""
    case_results = [
        {
            "case_id": "test_001",
            "success": True,
            "diagnosis": {
                "primary_diagnosis": "STEMI",
                "differential_diagnoses": ["STEMI"],
                "reasoning": "Test",
                "confidence": 0.85,
                "tokens_used": 1000,
                "model_used": "gpt-4o"
            },
            "safety_score": {"safety_score": 5},
            "quality_score": {"quality_score": 4},
            "latency_ms": 1500.0,
            "ground_truth": {"expert_diagnosis": "STEMI"}
        },
        {
            "case_id": "test_002",
            "success": False,
            "error": "API failure"
        }
    ]
    
    golden_cases = [
        {"patient_presentation": "Test", "relevant_history": "History", "lab_results": {}}
    ]
    
    mock_ragas = Mock()
    mock_ragas.evaluate_with_ragas.return_value = {
        "faithfulness": 0.85,
        "answer_relevancy": 0.90,
        "context_precision": 0.88,
        "context_recall": 0.82
    }
    
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        metrics = evaluator._compute_aggregate_metrics(case_results, golden_cases)
        
        # Verify failed cases are tracked
        assert metrics["total_cases"] == 2
        assert metrics["successful_cases"] == 1
        assert metrics["failed_cases"] == 1
        
        # Verify metrics are computed only from successful cases
        assert metrics["clinical_accuracy"] == 1.0
