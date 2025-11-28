#!/usr/bin/env python3
"""Command-line interface for Medical Diagnosis Evaluator.

This script provides a CLI for running evaluations with various options.
"""

import sys
import argparse
from pathlib import Path

from src.config import load_config_from_yaml
from src.evaluator import Evaluator
from src.dashboard import generate_dashboard_with_charts
from src.reports import save_all_reports


def parse_arguments():
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Medical Diagnosis Evaluator - Evaluate LLM-based diagnosis systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run evaluation with default config
  python evaluate.py --config config/openai_eval.yaml
  
  # Run with custom dataset
  python evaluate.py --config config/openai_eval.yaml --dataset data/custom_dataset.json
  
  # Quick test with subset
  python evaluate.py --config config/openai_eval.yaml --subset 10
  
  # Verbose output
  python evaluate.py --config config/openai_eval.yaml --verbose
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='Path to YAML configuration file'
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        help='Path to golden dataset JSON file (overrides config)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for results (overrides config)'
    )
    
    parser.add_argument(
        '--subset',
        type=int,
        help='Number of cases to evaluate (for quick tests)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--no-dashboard',
        action='store_true',
        help='Skip dashboard generation'
    )
    
    parser.add_argument(
        '--no-reports',
        action='store_true',
        help='Skip report generation'
    )
    
    return parser.parse_args()


def main():
    """Main CLI entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Print header
    print("=" * 70)
    print("Medical Diagnosis Evaluator")
    print("=" * 70)
    print()
    
    try:
        # Load configuration
        print(f"Loading configuration from: {args.config}")
        config = load_config_from_yaml(args.config)
        
        # Apply command-line overrides
        if args.dataset:
            config.golden_dataset_path = args.dataset
            print(f"Using dataset: {args.dataset}")
        
        if args.output_dir:
            config.output_dir = args.output_dir
            print(f"Output directory: {args.output_dir}")
        
        if args.subset:
            config.subset_size = args.subset
            print(f"Evaluating subset of {args.subset} cases")
        
        if args.verbose:
            config.verbose = True
        
        print()
        
        # Create evaluator
        evaluator = Evaluator(config)
        
        # Run evaluation
        print("Starting evaluation...")
        print()
        results = evaluator.run_evaluation()
        
        # Generate dashboard
        if not args.no_dashboard:
            print("\nGenerating dashboard...")
            dashboard_path = Path(config.output_dir) / "dashboard.html"
            generate_dashboard_with_charts(
                results.metrics,
                results.case_results,
                config,
                str(dashboard_path)
            )
        
        # Generate reports
        if not args.no_reports:
            print("\nGenerating reports...")
            report_paths = save_all_reports(
                results.metrics,
                results.case_results,
                config,
                config.output_dir
            )
        
        # Print final summary
        print("\n" + "=" * 70)
        print("EVALUATION COMPLETE")
        print("=" * 70)
        
        # Determine exit code based on thresholds
        all_thresholds_met = results.metrics.get("all_thresholds_met", False)
        
        if all_thresholds_met:
            print("\n✓ All thresholds met - PASS")
            exit_code = 0
        else:
            print("\n✗ Some thresholds not met - FAIL")
            
            # Show which thresholds failed
            thresholds = results.metrics.get("thresholds_met", {})
            failed = [name for name, passed in thresholds.items() if not passed]
            if failed:
                print(f"Failed thresholds: {', '.join(failed)}")
            
            exit_code = 1
        
        print(f"\nResults saved to: {config.output_dir}")
        print()
        
        return exit_code
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        print("\nPlease check that all file paths are correct.", file=sys.stderr)
        return 2
    
    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}", file=sys.stderr)
        print("\nPlease check your configuration file.", file=sys.stderr)
        return 2
    
    except KeyboardInterrupt:
        print("\n\n✗ Evaluation interrupted by user", file=sys.stderr)
        return 130
    
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}", file=sys.stderr)
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
