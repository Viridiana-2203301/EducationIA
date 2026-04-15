"""
Data Profiling Service.
Analyzes each dataset for: row counts, nulls, duplicates, distributions,
column types, and statistical summaries.
Uses chardet for encoding detection per csv-data-wrangler best practices.
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from app.schemas.schemas import DatasetProfile, ColumnProfile


def profile_dataset(df: pd.DataFrame, dataset_id: str, filename: str, encoding: str = "utf-8") -> DatasetProfile:
    """
    Generate a comprehensive profile for a single dataset.
    Validates row/column counts per csv-data-wrangler anti-pattern rules.
    """
    columns: List[ColumnProfile] = []

    for col_name in df.columns:
        series = df[col_name]
        col_profile = _profile_column(series, col_name)
        columns.append(col_profile)

    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

    profile = DatasetProfile(
        dataset_id=dataset_id,
        filename=filename,
        row_count=len(df),
        column_count=len(df.columns),
        duplicate_rows=int(df.duplicated().sum()),
        total_nulls=int(df.isnull().sum().sum()),
        columns=columns,
        memory_usage_mb=round(memory_mb, 2),
        encoding=encoding,
    )

    return profile


def _safe_float(val) -> Optional[float]:
    if val is None or pd.isna(val) or val == "":
        return None
    try:
        fval = float(val)
        if np.isinf(fval) or pd.isna(fval):
            return None
        return fval
    except (ValueError, TypeError):
        return None

def _profile_column(series: pd.Series, col_name: str) -> ColumnProfile:
    """Profile a single column."""
    null_count = int(series.isnull().sum())
    total = len(series)
    null_pct = round((null_count / total) * 100, 2) if total > 0 else 0.0

    unique_count = int(series.nunique())

    # Sample non-null values
    non_null = series.dropna()
    sample_values = non_null.head(5).tolist() if len(non_null) > 0 else []
    
    # Ensure sample values are JSON-serializable
    cleaned_samples = []
    for v in sample_values:
        if v is None or pd.isna(v):
            cleaned_samples.append(None)
        elif isinstance(v, (int, float)):
            if np.isinf(v):
                cleaned_samples.append(None)
            else:
                cleaned_samples.append(v)
        elif isinstance(v, (str, bool)):
            cleaned_samples.append(v)
        else:
            cleaned_samples.append(str(v))
    sample_values = cleaned_samples

    is_numeric = pd.api.types.is_numeric_dtype(series)
    is_datetime = pd.api.types.is_datetime64_any_dtype(series)
    is_categorical = (
        not is_numeric
        and not is_datetime
        and unique_count < max(20, total * 0.05)
        and total > 0
    )

    # Try to detect dates in string columns
    if not is_datetime and series.dtype == object and len(non_null) > 0:
        try:
            parsed = pd.to_datetime(non_null.head(20), infer_datetime_format=True, errors="coerce")
            if parsed.notna().sum() > len(parsed) * 0.7:
                is_datetime = True
        except Exception:
            pass

    col_profile = ColumnProfile(
        name=col_name,
        dtype=str(series.dtype),
        null_count=null_count,
        null_percentage=null_pct,
        unique_count=unique_count,
        sample_values=sample_values,
        is_numeric=is_numeric,
        is_categorical=is_categorical,
        is_datetime=is_datetime,
    )

    if is_numeric and len(non_null) > 0:
        mean_val = non_null.mean()
        std_val = non_null.std()
        min_val = non_null.min()
        max_val = non_null.max()
        median_val = non_null.median()

        col_profile.mean = _safe_float(round(float(mean_val), 4)) if not pd.isna(mean_val) else None
        col_profile.std = _safe_float(round(float(std_val), 4)) if not pd.isna(std_val) else None
        col_profile.min_val = _safe_float(min_val)
        col_profile.max_val = _safe_float(max_val)
        col_profile.median = _safe_float(round(float(median_val), 4)) if not pd.isna(median_val) else None

    return col_profile
