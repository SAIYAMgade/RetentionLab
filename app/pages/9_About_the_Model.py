"""
RetentionLab Page 9: About the Model, Methodology & Limitations.
Documents model design, training protocol, ethical AI governance, and analytical boundaries.
"""

from pathlib import Path
import streamlit as st
from app.components.ui import inject_custom_css, render_header

st.set_page_config(page_title="About the Model | RetentionLab", page_icon="📖", layout="wide")
inject_custom_css()

render_header(
    title="Model Methodology, Governance & Limitations",
    subtitle="Prediction Framing, Temporal Validation, Ethical AI Guidelines & Operating Boundaries",
)

st.markdown(
    """
    ### 1. Prediction Framing & Target Definition
    - **Snapshot Date ($T$)**: `2026-04-01`
    - **Historical Observation Window**: Trailing 180 calendar days ($T - 180\\text{d} \\le t \\le T$).
    - **Prediction Horizon**: 60 calendar days ($T < t \\le T + 60\\text{d}$).
    - **Target Label (`is_churn`)**:
      - `1` (Churned): The customer completed **0 successful purchase/renewal transactions** in the 60-day prediction horizon.
      - `0` (Retained): The customer completed **1 or more successful transactions** in the 60-day prediction horizon.
    - **Eligibility Criteria**: Accounts must possess at least 30 days of active tenure prior to snapshot date. New accounts under 30 days are excluded from training and scoring.

    ---

    ### 2. Temporal Data Splitting & Leakage Prevention
    - **Training Set (70%)**: Used exclusively to fit preprocessing pipelines (imputation, scaling) and train candidate classifiers.
    - **Validation Set (15%)**: Used to compare candidate models and determine the optimal decision threshold.
    - **Holdout Test Set (15%)**: Strictly isolated until final evaluation. **Never** used for feature selection, hyperparameter tuning, or threshold selection.
    - **Feature Leakage Prevention**: All 44 behavioral features are computed strictly on transactions, logins, tickets, and campaigns with timestamps $\\le T$.

    ---

    ### 3. Model Comparison & Selection Rationale
    Three distinct architectures were evaluated:
    1. **Logistic Regression (Interpretable Baseline)**:
       - Uses `StandardScaler` and `class_weight='balanced'`.
       - Provides transparent feature coefficients and linear interpretability.
    2. **Random Forest Classifier**:
       - 100 estimators, max depth 8, min samples leaf 10.
       - Captures non-linear interaction terms between spend contraction and service friction.
    3. **Histogram-based Gradient Boosting (Champion)**:
       - 100 iterations, max depth 6.
       - Delivers peak ROC-AUC (0.9395) and PR-AUC (0.9244) with fast inference.

    ---

    ### 4. Ethical AI & Operational Limitations
    > [!IMPORTANT]
    > **Synthetic Demonstration Notice**: RetentionLab was developed on a deterministic synthetic enterprise dataset. While the statistical distributions and behavioral mechanics closely mirror real-world B2B SaaS dynamics, the model's scores are analytical demonstrations and have not been validated against real customer financial outcomes.

    > [!WARNING]
    > **Non-Causal Association**: Model predictions represent probabilistic associations, not direct causation. A high churn score indicates that a customer's recent behavioral patterns resemble historically churned cohorts; it does not prove that those behaviors caused churn.

    > [!NOTE]
    > **Human-in-the-Loop Governance**: Prioritized recommendations (such as VIP touchpoints or lifecycle nudges) should always be reviewed by trained Customer Success Managers. Automated account termination or unilateral contract cancellation based solely on predicted risk scores is strictly contraindicated.
    """
)
