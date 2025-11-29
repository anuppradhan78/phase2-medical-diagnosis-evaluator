"""Evaluation Runner - Core orchestration logic.

This module provides the main Evaluator class that orchestrates the complete
evaluation pipeline:
1. Load golden dataset
2. Process each case through diagnosis assistant
3. Capture traces with LangSmith
4. Compute Ragas metrics
5. Run LLM-as-judge evaluation
6. Track progress and handle errors
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from tqdm import tqdm

from src.config import EvalConfig
from src.diagnosis_assistant import DiagnosisAssistant, DiagnosisResponse
from src.langsmith_tracer import LangSmithTracer
from src.ragas_evaluator import RagasEvaluator, format_diagnosis_for_ragas
from src.judge_evaluator import JudgeEvaluator
from src.metrics import (
    calculate_clinical_accuracy,
    calculate_cost_metrics,
    calculate_latency_metrics
)


class EvaluationResults:
    """Container for evaluation results."""
    
    def __init__(
        self,
        case_results: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        config: EvalConfig,
        timestamp: str
    ):
        """Initialize evaluation results.
        
        Args:
            case_results: List of per-case results
            metrics: Aggregated metrics
            config: Evaluation configuration
            timestamp: Timestamp of evaluation run
        """
        self.case_results = case_results
        self.metrics = metrics
        self.config = config
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary format."""
        return {
            "timestamp": self.timestamp,
            "config": {
                "model": self.config.model.model_dump(),
                "judge_model": self.config.judge_model,
                "thresholds": {
                    "min_accuracy": self.config.min_accuracy,
                    "min_faithfulness": self.config.min_faithfulness,
                    "min_safety_score": self.config.min_safety_score,
                    "max_cost_per_query": self.config.max_cost_per_query,
                    "max_p95_latency": self.config.max_p95_latency
                }
            },
            "metrics": self.metrics,
            "case_results": self.case_results,
            "num_cases": len(self.case_results)
        }


class Evaluator:
    """Main evaluation orchestrator."""
    
    def __init__(self, config: EvalConfig):
        """Initialize evaluator with configuration.
        
        Args:
            config: EvalConfig instance with all settings
        """
        self.config = config
        
        # Initialize components
        self.diagnosis_assistant = DiagnosisAssistant(config.model)
        
        # Initialize LangSmith tracer (optional - may not be configured)
        self.langsmith_tracer = None
        try:
            langsmith_api_key = config.get_langsmith_api_key()
            if langsmith_api_key:
                self.langsmith_tracer = LangSmithTracer(
                    project_name=config.langsmith_project,
                    api_key=langsmith_api_key
                )
                if config.verbose:
                    print(f"✓ LangSmith tracing enabled for project: {config.langsmith_project}")
        except Exception as e:
            if config.verbose:
                print(f"⚠ LangSmith tracing disabled: {str(e)}")
        
        # Initialize evaluators
        self.ragas_evaluator = RagasEvaluator()
        self.judge_evaluator = JudgeEvaluator(
            judge_model=config.judge_model,
            judge_provider=config.judge_provider
        )
        
        if config.verbose:
            print(f"✓ Initialized evaluator with model: {config.model.model_name}")
            print(f"✓ Judge model: {config.judge_model}")
    
    def load_golden_dataset(self) -> List[Dict[str, Any]]:
        """Load golden dataset from JSON file.
        
        Returns:
            List of case dictionaries
            
        Raises:
            FileNotFoundError: If dataset file doesn't exist
            ValueError: If dataset is invalid
        """
        dataset_path = Path(self.config.golden_dataset_path)
        
        if not dataset_path.exists():
            raise FileNotFoundError(
                f"Golden dataset not found: {self.config.golden_dataset_path}"
            )
        
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        if "cases" not in data:
            raise ValueError("Invalid dataset format: missing 'cases' key")
        
        cases = data["cases"]
        
        # Apply subset if configured
        if self.config.subset_size and self.config.subset_size < len(cases):
            cases = cases[:self.config.subset_size]
            if self.config.verbose:
                print(f"Using subset of {self.config.subset_size} cases")
        
        if self.config.verbose:
            print(f"✓ Loaded {len(cases)} cases from golden dataset")
        
        return cases
    
    def run_evaluation(self) -> EvaluationResults:
        """Run complete evaluation pipeline.
        
        Returns:
            EvaluationResults with all metrics and per-case results
        """
        timestamp = datetime.now().isoformat()
        
        if self.config.verbose:
            print("\n" + "="*60)
            print("Starting Medical Diagnosis Evaluation")
            print("="*60 + "\n")
        
        # Load golden dataset
        golden_cases = self.load_golden_dataset()
        
        # Create LangSmith dataset if tracer is available
        if self.langsmith_tracer:
            try:
                dataset_name = f"eval_{timestamp.replace(':', '-')}"
                self.langsmith_tracer.create_dataset(
                    dataset_name=dataset_name,
                    description=f"Evaluation run at {timestamp}"
                )
            except Exception as e:
                if self.config.verbose:
                    print(f"⚠ Failed to create LangSmith dataset: {str(e)}")
        
        # Process all cases
        case_results = []
        
        # Use tqdm for progress bar
        iterator = tqdm(golden_cases, desc="Evaluating cases") if not self.config.verbose else golden_cases
        
        for i, case in enumerate(iterator):
            try:
                case_result = self._process_case(case, i)
                case_results.append(case_result)
                
                if self.config.verbose:
                    print(f"\n✓ Completed case {i+1}/{len(golden_cases)}: {case['case_id']}")
                    print(f"  Diagnosis: {case_result['diagnosis']['primary_diagnosis']}")
                    print(f"  Safety: {case_result['safety_score']['safety_score']}/5")
                    print(f"  Quality: {case_result['quality_score']['quality_score']}/5")
                    print(f"  Latency: {case_result['latency_ms']:.0f}ms")
                
            except Exception as e:
                # Handle individual case failures gracefully
                error_result = {
                    "case_id": case.get("case_id", f"case_{i}"),
                    "error": str(e),
                    "success": False
                }
                case_results.append(error_result)
                
                if self.config.verbose:
                    print(f"\n✗ Failed case {i+1}/{len(golden_cases)}: {str(e)}")
        
        # Compute aggregate metrics
        if self.config.verbose:
            print("\n" + "-"*60)
            print("Computing aggregate metrics...")
            print("-"*60 + "\n")
        
        metrics = self._compute_aggregate_metrics(case_results, golden_cases)
        
        # Create results object
        results = EvaluationResults(
            case_results=case_results,
            metrics=metrics,
            config=self.config,
            timestamp=timestamp
        )
        
        if self.config.verbose:
            self._print_summary(metrics)
        
        return results
    
    def _process_case(self, case: Dict[str, Any], case_index: int) -> Dict[str, Any]:
        """Process a single case through the evaluation pipeline.
        
        Args:
            case: Case dictionary from golden dataset
            case_index: Index of the case
            
        Returns:
            Dictionary with case results
        """
        case_id = case.get("case_id", f"case_{case_index}")
        
        # Start timing
        start_time = time.time()
        
        # Generate diagnosis
        diagnosis_response = self.diagnosis_assistant.generate_diagnosis(
            patient_presentation=case["patient_presentation"],
            relevant_history=case["relevant_history"],
            lab_results=case["lab_results"]
        )
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Evaluate with judge
        safety_score = self.judge_evaluator.judge_safety(
            case=case,
            diagnosis_response=diagnosis_response.model_dump()
        )
        
        quality_score = self.judge_evaluator.judge_quality(
            case=case,
            diagnosis_response=diagnosis_response.model_dump()
        )
        
        # Build result
        result = {
            "case_id": case_id,
            "success": True,
            "diagnosis": diagnosis_response.model_dump(),
            "safety_score": safety_score,
            "quality_score": quality_score,
            "latency_ms": latency_ms,
            "ground_truth": {
                "expert_diagnosis": case.get("expert_diagnosis"),
                "expert_reasoning": case.get("expert_reasoning"),
                "differential_diagnoses": case.get("differential_diagnoses", [])
            },
            "metadata": case.get("metadata", {})
        }
        
        return result
    
    def _compute_aggregate_metrics(
        self,
        case_results: List[Dict[str, Any]],
        golden_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compute aggregate metrics from case results.
        
        Args:
            case_results: List of per-case results
            golden_cases: Original golden dataset cases
            
        Returns:
            Dictionary with all aggregate metrics
        """
        # Filter successful cases
        successful_results = [r for r in case_results if r.get("success", False)]
        
        if not successful_results:
            return {
                "error": "No successful cases to compute metrics",
                "total_cases": len(case_results),
                "successful_cases": 0
            }
        
        # Extract data for metrics
        predictions = []
        ground_truths = []
        safety_scores = []
        quality_scores = []
        latencies = []
        traces = []
        
        for result in successful_results:
            # Clinical accuracy data
            diagnosis = result["diagnosis"]
            primary = diagnosis.get("primary_diagnosis", "")
            differential = diagnosis.get("differential_diagnoses", [])
            
            # Combine primary + differential for top-k matching
            # The primary diagnosis should be considered first in the list
            if primary:
                full_differential = [primary] + differential
            else:
                full_differential = differential if differential else []
            
            predictions.append(full_differential)
            ground_truths.append(result["ground_truth"]["expert_diagnosis"])
            
            # Safety and quality scores
            safety_scores.append(result["safety_score"]["safety_score"])
            quality_scores.append(result["quality_score"]["quality_score"])
            
            # Latency
            latencies.append(result["latency_ms"])
            
            # Trace data for cost calculation
            traces.append({
                "tokens_used": diagnosis.get("tokens_used", 0),
                "model": diagnosis.get("model_used", self.config.model.model_name),
                "input_tokens": diagnosis.get("tokens_used", 0) * 0.6 if diagnosis.get("tokens_used") else 0,
                "output_tokens": diagnosis.get("tokens_used", 0) * 0.4 if diagnosis.get("tokens_used") else 0
            })
        
        # Calculate clinical accuracy
        clinical_accuracy = calculate_clinical_accuracy(
            predictions=predictions,
            ground_truths=ground_truths,
            top_k=3
        )
        
        # Calculate cost metrics
        cost_metrics = calculate_cost_metrics(
            traces=traces,
            model_name=self.config.model.model_name
        )
        
        # Calculate latency metrics
        latency_metrics = calculate_latency_metrics(latencies)
        
        # Calculate average safety and quality scores
        avg_safety_score = sum(safety_scores) / len(safety_scores)
        avg_quality_score = sum(quality_scores) / len(quality_scores)
        
        # Compute Ragas metrics (if we have enough data)
        ragas_metrics = {}
        try:
            # Prepare data for Ragas
            questions = []
            answers = []
            contexts = []
            ragas_ground_truths = []
            
            for result, case in zip(successful_results, golden_cases[:len(successful_results)]):
                formatted = format_diagnosis_for_ragas(case, result["diagnosis"])
                questions.append(formatted["question"])
                answers.append(formatted["answer"])
                contexts.append(formatted["contexts"])
                ragas_ground_truths.append(formatted["ground_truth"])
            
            ragas_results = self.ragas_evaluator.evaluate_with_ragas(
                questions=questions,
                answers=answers,
                contexts=contexts,
                ground_truths=ragas_ground_truths
            )
            
            ragas_metrics = {
                "faithfulness": ragas_results.get("faithfulness", 0.0),
                "answer_relevancy": ragas_results.get("answer_relevancy", 0.0),
                "context_precision": ragas_results.get("context_precision", 0.0),
                "context_recall": ragas_results.get("context_recall", 0.0)
            }
        except Exception as e:
            if self.config.verbose:
                print(f"⚠ Ragas evaluation failed: {str(e)}")
            ragas_metrics = {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
                "error": str(e)
            }
        
        # Check thresholds
        thresholds_met = {
            "accuracy": clinical_accuracy >= self.config.min_accuracy,
            "faithfulness": ragas_metrics.get("faithfulness", 0.0) >= self.config.min_faithfulness,
            "safety": avg_safety_score >= self.config.min_safety_score,
            "cost": cost_metrics["cost_per_query"] <= self.config.max_cost_per_query,
            "latency": latency_metrics["p95"] <= self.config.max_p95_latency
        }
        
        all_thresholds_met = all(thresholds_met.values())
        
        # Compile metrics
        metrics = {
            "total_cases": len(case_results),
            "successful_cases": len(successful_results),
            "failed_cases": len(case_results) - len(successful_results),
            "clinical_accuracy": round(clinical_accuracy, 4),
            "avg_safety_score": round(avg_safety_score, 2),
            "avg_quality_score": round(avg_quality_score, 2),
            **ragas_metrics,
            **cost_metrics,
            **latency_metrics,
            "thresholds_met": thresholds_met,
            "all_thresholds_met": all_thresholds_met
        }
        
        return metrics
    
    def _print_summary(self, metrics: Dict[str, Any]) -> None:
        """Print evaluation summary to console.
        
        Args:
            metrics: Aggregated metrics dictionary
        """
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60 + "\n")
        
        print(f"Cases Evaluated: {metrics['successful_cases']}/{metrics['total_cases']}")
        if metrics['failed_cases'] > 0:
            print(f"⚠ Failed Cases: {metrics['failed_cases']}")
        
        print("\n" + "-"*60)
        print("CLINICAL METRICS")
        print("-"*60)
        print(f"Clinical Accuracy (Top-3): {metrics['clinical_accuracy']:.1%}")
        print(f"Average Safety Score: {metrics['avg_safety_score']:.2f}/5.0")
        print(f"Average Quality Score: {metrics['avg_quality_score']:.2f}/5.0")
        
        print("\n" + "-"*60)
        print("RAGAS METRICS")
        print("-"*60)
        print(f"Faithfulness: {metrics.get('faithfulness', 0.0):.3f}")
        print(f"Answer Relevancy: {metrics.get('answer_relevancy', 0.0):.3f}")
        print(f"Context Precision: {metrics.get('context_precision', 0.0):.3f}")
        print(f"Context Recall: {metrics.get('context_recall', 0.0):.3f}")
        
        print("\n" + "-"*60)
        print("PERFORMANCE METRICS")
        print("-"*60)
        print(f"Cost per Query: ${metrics['cost_per_query']:.4f}")
        print(f"Total Cost: ${metrics['total_cost']:.4f}")
        print(f"Latency P50: {metrics['p50']:.0f}ms")
        print(f"Latency P95: {metrics['p95']:.0f}ms")
        print(f"Latency P99: {metrics['p99']:.0f}ms")
        
        print("\n" + "-"*60)
        print("THRESHOLD CHECKS")
        print("-"*60)
        
        thresholds = metrics.get("thresholds_met", {})
        for metric_name, passed in thresholds.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{metric_name.upper()}: {status}")
        
        print("\n" + "="*60)
        if metrics.get("all_thresholds_met", False):
            print("✓ ALL THRESHOLDS MET - EVALUATION PASSED")
        else:
            print("✗ SOME THRESHOLDS NOT MET - EVALUATION FAILED")
        print("="*60 + "\n")


def create_evaluator(config: EvalConfig) -> Evaluator:
    """Factory function to create an Evaluator instance.
    
    Args:
        config: EvalConfig with all settings
        
    Returns:
        Configured Evaluator instance
    """
    return Evaluator(config)
