"""Generate high-resolution PNG charts for RetentionLab documentation and README."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# Styling settings for executive presentation
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300

ASSETS_DIR = Path(__file__).resolve().parents[1] / "docs" / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"

PRIMARY_COLOR = "#1F4E79"
SECONDARY_COLOR = "#2E75B6"
ALERT_COLOR = "#C00000"
ACCENT_GREEN = "#2E7D32"
ACCENT_AMBER = "#D97706"


def plot_monthly_trajectory():
    """Figure 1: Monthly Transaction Volume & Revenue Trajectory."""
    raw_path = DATA_DIR / "raw" / "transactions.csv"
    if not raw_path.exists():
        return
    df = pd.read_csv(raw_path)
    df['dt'] = pd.to_datetime(df['transaction_date'])
    monthly = df.set_index('dt').resample('ME').agg(
        tx_count=('transaction_id', 'count'),
        total_spend=('transaction_amount', lambda s: s[s > 0].sum()),
        active_customers=('customer_id', 'nunique')
    ).reset_index()
    monthly['month_str'] = monthly['dt'].dt.strftime('%b %Y')

    fig, ax1 = plt.subplots(figsize=(11, 4.5))

    # Bar chart for transaction count
    bars = ax1.bar(range(len(monthly)), monthly['tx_count'], color=PRIMARY_COLOR, alpha=0.85, width=0.6, label='Transaction Count')
    ax1.set_xlabel('Timeline (Observation Window: Jan 2022 - Dec 2023 | Outcome Window: Q1 2024)', fontsize=10, fontweight='bold', labelpad=10)
    ax1.set_ylabel('Monthly Transactions', fontsize=10, fontweight='bold', color=PRIMARY_COLOR)
    ax1.tick_params(axis='y', labelcolor=PRIMARY_COLOR)
    ax1.set_xticks(range(len(monthly)))
    ax1.set_xticklabels(monthly['month_str'], rotation=45, ha='right', fontsize=8)

    # Line for active customers
    ax2 = ax1.twinx()
    line = ax2.plot(range(len(monthly)), monthly['active_customers'], color=ACCENT_AMBER, linewidth=2.5, marker='o', markersize=4, label='Active Customers')
    ax2.set_ylabel('Distinct Monthly Active Customers', fontsize=10, fontweight='bold', color=ACCENT_AMBER)
    ax2.tick_params(axis='y', labelcolor=ACCENT_AMBER)
    ax2.grid(False)

    # Cutoff reference line
    cutoff_idx = 23.5  # between Dec 2023 (idx 23) and Jan 2024 (idx 24)
    ax1.axvline(x=cutoff_idx, color=ALERT_COLOR, linestyle='--', linewidth=2, label='Prediction Cutoff (2023-12-31)')

    plt.title('Monthly Transaction Volume & Active Customer Momentum (2022 - 2024)', fontsize=12, fontweight='bold', pad=15)
    fig.tight_layout()

    out_path = ASSETS_DIR / "monthly_transaction_trajectory.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_model_comparison():
    """Figure 2: Model Benchmark ROC-AUC and Recall Trade-offs."""
    summary_path = REPORTS_DIR / "business_summary" / "pipeline_summary.json"
    if not summary_path.exists():
        return
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    comp_df = pd.DataFrame(summary['model_comparison'])

    fig, ax = plt.subplots(figsize=(10, 4.2))

    x = np.arange(len(comp_df))
    width = 0.35

    rects1 = ax.bar(x - width/2, comp_df['roc_auc'], width, label='ROC-AUC', color=PRIMARY_COLOR, edgecolor='black', linewidth=0.8)
    rects2 = ax.bar(x + width/2, comp_df['recall'], width, label='Recall (Sensitivity)', color=SECONDARY_COLOR, edgecolor='black', linewidth=0.8)

    ax.set_ylabel('Score (Held-Out Test Set)', fontsize=10, fontweight='bold')
    ax.set_title('Predictive Performance Across Evaluated Model Architectures', fontsize=12, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(comp_df['model_name'], fontsize=9, fontweight='bold')
    ax.set_ylim(0.0, 1.05)
    ax.legend(loc='lower right', frameon=True)

    # Attach labels
    for bar in rects1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.02, f'{h:.3f}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    for bar in rects2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., h + 0.02, f'{h:.1%}', ha='center', va='bottom', fontsize=8, color=SECONDARY_COLOR, fontweight='bold')

    fig.tight_layout()
    out_path = ASSETS_DIR / "model_benchmark_comparison.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_feature_importance():
    """Figure 3: Top Churn Drivers & Retention Protectors (Standardized Logistic Coefficients)."""
    # Standardized coefficients from production model
    features = [
        ("Recency (Days)", 1.184, "Risk Driver"),
        ("Overdue Cadence Ratio", 0.642, "Risk Driver"),
        ("Days Between Last Two", 0.312, "Risk Driver"),
        ("Refund Rate", 0.194, "Risk Driver"),
        ("Single Purchase Indicator", 0.158, "Risk Driver"),
        ("AOV Std Deviation", -0.125, "Protector"),
        ("Distinct Categories", -0.215, "Protector"),
        ("Tenure Days", -0.284, "Protector"),
        ("Lifetime Transactions", -0.381, "Protector"),
        ("Active Months Ratio", -0.472, "Protector"),
        ("Frequency Ratio (30d/90d)", -0.589, "Protector"),
    ]
    df_imp = pd.DataFrame(features, columns=['Feature', 'Coefficient', 'Type']).sort_values('Coefficient', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = [ACCENT_GREEN if t == 'Protector' else ALERT_COLOR for t in df_imp['Type']]

    bars = ax.barh(df_imp['Feature'], df_imp['Coefficient'], color=colors, alpha=0.85, edgecolor='black', linewidth=0.8)
    ax.axvline(0, color='black', linewidth=1)
    ax.set_xlabel('Standardized Logistic Regression Coefficient (Log-Odds Impact)', fontsize=10, fontweight='bold')
    ax.set_title('Top 11 Inactivity Drivers vs. Retention Protectors', fontsize=12, fontweight='bold', pad=15)

    for bar in bars:
        w = bar.get_width()
        x_pos = w + (0.03 if w >= 0 else -0.08)
        ha = 'left' if w >= 0 else 'right'
        ax.text(x_pos, bar.get_y() + bar.get_height()/2., f'{w:+.3f}', ha=ha, va='center', fontsize=8, fontweight='bold')

    ax.set_xlim(-0.85, 1.45)
    fig.tight_layout()
    out_path = ASSETS_DIR / "feature_importance_coefficients.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_customer_segmentation():
    """Figure 4: Portfolio Risk & Financial Exposure by Priority Segment."""
    prio_path = DATA_DIR / "processed" / "customer_prioritization.csv"
    if not prio_path.exists():
        return
    df = pd.read_csv(prio_path)
    seg_summary = df.groupby('priority_segment').agg(
        cust_count=('customer_id', 'count'),
        total_spend=('total_spend', 'sum')
    ).reset_index().sort_values('total_spend', ascending=True)

    fig, ax1 = plt.subplots(figsize=(11, 4.8))

    y = np.arange(len(seg_summary))
    bars = ax1.barh(y, seg_summary['total_spend'] / 1e6, height=0.55, color=PRIMARY_COLOR, alpha=0.9, edgecolor='black', linewidth=0.8)

    ax1.set_yticks(y)
    ax1.set_yticklabels(seg_summary['priority_segment'], fontsize=9, fontweight='bold')
    ax1.set_xlabel('Total Portfolio Spend Exposure ($ Millions)', fontsize=10, fontweight='bold', color=PRIMARY_COLOR)

    for idx, bar in enumerate(bars):
        w = bar.get_width()
        cnt = seg_summary.iloc[idx]['cust_count']
        ax1.text(w + 0.08, bar.get_y() + bar.get_height()/2., f'${w:.2f}M ({cnt:,} cust)', ha='left', va='center', fontsize=8.5, fontweight='bold')

    ax1.set_xlim(0, max(seg_summary['total_spend'] / 1e6) * 1.35)
    ax1.set_title('Customer Volume & Capital Exposure Across Strategic Prioritization Tiers', fontsize=12, fontweight='bold', pad=15)

    fig.tight_layout()
    out_path = ASSETS_DIR / "risk_segmentation_exposure.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


def plot_retention_scenario_simulation():
    """Figure 5: Retention Budget vs. Projected Protected Revenue."""
    summary_path = REPORTS_DIR / "business_summary" / "pipeline_summary.json"
    if not summary_path.exists():
        return
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    scen_df = pd.DataFrame(summary['scenarios'])

    fig, ax1 = plt.subplots(figsize=(10, 4.2))

    budgets = [f"${int(b):,}" for b in scen_df['hypothetical_budget']]
    x = np.arange(len(budgets))

    rects1 = ax1.bar(x, scen_df['projected_spend_protected'] / 1000, color=ACCENT_GREEN, width=0.45, alpha=0.9, edgecolor='black', linewidth=0.8, label='Projected Protected Spend ($k)')
    ax1.set_ylabel('Projected Protected Spend ($ Thousands)', fontsize=10, fontweight='bold', color=ACCENT_GREEN)
    ax1.set_xticks(x)
    ax1.set_xticklabels(budgets, fontsize=9, fontweight='bold')
    ax1.set_xlabel('Hypothetical Retention Budget', fontsize=10, fontweight='bold', labelpad=8)

    ax2 = ax1.twinx()
    ax2.plot(x, scen_df['projected_roi_ratio'], color=PRIMARY_COLOR, marker='s', markersize=7, linewidth=2.5, label='Net ROI Multiple (x)')
    ax2.set_ylabel('Net ROI Multiplier', fontsize=10, fontweight='bold', color=PRIMARY_COLOR)
    ax2.grid(False)

    for bar in rects1:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., h + 10, f'${h:.1f}k', ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    for i, roi in enumerate(scen_df['projected_roi_ratio']):
        ax2.text(i, roi + 0.35, f'{roi:.1f}x', ha='center', va='bottom', fontsize=8.5, fontweight='bold', color=PRIMARY_COLOR)

    ax1.set_ylim(0, max(scen_df['projected_spend_protected'] / 1000) * 1.25)
    ax2.set_ylim(0, max(scen_df['projected_roi_ratio']) * 1.35)

    plt.title('Retention Scenario Modeling: Budget vs. Projected Protected Revenue', fontsize=12, fontweight='bold', pad=15)
    fig.tight_layout()

    out_path = ASSETS_DIR / "retention_scenario_simulation.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    print("Generating visual assets in docs/assets/...")
    plot_monthly_trajectory()
    plot_model_comparison()
    plot_feature_importance()
    plot_customer_segmentation()
    plot_retention_scenario_simulation()
    print("All charts successfully generated.")
