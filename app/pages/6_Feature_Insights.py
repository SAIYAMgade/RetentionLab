"""
RetentionLab Page 6: Feature Insights & Behavioral Attribution.
Inspects the 44 documented features and model-derived importance weights.
"""

from pathlib import Path
import plotly.express as px
import streamlit as st
import pandas as pd
from app.components.ui import inject_custom_css, render_header, render_kpi
from retentionlab.config.settings import settings
from retentionlab.features.catalog import FEATURE_CATALOG

st.set_page_config(page_title="Feature Insights | RetentionLab", page_icon="🧬", layout="wide")
inject_custom_css()

render_header(
    title="Feature Engineering & Behavioral Insights",
    subtitle="Documentation & Predictive Contributions of the 44 Documented Behavioral Features",
)

col1, col2, col3 = st.columns(3)
with col1:
    render_kpi("Engineered Features", "44", "Exact documented catalog count", theme="navy")
with col2:
    render_kpi("Feature Categories", "6", "Multi-dimensional behavioral vectors", theme="teal")
with col3:
    render_kpi("Snapshot Observation", "2026-04-01", "Strictly historical event window", theme="amber")

st.markdown("---")

# Feature Importance Chart
imp_path = settings.root_dir / "models" / "feature_importance.csv"
if imp_path.exists():
    imp_df = pd.read_csv(imp_path)
    top_15_imp = imp_df.head(15).sort_values("abs_importance", ascending=True)

    st.markdown("#### 🏆 Top 15 Predictive Features by Absolute Importance")
    fig_imp = px.bar(
        top_15_imp,
        x="abs_importance",
        y="feature_name",
        orientation="h",
        color="abs_importance",
        color_continuous_scale="Blues",
        labels={"abs_importance": "Absolute Model Weight / Importance", "feature_name": "Behavioral Feature"},
    )
    fig_imp.update_layout(height=480, margin=dict(t=20, b=20, l=20, r=20), coloraxis_showscale=False)
    st.plotly_chart(fig_imp, use_container_width=True)

st.markdown("---")

# Full 44-Feature Catalog
st.markdown("#### 📖 Complete 44-Feature Behavioral Dictionary")

df_cat = pd.DataFrame(FEATURE_CATALOG)
selected_cat = st.selectbox(
    "Filter by Feature Category",
    options=["All Categories"] + sorted(df_cat["category"].unique().tolist()),
)

if selected_cat != "All Categories":
    display_cat = df_cat[df_cat["category"] == selected_cat]
else:
    display_cat = df_cat

st.dataframe(
    display_cat.rename(
        columns={
            "name": "Feature Name",
            "category": "Category",
            "unit": "Unit",
            "formula": "Calculation Formula",
            "description": "Business Description",
            "risk_direction": "Risk Relationship",
            "missing_handling": "Missing Value Strategy",
        }
    ),
    use_container_width=True,
    height=450,
)
