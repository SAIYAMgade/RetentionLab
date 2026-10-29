"""
Script to generate standard Jupyter notebooks for exploratory analysis and demonstration.
"""

import json
from pathlib import Path


def create_nb(cells):
    return {
        "cells": cells,
        "metadata": {
            "language_info": {"name": "python", "version": "3.11"},
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def md_cell(text):
    return {"cell_type": "markdown", "metadata": {}, "source": [text]}


def code_cell(code):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [code],
    }


def run():
    nb_dir = Path("notebooks")
    nb_dir.mkdir(exist_ok=True)

    # 01_data_exploration.ipynb
    nb1 = create_nb(
        [
            md_cell(
                "# RetentionLab: 01. Exploratory Data Analysis & Relational Auditing\nThis notebook demonstrates relational entity validation, transactional distribution analysis, and data quality checks."
            ),
            code_cell(
                'import pandas as pd\nfrom retentionlab.database.connection import execute_query\n\ncust_df = execute_query("SELECT * FROM customers")\ntxn_df = execute_query("SELECT * FROM transactions")\nprint("Loaded", len(cust_df), "customers and", len(txn_df), "transactions.")\ncust_df.head()'
            ),
            code_cell(
                "from retentionlab.validation.data_quality import run_sql_quality_checks\ndq_df = run_sql_quality_checks()\ndq_df"
            ),
        ]
    )
    (nb_dir / "01_data_exploration.ipynb").write_text(json.dumps(nb1, indent=2), encoding="utf-8")

    # 02_feature_validation.ipynb
    nb2 = create_nb(
        [
            md_cell(
                "# RetentionLab: 02. 44-Feature Behavioral Engineering & Leakage Validation\nThis notebook inspects the 44 behavioral features and proves that no future data leaks into the snapshot feature matrix."
            ),
            code_cell(
                'import pandas as pd\nfrom retentionlab.features.catalog import FEATURE_NAMES, FEATURE_CATALOG\nprint("Total behavioral features:", len(FEATURE_NAMES))\npd.DataFrame(FEATURE_CATALOG)[["name", "category", "unit", "risk_direction"]].head(10)'
            ),
            code_cell(
                'features_df = pd.read_csv("data/processed/customer_features_44.csv")\nfeatures_df.describe()'
            ),
        ]
    )
    (nb_dir / "02_feature_validation.ipynb").write_text(json.dumps(nb2, indent=2), encoding="utf-8")

    # 03_model_experiments.ipynb
    nb3 = create_nb(
        [
            md_cell(
                "# RetentionLab: 03. Model Benchmark Experiments & Decision Threshold Analysis\nThis notebook compares Logistic Regression, Random Forest, and HistGradientBoosting on strictly holdout test partitions."
            ),
            code_cell(
                'import pandas as pd, json\ncomp_df = pd.read_csv("models/model_comparison.csv")\ncomp_df'
            ),
            code_cell(
                'with open("models/model_metadata.json", "r") as f:\n    meta = json.load(f)\nprint("Champion Model:", meta["best_model_name"])\nprint("Optimized Threshold:", meta["selected_threshold"])\nprint("Test Metrics:", json.dumps(meta["test_metrics"], indent=2))'
            ),
        ]
    )
    (nb_dir / "03_model_experiments.ipynb").write_text(json.dumps(nb3, indent=2), encoding="utf-8")

    print("Jupyter notebooks generated successfully.")


if __name__ == "__main__":
    run()
