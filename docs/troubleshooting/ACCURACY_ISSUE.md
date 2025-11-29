# Accuracy Calculation Issue - Final Analysis

## Summary

Clinical accuracy shows 0% despite correct diagnoses due to how the LLM structures its response.

## The Real Problem

### How the LLM Responds:
```json
{
  "primary_diagnosis": "ST-Elevation Myocardial Infarction (STEMI)",
  "differential_diagnoses": [
    "Unstable Angina",
    "Acute Pericarditis", 
    "Aortic Dissection"
  ]
}
```

**Note**: The `differential_diagnoses` list contains ALTERNATIVES, not including the primary diagnosis.

### How Accuracy is Calculated:
The evaluator checks if the expert diagnosis appears in the LLM's `differential_diagnoses` list:

```python
predictions.append(differential)  # Only the alternatives!
ground_truths.append(expert_diagnosis)  # "STEMI"

# Checks if "STEMI" is in ["Unstable Angina", "Pericarditis", ...]
# Result: FALSE → 0% accuracy
```

## The Solution

The evaluator should include the PRIMARY diagnosis in the predictions list:

### Current Code (Incorrect):
```python
differential = diagnosis.get("differential_diagnoses", [])
if not differential:
    differential = [diagnosis.get("primary_diagnosis", "")]
predictions.append(differential)  # Missing primary!
```

### Fixed Code (Correct):
```python
# Always include primary diagnosis first
primary = diagnosis.get("primary_diagnosis", "")
differential = diagnosis.get("differential_diagnoses", [])

# Combine: primary + differential
full_list = [primary] + differential if primary else differential
predictions.append(full_list)
```

## Implementation

The fix needs to be applied in `src/evaluator.py` at line ~318:

**File**: `phase2-medical-diagnosis-evaluator/src/evaluator.py`
**Function**: `_compute_aggregate_metrics`
**Line**: ~318

### Before:
```python
for result in successful_results:
    # Clinical accuracy data
    diagnosis = result["diagnosis"]
    differential = diagnosis.get("differential_diagnoses", [])
    if not differential:
        # Use primary diagnosis if no differential
        differential = [diagnosis.get("primary_diagnosis", "")]
    predictions.append(differential)
    ground_truths.append(result["ground_truth"]["expert_diagnosis"])
```

### After:
```python
for result in successful_results:
    # Clinical accuracy data
    diagnosis = result["diagnosis"]
    primary = diagnosis.get("primary_diagnosis", "")
    differential = diagnosis.get("differential_diagnoses", [])
    
    # Combine primary + differential for top-k matching
    # The primary diagnosis should be considered first
    if primary:
        full_differential = [primary] + differential
    else:
        full_differential = differential if differential else []
    
    predictions.append(full_differential)
    ground_truths.append(result["ground_truth"]["expert_diagnosis"])
```

## Expected Impact

### Before Fix:
- Primary: "STEMI" ✓ (correct)
- Differential: ["Unstable Angina", "Pericarditis"]
- Checking: Is "STEMI" in differential? **NO**
- Accuracy: **0%** ❌

### After Fix:
- Primary: "STEMI" ✓ (correct)
- Differential: ["Unstable Angina", "Pericarditis"]
- **Combined**: ["STEMI", "Unstable Angina", "Pericarditis"]
- Checking: Is "STEMI" in combined list? **YES**
- Accuracy: **100%** ✅ (if all correct)

## Why This Makes Sense

In medical practice:
- **Primary Diagnosis** = Most likely diagnosis
- **Differential Diagnoses** = Alternative possibilities to consider

For evaluation:
- **Top-K Accuracy** = Is the correct diagnosis in the top K predictions?
- **Top-K should include** = Primary + Differential (all predictions)

The current implementation only checks alternatives, missing the primary diagnosis entirely.

## Action Required

1. **Update `src/evaluator.py`** with the fix above
2. **Re-run demos** to verify accuracy now calculates correctly
3. **Expected result**: Accuracy should be 60-100% depending on how well LLM diagnoses match

## Files to Modify

1. **`src/evaluator.py`** - Line ~318 in `_compute_aggregate_metrics` method

## Testing

After applying the fix:

```bash
# Run short demo
python demo_short.py

# Expected output:
# Clinical Accuracy (Top-3): 80-100% ✅
```

---

**Status**: Issue identified, solution documented
**Next Step**: Apply fix to evaluator.py
**Priority**: High (affects core metric calculation)
