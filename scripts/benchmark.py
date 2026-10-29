#!/usr/bin/env python3
"""
SignalForge Performance & Reliability Benchmark Runner.
Measures records/sec, stage latencies, memory footprint, duplicate prevention, and failure recovery.
"""
import argparse
import json
import time
import sys
import tracemalloc
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from signalforge.config import settings
from signalforge.db.connection import get_db_session, init_db
from signalforge.db.models import Pipeline, FactTransaction, DimCustomer
from signalforge.engine.extractors import JSONExtractor
from signalforge.engine.pipeline import PipelineEngine
from signalforge.quality.rules import QualityRule, RuleSeverity, RuleType
from signalforge.failure_lab.scenarios import FailureLab
from scripts.generate_synthetic_data import generate_customers, generate_transactions

def run_benchmark(batch_size: int = 5000) -> dict:
    print("=" * 70)
    print(f"SIGNALFORGE BENCHMARK: BATCH SIZE = {batch_size} RECORDS")
    print("=" * 70)

    init_db()
    bench_dir = settings.data_dir / "benchmark"
    bench_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate test data
    print("\n[1/5] Generating benchmark datasets...")
    customers = generate_customers(1000, seed=123)
    cust_ids = [c["customer_id"] for c in customers]
    transactions = generate_transactions(batch_size, cust_ids, seed=456, inject_faults=False)

    # Seed customers into DB so transactions have valid FKs
    with get_db_session() as db:
        for c in customers:
            if not db.query(DimCustomer).filter(DimCustomer.customer_id == c["customer_id"]).first():
                db.add(DimCustomer(
                    customer_id=c["customer_id"],
                    name=c["name"],
                    email=c["email"],
                    country=c["country"],
                    signup_date=pd.to_datetime(c["signup_date"]).to_pydatetime()
                ))
        db.commit()

    tx_file = bench_dir / "bench_transactions.json"
    with open(tx_file, "w", encoding="utf-8") as f:
        json.dump(transactions, f)

    # 2. Benchmark Pipeline Execution
    print("[2/5] Benchmarking Pipeline Throughput & Latency...")
    tracemalloc.start()
    t_start = time.perf_counter()

    with get_db_session() as db:
        pipeline = db.query(Pipeline).filter(Pipeline.name == "transaction_facts_pipeline").first()
        extractor = JSONExtractor(str(tx_file))
        rules = [
            QualityRule("not_null_tx_id", RuleType.NOT_NULL, "fact_transactions", {"column": "transaction_id"}, RuleSeverity.BATCH_FAIL),
            QualityRule("unique_tx_id", RuleType.UNIQUE, "fact_transactions", {"column": "transaction_id"}, RuleSeverity.RECORD_REJECT),
            QualityRule("non_negative_amount", RuleType.NON_NEGATIVE, "fact_transactions", {"column": "amount"}, RuleSeverity.RECORD_REJECT),
            QualityRule("valid_status", RuleType.CATEGORY_WHITELIST, "fact_transactions", {"column": "status", "allowed_values": ["COMPLETED", "PENDING", "FAILED", "CANCELLED"]}, RuleSeverity.RECORD_REJECT),
            QualityRule("referential_cust", RuleType.REFERENTIAL_INTEGRITY, "fact_transactions", {"column": "customer_id", "reference_dataset": "dim_customers", "reference_column": "customer_id"}, RuleSeverity.RECORD_REJECT),
        ]
        engine = PipelineEngine(db, pipeline, extractor, quality_rules=rules, dataset_name="fact_transactions", identifier_column="transaction_id")
        run = engine.run(trigger_type="MANUAL")
        records_loaded = run.records_loaded

    t_end = time.perf_counter()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    duration = t_end - t_start
    throughput = records_loaded / duration if duration > 0 else 0

    print(f"  -> Execution Duration : {duration:.2f} s")
    print(f"  -> Records Loaded     : {records_loaded} records")
    print(f"  -> Throughput         : {throughput:.1f} records/second")
    print(f"  -> Peak Memory Usage  : {peak_mem / 1024 / 1024:.2f} MB")

    # 3. Benchmark Idempotency & Duplicate Prevention
    print("\n[3/5] Testing Idempotent Re-execution (Duplicate Prevention)...")
    with get_db_session() as db:
        initial_count = db.query(FactTransaction).count()
        pipe = db.query(Pipeline).filter(Pipeline.name == "transaction_facts_pipeline").first()

        # Re-run same batch
        engine_rerun = PipelineEngine(db, pipe, extractor, quality_rules=rules, dataset_name="fact_transactions", identifier_column="transaction_id")
        run_rerun = engine_rerun.run(trigger_type="MANUAL")
        rerun_loaded = run_rerun.records_loaded

        post_count = db.query(FactTransaction).count()
        duplicate_records_created = post_count - initial_count

    print(f"  -> Initial Rows in DB : {initial_count}")
    print(f"  -> Re-run Loaded Count: {rerun_loaded}")
    print(f"  -> Final Rows in DB   : {post_count}")
    print(f"  -> Duplicates Created : {duplicate_records_created} (Idempotency {'PASSED' if duplicate_records_created == 0 else 'FAILED'})")

    # 4. Benchmark Failure Lab Recovery Scenarios
    print("\n[4/5] Testing Failure Lab Scenarios...")
    recovery_results = []
    with get_db_session() as db:
        lab = FailureLab(db)
        scenarios = lab.list_scenarios()
        for sc in scenarios:
            res = lab.run_scenario(sc["id"])
            success = (res.get("status") in ("FAILED", "COMPLETED"))
            recovery_results.append({
                "id": sc["id"],
                "name": sc["name"],
                "status": res.get("status"),
                "category": res.get("error_category") or "NONE",
                "handled": success
            })
            print(f"  [{'PASS' if success else 'FAIL'}] Scenario: {sc['name']} -> {res.get('status')} ({res.get('error_category') or 'NONE'})")

    # 5. Compile and Save Report
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "batch_size": batch_size,
        "metrics": {
            "execution_duration_sec": round(duration, 3),
            "records_loaded": records_loaded,
            "throughput_records_per_sec": round(throughput, 1),
            "peak_memory_mb": round(peak_mem / 1024 / 1024, 2),
            "duplicate_records_created_on_rerun": duplicate_records_created,
            "idempotency_verified": duplicate_records_created == 0,
        },
        "scenarios_tested": len(recovery_results),
        "scenarios_handled": sum(1 for r in recovery_results if r["handled"]),
        "scenario_details": recovery_results
    }

    report_path = settings.reports_dir / "benchmark_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n[5/5] Benchmark report saved to: {report_path}")
    print("=" * 70)
    print("BENCHMARK COMPLETED SUCCESSFULLY")
    print("=" * 70)
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SignalForge Benchmark Suite")
    parser.add_argument("--size", type=int, default=3000, help="Transaction batch size (default: 3000)")
    args = parser.parse_args()
    run_benchmark(batch_size=args.size)
