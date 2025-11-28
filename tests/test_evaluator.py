"""Unit tests for evaluation runner."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.evaluator import Evaluator, EvaluationResults, create_evaluator
from src.config import EvalConfig, ModelConfig
from src.diagnosis_assistant import DiagnosisResponse


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
        subset_size=5,
        verbose=False
    )


@pytest.fixture
def sample_golden_dataset():
    """Create a sample golden dataset."""
    return {
        "cases": [
            {
                "case_id": "test_001",
                "patient_presentation": "45-year-old male with chest pain",
                "relevant_history": "Hypertension, smoking",
                "lab_results": {"troponin": "2.5 ng/mL"},
                "expert_diagnosis": "STEMI",
                "expert_reasoning": "Elevated troponin with chest pain",
                "differential_diagnoses": ["STEMI", "Unstable Angina", "Pericarditis"],
                "metadata": {"specialty": "cardiology", "complexity": "moderate"}
            },
            {
                "case_id": "test_002",
                "patient_presentation": "30-year-old female with fever and cough",
                "relevant_history": "No significant history",
                "lab_results": {"WBC": "15000"},
                "expert_diagnosis": "Pneumonia",
                "expert_reasoning": "Fever, cough, elevated WBC",
                "differential_diagnoses": ["Pneumonia", "Bronchitis", "COVID-19"],
                "metadata": {"specialty": "pulmonology", "complexity": "low"}
            }
        ]
    }


@pytest.fixture
def mock_diagnosis_response():
    """Create a mock diagnosis response."""
    return DiagnosisResponse(
        primary_diagnosis="STEMI",
        differential_diagnoses=["STEMI", "Unstable Angina", "Pericarditis"],
        reasoning="Elevated troponin with typical chest pain suggests acute coronary syndrome",
        confidence=0.85,
        recommended_tests=["ECG", "Cardiac catheterization"],
        urgency="emergent",
        model_used="gpt-4o",
        tokens_used=1000,
        latency_ms=1500.0
    )


def test_evaluator_initialization(mock_config):
    """Test evaluator initialization."""
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator'), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        
        assert evaluator.config == mock_config
        assert evaluator.diagnosis_assistant is not None
        assert evaluator.ragas_evaluator is not None
        assert evaluator.judge_evaluator is not None


def test_load_golden_dataset(mock_config, sample_golden_dataset, tmp_path):
    """Test loading golden dataset."""
    # Create temporary dataset file
    dataset_file = tmp_path / "test_dataset.json"
    with open(dataset_file, 'w') as f:
        json.dump(sample_golden_dataset, f)
    
    # Update config with temp path
    mock_config.golden_dataset_path = str(dataset_file)
    mock_config.subset_size = None
    
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator'), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        cases = evaluator.load_golden_dataset()
        
        assert len(cases) == 2
        assert cases[0]["case_id"] == "test_001"
        assert cases[1]["case_id"] == "test_002"


def test_load_golden_dataset_with_subset(mock_config, sample_golden_dataset, tmp_path):
    """Test loading golden dataset with subset."""
    # Create temporary dataset file
    dataset_file = tmp_path / "test_dataset.json"
    with open(dataset_file, 'w') as f:
        json.dump(sample_golden_dataset, f)
    
    # Update config with temp path and subset
    mock_config.golden_dataset_path = str(dataset_file)
    mock_config.subset_size = 1
    
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator'), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        cases = evaluator.load_golden_dataset()
        
        assert len(cases) == 1
        assert cases[0]["case_id"] == "test_001"


def test_load_golden_dataset_file_not_found(mock_config):
    """Test loading golden dataset with missing file."""
    mock_config.golden_dataset_path = "nonexistent.json"
    
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator'), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        
        with pytest.raises(FileNotFoundError):
            evaluator.load_golden_dataset()


def test_process_case(mock_config, sample_golden_dataset, mock_diagnosis_response):
    """Test processing a single case."""
    case = sample_golden_dataset["cases"][0]
    
    # Mock components
    mock_assistant = Mock()
    mock_assistant.generate_diagnosis.return_value = mock_diagnosis_response
    
    mock_judge = Mock()
    mock_judge.judge_safety.return_value = {
        "safety_score": 5,
        "reasoning": "Safe diagnosis",
        "concerns": [],
        "strengths": ["Appropriate urgency"]
    }
    mock_judge.judge_quality.return_value = {
        "quality_score": 4,
        "reasoning": "Good quality",
        "diagnostic_accuracy": "Correct",
        "reasoning_quality": "Sound",
        "suggestions": []
    }
    
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_assistant), \
         patch('src.evaluator.RagasEvaluator'), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge):
        
        evaluator = Evaluator(mock_config)
        result = evaluator._process_case(case, 0)
        
        assert result["case_id"] == "test_001"
        assert result["success"] is True
        assert result["diagnosis"]["primary_diagnosis"] == "STEMI"
        assert result["safety_score"]["safety_score"] == 5
        assert result["quality_score"]["quality_score"] == 4
        assert "latency_ms" in result
        assert result["ground_truth"]["expert_diagnosis"] == "STEMI"


def test_compute_aggregate_metrics(mock_config):
    """Test computing aggregate metrics."""
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
        },
        {
            "case_id": "test_002",
            "success": True,
            "diagnosis": {
                "primary_diagnosis": "Pneumonia",
                "differential_diagnoses": ["Pneumonia", "Bronchitis"],
                "reasoning": "Test reasoning",
                "confidence": 0.80,
                "tokens_used": 800,
                "model_used": "gpt-4o"
            },
            "safety_score": {"safety_score": 4},
            "quality_score": {"quality_score": 5},
            "latency_ms": 1200.0,
            "ground_truth": {
                "expert_diagnosis": "Pneumonia",
                "expert_reasoning": "Expert reasoning"
            }
        }
    ]
    
    golden_cases = [
        {"patient_presentation": "Test 1", "relevant_history": "History 1", "lab_results": {}},
        {"patient_presentation": "Test 2", "relevant_history": "History 2", "lab_results": {}}
    ]
    
    # Mock Ragas evaluator
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
        
        assert metrics["total_cases"] == 2
        assert metrics["successful_cases"] == 2
        assert metrics["failed_cases"] == 0
        assert metrics["clinical_accuracy"] == 1.0  # Both correct
        assert metrics["avg_safety_score"] == 4.5
        assert metrics["avg_quality_score"] == 4.5
        assert "faithfulness" in metrics
        assert "cost_per_query" in metrics
        assert "p95" in metrics


def test_compute_aggregate_metrics_with_failures(mock_config):
    """Test computing metrics with some failed cases."""
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
        {"patient_presentation": "Test 1", "relevant_history": "History 1", "lab_results": {}}
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
        
        assert metrics["total_cases"] == 2
        assert metrics["successful_cases"] == 1
        assert metrics["failed_cases"] == 1


def test_evaluation_results_to_dict(mock_config):
    """Test converting evaluation results to dictionary."""
    case_results = [{"case_id": "test_001", "success": True}]
    metrics = {"clinical_accuracy": 0.85}
    timestamp = "2024-01-01T00:00:00"
    
    results = EvaluationResults(
        case_results=case_results,
        metrics=metrics,
        config=mock_config,
        timestamp=timestamp
    )
    
    result_dict = results.to_dict()
    
    assert result_dict["timestamp"] == timestamp
    assert result_dict["num_cases"] == 1
    assert "config" in result_dict
    assert "metrics" in result_dict
    assert "case_results" in result_dict


def test_create_evaluator(mock_config):
    """Test factory function."""
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator'), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = create_evaluator(mock_config)
        
        assert isinstance(evaluator, Evaluator)
        assert evaluator.config == mock_config


def test_evaluator_handles_ragas_failure(mock_config):
    """Test that evaluator handles Ragas failures gracefully."""
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
    
    # Mock Ragas to raise exception
    mock_ragas = Mock()
    mock_ragas.evaluate_with_ragas.side_effect = Exception("Ragas failed")
    
    with patch('src.evaluator.DiagnosisAssistant'), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas), \
         patch('src.evaluator.JudgeEvaluator'):
        
        evaluator = Evaluator(mock_config)
        metrics = evaluator._compute_aggregate_metrics(case_results, golden_cases)
        
        # Should still return metrics with default Ragas values
        assert "faithfulness" in metrics
        assert metrics["faithfulness"] == 0.0
        assert "error" in metrics or metrics["faithfulness"] == 0.0
