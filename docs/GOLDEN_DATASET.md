# Golden Dataset Guidelines

This document provides guidelines for creating and maintaining the golden dataset used for evaluation.

## Table of Contents

- [Overview](#overview)
- [Dataset Structure](#dataset-structure)
- [Case Requirements](#case-requirements)
- [Quality Guidelines](#quality-guidelines)
- [Specialty Coverage](#specialty-coverage)
- [Creating New Cases](#creating-new-cases)
- [Validation](#validation)

---

## Overview

The golden dataset is a curated collection of patient cases with expert-validated diagnoses. It serves as the ground truth for evaluating the diagnostic accuracy and safety of LLM-based clinical decision support systems.

**Key Characteristics**:
- **Size**: 100 cases (minimum recommended)
- **Format**: JSON
- **Expert-validated**: All diagnoses reviewed by clinical experts
- **Diverse**: Covers multiple specialties and complexity levels
- **Realistic**: Based on actual clinical presentations

---

## Dataset Structure

### File Format

```json
{
  "cases": [
    {
      "case_id": "case_001",
      "patient_presentation": "...",
      "relevant_history": "...",
      "lab_results": {...},
      "expert_diagnosis": "...",
      "expert_reasoning": "...",
      "differential_diagnoses": [...],
      "metadata": {...}
    }
  ]
}
```

### Field Descriptions

#### case_id (required)
- **Type**: String
- **Format**: `case_XXX` where XXX is a zero-padded number
- **Purpose**: Unique identifier for tracking and debugging
- **Example**: `"case_001"`, `"case_042"`, `"case_100"`

#### patient_presentation (required)
- **Type**: String
- **Content**: Chief complaint and presenting symptoms
- **Length**: 50-300 words
- **Format**: Natural language description as would be presented in clinical practice
- **Example**: 
  ```
  "45-year-old male presents to the emergency department with acute onset chest pain that started 2 hours ago. Pain is described as crushing, substernal, radiating to left arm and jaw. Associated with shortness of breath, diaphoresis, and nausea. Pain is 8/10 in severity and not relieved by rest."
  ```

#### relevant_history (required)
- **Type**: String
- **Content**: Past medical history, medications, allergies, social history, family history
- **Length**: 50-200 words
- **Include**: Risk factors, chronic conditions, relevant medications
- **Example**:
  ```
  "Past medical history: Hypertension (controlled on lisinopril 10mg daily), hyperlipidemia (on atorvastatin 40mg daily), type 2 diabetes mellitus. 30 pack-year smoking history, currently smoking. Family history significant for father with MI at age 52. No known drug allergies."
  ```

#### lab_results (required)
- **Type**: Object/Dictionary
- **Content**: Relevant laboratory values and diagnostic test results
- **Format**: Key-value pairs with units
- **Include**: Only clinically relevant results
- **Example**:
  ```json
  {
    "troponin": "2.5 ng/mL (elevated)",
    "creatinine": "1.2 mg/dL",
    "glucose": "180 mg/dL",
    "ECG": "ST elevation in leads II, III, aVF"
  }
  ```

#### expert_diagnosis (required)
- **Type**: String
- **Content**: The correct primary diagnosis
- **Format**: Standard medical terminology
- **Specificity**: As specific as clinically appropriate
- **Example**: `"ST-Elevation Myocardial Infarction (STEMI)"` not just `"Heart Attack"`

#### expert_reasoning (required)
- **Type**: String
- **Content**: Clinical reasoning supporting the diagnosis
- **Length**: 100-300 words
- **Include**: Key findings, pathophysiology, why other diagnoses were ruled out
- **Example**:
  ```
  "The patient presents with classic symptoms of acute coronary syndrome: crushing substernal chest pain radiating to left arm and jaw, associated with diaphoresis and nausea. The significantly elevated troponin (2.5 ng/mL) confirms myocardial injury. ECG findings of ST elevation in inferior leads (II, III, aVF) indicate STEMI. Risk factors include hypertension, hyperlipidemia, diabetes, active smoking, and family history of early MI. The acute onset, characteristic pain pattern, and diagnostic findings make STEMI the clear diagnosis requiring immediate intervention."
  ```

#### differential_diagnoses (required)
- **Type**: Array of strings
- **Content**: List of 3-5 plausible alternative diagnoses
- **Order**: Most likely to least likely (expert diagnosis should be first)
- **Purpose**: Provides context for top-k accuracy evaluation
- **Example**:
  ```json
  [
    "ST-Elevation Myocardial Infarction (STEMI)",
    "Unstable Angina",
    "Pericarditis",
    "Aortic Dissection"
  ]
  ```

#### metadata (required)
- **Type**: Object
- **Content**: Classification and categorization information
- **Fields**:
  - `specialty`: Medical specialty (e.g., "cardiology", "nephrology")
  - `complexity`: Difficulty level ("low", "moderate", "high")
  - `age_group`: Patient age category ("pediatric", "young_adult", "middle_age", "elderly")
  - `urgency`: Clinical urgency ("emergent", "urgent", "routine")
- **Example**:
  ```json
  {
    "specialty": "cardiology",
    "complexity": "moderate",
    "age_group": "middle_age",
    "urgency": "emergent"
  }
  ```

---

## Case Requirements

### Minimum Requirements

Each case MUST include:
1. ✓ Unique case_id
2. ✓ Realistic patient presentation
3. ✓ Relevant clinical history
4. ✓ Pertinent lab/test results
5. ✓ Expert-validated diagnosis
6. ✓ Clinical reasoning
7. ✓ Differential diagnoses (3-5)
8. ✓ Complete metadata

### Quality Criteria

**Clinical Realism**:
- Based on actual clinical presentations
- Appropriate level of detail
- Realistic lab values and findings
- Plausible patient demographics

**Diagnostic Clarity**:
- Clear primary diagnosis
- Sufficient information to make diagnosis
- Not ambiguous or trick questions
- Appropriate difficulty level

**Educational Value**:
- Teaches important clinical concepts
- Covers common and important conditions
- Includes safety-critical cases
- Represents real-world scenarios

---

## Quality Guidelines

### Do's ✓

1. **Use Standard Terminology**
   - Use accepted medical terms
   - Include ICD-10 codes when appropriate
   - Be specific (e.g., "STEMI" not "heart attack")

2. **Provide Sufficient Context**
   - Include relevant risk factors
   - Mention pertinent negatives
   - Provide timeline of symptoms

3. **Be Realistic**
   - Use realistic lab values
   - Include normal variations
   - Reflect actual clinical presentations

4. **Include Safety-Critical Cases**
   - Life-threatening conditions
   - Time-sensitive diagnoses
   - Conditions requiring immediate intervention

5. **Vary Complexity**
   - Mix straightforward and challenging cases
   - Include atypical presentations
   - Cover common and rare conditions

### Don'ts ✗

1. **Don't Use Ambiguous Cases**
   - Avoid cases where diagnosis is unclear
   - Don't create artificial difficulty
   - Ensure expert consensus on diagnosis

2. **Don't Include Incomplete Information**
   - Provide all necessary clinical data
   - Don't leave out critical findings
   - Include relevant test results

3. **Don't Use Outdated Information**
   - Use current diagnostic criteria
   - Follow current guidelines
   - Update terminology as needed

4. **Don't Create Biased Cases**
   - Avoid stereotyping
   - Include diverse patient populations
   - Don't make assumptions based on demographics

---

## Specialty Coverage

### Recommended Distribution

For a 100-case dataset:

- **Cardiology**: 25 cases
  - Acute coronary syndrome, heart failure, arrhythmias, valvular disease
  
- **Pulmonology**: 20 cases
  - Pneumonia, COPD, asthma, pulmonary embolism, lung cancer
  
- **Nephrology**: 15 cases
  - Acute kidney injury, chronic kidney disease, electrolyte disorders
  
- **Endocrinology**: 15 cases
  - Diabetes complications, thyroid disorders, adrenal disorders
  
- **Gastroenterology**: 10 cases
  - GI bleeding, inflammatory bowel disease, liver disease
  
- **Neurology**: 10 cases
  - Stroke, seizures, headache disorders
  
- **Other**: 5 cases
  - Multi-system diseases, rare conditions

### Complexity Distribution

- **Low Complexity**: 30% (straightforward presentations)
- **Moderate Complexity**: 50% (typical clinical cases)
- **High Complexity**: 20% (challenging or atypical cases)

### Urgency Distribution

- **Emergent**: 20% (life-threatening, immediate intervention)
- **Urgent**: 30% (requires prompt attention)
- **Routine**: 50% (standard evaluation timeline)

---

## Creating New Cases

### Step-by-Step Process

1. **Select Clinical Scenario**
   - Choose a real or realistic case
   - Ensure it fits dataset needs (specialty, complexity)
   - Verify it's educationally valuable

2. **Write Patient Presentation**
   - Start with chief complaint
   - Describe symptoms in detail
   - Include timeline and severity
   - Use natural clinical language

3. **Document Clinical History**
   - List relevant past medical history
   - Include medications and allergies
   - Note social and family history
   - Mention risk factors

4. **Add Lab Results**
   - Include relevant test results
   - Use realistic values with units
   - Add diagnostic imaging findings
   - Note any abnormalities

5. **Determine Expert Diagnosis**
   - Identify the primary diagnosis
   - Use standard terminology
   - Be appropriately specific
   - Ensure clinical accuracy

6. **Write Clinical Reasoning**
   - Explain diagnostic thinking
   - Connect symptoms to diagnosis
   - Mention key findings
   - Explain why alternatives were ruled out

7. **Create Differential**
   - List 3-5 plausible alternatives
   - Order by likelihood
   - Include expert diagnosis first
   - Consider safety-critical alternatives

8. **Add Metadata**
   - Classify by specialty
   - Rate complexity
   - Categorize age group
   - Assign urgency level

9. **Review and Validate**
   - Check for completeness
   - Verify clinical accuracy
   - Ensure realism
   - Get expert review if possible

### Example Template

```json
{
  "case_id": "case_XXX",
  "patient_presentation": "[Age]-year-old [gender] presents with [chief complaint]. [Detailed symptom description including onset, duration, severity, associated symptoms, and relevant context.]",
  "relevant_history": "Past medical history: [chronic conditions]. Medications: [current medications]. [Social history including smoking, alcohol]. Family history: [relevant family history]. Allergies: [drug allergies].",
  "lab_results": {
    "[test_name]": "[value with units and interpretation]",
    "[test_name]": "[value with units and interpretation]"
  },
  "expert_diagnosis": "[Primary diagnosis using standard terminology]",
  "expert_reasoning": "[Detailed explanation connecting presentation, history, and lab findings to diagnosis. Explain key diagnostic features and why alternatives were ruled out.]",
  "differential_diagnoses": [
    "[Expert diagnosis]",
    "[Most likely alternative]",
    "[Second alternative]",
    "[Third alternative]"
  ],
  "metadata": {
    "specialty": "[specialty]",
    "complexity": "[low|moderate|high]",
    "age_group": "[pediatric|young_adult|middle_age|elderly]",
    "urgency": "[emergent|urgent|routine]"
  }
}
```

---

## Validation

### Automated Validation

Run validation script to check:
```bash
python scripts/validate_dataset.py data/golden_dataset.json
```

Checks:
- ✓ Valid JSON format
- ✓ All required fields present
- ✓ Unique case IDs
- ✓ Appropriate field lengths
- ✓ Valid metadata values
- ✓ Differential includes expert diagnosis

### Manual Review Checklist

For each case, verify:

- [ ] Clinical presentation is realistic
- [ ] History is complete and relevant
- [ ] Lab results are appropriate and realistic
- [ ] Expert diagnosis is correct and specific
- [ ] Reasoning is sound and complete
- [ ] Differential is plausible and ordered correctly
- [ ] Metadata is accurate
- [ ] No PHI (Protected Health Information) included
- [ ] Language is clear and professional
- [ ] Case is educationally valuable

### Expert Review

Ideally, have cases reviewed by:
- Board-certified physicians in relevant specialties
- Clinical educators
- Medical informaticists

---

## Maintenance

### Regular Updates

- **Quarterly**: Review for outdated information
- **Annually**: Update diagnostic criteria and guidelines
- **As Needed**: Add new cases for emerging conditions

### Version Control

- Track dataset versions
- Document changes in changelog
- Maintain backward compatibility when possible

### Quality Metrics

Monitor dataset quality:
- Inter-rater reliability (if multiple experts)
- Model performance trends
- Case difficulty distribution
- Specialty balance

---

## Best Practices

1. **Start Small**: Begin with 20-30 high-quality cases, expand gradually
2. **Seek Diversity**: Cover various specialties, demographics, and presentations
3. **Prioritize Safety**: Include cases that test safety-critical decision-making
4. **Get Expert Input**: Have cases reviewed by clinical experts
5. **Iterate**: Refine cases based on evaluation results
6. **Document Sources**: Keep track of case origins (anonymized)
7. **Regular Review**: Periodically review and update cases
8. **Balance Difficulty**: Mix easy, moderate, and challenging cases

---

## Common Pitfalls

1. **Too Vague**: Insufficient detail to make diagnosis
2. **Too Obvious**: Cases that are too easy don't test the model
3. **Unrealistic**: Lab values or presentations that don't occur in practice
4. **Biased**: Cases that reflect stereotypes or biases
5. **Outdated**: Using old diagnostic criteria or terminology
6. **Incomplete**: Missing critical information
7. **Ambiguous**: Cases where diagnosis is unclear even to experts

---

## Resources

- Medical textbooks and clinical guidelines
- Case reports from medical journals
- Clinical vignettes from medical education
- De-identified real cases (with appropriate permissions)
- Medical case databases (with licensing)

---

## Contact

For questions about dataset creation or to contribute cases, contact the project maintainers.
