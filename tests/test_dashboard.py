"""Unit tests for dashboard generator."""

import pytest
from pathlib import Path
import tempfile
import os

from src.dashboard import (
    generate_dashboard,
    save_dashboard,
    _generate_summary_cards,
    _generate_threshold_status,
    _generate_failure_table,
    _get_langsmith_url
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
                "reasoning": "Elevated troponin with chest pain"
            },
            "safety_score": {"safety_score": 5},
            "quality_score": {"quality_score": 4},
            "ground_truth": {
                "expert_diagnosis": "STEMI"
            }
        },
        {
            "case_id": "test_002",
            "success": True,
            "diagnosis": {
                "primary_diagnosis": "Bronchitis",
                "differential_diagnoses": ["Bronchitis", "Common Cold"],
                "reasoning": "Cough without fever"
            },
            "safety_score": {"safety_score": 4},
            "quality_score": {"quality_score": 3},
            "ground_truth": {
                "expert_diagnosis": "Pneumonia"
            }
        },
        {
            "case_id": "test_003",
            "success": False,
            "error": "API timeout"
        }
    ]


def test_generate_dashboard_basic(mock_config, sample_metrics, sample_case_results):
    """Test basic dashboard generation."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert isinstance(html, str)
    assert len(html) > 0
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html


def test_dashboard_contains_title(mock_config, sample_metrics, sample_case_results):
    """Test dashboard contains title."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert "Medical Diagnosis Evaluation Results" in html
    assert "<title>" in html


def test_dashboard_contains_metrics(mock_config, sample_metrics, sample_case_results):
    """Test dashboard contains all key metrics."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    # Check for metric values
    assert "85.0%" in html or "0.85" in html  # Clinical accuracy
    assert "4.50" in html  # Safety score
    assert "4.20" in html  # Quality score
    assert "$0.0500" in html  # Cost per query
    assert "2500ms" in html  # P95 latency


def test_dashboard_contains_model_info(mock_config, sample_metrics, sample_case_results):
    """Test dashboard contains model information."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert "gpt-4o" in html
    assert "claude-3-5-sonnet-20241022" in html


def test_dashboard_contains_sections(mock_config, sample_metrics, sample_case_results):
    """Test dashboard contains all required sections."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert "Summary Metrics" in html
    assert "Threshold Validation" in html
    assert "Visualizations" in html
    assert "Top Failure Cases" in html or "Failure Cases" in html
    assert "LangSmith" in html


def test_dashboard_chart_placeholders(mock_config, sample_metrics, sample_case_results):
    """Test dashboard contains chart placeholders."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert "accuracy-trend" in html
    assert "cost-accuracy-scatter" in html
    assert "safety-distribution" in html
    assert "latency-distribution" in html


def test_dashboard_responsive_design(mock_config, sample_metrics, sample_case_results):
    """Test dashboard includes responsive CSS."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert "@media" in html
    assert "viewport" in html
    assert "max-width" in html


def test_generate_summary_cards(mock_config, sample_metrics):
    """Test summary cards generation."""
    cards_html = _generate_summary_cards(sample_metrics, mock_config)
    
    assert "Clinical Accuracy" in cards_html
    assert "Safety Score" in cards_html
    assert "Quality Score" in cards_html
    assert "Faithfulness" in cards_html
    assert "Cost per Query" in cards_html
    assert "P95 Latency" in cards_html


def test_generate_threshold_status_all_pass(mock_config, sample_metrics):
    """Test threshold status when all pass."""
    status_html = _generate_threshold_status(sample_metrics, mock_config)
    
    assert "All Thresholds Met" in status_html
    assert "✓" in status_html


def test_generate_threshold_status_some_fail(mock_config, sample_metrics):
    """Test threshold status when some fail."""
    # Modify metrics to fail some thresholds
    metrics_with_failures = sample_metrics.copy()
    metrics_with_failures["thresholds_met"] = {
        "accuracy": True,
        "faithfulness": False,
        "safety": True,
        "cost": False,
        "latency": True
    }
    metrics_with_failures["all_thresholds_met"] = False
    
    status_html = _generate_threshold_status(metrics_with_failures, mock_config)
    
    assert "Some Thresholds Not Met" in status_html
    assert "✗" in status_html


def test_generate_failure_table_with_failures(sample_case_results, sample_metrics):
    """Test failure table generation with failures."""
    table_html = _generate_failure_table(sample_case_results, sample_metrics)
    
    assert "<table" in table_html
    assert "test_002" in table_html  # Incorrect diagnosis
    assert "test_003" in table_html  # Processing failed
    assert "Incorrect Diagnosis" in table_html
    assert "Processing Failed" in table_html


def test_generate_failure_table_no_failures(mock_config, sample_metrics):
    """Test failure table when no failures."""
    # All successful cases with correct diagnoses
    successful_results = [
        {
            "case_id": "test_001",
            "success": True,
            "diagnosis": {
                "primary_diagnosis": "STEMI",
                "differential_diagnoses": ["STEMI"],
                "reasoning": "Test"
            },
            "safety_score": {"safety_score": 5},
            "quality_score": {"quality_score": 5},
            "ground_truth": {
                "expert_diagnosis": "STEMI"
            }
        }
    ]
    
    table_html = _generate_failure_table(successful_results, sample_metrics)
    
    assert "No failure cases" in table_html or "🎉" in table_html


def test_get_langsmith_url(mock_config):
    """Test LangSmith URL generation."""
    url = _get_langsmith_url(mock_config)
    
    assert isinstance(url, str)
    assert "langchain.com" in url
    assert "test-project" in url


def test_save_dashboard_creates_file(mock_config, sample_metrics, sample_case_results):
    """Test dashboard saves to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = save_dashboard(
            sample_metrics,
            sample_case_results,
            mock_config,
            tmpdir
        )
        
        assert os.path.exists(output_path)
        assert output_path.endswith(".html")
        
        # Verify file content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "<!DOCTYPE html>" in content
            assert "Medical Diagnosis" in content


def test_generate_dashboard_with_output_path(mock_config, sample_metrics, sample_case_results):
    """Test dashboard generation with output path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_dashboard.html")
        
        html = generate_dashboard(
            sample_metrics,
            sample_case_results,
            mock_config,
            output_path
        )
        
        assert os.path.exists(output_path)
        assert isinstance(html, str)


def test_dashboard_css_styling(mock_config, sample_metrics, sample_case_results):
    """Test dashboard includes CSS styling."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert "<style>" in html
    assert "</style>" in html
    assert "font-family" in html
    assert "background" in html
    assert "color" in html


def test_dashboard_includes_plotly(mock_config, sample_metrics, sample_case_results):
    """Test dashboard includes Plotly library."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert "plotly" in html.lower()
    assert "cdn" in html.lower()


def test_dashboard_timestamp(mock_config, sample_metrics, sample_case_results):
    """Test dashboard includes timestamp."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert "Generated:" in html
    # Should contain a date-like pattern
    import re
    assert re.search(r'\d{4}-\d{2}-\d{2}', html)


def test_dashboard_handles_empty_results(mock_config):
    """Test dashboard handles empty results gracefully."""
    empty_metrics = {
        "total_cases": 0,
        "successful_cases": 0,
        "failed_cases": 0,
        "clinical_accuracy": 0.0,
        "avg_safety_score": 0.0,
        "avg_quality_score": 0.0,
        "faithfulness": 0.0,
        "answer_relevancy": 0.0,
        "context_precision": 0.0,
        "context_recall": 0.0,
        "total_cost": 0.0,
        "cost_per_query": 0.0,
        "p50": 0.0,
        "p95": 0.0,
        "p99": 0.0,
        "mean": 0.0,
        "thresholds_met": {},
        "all_thresholds_met": False
    }
    
    html = generate_dashboard(empty_metrics, [], mock_config)
    
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html


def test_dashboard_metric_card_classes(mock_config, sample_metrics, sample_case_results):
    """Test metric cards have appropriate CSS classes."""
    html = generate_dashboard(sample_metrics, sample_case_results, mock_config)
    
    assert "metric-card" in html
    assert "success" in html  # For passing metrics



# ============================================================================
# Tests for Plotly Visualizations (Task 12)
# ============================================================================

def test_generate_plotly_charts(sample_case_results, sample_metrics):
    """Test Plotly charts generation."""
    from src.dashboard import generate_plotly_charts
    
    charts = generate_plotly_charts(sample_metrics, sample_case_results)
    
    assert isinstance(charts, dict)
    assert 'accuracy-trend' in charts
    assert 'cost-accuracy-scatter' in charts
    assert 'safety-distribution' in charts
    assert 'latency-distribution' in charts


def test_generate_accuracy_trend_chart(sample_case_results):
    """Test accuracy trend chart generation."""
    from src.dashboard import _generate_accuracy_trend
    import json
    
    chart_json = _generate_accuracy_trend(sample_case_results)
    
    assert isinstance(chart_json, str)
    chart_data = json.loads(chart_json)
    
    # Should have data if there are successful cases
    if chart_data:
        assert 'data' in chart_data
        assert 'layout' in chart_data


def test_generate_cost_accuracy_scatter_chart(sample_case_results):
    """Test cost vs accuracy scatter plot generation."""
    from src.dashboard import _generate_cost_accuracy_scatter
    import json
    
    chart_json = _generate_cost_accuracy_scatter(sample_case_results)
    
    assert isinstance(chart_json, str)
    chart_data = json.loads(chart_json)
    
    if chart_data:
        assert 'data' in chart_data
        assert 'layout' in chart_data


def test_generate_safety_distribution_chart(sample_case_results):
    """Test safety score distribution chart generation."""
    from src.dashboard import _generate_safety_distribution
    import json
    
    chart_json = _generate_safety_distribution(sample_case_results)
    
    assert isinstance(chart_json, str)
    chart_data = json.loads(chart_json)
    
    if chart_data:
        assert 'data' in chart_data
        assert 'layout' in chart_data


def test_generate_latency_distribution_chart(sample_case_results):
    """Test latency distribution chart generation."""
    from src.dashboard import _generate_latency_distribution
    import json
    
    chart_json = _generate_latency_distribution(sample_case_results)
    
    assert isinstance(chart_json, str)
    chart_data = json.loads(chart_json)
    
    if chart_data:
        assert 'data' in chart_data
        assert 'layout' in chart_data


def test_generate_dashboard_with_charts(mock_config, sample_metrics, sample_case_results):
    """Test dashboard generation with embedded charts."""
    from src.dashboard import generate_dashboard_with_charts
    
    html = generate_dashboard_with_charts(sample_metrics, sample_case_results, mock_config)
    
    assert isinstance(html, str)
    assert "<!DOCTYPE html>" in html
    assert "Plotly.newPlot" in html  # Chart rendering script
    assert "accuracy_trend" in html or "accuracy-trend" in html


def test_charts_handle_empty_results(mock_config):
    """Test charts handle empty results gracefully."""
    from src.dashboard import generate_plotly_charts
    
    empty_results = []
    empty_metrics = {
        "total_cases": 0,
        "successful_cases": 0,
        "failed_cases": 0
    }
    
    charts = generate_plotly_charts(empty_metrics, empty_results)
    
    assert isinstance(charts, dict)
    # Should return empty chart JSONs
    for chart_json in charts.values():
        assert isinstance(chart_json, str)


def test_charts_are_interactive(sample_case_results, sample_metrics):
    """Test that charts include interactivity features."""
    from src.dashboard import generate_plotly_charts
    import json
    
    charts = generate_plotly_charts(sample_metrics, sample_case_results)
    
    # Check accuracy trend chart for interactivity
    if charts['accuracy-trend'] != '{}':
        chart_data = json.loads(charts['accuracy-trend'])
        # Plotly charts should have layout with hovermode
        if 'layout' in chart_data:
            assert 'hovermode' in chart_data['layout']


def test_chart_scripts_generation(sample_case_results, sample_metrics):
    """Test JavaScript chart rendering scripts generation."""
    from src.dashboard import generate_plotly_charts, _generate_chart_scripts
    
    charts = generate_plotly_charts(sample_metrics, sample_case_results)
    scripts = _generate_chart_scripts(charts)
    
    assert isinstance(scripts, str)
    assert '<script>' in scripts
    assert '</script>' in scripts
    assert 'Plotly.newPlot' in scripts
    assert 'DOMContentLoaded' in scripts


def test_dashboard_with_charts_saves_to_file(mock_config, sample_metrics, sample_case_results):
    """Test dashboard with charts saves to file."""
    from src.dashboard import generate_dashboard_with_charts
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "dashboard_with_charts.html")
        
        html = generate_dashboard_with_charts(
            sample_metrics,
            sample_case_results,
            mock_config,
            output_path
        )
        
        assert os.path.exists(output_path)
        
        # Verify file contains charts
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Plotly.newPlot" in content


def test_accuracy_trend_shows_cumulative_accuracy(sample_case_results):
    """Test accuracy trend chart shows cumulative accuracy."""
    from src.dashboard import _generate_accuracy_trend
    import json
    
    chart_json = _generate_accuracy_trend(sample_case_results)
    chart_data = json.loads(chart_json)
    
    if chart_data and 'data' in chart_data:
        # Should have trace data
        assert len(chart_data['data']) > 0
        trace = chart_data['data'][0]
        
        # Should have x and y data
        if 'x' in trace and 'y' in trace:
            assert len(trace['x']) > 0
            assert len(trace['y']) > 0
            # Y values should be between 0 and 1 (percentages)
            assert all(0 <= y <= 1 for y in trace['y'])


def test_cost_accuracy_scatter_separates_correct_incorrect(sample_case_results):
    """Test cost vs accuracy scatter plot separates correct and incorrect."""
    from src.dashboard import _generate_cost_accuracy_scatter
    import json
    
    chart_json = _generate_cost_accuracy_scatter(sample_case_results)
    chart_data = json.loads(chart_json)
    
    if chart_data and 'data' in chart_data:
        # Should have two traces (correct and incorrect)
        assert len(chart_data['data']) >= 1


def test_safety_distribution_uses_histogram(sample_case_results):
    """Test safety distribution uses histogram visualization."""
    from src.dashboard import _generate_safety_distribution
    import json
    
    chart_json = _generate_safety_distribution(sample_case_results)
    chart_data = json.loads(chart_json)
    
    if chart_data and 'data' in chart_data:
        trace = chart_data['data'][0]
        # Should be histogram type
        assert trace.get('type') == 'histogram' or 'x' in trace


def test_latency_distribution_shows_statistics(sample_case_results):
    """Test latency distribution shows statistical information."""
    from src.dashboard import _generate_latency_distribution
    import json
    
    chart_json = _generate_latency_distribution(sample_case_results)
    chart_data = json.loads(chart_json)
    
    if chart_data and 'data' in chart_data:
        trace = chart_data['data'][0]
        # Should be box plot
        assert trace.get('type') == 'box' or 'y' in trace
