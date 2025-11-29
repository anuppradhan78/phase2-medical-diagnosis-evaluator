"""Script to generate a demo golden dataset with 10 medical cases for testing."""

import json
from pathlib import Path

def create_demo_dataset():
    """Create 10 diverse medical cases for demo purposes."""
    
    dataset = {
        "dataset_info": {
            "name": "Medical Diagnosis Demo Dataset",
            "version": "1.0",
            "total_cases": 10,
            "specialties": {
                "cardiology": 3,
                "pulmonology": 2,
                "endocrinology": 2,
                "gastroenterology": 2,
                "neurology": 1
            },
            "created_date": "2024-11-28"
        },
        "cases": [
            # Cardiology Cases
            {
                "case_id": "card_001",
                "patient_presentation": "58-year-old male with severe crushing chest pain radiating to left arm, diaphoresis, and nausea for 45 minutes.",
                "relevant_history": "Hypertension, hyperlipidemia, 30 pack-year smoking history, family history of CAD",
                "lab_results": {
                    "troponin_I": "2.5 ng/mL (elevated)",
                    "ECG": "ST elevation in leads II, III, aVF",
                    "CK-MB": "45 U/L (elevated)"
                },
                "expert_diagnosis": "STEMI",
                "expert_reasoning": "Classic presentation of ST-Elevation Myocardial Infarction (STEMI) with chest pain, elevated cardiac biomarkers, and ST elevations on ECG. Requires immediate cardiac catheterization.",
                "differential_diagnoses": ["STEMI", "Unstable Angina", "Pericarditis"],
                "metadata": {
                    "specialty": "cardiology",
                    "complexity": "high",
                    "age_group": "middle_age",
                    "urgency": "emergency"
                }
            },
            {
                "case_id": "card_002",
                "patient_presentation": "72-year-old female with progressive shortness of breath, orthopnea, and bilateral leg swelling for 2 weeks.",
                "relevant_history": "Hypertension, previous MI 5 years ago, diabetes mellitus type 2",
                "lab_results": {
                    "BNP": "850 pg/mL (elevated)",
                    "echocardiogram": "EF 35%, dilated left ventricle",
                    "chest_xray": "Cardiomegaly, pulmonary edema"
                },
                "expert_diagnosis": "Heart Failure",
                "expert_reasoning": "Congestive Heart Failure with Reduced Ejection Fraction - symptoms of volume overload with elevated BNP and reduced EF on echo. Requires diuresis and optimization of heart failure medications.",
                "differential_diagnoses": ["Heart Failure", "Pulmonary Edema", "Renal Failure"],
                "metadata": {
                    "specialty": "cardiology",
                    "complexity": "moderate",
                    "age_group": "elderly",
                    "urgency": "urgent"
                }
            },
            {
                "case_id": "card_003",
                "patient_presentation": "45-year-old male with palpitations, lightheadedness, and chest discomfort during exercise.",
                "relevant_history": "No significant past medical history, active lifestyle",
                "lab_results": {
                    "ECG": "Sinus rhythm at rest",
                    "stress_test": "Frequent PVCs during exercise, non-sustained VT",
                    "echocardiogram": "Normal structure and function, EF 60%"
                },
                "expert_diagnosis": "Ventricular Arrhythmia",
                "expert_reasoning": "Exercise-induced ventricular ectopy with non-sustained VT. Requires further evaluation with Holter monitor and possible EP study.",
                "differential_diagnoses": ["Ventricular Arrhythmia", "Supraventricular Tachycardia", "Anxiety"],
                "metadata": {
                    "specialty": "cardiology",
                    "complexity": "moderate",
                    "age_group": "middle_age",
                    "urgency": "semi_urgent"
                }
            },
            # Pulmonology Cases
            {
                "case_id": "pulm_001",
                "patient_presentation": "62-year-old male with productive cough, fever (102°F), and shortness of breath for 3 days.",
                "relevant_history": "COPD, 40 pack-year smoking history, recent upper respiratory infection",
                "lab_results": {
                    "chest_xray": "Right lower lobe consolidation",
                    "WBC": "15,000/μL with left shift",
                    "SpO2": "88% on room air"
                },
                "expert_diagnosis": "Pneumonia",
                "expert_reasoning": "Community-Acquired Pneumonia - classic presentation with fever, productive cough, and lobar consolidation on imaging. Requires antibiotics and supportive care.",
                "differential_diagnoses": ["Pneumonia", "COPD Exacerbation", "Lung Abscess"],
                "metadata": {
                    "specialty": "pulmonology",
                    "complexity": "moderate",
                    "age_group": "elderly",
                    "urgency": "urgent"
                }
            },
            {
                "case_id": "pulm_002",
                "patient_presentation": "28-year-old female with sudden onset severe dyspnea and pleuritic chest pain after long flight.",
                "relevant_history": "Oral contraceptive use, recent 12-hour flight from Europe",
                "lab_results": {
                    "D-dimer": "2.5 μg/mL (elevated)",
                    "CT_angiography": "Filling defect in right pulmonary artery",
                    "ABG": "PaO2 65 mmHg, respiratory alkalosis"
                },
                "expert_diagnosis": "Pulmonary Embolism",
                "expert_reasoning": "Acute Pulmonary Embolism - high-risk presentation with positive CT angiography. Requires immediate anticoagulation and hemodynamic monitoring.",
                "differential_diagnoses": ["Pulmonary Embolism", "Pneumothorax", "Pleuritis"],
                "metadata": {
                    "specialty": "pulmonology",
                    "complexity": "high",
                    "age_group": "young_adult",
                    "urgency": "emergency"
                }
            },
            # Endocrinology Cases
            {
                "case_id": "endo_001",
                "patient_presentation": "52-year-old female with polyuria, polydipsia, weight loss, and fatigue for 6 weeks.",
                "relevant_history": "Obesity (BMI 32), family history of diabetes, sedentary lifestyle",
                "lab_results": {
                    "fasting_glucose": "285 mg/dL",
                    "HbA1c": "10.2%",
                    "urinalysis": "Glucose 3+, ketones negative"
                },
                "expert_diagnosis": "Type 2 Diabetes",
                "expert_reasoning": "Type 2 Diabetes Mellitus, newly diagnosed - classic symptoms with markedly elevated glucose and HbA1c. Requires diabetes education, lifestyle modification, and likely metformin initiation.",
                "differential_diagnoses": ["Type 2 Diabetes", "Type 1 Diabetes", "MODY"],
                "metadata": {
                    "specialty": "endocrinology",
                    "complexity": "moderate",
                    "age_group": "middle_age",
                    "urgency": "semi_urgent"
                }
            },
            {
                "case_id": "endo_002",
                "patient_presentation": "35-year-old female with heat intolerance, palpitations, weight loss, and tremor for 2 months.",
                "relevant_history": "No significant past medical history, family history of autoimmune disease",
                "lab_results": {
                    "TSH": "0.01 mIU/L (suppressed)",
                    "free_T4": "3.2 ng/dL (elevated)",
                    "TSI": "Positive",
                    "thyroid_ultrasound": "Diffusely enlarged, increased vascularity"
                },
                "expert_diagnosis": "Graves' Disease",
                "expert_reasoning": "Graves' Disease (Hyperthyroidism) - suppressed TSH with elevated T4 and positive TSI antibodies. Requires antithyroid medication and beta-blocker for symptom control.",
                "differential_diagnoses": ["Graves' Disease", "Toxic Multinodular Goiter", "Thyroiditis"],
                "metadata": {
                    "specialty": "endocrinology",
                    "complexity": "moderate",
                    "age_group": "young_adult",
                    "urgency": "semi_urgent"
                }
            },
            # Gastroenterology Cases
            {
                "case_id": "gi_001",
                "patient_presentation": "42-year-old male with severe right lower quadrant pain, nausea, vomiting, and fever for 12 hours.",
                "relevant_history": "No significant past medical history, no previous surgeries",
                "lab_results": {
                    "WBC": "16,500/μL with left shift",
                    "CT_abdomen": "Inflamed appendix 12mm, periappendiceal fat stranding",
                    "urinalysis": "Normal"
                },
                "expert_diagnosis": "Appendicitis",
                "expert_reasoning": "Acute Appendicitis - classic presentation with RLQ pain, fever, leukocytosis, and CT findings. Requires urgent surgical consultation for appendectomy.",
                "differential_diagnoses": ["Appendicitis", "Diverticulitis", "Mesenteric Adenitis"],
                "metadata": {
                    "specialty": "gastroenterology",
                    "complexity": "moderate",
                    "age_group": "middle_age",
                    "urgency": "urgent"
                }
            },
            {
                "case_id": "gi_002",
                "patient_presentation": "68-year-old male with melena, fatigue, and dizziness for 3 days.",
                "relevant_history": "NSAID use for arthritis, history of peptic ulcer disease 10 years ago",
                "lab_results": {
                    "hemoglobin": "7.2 g/dL (low)",
                    "BUN": "45 mg/dL",
                    "creatinine": "1.1 mg/dL",
                    "stool_guaiac": "Positive"
                },
                "expert_diagnosis": "Peptic Ulcer Bleeding",
                "expert_reasoning": "Upper Gastrointestinal Bleeding (likely peptic ulcer) - melena with anemia and elevated BUN/Cr ratio suggests upper GI bleed. NSAID use is risk factor. Requires urgent endoscopy.",
                "differential_diagnoses": ["Peptic Ulcer Bleeding", "Gastritis", "Esophageal Varices"],
                "metadata": {
                    "specialty": "gastroenterology",
                    "complexity": "high",
                    "age_group": "elderly",
                    "urgency": "urgent"
                }
            },
            # Neurology Case
            {
                "case_id": "neuro_001",
                "patient_presentation": "55-year-old female with sudden onset right-sided weakness, facial droop, and slurred speech 2 hours ago.",
                "relevant_history": "Hypertension, atrial fibrillation (not on anticoagulation), diabetes",
                "lab_results": {
                    "CT_head": "No acute hemorrhage",
                    "glucose": "145 mg/dL",
                    "INR": "1.0",
                    "NIHSS_score": "12"
                },
                "expert_diagnosis": "Ischemic Stroke",
                "expert_reasoning": "Acute Ischemic Stroke (Left MCA Territory) - acute focal neurological deficits within tPA window. CT negative for hemorrhage. Candidate for thrombolysis given time frame and no contraindications.",
                "differential_diagnoses": ["Ischemic Stroke", "Hemorrhagic Stroke", "Todd's Paralysis"],
                "metadata": {
                    "specialty": "neurology",
                    "complexity": "high",
                    "age_group": "middle_age",
                    "urgency": "emergency"
                }
            }
        ]
    }
    
    return dataset

if __name__ == "__main__":
    dataset = create_demo_dataset()
    
    output_path = Path(__file__).parent.parent / "data" / "golden_dataset.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"✓ Generated {len(dataset['cases'])} cases")
    print(f"✓ Saved to {output_path}")
    print()
    print("Dataset breakdown:")
    for specialty, count in dataset['dataset_info']['specialties'].items():
        print(f"  - {specialty}: {count} cases")
