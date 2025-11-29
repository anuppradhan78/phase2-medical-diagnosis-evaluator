"""Debug script to understand why accuracy is 0%."""

import json
from pathlib import Path

# Load the most recent evaluation results
results_dir = Path("eval_results/openai_gpt4o")
json_files = list(results_dir.glob("evaluation_report_*.json"))

if not json_files:
    print("No evaluation results found")
    exit(1)

# Get most recent
latest = max(json_files, key=lambda p: p.stat().st_mtime)
print(f"Loading: {latest.name}")
print()

with open(latest, 'r') as f:
    data = json.load(f)

print("Checking accuracy calculation...")
print("=" * 70)
print()

# Check first 5 cases
for i, case_result in enumerate(data['case_results'][:5], 1):
    case_id = case_result['case_id']
    
    # LLM's response
    diagnosis = case_result['diagnosis']
    llm_primary = diagnosis.get('primary_diagnosis', '')
    llm_differential = diagnosis.get('differential_diagnoses', [])
    
    # Ground truth
    ground_truth = case_result['ground_truth']
    expert_diagnosis = ground_truth['expert_diagnosis']
    
    print(f"Case {i}: {case_id}")
    print(f"  Expert Diagnosis: '{expert_diagnosis}'")
    print(f"  LLM Primary: '{llm_primary}'")
    print(f"  LLM Differential: {llm_differential}")
    
    # Check if expert diagnosis is in LLM's differential
    if llm_differential:
        expert_lower = expert_diagnosis.lower().strip()
        diff_lower = [d.lower().strip() for d in llm_differential]
        match = expert_lower in diff_lower
        print(f"  Match in differential: {match}")
    else:
        print(f"  ⚠️  LLM differential is EMPTY!")
        # Fallback: check primary
        expert_lower = expert_diagnosis.lower().strip()
        primary_lower = llm_primary.lower().strip()
        match = expert_lower in primary_lower or primary_lower in expert_lower
        print(f"  Match in primary (fallback): {match}")
    
    print()

print("=" * 70)
print("\nConclusion:")
print("If LLM's differential_diagnoses list is empty, accuracy will be 0%")
print("even if the primary_diagnosis is correct.")
