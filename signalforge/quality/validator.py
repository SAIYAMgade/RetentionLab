import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd
import numpy as np

from signalforge.quality.rules import QualityRule, RuleEvaluationResult, RuleSeverity, RuleType

class QualityValidator:
    """Evaluates declarative data quality rules against pandas DataFrames."""

    def __init__(self, rules: List[QualityRule]):
        self.rules = [r for r in rules if r.is_active]

    def evaluate(
        self,
        df: pd.DataFrame,
        reference_data: Optional[Dict[str, Set[Any]]] = None,
        identifier_column: Optional[str] = None
    ) -> Tuple[bool, pd.DataFrame, List[Dict[str, Any]], List[RuleEvaluationResult]]:
        """
        Evaluates rules against DataFrame.
        Returns:
            (is_batch_valid, valid_df, rejected_records_list, rule_results)
        """
        rule_results: List[RuleEvaluationResult] = []
        rejected_by_index: Dict[int, List[str]] = {}
        batch_failed = False
        batch_failure_reasons: List[str] = []

        total_rows = len(df)

        for rule in self.rules:
            t0 = time.perf_counter()
            eval_res = self._evaluate_rule(rule, df, reference_data)
            eval_res.execution_time_ms = round((time.perf_counter() - t0) * 1000, 2)
            rule_results.append(eval_res)

            if not eval_res.passed:
                if rule.severity == RuleSeverity.BATCH_FAIL:
                    batch_failed = True
                    batch_failure_reasons.append(
                        f"Rule {rule.rule_name} (BATCH_FAIL) failed with {eval_res.failed_count} violations"
                    )
                else:
                    # Accumulate record-level rejection reasons
                    for idx, reasons in eval_res.rejection_reasons_by_index.items():
                        rejected_by_index.setdefault(idx, []).extend(reasons)

        # Build rejected records payload
        rejected_records: List[Dict[str, Any]] = []
        rejected_indices = set(rejected_by_index.keys())

        for idx in sorted(rejected_indices):
            row_data = df.iloc[idx].to_dict()
            # Clean timestamps / NaN for JSON serialization
            cleaned_row = {
                k: (None if pd.isna(v) else (v.isoformat() if hasattr(v, "isoformat") else v))
                for k, v in row_data.items()
            }
            ident_val = str(cleaned_row.get(identifier_column)) if identifier_column and identifier_column in cleaned_row else str(idx)
            rejected_records.append({
                "record_identifier": ident_val,
                "raw_data": cleaned_row,
                "rejection_reasons": rejected_by_index[idx]
            })

        # Filter out rejected rows to produce valid_df
        if rejected_indices:
            valid_df = df.drop(index=list(rejected_indices)).reset_index(drop=True)
        else:
            valid_df = df.copy()

        is_batch_valid = not batch_failed
        return is_batch_valid, valid_df, rejected_records, rule_results

    def _evaluate_rule(
        self,
        rule: QualityRule,
        df: pd.DataFrame,
        reference_data: Optional[Dict[str, Set[Any]]]
    ) -> RuleEvaluationResult:
        column = rule.params.get("column")
        total_checked = len(df)
        failed_indices: List[int] = []
        reasons_by_idx: Dict[int, List[str]] = {}
        sample_failures: List[Dict[str, Any]] = []

        # 1. NOT_NULL
        if rule.rule_type == RuleType.NOT_NULL:
            if column not in df.columns:
                failed_indices = list(range(len(df)))
                for idx in failed_indices:
                    reasons_by_idx[idx] = [f"Missing required column '{column}'"]
            else:
                mask = df[column].isna() | (df[column].astype(str).str.strip() == "") | (df[column].astype(str) == "None")
                bad_idx = df[mask].index.tolist()
                for idx in bad_idx:
                    reasons_by_idx[idx] = [f"Null or empty value in required column '{column}'"]
                failed_indices = bad_idx

        # 2. UNIQUE
        elif rule.rule_type == RuleType.UNIQUE:
            if column in df.columns:
                dup_mask = df.duplicated(subset=[column], keep="first")
                bad_idx = df[dup_mask].index.tolist()
                for idx in bad_idx:
                    val = df.iloc[idx][column]
                    reasons_by_idx[idx] = [f"Duplicate value '{val}' in unique column '{column}'"]
                failed_indices = bad_idx

        # 3. TYPE_CHECK
        elif rule.rule_type == RuleType.TYPE_CHECK:
            expected_type = rule.params.get("expected_type", "string").lower()
            if column in df.columns:
                for idx, val in enumerate(df[column]):
                    if pd.isna(val):
                        continue
                    is_valid = True
                    if expected_type in ("int", "integer"):
                        try:
                            float_val = float(val)
                            is_valid = float_val.is_integer()
                        except (ValueError, TypeError):
                            is_valid = False
                    elif expected_type in ("float", "numeric", "number"):
                        try:
                            float(val)
                        except (ValueError, TypeError):
                            is_valid = False
                    elif expected_type in ("datetime", "timestamp"):
                        try:
                            pd.to_datetime(val)
                        except Exception:
                            is_valid = False
                    if not is_valid:
                        failed_indices.append(idx)
                        reasons_by_idx[idx] = [f"Value '{val}' in column '{column}' cannot be cast to {expected_type}"]

        # 4. NON_NEGATIVE
        elif rule.rule_type == RuleType.NON_NEGATIVE:
            if column in df.columns:
                numeric_series = pd.to_numeric(df[column], errors="coerce")
                neg_mask = (numeric_series < 0) & numeric_series.notna()
                bad_idx = df[neg_mask].index.tolist()
                for idx in bad_idx:
                    val = df.iloc[idx][column]
                    reasons_by_idx[idx] = [f"Negative value '{val}' violates non-negative constraint on '{column}'"]
                failed_indices = bad_idx

        # 5. VALID_TIMESTAMP
        elif rule.rule_type == RuleType.VALID_TIMESTAMP:
            if column in df.columns:
                for idx, val in enumerate(df[column]):
                    if pd.isna(val):
                        continue
                    try:
                        pd.to_datetime(val)
                    except Exception:
                        failed_indices.append(idx)
                        reasons_by_idx[idx] = [f"Invalid timestamp format '{val}' in column '{column}'"]

        # 6. REFERENTIAL_INTEGRITY
        elif rule.rule_type == RuleType.REFERENTIAL_INTEGRITY:
            ref_dataset = rule.params.get("reference_dataset")
            ref_column = rule.params.get("reference_column")
            if column in df.columns and reference_data and ref_dataset in reference_data:
                valid_fk_set = reference_data[ref_dataset]
                for idx, val in enumerate(df[column]):
                    if pd.notna(val) and str(val) not in valid_fk_set and val not in valid_fk_set:
                        failed_indices.append(idx)
                        reasons_by_idx[idx] = [
                            f"Foreign key violation: '{val}' does not exist in {ref_dataset}.{ref_column}"
                        ]

        # 7. CATEGORY_WHITELIST
        elif rule.rule_type == RuleType.CATEGORY_WHITELIST:
            allowed = set(rule.params.get("allowed_values", []))
            if column in df.columns and allowed:
                for idx, val in enumerate(df[column]):
                    if pd.notna(val) and val not in allowed and str(val) not in allowed:
                        failed_indices.append(idx)
                        reasons_by_idx[idx] = [
                            f"Unexpected category '{val}' in column '{column}'. Allowed: {sorted(list(allowed))}"
                        ]

        # 8. RECORD_COUNT_DEVIATION
        elif rule.rule_type == RuleType.RECORD_COUNT_DEVIATION:
            min_count = rule.params.get("min_count", 0)
            max_count = rule.params.get("max_count", float("inf"))
            if len(df) < min_count or len(df) > max_count:
                failed_indices = [0] if len(df) > 0 else []
                sample_failures.append({
                    "error": f"Record count {len(df)} outside allowed range [{min_count}, {max_count}]"
                })

        # 9. DATA_FRESHNESS
        elif rule.rule_type == RuleType.DATA_FRESHNESS:
            max_age_hours = rule.params.get("max_age_hours", 24)
            if column in df.columns and len(df) > 0:
                try:
                    timestamps = pd.to_datetime(df[column], errors="coerce").dropna()
                    if not timestamps.empty:
                        latest = timestamps.max()
                        if latest.tzinfo is not None:
                            now = datetime.now(timezone.utc)
                        else:
                            now = datetime.utcnow()
                        age_hours = (now - latest.to_pydatetime()).total_seconds() / 3600.0
                        if age_hours > max_age_hours:
                            failed_indices = [0]
                            sample_failures.append({
                                "error": f"Data stale: latest record timestamp {latest} is {age_hours:.1f} hours old (threshold: {max_age_hours}h)"
                            })
                except Exception as ex:
                    failed_indices = [0]
                    sample_failures.append({"error": f"Freshness calculation failed: {str(ex)}"})

        # 10. SCHEMA_COMPATIBILITY
        elif rule.rule_type == RuleType.SCHEMA_COMPATIBILITY:
            required_cols = set(rule.params.get("required_columns", []))
            missing = required_cols - set(df.columns)
            if missing:
                failed_indices = [0] if len(df) > 0 else []
                sample_failures.append({
                    "error": f"Schema incompatible: missing required columns {sorted(list(missing))}"
                })

        # Populate sample failures from individual row failures
        if not sample_failures and failed_indices:
            for idx in failed_indices[:5]:
                row_dict = df.iloc[idx].to_dict()
                sample_failures.append({
                    "index": idx,
                    "reasons": reasons_by_idx.get(idx, []),
                    "data": {k: (None if pd.isna(v) else str(v)) for k, v in row_dict.items()}
                })

        failed_count = len(failed_indices)
        passed = (failed_count == 0)

        return RuleEvaluationResult(
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            dataset_name=rule.dataset_name,
            passed=passed,
            total_checked=total_checked,
            failed_count=failed_count,
            severity=rule.severity,
            sample_failures=sample_failures,
            failed_indices=failed_indices,
            rejection_reasons_by_index=reasons_by_idx
        )
