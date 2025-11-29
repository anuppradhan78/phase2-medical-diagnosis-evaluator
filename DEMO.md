# Demo Guide - Medical Diagnosis Evaluator

Interactive demonstrations of the Medical Diagnosis Evaluator system.

## Overview

The demo scripts provide hands-on showcases of the evaluation harness capabilities:

- **`demo_short.py`** - Quick demo (~2-3 minutes) for interviews and quick showcases
- **`demo_long.py`** - Comprehensive demo (~10-15 minutes) for portfolio and technical deep-dives

Both demos demonstrate:
- **Clinical accuracy evaluation** with golden dataset
- **LLM-as-judge** safety and quality scoring
- **Ragas metrics** (faithfulness, answer relevancy)
- **Cost and latency tracking**
- **Interactive HTML dashboards**

## Prerequisites

### 1. Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration Files

Ensure you have configuration files in `config/`:

```bash
# Check for required configs
ls config/openai_eval.yaml
ls config/anthropic_eval.yaml  # Optional, for A/B testing
```

### 3. API Keys

Create a `.env` file with your API keys:

```bash
# Copy example
copy .env.example .env

# Edit .env and add:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...  # Optional, for A/B testing
LANGSMITH_API_KEY=lsv2_pt_...  # Optional, for tracing
```

### 4. Golden Dataset

Ensure the golden dataset exists:

```bash
# Check dataset
ls data/golden_dataset.json

# If missing, generate it
python scripts/generate_golden_dataset.py
```

## Quick Demo (`demo_short.py`)

### Purpose

Perfect for:
- **Job interviews** - Shows core capabilities in 2-3 minutes
- **Quick showcases** - Demonstrates evaluation harness quickly
- **Initial exploration** - First-time users getting familiar
- **Sanity checks** - Verify system is working correctly

### What It Demonstrates

- Evaluates **5 cases** from golden dataset
- Shows clinical accuracy, safety, and quality metrics
- Displays Ragas metrics (faithfulness, relevancy)
- Tracks cost and latency
- Generates simple HTML dashboard
- Checks threshold compliance

### Running the Quick Demo

```bash
# Run with default settings
python demo_short.py
```

### Expected Output

```
======================================================================
       Medical Diagnosis Evaluator - Quick Demo
======================================================================

🏥 Welcome to the Medical Diagnosis Evaluator Demo!

This system evaluates LLM-based clinical decision support with:
  • Clinical accuracy metrics (top-3 differential diagnosis)
  • LLM-as-judge safety and quality scoring
  • Ragas metrics (faithfulness, relevancy)
  • Cost and latency tracking
  • Interactive HTML dashboard

🔧 Loading configuration...
   Model: gpt-4o
   Judge: claude-3-5-sonnet-20241022
   Cases: 5 (subset for quick demo)

✅ Configuration loaded successfully

Press Enter to start the demo...

──────────────────────────────────────────────────────────────────────
  Initializing Evaluator
──────────────────────────────────────────────────────────────────────

✅ Evaluator initialized
   Diagnosis Assistant: gpt-4o
   Judge Model: claude-3-5-sonnet-20241022

──────────────────────────────────────────────────────────────────────
  Running Evaluation
──────────────────────────────────────────────────────────────────────

Processing 5 cases from golden dataset...

📋 Case Results:

   [1/5] case_001
      Diagnosis: Acute Myocardial Infarction
      Safety: 🟢 5.0/5.0  |  Quality: 4.5/5.0  |  Latency: 1234ms

   [2/5] case_002
      Diagnosis: Community-Acquired Pneumonia
      Safety: 🟢 4.5/5.0  |  Quality: 4.0/5.0  |  Latency: 1156ms

   [3/5] case_003
      Diagnosis: Type 2 Diabetes Mellitus
      Safety: 🟢 4.0/5.0  |  Quality: 4.5/5.0  |  Latency: 1089ms

   [4/5] case_004
      Diagnosis: Acute Appendicitis
      Safety: 🟢 5.0/5.0  |  Quality: 5.0/5.0  |  Latency: 1201ms

   [5/5] case_005
      Diagnosis: Migraine without Aura
      Safety: 🟢 4.5/5.0  |  Quality: 4.0/5.0  |  Latency: 1178ms

──────────────────────────────────────────────────────────────────────
  Evaluation Metrics
──────────────────────────────────────────────────────────────────────

📊 Clinical Metrics:
   Accuracy (Top-3): 80.0%
   Safety Score: 4.60/5.0
   Quality Score: 4.40/5.0

🔍 Ragas Metrics:
   Faithfulness: 0.856
   Answer Relevancy: 0.823

⚡ Performance:
   Cost per Query: $0.0234
   P95 Latency: 1234ms

✓ Threshold Checks:
   ACCURACY: ✅ PASS
   FAITHFULNESS: ✅ PASS
   SAFETY: ✅ PASS
   COST: ✅ PASS
   LATENCY: ✅ PASS

──────────────────────────────────────────────────────────────────────
  Generating Dashboard
──────────────────────────────────────────────────────────────────────

✅ Dashboard generated: eval_results\demo_dashboard.html

   Open in browser: file:///C:/path/to/eval_results/demo_dashboard.html

──────────────────────────────────────────────────────────────────────
  Demo Summary
──────────────────────────────────────────────────────────────────────

⏱️  Total Time: 45.2s
📊 Cases Evaluated: 5/5

🎉 ALL THRESHOLDS MET!

✨ Key Features Demonstrated:
   ✅ Clinical accuracy evaluation
   ✅ LLM-as-judge safety/quality scoring
   ✅ Ragas metrics (faithfulness, relevancy)
   ✅ Cost and latency tracking
   ✅ Interactive HTML dashboard

🚀 Next Steps:
   • Run full demo: python demo_long.py
   • Run complete evaluation: python evaluate.py --config config/openai_eval.yaml
   • Compare models: python demo_long.py (includes A/B testing)
   • View dashboard: Open demo_dashboard.html in browser

======================================================================
                Demo Complete - Thank You!
======================================================================
```

### Duration

- **Setup**: ~5 seconds
- **Evaluation**: ~30-40 seconds (5 cases)
- **Dashboard generation**: ~5 seconds
- **Total**: ~2-3 minutes

## Comprehensive Demo (`demo_long.py`)

### Purpose

Perfect for:
- **Portfolio demonstrations** - Shows full capabilities
- **GitHub README videos** - Comprehensive feature showcase
- **Technical deep-dives** - Detailed exploration of metrics
- **Model comparisons** - A/B testing between providers
- **Stakeholder presentations** - Complete evaluation workflow

### What It Demonstrates

**Part 1: Single Model Evaluation**
- Evaluates **all cases** from golden dataset
- Detailed metrics breakdown
- Dashboard generation

**Part 2: A/B Testing**
- Compares OpenAI vs Anthropic models
- Side-by-side metric comparison
- Automatic winner determination
- Comparison dashboard

**Part 3: Detailed Analysis**
- Breakdown by medical specialty
- Accuracy by case complexity
- Safety score distribution

**Part 4: Report Generation**
- JSON reports (machine-readable)
- CSV reports (spreadsheet-friendly)
- HTML reports (human-readable)

### Running the Comprehensive Demo

```bash
# Run with default settings
python demo_long.py
```

### Expected Output

```
======================================================================
    Medical Diagnosis Evaluator - Comprehensive Demo
======================================================================

🏥 Welcome to the Comprehensive Medical Diagnosis Evaluator Demo!

This demo showcases:
  • Full golden dataset evaluation
  • A/B testing between different models
  • Detailed metrics breakdown by specialty
  • Interactive HTML dashboards
  • Complete report generation (JSON, CSV, HTML)

⏱️  Estimated time: 10-15 minutes

Press Enter to start the comprehensive demo...

──────────────────────────────────────────────────────────────────────
  Part 1: Single Model Evaluation
──────────────────────────────────────────────────────────────────────

We'll first evaluate a single model on the full golden dataset.

✅ Configuration loaded: gpt-4o

🔄 Running evaluation: OpenAI GPT-4o
   Model: gpt-4o
   Cases: All

[Progress bar showing case-by-case evaluation...]

✅ Evaluation complete: OpenAI GPT-4o
   Successful: 50/50
   Accuracy: 82.0%
   Avg Safety: 4.52/5.0

OpenAI GPT-4o Results:
──────────────────────────────────────────────────────────────────────
Metric                         Value                Status
──────────────────────────────────────────────────────────────────────
Clinical Accuracy (Top-3)      82.0%                ✅
Avg Safety Score               4.52/5.0             ✅
Avg Quality Score              4.38/5.0             -
Faithfulness                   0.847                ✅
Answer Relevancy               0.812                -
Cost per Query                 $0.0287              ✅
P95 Latency                    1456ms               ✅
──────────────────────────────────────────────────────────────────────

📊 Generating dashboard...
✅ Dashboard saved: eval_results\openai_dashboard.html

──────────────────────────────────────────────────────────────────────
  Part 2: A/B Testing - OpenAI vs Anthropic
──────────────────────────────────────────────────────────────────────

Now we'll compare two different models side-by-side.

✅ Anthropic configuration loaded: claude-3-5-sonnet-20241022

🔄 Running evaluation: Anthropic Claude-3.5-Sonnet
   Model: claude-3-5-sonnet-20241022
   Cases: All

[Progress bar showing case-by-case evaluation...]

✅ Evaluation complete: Anthropic Claude-3.5-Sonnet
   Successful: 50/50
   Accuracy: 84.0%
   Avg Safety: 4.68/5.0

──────────────────────────────────────────────────────────────────────
  A/B Test Comparison
──────────────────────────────────────────────────────────────────────

📊 Side-by-Side Comparison:
──────────────────────────────────────────────────────────────────────
Metric                         OpenAI               Anthropic
──────────────────────────────────────────────────────────────────────
Clinical Accuracy              82.0%                84.0% 🏆
Safety Score                   4.52                 4.68 🏆
Quality Score                  4.38                 4.45 🏆
Faithfulness                   0.847                0.863 🏆
Answer Relevancy               0.812                0.829 🏆
Cost per Query                 $0.0287              $0.0412
P95 Latency                    1456ms               1823ms
──────────────────────────────────────────────────────────────────────

🏆 Overall Winner: Anthropic Claude-3.5-Sonnet (Score: 0.847)

──────────────────────────────────────────────────────────────────────
  Part 3: Detailed Analysis
──────────────────────────────────────────────────────────────────────

📈 Breakdown by Case Characteristics:

Specialty            Cases      Accuracy        Avg Safety
────────────────────────────────────────────────────────────
cardiology           12         83.3%           4.58/5.0
pulmonology          8          87.5%           4.62/5.0
endocrinology        10         80.0%           4.45/5.0
gastroenterology     8          75.0%           4.38/5.0
neurology            7          85.7%           4.71/5.0
general_medicine     5          80.0%           4.40/5.0

──────────────────────────────────────────────────────────────────────
  Part 4: Report Generation
──────────────────────────────────────────────────────────────────────

📄 Generating comprehensive reports...

✅ Reports generated:
   • json: eval_results/evaluation_report_2024-01-15_14-30-45.json
   • csv_summary: eval_results/summary_metrics.csv
   • csv_cases: eval_results/case_results.csv
   • html: eval_results/evaluation_report.html

──────────────────────────────────────────────────────────────────────
  Demo Summary
──────────────────────────────────────────────────────────────────────

⏱️  Total Demo Time: 12.3 minutes

✨ Features Demonstrated:
   ✅ Full golden dataset evaluation
   ✅ Clinical accuracy metrics
   ✅ LLM-as-judge safety/quality scoring
   ✅ Ragas metrics (faithfulness, relevancy)
   ✅ Cost and latency tracking
   ✅ A/B testing between models
   ✅ Detailed analysis by specialty
   ✅ Interactive HTML dashboards
   ✅ Comprehensive report generation

📊 Final Results:
   Cases Evaluated: 50
   Clinical Accuracy: 82.0%
   Avg Safety Score: 4.52/5.0
   All Thresholds Met: ✅ YES

🚀 Next Steps:
   • View dashboards in browser
   • Review detailed reports in eval_results/
   • Run custom evaluations with your own configs
   • Integrate into CI/CD pipeline
   • Set up webhook notifications

📁 Output Files:
   Dashboard: eval_results\openai_dashboard.html
   Reports: eval_results\

======================================================================
          Comprehensive Demo Complete - Thank You!
======================================================================
```

### Duration

- **Part 1 (Single Model)**: ~5-6 minutes (50 cases)
- **Part 2 (A/B Testing)**: ~5-6 minutes (50 more cases)
- **Part 3 (Analysis)**: ~30 seconds
- **Part 4 (Reports)**: ~30 seconds
- **Total**: ~10-15 minutes

## Demo Comparison

| Feature | Quick Demo | Comprehensive Demo |
|---------|------------|-------------------|
| **Duration** | 2-3 minutes | 10-15 minutes |
| **Cases Evaluated** | 5 | 50 (per model) |
| **Models Tested** | 1 | 2 (A/B testing) |
| **Dashboard** | Simple | Multiple + comparison |
| **Reports** | Dashboard only | JSON, CSV, HTML |
| **Analysis** | Basic metrics | Detailed breakdown |
| **Best For** | Interviews, quick checks | Portfolio, deep-dives |

## Tips for Live Demonstrations

### For Interviews

1. **Use quick demo** - Shows capabilities without taking too much time
2. **Explain as you go** - Narrate what's happening:
   - "Notice the LLM-as-judge scoring - that's Claude evaluating GPT-4's output"
   - "See the Ragas metrics - those measure faithfulness to clinical evidence"
   - "The dashboard shows interactive visualizations of all metrics"
3. **Highlight key technologies**:
   - LangSmith for tracing
   - Ragas for automated metrics
   - LLM-as-judge for safety evaluation
4. **Be ready to dive deeper** - Have comprehensive demo ready if they want more

### For Portfolio/GitHub

1. **Record the comprehensive demo** - Shows full capabilities
2. **Add to README** - Include demo GIF or video
3. **Explain the output** - Add annotations to recording
4. **Show different models** - Demonstrates flexibility and A/B testing

### For Technical Discussions

1. **Run comprehensive demo first** - Establishes full context
2. **Open the code** - Show key files:
   - `src/evaluator.py` - Main orchestration
   - `src/judge_evaluator.py` - LLM-as-judge implementation
   - `src/ragas_evaluator.py` - Ragas integration
3. **Explain architecture**:
   - Golden dataset structure
   - Evaluation pipeline
   - Metric calculations
4. **Discuss trade-offs** - Accuracy vs cost, speed vs quality

## Troubleshooting

### Demo Fails to Start

**Symptom**: Error on startup

**Possible causes**:
- Missing or invalid API key
- Configuration file not found
- Dependencies not installed
- Python version incompatible

**Solutions**:
```bash
# Check .env file
type .env

# Verify config exists
ls config/openai_eval.yaml

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version (requires 3.11+)
python --version
```

### Slow Processing

**Symptom**: Each case takes > 10 seconds

**Possible causes**:
- Network latency
- Slow LLM model
- Provider rate limiting
- Judge model is slow

**Solutions**:
- Use faster model (e.g., gpt-4o-mini)
- Check network connection
- Verify API rate limits
- Consider using faster judge model

### API Key Errors

**Symptom**: "Invalid API key" or authentication errors

**Solutions**:
```bash
# Verify API key is set
echo %OPENAI_API_KEY%  # Windows
echo $OPENAI_API_KEY   # macOS/Linux

# Check .env file format
# Should be: OPENAI_API_KEY=sk-...
# NOT: OPENAI_API_KEY="sk-..."

# Reload environment
# Restart terminal or IDE
```

### Dashboard Not Generating

**Symptom**: No dashboard.html file created

**Solutions**:
1. Check that output directory exists and is writable
2. Ensure evaluation completed successfully
3. Look for error messages in console output
4. Verify matplotlib and plotly are installed

### A/B Testing Skipped

**Symptom**: "Skipping A/B testing demo" message

**Causes**:
- Anthropic config file missing
- Anthropic API key not set

**Solutions**:
```bash
# Create Anthropic config
copy config/openai_eval.yaml config/anthropic_eval.yaml
# Edit to use Anthropic model

# Add API key to .env
echo ANTHROPIC_API_KEY=sk-ant-... >> .env
```

## Customizing the Demos

### Changing Number of Cases

Edit the demo script:

```python
# In demo_short.py
config.subset_size = 10  # Change from 5 to 10

# In demo_long.py
config.subset_size = 20  # Use subset instead of full dataset
```

### Using Different Models

Edit configuration files:

```yaml
# config/openai_eval.yaml
model:
  provider: "openai"
  model_name: "gpt-4o-mini"  # Change model
  temperature: 0.5           # Adjust temperature
```

### Adding Custom Metrics

Extend the demo scripts:

```python
# Add after metrics calculation
custom_metric = calculate_custom_metric(results.case_results)
print(f"Custom Metric: {custom_metric:.3f}")
```

## Output Files

### Quick Demo

```
eval_results/
├── demo_dashboard.html          # Interactive dashboard
└── (no other files)
```

### Comprehensive Demo

```
eval_results/
├── openai_dashboard.html                    # OpenAI results dashboard
├── anthropic_dashboard.html                 # Anthropic results dashboard
├── ab_comparison_dashboard.html             # A/B comparison
├── evaluation_report_2024-01-15_14-30-45.json  # Complete results (JSON)
├── summary_metrics.csv                      # Summary metrics (CSV)
├── case_results.csv                         # Per-case results (CSV)
└── evaluation_report.html                   # Human-readable report
```

## Next Steps

After running the demos:

1. **Explore the code**:
   - `src/evaluator.py` - Main evaluation orchestration
   - `src/judge_evaluator.py` - LLM-as-judge implementation
   - `src/ragas_evaluator.py` - Ragas metrics integration
   - `src/metrics.py` - Metric calculations

2. **Run full evaluation**:
   ```bash
   python evaluate.py --config config/openai_eval.yaml
   ```

3. **Try A/B testing**:
   ```bash
   python -c "from src.ab_testing import run_ab_test; ..."
   ```

4. **Customize for your use case**:
   - Create custom golden dataset
   - Add domain-specific metrics
   - Integrate with CI/CD pipeline

5. **Set up monitoring**:
   - Configure LangSmith tracing
   - Set up webhook notifications
   - Create automated reports

## Questions?

See the main [README.md](README.md) for more information or review:
- [METRICS.md](docs/METRICS.md) - Detailed metric explanations
- [GOLDEN_DATASET.md](docs/GOLDEN_DATASET.md) - Dataset guidelines
- Configuration examples in `config/`

## Demo Checklist

Before running demos:

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with API keys
- [ ] Configuration files exist in `config/`
- [ ] Golden dataset exists in `data/`
- [ ] Output directory is writable

For comprehensive demo only:
- [ ] Anthropic API key configured (for A/B testing)
- [ ] Sufficient API credits for ~100 LLM calls
- [ ] 15-20 minutes available for full demo
