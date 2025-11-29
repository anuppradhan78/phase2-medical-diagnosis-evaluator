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
├── demo_short.py           # Quick demo script (~2-3 min)
├── demo_long.py            # Comprehensive demo (~10-15 min)
├── DEMO.md                 # Demo guide and documentation
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

### Try the Interactive Demo

**Perfect for first-time users and demonstrations:**

```bash
# Quick demo (~2-3 minutes) - Great for interviews
python demo_short.py

# Comprehensive demo (~10-15 minutes) - Full feature showcase
python demo_long.py
```

**See [DEMO.md](DEMO.md) for detailed demo guide.**

### Run Your First Evaluation

```bash
# Run evaluation with OpenAI model
python evaluate.py --config config/openai_eval.yaml

# Run with a subset for quick testing
python evaluate.py --config config/openai_eval.yaml --subset 10

# Run with verbose output
python evaluate.py --config config/openai_eval.yaml --verbose
```

### View Results

After running an evaluation, you'll find:
- **Dashboard**: `eval_results/dashboard.html` - Interactive HTML dashboard
- **JSON Report**: `eval_results/evaluation_report_*.json` - Complete results
- **CSV Reports**: `eval_results/*.csv` - Spreadsheet-friendly format

## Usage Examples

### Basic Evaluation

```python
from src.config import load_config_from_yaml
from src.evaluator import Evaluator

# Load configuration
config = load_config_from_yaml("config/openai_eval.yaml")

# Create evaluator
evaluator = Evaluator(config)

# Run evaluation
results = evaluator.run_evaluation()

# Print summary
print(f"Clinical Accuracy: {results.metrics['clinical_accuracy']:.2%}")
print(f"Avg Safety Score: {results.metrics['avg_safety_score']:.2f}/5.0")
```

### A/B Testing

```python
from src.config import load_config_from_yaml
from src.ab_testing import run_ab_test

# Load two configurations
config_a = load_config_from_yaml("config/openai_eval.yaml")
config_b = load_config_from_yaml("config/anthropic_eval.yaml")

# Run A/B test
results = run_ab_test(config_a, config_b, output_dir="./ab_results")

# Winner is automatically determined
print(f"Winner: Config {results['comparison']['winner']}")
```

### Webhook Notifications

```python
from src.webhooks import send_evaluation_webhook

# Send results to Slack
send_evaluation_webhook(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    results=results,
    dashboard_url="http://your-dashboard-url.com",
    webhook_type="slack"
)
```

## Configuration Guide

### YAML Configuration File

```yaml
# Model configuration
model:
  provider: "openai"  # openai, anthropic, groq, grok
  model_name: "gpt-4o"
  temperature: 0.7
  max_tokens: 2000

# Judge model for safety/quality evaluation
judge_model: "claude-3-5-sonnet-20241022"
judge_provider: "anthropic"

# Dataset and output
golden_dataset_path: "data/golden_dataset.json"
output_dir: "./eval_results"

# LangSmith tracing (optional)
langsmith_project: "medical-diagnosis-eval"

# Metric thresholds
min_accuracy: 0.75
min_faithfulness: 0.80
min_safety_score: 4.0
max_cost_per_query: 0.10
max_p95_latency: 3000.0
```

### Environment Variables

Create a `.env` file with your API keys:

```bash
# Required for model evaluation
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional for LangSmith tracing
LANGSMITH_API_KEY=lsv2_pt_...

# Optional for other providers
GROQ_API_KEY=gsk_...
GROK_API_KEY=xai-...
```

## CLI Reference

```bash
# Basic usage
python evaluate.py --config CONFIG_FILE

# Options
--config PATH          Path to YAML configuration file (required)
--dataset PATH         Override dataset path from config
--output-dir PATH      Override output directory
--subset N             Evaluate only N cases (for quick tests)
--verbose              Enable detailed logging
--no-dashboard         Skip dashboard generation
--no-reports           Skip report generation

# Examples
python evaluate.py --config config/openai_eval.yaml --subset 10 --verbose
python evaluate.py --config config/anthropic_eval.yaml --output-dir ./my_results
```

## Key Metrics

- **Clinical Accuracy**: % of cases where correct diagnosis appears in top-3 differential
- **Safety Score**: LLM-as-judge evaluation of clinical safety (1-5 scale)
- **Quality Score**: LLM-as-judge evaluation of diagnostic quality (1-5 scale)
- **Faithfulness**: Ragas metric measuring grounding in clinical evidence
- **Answer Relevancy**: Ragas metric measuring response relevance
- **Cost per Query**: Average API cost in USD
- **P95 Latency**: 95th percentile response time in milliseconds

See [docs/METRICS.md](docs/METRICS.md) for detailed metric explanations.

## Troubleshooting

### API Key Issues

**Problem**: `AuthenticationError: Invalid API key`

**Solution**: 
1. Check that your `.env` file exists and contains valid API keys
2. Ensure the `.env` file is in the project root directory
3. Verify API keys are not expired
4. Restart your terminal/IDE after adding environment variables

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'langsmith'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### LangSmith Tracing Issues

**Problem**: Evaluation runs but no traces appear in LangSmith

**Solution**:
1. Verify `LANGSMITH_API_KEY` is set in `.env`
2. Check that `langsmith_project` is configured in your YAML file
3. LangSmith tracing is optional - evaluation will continue without it

### Ragas Evaluation Failures

**Problem**: `Ragas evaluation failed: ...`

**Solution**:
- Ragas failures are non-fatal - evaluation continues with default values
- Check that you have sufficient API credits
- Verify network connectivity
- Ragas metrics will show 0.0 if evaluation fails

### Memory Issues

**Problem**: `MemoryError` or system slowdown

**Solution**:
```bash
# Use subset for testing
python evaluate.py --config config/openai_eval.yaml --subset 20

# Process fewer cases at a time by modifying the dataset
```

### Dashboard Not Generating

**Problem**: No dashboard.html file created

**Solution**:
1. Check that output directory exists and is writable
2. Ensure evaluation completed successfully
3. Look for error messages in console output
4. Try running with `--verbose` flag for more details

## Advanced Features

### Custom Golden Dataset

Create your own dataset following this format:

```json
{
  "cases": [
    {
      "case_id": "case_001",
      "patient_presentation": "45-year-old male with chest pain...",
      "relevant_history": "Hypertension, smoking history",
      "lab_results": {"troponin": "2.5 ng/mL"},
      "expert_diagnosis": "STEMI",
      "expert_reasoning": "Elevated troponin with typical chest pain...",
      "differential_diagnoses": ["STEMI", "Unstable Angina", "Pericarditis"],
      "metadata": {
        "specialty": "cardiology",
        "complexity": "moderate",
        "age_group": "middle_age"
      }
    }
  ]
}
```

See [docs/GOLDEN_DATASET.md](docs/GOLDEN_DATASET.md) for detailed guidelines.

### Extending the Evaluator

Add custom metrics by extending the `Evaluator` class:

```python
from src.evaluator import Evaluator

class CustomEvaluator(Evaluator):
    def _compute_aggregate_metrics(self, case_results, golden_cases):
        # Call parent method
        metrics = super()._compute_aggregate_metrics(case_results, golden_cases)
        
        # Add custom metrics
        metrics["custom_metric"] = self._compute_custom_metric(case_results)
        
        return metrics
    
    def _compute_custom_metric(self, case_results):
        # Your custom logic here
        return 0.95
```

## Project Architecture

The evaluation harness follows a modular architecture:

1. **Configuration Layer** (`config.py`): YAML-based configuration with Pydantic validation
2. **System Under Test** (`diagnosis_assistant.py`): Wrapper for the diagnosis system
3. **Tracing Layer** (`langsmith_tracer.py`): Optional LangSmith integration
4. **Evaluation Layer**:
   - `ragas_evaluator.py`: Automated metrics (faithfulness, relevancy)
   - `judge_evaluator.py`: LLM-as-judge for safety/quality
   - `metrics.py`: Accuracy, cost, and latency calculations
5. **Orchestration** (`evaluator.py`): Main evaluation pipeline
6. **Reporting Layer**:
   - `dashboard.py`: HTML dashboard generation
   - `reports.py`: JSON/CSV report generation
7. **Integration Layer**:
   - `ab_testing.py`: A/B test comparisons
   - `webhooks.py`: CI/CD notifications

## Contributing

This is an educational project. To extend or modify:

1. Add new metrics in `src/metrics.py`
2. Extend evaluation logic in `src/evaluator.py`
3. Add tests in `tests/`
4. Update documentation

## Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review [docs/METRICS.md](docs/METRICS.md) for metric details
3. Examine example configurations in `config/`

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
