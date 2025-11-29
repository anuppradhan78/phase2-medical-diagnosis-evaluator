"""A/B Testing Support for comparing model configurations.

This module provides functionality to run A/B tests comparing two different
model configurations on the same golden dataset and generate comparison reports.
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path
import json
from datetime import datetime
from scipy import stats
import numpy as np

from src.evaluator import Evaluator, EvaluationResults
from src.config import EvalConfig


def run_ab_test(
    config_a: EvalConfig,
    config_b: EvalConfig,
    output_dir: str = "./ab_test_results"
) -> Dict[str, Any]:
    """Run A/B test comparing two model configurations.
    
    Args:
        config_a: Configuration for model A
        config_b: Configuration for model B
        output_dir: Directory to save comparison results
        
    Returns:
        Dictionary containing:
        - results_a: Evaluation results for config A
        - results_b: Evaluation results for config B
        - comparison: Metric comparisons and statistical tests
        - timestamp: When the test was run
    """
    print("="*70)
    print("A/B Testing: Comparing Two Model Configurations")
    print("="*70)
    print()
    
    # Ensure both configs use the same dataset
    if config_a.golden_dataset_path != config_b.golden_dataset_path:
        print("⚠ Warning: Configs use different datasets. Using dataset from config A.")
        config_b.golden_dataset_path = config_a.golden_dataset_path
    
    # Run evaluation for Config A
    print("Running evaluation for Config A...")
    print(f"  Model: {config_a.model.model_name}")
    print(f"  Provider: {config_a.model.provider}")
    print()
    
    evaluator_a = Evaluator(config_a)
    results_a = evaluator_a.run_evaluation()
    
    print("\n" + "-"*70)
    print("Config A Results:")
    print(f"  Clinical Accuracy: {results_a.metrics.get('clinical_accuracy', 0):.2%}")
    print(f"  Avg Safety Score: {results_a.metrics.get('avg_safety_score', 0):.2f}/5.0")
    print(f"  Cost per Query: ${results_a.metrics.get('cost_per_query', 0):.4f}")
    print(f"  P95 Latency: {results_a.metrics.get('p95', 0):.0f}ms")
    print("-"*70)
    print()
    
    # Run evaluation for Config B
    print("Running evaluation for Config B...")
    print(f"  Model: {config_b.model.model_name}")
    print(f"  Provider: {config_b.model.provider}")
    print()
    
    evaluator_b = Evaluator(config_b)
    results_b = evaluator_b.run_evaluation()
    
    print("\n" + "-"*70)
    print("Config B Results:")
    print(f"  Clinical Accuracy: {results_b.metrics.get('clinical_accuracy', 0):.2%}")
    print(f"  Avg Safety Score: {results_b.metrics.get('avg_safety_score', 0):.2f}/5.0")
    print(f"  Cost per Query: ${results_b.metrics.get('cost_per_query', 0):.4f}")
    print(f"  P95 Latency: {results_b.metrics.get('p95', 0):.0f}ms")
    print("-"*70)
    print()
    
    # Compute comparisons
    print("Computing metric comparisons and statistical significance...")
    comparison = compute_metric_comparison(results_a, results_b)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate comparison report
    timestamp = datetime.now().isoformat()
    ab_test_results = {
        "timestamp": timestamp,
        "config_a": {
            "model": config_a.model.model_dump(),
            "judge_model": config_a.judge_model
        },
        "config_b": {
            "model": config_b.model.model_dump(),
            "judge_model": config_b.judge_model
        },
        "results_a": results_a.to_dict(),
        "results_b": results_b.to_dict(),
        "comparison": comparison
    }
    
    # Save comparison report
    report_path = output_path / f"ab_test_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(ab_test_results, f, indent=2, default=str)
    
    print(f"\n✓ A/B test comparison saved to: {report_path}")
    
    # Print summary
    print_comparison_summary(comparison)
    
    return ab_test_results


def compute_metric_comparison(
    results_a: EvaluationResults,
    results_b: EvaluationResults
) -> Dict[str, Any]:
    """Compute metric comparisons and statistical significance.
    
    Args:
        results_a: Results from config A
        results_b: Results from config B
        
    Returns:
        Dictionary with metric comparisons and statistical tests
    """
    comparison = {
        "metrics": {},
        "statistical_tests": {},
        "winner": None
    }
    
    metrics_a = results_a.metrics
    metrics_b = results_b.metrics
    
    # Compare key metrics
    key_metrics = [
        "clinical_accuracy",
        "avg_safety_score",
        "avg_quality_score",
        "faithfulness",
        "answer_relevancy",
        "cost_per_query",
        "p95"
    ]
    
    for metric in key_metrics:
        if metric in metrics_a and metric in metrics_b:
            value_a = metrics_a[metric]
            value_b = metrics_b[metric]
            
            # Calculate difference and percent change
            diff = value_b - value_a
            if value_a != 0:
                percent_change = (diff / value_a) * 100
            else:
                percent_change = 0 if diff == 0 else float('inf')
            
            # Determine if higher is better
            higher_is_better = metric not in ["cost_per_query", "p95"]
            
            comparison["metrics"][metric] = {
                "config_a": value_a,
                "config_b": value_b,
                "difference": diff,
                "percent_change": percent_change,
                "winner": "B" if (diff > 0 and higher_is_better) or (diff < 0 and not higher_is_better) else "A" if diff != 0 else "Tie"
            }
    
    # Perform statistical significance tests on per-case metrics
    comparison["statistical_tests"] = perform_statistical_tests(results_a, results_b)
    
    # Determine overall winner
    comparison["winner"] = determine_overall_winner(comparison["metrics"])
    
    return comparison


def perform_statistical_tests(
    results_a: EvaluationResults,
    results_b: EvaluationResults
) -> Dict[str, Any]:
    """Perform statistical significance tests on per-case metrics.
    
    Args:
        results_a: Results from config A
        results_b: Results from config B
        
    Returns:
        Dictionary with statistical test results
    """
    tests = {}
    
    # Extract per-case metrics
    successful_a = [r for r in results_a.case_results if r.get("success", False)]
    successful_b = [r for r in results_b.case_results if r.get("success", False)]
    
    if len(successful_a) < 2 or len(successful_b) < 2:
        return {"note": "Insufficient data for statistical tests"}
    
    # Test latency differences
    latencies_a = [r["latency_ms"] for r in successful_a]
    latencies_b = [r["latency_ms"] for r in successful_b]
    
    if len(latencies_a) == len(latencies_b):
        # Paired t-test (same cases evaluated)
        t_stat, p_value = stats.ttest_rel(latencies_a, latencies_b)
        tests["latency"] = {
            "test": "paired_t_test",
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "interpretation": "Latency difference is statistically significant" if p_value < 0.05 else "No significant latency difference"
        }
    
    # Test safety score differences
    safety_a = [r["safety_score"]["safety_score"] for r in successful_a]
    safety_b = [r["safety_score"]["safety_score"] for r in successful_b]
    
    if len(safety_a) == len(safety_b):
        t_stat, p_value = stats.ttest_rel(safety_a, safety_b)
        tests["safety_score"] = {
            "test": "paired_t_test",
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "interpretation": "Safety score difference is statistically significant" if p_value < 0.05 else "No significant safety score difference"
        }
    
    # Test quality score differences
    quality_a = [r["quality_score"]["quality_score"] for r in successful_a]
    quality_b = [r["quality_score"]["quality_score"] for r in successful_b]
    
    if len(quality_a) == len(quality_b):
        t_stat, p_value = stats.ttest_rel(quality_a, quality_b)
        tests["quality_score"] = {
            "test": "paired_t_test",
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "interpretation": "Quality score difference is statistically significant" if p_value < 0.05 else "No significant quality score difference"
        }
    
    return tests


def determine_overall_winner(metric_comparisons: Dict[str, Dict[str, Any]]) -> str:
    """Determine overall winner based on metric comparisons.
    
    Args:
        metric_comparisons: Dictionary of metric comparisons
        
    Returns:
        "A", "B", or "Tie"
    """
    wins_a = 0
    wins_b = 0
    
    # Weight different metrics
    weights = {
        "clinical_accuracy": 3,  # Most important
        "avg_safety_score": 3,   # Most important
        "avg_quality_score": 2,
        "faithfulness": 2,
        "answer_relevancy": 1,
        "cost_per_query": 2,
        "p95": 1
    }
    
    for metric, comparison in metric_comparisons.items():
        weight = weights.get(metric, 1)
        winner = comparison.get("winner")
        
        if winner == "A":
            wins_a += weight
        elif winner == "B":
            wins_b += weight
    
    if wins_a > wins_b:
        return "A"
    elif wins_b > wins_a:
        return "B"
    else:
        return "Tie"


def print_comparison_summary(comparison: Dict[str, Any]) -> None:
    """Print a summary of the A/B test comparison.
    
    Args:
        comparison: Comparison results dictionary
    """
    print("\n" + "="*70)
    print("A/B TEST COMPARISON SUMMARY")
    print("="*70)
    print()
    
    print("METRIC COMPARISONS:")
    print("-"*70)
    
    for metric, data in comparison["metrics"].items():
        metric_name = metric.replace("_", " ").title()
        value_a = data["config_a"]
        value_b = data["config_b"]
        diff = data["difference"]
        pct_change = data["percent_change"]
        winner = data["winner"]
        
        # Format values based on metric type
        if "cost" in metric:
            value_a_str = f"${value_a:.4f}"
            value_b_str = f"${value_b:.4f}"
            diff_str = f"${abs(diff):.4f}"
        elif "accuracy" in metric or "faithfulness" in metric or "relevancy" in metric:
            value_a_str = f"{value_a:.2%}"
            value_b_str = f"{value_b:.2%}"
            diff_str = f"{abs(diff):.2%}"
        elif "score" in metric:
            value_a_str = f"{value_a:.2f}"
            value_b_str = f"{value_b:.2f}"
            diff_str = f"{abs(diff):.2f}"
        else:
            value_a_str = f"{value_a:.2f}"
            value_b_str = f"{value_b:.2f}"
            diff_str = f"{abs(diff):.2f}"
        
        direction = "↑" if diff > 0 else "↓" if diff < 0 else "="
        winner_str = f"✓ Config {winner}" if winner != "Tie" else "Tie"
        
        print(f"{metric_name:25} A: {value_a_str:12} B: {value_b_str:12} {direction} {diff_str:10} ({pct_change:+.1f}%) {winner_str}")
    
    print()
    print("-"*70)
    print("STATISTICAL SIGNIFICANCE:")
    print("-"*70)
    
    for test_name, test_data in comparison.get("statistical_tests", {}).items():
        if "note" in test_data:
            print(f"{test_name}: {test_data['note']}")
        else:
            sig_str = "✓ SIGNIFICANT" if test_data.get("significant") else "Not significant"
            print(f"{test_name:20} p-value: {test_data.get('p_value', 0):.4f} {sig_str}")
            print(f"  {test_data.get('interpretation', '')}")
    
    print()
    print("="*70)
    print(f"OVERALL WINNER: Config {comparison['winner']}")
    print("="*70)
    print()


def generate_comparison_dashboard(
    ab_test_results: Dict[str, Any],
    output_path: str
) -> None:
    """Generate HTML dashboard comparing A/B test results.
    
    Args:
        ab_test_results: A/B test results dictionary
        output_path: Path to save dashboard HTML
    """
    comparison = ab_test_results["comparison"]
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>A/B Test Comparison Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .winner {{
            background: #4CAF50;
            color: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            font-size: 24px;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f8f8;
            font-weight: 600;
        }}
        .better {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .worse {{
            color: #f44336;
        }}
        .config-info {{
            background: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>A/B Test Comparison Dashboard</h1>
        <p>Generated: {ab_test_results['timestamp']}</p>
        
        <div class="winner">
            Overall Winner: Config {comparison['winner']}
        </div>
        
        <h2>Configuration Details</h2>
        <div class="config-info">
            <h3>Config A</h3>
            <p>Model: {ab_test_results['config_a']['model']['model_name']}</p>
            <p>Provider: {ab_test_results['config_a']['model']['provider']}</p>
            <p>Temperature: {ab_test_results['config_a']['model']['temperature']}</p>
        </div>
        
        <div class="config-info">
            <h3>Config B</h3>
            <p>Model: {ab_test_results['config_b']['model']['model_name']}</p>
            <p>Provider: {ab_test_results['config_b']['model']['provider']}</p>
            <p>Temperature: {ab_test_results['config_b']['model']['temperature']}</p>
        </div>
        
        <h2>Metric Comparison</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Config A</th>
                <th>Config B</th>
                <th>Difference</th>
                <th>Winner</th>
            </tr>
"""
    
    for metric, data in comparison["metrics"].items():
        metric_name = metric.replace("_", " ").title()
        winner_class = "better" if data["winner"] != "Tie" else ""
        
        html += f"""
            <tr>
                <td>{metric_name}</td>
                <td>{data['config_a']:.4f}</td>
                <td>{data['config_b']:.4f}</td>
                <td class="{winner_class}">{data['difference']:+.4f} ({data['percent_change']:+.1f}%)</td>
                <td class="{winner_class}">Config {data['winner']}</td>
            </tr>
"""
    
    html += """
        </table>
        
        <h2>Statistical Significance</h2>
        <table>
            <tr>
                <th>Test</th>
                <th>P-Value</th>
                <th>Significant?</th>
                <th>Interpretation</th>
            </tr>
"""
    
    for test_name, test_data in comparison.get("statistical_tests", {}).items():
        if "note" not in test_data:
            sig_class = "better" if test_data.get("significant") else ""
            sig_text = "Yes" if test_data.get("significant") else "No"
            
            html += f"""
            <tr>
                <td>{test_name.replace("_", " ").title()}</td>
                <td>{test_data.get('p_value', 0):.4f}</td>
                <td class="{sig_class}">{sig_text}</td>
                <td>{test_data.get('interpretation', '')}</td>
            </tr>
"""
    
    html += """
        </table>
    </div>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Comparison dashboard saved to: {output_path}")
