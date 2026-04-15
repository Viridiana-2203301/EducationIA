"""
Data Cleaning & Normalization Service.
Handles: duplicate removal, null imputation, type correction, string stripping,
date normalization, numeric scaling, and text normalization.
Preserves original files, outputs cleaned versions. Logs cleaning statistics.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple
from app.schemas.schemas import CleaningStats

COLUMN_NORMALIZATION_MAP = {
    "cve_entidad": "entidad",
    "entidad": "c_nom_ent",
    "cve_municipio": "cv_mun",
    "municipio": "c_nom_mun",
    "alumnos_lic_esc": "alumnos",
    "ni_lic_total_esc": "nvo_ing",
}

import re

def _extract_education_level(filename: str) -> str:
    """Extrae el nivel educativo del nombre del archivo."""
    if not filename:
        return "desconocido"
    name = filename.lower()
    
    # Try finding exact common levels
    levels = [
        "media_superior", "superior_escolarizada", "basica", "capacitacion", "especial"
    ]
    for level in levels:
        if level in name:
            return level.replace("_", " ")
            
    # Fallback to cleaning the name
    name = name.split(".csv")[0]
    # Remove uuid prefix if present (e.g., a64c9bce_)
    if len(name) > 9 and name[8] == "_":
        name = name[9:]
    # Remove common prefixes and suffixes
    name = name.replace("educacion_", "")
    name = re.sub(r'_\d{4}_\d{4}$', '', name)
    return name.replace("_", " ")


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to a standard format to allow matching across dataset types."""
    # Only apply the mapping if it's a dataset in the 'superior' format
    # The 'superior' format uses 'cve_entidad' instead of 'entidad' for the ID.
    if "cve_entidad" in df.columns or "cve_municipio" in df.columns or "alumnos_lic_esc" in df.columns:
        return df.rename(columns=COLUMN_NORMALIZATION_MAP)
    return df


def clean_dataset(df: pd.DataFrame, dataset_id: str, filename: str = "") -> Tuple[pd.DataFrame, CleaningStats]:
    """
    Full cleaning pipeline for a single dataset.
    Returns (cleaned_df, cleaning_stats).
    """
    rows_before = len(df)
    stats = CleaningStats(
        dataset_id=dataset_id,
        rows_before=rows_before,
        rows_after=rows_before,
    )

    # Añadir columna de tipo de educación si se proporciona el filename
    if filename:
        df["tipo_educacion"] = _extract_education_level(filename)

    # 0. Normalize column names
    df = _normalize_column_names(df)

    # 1. Strip whitespace from string columns
    df = _strip_strings(df)


    # 2. Remove exact duplicate rows
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        stats.duplicates_removed = dup_count

    # 3. Handle null values
    df, nulls_filled, nulls_dropped = _handle_nulls(df)
    stats.nulls_filled = nulls_filled
    stats.nulls_dropped = nulls_dropped

    # 4. Correct data types
    df, types_corrected = _correct_types(df)
    stats.types_corrected = types_corrected

    # 5. Normalize numeric columns (StandardScaler-like)
    df, normalized_cols = _normalize_numerics(df)
    stats.columns_normalized = normalized_cols

    # 6. Normalize date columns
    df = _normalize_dates(df)

    stats.rows_after = len(df)

    return df, stats


def _strip_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and special chars from string columns."""
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
        # Replace 'nan' strings back to NaN
        df[col] = df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})
    return df


def _handle_nulls(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Strategy:
    - Numeric columns: fill with median if <30% null, drop rows if >50% null
    - Categorical columns: fill with mode if <30% null, 'Desconocido' if 30-50%, drop >50%
    """
    nulls_filled = 0
    nulls_dropped = 0

    for col in df.columns:
        null_pct = df[col].isnull().mean()

        if null_pct == 0:
            continue

        if null_pct > 0.5:
            # Drop column if more than 50% null
            nulls_dropped += int(df[col].isnull().sum())
            df = df.drop(columns=[col])
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            median_val = df[col].median()
            null_count = int(df[col].isnull().sum())
            df[col] = df[col].fillna(median_val)
            nulls_filled += null_count
        else:
            null_count = int(df[col].isnull().sum())
            if null_pct < 0.3:
                mode_val = df[col].mode()
                if len(mode_val) > 0:
                    df[col] = df[col].fillna(mode_val.iloc[0])
                else:
                    df[col] = df[col].fillna("Desconocido")
            else:
                df[col] = df[col].fillna("Desconocido")
            nulls_filled += null_count

    return df, nulls_filled, nulls_dropped


def _correct_types(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Try to convert string columns to proper types."""
    corrected = 0

    for col in df.select_dtypes(include=["object"]).columns:
        non_null = df[col].dropna()
        if len(non_null) == 0:
            continue

        # Try numeric conversion
        try:
            numeric_vals = pd.to_numeric(non_null, errors="coerce")
            if numeric_vals.notna().mean() > 0.8:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                corrected += 1
                continue
        except Exception:
            pass

        # Try datetime conversion
        try:
            datetime_vals = pd.to_datetime(non_null.head(50), errors="coerce", format="mixed")
            if datetime_vals.notna().mean() > 0.7:
                df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
                corrected += 1
                continue
        except Exception:
            pass

    return df, corrected


def _normalize_numerics(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Add normalized versions of numeric columns using min-max scaling.
    Original columns are preserved, normalized columns added with _norm suffix.
    """
    normalized_cols = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    for col in numeric_cols:
        min_val = df[col].min()
        max_val = df[col].max()

        if max_val - min_val > 0:
            norm_col_name = f"{col}_norm"
            df[norm_col_name] = (df[col] - min_val) / (max_val - min_val)
            normalized_cols.append(norm_col_name)

    return df, normalized_cols


def _normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize datetime columns to consistent format."""
    for col in df.select_dtypes(include=["datetime64"]).columns:
        # Already datetime type, ensure UTC-naive
        try:
            if df[col].dt.tz is not None:
                df[col] = df[col].dt.tz_localize(None)
        except Exception:
            pass
    return df
