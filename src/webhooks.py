"""Webhook integration for CI/CD and monitoring systems.

This module provides functionality to send evaluation results to webhook endpoints,
supporting both generic HTTP webhooks and Slack-specific formatting.
"""

import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime


def send_webhook(
    webhook_url: str,
    metrics: Dict[str, Any],
    config: Any,
    dashboard_url: Optional[str] = None,
    webhook_type: str = "generic"
) -> bool:
    """Send evaluation results to a webhook endpoint.
    
    Args:
        webhook_url: URL of the webhook endpoint
        metrics: Evaluation metrics dictionary
        config: Evaluation configuration
        dashboard_url: Optional URL to the dashboard
        webhook_type: Type of webhook ("generic" or "slack")
        
    Returns:
        True if webhook sent successfully, False otherwise
    """
    try:
        if webhook_type.lower() == "slack":
            payload = format_slack_payload(metrics, config, dashboard_url)
        else:
            payload = format_generic_payload(metrics, config, dashboard_url)
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        
        print(f"✓ Webhook sent successfully to {webhook_url}")
        return True
        
    except requests.exceptions.Timeout:
        print(f"✗ Webhook timeout: {webhook_url}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Webhook failed: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error sending webhook: {str(e)}")
        return False


def format_generic_payload(
    metrics: Dict[str, Any],
    config: Any,
    dashboard_url: Optional[str] = None
) -> Dict[str, Any]:
    """Format payload for generic HTTP webhook.
    
    Args:
        metrics: Evaluation metrics
        config: Evaluation configuration
        dashboard_url: Optional dashboard URL
        
    Returns:
        Formatted payload dictionary
    """
    timestamp = datetime.now().isoformat()
    
    # Determine pass/fail status
    all_thresholds_met = metrics.get("all_thresholds_met", False)
    status = "PASS" if all_thresholds_met else "FAIL"
    
    # Build payload
    payload = {
        "timestamp": timestamp,
        "status": status,
        "model": {
            "name": config.model.model_name,
            "provider": config.model.provider
        },
        "metrics": {
            "clinical_accuracy": metrics.get("clinical_accuracy", 0),
            "avg_safety_score": metrics.get("avg_safety_score", 0),
            "avg_quality_score": metrics.get("avg_quality_score", 0),
            "faithfulness": metrics.get("faithfulness", 0),
            "answer_relevancy": metrics.get("answer_relevancy", 0),
            "cost_per_query": metrics.get("cost_per_query", 0),
            "p95_latency": metrics.get("p95", 0)
        },
        "summary": {
            "total_cases": metrics.get("total_cases", 0),
            "successful_cases": metrics.get("successful_cases", 0),
            "failed_cases": metrics.get("failed_cases", 0)
        },
        "thresholds": {
            "accuracy_met": metrics.get("thresholds_met", {}).get("accuracy", False),
            "faithfulness_met": metrics.get("thresholds_met", {}).get("faithfulness", False),
            "safety_met": metrics.get("thresholds_met", {}).get("safety", False),
            "cost_met": metrics.get("thresholds_met", {}).get("cost", False),
            "latency_met": metrics.get("thresholds_met", {}).get("latency", False)
        }
    }
    
    if dashboard_url:
        payload["dashboard_url"] = dashboard_url
    
    return payload


def format_slack_payload(
    metrics: Dict[str, Any],
    config: Any,
    dashboard_url: Optional[str] = None
) -> Dict[str, Any]:
    """Format payload for Slack webhook with rich formatting.
    
    Args:
        metrics: Evaluation metrics
        config: Evaluation configuration
        dashboard_url: Optional dashboard URL
        
    Returns:
        Slack-formatted payload dictionary
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine pass/fail status
    all_thresholds_met = metrics.get("all_thresholds_met", False)
    status = "PASS" if all_thresholds_met else "FAIL"
    status_emoji = "✅" if all_thresholds_met else "❌"
    color = "good" if all_thresholds_met else "danger"
    
    # Build metric fields
    fields = [
        {
            "title": "Clinical Accuracy",
            "value": f"{metrics.get('clinical_accuracy', 0):.1%}",
            "short": True
        },
        {
            "title": "Avg Safety Score",
            "value": f"{metrics.get('avg_safety_score', 0):.2f}/5.0",
            "short": True
        },
        {
            "title": "Faithfulness",
            "value": f"{metrics.get('faithfulness', 0):.3f}",
            "short": True
        },
        {
            "title": "Cost per Query",
            "value": f"${metrics.get('cost_per_query', 0):.4f}",
            "short": True
        },
        {
            "title": "P95 Latency",
            "value": f"{metrics.get('p95', 0):.0f}ms",
            "short": True
        },
        {
            "title": "Cases Evaluated",
            "value": f"{metrics.get('successful_cases', 0)}/{metrics.get('total_cases', 0)}",
            "short": True
        }
    ]
    
    # Build threshold status
    thresholds = metrics.get("thresholds_met", {})
    threshold_text = []
    for name, met in thresholds.items():
        emoji = "✓" if met else "✗"
        threshold_text.append(f"{emoji} {name.replace('_', ' ').title()}")
    
    # Build attachment
    attachment = {
        "color": color,
        "title": f"{status_emoji} Medical Diagnosis Evaluation {status}",
        "text": f"Model: *{config.model.model_name}* ({config.model.provider})",
        "fields": fields,
        "footer": f"Thresholds: {' | '.join(threshold_text)}",
        "ts": int(datetime.now().timestamp())
    }
    
    # Add dashboard link if available
    if dashboard_url:
        attachment["actions"] = [
            {
                "type": "button",
                "text": "View Dashboard",
                "url": dashboard_url
            }
        ]
    
    payload = {
        "text": f"Evaluation completed at {timestamp}",
        "attachments": [attachment]
    }
    
    return payload


def send_evaluation_webhook(
    webhook_url: str,
    results: Any,
    dashboard_url: Optional[str] = None,
    webhook_type: str = "generic"
) -> bool:
    """Send evaluation results to webhook (convenience function).
    
    Args:
        webhook_url: Webhook endpoint URL
        results: EvaluationResults object
        dashboard_url: Optional dashboard URL
        webhook_type: Type of webhook ("generic" or "slack")
        
    Returns:
        True if successful, False otherwise
    """
    return send_webhook(
        webhook_url=webhook_url,
        metrics=results.metrics,
        config=results.config,
        dashboard_url=dashboard_url,
        webhook_type=webhook_type
    )


def check_webhook_connectivity(webhook_url: str, webhook_type: str = "generic") -> bool:
    """Test webhook connectivity with a simple message.
    
    Args:
        webhook_url: Webhook endpoint URL
        webhook_type: Type of webhook ("generic" or "slack")
        
    Returns:
        True if webhook is reachable, False otherwise
    """
    try:
        if webhook_type.lower() == "slack":
            payload = {
                "text": "🔔 Test message from Medical Diagnosis Evaluator",
                "attachments": [
                    {
                        "color": "good",
                        "text": "Webhook connection successful!",
                        "footer": "Medical Diagnosis Evaluator",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
        else:
            payload = {
                "message": "Test message from Medical Diagnosis Evaluator",
                "timestamp": datetime.now().isoformat(),
                "status": "test"
            }
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        
        print(f"✓ Webhook test successful: {webhook_url}")
        return True
        
    except Exception as e:
        print(f"✗ Webhook test failed: {str(e)}")
        return False


def format_failure_summary(case_results: list) -> str:
    """Format a summary of failed cases for webhook notification.
    
    Args:
        case_results: List of case results
        
    Returns:
        Formatted failure summary string
    """
    failed_cases = [r for r in case_results if not r.get("success", False)]
    
    if not failed_cases:
        return "No failures"
    
    summary_lines = [f"Failed {len(failed_cases)} cases:"]
    
    for i, case in enumerate(failed_cases[:5], 1):  # Show first 5 failures
        case_id = case.get("case_id", "unknown")
        error = case.get("error", "Unknown error")
        summary_lines.append(f"{i}. {case_id}: {error[:50]}...")
    
    if len(failed_cases) > 5:
        summary_lines.append(f"... and {len(failed_cases) - 5} more")
    
    return "\n".join(summary_lines)
