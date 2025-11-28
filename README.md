# Phase 2: Medical Diagnosis Evaluator

A comprehensive evaluation harness for assessing LLM-based clinical decision support systems.

## Project Structure

```
phase2-medical-diagnosis-evaluator/
├── src/                    # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── diagnosis_assistant.py  # System under test wrapper
│   ├── langsmith_tracer.py     # LangSmith integration
│   ├── ragas_evaluator.py      # Ragas metrics
│   ├── judge_evaluator.py      # LLM-as-judge
│   ├── metrics.py              # Metric calculations
│   ├── evaluator.py            # Main evaluation runner
│   ├── dashboard.py            # Dashboard generation
│   ├── ab_testing.py           # A/B testing support
│   └── webhooks.py             # Webhook notifications
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_metrics.py
│   └── test_evaluator.py
├── config/                 # Configuration files
│   ├── openai_eval.yaml
│   ├── anthropic_eval.yaml
│   └── grok_eval.yaml
├── data/                   # Golden dataset
│   └── golden_dataset.json
├── docs/                   # Documentation
│   ├── METRICS.md
│   └── GOLDEN_DATASET.md
├── venv/                   # Virtual environment (not in git)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
└── evaluate.py            # CLI entry point

```

## Setup Instructions

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env and add your API keys
```

### 4. Verify Installation

```bash
python -c "import langsmith; import ragas; import openai; print('Setup successful!')"
```

## Quick Start

Coming soon...

## Learning Objectives

- Build reusable evaluation harnesses with golden datasets
- Implement LangSmith tracing for full observability
- Use Ragas/DeepEval for automated metric calculation
- Deploy LLM-as-judge with Claude-3.5-Sonnet or GPT-4o
- Generate automated evaluation reports with dashboards

## Requirements

- Python 3.11+
- API keys for LangSmith, OpenAI, and Anthropic
- Virtual environment (isolated from system Python)

## License

Educational project for GenAI course.
