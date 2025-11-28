"""Unit tests for report generation."""

import pytest
import json
import csv
import tempfile
import os
from pathlib import Path

from src.reports import (
    generate_json_report,
    generate_csv_report,
    generate_summary_csv,
    save_all_reports,
    load_json_report,
    validate_json_report
)
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
        max_p95_latency=3000.0
    )


@pytest.fixture
def sample_metrics():
    """Create sample metrics."""
    return {
        "total_cases": 10,
        "successful_cases": 9,
        "failed_cases": 1,
        "clinical_accuracy": 0.85,
        "avg_safety_score": 4.5,
        "avg_quality_score": 4.2,
        "faithfulness": 0.88,
        "answer_relevancy": 0.92,
        "context_precision": 0.85,
        "context_recall": 0.80,
        "total_cost": 0.50,
        "cost_per_query": 0.05,
        "total_tokens": 10000,
        "p50": 1200.0,
        "p95": 2500.0,
        "p99": 3000.0,
        "mean": 1500.0,
        "thresholds_met": {
            "accuracy": True,
            "faithfulness": True,
            "safety": True,
            "cost": True,
            "latency": True
        },
        "all_thresholds_met": True
    }


@pytest.fixture
def sample_case_results():
    """Create sample case results."""
    return [
        {
            "case_id": "test_001",
            "success": True,
            "diagnosis": {
                "primary_diagnosis": "STEMI",
                "differential_diagnoses": ["STEMI", "Unstable Angina"],
                "reasoning": "Elevated troponin with chest pain",
                "confidence": 0.85,
                "tokens_used": 1000
            },
            "safety_score": {"safety_score": 5},
            "quality_score": {"quality_score": 4},
            "latency_ms": 1500.0,
            "ground_truth": {
                "expert_diagnosis": "STEMI"
            }
        },
        {
            "case_id": "test_002",
            "success": False,
            "error": "API timeout"
        }
    ]


def test_generate_json_report_basic(mock_config, sample_metrics, sample_case_results):
    """Test basic JSON report generation."""
    json_str = generate_json_report(sample_metrics, sample_case_results, mock_config)
    
    assert isinstance(json_str, str)
    assert len(json_str) > 0
    
    # Parse JSON to verify it's valid
    report = json.loads(json_str)
    assert isinstance(report, dict)


def test_json_report_contains_metadata(mock_config, sample_metrics, sample_case_results):
    """Test JSON report contains metadata."""
    json_str = generate_json_report(sample_metrics, sample_case_results, mock_config)
    report = json.loads(json_str)
    
    assert "metadata" in report
    assert "timestamp" in report["metadata"]
    assert "evaluation_type" in report["metadata"]
    assert "version" in report["metadata"]


def test_json_report_contains_configuration(mock_config, sample_metrics, sample_case_results):
    """Test JSON report contains configuration."""
    json_str = generate_json_report(sample_metrics, sample_case_results, mock_config)
    report = json.loads(json_str)
    
    assert "configuration" in report
    assert "model" in report["configuration"]
    assert "judge_model" in report["configuration"]
    assert "thresholds" in report["configuration"]
    
    # Check model details
    assert report["configuration"]["model"]["model_name"] == "gpt-4o"
    assert report["configuration"]["judge_model"] == "claude-3-5-sonnet-20241022"


def test_json_report_contains_metrics(mock_config, sample_metrics, sample_case_results):
    """Test JSON report contains all metrics."""
    json_str = generate_json_report(sample_metrics, sample_case_results, mock_config)
    report = json.loads(json_str)
    
    assert "summary_metrics" in report
    assert report["summary_metrics"]["clinical_accuracy"] == 0.85
    assert report["summary_metrics"]["avg_safety_score"] == 4.5


def test_json_report_contains_case_results(mock_config, sample_metrics, sample_case_results):
    """Test JSON report contains case results."""
    json_str = generate_json_report(sample_metrics, sample_case_results, mock_config)
    report = json.loads(json_str)
    
    assert "case_results" in report
    assert len(report["case_results"]) == 2
    assert report["case_results"][0]["case_id"] == "test_001"


def test_json_report_saves_to_file(mock_config, sample_metrics, sample_case_results):
    """Test JSON report saves to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_report.json")
        
        json_str = generate_json_report(
            sample_metrics,
            sample_case_results,
            mock_config,
            output_path
        )
        
        assert os.path.exists(output_path)
        
        # Verify file content
        with open(output_path, 'r') as f:
            content = f.read()
            assert content == json_str


def test_generate_csv_report_basic(mock_config, sample_metrics, sample_case_results):
    """Test basic CSV report generation."""
    csv_str = generate_csv_report(sample_metrics, sample_case_results, mock_config)
    
    assert isinstance(csv_str, str)
    assert len(csv_str) > 0
    assert "case_id" in csv_str  # Header
    assert "test_001" in csv_str  # Data


def test_csv_report_has_headers(mock_config, sample_metrics, sample_case_results):
    """Test CSV report has proper headers."""
    csv_str = generate_csv_report(sample_metrics, sample_case_results, mock_config)
    
    expected_headers = [
        "case_id", "success", "primary_diagnosis", "differential_diagnoses",
        "expert_diagnosis", "correct_in_top_3", "safety_score", "quality_score",
        "confidence", "latency_ms", "tokens_used", "reasoning", "error"
    ]
    
    # Check that all headers are in the CSV string
    for header in expected_headers:
        assert header in csv_str


def test_csv_report_has_data_rows(mock_config, sample_metrics, sample_case_results):
    """Test CSV report has data rows."""
    csv_str = generate_csv_report(sample_metrics, sample_case_results, mock_config)
    
    lines = csv_str.strip().split('\n')
    assert len(lines) >= 3  # Header + 2 data rows


def test_csv_report_handles_failed_cases(mock_config, sample_metrics, sample_case_results):
    """Test CSV report handles failed cases."""
    csv_str = generate_csv_report(sample_metrics, sample_case_results, mock_config)
    
    assert "API timeout" in csv_str
    assert "test_002" in csv_str


def test_csv_report_saves_to_file(mock_config, sample_metrics, sample_case_results):
    """Test CSV report saves to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_report.csv")
        
        csv_str = generate_csv_report(
            sample_metrics,
            sample_case_results,
            mock_config,
            output_path
        )
        
        assert os.path.exists(output_path)


def test_generate_summary_csv(mock_config, sample_metrics):
    """Test summary CSV generation."""
    csv_str = generate_summary_csv(sample_metrics, mock_config)
    
    assert isinstance(csv_str, str)
    assert "metric" in csv_str
    assert "value" in csv_str
    assert "Clinical Accuracy" in csv_str
    assert "gpt-4o" in csv_str


def test_summary_csv_includes_all_metrics(mock_config, sample_metrics):
    """Test summary CSV includes all key metrics."""
    csv_str = generate_summary_csv(sample_metrics, mock_config)
    
    expected_metrics = [
        "Clinical Accuracy",
        "Average Safety Score",
        "Faithfulness",
        "Cost per Query",
        "P95 Latency"
    ]
    
    for metric in expected_metrics:
        assert metric in csv_str


def test_save_all_reports(mock_config, sample_metrics, sample_case_results):
    """Test saving all report formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_paths = save_all_reports(
            sample_metrics,
            sample_case_results,
            mock_config,
            tmpdir
        )
        
        assert "json" in report_paths
        assert "csv_details" in report_paths
        assert "csv_summary" in report_paths
        
        # Verify all files exist
        assert os.path.exists(report_paths["json"])
        assert os.path.exists(report_paths["csv_details"])
        assert os.path.exists(report_paths["csv_summary"])


def test_load_json_report(mock_config, sample_metrics, sample_case_results):
    """Test loading JSON report from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_report.json")
        
        # Generate and save report
        generate_json_report(
            sample_metrics,
            sample_case_results,
            mock_config,
            output_path
        )
        
        # Load report
        loaded_report = load_json_report(output_path)
        
        assert isinstance(loaded_report, dict)
        assert "metadata" in loaded_report
        assert "summary_metrics" in loaded_report


def test_validate_json_report_valid(mock_config, sample_metrics, sample_case_results):
    """Test validation of valid JSON report."""
    json_str = generate_json_report(sample_metrics, sample_case_results, mock_config)
    report = json.loads(json_str)
    
    assert validate_json_report(report) is True


def test_validate_json_report_invalid():
    """Test validation of invalid JSON report."""
    invalid_report = {"metadata": {}}
    
    assert validate_json_report(invalid_report) is False


def test_json_report_handles_empty_results(mock_config):
    """Test JSON report handles empty results."""
    empty_metrics = {
        "total_cases": 0,
        "successful_cases": 0,
        "failed_cases": 0,
        "all_thresholds_met": False
    }
    empty_results = []
    
    json_str = generate_json_report(empty_metrics, empty_results, mock_config)
    report = json.loads(json_str)
    
    assert report["summary_metrics"]["total_cases"] == 0
    assert len(report["case_results"]) == 0


def test_csv_report_handles_empty_results(mock_config):
    """Test CSV report handles empty results."""
    empty_metrics = {
        "total_cases": 0,
        "successful_cases": 0,
        "failed_cases": 0
    }
    empty_results = []
    
    csv_str = generate_csv_report(empty_metrics, empty_results, mock_config)
    
    # Should still have headers
    assert "case_id" in csv_str


def test_csv_report_truncates_long_reasoning(mock_config, sample_metrics):
    """Test CSV report truncates long reasoning text."""
    long_reasoning_result = [{
        "case_id": "test_001",
        "success": True,
        "diagnosis": {
            "primary_diagnosis": "Test",
            "differential_diagnoses": ["Test"],
            "reasoning": "A" * 500,  # Very long reasoning
            "confidence": 0.85,
            "tokens_used": 1000
        },
        "safety_score": {"safety_score": 5},
        "quality_score": {"quality_score": 4},
        "latency_ms": 1500.0,
        "ground_truth": {"expert_diagnosis": "Test"}
    }]
    
    csv_str = generate_csv_report(sample_metrics, long_reasoning_result, mock_config)
    
    # Reasoning should be truncated to 200 chars
    assert len(csv_str) < 1000  # Much shorter than 500 char reasoning


def test_report_paths_have_timestamps(mock_config, sample_metrics, sample_case_results):
    """Test report file paths include timestamps."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_paths = save_all_reports(
            sample_metrics,
            sample_case_results,
            mock_config,
            tmpdir
        )
        
        # All paths should contain timestamp pattern
        for path in report_paths.values():
            assert "_" in path  # Timestamp separator
            assert ".json" in path or ".csv" in path


def test_json_report_is_pretty_printed(mock_config, sample_metrics, sample_case_results):
    """Test JSON report is formatted with indentation."""
    json_str = generate_json_report(sample_metrics, sample_case_results, mock_config)
    
    # Pretty-printed JSON should have newlines and indentation
    assert "\n" in json_str
    assert "  " in json_str  # Indentation


def test_csv_can_be_parsed(mock_config, sample_metrics, sample_case_results):
    """Test CSV report can be parsed back."""
    csv_str = generate_csv_report(sample_metrics, sample_case_results, mock_config)
    
    import io
    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["case_id"] == "test_001"
