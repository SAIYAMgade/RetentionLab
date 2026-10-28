"""Feature engineering and target definition script."""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retentionlab.config.settings import DEFAULT_CONFIG
from retentionlab.preprocessing.cleaning import clean_transactions
from retentionlab.features.target import create_target_labels
from retentionlab.features.builder import build_customer_features


def main():
    print("Executing scripts/build_features.py...")
    config = DEFAULT_CONFIG
    df_raw = pd.read_csv(config.raw_transactions_path)
    df_clean = clean_transactions(df_raw)

    print(f"Assigning target labels with cutoff={config.cutoff_date}...")
    target_df = create_target_labels(df_clean, config)
    print(f"Target assigned: {len(target_df)} customers, {target_df[config.target_col].mean():.1%} inactive.")

    print("Building 44 behavioral features with zero future leakage...")
    features_df = build_customer_features(df_clean, eligible_customers=target_df, config=config)

    config.features_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_parquet(config.features_path, index=False)
    print(f"Saved {features_df.shape[1] - 1} features to {config.features_path}.")


if __name__ == "__main__":
    main()
