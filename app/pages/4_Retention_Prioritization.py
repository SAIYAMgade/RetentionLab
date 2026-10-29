"""
RetentionLab Page 4: Retention Prioritization.
Revenue-aware operational ranking and customer success action dispatcher.
"""

from pathlib import Path
import plotly.express as px
import streamlit as st
import pandas as pd
from app.components.ui import inject_custom_css, render_header, render_kpi
from retentionlab.config.settings import settings

st.set_page_config(page_title="Retention Prioritization | RetentionLab", page_icon="🎯", layout="wide")
inject_custom_css()

render_header(
    title="Customer Retention Prioritization Engine",
    subtitle="Revenue-Aware Queue Ranking, Exposure Analysis & Action Recommendations",
)

scores_path = settings.root_dir / "data" / "processed" / "customer_prioritization.csv"
if not scores_path.exists():
    st.warning("Scored dataset not found. Please run the scoring pipeline first.")
    st.stop()

scored_df = pd.read_csv(scores_path)

# Top explanation callout
st.markdown(
    """
    <div style="background-color: #f1f5f9; border-left: 4px solid #00a896; padding: 0.85rem 1.25rem; border-radius: 4px; margin-bottom: 1rem;">
        <strong>Prioritization Scoring Methodology:</strong><br>
        <code>Prioritization Score = 0.55 * Churn_Probability + 0.45 * Normalized_Annual_Spend</code><br>
        <span style="font-size: 0.85rem; color: #64748b;">
        Accounts are ranked so Customer Success teams prioritize high-value, high-risk accounts where intervention delivers maximum revenue protection.
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar Controls
st.sidebar.markdown("### 🎛️ Queue Settings")
cohort_pct = st.sidebar.slider("Top Cohort Threshold (%)", min_value=5, max_value=30, value=15, step=5)
selected_actions = st.sidebar.multiselect(
    "Action Category Filter",
    options=sorted(scored_df["suggested_action"].dropna().unique()),
    default=sorted(scored_df["suggested_action"].dropna().unique()),
)
min_exposure = st.sidebar.number_input("Minimum Risk Exposure ($)", min_value=0.0, value=0.0, step=1000.0)

# Dynamically calculate cohort based on slider
n_cohort = int(len(scored_df) * (cohort_pct / 100.0))
ranked_df = scored_df.sort_values(
    ["prioritization_score", "risk_weighted_exposure", "churn_probability"],
    ascending=[False, False, False]
).reset_index(drop=True)
ranked_df["retention_rank"] = range(1, len(ranked_df) + 1)
ranked_df["is_selected_cohort"] = 0
ranked_df.loc[: n_cohort - 1, "is_selected_cohort"] = 1

# Filter for table
display_df = ranked_df[
    (ranked_df["is_selected_cohort"] == 1)
    & (ranked_df["suggested_action"].isin(selected_actions))
    & (ranked_df["risk_weighted_exposure"] >= min_exposure)
]

# Cohort KPIs
total_accounts = len(display_df)
cohort_exposure = display_df["risk_weighted_exposure"].sum()
portfolio_exposure = scored_df["risk_weighted_exposure"].sum()
avg_val = display_df["historical_value_proxy"].mean() if total_accounts > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi("Prioritized Accounts", f"{total_accounts:,d}", f"Top {cohort_pct}% cohort", theme="navy")
with col2:
    render_kpi("Risk-Weighted Exposure", f"${cohort_exposure/1e6:.2f}M", f"{cohort_exposure/portfolio_exposure:.1%} of portfolio risk" if portfolio_exposure > 0 else "$0", theme="coral")
with col3:
    render_kpi("Mean Annualized Spend", f"${avg_val:,.0f}", "High historical contribution", theme="teal")
with col4:
    vip_count = len(display_df[display_df["suggested_action"] == "VIP Human Touchpoint"])
    render_kpi("VIP Touchpoints", f"{vip_count:,d}", "Requires dedicated CSM review", theme="amber")

st.markdown("---")

# Visual: Action Category Distribution
col_v1, col_v2 = st.columns([1, 1])

with col_v1:
    st.markdown("#### 📋 Recommended Action Breakdown")
    act_counts = display_df["suggested_action"].value_counts().reset_index()
    act_counts.columns = ["Action Category", "Count"]
    fig_act = px.bar(
        act_counts,
        x="Count",
        y="Action Category",
        orientation="h",
        color="Action Category",
        color_discrete_sequence=["#0f2942", "#00a896", "#028090", "#f59e0b", "#e63946"],
        text="Count",
    )
    fig_act.update_traces(textposition="outside")
    fig_act.update_layout(height=320, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
    st.plotly_chart(fig_act, use_container_width=True)

with col_v2:
    st.markdown("#### 🎯 Risk Band Distribution in Prioritized Cohort")
    band_order = ["Critical Risk", "High Risk", "Moderate Risk", "Low Risk"]
    color_map = {"Critical Risk": "#e63946", "High Risk": "#f59e0b", "Moderate Risk": "#028090", "Low Risk": "#10b981"}
    b_counts = display_df["risk_band"].value_counts().reindex(band_order).fillna(0).reset_index()
    b_counts.columns = ["Risk Band", "Count"]
    fig_b = px.bar(
        b_counts,
        x="Risk Band",
        y="Count",
        color="Risk Band",
        color_discrete_map=color_map,
        text="Count",
    )
    fig_b.update_traces(textposition="outside")
    fig_b.update_layout(height=320, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
    st.plotly_chart(fig_b, use_container_width=True)

st.markdown("---")

# Worklist Table
st.markdown("#### 📑 Prioritized Customer Worklist")

table_cols = [
    "retention_rank",
    "customer_id",
    "risk_band",
    "churn_probability",
    "historical_value_proxy",
    "risk_weighted_exposure",
    "prioritization_score",
    "top_risk_signals",
    "suggested_action",
    "recommended_next_step",
]

st.dataframe(
    display_df[table_cols].rename(
        columns={
            "retention_rank": "Rank",
            "customer_id": "Customer ID",
            "risk_band": "Risk Tier",
            "churn_probability": "Churn Prob",
            "historical_value_proxy": "Annual Spend ($)",
            "risk_weighted_exposure": "Exposure ($)",
            "prioritization_score": "Priority Score",
            "top_risk_signals": "Leading Risk Signals",
            "suggested_action": "Action Category",
            "recommended_next_step": "Operational Next Step",
        }
    ),
    use_container_width=True,
    height=480,
)

# Export controls
csv_data = display_df[table_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Export Current Filtered Prioritization Worklist (CSV)",
    data=csv_data,
    file_name=f"retention_prioritized_top_{cohort_pct}pct.csv",
    mime="text/csv",
)
