"""
RetentionLab End-to-End Master Pipeline Orchestrator.
Executes data generation, ingestion, quality checks, 44-feature engineering,
leakage-free target labeling, model benchmarking, scoring, prioritization, and BI exports.
"""

import time
from typing import Dict, Any
import pandas as pd
from retentionlab.config.settings import settings
from retentionlab.data_generation.generator import SyntheticDataGenerator
from retentionlab.database.connection import get_engine, init_db, save_dataframe_to_table, execute_query
from retentionlab.evaluation.evaluator import ModelEvaluator
from retentionlab.features.builder import FeatureBuilder
from retentionlab.labels.target import TargetLabeler
from retentionlab.models.trainer import ModelTrainer
from retentionlab.reporting.excel_generator import ExcelReportGenerator
from retentionlab.reporting.powerbi_exporter import PowerBIExporter
from retentionlab.scoring.scorer import CustomerScorer
from retentionlab.validation.data_quality import run_sql_quality_checks


class RetentionLabPipeline:
    """
    Complete end-to-end analytical pipeline runner.
    """

    def __init__(self):
        self.settings = settings

    def run_all(self) -> Dict[str, Any]:
        """Execute all 11 stages of the pipeline sequentially."""
        pipeline_start = time.time()
        print("\n==================================================================")
        print("🚀 RETENTIONLAB MASTER PIPELINE: STARTING EXECUTION")
        print("==================================================================\n")

        # Stage 1: Synthetic Data Generation
        print("[1/8] Generating deterministic synthetic datasets...")
        t0 = time.time()
        generator = SyntheticDataGenerator(
            num_customers=self.settings.data_gen.num_customers,
            random_seed=self.settings.data_gen.random_seed,
            start_date=self.settings.data_gen.start_date,
            end_date=self.settings.data_gen.end_date,
            snapshot_date=self.settings.data_gen.snapshot_date,
            target_transaction_count=self.settings.data_gen.target_transaction_count,
        )
        data = generator.generate_all()
        print(f"      -> Generated {len(data['transactions']):,d} transactions across {len(data['customers']):,d} customers in {time.time() - t0:.2f}s")

        # Stage 2: Database Ingestion & Indexing
        print("[2/8] Initializing database and ingesting relational entities...")
        t0 = time.time()
        engine = get_engine()
        init_db(engine)
        for tbl_name, df in data.items():
            save_dataframe_to_table(df, tbl_name, if_exists="replace", engine=engine)

        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_txn_cust_date ON transactions(customer_id, transaction_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(transaction_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_txn_cust ON transactions(customer_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_act_cust ON customer_activity(customer_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_act_date ON customer_activity(activity_date);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sup_cust ON support_tickets(customer_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_cam_cust ON campaign_interactions(customer_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_snap_cust ON customer_snapshots(customer_id);"))
            conn.commit()
        print(f"      -> Ingested and indexed 7 tables in {time.time() - t0:.2f}s")

        # Stage 3: Relational Data Quality Checks
        print("[3/8] Running relational schema & integrity assertions...")
        t0 = time.time()
        dq_results = run_sql_quality_checks()
        failed_checks = dq_results[dq_results["status"] != "PASS"]
        if not failed_checks.empty:
            raise ValueError(f"Data quality checks failed: {failed_checks.to_dict(orient='records')}")
        print(f"      -> Verified {len(dq_results)} SQL data quality assertions (0 failures) in {time.time() - t0:.2f}s")

        # Stage 4: 44-Feature Behavioral Engineering
        print(f"[4/8] Building 44 behavioral features at snapshot date {self.settings.features.snapshot_date}...")
        t0 = time.time()
        builder = FeatureBuilder(snapshot_date=self.settings.features.snapshot_date)
        features_df = builder.build_features(
            data["customers"], data["transactions"], data["customer_activity"],
            data["support_tickets"], data["campaign_interactions"], data["products"]
        )
        proc_dir = self.settings.root_dir / "data" / "processed"
        proc_dir.mkdir(parents=True, exist_ok=True)
        features_df.to_csv(proc_dir / "customer_features_44.csv", index=False)
        print(f"      -> Engineered {len(features_df):,d} customer snapshots x 44 features in {time.time() - t0:.2f}s")

        # Stage 5: Leakage-Free Target Labeling
        print("[5/8] Constructing leakage-free future-window churn labels...")
        t0 = time.time()
        labeler = TargetLabeler(
            snapshot_date=self.settings.features.snapshot_date,
            prediction_horizon_days=self.settings.data_gen.prediction_horizon_days,
        )
        labels_df = labeler.create_labels(data["customers"], data["transactions"])
        labels_df.to_csv(proc_dir / "churn_labels.csv", index=False)
        print(f"      -> Observed future churn rate: {labels_df['is_churn'].mean():.1%} in {time.time() - t0:.2f}s")

        # Stage 6: Model Training & Benchmarking
        print("[6/8] Training candidate classifiers & optimizing validation decision threshold...")
        t0 = time.time()
        trainer = ModelTrainer(random_state=self.settings.modeling.random_state)
        data_splits = trainer.prepare_data(
            features_df, labels_df,
            test_size=self.settings.modeling.test_size,
            val_size=self.settings.modeling.val_size
        )
        train_output = trainer.train_and_compare(data_splits)
        evaluator = ModelEvaluator()
        art_paths = evaluator.save_model_artifacts(train_output, trainer.feature_names)
        best_name = train_output["best_model_name"]
        test_auc = train_output["candidate_results"][best_name]["test_metrics"]["roc_auc"]
        print(f"      -> Champion: {best_name} (Holdout Test ROC-AUC: {test_auc:.4f}) in {time.time() - t0:.2f}s")

        # Stage 7: Customer Scoring & Prioritization
        print("[7/8] Scoring customer risk, attaching signals & ranking operational cohorts...")
        t0 = time.time()
        scorer = CustomerScorer()
        scored_df = scorer.score_customers(features_df)
        scorer.persist_scores(scored_df)
        top_cohort_cnt = int(scored_df["is_top_15_percent"].sum())
        top_exposure = scored_df.loc[scored_df["is_top_15_percent"] == 1, "risk_weighted_exposure"].sum()
        print(f"      -> Scored {len(scored_df):,d} accounts; Top 15% Cohort: {top_cohort_cnt:,d} accounts (${top_exposure/1e6:.2f}M exposure) in {time.time() - t0:.2f}s")

        # Stage 8: Power BI & Excel Exports
        print("[8/8] Exporting Power BI star-schema tables & Excel action workbook...")
        t0 = time.time()
        pbi_exp = PowerBIExporter()
        pbi_exp.export_star_schema()
        comp_df = pd.read_csv(self.settings.root_dir / "models" / "model_comparison.csv")
        excel_gen = ExcelReportGenerator()
        wb_path = excel_gen.generate_workbook(scored_df, comp_df)
        print(f"      -> Reporting assets generated in {time.time() - t0:.2f}s")

        total_elapsed = time.time() - pipeline_start
        print("\n==================================================================")
        print(f"✅ RETENTIONLAB PIPELINE COMPLETED SUCCESSFULLY IN {total_elapsed:.2f}s")
        print("==================================================================\n")

        return {
            "total_transactions": len(data["transactions"]),
            "total_customers": len(data["customers"]),
            "scored_customers": len(scored_df),
            "champion_model": best_name,
            "test_roc_auc": test_auc,
            "top_cohort_size": top_cohort_cnt,
            "top_cohort_exposure": top_exposure,
            "excel_workbook_path": str(wb_path),
            "elapsed_seconds": total_elapsed,
        }
