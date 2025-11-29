"""Quick demo script for Medical Diagnosis Evaluator.

Demonstrates core evaluation capabilities with a small subset of cases.
Perfect for interviews, quick showcases, or initial exploration.

Usage:
    python demo_short.py
    
Duration: ~2-3 minutes
Cases: 5 from golden dataset
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any

from src.config import load_config_from_yaml, EvalConfig
from src.evaluator import Evaluator
from src.dashboard import generate_dashboard_with_charts


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


def print_case_summary(case_result: Dict[str, Any], case_num: int, total: int):
    """Print summary for a single case."""
    case_id = case_result.get("case_id", "unknown")
    success = case_result.get("success", False)
    
    if not success:
        print(f"   [{case_num}/{total}] {case_id}: ❌ FAILED - {case_result.get('error', 'Unknown error')}")
        return
    
    diagnosis = case_result["diagnosis"]
    primary = diagnosis.get("primary_diagnosis", "N/A")
    safety = case_result["safety_score"]["safety_score"]
    quality = case_result["quality_score"]["quality_score"]
    latency = case_result["latency_ms"]
    
    # Safety emoji
    safety_emoji = "🟢" if safety >= 4.0 else "🟡" if safety >= 3.0 else "🔴"
    
    print(f"   [{case_num}/{total}] {case_id}")
    print(f"      Diagnosis: {primary}")
    print(f"      Safety: {safety_emoji} {safety:.1f}/5.0  |  Quality: {quality:.1f}/5.0  |  Latency: {latency:.0f}ms")


def run_quick_demo():
    """Run quick demonstration of evaluation system."""
    start_time = time.time()
    
    # Print welcome
    print_header("Medical Diagnosis Evaluator - Quick Demo")
    
    print("🏥 Welcome to the Medical Diagnosis Evaluator Demo!")
    print()
    print("This system evaluates LLM-based clinical decision support with:")
    print("  • Clinical accuracy metrics (top-3 differential diagnosis)")
    print("  • LLM-as-judge safety and quality scoring")
    print("  • Ragas metrics (faithfulness, relevancy)")
    print("  • Cost and latency tracking")
    print("  • Interactive HTML dashboard")
    print()
    
    # Check for config file
    config_path = "config/openai_eval.yaml"
    if not Path(config_path).exists():
        print(f"❌ Error: Configuration file not found: {config_path}")
        print()
        print("Please ensure you have:")
        print("  1. Created config/openai_eval.yaml")
        print("  2. Set up your .env file with API keys")
        print()
        return 1
    
    # Load configuration
    print("🔧 Loading configuration...")
    try:
        config = load_config_from_yaml(config_path)
        
        # Override for quick demo
        config.subset_size = 5
        config.verbose = False
        
        print(f"   Model: {config.model.model_name}")
        print(f"   Judge: {config.judge_model}")
        print(f"   Cases: {config.subset_size} (subset for quick demo)")
        print()
    except Exception as e:
        print(f"❌ Error loading configuration: {str(e)}")
        print()
        return 1
    
    # Check API keys
    api_key = config.model.get_api_key()
    if not api_key:
        print(f"❌ Error: API key not found for {config.model.provider}")
        print()
        print("Please set up your .env file with:")
        print(f"   {config.model.provider.upper()}_API_KEY=your-key-here")
        print()
        return 1
    
    print("✅ Configuration loaded successfully")
    print()
    
    try:
        input("Press Enter to start the demo...")
    except EOFError:
        print("Starting demo automatically...")
        time.sleep(1)
    
    # Create evaluator
    print_section("Initializing Evaluator")
    
    try:
        evaluator = Evaluator(config)
        print("✅ Evaluator initialized")
        print(f"   Diagnosis Assistant: {config.model.model_name}")
        print(f"   Judge Model: {config.judge_model}")
        print()
    except Exception as e:
        print(f"❌ Error initializing evaluator: {str(e)}")
        print()
        return 1
    
    # Run evaluation
    print_section("Running Evaluation")
    print(f"Processing {config.subset_size} cases from golden dataset...")
    print()
    
    try:
        results = evaluator.run_evaluation()
        
        # Print case summaries
        print()
        print("📋 Case Results:")
        print()
        for i, case_result in enumerate(results.case_results, 1):
            print_case_summary(case_result, i, len(results.case_results))
        
    except Exception as e:
        print(f"❌ Evaluation failed: {str(e)}")
        print()
        return 1
    
    # Print metrics summary
    print_section("Evaluation Metrics")
    
    metrics = results.metrics
    
    print("📊 Clinical Metrics:")
    print(f"   Accuracy (Top-3): {metrics['clinical_accuracy']:.1%}")
    print(f"   Safety Score: {metrics['avg_safety_score']:.2f}/5.0")
    print(f"   Quality Score: {metrics['avg_quality_score']:.2f}/5.0")
    print()
    
    print("🔍 Ragas Metrics:")
    print(f"   Faithfulness: {metrics.get('faithfulness', 0.0):.3f}")
    print(f"   Answer Relevancy: {metrics.get('answer_relevancy', 0.0):.3f}")
    print()
    
    print("⚡ Performance:")
    print(f"   Cost per Query: ${metrics['cost_per_query']:.4f}")
    print(f"   P95 Latency: {metrics['p95']:.0f}ms")
    print()
    
    # Threshold checks
    print("✓ Threshold Checks:")
    thresholds = metrics.get("thresholds_met", {})
    for metric_name, passed in thresholds.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {metric_name.upper()}: {status}")
    print()
    
    # Generate dashboard
    print_section("Generating Dashboard")
    
    try:
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        dashboard_path = output_dir / "demo_dashboard.html"
        generate_dashboard_with_charts(
            metrics=results.metrics,
            case_results=results.case_results,
            config=config,
            output_path=str(dashboard_path)
        )
        
        print(f"✅ Dashboard generated: {dashboard_path}")
        print()
        print(f"   Open in browser: file:///{dashboard_path.absolute()}")
        print()
    except Exception as e:
        print(f"⚠️  Dashboard generation failed: {str(e)}")
        print()
    
    # Summary
    total_time = time.time() - start_time
    
    print_section("Demo Summary")
    
    print(f"⏱️  Total Time: {total_time:.1f}s")
    print(f"📊 Cases Evaluated: {metrics['successful_cases']}/{metrics['total_cases']}")
    print()
    
    if metrics.get("all_thresholds_met", False):
        print("🎉 ALL THRESHOLDS MET!")
    else:
        print("⚠️  Some thresholds not met (expected for small sample)")
    print()
    
    print("✨ Key Features Demonstrated:")
    print("   ✅ Clinical accuracy evaluation")
    print("   ✅ LLM-as-judge safety/quality scoring")
    print("   ✅ Ragas metrics (faithfulness, relevancy)")
    print("   ✅ Cost and latency tracking")
    print("   ✅ Interactive HTML dashboard")
    print()
    
    print("🚀 Next Steps:")
    print("   • Run full demo: python demo_long.py")
    print("   • Run complete evaluation: python evaluate.py --config config/openai_eval.yaml")
    print("   • Compare models: python demo_long.py (includes A/B testing)")
    print("   • View dashboard: Open demo_dashboard.html in browser")
    print()
    
    print_header("Demo Complete - Thank You!")
    
    return 0


def main():
    """Main entry point."""
    try:
        exit_code = run_quick_demo()
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
