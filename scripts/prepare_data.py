"""Data preparation script: Ingestion, Audit, and Cleaning."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from retentionlab.config.settings import DEFAULT_CONFIG
from retentionlab.ingestion.synthetic_generator import generate_synthetic_transactions
from retentionlab.preprocessing.cleaning import audit_transactions, clean_transactions
import pandas as pd


def main():
    print("Executing scripts/prepare_data.py...")
    config = DEFAULT_CONFIG
    raw_path = config.raw_transactions_path

    if not raw_path.exists():
        print(f"Generating synthetic transaction dataset ({config.n_customers} customers)...")
        df_raw = generate_synthetic_transactions(config)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        df_raw.to_csv(raw_path, index=False)
        # Create sample
        config.sample_transactions_path.parent.mkdir(parents=True, exist_ok=True)
        df_raw.head(5000).to_csv(config.sample_transactions_path, index=False)
    else:
        print(f"Loading raw data from {raw_path}...")
        df_raw = pd.read_csv(raw_path)

    audit = audit_transactions(df_raw)
    print(f"Audit completed: {audit['row_count']} rows, {audit['distinct_customer_count']} customers.")

    df_cleaned = clean_transactions(df_raw)
    print(f"Cleaned dataset contains {len(df_cleaned)} valid transactions.")
    print("Data preparation complete.")


if __name__ == "__main__":
    main()
