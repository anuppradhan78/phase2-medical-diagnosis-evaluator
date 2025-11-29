"""Dashboard generator for evaluation results.

This module generates an HTML dashboard with:
- Summary metrics cards
- Placeholder sections for charts
- Failure cases table
- LangSmith integration link
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


def generate_dashboard(
    metrics: Dict[str, Any],
    case_results: List[Dict[str, Any]],
    config: Any,
    output_path: Optional[str] = None
) -> str:
    """Generate HTML dashboard from evaluation results.
    
    Args:
        metrics: Aggregated metrics dictionary
        case_results: List of per-case results
        config: Evaluation configuration
        output_path: Optional path to save HTML file
        
    Returns:
        HTML string for dashboard
    """
    # Generate HTML sections
    html = _generate_html_template(metrics, case_results, config)
    
    # Save to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Dashboard saved to: {output_path}")
    
    return html


def _generate_html_template(
    metrics: Dict[str, Any],
    case_results: List[Dict[str, Any]],
    config: Any
) -> str:
    """Generate complete HTML template.
    
    Args:
        metrics: Aggregated metrics
        case_results: Per-case results
        config: Evaluation configuration
        
    Returns:
        Complete HTML string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Diagnosis Evaluator - Results</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        {_get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>Medical Diagnosis Evaluation Results</h1>
            <p class="timestamp">Generated: {timestamp}</p>
            <p class="model-info">Model: {config.model.model_name} | Judge: {config.judge_model}</p>
        </header>

        <!-- Summary Metrics -->
        <section class="summary-section">
            <h2>Summary Metrics</h2>
            <div class="metrics-grid">
                {_generate_summary_cards(metrics, config)}
            </div>
        </section>

        <!-- Threshold Status -->
        <section class="threshold-section">
            <h2>Threshold Validation</h2>
            {_generate_threshold_status(metrics, config)}
        </section>

        <!-- Charts Section (Placeholders) -->
        <section class="charts-section">
            <h2>Visualizations</h2>
            <div class="charts-grid">
                <div class="chart-placeholder" id="accuracy-trend">
                    <h3>Accuracy Trend</h3>
                    <p class="placeholder-text">Chart will be rendered here</p>
                </div>
                <div class="chart-placeholder" id="cost-accuracy-scatter">
                    <h3>Cost vs Accuracy</h3>
                    <p class="placeholder-text">Chart will be rendered here</p>
                </div>
                <div class="chart-placeholder" id="safety-distribution">
                    <h3>Safety Score Distribution</h3>
                    <p class="placeholder-text">Chart will be rendered here</p>
                </div>
                <div class="chart-placeholder" id="latency-distribution">
                    <h3>Latency Distribution</h3>
                    <p class="placeholder-text">Chart will be rendered here</p>
                </div>
            </div>
        </section>

        <!-- Failure Cases -->
        <section class="failures-section">
            <h2>Top Failure Cases</h2>
            {_generate_failure_table(case_results, metrics)}
        </section>

        <!-- LangSmith Link -->
        <section class="langsmith-section">
            <h2>Detailed Trace Analysis</h2>
            <div class="langsmith-link">
                <p>View complete traces and detailed analysis in LangSmith:</p>
                <a href="{_get_langsmith_url(config)}" target="_blank" class="btn-primary">
                    Open LangSmith Dashboard →
                </a>
            </div>
        </section>

        <!-- Footer -->
        <footer class="footer">
            <p>Medical Diagnosis Evaluator | Generated with ❤️ by Kiro</p>
        </footer>
    </div>
</body>
</html>"""
    
    return html


def _get_css_styles() -> str:
    """Get CSS styles for dashboard.
    
    Returns:
        CSS string
    """
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .timestamp, .model-info {
            opacity: 0.9;
            font-size: 0.95em;
        }

        section {
            padding: 40px;
            border-bottom: 1px solid #e0e0e0;
        }

        section:last-of-type {
            border-bottom: none;
        }

        h2 {
            font-size: 1.8em;
            margin-bottom: 25px;
            color: #667eea;
            font-weight: 600;
        }

        h3 {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #555;
        }

        /* Summary Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .metric-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
        }

        .metric-card h3 {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .metric-value {
            font-size: 2.5em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }

        .metric-label {
            font-size: 0.85em;
            color: #888;
        }

        .metric-card.success .metric-value {
            color: #10b981;
        }

        .metric-card.warning .metric-value {
            color: #f59e0b;
        }

        .metric-card.danger .metric-value {
            color: #ef4444;
        }

        /* Threshold Status */
        .threshold-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .threshold-item {
            display: flex;
            align-items: center;
            padding: 15px;
            background: #f9fafb;
            border-radius: 8px;
            border-left: 4px solid #d1d5db;
        }

        .threshold-item.pass {
            border-left-color: #10b981;
            background: #f0fdf4;
        }

        .threshold-item.fail {
            border-left-color: #ef4444;
            background: #fef2f2;
        }

        .threshold-icon {
            font-size: 1.5em;
            margin-right: 10px;
        }

        .threshold-item.pass .threshold-icon {
            color: #10b981;
        }

        .threshold-item.fail .threshold-icon {
            color: #ef4444;
        }

        .threshold-label {
            font-weight: 600;
            color: #374151;
        }

        /* Charts Section */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }

        .chart-placeholder {
            background: #f9fafb;
            border: 2px dashed #d1d5db;
            border-radius: 10px;
            padding: 20px;
            min-height: 400px;
            position: relative;
        }
        
        .chart-placeholder h3 {
            margin: 0 0 15px 0;
            text-align: center;
        }

        .placeholder-text {
            color: #9ca3af;
            font-style: italic;
            text-align: center;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }
        
        /* When chart is rendered, hide placeholder text */
        .chart-placeholder:has(.js-plotly-plot) .placeholder-text {
            display: none;
        }

        /* Failure Cases Table */
        .failure-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .failure-table th {
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }

        .failure-table td {
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
        }

        .failure-table tr:last-child td {
            border-bottom: none;
        }

        .failure-table tr:hover {
            background: #f9fafb;
        }

        .case-id {
            font-weight: 600;
            color: #667eea;
        }

        .diagnosis-text {
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .score-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .score-badge.high {
            background: #d1fae5;
            color: #065f46;
        }

        .score-badge.medium {
            background: #fef3c7;
            color: #92400e;
        }

        .score-badge.low {
            background: #fee2e2;
            color: #991b1b;
        }

        /* LangSmith Section */
        .langsmith-link {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 10px;
        }

        .btn-primary {
            display: inline-block;
            padding: 15px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1.1em;
            margin-top: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
        }

        /* Footer */
        .footer {
            background: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 0.9em;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                border-radius: 0;
            }

            .header h1 {
                font-size: 1.8em;
            }

            .metrics-grid,
            .charts-grid {
                grid-template-columns: 1fr;
            }

            section {
                padding: 20px;
            }

            .failure-table {
                font-size: 0.9em;
            }

            .failure-table th,
            .failure-table td {
                padding: 10px;
            }
        }

        @media (max-width: 480px) {
            body {
                padding: 0;
            }

            .header {
                padding: 20px;
            }

            .header h1 {
                font-size: 1.5em;
            }

            .metric-value {
                font-size: 2em;
            }
        }

        /* No data message */
        .no-data {
            text-align: center;
            padding: 40px;
            color: #9ca3af;
            font-style: italic;
        }
    """


def _generate_summary_cards(metrics: Dict[str, Any], config: Any) -> str:
    """Generate summary metric cards HTML.
    
    Args:
        metrics: Aggregated metrics
        config: Evaluation configuration
        
    Returns:
        HTML string for metric cards
    """
    # Determine card classes based on thresholds
    accuracy_class = "success" if metrics.get("clinical_accuracy", 0) >= config.min_accuracy else "danger"
    safety_class = "success" if metrics.get("avg_safety_score", 0) >= config.min_safety_score else "warning"
    cost_class = "success" if metrics.get("cost_per_query", 999) <= config.max_cost_per_query else "warning"
    latency_class = "success" if metrics.get("p95", 9999) <= config.max_p95_latency else "warning"
    
    cards_html = f"""
        <div class="metric-card {accuracy_class}">
            <h3>Clinical Accuracy</h3>
            <div class="metric-value">{metrics.get('clinical_accuracy', 0):.1%}</div>
            <div class="metric-label">Top-3 Match Rate</div>
        </div>
        
        <div class="metric-card {safety_class}">
            <h3>Safety Score</h3>
            <div class="metric-value">{metrics.get('avg_safety_score', 0):.2f}</div>
            <div class="metric-label">Out of 5.0</div>
        </div>
        
        <div class="metric-card">
            <h3>Quality Score</h3>
            <div class="metric-value">{metrics.get('avg_quality_score', 0):.2f}</div>
            <div class="metric-label">Out of 5.0</div>
        </div>
        
        <div class="metric-card">
            <h3>Faithfulness</h3>
            <div class="metric-value">{metrics.get('faithfulness', 0):.3f}</div>
            <div class="metric-label">Ragas Metric</div>
        </div>
        
        <div class="metric-card">
            <h3>Answer Relevancy</h3>
            <div class="metric-value">{metrics.get('answer_relevancy', 0):.3f}</div>
            <div class="metric-label">Ragas Metric</div>
        </div>
        
        <div class="metric-card {cost_class}">
            <h3>Cost per Query</h3>
            <div class="metric-value">${metrics.get('cost_per_query', 0):.4f}</div>
            <div class="metric-label">USD</div>
        </div>
        
        <div class="metric-card {latency_class}">
            <h3>P95 Latency</h3>
            <div class="metric-value">{metrics.get('p95', 0):.0f}ms</div>
            <div class="metric-label">95th Percentile</div>
        </div>
        
        <div class="metric-card">
            <h3>Cases Evaluated</h3>
            <div class="metric-value">{metrics.get('successful_cases', 0)}</div>
            <div class="metric-label">of {metrics.get('total_cases', 0)} total</div>
        </div>
    """
    
    return cards_html


def _generate_threshold_status(metrics: Dict[str, Any], config: Any) -> str:
    """Generate threshold validation status HTML.
    
    Args:
        metrics: Aggregated metrics
        config: Evaluation configuration
        
    Returns:
        HTML string for threshold status
    """
    thresholds = metrics.get("thresholds_met", {})
    all_met = metrics.get("all_thresholds_met", False)
    
    threshold_items = []
    threshold_labels = {
        "accuracy": "Clinical Accuracy",
        "faithfulness": "Faithfulness",
        "safety": "Safety Score",
        "cost": "Cost per Query",
        "latency": "P95 Latency"
    }
    
    for key, passed in thresholds.items():
        label = threshold_labels.get(key, key.title())
        status_class = "pass" if passed else "fail"
        icon = "✓" if passed else "✗"
        
        threshold_items.append(f"""
            <div class="threshold-item {status_class}">
                <span class="threshold-icon">{icon}</span>
                <span class="threshold-label">{label}</span>
            </div>
        """)
    
    overall_status = "✓ All Thresholds Met" if all_met else "✗ Some Thresholds Not Met"
    overall_class = "pass" if all_met else "fail"
    
    html = f"""
        <div class="threshold-item {overall_class}" style="grid-column: 1 / -1; font-size: 1.1em; margin-bottom: 15px;">
            <span class="threshold-icon">{'✓' if all_met else '✗'}</span>
            <span class="threshold-label">{overall_status}</span>
        </div>
        <div class="threshold-grid">
            {''.join(threshold_items)}
        </div>
    """
    
    return html


def _generate_failure_table(case_results: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
    """Generate failure cases table HTML.
    
    Args:
        case_results: List of per-case results
        metrics: Aggregated metrics
        
    Returns:
        HTML string for failure table
    """
    # Find failed or low-scoring cases
    failure_cases = []
    
    for result in case_results:
        if not result.get("success", False):
            failure_cases.append({
                "case_id": result.get("case_id", "Unknown"),
                "reason": "Processing Failed",
                "error": result.get("error", "Unknown error"),
                "safety_score": 0,
                "quality_score": 0
            })
        else:
            # Check if diagnosis was incorrect
            diagnosis = result.get("diagnosis", {})
            ground_truth = result.get("ground_truth", {})
            differential = diagnosis.get("differential_diagnoses", [])
            expert_diagnosis = ground_truth.get("expert_diagnosis", "")
            
            # Check if correct diagnosis is in top 3
            differential_lower = [d.lower().strip() for d in differential[:3]]
            is_correct = expert_diagnosis.lower().strip() in differential_lower
            
            if not is_correct:
                failure_cases.append({
                    "case_id": result.get("case_id", "Unknown"),
                    "reason": "Incorrect Diagnosis",
                    "predicted": diagnosis.get("primary_diagnosis", "Unknown"),
                    "expected": expert_diagnosis,
                    "safety_score": result.get("safety_score", {}).get("safety_score", 0),
                    "quality_score": result.get("quality_score", {}).get("quality_score", 0)
                })
    
    # Limit to top 10
    failure_cases = failure_cases[:10]
    
    if not failure_cases:
        return '<p class="no-data">No failure cases found! All evaluations passed successfully. 🎉</p>'
    
    rows = []
    for case in failure_cases:
        safety_class = "high" if case["safety_score"] >= 4 else "medium" if case["safety_score"] >= 3 else "low"
        quality_class = "high" if case["quality_score"] >= 4 else "medium" if case["quality_score"] >= 3 else "low"
        
        if case["reason"] == "Processing Failed":
            row = f"""
                <tr>
                    <td class="case-id">{case['case_id']}</td>
                    <td>{case['reason']}</td>
                    <td colspan="2" class="diagnosis-text">{case['error']}</td>
                    <td>-</td>
                    <td>-</td>
                </tr>
            """
        else:
            row = f"""
                <tr>
                    <td class="case-id">{case['case_id']}</td>
                    <td>{case['reason']}</td>
                    <td class="diagnosis-text">{case['predicted']}</td>
                    <td class="diagnosis-text">{case['expected']}</td>
                    <td><span class="score-badge {safety_class}">{case['safety_score']:.1f}</span></td>
                    <td><span class="score-badge {quality_class}">{case['quality_score']:.1f}</span></td>
                </tr>
            """
        rows.append(row)
    
    table_html = f"""
        <table class="failure-table">
            <thead>
                <tr>
                    <th>Case ID</th>
                    <th>Reason</th>
                    <th>Predicted</th>
                    <th>Expected</th>
                    <th>Safety</th>
                    <th>Quality</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
    """
    
    return table_html


def _get_langsmith_url(config: Any) -> str:
    """Get LangSmith dashboard URL.
    
    Args:
        config: Evaluation configuration
        
    Returns:
        LangSmith URL string
    """
    project_name = config.langsmith_project
    # LangSmith URL format
    return f"https://smith.langchain.com/o/default/projects/p/{project_name}"


def save_dashboard(
    metrics: Dict[str, Any],
    case_results: List[Dict[str, Any]],
    config: Any,
    output_dir: str = "./eval_results"
) -> str:
    """Save dashboard to HTML file.
    
    Args:
        metrics: Aggregated metrics
        case_results: Per-case results
        config: Evaluation configuration
        output_dir: Output directory path
        
    Returns:
        Path to saved HTML file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_dashboard_{timestamp}.html"
    output_path = Path(output_dir) / filename
    
    generate_dashboard(metrics, case_results, config, str(output_path))
    
    return str(output_path)



# ============================================================================
# Plotly Visualization Functions
# ============================================================================

def generate_plotly_charts(
    metrics: Dict[str, Any],
    case_results: List[Dict[str, Any]]
) -> Dict[str, str]:
    """Generate all Plotly charts as JSON strings.
    
    Args:
        metrics: Aggregated metrics
        case_results: Per-case results
        
    Returns:
        Dictionary mapping chart IDs to Plotly JSON strings
    """
    import plotly.graph_objects as go
    import plotly.express as px
    import json
    
    charts = {}
    
    # 1. Accuracy Trend Chart
    charts['accuracy-trend'] = _generate_accuracy_trend(case_results)
    
    # 2. Cost vs Accuracy Scatter Plot
    charts['cost-accuracy-scatter'] = _generate_cost_accuracy_scatter(case_results)
    
    # 3. Safety Score Distribution
    charts['safety-distribution'] = _generate_safety_distribution(case_results)
    
    # 4. Latency Distribution
    charts['latency-distribution'] = _generate_latency_distribution(case_results)
    
    return charts


def _generate_accuracy_trend(case_results: List[Dict[str, Any]]) -> str:
    """Generate accuracy trend chart.
    
    Shows cumulative accuracy over cases processed.
    
    Args:
        case_results: Per-case results
        
    Returns:
        Plotly JSON string
    """
    import plotly.graph_objects as go
    import json
    
    # Filter successful cases
    successful_cases = [r for r in case_results if r.get("success", False)]
    
    if not successful_cases:
        return json.dumps({})
    
    # Calculate cumulative accuracy
    case_numbers = []
    cumulative_accuracy = []
    correct_count = 0
    
    for i, result in enumerate(successful_cases, 1):
        diagnosis = result.get("diagnosis", {})
        ground_truth = result.get("ground_truth", {})
        
        differential = diagnosis.get("differential_diagnoses", [])
        expert_diagnosis = ground_truth.get("expert_diagnosis", "")
        
        # Check if correct
        differential_lower = [d.lower().strip() for d in differential[:3]]
        is_correct = expert_diagnosis.lower().strip() in differential_lower
        
        if is_correct:
            correct_count += 1
        
        case_numbers.append(i)
        cumulative_accuracy.append(correct_count / i)
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=case_numbers,
        y=cumulative_accuracy,
        mode='lines+markers',
        name='Cumulative Accuracy',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8, color='#764ba2'),
        hovertemplate='<b>Case %{x}</b><br>Accuracy: %{y:.1%}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Accuracy Trend Over Cases',
        xaxis_title='Number of Cases Evaluated',
        yaxis_title='Cumulative Accuracy',
        yaxis=dict(tickformat='.0%', range=[0, 1.05]),
        hovermode='closest',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return json.dumps(fig.to_dict())


def _generate_cost_accuracy_scatter(case_results: List[Dict[str, Any]]) -> str:
    """Generate cost vs accuracy scatter plot.
    
    Shows relationship between cost and correctness.
    
    Args:
        case_results: Per-case results
        
    Returns:
        Plotly JSON string
    """
    import plotly.graph_objects as go
    import json
    
    # Filter successful cases
    successful_cases = [r for r in case_results if r.get("success", False)]
    
    if not successful_cases:
        return json.dumps({})
    
    costs = []
    correctness = []
    case_ids = []
    
    for result in successful_cases:
        diagnosis = result.get("diagnosis", {})
        ground_truth = result.get("ground_truth", {})
        
        # Calculate cost (rough estimate from tokens)
        tokens = diagnosis.get("tokens_used", 1000)
        cost = (tokens / 1_000_000) * 5.0  # Rough estimate
        
        # Check correctness
        differential = diagnosis.get("differential_diagnoses", [])
        expert_diagnosis = ground_truth.get("expert_diagnosis", "")
        differential_lower = [d.lower().strip() for d in differential[:3]]
        is_correct = expert_diagnosis.lower().strip() in differential_lower
        
        costs.append(cost)
        correctness.append(1 if is_correct else 0)
        case_ids.append(result.get("case_id", "Unknown"))
    
    # Create figure
    fig = go.Figure()
    
    # Separate correct and incorrect
    correct_costs = [c for c, corr in zip(costs, correctness) if corr == 1]
    incorrect_costs = [c for c, corr in zip(costs, correctness) if corr == 0]
    correct_ids = [cid for cid, corr in zip(case_ids, correctness) if corr == 1]
    incorrect_ids = [cid for cid, corr in zip(case_ids, correctness) if corr == 0]
    
    fig.add_trace(go.Scatter(
        x=correct_costs,
        y=[1] * len(correct_costs),
        mode='markers',
        name='Correct',
        marker=dict(size=12, color='#10b981', symbol='circle'),
        text=correct_ids,
        hovertemplate='<b>%{text}</b><br>Cost: $%{x:.4f}<br>Correct<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=incorrect_costs,
        y=[0] * len(incorrect_costs),
        mode='markers',
        name='Incorrect',
        marker=dict(size=12, color='#ef4444', symbol='x'),
        text=incorrect_ids,
        hovertemplate='<b>%{text}</b><br>Cost: $%{x:.4f}<br>Incorrect<extra></extra>'
    ))
    
    fig.update_layout(
        title='Cost vs Diagnostic Accuracy',
        xaxis_title='Estimated Cost per Query (USD)',
        yaxis_title='Correctness',
        yaxis=dict(tickvals=[0, 1], ticktext=['Incorrect', 'Correct']),
        hovermode='closest',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=True
    )
    
    return json.dumps(fig.to_dict())


def _generate_safety_distribution(case_results: List[Dict[str, Any]]) -> str:
    """Generate safety score distribution histogram.
    
    Shows distribution of safety scores across cases.
    
    Args:
        case_results: Per-case results
        
    Returns:
        Plotly JSON string
    """
    import plotly.graph_objects as go
    import json
    
    # Filter successful cases
    successful_cases = [r for r in case_results if r.get("success", False)]
    
    if not successful_cases:
        return json.dumps({})
    
    # Extract safety scores
    safety_scores = []
    for result in successful_cases:
        score = result.get("safety_score", {}).get("safety_score", 0)
        safety_scores.append(score)
    
    # Create histogram
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=safety_scores,
        nbinsx=5,
        marker=dict(
            color='#667eea',
            line=dict(color='white', width=2)
        ),
        hovertemplate='Score: %{x}<br>Count: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Safety Score Distribution',
        xaxis_title='Safety Score (1-5)',
        yaxis_title='Number of Cases',
        xaxis=dict(tickvals=[1, 2, 3, 4, 5]),
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        bargap=0.1
    )
    
    return json.dumps(fig.to_dict())


def _generate_latency_distribution(case_results: List[Dict[str, Any]]) -> str:
    """Generate latency distribution chart.
    
    Shows distribution of response latencies.
    
    Args:
        case_results: Per-case results
        
    Returns:
        Plotly JSON string
    """
    import plotly.graph_objects as go
    import json
    
    # Filter successful cases
    successful_cases = [r for r in case_results if r.get("success", False)]
    
    if not successful_cases:
        return json.dumps({})
    
    # Extract latencies
    latencies = []
    for result in successful_cases:
        latency = result.get("latency_ms", 0)
        latencies.append(latency)
    
    # Create box plot
    fig = go.Figure()
    
    fig.add_trace(go.Box(
        y=latencies,
        name='Latency',
        marker=dict(color='#764ba2'),
        boxmean='sd',
        hovertemplate='Latency: %{y:.0f}ms<extra></extra>'
    ))
    
    fig.update_layout(
        title='Latency Distribution',
        yaxis_title='Latency (ms)',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=False
    )
    
    return json.dumps(fig.to_dict())


def generate_dashboard_with_charts(
    metrics: Dict[str, Any],
    case_results: List[Dict[str, Any]],
    config: Any,
    output_path: Optional[str] = None
) -> str:
    """Generate HTML dashboard with embedded Plotly charts.
    
    Args:
        metrics: Aggregated metrics dictionary
        case_results: List of per-case results
        config: Evaluation configuration
        output_path: Optional path to save HTML file
        
    Returns:
        HTML string for dashboard with charts
    """
    # Generate charts
    charts = generate_plotly_charts(metrics, case_results)
    
    # Generate base HTML
    html = _generate_html_template(metrics, case_results, config)
    
    # Inject chart rendering JavaScript
    chart_scripts = _generate_chart_scripts(charts)
    
    # Insert scripts before closing body tag
    html = html.replace('</body>', f'{chart_scripts}</body>')
    
    # Save to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Dashboard with charts saved to: {output_path}")
    
    return html


def _generate_chart_scripts(charts: Dict[str, str]) -> str:
    """Generate JavaScript to render Plotly charts.
    
    Args:
        charts: Dictionary mapping chart IDs to Plotly JSON strings
        
    Returns:
        JavaScript code as string
    """
    scripts = ['<script>']
    scripts.append('// Render Plotly charts')
    scripts.append('document.addEventListener("DOMContentLoaded", function() {')
    
    for chart_id, chart_json in charts.items():
        if chart_json and chart_json != '{}':
            scripts.append(f'''
    // Render {chart_id}
    var {chart_id.replace("-", "_")}_data = {chart_json};
    var {chart_id.replace("-", "_")}_div = document.getElementById("{chart_id}");
    if ({chart_id.replace("-", "_")}_div) {{
        // Clear placeholder content except title
        var title = {chart_id.replace("-", "_")}_div.querySelector('h3');
        {chart_id.replace("-", "_")}_div.innerHTML = '';
        if (title) {{
            {chart_id.replace("-", "_")}_div.appendChild(title);
        }}
        
        // Render chart with proper configuration
        var config = {{
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        }};
        
        Plotly.newPlot("{chart_id}", {chart_id.replace("-", "_")}_data.data, {chart_id.replace("-", "_")}_data.layout, config);
    }}
''')
    
    scripts.append('});')
    scripts.append('</script>')
    
    return '\n'.join(scripts)
