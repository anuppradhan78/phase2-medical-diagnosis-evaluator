"""Tests for A/B testing functionality."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.ab_testing import (
    run_ab_test,
    compute_metric_comparison,
    determine_overall_winner,
    generate_comparison_dashboard
)
from src.config import EvalConfig, ModelConfig
from src.evaluator import EvaluationResults


@pytest.fixture
def mock_results_a():
    """Create mock evaluation results for config A."""
    return EvaluationResults(
        case_results=[
            {
                "case_id": "test_001",
                "success": True,
                "diagnosis": {"primary_diagnosis": "Test"},
                "safety_score": {"safety_score": 4},
                "quality_score": {"quality_score": 4},
                "latency_ms": 1000.0,
                "ground_truth": {"expert_diagnosis": "Test"}
            },
            {
                "case_id": "test_002",
                "success": True,
                "diagnosis": {"primary_diagnosis": "Test"},
                "safety_score": {"safety_score": 5},
                "quality_score": {"quality_score": 5},
                "latency_ms": 1200.0,
                "ground_truth": {"expert_diagnosis": "Test"}
            }
        ],
        metrics={
            "clinical_accuracy": 0.85,
            "avg_safety_score": 4.5,
            "avg_quality_score": 4.5,
            "faithfulness": 0.80,
            "answer_relevancy": 0.85,
            "cost_per_query": 0.05,
            "p95": 1200.0
        },
        config=Mock(),
        timestamp="2024-01-01T00:00:00"
    )


@pytest.fixture
def mock_results_b():
    """Create mock evaluation results for config B."""
    return EvaluationResults(
        case_results=[
            {
                "case_id": "test_001",
                "success": True,
                "diagnosis": {"primary_diagnosis": "Test"},
                "safety_score": {"safety_score": 5},
                "quality_score": {"quality_score": 5},
                "latency_ms": 900.0,
                "ground_truth": {"expert_diagnosis": "Test"}
            },
            {
                "case_id": "test_002",
                "success": True,
                "diagnosis": {"primary_diagnosis": "Test"},
                "safety_score": {"safety_score": 5},
                "quality_score": {"quality_score": 4},
                "latency_ms": 1000.0,
                "ground_truth": {"expert_diagnosis": "Test"}
            }
        ],
        metrics={
            "clinical_accuracy": 0.90,
            "avg_safety_score": 5.0,
            "avg_quality_score": 4.5,
            "faithfulness": 0.85,
            "answer_relevancy": 0.88,
            "cost_per_query": 0.08,
            "p95": 1000.0
        },
        config=Mock(),
        timestamp="2024-01-01T00:00:00"
    )


def test_compute_metric_comparison(mock_results_a, mock_results_b):
    """Test computing metric comparisons."""
    comparison = compute_metric_comparison(mock_results_a, mock_results_b)
    
    assert "metrics" in comparison
    assert "statistical_tests" in comparison
    assert "winner" in comparison
    
    # Check clinical accuracy comparison
    assert "clinical_accuracy" in comparison["metrics"]
    acc_comp = comparison["metrics"]["clinical_accuracy"]
    assert acc_comp["config_a"] == 0.85
    assert acc_comp["config_b"] == 0.90
    assert abs(acc_comp["difference"] - 0.05) < 0.001  # Allow for floating point precision
    assert acc_comp["winner"] == "B"  # B has higher accuracy
    
    # Check cost comparison (lower is better)
    assert "cost_per_query" in comparison["metrics"]
    cost_comp = comparison["metrics"]["cost_per_query"]
    assert cost_comp["config_a"] == 0.05
    assert cost_comp["config_b"] == 0.08
    assert cost_comp["winner"] == "A"  # A has lower cost


def test_determine_overall_winner():
    """Test determining overall winner."""
    metric_comparisons = {
        "clinical_accuracy": {"winner": "B"},
        "avg_safety_score": {"winner": "B"},
        "avg_quality_score": {"winner": "Tie"},
        "cost_per_query": {"winner": "A"},
        "p95": {"winner": "B"}
    }
    
    winner = determine_overall_winner(metric_comparisons)
    assert winner in ["A", "B", "Tie"]


def test_run_ab_test(tmp_path, mock_results_a, mock_results_b):
    """Test running complete A/B test."""
    config_a = EvalConfig(
        model=ModelConfig(provider="openai", model_name="gpt-4o", temperature=0.7, max_tokens=2000),
        judge_model="claude-3-5-sonnet-20241022",
        judge_provider="anthropic",
        golden_dataset_path=str(tmp_path / "dataset.json"),
        output_dir=str(tmp_path / "output_a"),
        langsmith_project="test-a"
    )
    
    config_b = EvalConfig(
        model=ModelConfig(provider="anthropic", model_name="claude-3-5-sonnet-20241022", temperature=0.7, max_tokens=2000),
        judge_model="gpt-4o",
        judge_provider="openai",
        golden_dataset_path=str(tmp_path / "dataset.json"),
        output_dir=str(tmp_path / "output_b"),
        langsmith_project="test-b"
    )
    
    # Create dummy dataset
    dataset = {"cases": [{"case_id": "test_001", "patient_presentation": "Test"}]}
    with open(tmp_path / "dataset.json", 'w') as f:
        json.dump(dataset, f)
    
    # Mock the Evaluator to return our mock results
    with patch('src.ab_testing.Evaluator') as mock_evaluator_class:
        mock_evaluator_a = Mock()
        mock_evaluator_b = Mock()
        mock_evaluator_a.run_evaluation.return_value = mock_results_a
        mock_evaluator_b.run_evaluation.return_value = mock_results_b
        
        mock_evaluator_class.side_effect = [mock_evaluator_a, mock_evaluator_b]
        
        output_dir = tmp_path / "ab_results"
        results = run_ab_test(config_a, config_b, str(output_dir))
        
        assert "timestamp" in results
        assert "config_a" in results
        assert "config_b" in results
        assert "results_a" in results
        assert "results_b" in results
        assert "comparison" in results
        
        # Verify comparison report was saved
        json_files = list(output_dir.glob("ab_test_comparison_*.json"))
        assert len(json_files) > 0


def test_generate_comparison_dashboard(tmp_path, mock_results_a, mock_results_b):
    """Test generating comparison dashboard."""
    comparison = compute_metric_comparison(mock_results_a, mock_results_b)
    
    ab_test_results = {
        "timestamp": "2024-01-01T00:00:00",
        "config_a": {
            "model": {"model_name": "gpt-4o", "provider": "openai", "temperature": 0.7}
        },
        "config_b": {
            "model": {"model_name": "claude-3-5-sonnet-20241022", "provider": "anthropic", "temperature": 0.7}
        },
        "comparison": comparison
    }
    
    dashboard_path = tmp_path / "comparison_dashboard.html"
    generate_comparison_dashboard(ab_test_results, str(dashboard_path))
    
    assert dashboard_path.exists()
    
    with open(dashboard_path, encoding='utf-8') as f:
        html_content = f.read()
        assert "<!DOCTYPE html>" in html_content
        assert "A/B Test Comparison Dashboard" in html_content
        assert "Config A" in html_content
        assert "Config B" in html_content
        assert "gpt-4o" in html_content
        assert "claude-3-5-sonnet-20241022" in html_content


def test_statistical_tests_with_insufficient_data():
    """Test statistical tests with insufficient data."""
    from src.ab_testing import perform_statistical_tests
    
    results_a = EvaluationResults(
        case_results=[{"case_id": "test_001", "success": True, "latency_ms": 1000.0, "safety_score": {"safety_score": 4}, "quality_score": {"quality_score": 4}}],
        metrics={},
        config=Mock(),
        timestamp="2024-01-01T00:00:00"
    )
    
    results_b = EvaluationResults(
        case_results=[{"case_id": "test_001", "success": True, "latency_ms": 900.0, "safety_score": {"safety_score": 5}, "quality_score": {"quality_score": 5}}],
        metrics={},
        config=Mock(),
        timestamp="2024-01-01T00:00:00"
    )
    
    tests = perform_statistical_tests(results_a, results_b)
    
    # Should return a note about insufficient data
    assert "note" in tests or len(tests) == 0


def test_metric_comparison_with_zero_values():
    """Test metric comparison handles zero values correctly."""
    results_a = EvaluationResults(
        case_results=[],
        metrics={"clinical_accuracy": 0.0, "cost_per_query": 0.0},
        config=Mock(),
        timestamp="2024-01-01T00:00:00"
    )
    
    results_b = EvaluationResults(
        case_results=[],
        metrics={"clinical_accuracy": 0.5, "cost_per_query": 0.05},
        config=Mock(),
        timestamp="2024-01-01T00:00:00"
    )
    
    comparison = compute_metric_comparison(results_a, results_b)
    
    assert "clinical_accuracy" in comparison["metrics"]
    # Should handle division by zero gracefully
    assert comparison["metrics"]["clinical_accuracy"]["percent_change"] == float('inf')
