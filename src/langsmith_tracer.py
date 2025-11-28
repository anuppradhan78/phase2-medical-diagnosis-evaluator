"""LangSmith integration for tracing and dataset management.

This module provides functions for:
- Tracing LLM calls with full observability
- Creating and managing evaluation datasets
- Retrieving traces for analysis
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from langsmith import Client, traceable
from langsmith.schemas import Example, Run


class LangSmithTracer:
    """Wrapper for LangSmith tracing and dataset management."""
    
    def __init__(self, project_name: str = "medical-diagnosis-eval", api_key: Optional[str] = None):
        """Initialize LangSmith client.
        
        Args:
            project_name: Name of the LangSmith project
            api_key: LangSmith API key (defaults to LANGSMITH_API_KEY env var)
        """
        self.project_name = project_name
        
        # Get API key from parameter or environment
        api_key = api_key or os.getenv("LANGSMITH_API_KEY")
        if not api_key:
            raise ValueError(
                "LangSmith API key not found. Set LANGSMITH_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Initialize client
        self.client = Client(api_key=api_key)
        
        # Set environment variable for traceable decorator
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ["LANGSMITH_PROJECT"] = project_name
    
    def create_dataset(
        self,
        dataset_name: str,
        description: Optional[str] = None
    ) -> str:
        """Create a new dataset in LangSmith.
        
        Args:
            dataset_name: Name for the dataset
            description: Optional description
            
        Returns:
            Dataset ID
        """
        try:
            # Check if dataset already exists
            existing_datasets = list(self.client.list_datasets(dataset_name=dataset_name))
            if existing_datasets:
                dataset = existing_datasets[0]
                print(f"Dataset '{dataset_name}' already exists with ID: {dataset.id}")
                return str(dataset.id)
            
            # Create new dataset
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=description or f"Evaluation dataset created on {datetime.now().isoformat()}"
            )
            
            print(f"Created dataset '{dataset_name}' with ID: {dataset.id}")
            return str(dataset.id)
            
        except Exception as e:
            raise Exception(f"Failed to create dataset: {str(e)}")
    
    def add_examples(
        self,
        dataset_name: str,
        examples: List[Dict[str, Any]]
    ) -> List[str]:
        """Add examples to a dataset.
        
        Args:
            dataset_name: Name of the dataset
            examples: List of example dictionaries with 'inputs' and 'outputs' keys
            
        Returns:
            List of example IDs
        
        Example:
            examples = [
                {
                    "inputs": {"patient_presentation": "Chest pain..."},
                    "outputs": {"diagnosis": "STEMI"}
                }
            ]
        """
        try:
            # Get or create dataset
            dataset_id = self.create_dataset(dataset_name)
            
            example_ids = []
            for example in examples:
                if "inputs" not in example or "outputs" not in example:
                    raise ValueError("Each example must have 'inputs' and 'outputs' keys")
                
                # Create example
                created_example = self.client.create_example(
                    dataset_id=dataset_id,
                    inputs=example["inputs"],
                    outputs=example["outputs"],
                    metadata=example.get("metadata", {})
                )
                
                example_ids.append(str(created_example.id))
            
            print(f"Added {len(example_ids)} examples to dataset '{dataset_name}'")
            return example_ids
            
        except Exception as e:
            raise Exception(f"Failed to add examples: {str(e)}")
    
    def get_traces(
        self,
        project_name: Optional[str] = None,
        limit: int = 100,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Run]:
        """Retrieve traces from LangSmith.
        
        Args:
            project_name: Project name (defaults to instance project_name)
            limit: Maximum number of traces to retrieve
            filter_dict: Optional filter criteria
            
        Returns:
            List of Run objects containing trace information
        """
        project = project_name or self.project_name
        
        try:
            runs = list(self.client.list_runs(
                project_name=project,
                limit=limit,
                filter=filter_dict
            ))
            
            print(f"Retrieved {len(runs)} traces from project '{project}'")
            return runs
            
        except Exception as e:
            raise Exception(f"Failed to retrieve traces: {str(e)}")
    
    def get_trace_metadata(self, run: Run) -> Dict[str, Any]:
        """Extract metadata from a trace run.
        
        Args:
            run: Run object from LangSmith
            
        Returns:
            Dictionary with trace metadata
        """
        metadata = {
            "run_id": str(run.id),
            "name": run.name,
            "run_type": run.run_type,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "latency_ms": None,
            "tokens": {},
            "error": run.error,
            "metadata": run.extra.get("metadata", {}) if run.extra else {}
        }
        
        # Calculate latency
        if run.start_time and run.end_time:
            latency = (run.end_time - run.start_time).total_seconds() * 1000
            metadata["latency_ms"] = latency
        
        # Extract token usage
        if run.outputs and isinstance(run.outputs, dict):
            usage = run.outputs.get("usage", {})
            if usage:
                metadata["tokens"] = {
                    "input": usage.get("input_tokens", 0),
                    "output": usage.get("output_tokens", 0),
                    "total": usage.get("total_tokens", 0)
                }
        
        return metadata


# Decorator for tracing functions
def trace_diagnosis(
    case_id: str,
    model_name: str,
    project_name: str = "medical-diagnosis-eval"
):
    """Decorator to trace diagnosis generation.
    
    Args:
        case_id: Unique identifier for the case
        model_name: Name of the model being used
        project_name: LangSmith project name
        
    Example:
        @trace_diagnosis(case_id="card_001", model_name="gpt-4o")
        def generate_diagnosis(inputs):
            # ... diagnosis logic
            return diagnosis
    """
    def decorator(func):
        @traceable(
            name=f"diagnosis_{case_id}",
            project_name=project_name,
            metadata={
                "case_id": case_id,
                "model": model_name
            }
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def create_langsmith_tracer(
    project_name: str = "medical-diagnosis-eval",
    api_key: Optional[str] = None
) -> LangSmithTracer:
    """Factory function to create a LangSmithTracer instance.
    
    Args:
        project_name: Name of the LangSmith project
        api_key: Optional API key (defaults to environment variable)
        
    Returns:
        Configured LangSmithTracer instance
    """
    return LangSmithTracer(project_name=project_name, api_key=api_key)


def load_golden_dataset_to_langsmith(
    golden_dataset_path: str,
    dataset_name: str = "medical-diagnosis-golden",
    project_name: str = "medical-diagnosis-eval"
) -> str:
    """Load golden dataset into LangSmith for evaluation.
    
    Args:
        golden_dataset_path: Path to golden_dataset.json
        dataset_name: Name for the LangSmith dataset
        project_name: LangSmith project name
        
    Returns:
        Dataset ID
    """
    import json
    from pathlib import Path
    
    # Load golden dataset
    dataset_path = Path(golden_dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Golden dataset not found: {golden_dataset_path}")
    
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    # Create tracer
    tracer = create_langsmith_tracer(project_name=project_name)
    
    # Convert cases to examples
    examples = []
    for case in data["cases"]:
        example = {
            "inputs": {
                "case_id": case["case_id"],
                "patient_presentation": case["patient_presentation"],
                "relevant_history": case["relevant_history"],
                "lab_results": case["lab_results"]
            },
            "outputs": {
                "expert_diagnosis": case["expert_diagnosis"],
                "expert_reasoning": case["expert_reasoning"],
                "differential_diagnoses": case["differential_diagnoses"]
            },
            "metadata": case["metadata"]
        }
        examples.append(example)
    
    # Add to LangSmith
    tracer.add_examples(dataset_name, examples)
    
    print(f"Loaded {len(examples)} cases from golden dataset to LangSmith")
    
    return tracer.create_dataset(dataset_name)
