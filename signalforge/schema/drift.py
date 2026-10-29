from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

class DriftSeverity(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    POTENTIALLY_BREAKING = "POTENTIALLY_BREAKING"
    BREAKING = "BREAKING"

class DriftType(str, Enum):
    NONE = "NONE"
    COLUMN_ADDED = "COLUMN_ADDED"
    COLUMN_REMOVED = "COLUMN_REMOVED"
    TYPE_CHANGED = "TYPE_CHANGED"
    REQUIRED_MISSING = "REQUIRED_MISSING"
    POSSIBLE_RENAME = "POSSIBLE_RENAME"

@dataclass
class ColumnMeta:
    name: str
    data_type: str  # string, integer, float, datetime, boolean
    nullable: bool = True
    required: bool = False

@dataclass
class DriftReport:
    has_drift: bool
    severity: DriftSeverity
    drift_types: List[DriftType]
    diff: Dict[str, Any]
    recommended_action: str
    added_columns: List[str] = field(default_factory=list)
    removed_columns: List[str] = field(default_factory=list)
    type_changes: Dict[str, Dict[str, str]] = field(default_factory=dict)
    missing_required: List[str] = field(default_factory=list)

def infer_schema_from_df(df: pd.DataFrame, required_columns: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
    """Infers simplified column metadata from a pandas DataFrame."""
    required_set = set(required_columns or [])
    columns_meta: Dict[str, Dict[str, Any]] = {}

    for col in df.columns:
        series = df[col]
        # Infer basic type
        if pd.api.types.is_integer_dtype(series):
            simple_type = "integer"
        elif pd.api.types.is_float_dtype(series):
            simple_type = "float"
        elif pd.api.types.is_datetime64_any_dtype(series):
            simple_type = "datetime"
        elif pd.api.types.is_bool_dtype(series):
            simple_type = "boolean"
        else:
            # Check if string column contains ISO datetime strings
            sample_non_null = series.dropna().head(10)
            if not sample_non_null.empty and any(term in col.lower() for term in ["date", "time", "timestamp"]):
                try:
                    pd.to_datetime(sample_non_null)
                    simple_type = "datetime"
                except Exception:
                    simple_type = "string"
            else:
                simple_type = "string"

        has_nulls = bool(series.isna().any())
        columns_meta[col] = {
            "name": col,
            "data_type": simple_type,
            "nullable": has_nulls,
            "required": (col in required_set)
        }

    return columns_meta

class SchemaDriftDetector:
    """Compares an observed dataset schema against a baseline schema version."""

    COMPATIBLE_TYPE_PROMOTIONS = {
        ("integer", "float"),
        ("integer", "string"),
        ("float", "string"),
        ("boolean", "string"),
    }

    @classmethod
    def detect_drift(
        cls,
        baseline_schema: Dict[str, Dict[str, Any]],
        observed_schema: Dict[str, Dict[str, Any]]
    ) -> DriftReport:
        baseline_cols = set(baseline_schema.keys())
        observed_cols = set(observed_schema.keys())

        added = sorted(list(observed_cols - baseline_cols))
        removed = sorted(list(baseline_cols - observed_cols))

        missing_required = [
            col for col in removed
            if baseline_schema[col].get("required", False)
        ]

        type_changes: Dict[str, Dict[str, str]] = {}
        for col in baseline_cols.intersection(observed_cols):
            base_t = baseline_schema[col].get("data_type", "string")
            obs_t = observed_schema[col].get("data_type", "string")
            if base_t != obs_t:
                type_changes[col] = {"from": base_t, "to": obs_t}

        drift_types: List[DriftType] = []
        severity = DriftSeverity.COMPATIBLE
        has_drift = bool(added or removed or type_changes)

        if not has_drift:
            return DriftReport(
                has_drift=False,
                severity=DriftSeverity.COMPATIBLE,
                drift_types=[DriftType.NONE],
                diff={},
                recommended_action="No drift detected. Observed schema matches baseline."
            )

        # Check severity rules
        if missing_required:
            severity = DriftSeverity.BREAKING
            drift_types.append(DriftType.REQUIRED_MISSING)

        for col, change in type_changes.items():
            drift_types.append(DriftType.TYPE_CHANGED)
            base_t, obs_t = change["from"], change["to"]
            if (base_t, obs_t) not in cls.COMPATIBLE_TYPE_PROMOTIONS:
                severity = DriftSeverity.BREAKING

        if removed and severity != DriftSeverity.BREAKING:
            severity = DriftSeverity.POTENTIALLY_BREAKING
            drift_types.append(DriftType.COLUMN_REMOVED)

        if added:
            drift_types.append(DriftType.COLUMN_ADDED)
            if severity == DriftSeverity.COMPATIBLE:
                severity = DriftSeverity.COMPATIBLE

        # Generate recommendation
        actions = []
        if missing_required:
            actions.append(f"CRITICAL: Required columns missing ({missing_required}). Check upstream data source or API contract.")
        if type_changes:
            actions.append(f"Type changes detected ({type_changes}). Validate downstream consumer compatibility.")
        if removed and not missing_required:
            actions.append(f"Optional columns removed ({removed}). Verify if downstream models depend on these fields.")
        if added:
            actions.append(f"New columns detected ({added}). Consider registering a new schema version to capture these fields.")

        recommended_action = " ".join(actions)

        diff = {
            "added_columns": added,
            "removed_columns": removed,
            "missing_required": missing_required,
            "type_changes": type_changes
        }

        return DriftReport(
            has_drift=True,
            severity=severity,
            drift_types=drift_types,
            diff=diff,
            recommended_action=recommended_action,
            added_columns=added,
            removed_columns=removed,
            type_changes=type_changes,
            missing_required=missing_required
        )
