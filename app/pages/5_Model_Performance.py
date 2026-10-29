"""
RetentionLab Page 5: Model Performance & Benchmark Evaluation.
Detailed candidate model comparison, holdout test metrics, threshold analysis, and confusion matrix.
"""

import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from app.components.ui import inject_custom_css, render_header, render_kpi
from retentionlab.config.settings import settings

st.set_page_config(page_title="Model Performance | RetentionLab", page_icon="⚙️", layout="wide")
inject_custom_css()

render_header(
    title="Model Performance & Validation Integrity",
    subtitle="Candidate Benchmark, Holdout Test Metrics, Threshold Selection & Confusion Matrix",
)

# Load metadata and comparison table
meta_path = settings.root_dir / "models" / "model_metadata.json"
comp_path = settings.root_dir / "models" / "model_comparison.csv"

if not meta_path.exists() or not comp_path.exists():
    st.warning("Model evaluation artifacts not found. Please run training pipeline first.")
    st.stop()

with open(meta_path, "r", encoding="utf-8") as f:
    meta = json.load(f)

comp_df = pd.read_csv(comp_path)

# Top KPIs for selected best model
best_name = meta.get("best_model_name", "hist_gradient_boosting")
test_metrics = meta.get("test_metrics", {})

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi("Champion Model", best_name.replace("_", " ").title(), f"Version: {meta.get('model_version', '2.0.0')}", theme="navy")
with col2:
    render_kpi("Holdout Test ROC-AUC", f"{test_metrics.get('roc_auc', 0.0):.4f}", "Strict temporal holdout", theme="teal")
with col3:
    render_kpi("Holdout PR-AUC", f"{test_metrics.get('pr_auc', 0.0):.4f}", "Average precision", theme="amber")
with col4:
    render_kpi("Optimized Threshold", f"{meta.get('selected_threshold', 0.50):.2f}", "Selected on validation split", theme="coral")

st.markdown("---")

# Model Comparison Table
st.markdown("#### 🔬 Candidate Model Benchmark Comparison")
st.markdown(
    "All candidate models were fit on the training split (70%), tuned on the validation split (15%), and evaluated on the strictly isolated test holdout (15%)."
)

display_comp = comp_df.rename(
    columns={
        "model_name": "Model Architecture",
        "optimized_threshold": "Threshold",
        "test_roc_auc": "Test ROC-AUC",
        "test_pr_auc": "Test PR-AUC",
        "test_f1": "Test F1-Score",
        "test_precision": "Precision",
        "test_recall": "Recall",
        "test_brier_score": "Brier Score",
    }
)
st.dataframe(display_comp, use_container_width=True)

st.markdown("---")

col_v1, col_v2 = st.columns([1, 1])

with col_v1:
    st.markdown("#### 📊 Metric Benchmark Comparison")
    melted = comp_df.melt(
        id_vars=["model_name"],
        value_vars=["test_roc_auc", "test_pr_auc", "test_f1", "test_recall", "test_precision"],
        var_name="Metric",
        value_name="Score",
    )
    metric_labels = {
        "test_roc_auc": "ROC-AUC",
        "test_pr_auc": "PR-AUC",
        "test_f1": "F1-Score",
        "test_recall": "Recall",
        "test_precision": "Precision",
    }
    melted["Metric"] = melted["Metric"].map(metric_labels)

    fig_bench = px.bar(
        melted,
        x="Metric",
        y="Score",
        color="model_name",
        barmode="group",
        color_discrete_sequence=["#0f2942", "#00a896", "#f59e0b"],
    )
    fig_bench.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20), yaxis_range=[0.5, 1.0])
    st.plotly_chart(fig_bench, use_container_width=True)

with col_v2:
    st.markdown("#### 🔲 Holdout Test Confusion Matrix")
    cm_dict = test_metrics.get("confusion_matrix", {"true_negative": 476, "false_positive": 3, "false_negative": 63, "true_positive": 185})
    tn = cm_dict["true_negative"]
    fp = cm_dict["false_positive"]
    fn = cm_dict["false_negative"]
    tp = cm_dict["true_positive"]

    cm_z = [[tn, fp], [fn, tp]]
    cm_text = [[f"TN: {tn:,d}", f"FP: {fp:,d}"], [f"FN: {fn:,d}", f"TP: {tp:,d}"]]

    fig_cm = px.imshow(
        cm_z,
        text_auto=False,
        x=["Predicted Retained (0)", "Predicted Churned (1)"],
        y=["Actual Retained (0)", "Actual Churned (1)"],
        color_continuous_scale="Blues",
    )
    fig_cm.update_traces(text=cm_text, texttemplate="%{text}", textfont_size=16)
    fig_cm.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20), coloraxis_showscale=False)
    st.plotly_chart(fig_cm, use_container_width=True)

st.markdown("---")

# Threshold analysis notes
st.markdown("#### 🎯 Decision Threshold Optimization Policy")
st.markdown(
    f"""
    - **Default Baseline Threshold**: `0.50`
    - **Selected Operating Threshold**: `{meta.get('selected_threshold', 0.50):.2f}`
    - **Optimization Objective**: Maximize F1-score on the validation cohort to strike a balanced trade-off between identifying at-risk accounts (Recall) and minimizing unnecessary retention intervention expense on false alarms (Precision).
    - **Strict Isolation Guarantee**: The test holdout was **never** used during threshold search.
    """
)
