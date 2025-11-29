"""Ragas metrics integration for automated evaluation.

This module provides functions for computing Ragas metrics:
- Faithfulness: Whether the answer is grounded in the context
- Answer Relevancy: Whether the answer addresses the question
- Context Precision: Whether retrieved context is relevant
- Context Recall: Whether all relevant context was retrieved
"""

from typing import List, Dict, Any, Optional
import warnings

try:
    # Try newer Ragas API (0.2+)
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall
    )
except ImportError:
    # Fallback for older versions
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy

from datasets import Dataset
from langchain_openai import ChatOpenAI
import os


class RagasEvaluator:
    """Wrapper for Ragas evaluation metrics."""
    
    def __init__(self):
        """Initialize Ragas evaluator."""
        # Suppress warnings from Ragas
        warnings.filterwarnings('ignore', category=UserWarning)
        
        # Initialize LLM for Ragas (required for newer versions)
        try:
            self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        except Exception as e:
            print(f"Warning: Could not initialize Ragas LLM: {e}")
            self.llm = None
    
    def evaluate_with_ragas(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[str],
        metrics: Optional[List] = None
    ) -> Dict[str, float]:
        """Compute Ragas metrics for evaluation.
        
        Args:
            questions: List of questions/patient presentations
            answers: List of generated answers/diagnoses
            contexts: List of context lists (relevant history, labs, etc.)
            ground_truths: List of ground truth answers/expert diagnoses
            metrics: Optional list of metrics to compute (defaults to all 4)
            
        Returns:
            Dictionary with metric scores
            
        Example:
            results = evaluator.evaluate_with_ragas(
                questions=["Patient with chest pain..."],
                answers=["Diagnosis: STEMI..."],
                contexts=[["History: HTN, DM", "Labs: Troponin 2.5"]],
                ground_truths=["STEMI"]
            )
            # Returns: {"faithfulness": 0.85, "answer_relevancy": 0.90, ...}
        """
        try:
            # Validate inputs
            if not all(len(lst) == len(questions) for lst in [answers, contexts, ground_truths]):
                raise ValueError(
                    "All input lists must have the same length. "
                    f"Got: questions={len(questions)}, answers={len(answers)}, "
                    f"contexts={len(contexts)}, ground_truths={len(ground_truths)}"
                )
            
            # Handle empty contexts
            processed_contexts = []
            for ctx_list in contexts:
                if not ctx_list or all(not c for c in ctx_list):
                    # Provide default context if missing
                    processed_contexts.append(["No additional context provided"])
                else:
                    processed_contexts.append([c for c in ctx_list if c])
            
            # Create dataset in Ragas format
            data = {
                "question": questions,
                "answer": answers,
                "contexts": processed_contexts,
                "ground_truth": ground_truths
            }
            
            dataset = Dataset.from_dict(data)
            
            # Select metrics
            if metrics is None:
                metrics = [
                    faithfulness,
                    answer_relevancy,
                    context_precision,
                    context_recall
                ]
            
            # Evaluate with LLM if available
            if self.llm:
                results = evaluate(
                    dataset,
                    metrics=metrics,
                    llm=self.llm
                )
            else:
                results = evaluate(
                    dataset,
                    metrics=metrics
                )
            
            # Extract scores
            scores = {}
            for metric in metrics:
                metric_name = metric.name
                if metric_name in results:
                    scores[metric_name] = float(results[metric_name])
            
            return scores
            
        except Exception as e:
            # Handle errors gracefully
            print(f"⚠ Ragas evaluation skipped: {str(e)[:100]}")
            print("  Note: Ragas metrics are optional. Core evaluation continues.")
            # Return default scores
            return {
                "faithfulness": 0.0,
                "answer_relevancy": 0.0,
                "context_precision": 0.0,
                "context_recall": 0.0,
                "ragas_skipped": True
            }
    
    def compute_faithfulness(
        self,
        answers: List[str],
        contexts: List[List[str]]
    ) -> float:
        """Compute faithfulness score.
        
        Faithfulness measures whether the answer is grounded in the provided context.
        
        Args:
            answers: List of generated answers
            contexts: List of context lists
            
        Returns:
            Average faithfulness score (0-1)
        """
        # Create dummy questions and ground truths for faithfulness
        questions = ["Evaluate this answer"] * len(answers)
        ground_truths = answers  # Use answers as ground truth for faithfulness
        
        results = self.evaluate_with_ragas(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths,
            metrics=[faithfulness]
        )
        
        return results.get("faithfulness", 0.0)
    
    def compute_answer_relevancy(
        self,
        questions: List[str],
        answers: List[str]
    ) -> float:
        """Compute answer relevancy score.
        
        Answer relevancy measures whether the answer addresses the question.
        
        Args:
            questions: List of questions
            answers: List of generated answers
            
        Returns:
            Average answer relevancy score (0-1)
        """
        # Create dummy contexts and ground truths
        contexts = [["Context provided"] for _ in questions]
        ground_truths = answers
        
        results = self.evaluate_with_ragas(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths,
            metrics=[answer_relevancy]
        )
        
        return results.get("answer_relevancy", 0.0)
    
    def compute_context_metrics(
        self,
        questions: List[str],
        contexts: List[List[str]],
        ground_truths: List[str]
    ) -> Dict[str, float]:
        """Compute context precision and recall.
        
        Args:
            questions: List of questions
            contexts: List of context lists
            ground_truths: List of ground truth answers
            
        Returns:
            Dictionary with context_precision and context_recall scores
        """
        # Use ground truths as answers for context metrics
        answers = ground_truths
        
        results = self.evaluate_with_ragas(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths,
            metrics=[context_precision, context_recall]
        )
        
        return {
            "context_precision": results.get("context_precision", 0.0),
            "context_recall": results.get("context_recall", 0.0)
        }


def create_ragas_evaluator() -> RagasEvaluator:
    """Factory function to create a RagasEvaluator instance.
    
    Returns:
        Configured RagasEvaluator instance
    """
    return RagasEvaluator()


def format_diagnosis_for_ragas(
    case: Dict[str, Any],
    diagnosis_response: Dict[str, Any]
) -> Dict[str, Any]:
    """Format a diagnosis case for Ragas evaluation.
    
    Args:
        case: Golden dataset case with patient info and expert diagnosis
        diagnosis_response: Generated diagnosis response
        
    Returns:
        Dictionary formatted for Ragas evaluation
    """
    # Extract question (patient presentation)
    question = case.get("patient_presentation", "")
    
    # Extract answer (generated diagnosis and reasoning)
    answer = f"{diagnosis_response.get('primary_diagnosis', '')}\n\n"
    answer += f"Reasoning: {diagnosis_response.get('reasoning', '')}"
    
    # Extract contexts (relevant history and lab results)
    contexts = []
    if case.get("relevant_history"):
        contexts.append(f"History: {case['relevant_history']}")
    
    if case.get("lab_results"):
        lab_str = ", ".join([f"{k}: {v}" for k, v in case["lab_results"].items()])
        contexts.append(f"Lab Results: {lab_str}")
    
    # Extract ground truth (expert diagnosis and reasoning)
    ground_truth = f"{case.get('expert_diagnosis', '')}\n\n"
    ground_truth += f"Reasoning: {case.get('expert_reasoning', '')}"
    
    return {
        "question": question,
        "answer": answer,
        "contexts": contexts,
        "ground_truth": ground_truth
    }
