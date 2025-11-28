"""Integration tests for complete evaluation pipeline.

These tests verify the end-to-end evaluation flow with minimal mocking.
Tests the complete pipeline from loading dataset through generating reports.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.evaluator import Evaluator, EvaluationResults
from src.config import EvalConfig, ModelConfig
from src.diagnosis_assistant import DiagnosisResponse


@pytest.fixture
def small_test_dataset(tmp_path):
    """Create a small test dataset (10 cases) for integration testing."""
    dataset = {
        "cases": [
            {
                "case_id": f"int_test_{i:03d}",
                "patient_presentation": f"Test patient {i} with symptoms",
                "relevant_history": f"History for patient {i}",
                "lab_results": {"test_value": f"{i}.0"},
                "expert_diagnosis": f"Diagnosis_{i % 3}",
                "expert_reasoning": f"Reasoning for diagnosis {i}",
                "differential_diagnoses": [f"Diagnosis_{i % 3}", f"Alt_Diagnosis_{i}"],
                "metadata": {
                    "specialty": ["cardiology", "nephrology", "endocrinology"][i % 3],
                    "complexity": ["low", "moderate", "high"][i % 3],
                    "age_group": "middle_age"
                }
            }
            for i in range(10)
        ]
    }
    
    dataset_file = tmp_path / "test_dataset.json"
    with open(dataset_file, 'w') as f:
        json.dump(dataset, f)
    
    return dataset_file


@pytest.fixture
def integration_config(tmp_path, small_test_dataset):
    """Create configuration for integration tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    return EvalConfig(
        model=ModelConfig(
            provider="openai",
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=2000
        ),
        judge_model="claude-3-5-sonnet-20241022",
        judge_provider="anthropic",
        golden_dataset_path=str(small_test_dataset),
        output_dir=str(output_dir),
        langsmith_project="integration-test-project",
        min_accuracy=0.70,
        min_faithfulness=0.75,
        min_safety_score=3.5,
        max_cost_per_query=0.15,
        max_p95_latency=5000.0,
        subset_size=None,
        verbose=False
    )


@pytest.fixture
def mock_diagnosis_assistant():
    """Create a mock diagnosis assistant that returns realistic responses."""
    def generate_diagnosis_side_effect(patient_presentation, relevant_history, lab_results):
        import re
        match = re.search(r'patient (\d+)', patient_presentation)
        case_num = int(match.group(1)) if match else 0
        
        return DiagnosisResponse(
            primary_diagnosis=f"Diagnosis_{case_num % 3}",
            differential_diagnoses=[f"Diagnosis_{case_num % 3}", f"Alt_Diagnosis_{case_num}"],
            reasoning=f"Clinical reasoning for case {case_num}",
            confidence=0.80 + (case_num % 10) * 0.02,
            recommended_tests=["Test A", "Test B"],
            urgency="routine",
            model_used="gpt-4o",
            tokens_used=800 + case_num * 10,
            latency_ms=1000.0 + case_num * 100
        )
    
    mock = Mock()
    mock.generate_diagnosis.side_effect = generate_diagnosis_side_effect
    return mock


@pytest.fixture
def mock_judge_evaluator():
    """Create a mock judge evaluator."""
    def judge_safety_side_effect(case, diagnosis_response):
        return {
            "safety_score": 4,
            "reasoning": "Safe diagnosis with appropriate recommendations",
            "concerns": [],
            "strengths": ["Appropriate urgency", "Comprehensive differential"]
        }
    
    def judge_quality_side_effect(case, diagnosis_response):
        return {
            "quality_score": 4,
            "reasoning": "Good quality diagnosis",
            "diagnostic_accuracy": "Correct",
            "reasoning_quality": "Sound clinical reasoning",
            "suggestions": []
        }
    
    mock = Mock()
    mock.judge_safety.side_effect = judge_safety_side_effect
    mock.judge_quality.side_effect = judge_quality_side_effect
    return mock


@pytest.fixture
def mock_ragas_evaluator():
    """Create a mock Ragas evaluator."""
    def evaluate_side_effect(questions, answers, contexts, ground_truths):
        return {
            "faithfulness": 0.85,
            "answer_relevancy": 0.88,
            "context_precision": 0.82,
            "context_recall": 0.80
        }
    
    mock = Mock()
    mock.evaluate_with_ragas.side_effect = evaluate_side_effect
    return mock


def test_end_to_end_evaluation_pipeline(
    integration_config,
    mock_diagnosis_assistant,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test complete evaluation pipeline end-to-end."""
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        evaluator = Evaluator(integration_config)
        results = evaluator.run_evaluation()
        
        assert isinstance(results, EvaluationResults)
        assert len(results.case_results) == 10
        assert results.metrics is not None
        assert results.config == integration_config
        
        successful_cases = [r for r in results.case_results if r["success"]]
        assert len(successful_cases) == 10
        
        assert "clinical_accuracy" in results.metrics
        assert "avg_safety_score" in results.metrics
        assert "avg_quality_score" in results.metrics
        assert "faithfulness" in results.metrics
        assert "cost_per_query" in results.metrics
        assert "p95" in results.metrics


def test_evaluation_error_handling(
    integration_config,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test that evaluation handles errors gracefully."""
    def failing_generate_diagnosis(patient_presentation, relevant_history, lab_results):
        import re
        match = re.search(r'patient (\d+)', patient_presentation)
        case_num = int(match.group(1)) if match else 0
        
        if case_num in [3, 7]:
            raise Exception(f"API failure for case {case_num}")
        
        return DiagnosisResponse(
            primary_diagnosis=f"Diagnosis_{case_num % 3}",
            differential_diagnoses=[f"Diagnosis_{case_num % 3}"],
            reasoning=f"Reasoning {case_num}",
            confidence=0.85,
            recommended_tests=[],
            urgency="routine",
            model_used="gpt-4o",
            tokens_used=1000,
            latency_ms=1500.0
        )
    
    mock_assistant = Mock()
    mock_assistant.generate_diagnosis.side_effect = failing_generate_diagnosis
    
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        evaluator = Evaluator(integration_config)
        results = evaluator.run_evaluation()
        
        assert len(results.case_results) == 10
        
        failed_cases = [r for r in results.case_results if not r["success"]]
        assert len(failed_cases) == 2
        
        successful_cases = [r for r in results.case_results if r["success"]]
        assert len(successful_cases) == 8
        
        assert results.metrics["successful_cases"] == 8
        assert results.metrics["failed_cases"] == 2


def test_reports_generated(
    integration_config,
    mock_diagnosis_assistant,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test that all reports are generated correctly."""
    from src.reports import save_all_reports
    from src.dashboard import generate_dashboard_with_charts
    
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        evaluator = Evaluator(integration_config)
        results = evaluator.run_evaluation()
        
        # Generate reports using the reports module
        save_all_reports(
            results.metrics,
            results.case_results,
            integration_config,
            integration_config.output_dir
        )
        
        # Generate dashboard
        dashboard_path = Path(integration_config.output_dir) / "dashboard.html"
        generate_dashboard_with_charts(
            results.metrics,
            results.case_results,
            integration_config,
            str(dashboard_path)
        )
        
        output_dir = Path(integration_config.output_dir)
        
        # Verify JSON report exists (check both possible naming patterns)
        json_files = list(output_dir.glob("evaluation_report_*.json")) + list(output_dir.glob("evaluation_results_*.json"))
        assert len(json_files) > 0
        
        with open(json_files[0]) as f:
            json_data = json.load(f)
            # Check for either metrics or evaluation_status (different report formats)
            assert "metrics" in json_data or "evaluation_status" in json_data
            assert "case_results" in json_data
            assert "metadata" in json_data or "timestamp" in json_data
        
        # Verify CSV reports exist
        csv_files = list(output_dir.glob("*.csv"))
        assert len(csv_files) >= 2
        
        # Verify dashboard exists
        assert dashboard_path.exists()
        
        with open(dashboard_path, encoding='utf-8') as f:
            html_content = f.read()
            assert "<!DOCTYPE html>" in html_content or "<html>" in html_content
            assert "Clinical Accuracy" in html_content


def test_metrics_computed_correctly(
    integration_config,
    mock_diagnosis_assistant,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test that metrics are computed correctly."""
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        evaluator = Evaluator(integration_config)
        results = evaluator.run_evaluation()
        
        metrics = results.metrics
        
        required_metrics = [
            "total_cases", "successful_cases",
            "clinical_accuracy", "avg_safety_score", "avg_quality_score",
            "faithfulness", "answer_relevancy", "context_precision", "context_recall",
            "total_cost", "cost_per_query", "total_tokens",
            "p50", "p95", "p99", "mean"
        ]
        
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
        
        assert 0 <= metrics["clinical_accuracy"] <= 1
        assert 1 <= metrics["avg_safety_score"] <= 5
        assert 1 <= metrics["avg_quality_score"] <= 5
        assert 0 <= metrics["faithfulness"] <= 1
        assert metrics["total_cost"] >= 0
        assert metrics["cost_per_query"] >= 0
        assert metrics["p95"] >= metrics["p50"]


def test_evaluation_completes_quickly(
    integration_config,
    mock_diagnosis_assistant,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test that evaluation completes in reasonable time (< 30 seconds)."""
    import time
    
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        evaluator = Evaluator(integration_config)
        
        start_time = time.time()
        results = evaluator.run_evaluation()
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 30, f"Evaluation took {elapsed_time:.2f}s, expected < 30s"
        assert len(results.case_results) == 10


def test_evaluation_with_different_configs(
    tmp_path,
    small_test_dataset,
    mock_diagnosis_assistant,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test evaluation with different model configurations."""
    configs = [
        EvalConfig(
            model=ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.5, max_tokens=1500),
            judge_model="claude-3-5-sonnet-20241022",
            judge_provider="anthropic",
            golden_dataset_path=str(small_test_dataset),
            output_dir=str(tmp_path / "output1"),
            langsmith_project="test-config-1"
        ),
        EvalConfig(
            model=ModelConfig(provider="anthropic", model_name="claude-3-5-sonnet-20241022", temperature=0.7, max_tokens=2000),
            judge_model="gpt-4o",
            judge_provider="openai",
            golden_dataset_path=str(small_test_dataset),
            output_dir=str(tmp_path / "output2"),
            langsmith_project="test-config-2"
        )
    ]
    
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        results_list = []
        for config in configs:
            (tmp_path / config.output_dir).mkdir(parents=True, exist_ok=True)
            evaluator = Evaluator(config)
            results = evaluator.run_evaluation()
            results_list.append(results)
        
        assert len(results_list) == 2
        assert all(len(r.case_results) == 10 for r in results_list)
        assert all(r.metrics is not None for r in results_list)


def test_subset_evaluation(
    tmp_path,
    small_test_dataset,
    mock_diagnosis_assistant,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test evaluation with subset of dataset."""
    config = EvalConfig(
        model=ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.7, max_tokens=2000),
        judge_model="claude-3-5-sonnet-20241022",
        judge_provider="anthropic",
        golden_dataset_path=str(small_test_dataset),
        output_dir=str(tmp_path / "output"),
        langsmith_project="subset-test",
        subset_size=5
    )
    
    (tmp_path / "output").mkdir()
    
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        evaluator = Evaluator(config)
        results = evaluator.run_evaluation()
        
        assert len(results.case_results) == 5
        assert results.metrics["total_cases"] == 5


def test_threshold_validation(
    integration_config,
    mock_diagnosis_assistant,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test that threshold validation works correctly."""
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        evaluator = Evaluator(integration_config)
        results = evaluator.run_evaluation()
        
        # Manually check thresholds since there's no check_thresholds method
        metrics = results.metrics
        
        thresholds_met = (
            metrics.get("clinical_accuracy", 0) >= integration_config.min_accuracy and
            metrics.get("faithfulness", 0) >= integration_config.min_faithfulness and
            metrics.get("avg_safety_score", 0) >= integration_config.min_safety_score and
            metrics.get("cost_per_query", float('inf')) <= integration_config.max_cost_per_query and
            metrics.get("p95", float('inf')) <= integration_config.max_p95_latency
        )
        
        assert isinstance(thresholds_met, bool)
        # With our mocked values, thresholds should be met
        assert thresholds_met is True


def test_evaluation_with_ragas_failure(
    integration_config,
    mock_diagnosis_assistant,
    mock_judge_evaluator
):
    """Test that evaluation continues even if Ragas fails."""
    mock_ragas = Mock()
    mock_ragas.evaluate_with_ragas.side_effect = Exception("Ragas API failure")
    
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas):
        
        evaluator = Evaluator(integration_config)
        results = evaluator.run_evaluation()
        
        assert len(results.case_results) == 10
        assert "faithfulness" in results.metrics
        assert results.metrics["faithfulness"] == 0.0 or results.metrics.get("ragas_error")


def test_case_result_structure(
    integration_config,
    mock_diagnosis_assistant,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test that case results have correct structure."""
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        evaluator = Evaluator(integration_config)
        results = evaluator.run_evaluation()
        
        successful_case = next(r for r in results.case_results if r["success"])
        
        required_fields = [
            "case_id", "success", "diagnosis", "safety_score",
            "quality_score", "latency_ms", "ground_truth"
        ]
        
        for field in required_fields:
            assert field in successful_case, f"Missing field: {field}"
        
        diagnosis = successful_case["diagnosis"]
        assert "primary_diagnosis" in diagnosis
        assert "differential_diagnoses" in diagnosis
        assert "reasoning" in diagnosis
        assert "confidence" in diagnosis


def test_evaluation_results_serialization(
    integration_config,
    mock_diagnosis_assistant,
    mock_judge_evaluator,
    mock_ragas_evaluator
):
    """Test that evaluation results can be serialized to JSON."""
    with patch('src.evaluator.DiagnosisAssistant', return_value=mock_diagnosis_assistant), \
         patch('src.evaluator.JudgeEvaluator', return_value=mock_judge_evaluator), \
         patch('src.evaluator.RagasEvaluator', return_value=mock_ragas_evaluator):
        
        evaluator = Evaluator(integration_config)
        results = evaluator.run_evaluation()
        
        results_dict = results.to_dict()
        
        json_str = json.dumps(results_dict)
        assert len(json_str) > 0
        
        loaded_dict = json.loads(json_str)
        assert loaded_dict["num_cases"] == 10
        assert "metrics" in loaded_dict
        assert "case_results" in loaded_dict
