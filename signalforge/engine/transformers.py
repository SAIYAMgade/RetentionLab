from typing import Any, Callable, Dict, List, Optional
import pandas as pd
import numpy as np

class Transformer:
    """Performs schema mapping, type normalization, and cleaning on dataframes."""

    def __init__(
        self,
        field_mapping: Optional[Dict[str, str]] = None,
        type_conversions: Optional[Dict[str, str]] = None,
        fill_defaults: Optional[Dict[str, Any]] = None,
        drop_duplicates_subset: Optional[List[str]] = None,
        custom_transforms: Optional[List[Callable[[pd.DataFrame], pd.DataFrame]]] = None
    ):
        self.field_mapping = field_mapping or {}
        self.type_conversions = type_conversions or {}
        self.fill_defaults = fill_defaults or {}
        self.drop_duplicates_subset = drop_duplicates_subset
        self.custom_transforms = custom_transforms or []

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        df_out = df.copy()

        # 1. Rename columns according to mapping
        if self.field_mapping:
            df_out = df_out.rename(columns=self.field_mapping)

        # 2. Fill default values
        for col, default_val in self.fill_defaults.items():
            if col in df_out.columns:
                df_out[col] = df_out[col].fillna(default_val)

        # 3. Apply type conversions
        for col, target_type in self.type_conversions.items():
            if col in df_out.columns:
                t = target_type.lower()
                if t in ("int", "integer"):
                    df_out[col] = pd.to_numeric(df_out[col], errors="coerce").fillna(0).astype(int)
                elif t in ("float", "numeric"):
                    df_out[col] = pd.to_numeric(df_out[col], errors="coerce").astype(float)
                elif t in ("datetime", "timestamp"):
                    df_out[col] = pd.to_datetime(df_out[col], errors="coerce")
                elif t in ("str", "string"):
                    df_out[col] = df_out[col].astype(str).str.strip()

        # 4. String column trimming
        for col in df_out.select_dtypes(include=["object"]).columns:
            df_out[col] = df_out[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

        # 5. Deduplicate
        if self.drop_duplicates_subset:
            valid_cols = [c for c in self.drop_duplicates_subset if c in df_out.columns]
            if valid_cols:
                df_out = df_out.drop_duplicates(subset=valid_cols, keep="last")

        # 6. Apply custom transform functions
        for custom_fn in self.custom_transforms:
            df_out = custom_fn(df_out)

        return df_out.reset_index(drop=True)
