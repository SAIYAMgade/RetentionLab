"""
RetentionLab Page 2: Customer Explorer.
Interactive customer-level drilldown with granular filters and behavioral inspection.
"""

from pathlib import Path
import streamlit as st
import pandas as pd
from app.components.ui import inject_custom_css, render_header, render_kpi
from retentionlab.config.settings import settings
from retentionlab.database.connection import execute_query

st.set_page_config(page_title="Customer Explorer | RetentionLab", page_icon="🔎", layout="wide")
inject_custom_css()

render_header(
    title="Customer Risk Explorer",
    subtitle="Granular Customer Drilldown, Feature Inspection & Behavioral Attribution",
)

scores_path = settings.root_dir / "data" / "processed" / "customer_prioritization.csv"
if not scores_path.exists():
    st.warning("Scored dataset not found. Please run the scoring pipeline first.")
    st.stop()

scored_df = pd.read_csv(scores_path)
cust_df = execute_query("SELECT * FROM customers")
merged = pd.merge(scored_df, cust_df[["customer_id", "customer_segment", "region", "subscription_type", "acquisition_channel", "signup_date"]], on="customer_id", how="left")

# Filters Sidebar
st.sidebar.markdown("### 🔍 Customer Filters")
filter_band = st.sidebar.multiselect(
    "Risk Band",
    options=["Critical Risk", "High Risk", "Moderate Risk", "Low Risk"],
    default=["Critical Risk", "High Risk"],
)
filter_segment = st.sidebar.multiselect(
    "Customer Segment",
    options=sorted(merged["customer_segment"].dropna().unique()),
    default=sorted(merged["customer_segment"].dropna().unique()),
)
min_spend, max_spend = float(merged["historical_value_proxy"].min()), float(merged["historical_value_proxy"].max())
selected_spend_range = st.sidebar.slider(
    "Annualized Spend Range ($)",
    min_value=0.0,
    max_value=max_spend,
    value=(0.0, max_spend),
    step=500.0,
)
search_cust = st.sidebar.text_input("Search Customer ID", placeholder="e.g. CUST-00042")

filtered_df = merged[
    (merged["risk_band"].isin(filter_band))
    & (merged["customer_segment"].isin(filter_segment))
    & (merged["historical_value_proxy"] >= selected_spend_range[0])
    & (merged["historical_value_proxy"] <= selected_spend_range[1])
]

if search_cust:
    filtered_df = filtered_df[filtered_df["customer_id"].str.contains(search_cust.strip(), case=False)]

st.markdown(f"**Showing {len(filtered_df):,d} matching accounts**")

# Two column layout: Table on Left, Customer Detail Inspector on Right
col_table, col_inspect = st.columns([3, 2])

with col_table:
    display_cols = [
        "customer_id",
        "customer_segment",
        "risk_band",
        "churn_probability",
        "historical_value_proxy",
        "prioritization_score",
        "top_risk_signals",
    ]
    st.dataframe(
        filtered_df[display_cols].rename(
            columns={
                "customer_id": "Customer ID",
                "customer_segment": "Segment",
                "risk_band": "Risk Tier",
                "churn_probability": "Churn Prob",
                "historical_value_proxy": "Annual Spend ($)",
                "prioritization_score": "Priority Score",
                "top_risk_signals": "Leading Risk Signals",
            }
        ),
        use_container_width=True,
        height=520,
    )

with col_inspect:
    st.markdown("#### 👤 Account Behavioral Dossier")
    if not filtered_df.empty:
        selected_id = st.selectbox("Select Customer to Inspect", options=filtered_df["customer_id"].tolist())
        c_row = filtered_df[filtered_df["customer_id"] == selected_id].iloc[0]

        # Account details box
        band = c_row["risk_band"]
        badge_class = "risk-critical" if band == "Critical Risk" else (
            "risk-high" if band == "High Risk" else (
                "risk-moderate" if band == "Moderate Risk" else "risk-low"
            )
        )

        st.markdown(
            f"""
            <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <h3 style="margin: 0; color: #0f2942;">{c_row['customer_id']}</h3>
                    <span class="risk-badge {badge_class}">{c_row['risk_band']}</span>
                </div>
                <div style="font-size: 0.9rem; color: #475569; margin-bottom: 0.5rem;">
                    <strong>Segment:</strong> {c_row['customer_segment']} | <strong>Region:</strong> {c_row['region']} | <strong>Plan:</strong> {c_row['subscription_type']}
                </div>
                <div style="font-size: 0.9rem; color: #475569; margin-bottom: 0.75rem;">
                    <strong>Member Since:</strong> {c_row['signup_date']} | <strong>Tenure:</strong> {c_row['tenure_days']} days
                </div>
                <hr style="margin: 0.75rem 0; border: 0; border-top: 1px solid #e2e8f0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.75rem;">
                    <div><strong>Estimated Churn Risk:</strong> <span style="font-size: 1.1rem; color: #0f2942; font-weight: 700;">{c_row['churn_probability']:.1%}</span></div>
                    <div><strong>Priority Score:</strong> <span style="font-size: 1.1rem; color: #00a896; font-weight: 700;">{c_row['prioritization_score']:.3f}</span></div>
                    <div><strong>Annualized Spend:</strong> ${c_row['historical_value_proxy']:,.2f}</div>
                    <div><strong>Risk Exposure:</strong> ${c_row['risk_weighted_exposure']:,.2f}</div>
                </div>
                <hr style="margin: 0.75rem 0; border: 0; border-top: 1px solid #e2e8f0;">
                <div>
                    <strong>Leading Risk Signals:</strong>
                    <div style="background-color: #ffffff; border-left: 3px solid #e63946; padding: 0.5rem 0.75rem; margin-top: 0.35rem; font-size: 0.85rem; color: #334155;">
                        {c_row['top_risk_signals']}
                    </div>
                </div>
                <div style="margin-top: 0.75rem;">
                    <strong>Operational Recommendation:</strong>
                    <div style="background-color: #ffffff; border-left: 3px solid #00a896; padding: 0.5rem 0.75rem; margin-top: 0.35rem; font-size: 0.85rem; color: #334155;">
                        <strong>{c_row['suggested_action']}</strong>: {c_row['recommended_next_step']}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("No customer available under current filters.")
