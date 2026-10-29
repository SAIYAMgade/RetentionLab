"""
RetentionLab Page 1: Executive Overview.
High-level portfolio health, risk exposure, and segment breakdown.
"""

from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from app.components.ui import inject_custom_css, render_header, render_kpi
from retentionlab.config.settings import settings
from retentionlab.database.connection import execute_query

st.set_page_config(page_title="Executive Overview | RetentionLab", page_icon="📊", layout="wide")
inject_custom_css()

render_header(
    title="Executive Retention Overview",
    subtitle="Portfolio Risk Distribution, Revenue Exposure & Operational Cohorts",
)

# Load data
scores_path = settings.root_dir / "data" / "processed" / "customer_prioritization.csv"
cust_df = execute_query("SELECT * FROM customers")

if not scores_path.exists():
    st.warning("Scored dataset not found. Please run the scoring pipeline first.")
    st.stop()

scored_df = pd.read_csv(scores_path)
merged = pd.merge(scored_df, cust_df[["customer_id", "customer_segment", "region", "subscription_type", "acquisition_channel"]], on="customer_id", how="left")

# Sidebar Filters
st.sidebar.markdown("### 🔍 Global Filters")
selected_segments = st.sidebar.multiselect(
    "Customer Segment",
    options=sorted(merged["customer_segment"].dropna().unique()),
    default=sorted(merged["customer_segment"].dropna().unique()),
)
selected_regions = st.sidebar.multiselect(
    "Region",
    options=sorted(merged["region"].dropna().unique()),
    default=sorted(merged["region"].dropna().unique()),
)
selected_subs = st.sidebar.multiselect(
    "Subscription Type",
    options=sorted(merged["subscription_type"].dropna().unique()),
    default=sorted(merged["subscription_type"].dropna().unique()),
)

# Apply filters
filtered_df = merged[
    (merged["customer_segment"].isin(selected_segments))
    & (merged["region"].isin(selected_regions))
    & (merged["subscription_type"].isin(selected_subs))
]

if filtered_df.empty:
    st.error("No customers match the selected filter criteria. Please broaden your selection.")
    st.stop()

# KPIs
total_cust = len(filtered_df)
high_crit_cnt = len(filtered_df[filtered_df["risk_band"].isin(["Critical Risk", "High Risk"])])
top_cohort_cnt = int(filtered_df["is_top_15_percent"].sum())
total_exp = filtered_df["risk_weighted_exposure"].sum()
top_exp = filtered_df.loc[filtered_df["is_top_15_percent"] == 1, "risk_weighted_exposure"].sum()
avg_prob = filtered_df["churn_probability"].mean()

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi("Filtered Customers", f"{total_cust:,d}", f"{total_cust/len(merged):.1%} of portfolio", theme="navy")
with c2:
    render_kpi("High & Critical Risk", f"{high_crit_cnt:,d}", f"{high_crit_cnt/total_cust:.1%} of filtered base", theme="coral")
with c3:
    render_kpi("Top 15% Review Cohort", f"{top_cohort_cnt:,d}", "Actionable worklist accounts", theme="teal")
with c4:
    render_kpi("Top Cohort Exposure", f"${top_exp/1e6:.2f}M", f"{top_exp/total_exp:.1%} of total risk" if total_exp > 0 else "$0", theme="amber")

st.markdown("---")

# Visualizations Row 1
col_v1, col_v2 = st.columns([1, 1])

with col_v1:
    st.markdown("#### 🎯 Customer Risk Tier Distribution")
    band_order = ["Critical Risk", "High Risk", "Moderate Risk", "Low Risk"]
    color_map = {
        "Critical Risk": "#e63946",
        "High Risk": "#f59e0b",
        "Moderate Risk": "#028090",
        "Low Risk": "#10b981",
    }
    tier_counts = filtered_df["risk_band"].value_counts().reindex(band_order).fillna(0).reset_index()
    tier_counts.columns = ["Risk Tier", "Customers"]

    fig_tier = px.bar(
        tier_counts,
        x="Risk Tier",
        y="Customers",
        color="Risk Tier",
        color_discrete_map=color_map,
        text="Customers",
    )
    fig_tier.update_traces(textposition="outside")
    fig_tier.update_layout(height=340, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
    st.plotly_chart(fig_tier, use_container_width=True)

with col_v2:
    st.markdown("#### 💰 Risk-Weighted Exposure by Segment")
    seg_exp = filtered_df.groupby("customer_segment")["risk_weighted_exposure"].sum().reset_index()
    fig_seg = px.pie(
        seg_exp,
        names="customer_segment",
        values="risk_weighted_exposure",
        color_discrete_sequence=["#0f2942", "#00a896", "#028090", "#f59e0b"],
        hole=0.45,
    )
    fig_seg.update_layout(height=340, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_seg, use_container_width=True)

st.markdown("---")

# Monthly Transaction Trend from Database
st.markdown("#### 📈 Historical Platform Transaction & GMV Trajectory")
txn_trend = execute_query(
    """
    SELECT 
        STRFTIME('%Y-%m', transaction_date) AS month,
        ROUND(SUM(CASE WHEN transaction_status = 'Success' THEN transaction_amount ELSE 0 END), 2) AS gmv,
        COUNT(transaction_id) AS txns
    FROM transactions
    GROUP BY STRFTIME('%Y-%m', transaction_date)
    ORDER BY month ASC
    """
)
fig_trend = go.Figure()
fig_trend.add_trace(
    go.Bar(
        x=txn_trend["month"],
        y=txn_trend["gmv"],
        name="Gross Revenue ($)",
        marker_color="#0f2942",
        yaxis="y",
    )
)
fig_trend.add_trace(
    go.Scatter(
        x=txn_trend["month"],
        y=txn_trend["txns"],
        name="Transaction Volume",
        marker_color="#00a896",
        mode="lines+markers",
        line=dict(width=3),
        yaxis="y2",
    )
)
fig_trend.update_layout(
    height=360,
    margin=dict(t=30, b=20, l=20, r=20),
    yaxis=dict(title="Gross Revenue ($)"),
    yaxis2=dict(title="Transaction Count", overlaying="y", side="right"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_trend, use_container_width=True)
