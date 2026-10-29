"""
Script to generate deterministic synthetic dataset for RetentionLab.
Validates constraints (>97k transactions) and loads records into database and data/raw.
"""

import sys
import time
from pathlib import Path
from retentionlab.config.settings import settings
from retentionlab.data_generation.generator import SyntheticDataGenerator
from retentionlab.database.connection import init_db, save_dataframe_to_table, get_engine


def run_data_generation() -> None:
    print(f"=== RetentionLab Data Generation: Starting with seed {settings.data_gen.random_seed} ===")
    t0 = time.time()

    generator = SyntheticDataGenerator(
        num_customers=settings.data_gen.num_customers,
        random_seed=settings.data_gen.random_seed,
        start_date=settings.data_gen.start_date,
        end_date=settings.data_gen.end_date,
        snapshot_date=settings.data_gen.snapshot_date,
        target_transaction_count=settings.data_gen.target_transaction_count,
    )

    data = generator.generate_all()

    # Save to data/raw
    raw_dir = settings.root_dir / settings.data_gen.__dict__.get("raw_data_dir", "data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("\n--- Saving Raw CSV Datasets ---")
    for name, df in data.items():
        csv_path = raw_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False)
        print(f"  * {name:<22}: {len(df):>8,d} records -> {csv_path.name}")

    # Initialize DB & load
    print("\n--- Initializing Relational Database ---")
    engine = get_engine()
    init_db(engine)

    print("--- Ingesting Data into SQLite Database ---")
    for name, df in data.items():
        save_dataframe_to_table(df, name, if_exists="replace", engine=engine)
        print(f"  * Loaded {len(df):>8,d} rows into table '{name}'")

    print("--- Building Analytical Indexes ---")
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_txn_cust_date ON transactions(customer_id, transaction_date);'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(transaction_date);'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_txn_cust ON transactions(customer_id);'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_act_cust ON customer_activity(customer_id);'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_act_date ON customer_activity(activity_date);'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_sup_cust ON support_tickets(customer_id);'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_cam_cust ON campaign_interactions(customer_id);'))
        conn.execute(text('CREATE INDEX IF NOT EXISTS idx_snap_cust ON customer_snapshots(customer_id);'))
        conn.commit()

    elapsed = time.time() - t0
    total_txns = len(data["transactions"])
    print(f"\n[SUCCESS] Generated {total_txns:,d} transactions across {len(data['customers']):,d} customers in {elapsed:.2f}s.")
    print("Database ready at data/retentionlab.db\n")


if __name__ == "__main__":
    run_data_generation()
