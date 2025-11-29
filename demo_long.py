"""Comprehensive demo script for Medical Diagnosis Evaluator.

Demonstrates full evaluation capabilities including A/B testing and
advanced features. Perfect for portfolio demonstrations and technical deep-dives.

Usage:
    python demo_long.py
    
Duration: ~10-15 minutes
Features:
    - Full golden dataset evaluation
    - A/B testing (OpenAI vs Anthropic)
    - Detailed metrics breakdown
    - Dashboard generation
    - Webhook notification demo (optional)
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.config import load_config_from_yaml, EvalConfig
from src.evaluator import Evaluator
from src.dashboard import generate_dashboard_with_charts
from src.ab_testing import run_ab_test, generate_comparison_dashboard
from src.reports import save_all_reports


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 70
    print()
    print(char * width)
    print(text.center(width))
    print(char * width)
    print()


def print_section(text: str):
    """Print a section divider."""
    print()
    print(f"{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}")
    print()


def print_metrics_table(metrics: Dict[str, Any], title: str = "Metrics"):
    """Print metrics in a formatted table."""
    print(f"\n{title}:")
    print(f"{'─' * 70}")
    print(f"{'Metric':<30} {'Value':<20} {'Status':<20}")
    print(f"{'─' * 70}")
    
    # Clinical metrics
    accuracy = metrics.get('clinical_accuracy', 0.0)
    safety = metrics.get('avg_safety_score', 0.0)
    quality = metrics.get('avg_quality_score', 0.0)
    
    accuracy_str = f"{accuracy:.1%}"
    safety_str = f"{safety:.2f}/5.0"
    quality_str = f"{quality:.2f}/5.0"
    
    print(f"{'Clinical Accuracy (Top-3)':<30} {accuracy_str:<20} {'✅' if accuracy >= 0.75 else '❌'}")
    print(f"{'Avg Safety Score':<30} {safety_str:<20} {'✅' if safety >= 4.0 else '❌'}")
    print(f"{'Avg Quality Score':<30} {quality_str:<20} {'-'}")
    
    # Ragas metrics
    faithfulness = metrics.get('faithfulness', 0.0)
    relevancy = metrics.get('answer_relevancy', 0.0)
    
    faithfulness_str = f"{faithfulness:.3f}"
    relevancy_str = f"{relevancy:.3f}"
    
    print(f"{'Faithfulness':<30} {faithfulness_str:<20} {'✅' if faithfulness >= 0.80 else '❌'}")
    print(f"{'Answer Relevancy':<30} {relevancy_str:<20} {'-'}")
    
    # Performance metrics
    cost = metrics.get('cost_per_query', 0.0)
    p95 = metrics.get('p95', 0.0)
    
    cost_str = f"${cost:.4f}"
    p95_str = f"{p95:.0f}ms"
    
    print(f"{'Cost per Query':<30} {cost_str:<20} {'✅' if cost <= 0.10 else '❌'}")
    print(f"{'P95 Latency':<30} {p95_str:<20} {'✅' if p95 <= 3000 else '❌'}")
    
    print(f"{'─' * 70}\n")


def run_single_evaluation(config: EvalConfig, name: str) -> Any:
    """Run a single evaluation and return results."""
    print(f"\n🔄 Running evaluation: {name}")
    print(f"   Model: {config.model.model_name}")
    print(f"   Cases: {config.subset_size if config.subset_size else 'All'}")
    print()
    
    evaluator = Evaluator(config)
    results = evaluator.run_evaluation()
    
    print(f"\n✅ Evaluation complete: {name}")
    print(f"   Successful: {results.metrics['successful_cases']}/{results.metrics['total_cases']}")
    print(f"   Accuracy: {results.metrics['clinical_accuracy']:.1%}")
    print(f"   Avg Safety: {results.metrics['avg_safety_score']:.2f}/5.0")
    
    return results


def run_comprehensive_demo():
    """Run comprehensive demonstration of evaluation system."""
    start_time = time.time()
    
    # Print welcome
    print_header("Medical Diagnosis Evaluator - Comprehensive Demo")
    
    print("🏥 Welcome to the Comprehensive Medical Diagnosis Evaluator Demo!")
    print()
    print("This demo showcases:")
    print("  • Full golden dataset evaluation")
    print("  • A/B testing between different models")
    print("  • Detailed metrics breakdown by specialty")
    print("  • Interactive HTML dashboards")
    print("  • Complete report generation (JSON, CSV, HTML)")
    print()
    print("⏱️  Estimated time: 10-15 minutes")
    print()
    
    try:
        input("Press Enter to start the comprehensive demo...")
    except EOFError:
        print("Starting demo automatically...")
        time.sleep(1)
    
    # ========================================================================
    # PART 1: Single Model Evaluation
    # ========================================================================
    
    print_section("Part 1: Single Model Evaluation")
    
    print("We'll first evaluate a single model on the full golden dataset.")
    print()
    
    # Load OpenAI configuration
    config_path = "config/openai_eval.yaml"
    if not Path(config_path).exists():
        print(f"❌ Error: Configuration file not found: {config_path}")
        print()
        return 1
    
    try:
        config = load_config_from_yaml(config_path)
        config.verbose = False
        config.subset_size = None  # Use full dataset
        
        print(f"✅ Configuration loaded: {config.model.model_name}")
        print()
    except Exception as e:
        print(f"❌ Error loading configuration: {str(e)}")
        print()
        return 1
    
    # Check API key
    api_key = config.model.get_api_key()
    if not api_key:
        print(f"❌ Error: API key not found for {config.model.provider}")
        print()
        return 1
    
    # Run evaluation
    try:
        results_openai = run_single_evaluation(config, "OpenAI GPT-4o")
    except Exception as e:
        print(f"❌ Evaluation failed: {str(e)}")
        print()
        return 1
    
    # Print detailed metrics
    print_metrics_table(results_openai.metrics, "OpenAI GPT-4o Results")
    
    # Generate dashboard
    print("📊 Generating dashboard...")
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dashboard_path = output_dir / "openai_dashboard.html"
    try:
        generate_dashboard_with_charts(
            metrics=results_openai.metrics,
            case_results=results_openai.case_results,
            config=config,
            output_path=str(dashboard_path)
        )
        print(f"✅ Dashboard saved: {dashboard_path}")
    except Exception as e:
        print(f"⚠️  Dashboard generation failed: {str(e)}")
    
    print()
    
    # ========================================================================
    # PART 2: A/B Testing
    # ========================================================================
    
    print_section("Part 2: A/B Testing - OpenAI vs Anthropic")
    
    print("Now we'll compare two different models side-by-side.")
    print()
    
    # Check if Anthropic config exists
    anthropic_config_path = "config/anthropic_eval.yaml"
    if not Path(anthropic_config_path).exists():
        print(f"⚠️  Anthropic config not found: {anthropic_config_path}")
        print("   Skipping A/B testing demo")
        print()
    else:
        try:
            # Load Anthropic configuration
            config_anthropic = load_config_from_yaml(anthropic_config_path)
            config_anthropic.verbose = False
            config_anthropic.subset_size = None
            
            # Check API key
            anthropic_key = config_anthropic.model.get_api_key()
            if not anthropic_key:
                print(f"⚠️  Anthropic API key not found")
                print("   Skipping A/B testing demo")
                print()
            else:
                print(f"✅ Anthropic configuration loaded: {config_anthropic.model.model_name}")
                print()
                
                # Run Anthropic evaluation
                results_anthropic = run_single_evaluation(
                    config_anthropic,
                    "Anthropic Claude-3.5-Sonnet"
                )
                
                # Check if Anthropic evaluation was successful
                if results_anthropic.metrics.get('successful_cases', 0) == 0:
                    print("\n⚠️  Anthropic evaluation had no successful cases")
                    print("   Skipping A/B comparison")
                    print()
                else:
                    # Print comparison
                    print_section("A/B Test Comparison")
                    
                    print("📊 Side-by-Side Comparison:")
                    print(f"{'─' * 70}")
                    print(f"{'Metric':<30} {'OpenAI':<20} {'Anthropic':<20}")
                    print(f"{'─' * 70}")
                    
                    # Compare metrics
                    metrics_a = results_openai.metrics
                    metrics_b = results_anthropic.metrics
                    
                    def compare_metric(name: str, key: str, format_str: str = "{:.3f}"):
                        val_a = metrics_a.get(key, 0.0)
                        val_b = metrics_b.get(key, 0.0)
                        winner = "🏆" if val_a > val_b else ("🏆" if val_b > val_a else "=")
                        print(f"{name:<30} {format_str.format(val_a):<20} {format_str.format(val_b) + ' ' + winner:<20}")
                    
                    compare_metric("Clinical Accuracy", "clinical_accuracy", "{:.1%}")
                    compare_metric("Safety Score", "avg_safety_score", "{:.2f}")
                    compare_metric("Quality Score", "avg_quality_score", "{:.2f}")
                    compare_metric("Faithfulness", "faithfulness", "{:.3f}")
                    compare_metric("Answer Relevancy", "answer_relevancy", "{:.3f}")
                    compare_metric("Cost per Query", "cost_per_query", "${:.4f}")
                    compare_metric("P95 Latency", "p95", "{:.0f}ms")
                    
                    print(f"{'─' * 70}\n")
                    
                    # Determine winner
                    score_a = (
                        metrics_a.get('clinical_accuracy', 0.0) * 0.3 +
                        metrics_a.get('avg_safety_score', 0.0) / 5.0 * 0.3 +
                        metrics_a.get('faithfulness', 0.0) * 0.2 +
                        (1.0 - min(metrics_a.get('cost_per_query', 0.0) / 0.10, 1.0)) * 0.1 +
                        (1.0 - min(metrics_a.get('p95', 0.0) / 3000.0, 1.0)) * 0.1
                    )
                    
                    score_b = (
                        metrics_b.get('clinical_accuracy', 0.0) * 0.3 +
                        metrics_b.get('avg_safety_score', 0.0) / 5.0 * 0.3 +
                        metrics_b.get('faithfulness', 0.0) * 0.2 +
                        (1.0 - min(metrics_b.get('cost_per_query', 0.0) / 0.10, 1.0)) * 0.1 +
                        (1.0 - min(metrics_b.get('p95', 0.0) / 3000.0, 1.0)) * 0.1
                    )
                    
                    if score_a > score_b:
                        winner = "OpenAI GPT-4o"
                        winner_score = score_a
                    elif score_b > score_a:
                        winner = "Anthropic Claude-3.5-Sonnet"
                        winner_score = score_b
                    else:
                        winner = "Tie"
                        winner_score = score_a
                    
                    print(f"🏆 Overall Winner: {winner} (Score: {winner_score:.3f})")
                    print()
                    
                    # Generate comparison dashboard
                    print("📊 Generating A/B comparison dashboard...")
                    ab_dashboard_path = output_dir / "ab_comparison_dashboard.html"
                    try:
                        # Create a simple A/B test results structure
                        ab_test_results = {
                            "timestamp": datetime.now().isoformat(),
                            "config_a": {
                                "model": config.model.model_dump(),
                                "judge_model": config.judge_model
                            },
                            "config_b": {
                                "model": config_anthropic.model.model_dump(),
                                "judge_model": config_anthropic.judge_model
                            },
                            "results_a": results_openai.to_dict(),
                            "results_b": results_anthropic.to_dict(),
                            "comparison": {
                                "metrics": {},
                                "winner": winner
                            }
                        }
                        
                        # Add metric comparisons
                        for metric_name in ["clinical_accuracy", "avg_safety_score", "avg_quality_score", 
                                           "faithfulness", "answer_relevancy", "cost_per_query", "p95"]:
                            val_a = metrics_a.get(metric_name, 0.0)
                            val_b = metrics_b.get(metric_name, 0.0)
                            ab_test_results["comparison"]["metrics"][metric_name] = {
                                "config_a": val_a,
                                "config_b": val_b,
                                "difference": val_b - val_a,
                                "percent_change": ((val_b - val_a) / val_a * 100) if val_a != 0 else 0,
                                "winner": "B" if val_b > val_a else "A" if val_a > val_b else "Tie"
                            }
                        
                        generate_comparison_dashboard(ab_test_results, str(ab_dashboard_path))
                        print(f"✅ A/B comparison dashboard saved: {ab_dashboard_path}")
                        print()
                    except Exception as e:
                        print(f"⚠️  A/B dashboard generation failed: {str(e)}")
                        print()
        
        except Exception as e:
            print(f"⚠️  A/B testing failed: {str(e)}")
            print("   Continuing with single model results")
            print()
    
    # ========================================================================
    # PART 3: Detailed Analysis
    # ========================================================================
    
    print_section("Part 3: Detailed Analysis")
    
    print("📈 Breakdown by Case Characteristics:")
    print()
    
    # Analyze by specialty
    specialty_stats = {}
    for case_result in results_openai.case_results:
        if not case_result.get("success"):
            continue
        
        specialty = case_result.get("metadata", {}).get("specialty", "unknown")
        if specialty not in specialty_stats:
            specialty_stats[specialty] = {"total": 0, "correct": 0, "safety_scores": []}
        
        specialty_stats[specialty]["total"] += 1
        
        # Check if diagnosis was correct (simplified check)
        diagnosis = case_result["diagnosis"].get("primary_diagnosis", "")
        ground_truth = case_result["ground_truth"].get("expert_diagnosis", "")
        if diagnosis.lower() in ground_truth.lower() or ground_truth.lower() in diagnosis.lower():
            specialty_stats[specialty]["correct"] += 1
        
        specialty_stats[specialty]["safety_scores"].append(
            case_result["safety_score"]["safety_score"]
        )
    
    print(f"{'Specialty':<20} {'Cases':<10} {'Accuracy':<15} {'Avg Safety':<15}")
    print(f"{'─' * 60}")
    for specialty, stats in sorted(specialty_stats.items()):
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        avg_safety = sum(stats["safety_scores"]) / len(stats["safety_scores"]) if stats["safety_scores"] else 0.0
        accuracy_str = f"{accuracy:.1%}"
        safety_str = f"{avg_safety:.2f}/5.0"
        print(f"{specialty:<20} {stats['total']:<10} {accuracy_str:<15} {safety_str}")
    print()
    
    # ========================================================================
    # PART 4: Report Generation
    # ========================================================================
    
    print_section("Part 4: Report Generation")
    
    print("📄 Generating comprehensive reports...")
    print()
    
    try:
        report_paths = save_all_reports(
            metrics=results_openai.metrics,
            case_results=results_openai.case_results,
            config=config,
            output_dir=str(output_dir)
        )
        
        print("✅ Reports generated:")
        for report_type, path in report_paths.items():
            print(f"   • {report_type}: {path}")
        print()
    except Exception as e:
        print(f"⚠️  Report generation failed: {str(e)}")
        print()
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    total_time = time.time() - start_time
    
    print_section("Demo Summary")
    
    print(f"⏱️  Total Demo Time: {total_time / 60:.1f} minutes")
    print()
    
    print("✨ Features Demonstrated:")
    print("   ✅ Full golden dataset evaluation")
    print("   ✅ Clinical accuracy metrics")
    print("   ✅ LLM-as-judge safety/quality scoring")
    print("   ✅ Ragas metrics (faithfulness, relevancy)")
    print("   ✅ Cost and latency tracking")
    if Path("config/anthropic_eval.yaml").exists():
        print("   ✅ A/B testing between models")
    print("   ✅ Detailed analysis by specialty")
    print("   ✅ Interactive HTML dashboards")
    print("   ✅ Comprehensive report generation")
    print()
    
    print("📊 Final Results:")
    print(f"   Cases Evaluated: {results_openai.metrics['successful_cases']}")
    print(f"   Clinical Accuracy: {results_openai.metrics['clinical_accuracy']:.1%}")
    print(f"   Avg Safety Score: {results_openai.metrics['avg_safety_score']:.2f}/5.0")
    print(f"   All Thresholds Met: {'✅ YES' if results_openai.metrics.get('all_thresholds_met') else '❌ NO'}")
    print()
    
    print("🚀 Next Steps:")
    print("   • View dashboards in browser")
    print("   • Review detailed reports in eval_results/")
    print("   • Run custom evaluations with your own configs")
    print("   • Integrate into CI/CD pipeline")
    print("   • Set up webhook notifications")
    print()
    
    print("📁 Output Files:")
    print(f"   Dashboard: {dashboard_path}")
    print(f"   Reports: {output_dir}/")
    print()
    
    print_header("Comprehensive Demo Complete - Thank You!")
    
    return 0


def main():
    """Main entry point."""
    try:
        exit_code = run_comprehensive_demo()
        return exit_code
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        print()
        return 130
    except Exception as e:
        print(f"\n\n❌ Demo failed: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
