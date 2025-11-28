"""Metrics calculation for evaluation results.

This module provides functions for calculating:
- Clinical accuracy (top-k matching)
- Cost metrics from token usage
- Latency metrics (percentiles)
"""

from typing import List, Dict, Any, Optional
import numpy as np


# API pricing data (per 1M tokens) - Updated as of Jan 2024
API_PRICING = {
    "gpt-4o": {
        "input": 2.50,  # $2.50 per 1M input tokens
        "output": 10.00  # $10.00 per 1M output tokens
    },
    "gpt-4-turbo": {
        "input": 10.00,
        "output": 30.00
    },
    "gpt-3.5-turbo": {
        "input": 0.50,
        "output": 1.50
    },
    "claude-3-5-sonnet-20241022": {
        "input": 3.00,
        "output": 15.00
    },
    "claude-3-opus": {
        "input": 15.00,
        "output": 75.00
    },
    "claude-3-sonnet": {
        "input": 3.00,
        "output": 15.00
    },
    "claude-3-haiku": {
        "input": 0.25,
        "output": 1.25
    },
    # Default pricing for unknown models
    "default": {
        "input": 5.00,
        "output": 15.00
    }
}


def calculate_clinical_accuracy(
    predictions: List[List[str]],
    ground_truths: List[str],
    top_k: int = 3
) -> float:
    """Calculate clinical accuracy using top-k matching.
    
    Accuracy is defined as the percentage of cases where the ground truth
    diagnosis appears in the top-k predicted diagnoses.
    
    Args:
        predictions: List of prediction lists (differential diagnoses)
        ground_truths: List of ground truth diagnoses
        top_k: Number of top predictions to consider (default: 3)
        
    Returns:
        Accuracy score between 0.0 and 1.0
        
    Example:
        predictions = [["STEMI", "Unstable Angina", "Pericarditis"], ["Pneumonia"]]
        ground_truths = ["STEMI", "Pneumonia"]
        accuracy = calculate_clinical_accuracy(predictions, ground_truths, top_k=3)
        # Returns: 1.0 (both correct in top-3)
    """
    if not predictions or not ground_truths:
        return 0.0
    
    if len(predictions) != len(ground_truths):
        raise ValueError(
            f"Predictions and ground truths must have same length. "
            f"Got {len(predictions)} predictions and {len(ground_truths)} ground truths"
        )
    
    correct = 0
    for pred_list, truth in zip(predictions, ground_truths):
        # Normalize for case-insensitive comparison
        pred_list_lower = [p.lower().strip() for p in pred_list[:top_k]]
        truth_lower = truth.lower().strip()
        
        # Check if ground truth is in top-k predictions
        if truth_lower in pred_list_lower:
            correct += 1
    
    accuracy = correct / len(predictions)
    return accuracy


def calculate_cost_metrics(
    traces: List[Dict[str, Any]],
    model_name: Optional[str] = None
) -> Dict[str, float]:
    """Calculate cost metrics from token usage.
    
    Args:
        traces: List of trace dictionaries with token usage info
        model_name: Optional model name for pricing lookup
        
    Returns:
        Dictionary with cost metrics:
        - total_cost: Total cost in USD
        - cost_per_query: Average cost per query
        - total_input_tokens: Total input tokens
        - total_output_tokens: Total output tokens
        - total_tokens: Total tokens
        
    Example:
        traces = [
            {"tokens_used": 1000, "model": "gpt-4o", "input_tokens": 500, "output_tokens": 500}
        ]
        metrics = calculate_cost_metrics(traces)
    """
    if not traces:
        return {
            "total_cost": 0.0,
            "cost_per_query": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0
        }
    
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0
    
    for trace in traces:
        # Extract model name
        trace_model = trace.get("model_used") or trace.get("model") or model_name or "default"
        
        # Get pricing for model
        pricing = API_PRICING.get(trace_model, API_PRICING["default"])
        
        # Extract token counts
        input_tokens = trace.get("input_tokens", 0)
        output_tokens = trace.get("output_tokens", 0)
        
        # If not split, try to get total and estimate split (60/40)
        if input_tokens == 0 and output_tokens == 0:
            total_tokens = trace.get("tokens_used", 0)
            if total_tokens > 0:
                input_tokens = int(total_tokens * 0.6)
                output_tokens = int(total_tokens * 0.4)
        
        # Calculate cost for this trace
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        trace_cost = input_cost + output_cost
        
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        total_cost += trace_cost
    
    return {
        "total_cost": round(total_cost, 4),
        "cost_per_query": round(total_cost / len(traces), 4),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens
    }


def calculate_latency_metrics(
    latencies: List[float]
) -> Dict[str, float]:
    """Calculate latency percentiles and statistics.
    
    Args:
        latencies: List of latency values in milliseconds
        
    Returns:
        Dictionary with latency metrics:
        - p50: 50th percentile (median)
        - p95: 95th percentile
        - p99: 99th percentile
        - mean: Average latency
        - min: Minimum latency
        - max: Maximum latency
        
    Example:
        latencies = [100, 200, 150, 300, 250]
        metrics = calculate_latency_metrics(latencies)
    """
    if not latencies:
        return {
            "p50": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "mean": 0.0,
            "min": 0.0,
            "max": 0.0
        }
    
    latencies_array = np.array(latencies)
    
    return {
        "p50": round(float(np.percentile(latencies_array, 50)), 2),
        "p95": round(float(np.percentile(latencies_array, 95)), 2),
        "p99": round(float(np.percentile(latencies_array, 99)), 2),
        "mean": round(float(np.mean(latencies_array)), 2),
        "min": round(float(np.min(latencies_array)), 2),
        "max": round(float(np.max(latencies_array)), 2)
    }


def aggregate_scores(scores: List[float]) -> Dict[str, float]:
    """Aggregate a list of scores into summary statistics.
    
    Args:
        scores: List of score values
        
    Returns:
        Dictionary with aggregated metrics:
        - mean: Average score
        - median: Median score
        - std: Standard deviation
        - min: Minimum score
        - max: Maximum score
    """
    if not scores:
        return {
            "mean": 0.0,
            "median": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0
        }
    
    scores_array = np.array(scores)
    
    return {
        "mean": round(float(np.mean(scores_array)), 4),
        "median": round(float(np.median(scores_array)), 4),
        "std": round(float(np.std(scores_array)), 4),
        "min": round(float(np.min(scores_array)), 4),
        "max": round(float(np.max(scores_array)), 4)
    }


def calculate_pass_rate(
    scores: List[float],
    threshold: float
) -> float:
    """Calculate the percentage of scores that meet or exceed a threshold.
    
    Args:
        scores: List of score values
        threshold: Minimum passing score
        
    Returns:
        Pass rate between 0.0 and 1.0
    """
    if not scores:
        return 0.0
    
    passing = sum(1 for score in scores if score >= threshold)
    return passing / len(scores)


def get_model_pricing(model_name: str) -> Dict[str, float]:
    """Get pricing information for a model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Dictionary with input and output pricing per 1M tokens
    """
    return API_PRICING.get(model_name, API_PRICING["default"])
