"""Tests for webhook integration."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.webhooks import (
    send_webhook,
    format_generic_payload,
    format_slack_payload,
    send_evaluation_webhook,
    check_webhook_connectivity,
    format_failure_summary
)
from src.config import ModelConfig


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock()
    config.model = ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        temperature=0.7,
        max_tokens=2000
    )
    return config


@pytest.fixture
def sample_metrics():
    """Create sample metrics."""
    return {
        "clinical_accuracy": 0.85,
        "avg_safety_score": 4.5,
        "avg_quality_score": 4.3,
        "faithfulness": 0.82,
        "answer_relevancy": 0.88,
        "cost_per_query": 0.045,
        "p95": 1500.0,
        "total_cases": 100,
        "successful_cases": 98,
        "failed_cases": 2,
        "all_thresholds_met": True,
        "thresholds_met": {
            "accuracy": True,
            "faithfulness": True,
            "safety": True,
            "cost": True,
            "latency": True
        }
    }


def test_format_generic_payload(sample_metrics, mock_config):
    """Test formatting generic webhook payload."""
    payload = format_generic_payload(sample_metrics, mock_config, "http://dashboard.example.com")
    
    assert "timestamp" in payload
    assert payload["status"] == "PASS"
    assert payload["model"]["name"] == "gpt-4o"
    assert payload["model"]["provider"] == "openai"
    assert payload["metrics"]["clinical_accuracy"] == 0.85
    assert payload["metrics"]["cost_per_query"] == 0.045
    assert payload["summary"]["total_cases"] == 100
    assert payload["summary"]["successful_cases"] == 98
    assert payload["summary"]["failed_cases"] == 2
    assert payload["dashboard_url"] == "http://dashboard.example.com"
    assert payload["thresholds"]["accuracy_met"] is True


def test_format_generic_payload_fail_status(mock_config):
    """Test generic payload with failed status."""
    metrics = {
        "clinical_accuracy": 0.65,
        "all_thresholds_met": False,
        "thresholds_met": {"accuracy": False}
    }
    
    payload = format_generic_payload(metrics, mock_config)
    
    assert payload["status"] == "FAIL"
    assert payload["thresholds"]["accuracy_met"] is False


def test_format_slack_payload(sample_metrics, mock_config):
    """Test formatting Slack webhook payload."""
    payload = format_slack_payload(sample_metrics, mock_config, "http://dashboard.example.com")
    
    assert "text" in payload
    assert "attachments" in payload
    assert len(payload["attachments"]) == 1
    
    attachment = payload["attachments"][0]
    assert attachment["color"] == "good"
    assert "✅" in attachment["title"]
    assert "PASS" in attachment["title"]
    assert "gpt-4o" in attachment["text"]
    assert len(attachment["fields"]) == 6
    
    # Check fields
    field_titles = [f["title"] for f in attachment["fields"]]
    assert "Clinical Accuracy" in field_titles
    assert "Avg Safety Score" in field_titles
    assert "Cost per Query" in field_titles
    
    # Check dashboard link
    assert "actions" in attachment
    assert attachment["actions"][0]["url"] == "http://dashboard.example.com"


def test_format_slack_payload_fail_status(mock_config):
    """Test Slack payload with failed status."""
    metrics = {
        "clinical_accuracy": 0.65,
        "avg_safety_score": 3.5,
        "faithfulness": 0.70,
        "cost_per_query": 0.15,
        "p95": 4000.0,
        "total_cases": 100,
        "successful_cases": 95,
        "failed_cases": 5,
        "all_thresholds_met": False,
        "thresholds_met": {
            "accuracy": False,
            "faithfulness": False,
            "safety": True,
            "cost": False,
            "latency": False
        }
    }
    
    payload = format_slack_payload(metrics, mock_config)
    
    attachment = payload["attachments"][0]
    assert attachment["color"] == "danger"
    assert "❌" in attachment["title"]
    assert "FAIL" in attachment["title"]
    assert "✗" in attachment["footer"]  # Failed thresholds


@patch('src.webhooks.requests.post')
def test_send_webhook_success(mock_post, sample_metrics, mock_config):
    """Test successful webhook delivery."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    result = send_webhook(
        webhook_url="http://webhook.example.com",
        metrics=sample_metrics,
        config=mock_config,
        webhook_type="generic"
    )
    
    assert result is True
    assert mock_post.called
    assert mock_post.call_args[0][0] == "http://webhook.example.com"


@patch('src.webhooks.requests.post')
def test_send_webhook_timeout(mock_post, sample_metrics, mock_config):
    """Test webhook timeout handling."""
    import requests
    mock_post.side_effect = requests.exceptions.Timeout()
    
    result = send_webhook(
        webhook_url="http://webhook.example.com",
        metrics=sample_metrics,
        config=mock_config
    )
    
    assert result is False


@patch('src.webhooks.requests.post')
def test_send_webhook_request_error(mock_post, sample_metrics, mock_config):
    """Test webhook request error handling."""
    import requests
    mock_post.side_effect = requests.exceptions.RequestException("Connection error")
    
    result = send_webhook(
        webhook_url="http://webhook.example.com",
        metrics=sample_metrics,
        config=mock_config
    )
    
    assert result is False


@patch('src.webhooks.requests.post')
def test_send_webhook_slack_type(mock_post, sample_metrics, mock_config):
    """Test sending Slack-formatted webhook."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    result = send_webhook(
        webhook_url="http://hooks.slack.com/services/XXX",
        metrics=sample_metrics,
        config=mock_config,
        webhook_type="slack"
    )
    
    assert result is True
    
    # Verify Slack-formatted payload was sent
    call_args = mock_post.call_args
    payload = call_args[1]["json"]
    assert "attachments" in payload


@patch('src.webhooks.requests.post')
def test_send_evaluation_webhook(mock_post, sample_metrics, mock_config):
    """Test convenience function for sending evaluation webhook."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    # Create mock results
    mock_results = Mock()
    mock_results.metrics = sample_metrics
    mock_results.config = mock_config
    
    result = send_evaluation_webhook(
        webhook_url="http://webhook.example.com",
        results=mock_results,
        dashboard_url="http://dashboard.example.com"
    )
    
    assert result is True


@patch('src.webhooks.requests.post')
def test_check_webhook_connectivity_generic(mock_post):
    """Test webhook connectivity test with generic format."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    result = check_webhook_connectivity("http://webhook.example.com", "generic")
    
    assert result is True
    assert mock_post.called
    
    # Verify test payload
    payload = mock_post.call_args[1]["json"]
    assert "message" in payload
    assert "Test message" in payload["message"]


@patch('src.webhooks.requests.post')
def test_check_webhook_connectivity_slack(mock_post):
    """Test webhook connectivity test with Slack format."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response
    
    result = check_webhook_connectivity("http://hooks.slack.com/services/XXX", "slack")
    
    assert result is True
    
    # Verify Slack test payload
    payload = mock_post.call_args[1]["json"]
    assert "text" in payload
    assert "attachments" in payload


@patch('src.webhooks.requests.post')
def test_check_webhook_connectivity_failure(mock_post):
    """Test webhook connectivity test failure."""
    import requests
    mock_post.side_effect = requests.exceptions.ConnectionError()
    
    result = check_webhook_connectivity("http://webhook.example.com")
    
    assert result is False


def test_format_failure_summary():
    """Test formatting failure summary."""
    case_results = [
        {"case_id": "case_001", "success": True},
        {"case_id": "case_002", "success": False, "error": "API timeout"},
        {"case_id": "case_003", "success": True},
        {"case_id": "case_004", "success": False, "error": "Invalid response format"},
        {"case_id": "case_005", "success": False, "error": "Model returned empty diagnosis"}
    ]
    
    summary = format_failure_summary(case_results)
    
    assert "Failed 3 cases" in summary
    assert "case_002" in summary
    assert "case_004" in summary
    assert "case_005" in summary
    assert "API timeout" in summary


def test_format_failure_summary_no_failures():
    """Test failure summary with no failures."""
    case_results = [
        {"case_id": "case_001", "success": True},
        {"case_id": "case_002", "success": True}
    ]
    
    summary = format_failure_summary(case_results)
    
    assert summary == "No failures"


def test_format_failure_summary_many_failures():
    """Test failure summary with many failures (should truncate)."""
    case_results = [
        {"case_id": f"case_{i:03d}", "success": False, "error": f"Error {i}"}
        for i in range(10)
    ]
    
    summary = format_failure_summary(case_results)
    
    assert "Failed 10 cases" in summary
    assert "and 5 more" in summary  # Should show first 5 and indicate more
