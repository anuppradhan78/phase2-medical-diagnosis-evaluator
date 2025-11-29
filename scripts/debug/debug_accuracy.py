"""Debug script to check why accuracy is showing 0%."""

import json
from pathlib import Path

# Load the golden dataset
dataset_path = Path("data/golden_dataset.json")
with open(dataset_path, 'r') as f:
    data = json.load(f)

print("Checking accuracy calculation issue...")
print("=" * 70)
print()

# Check first 5 cases
for i, case in enumerate(data['cases'][:5], 1):
    case_id = case['case_id']
    expert_diagnosis = case['expert_diagnosis']
    differential = case['differential_diagnoses']
    
    print(f"Case {i}: {case_id}")
    print(f"  Expert Diagnosis: '{expert_diagnosis}'")
    print(f"  Differential Diagnoses: {differential}")
    
    # Check if expert diagnosis is in differential
    expert_lower = expert_diagnosis.lower().strip()
    diff_lower = [d.lower().strip() for d in differential]
    
    match = expert_lower in diff_lower
    print(f"  Match: {match}")
    
    if not match:
        print(f"  ⚠️  Expert diagnosis NOT in differential!")
        print(f"  Looking for: '{expert_lower}'")
        print(f"  In list: {diff_lower}")
    
    print()

print("=" * 70)
print("\nDiagnosis:")
print("The accuracy calculation expects the expert_diagnosis to appear")
print("in the differential_diagnoses list. If it doesn't match exactly,")
print("accuracy will be 0%.")
print()
print("Solution: Ensure expert_diagnosis matches one of the differential_diagnoses")
