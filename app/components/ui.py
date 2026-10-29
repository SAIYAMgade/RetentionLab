"""
RetentionLab UI Component Library & Enterprise Styling.
Provides clean navy, teal, and neutral design styling for Streamlit.
"""

from typing import Any, Dict, Optional
import streamlit as st
import pandas as pd


def inject_custom_css() -> None:
    """Inject polished enterprise CSS styling into Streamlit."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Main page container */
        .main .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            max-width: 1280px;
        }
        
        /* Executive Header Banner */
        .retentionlab-header {
            background: linear-gradient(135deg, #0f2942 0%, #1b3a57 100%);
            color: #ffffff;
            padding: 1.25rem 1.75rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            border-left: 5px solid #00a896;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        .retentionlab-header h1 {
            color: #ffffff !important;
            font-size: 1.6rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .retentionlab-header p {
            color: #94a3b8 !important;
            font-size: 0.9rem !important;
            margin-top: 0.25rem !important;
            margin-bottom: 0 !important;
        }
        
        /* Metric KPI Cards */
        .kpi-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            border-top: 3px solid #0f2942;
        }
        .kpi-card.teal { border-top-color: #00a896; }
        .kpi-card.coral { border-top-color: #e63946; }
        .kpi-card.amber { border-top-color: #f59e0b; }
        
        .kpi-label {
            font-size: 0.8rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }
        .kpi-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #0f2942;
            margin-bottom: 0.15rem;
        }
        .kpi-subtext {
            font-size: 0.8rem;
            color: #94a3b8;
        }
        
        /* Risk Badges */
        .risk-badge {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-align: center;
        }
        .risk-critical { background-color: #fee2e2; color: #b91c1c; }
        .risk-high { background-color: #ffedd5; color: #c2410c; }
        .risk-moderate { background-color: #fef9c3; color: #854d0e; }
        .risk-low { background-color: #dcfce7; color: #15803d; }
        
        /* Section Dividers */
        .section-title {
            color: #0f2942;
            font-size: 1.15rem;
            font-weight: 700;
            margin-top: 1.25rem;
            margin-bottom: 0.75rem;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title: str, subtitle: str) -> None:
    """Render standard executive navy banner."""
    st.markdown(
        f"""
        <div class="retentionlab-header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(label: str, value: str, subtext: str = "", theme: str = "navy") -> None:
    """Render a styled KPI card."""
    st.markdown(
        f"""
        <div class="kpi-card {theme}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-subtext">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
