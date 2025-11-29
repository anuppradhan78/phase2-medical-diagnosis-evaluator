"""Quick test to verify demo scripts can be imported and basic functions work."""

import sys
from pathlib import Path

def test_demo_imports():
    """Test that demo modules can be imported."""
    print("Testing demo imports...")
    
    try:
        import demo_short
        print("✅ demo_short.py imports successfully")
    except Exception as e:
        print(f"❌ demo_short.py import failed: {e}")
        return False
    
    try:
        import demo_long
        print("✅ demo_long.py imports successfully")
    except Exception as e:
        print(f"❌ demo_long.py import failed: {e}")
        return False
    
    return True


def test_demo_functions():
    """Test that demo helper functions work."""
    print("\nTesting demo helper functions...")
    
    try:
        import demo_short
        
        # Test print functions
        demo_short.print_header("Test Header")
        demo_short.print_section("Test Section")
        
        print("✅ demo_short helper functions work")
    except Exception as e:
        print(f"❌ demo_short functions failed: {e}")
        return False
    
    try:
        import demo_long
        
        # Test print functions
        demo_long.print_header("Test Header")
        demo_long.print_section("Test Section")
        
        # Test metrics table with dummy data
        dummy_metrics = {
            'clinical_accuracy': 0.85,
            'avg_safety_score': 4.5,
            'avg_quality_score': 4.2,
            'faithfulness': 0.87,
            'answer_relevancy': 0.82,
            'cost_per_query': 0.025,
            'p95': 1500.0
        }
        demo_long.print_metrics_table(dummy_metrics, "Test Metrics")
        
        print("✅ demo_long helper functions work")
    except Exception as e:
        print(f"❌ demo_long functions failed: {e}")
        return False
    
    return True


def test_config_files():
    """Test that required configuration files exist."""
    print("\nChecking configuration files...")
    
    config_dir = Path("config")
    if not config_dir.exists():
        print("❌ config/ directory not found")
        return False
    
    openai_config = config_dir / "openai_eval.yaml"
    if not openai_config.exists():
        print("❌ config/openai_eval.yaml not found")
        return False
    else:
        print("✅ config/openai_eval.yaml exists")
    
    anthropic_config = config_dir / "anthropic_eval.yaml"
    if not anthropic_config.exists():
        print("⚠️  config/anthropic_eval.yaml not found (optional for A/B testing)")
    else:
        print("✅ config/anthropic_eval.yaml exists")
    
    return True


def test_dataset():
    """Test that golden dataset exists."""
    print("\nChecking golden dataset...")
    
    dataset_path = Path("data/golden_dataset.json")
    if not dataset_path.exists():
        print("❌ data/golden_dataset.json not found")
        print("   Run: python scripts/generate_golden_dataset.py")
        return False
    else:
        print("✅ data/golden_dataset.json exists")
        
        # Check dataset is valid JSON
        try:
            import json
            with open(dataset_path, 'r') as f:
                data = json.load(f)
            
            if "cases" not in data:
                print("❌ Dataset missing 'cases' key")
                return False
            
            num_cases = len(data["cases"])
            print(f"✅ Dataset contains {num_cases} cases")
        except Exception as e:
            print(f"❌ Dataset is not valid JSON: {e}")
            return False
    
    return True


def main():
    """Run all tests."""
    print("="*70)
    print("Demo Scripts Verification")
    print("="*70)
    print()
    
    all_passed = True
    
    # Test imports
    if not test_demo_imports():
        all_passed = False
    
    # Test functions
    if not test_demo_functions():
        all_passed = False
    
    # Test config files
    if not test_config_files():
        all_passed = False
    
    # Test dataset
    if not test_dataset():
        all_passed = False
    
    # Summary
    print()
    print("="*70)
    if all_passed:
        print("✅ All tests passed! Demos are ready to run.")
        print()
        print("To run demos:")
        print("  python demo_short.py    # Quick demo (2-3 min)")
        print("  python demo_long.py     # Full demo (10-15 min)")
    else:
        print("❌ Some tests failed. Please fix issues before running demos.")
    print("="*70)
    print()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
