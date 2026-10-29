"""
RetentionLab Customer Scoring & Prioritization CLI Script.
Scores eligible customers using the trained model artifact and exports worklists.
"""

import sys
import time
from pathlib import Path
import pandas as pd
from retentionlab.config.settings import settings
from retentionlab.scoring.scorer import CustomerScorer


def run_scoring() -> None:
    print("=== RetentionLab: Scoring & Retention Prioritization Pipeline ===")
    t0 = time.time()

    features_path = settings.root_dir / "data" / "processed" / "customer_features_44.csv"
    if not features_path.exists():
        print(f"Error: Features file not found at {features_path}. Run training or feature builder first.")
        sys.exit(1)

    print(f"Loading customer snapshot features from {features_path.name}...")
    features_df = pd.read_csv(features_path)

    scorer = CustomerScorer()
    print("Generating churn probabilities and attaching explainable risk signals...")
    scored_df = scorer.score_customers(features_df)

    print("\n--- Scoring & Risk Distribution Summary ---")
    band_counts = scored_df["risk_band"].value_counts()
    for band, count in band_counts.items():
        print(f"  * {band:<16}: {count:>5,d} customers ({count/len(scored_df):.1%})")

    top_cohort_count = int(scored_df["is_top_15_percent"].sum())
    total_exposure = scored_df.loc[scored_df["is_top_15_percent"] == 1, "risk_weighted_exposure"].sum()
    print(f"\nTop 15% Operational Cohort: {top_cohort_count:,d} customers")
    print(f"Total Risk-Weighted Exposure in Top Cohort: ${total_exposure:,.2f}")

    print("\nPersisting scores to CSV and database table 'retention_scores'...")
    scorer.persist_scores(scored_df)

    print(f"[SUCCESS] Scored {len(scored_df):,d} customers in {time.time() - t0:.2f}s.\n")


if __name__ == "__main__":
    run_scoring()
