"""Master end-to-end pipeline orchestrator for RetentionLab."""
import json
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

from retentionlab.config.settings import DEFAULT_CONFIG, PipelineConfig
from retentionlab.ingestion.synthetic_generator import generate_synthetic_transactions
from retentionlab.preprocessing.cleaning import audit_transactions, clean_transactions
from retentionlab.features.target import create_target_labels
from retentionlab.features.builder import build_customer_features
from retentionlab.analytics.sql_runner import init_database, run_all_sql_files
from retentionlab.analytics.statistical import perform_statistical_tests
from retentionlab.modeling.trainer import prepare_modeling_data, build_models
from retentionlab.evaluation.metrics import (
    evaluate_model_performance,
    find_optimal_threshold,
    generate_model_comparison_table,
)
from retentionlab.prioritization.framework import (
    assign_risk_and_prioritization,
    calculate_retention_scenarios,
)
from retentionlab.reporting.excel_generator import build_excel_report


def run_pipeline(config: PipelineConfig = DEFAULT_CONFIG) -> Dict[str, Any]:
    """Execute the complete analytical pipeline from raw data to business reports."""
    print("=" * 70)
    print("RETENTIONLAB: CUSTOMER RETENTION & PREDICTIVE ANALYTICS ENGINE")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Ingestion & Raw Data Check
    # -------------------------------------------------------------
    raw_path = config.raw_transactions_path
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    if raw_path.exists():
        print(f"[Phase 1] Loading existing raw transaction data from {raw_path}...")
        raw_df = pd.read_csv(raw_path)
    else:
        print("[Phase 1] No raw data found. Generating synthetic transactions...")
        raw_df = generate_synthetic_transactions(config)
        raw_df.to_csv(raw_path, index=False)
        # Also create a 5,000-row sample dataset in data/sample/
        config.sample_transactions_path.parent.mkdir(parents=True, exist_ok=True)
        raw_df.head(5000).to_csv(config.sample_transactions_path, index=False)
        print(f"Generated {len(raw_df):,} transactions for {raw_df['customer_id'].nunique():,} customers.")

    # -------------------------------------------------------------
    # 2. Data Audit & Preprocessing / Cleaning
    # -------------------------------------------------------------
    print("[Phase 2] Auditing transaction dataset...")
    audit_results = audit_transactions(raw_df)
    print(f"  Rows: {audit_results['row_count']:,} | Customers: {audit_results['distinct_customer_count']:,}")
    print(f"  Dates: {audit_results['min_transaction_date'][:10]} to {audit_results['max_transaction_date'][:10]}")

    cleaned_df = clean_transactions(raw_df)

    # -------------------------------------------------------------
    # 3. Target Labeling & Feature Engineering (Zero-Leakage)
    # -------------------------------------------------------------
    print(f"[Phase 3] Defining operational target (Cutoff: {config.cutoff_date}, Horizon: {config.outcome_window_days}d)...")
    target_df = create_target_labels(cleaned_df, config)
    print(f"  Eligible customers: {len(target_df):,} | Inactive rate: {target_df[config.target_col].mean():.1%}")

    print("[Phase 4] Computing 44 customer behavioral features strictly before cutoff date...")
    features_df = build_customer_features(cleaned_df, eligible_customers=target_df, config=config)
    print(f"  Extracted {features_df.shape[1] - 1} behavioral features for {len(features_df):,} customers.")

    # Save features and target
    config.features_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_parquet(config.features_path, index=False)

    # -------------------------------------------------------------
    # 4. Statistical Analysis
    # -------------------------------------------------------------
    print("[Phase 5] Performing statistical hypothesis tests...")
    stat_tests = perform_statistical_tests(features_df, target_df)
    for st in stat_tests:
        print(f"  {st['test_name']}: p={st['p_value']:.4e}, effect={st['effect_size']} ({st['effect_size_type']})")

    # -------------------------------------------------------------
    # 5. Modeling & Evaluation
    # -------------------------------------------------------------
    print("[Phase 6] Training and evaluating predictive models...")
    X_train, X_test, y_train, y_test, ids_train, ids_test = prepare_modeling_data(features_df, target_df, config)

    model_dict = build_models(config)
    eval_list = []
    trained_pipelines = {}
    test_predictions_dict = {}

    for name, model in model_dict.items():
        model.fit(X_train, y_train)
        trained_pipelines[name] = model

        # Predict probabilities
        y_prob = model.predict_proba(X_test)[:, 1]
        test_predictions_dict[name] = y_prob

        # Optimize threshold on training data or pick balanced threshold
        prob_train = model.predict_proba(X_train)[:, 1]
        opt_thresh = find_optimal_threshold(y_train, prob_train, metric="f1")

        # Evaluate on test set
        metrics = evaluate_model_performance(name, y_test.values, y_prob, threshold=opt_thresh)
        eval_list.append(metrics)
        print(f"  {name:20s} | Threshold: {opt_thresh:.2f} | ROC-AUC: {metrics['roc_auc']:.4f} | Recall: {metrics['recall']:.1%} | Precision: {metrics['precision']:.1%} | F1: {metrics['f1_score']:.4f}")

    comparison_df = generate_model_comparison_table(eval_list)

    # -------------------------------------------------------------
    # 6. Customer Scoring & Prioritization
    # -------------------------------------------------------------
    print("[Phase 7] Scoring complete eligible customer base with production Logistic Regression...")
    prod_model = trained_pipelines["LogisticRegression"]
    feature_cols = [c for c in features_df.columns if c != "customer_id"]
    all_probs = prod_model.predict_proba(features_df[feature_cols])[:, 1]

    pred_records = []
    for cid, prob in zip(features_df["customer_id"], all_probs):
        pred_records.append({
            "customer_id": cid,
            "model_name": "LogisticRegression",
            "model_version": "v1.0.0",
            "prediction_date": config.cutoff_date,
            "inactivity_probability": float(round(prob, 4)),
            "predicted_label": int(prob >= 0.50),
            "threshold_used": 0.50,
            "risk_score": float(round(prob, 4))
        })
    predictions_df = pd.DataFrame(pred_records)
    predictions_df.to_parquet(config.predictions_path, index=False)

    print("[Phase 8] Assigning customer risk tiers and prioritization actions...")
    prioritization_df = assign_risk_and_prioritization(features_df, predictions_df, config)
    prioritization_df.to_csv(config.prioritization_path, index=False)

    # Scenarios
    scenarios_df = calculate_retention_scenarios(prioritization_df)

    # -------------------------------------------------------------
    # 7. SQL Database Initialization & Analytics Verification
    # -------------------------------------------------------------
    print("[Phase 9] Initializing SQLite database and verifying 20 SQL analytical queries...")
    db_conn = init_database(
        raw_df=raw_df,
        cleaned_df=cleaned_df,
        features_df=features_df,
        target_df=target_df,
        predictions_df=predictions_df,
        prioritization_df=prioritization_df,
        config=config
    )
    sql_exec_summary = run_all_sql_files(db_conn)
    print(f"  Executed SQL files: {len(sql_exec_summary)} successfully.")

    # -------------------------------------------------------------
    # 8. Excel & Power BI Artifact Generation
    # -------------------------------------------------------------
    print("[Phase 10] Generating 7-sheet executive Excel report...")
    excel_path = build_excel_report(
        prioritization_df=prioritization_df,
        comparison_df=comparison_df,
        scenarios_df=scenarios_df,
        audit_data=audit_results,
        statistical_tests=stat_tests,
        output_path=config.excel_report_path,
        config=config
    )
    print(f"  Excel report created at: {excel_path}")

    # Export Power BI data tables as CSV
    pbi_dir = config.excel_report_path.parents[1] / "powerbi" / "data"
    pbi_dir.mkdir(parents=True, exist_ok=True)
    prioritization_df.to_csv(pbi_dir / "pbi_customer_prioritization.csv", index=False)
    comparison_df.to_csv(pbi_dir / "pbi_model_comparison.csv", index=False)
    scenarios_df.to_csv(pbi_dir / "pbi_retention_scenarios.csv", index=False)

    # Save summary report JSON
    summary_report = {
        "execution_timestamp": str(pd.Timestamp.now()),
        "data_audit": audit_results,
        "model_comparison": comparison_df.to_dict(orient="records"),
        "statistical_tests": stat_tests,
        "scenarios": scenarios_df.to_dict(orient="records"),
        "sql_execution": sql_exec_summary
    }

    report_json_path = config.excel_report_path.parents[1] / "reports" / "business_summary" / "pipeline_summary.json"
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    print("=" * 70)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("=" * 70)

    return {
        "audit": audit_results,
        "comparison": comparison_df,
        "statistical_tests": stat_tests,
        "prioritization": prioritization_df,
        "scenarios": scenarios_df,
        "excel_path": str(excel_path)
    }


if __name__ == "__main__":
    run_pipeline()
