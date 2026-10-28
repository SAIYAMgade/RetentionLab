"""Generator for RetentionLab Jupyter Notebooks."""
import json
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).resolve().parents[1] / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)


def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.14.7"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }


def md_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    }


def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.split("\n")]
    }


# Notebook 1: Data Audit
nb1_cells = [
    md_cell("# RetentionLab: 01. Comprehensive Dataset Audit\n\nThis notebook executes the 12-point transaction audit defined in Section 4.2."),
    code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path.cwd().parent / "src"))

from retentionlab.config.settings import DEFAULT_CONFIG
from retentionlab.preprocessing.cleaning import audit_transactions

raw_path = DEFAULT_CONFIG.raw_transactions_path
print(f"Loading transaction dataset from {raw_path}...")
df_raw = pd.read_csv(raw_path)
print(f"Loaded {len(df_raw):,} records.")"""),
    code_cell("""# Run complete 12-point audit
audit_results = audit_transactions(df_raw)

print("=" * 60)
print("RETENTIONLAB: 12-POINT TRANSACTION AUDIT SUMMARY")
print("=" * 60)
for k, v in audit_results.items():
    if isinstance(v, dict):
        print(f"\\n--- {k.replace('_', ' ').upper()} ---")
        for sub_k, sub_v in v.items():
            print(f"  {sub_k}: {sub_v}")
    elif isinstance(v, list):
        print(f"\\n--- {k.replace('_', ' ').upper()} ---")
        for item in v:
            print(f"  • {item}")
    else:
        print(f"{k:45s}: {v}")"""),
    code_cell("""# Visualizing transaction volume over time
import matplotlib.pyplot as plt

df_raw['date'] = pd.to_datetime(df_raw['transaction_date'])
monthly_tx = df_raw.set_index('date').resample('M')['transaction_id'].count()

plt.figure(figsize=(10, 4))
monthly_tx.plot(kind='bar', color='#1F4E79', edgecolor='black')
plt.title('Monthly Transaction Volume (2022 - 2024)', fontsize=12, fontweight='bold')
plt.xlabel('Month')
plt.ylabel('Transactions')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()""")
]

# Notebook 2: Exploratory Data Analysis
nb2_cells = [
    md_cell("# RetentionLab: 02. Exploratory Data Analysis (EDA)\n\nInvestigating customer purchase cycles, value distributions, and early churn indicators."),
    code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path.cwd().parent / "src"))
from retentionlab.config.settings import DEFAULT_CONFIG

features_path = DEFAULT_CONFIG.features_path
df_feat = pd.read_parquet(features_path)
print(f"Loaded {len(df_feat):,} customer behavioral profiles.")"""),
    code_cell("""# Distribution of Recency Days & Lifetime Spend
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

sns.histplot(df_feat['recency_days'], bins=40, kde=True, ax=axes[0], color='#1F4E79')
axes[0].set_title('Customer Recency Distribution (Days since last purchase)')
axes[0].set_xlabel('Recency (Days)')

sns.histplot(np.log10(df_feat['total_spend']), bins=40, kde=True, ax=axes[1], color='#2E75B6')
axes[1].set_title('Log10 Customer Total Spend Distribution')
axes[1].set_xlabel('Log10 Spend ($)')

plt.tight_layout()
plt.show()"""),
    code_cell("""# Channel and Category Breakdown
prio_df = pd.read_csv(DEFAULT_CONFIG.prioritization_path)

plt.figure(figsize=(10, 4))
sns.countplot(data=prio_df, x='priority_segment', palette='crest', order=prio_df['priority_segment'].value_counts().index)
plt.title('Customer Distribution Across Retention Priority Tiers')
plt.xticks(rotation=35, ha='right')
plt.tight_layout()
plt.show()""")
]

# Notebook 3: Feature Analysis & Statistical Testing
nb3_cells = [
    md_cell("# RetentionLab: 03. Feature Analysis & Statistical Hypotheses\n\nAssessing behavioral feature separation between active and churning customers."),
    code_cell("""import sys
from pathlib import Path
import pandas as pd
import numpy as np
import sqlite3

sys.path.insert(0, str(Path.cwd().parent / "src"))
from retentionlab.config.settings import DEFAULT_CONFIG
from retentionlab.analytics.statistical import perform_statistical_tests

feat_df = pd.read_parquet(DEFAULT_CONFIG.features_path)
conn = sqlite3.connect(str(DEFAULT_CONFIG.processed_db_path))
target_df = pd.read_sql_query("SELECT customer_id, is_inactive FROM target_labels", conn)

stat_results = perform_statistical_tests(feat_df, target_df)
df_stat = pd.DataFrame(stat_results)
df_stat[['test_name', 'p_value', 'effect_size', 'effect_size_type', 'statistically_significant']]"""),
    code_cell("""# Feature correlations with inactivity
merged = pd.merge(feat_df, target_df, on='customer_id')
corrs = merged.drop(columns=['customer_id']).corr()['is_inactive'].sort_values()

print("Top 5 Inactivity Protectors (Negative Correlation):")
print(corrs.head(5))

print("\\nTop 5 Inactivity Indicators (Positive Correlation):")
print(corrs.tail(6))""")
]

# Notebook 4: Model Evaluation
nb4_cells = [
    md_cell("# RetentionLab: 04. Model Evaluation & Prioritization Matrix\n\nComparing Baseline, Logistic Regression, KNN, Random Forest, and Gradient Boosting."),
    code_cell("""import sys
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path.cwd().parent / "src"))
from retentionlab.config.settings import DEFAULT_CONFIG

summary_json_path = DEFAULT_CONFIG.excel_report_path.parents[1] / "reports" / "business_summary" / "pipeline_summary.json"
with open(summary_json_path, 'r') as f:
    summary = json.load(f)

comp_df = pd.DataFrame(summary['model_comparison'])
comp_df"""),
    code_cell("""# Visualizing Model ROC-AUC & Recall Trade-offs
plt.figure(figsize=(9, 4))
bars = plt.bar(comp_df['model_name'], comp_df['roc_auc'], color='#1F4E79', edgecolor='black', width=0.5)
plt.title('Model ROC-AUC Comparison on Held-Out Test Set', fontweight='bold')
plt.ylabel('ROC-AUC Score')
plt.ylim(0.5, 0.9)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.01, f"{yval:.4f}", ha='center', va='bottom', fontweight='bold')
plt.tight_layout()
plt.show()"""),
    code_cell("""# Retention Scenario Analysis
scen_df = pd.DataFrame(summary['scenarios'])
scen_df[['hypothetical_budget', 'max_customers_contacted', 'projected_retained_customers', 'projected_spend_protected', 'projected_roi_ratio']]""")
]

# Write all 4 notebooks
for fname, cells in [
    ("01_data_audit.ipynb", nb1_cells),
    ("02_exploratory_analysis.ipynb", nb2_cells),
    ("03_feature_analysis.ipynb", nb3_cells),
    ("04_model_evaluation.ipynb", nb4_cells),
]:
    nb_path = NOTEBOOKS_DIR / fname
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(make_notebook(cells), f, indent=2)
    print(f"Generated notebook: {nb_path}")
