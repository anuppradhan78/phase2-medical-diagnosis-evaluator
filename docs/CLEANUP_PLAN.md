# Directory Cleanup Plan

## Current State Analysis

### Root Directory Files (Too Many!)
- Multiple debug/troubleshooting MD files
- Debug Python scripts
- Demo files mixed with main scripts
- Setup/status documentation

## Organization Strategy

### Keep in Root (User-Facing)
1. **README.md** - Main documentation
2. **DEMO.md** - Demo guide (user-facing)
3. **demo_short.py** - Quick demo script
4. **demo_long.py** - Comprehensive demo script
5. **evaluate.py** - Main evaluation script
6. **test_demos.py** - Demo verification script
7. **requirements.txt** - Dependencies
8. **.env.example** - Environment template
9. **.gitignore** - Git configuration

### Move to docs/ (Technical Documentation)
1. **SETUP_COMPLETE.md** → docs/SETUP_COMPLETE.md
2. **DEMO_SETUP_COMPLETE.md** → docs/DEMO_SETUP_COMPLETE.md
3. **DEMO_DEBUG_SUMMARY.md** → docs/troubleshooting/DEMO_DEBUG_SUMMARY.md
4. **DEMO_FINAL_STATUS.md** → docs/troubleshooting/DEMO_FINAL_STATUS.md
5. **DEMO_RUN_SUMMARY.md** → docs/troubleshooting/DEMO_RUN_SUMMARY.md
6. **ACCURACY_ISSUE_FINAL.md** → docs/troubleshooting/ACCURACY_ISSUE.md
7. **ERROR_FIX_SUMMARY.md** → docs/troubleshooting/ERROR_FIX_SUMMARY.md
8. **DASHBOARD_FIX_SUMMARY.md** → docs/troubleshooting/DASHBOARD_FIX.md

### Move to scripts/ (Debug/Utility Scripts)
1. **debug_accuracy.py** → scripts/debug/debug_accuracy.py
2. **debug_evaluation.py** → scripts/debug/debug_evaluation.py

### Delete (Redundant/Temporary)
- None (all files have value for documentation/debugging)

## Directory Structure After Cleanup

```
phase2-medical-diagnosis-evaluator/
├── README.md                    # Main documentation
├── DEMO.md                      # Demo guide
├── demo_short.py                # Quick demo
├── demo_long.py                 # Full demo
├── evaluate.py                  # Main evaluation
├── test_demos.py                # Demo tests
├── requirements.txt             # Dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Git config
│
├── docs/                        # Documentation
│   ├── METRICS.md              # (existing)
│   ├── GOLDEN_DATASET.md       # (existing)
│   ├── SETUP_COMPLETE.md       # Setup documentation
│   ├── DEMO_SETUP_COMPLETE.md  # Demo setup
│   └── troubleshooting/        # Troubleshooting docs
│       ├── DEMO_DEBUG_SUMMARY.md
│       ├── DEMO_FINAL_STATUS.md
│       ├── DEMO_RUN_SUMMARY.md
│       ├── ACCURACY_ISSUE.md
│       ├── ERROR_FIX_SUMMARY.md
│       └── DASHBOARD_FIX.md
│
├── scripts/                     # Utility scripts
│   ├── generate_golden_dataset.py
│   ├── generate_demo_dataset.py
│   └── debug/                   # Debug scripts
│       ├── debug_accuracy.py
│       └── debug_evaluation.py
│
├── src/                         # Source code
├── tests/                       # Tests
├── config/                      # Configuration
├── data/                        # Data files
└── eval_results/                # Evaluation outputs
```

## Benefits

1. **Cleaner Root** - Only essential user-facing files
2. **Better Organization** - Documentation grouped logically
3. **Easier Navigation** - Clear separation of concerns
4. **Professional** - Looks like a production project
5. **Maintainable** - Easy to find troubleshooting docs

## Implementation

Execute moves in order:
1. Create docs/troubleshooting/ directory
2. Create scripts/debug/ directory
3. Move documentation files
4. Move debug scripts
5. Update any references in README or other docs
