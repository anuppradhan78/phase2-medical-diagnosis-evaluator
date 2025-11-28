"""Report generation for evaluation results.

This module generates JSON and CSV reports from evaluation results.
"""

import json
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


def generate_json_report(
    metrics: Dict[str, Any],
    case_results: List[Dict[str, Any]],
    config: Any,
    output_path: Optional[str] = None
) -> str:
    """Generate JSON report from evaluation results.
    
    Args:
        metrics: Aggregated metrics dictionary
        case_results: List of per-case results
        config: Evaluation configuration
        output_path: Optional path to save JSON file
        
    Returns:
        JSON string
    """
    timestamp = datetime.now().isoformat()
    
    # Build report structure
    report = {
        "metadata": {
            "timestamp": timestamp,
            "evaluation_type": "medical_diagnosis",
            "version": "1.0"
        },
        "configuration": {
            "model": {
                "provider": config.model.provider,
                "model_name": config.model.model_name,
                "temperature": config.model.temperature,
                "max_tokens": config.model.max_tokens
            },
            "judge_model": config.judge_model,
            "judge_provider": config.judge_provider,
            "dataset_path": config.golden_dataset_path,
            "thresholds": {
                "min_accuracy": config.min_accuracy,
                "min_faithfulness": config.min_faithfulness,
                "min_safety_score": config.min_safety_score,
                "max_cost_per_query": config.max_cost_per_query,
                "max_p95_latency": config.max_p95_latency
            }
        },
        "summary_metrics": metrics,
        "case_results": case_results,
        "evaluation_status": {
            "total_cases": metrics.get("total_cases", 0),
            "successful_cases": metrics.get("successful_cases", 0),
            "failed_cases": metrics.get("failed_cases", 0),
            "all_thresholds_met": metrics.get("all_thresholds_met", False)
        }
    }
    
    # Convert to JSON
    json_str = json.dumps(report, indent=2, default=str)
    
    # Save to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"JSON report saved to: {output_path}")
    
    return json_str


def generate_csv_report(
    metrics: Dict[str, Any],
    case_results: List[Dict[str, Any]],
    config: Any,
    output_path: Optional[str] = None
) -> str:
    """Generate CSV report from evaluation results.
    
    Creates a CSV with one row per case, including all relevant metrics.
    
    Args:
        metrics: Aggregated metrics dictionary
        case_results: List of per-case results
        config: Evaluation configuration
        output_path: Optional path to save CSV file
        
    Returns:
        CSV string
    """
    # Define CSV columns
    columns = [
        "case_id",
        "success",
        "primary_diagnosis",
        "differential_diagnoses",
        "expert_diagnosis",
        "correct_in_top_3",
        "safety_score",
        "quality_score",
        "confidence",
        "latency_ms",
        "tokens_used",
        "reasoning",
        "error"
    ]
    
    # Build rows
    rows = []
    for result in case_results:
        if result.get("success", False):
            diagnosis = result.get("diagnosis", {})
            ground_truth = result.get("ground_truth", {})
            
            # Check if correct
            differential = diagnosis.get("differential_diagnoses", [])
            expert_diagnosis = ground_truth.get("expert_diagnosis", "")
            differential_lower = [d.lower().strip() for d in differential[:3]]
            is_correct = expert_diagnosis.lower().strip() in differential_lower
            
            row = {
                "case_id": result.get("case_id", ""),
                "success": "Yes",
                "primary_diagnosis": diagnosis.get("primary_diagnosis", ""),
                "differential_diagnoses": "; ".join(differential),
                "expert_diagnosis": expert_diagnosis,
                "correct_in_top_3": "Yes" if is_correct else "No",
                "safety_score": result.get("safety_score", {}).get("safety_score", ""),
                "quality_score": result.get("quality_score", {}).get("quality_score", ""),
                "confidence": diagnosis.get("confidence", ""),
                "latency_ms": result.get("latency_ms", ""),
                "tokens_used": diagnosis.get("tokens_used", ""),
                "reasoning": diagnosis.get("reasoning", "")[:200],  # Truncate for CSV
                "error": ""
            }
        else:
            row = {
                "case_id": result.get("case_id", ""),
                "success": "No",
                "primary_diagnosis": "",
                "differential_diagnoses": "",
                "expert_diagnosis": "",
                "correct_in_top_3": "",
                "safety_score": "",
                "quality_score": "",
                "confidence": "",
                "latency_ms": "",
                "tokens_used": "",
                "reasoning": "",
                "error": result.get("error", "")
            }
        
        rows.append(row)
    
    # Convert to CSV string
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    csv_str = output.getvalue()
    
    # Save to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_str)
        print(f"CSV report saved to: {output_path}")
    
    return csv_str


def generate_summary_csv(
    metrics: Dict[str, Any],
    config: Any,
    output_path: Optional[str] = None
) -> str:
    """Generate summary CSV with aggregated metrics.
    
    Creates a simple CSV with metric names and values.
    
    Args:
        metrics: Aggregated metrics dictionary
        config: Evaluation configuration
        output_path: Optional path to save CSV file
        
    Returns:
        CSV string
    """
    timestamp = datetime.now().isoformat()
    
    # Build rows
    rows = [
        {"metric": "Timestamp", "value": timestamp},
        {"metric": "Model", "value": config.model.model_name},
        {"metric": "Judge Model", "value": config.judge_model},
        {"metric": "", "value": ""},  # Blank row
        {"metric": "Total Cases", "value": metrics.get("total_cases", 0)},
        {"metric": "Successful Cases", "value": metrics.get("successful_cases", 0)},
        {"metric": "Failed Cases", "value": metrics.get("failed_cases", 0)},
        {"metric": "", "value": ""},  # Blank row
        {"metric": "Clinical Accuracy", "value": f"{metrics.get('clinical_accuracy', 0):.2%}"},
        {"metric": "Average Safety Score", "value": f"{metrics.get('avg_safety_score', 0):.2f}"},
        {"metric": "Average Quality Score", "value": f"{metrics.get('avg_quality_score', 0):.2f}"},
        {"metric": "", "value": ""},  # Blank row
        {"metric": "Faithfulness", "value": f"{metrics.get('faithfulness', 0):.3f}"},
        {"metric": "Answer Relevancy", "value": f"{metrics.get('answer_relevancy', 0):.3f}"},
        {"metric": "Context Precision", "value": f"{metrics.get('context_precision', 0):.3f}"},
        {"metric": "Context Recall", "value": f"{metrics.get('context_recall', 0):.3f}"},
        {"metric": "", "value": ""},  # Blank row
        {"metric": "Cost per Query", "value": f"${metrics.get('cost_per_query', 0):.4f}"},
        {"metric": "Total Cost", "value": f"${metrics.get('total_cost', 0):.4f}"},
        {"metric": "Total Tokens", "value": metrics.get("total_tokens", 0)},
        {"metric": "", "value": ""},  # Blank row
        {"metric": "P50 Latency (ms)", "value": f"{metrics.get('p50', 0):.0f}"},
        {"metric": "P95 Latency (ms)", "value": f"{metrics.get('p95', 0):.0f}"},
        {"metric": "P99 Latency (ms)", "value": f"{metrics.get('p99', 0):.0f}"},
        {"metric": "Mean Latency (ms)", "value": f"{metrics.get('mean', 0):.0f}"},
        {"metric": "", "value": ""},  # Blank row
        {"metric": "All Thresholds Met", "value": "Yes" if metrics.get("all_thresholds_met", False) else "No"}
    ]
    
    # Convert to CSV string
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["metric", "value"])
    writer.writeheader()
    writer.writerows(rows)
    csv_str = output.getvalue()
    
    # Save to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_str)
        print(f"Summary CSV saved to: {output_path}")
    
    return csv_str


def save_all_reports(
    metrics: Dict[str, Any],
    case_results: List[Dict[str, Any]],
    config: Any,
    output_dir: str = "./eval_results"
) -> Dict[str, str]:
    """Save all report formats to output directory.
    
    Args:
        metrics: Aggregated metrics
        case_results: Per-case results
        config: Evaluation configuration
        output_dir: Output directory path
        
    Returns:
        Dictionary mapping report type to file path
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    report_paths = {}
    
    # JSON report
    json_path = output_path / f"evaluation_report_{timestamp}.json"
    generate_json_report(metrics, case_results, config, str(json_path))
    report_paths["json"] = str(json_path)
    
    # Detailed CSV report
    csv_path = output_path / f"evaluation_details_{timestamp}.csv"
    generate_csv_report(metrics, case_results, config, str(csv_path))
    report_paths["csv_details"] = str(csv_path)
    
    # Summary CSV report
    summary_csv_path = output_path / f"evaluation_summary_{timestamp}.csv"
    generate_summary_csv(metrics, config, str(summary_csv_path))
    report_paths["csv_summary"] = str(summary_csv_path)
    
    print(f"\nAll reports saved to: {output_dir}")
    return report_paths


def load_json_report(file_path: str) -> Dict[str, Any]:
    """Load a JSON report from file.
    
    Args:
        file_path: Path to JSON report file
        
    Returns:
        Report dictionary
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_json_report(report: Dict[str, Any]) -> bool:
    """Validate that a JSON report has all required fields.
    
    Args:
        report: Report dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = ["metadata", "configuration", "summary_metrics", "case_results"]
    
    for key in required_keys:
        if key not in report:
            return False
    
    # Check metadata
    if "timestamp" not in report["metadata"]:
        return False
    
    # Check configuration
    if "model" not in report["configuration"]:
        return False
    
    # Check summary metrics
    if "total_cases" not in report["summary_metrics"]:
        return False
    
    return True
