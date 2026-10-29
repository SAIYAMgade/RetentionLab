"""
RetentionLab Page 3: Churn Analytics.
Descriptive and cohort analysis of churn relationships across segments and channels.
"""

from pathlib import Path
import plotly.express as px
import streamlit as st
import pandas as pd
from app.components.ui import inject_custom_css, render_header
from retentionlab.config.settings import settings
from retentionlab.database.connection import execute_query

st.set_page_config(page_title="Churn Analytics | RetentionLab", page_icon="📉", layout="wide")
inject_custom_css()

render_header(
    title="Descriptive Churn Analytics",
    subtitle="Behavioral Decay Patterns, Cohort Trends & Channel Attrition",
)

st.info("ℹ️ **Methodology Notice**: The analyses presented here reflect historical descriptive correlations and observed associations. They do not demonstrate direct causation.")

# Load database analytics
channel_churn = execute_query(
    """
    SELECT 
        acquisition_channel,
        total_acquired_customers,
        churned_customers,
        churn_rate_pct,
        retention_rate_pct,
        revenue_per_customer
    FROM (
        SELECT 
            c.acquisition_channel,
            COUNT(DISTINCT c.customer_id) AS total_acquired_customers,
            COUNT(DISTINCT CASE 
                WHEN NOT EXISTS (
                    SELECT 1 FROM transactions t2 
                    WHERE t2.customer_id = c.customer_id 
                      AND t2.transaction_date > '2026-04-01' 
                      AND t2.transaction_date <= '2026-05-31' 
                      AND t2.transaction_status = 'Success'
                ) AND c.tenure_days >= 30 THEN c.customer_id 
            END) AS churned_customers,
            ROUND(SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END), 2) AS total_channel_revenue,
            ROUND(100.0 * COUNT(DISTINCT CASE 
                WHEN NOT EXISTS (
                    SELECT 1 FROM transactions t2 
                    WHERE t2.customer_id = c.customer_id 
                      AND t2.transaction_date > '2026-04-01' 
                      AND t2.transaction_date <= '2026-05-31' 
                      AND t2.transaction_status = 'Success'
                ) AND c.tenure_days >= 30 THEN c.customer_id 
            END) / COUNT(DISTINCT c.customer_id), 2) AS churn_rate_pct,
            ROUND(100.0 - (100.0 * COUNT(DISTINCT CASE 
                WHEN NOT EXISTS (
                    SELECT 1 FROM transactions t2 
                    WHERE t2.customer_id = c.customer_id 
                      AND t2.transaction_date > '2026-04-01' 
                      AND t2.transaction_date <= '2026-05-31' 
                      AND t2.transaction_status = 'Success'
                ) AND c.tenure_days >= 30 THEN c.customer_id 
            END) / COUNT(DISTINCT c.customer_id)), 2) AS retention_rate_pct,
            ROUND(SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_customer
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        GROUP BY c.acquisition_channel
    )
    ORDER BY churn_rate_pct DESC
    """
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📡 Churn Rate by Acquisition Channel")
    fig_chan = px.bar(
        channel_churn,
        x="acquisition_channel",
        y="churn_rate_pct",
        color="acquisition_channel",
        color_discrete_sequence=["#e63946", "#f59e0b", "#028090", "#0f2942", "#10b981"],
        text=channel_churn["churn_rate_pct"].apply(lambda v: f"{v:.1f}%"),
    )
    fig_chan.update_traces(textposition="outside")
    fig_chan.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20), yaxis_title="Churn Rate (%)", showlegend=False)
    st.plotly_chart(fig_chan, use_container_width=True)

with col2:
    st.markdown("#### 💼 Revenue per Customer by Channel")
    fig_rev = px.bar(
        channel_churn,
        x="acquisition_channel",
        y="revenue_per_customer",
        color="acquisition_channel",
        color_discrete_sequence=["#0f2942", "#00a896", "#028090", "#f59e0b", "#e63946"],
        text=channel_churn["revenue_per_customer"].apply(lambda v: f"${v:,.0f}"),
    )
    fig_rev.update_traces(textposition="outside")
    fig_rev.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20), yaxis_title="Average Revenue ($)", showlegend=False)
    st.plotly_chart(fig_rev, use_container_width=True)

st.markdown("---")

# Segment Churn & Refund Rates
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### 🏢 Customer Segment Churn & Concentration")
    seg_stats = execute_query(
        """
        SELECT 
            c.customer_segment,
            COUNT(DISTINCT c.customer_id) AS customers,
            ROUND(AVG(c.tenure_days), 1) AS avg_tenure_days,
            ROUND(SUM(CASE WHEN t.transaction_status = 'Success' THEN t.transaction_amount ELSE 0 END), 2) AS total_revenue
        FROM customers c
        LEFT JOIN transactions t ON c.customer_id = t.customer_id
        GROUP BY c.customer_segment
        ORDER BY total_revenue DESC
        """
    )
    fig_seg_bar = px.bar(
        seg_stats,
        x="customer_segment",
        y="total_revenue",
        color="customer_segment",
        color_discrete_sequence=["#0f2942", "#00a896", "#028090", "#f59e0b"],
        text=seg_stats["total_revenue"].apply(lambda v: f"${v/1e6:.1f}M"),
    )
    fig_seg_bar.update_traces(textposition="outside")
    fig_seg_bar.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20), yaxis_title="Total GMV ($)", showlegend=False)
    st.plotly_chart(fig_seg_bar, use_container_width=True)

with col4:
    st.markdown("#### ⚠️ Payment Failure Impact by Subscription Model")
    pay_fail = execute_query(
        """
        SELECT 
            c.subscription_type,
            COUNT(t.transaction_id) AS attempts,
            ROUND(100.0 * COUNT(CASE WHEN t.payment_status = 'Failed' THEN 1 END) / COUNT(t.transaction_id), 2) AS fail_rate_pct
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        GROUP BY c.subscription_type
        ORDER BY fail_rate_pct DESC
        """
    )
    fig_fail = px.bar(
        pay_fail,
        x="subscription_type",
        y="fail_rate_pct",
        color="subscription_type",
        color_discrete_sequence=["#e63946", "#f59e0b", "#028090"],
        text=pay_fail["fail_rate_pct"].apply(lambda v: f"{v:.1f}%"),
    )
    fig_fail.update_traces(textposition="outside")
    fig_fail.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20), yaxis_title="Failure Rate (%)", showlegend=False)
    st.plotly_chart(fig_fail, use_container_width=True)
