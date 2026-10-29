#!/usr/bin/env python3
"""
Deterministic Synthetic Data Generator for SignalForge.
Generates realistic customer dimensions, financial transactions, and streaming event batches.
"""
import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any

COUNTRIES = ["USA", "GBR", "DEU", "FRA", "CAN", "JPN", "AUS", "SGP", "IND", "NLD"]
STATUSES = ["COMPLETED", "COMPLETED", "COMPLETED", "PENDING", "FAILED", "CANCELLED"]
PAYMENT_METHODS = ["credit_card", "debit_card", "bank_transfer", "paypal", "apple_pay"]
CURRENCIES = ["USD", "EUR", "GBP"]

def generate_customers(num_customers: int, seed: int = 42) -> List[Dict[str, Any]]:
    random.seed(seed)
    customers = []
    base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Casey", "Riley", "Avery", "Jamie"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    for i in range(1, num_customers + 1):
        cust_id = f"CUST_{i:06d}"
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        days_offset = random.randint(0, 600)
        signup_dt = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%dT%H:%M:%SZ")

        customers.append({
            "customer_id": cust_id,
            "name": f"{fn} {ln}",
            "email": f"{fn.lower()}.{ln.lower()}{i}@example.com",
            "country": random.choice(COUNTRIES),
            "signup_date": signup_dt
        })
    return customers

def generate_transactions(
    num_transactions: int,
    customer_ids: List[str],
    seed: int = 42,
    inject_faults: bool = False
) -> List[Dict[str, Any]]:
    random.seed(seed + 100)
    transactions = []
    now = datetime.now(timezone.utc)

    for i in range(1, num_transactions + 1):
        tx_id = f"TX_{i:08d}"
        cust_id = random.choice(customer_ids)
        amount = round(random.uniform(5.0, 1500.0), 2)
        status = random.choice(STATUSES)
        currency = random.choice(CURRENCIES)
        pay_method = random.choice(PAYMENT_METHODS)

        # Timestamps within the last 14 days
        hours_ago = random.uniform(0.5, 336.0)
        tx_timestamp = (now - timedelta(hours=hours_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Configurable fault injection for testing
        if inject_faults and i % 50 == 0:
            amount = -round(random.uniform(10.0, 100.0), 2)  # Negative amount fault
        elif inject_faults and i % 75 == 0:
            status = "UNKNOWN_STATUS"  # Category whitelist fault
        elif inject_faults and i % 100 == 0:
            cust_id = "CUST_NON_EXISTENT_999999"  # Referential integrity fault

        transactions.append({
            "transaction_id": tx_id,
            "customer_id": cust_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "transaction_timestamp": tx_timestamp,
            "payment_method": pay_method
        })
    return transactions

def main():
    parser = argparse.ArgumentParser(description="SignalForge Deterministic Synthetic Data Generator")
    parser.add_argument("--customers", type=int, default=500, help="Number of customer records (default: 500)")
    parser.add_argument("--transactions", type=int, default=2500, help="Number of transaction records (default: 2500)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--faults", action="store_true", help="Inject controlled fault anomalies into transactions")
    parser.add_argument("--output-dir", type=str, default="./data", help="Target output directory")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.customers} customers (seed={args.seed})...")
    customers = generate_customers(args.customers, seed=args.seed)
    cust_file = out_dir / "customers.csv"
    import pandas as pd
    pd.DataFrame(customers).to_csv(cust_file, index=False)
    print(f"Saved {cust_file} ({len(customers)} rows)")

    cust_ids = [c["customer_id"] for c in customers]
    print(f"Generating {args.transactions} transactions (faults={args.faults})...")
    transactions = generate_transactions(args.transactions, cust_ids, seed=args.seed, inject_faults=args.faults)

    tx_file = out_dir / "transactions.json"
    with open(tx_file, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2)
    print(f"Saved {tx_file} ({len(transactions)} records)")

    # Also save event stream lines format
    stream_file = out_dir / "events_stream.jsonl"
    with open(stream_file, "w", encoding="utf-8") as f:
        for tx in transactions[:500]:
            f.write(json.dumps(tx) + "\n")
    print(f"Saved {stream_file} (500 event stream records)")

    # Save REST API mock dataset
    api_mock_file = out_dir / "api_mock_data.json"
    with open(api_mock_file, "w", encoding="utf-8") as f:
        json.dump({"records": transactions[:200]}, f, indent=2)
    print(f"Saved {api_mock_file} (200 records)")

    print("Synthetic data generation complete.")

if __name__ == "__main__":
    main()
