"""Tests for metrics calculator."""

import pytest
import numpy as np

from src.metrics import (
    calculate_clinical_accuracy,
    calculate_cost_metrics,
    calculate_latency_metrics,
    aggregate_scores,
    calculate_pass_rate,
    get_model_pricing,
    API_PRICING
)


class TestClinicalAccuracy:
    """Tests for clinical accuracy calculation."""
    
    def test_perfect_accuracy(self):
        """Test 100% accuracy."""
        predictions = [
            ["STEMI", "Unstable Angina"],
            ["Pneumonia", "Bronchitis"]
        ]
        ground_truths = ["STEMI", "Pneumonia"]
        
        accuracy = calculate_clinical_accuracy(predictions, ground_truths, top_k=3)
        assert accuracy == 1.0
    
    def test_zero_accuracy(self):
        """Test 0% accuracy."""
        predictions = [
            ["Wrong1", "Wrong2"],
            ["Wrong3", "Wrong4"]
        ]
        ground_truths = ["Correct1", "Correct2"]
        
        accuracy = calculate_clinical_accuracy(predictions, ground_truths, top_k=3)
        assert accuracy == 0.0
    
    def test_partial_accuracy(self):
        """Test partial accuracy."""
        predictions = [
            ["STEMI", "Angina"],  # Correct
            ["Wrong", "Wrong2"],  # Incorrect
            ["Pneumonia", "Flu"]  # Correct
        ]
        ground_truths = ["STEMI", "Correct", "Pneumonia"]
        
        accuracy = calculate_clinical_accuracy(predictions, ground_truths, top_k=3)
        assert accuracy == pytest.approx(2/3)
    
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        predictions = [["stemi", "ANGINA"]]
        ground_truths = ["STEMI"]
        
        accuracy = calculate_clinical_accuracy(predictions, ground_truths)
        assert accuracy == 1.0
    
    def test_top_k_filtering(self):
        """Test that only top-k predictions are considered."""
        predictions = [
            ["Wrong1", "Wrong2", "Wrong3", "Correct"]  # Correct is 4th
        ]
        ground_truths = ["Correct"]
        
        # With top_k=3, should not find it
        accuracy = calculate_clinical_accuracy(predictions, ground_truths, top_k=3)
        assert accuracy == 0.0
        
        # With top_k=4, should find it
        accuracy = calculate_clinical_accuracy(predictions, ground_truths, top_k=4)
        assert accuracy == 1.0
    
    def test_empty_lists(self):
        """Test handling of empty lists."""
        accuracy = calculate_clinical_accuracy([], [], top_k=3)
        assert accuracy == 0.0
    
    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise error."""
        predictions = [["A"], ["B"]]
        ground_truths = ["A"]
        
        with pytest.raises(ValueError, match="same length"):
            calculate_clinical_accuracy(predictions, ground_truths)


class TestCostMetrics:
    """Tests for cost metrics calculation."""
    
    def test_cost_calculation_with_split_tokens(self):
        """Test cost calculation with input/output tokens."""
        traces = [
            {
                "model": "gpt-4o",
                "input_tokens": 1000,
                "output_tokens": 500
            }
        ]
        
        metrics = calculate_cost_metrics(traces)
        
        # Cost = (1000/1M * 2.50) + (500/1M * 10.00)
        expected_cost = (1000/1_000_000 * 2.50) + (500/1_000_000 * 10.00)
        assert metrics["total_cost"] == pytest.approx(expected_cost, abs=0.0001)
        assert metrics["cost_per_query"] == pytest.approx(expected_cost, abs=0.0001)
        assert metrics["total_input_tokens"] == 1000
        assert metrics["total_output_tokens"] == 500
    
    def test_cost_calculation_with_total_tokens(self):
        """Test cost calculation with only total tokens."""
        traces = [
            {
                "model": "gpt-4o",
                "tokens_used": 1000
            }
        ]
        
        metrics = calculate_cost_metrics(traces)
        
        # Should estimate 60/40 split
        assert metrics["total_input_tokens"] == 600
        assert metrics["total_output_tokens"] == 400
        assert metrics["total_cost"] > 0
    
    def test_multiple_traces(self):
        """Test cost calculation across multiple traces."""
        traces = [
            {"model": "gpt-4o", "input_tokens": 1000, "output_tokens": 500},
            {"model": "gpt-4o", "input_tokens": 2000, "output_tokens": 1000}
        ]
        
        metrics = calculate_cost_metrics(traces)
        
        assert metrics["total_input_tokens"] == 3000
        assert metrics["total_output_tokens"] == 1500
        assert metrics["cost_per_query"] == pytest.approx(metrics["total_cost"] / 2, abs=0.0001)
    
    def test_unknown_model_uses_default_pricing(self):
        """Test that unknown models use default pricing."""
        traces = [
            {"model": "unknown-model", "input_tokens": 1000, "output_tokens": 500}
        ]
        
        metrics = calculate_cost_metrics(traces)
        
        # Should use default pricing
        assert metrics["total_cost"] > 0
    
    def test_empty_traces(self):
        """Test handling of empty traces."""
        metrics = calculate_cost_metrics([])
        
        assert metrics["total_cost"] == 0.0
        assert metrics["cost_per_query"] == 0.0
        assert metrics["total_tokens"] == 0


class TestLatencyMetrics:
    """Tests for latency metrics calculation."""
    
    def test_latency_percentiles(self):
        """Test latency percentile calculations."""
        latencies = [100, 200, 300, 400, 500]
        
        metrics = calculate_latency_metrics(latencies)
        
        assert metrics["p50"] == 300.0  # Median
        assert metrics["mean"] == 300.0
        assert metrics["min"] == 100.0
        assert metrics["max"] == 500.0
        assert metrics["p95"] > metrics["p50"]
        assert metrics["p99"] > metrics["p95"]
    
    def test_single_latency(self):
        """Test with single latency value."""
        latencies = [250.5]
        
        metrics = calculate_latency_metrics(latencies)
        
        assert metrics["p50"] == 250.5
        assert metrics["p95"] == 250.5
        assert metrics["p99"] == 250.5
        assert metrics["mean"] == 250.5
    
    def test_empty_latencies(self):
        """Test handling of empty latencies."""
        metrics = calculate_latency_metrics([])
        
        assert metrics["p50"] == 0.0
        assert metrics["p95"] == 0.0
        assert metrics["mean"] == 0.0


class TestAggregateScores:
    """Tests for score aggregation."""
    
    def test_aggregate_scores(self):
        """Test score aggregation."""
        scores = [0.8, 0.9, 0.85, 0.75, 0.95]
        
        metrics = aggregate_scores(scores)
        
        assert metrics["mean"] == pytest.approx(0.85, abs=0.01)
        assert metrics["median"] == 0.85
        assert metrics["min"] == 0.75
        assert metrics["max"] == 0.95
        assert metrics["std"] > 0
    
    def test_empty_scores(self):
        """Test handling of empty scores."""
        metrics = aggregate_scores([])
        
        assert metrics["mean"] == 0.0
        assert metrics["median"] == 0.0


class TestPassRate:
    """Tests for pass rate calculation."""
    
    def test_all_pass(self):
        """Test 100% pass rate."""
        scores = [0.8, 0.9, 0.85]
        pass_rate = calculate_pass_rate(scores, threshold=0.75)
        
        assert pass_rate == 1.0
    
    def test_none_pass(self):
        """Test 0% pass rate."""
        scores = [0.5, 0.6, 0.7]
        pass_rate = calculate_pass_rate(scores, threshold=0.75)
        
        assert pass_rate == 0.0
    
    def test_partial_pass(self):
        """Test partial pass rate."""
        scores = [0.8, 0.7, 0.9, 0.6]
        pass_rate = calculate_pass_rate(scores, threshold=0.75)
        
        assert pass_rate == 0.5  # 2 out of 4
    
    def test_empty_scores(self):
        """Test handling of empty scores."""
        pass_rate = calculate_pass_rate([], threshold=0.75)
        assert pass_rate == 0.0


class TestModelPricing:
    """Tests for model pricing lookup."""
    
    def test_get_known_model_pricing(self):
        """Test getting pricing for known model."""
        pricing = get_model_pricing("gpt-4o")
        
        assert "input" in pricing
        assert "output" in pricing
        assert pricing["input"] > 0
        assert pricing["output"] > 0
    
    def test_get_unknown_model_pricing(self):
        """Test getting pricing for unknown model."""
        pricing = get_model_pricing("unknown-model")
        
        assert pricing == API_PRICING["default"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
