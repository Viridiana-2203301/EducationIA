"""
Correlation Analysis Module.
Computes Pearson and Spearman correlation matrices.
Identifies strong correlations automatically.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from app.schemas.schemas import CorrelationResult


def compute_correlations(df: pd.DataFrame) -> List[CorrelationResult]:
    """Compute Pearson and Spearman correlations for numeric columns."""
    results = []

    numeric_df = df.select_dtypes(include=[np.number])
    # Exclude _norm columns to avoid redundancy
    numeric_df = numeric_df[[c for c in numeric_df.columns if not c.endswith("_norm")]]

    if numeric_df.shape[1] < 2:
        return results

    # Pearson
    pearson = _compute_correlation_matrix(numeric_df, method="pearson")
    if pearson:
        results.append(pearson)

    # Spearman
    spearman = _compute_correlation_matrix(numeric_df, method="spearman")
    if spearman:
        results.append(spearman)

    return results


def _compute_correlation_matrix(df: pd.DataFrame, method: str) -> CorrelationResult:
    """Compute a single correlation matrix and extract strong correlations."""
    try:
        corr_matrix = df.corr(method=method)

        # Convert to serializable dict
        matrix_dict = {}
        for col in corr_matrix.columns:
            matrix_dict[col] = {}
            for row in corr_matrix.index:
                val = corr_matrix.loc[row, col]
                matrix_dict[col][row] = round(float(val), 4) if not np.isnan(val) else 0.0

        # Find strong correlations (|r| > 0.5, excluding self-correlations)
        strong: List[Dict[str, Any]] = []
        seen = set()

        for i, col_a in enumerate(corr_matrix.columns):
            for j, col_b in enumerate(corr_matrix.columns):
                if i >= j:
                    continue
                val = corr_matrix.iloc[i, j]
                if np.isnan(val):
                    continue
                if abs(val) > 0.5:
                    pair_key = tuple(sorted([col_a, col_b]))
                    if pair_key not in seen:
                        seen.add(pair_key)
                        strength = "fuerte" if abs(val) > 0.7 else "moderada"
                        direction = "positiva" if val > 0 else "negativa"

                        strong.append({
                            "column_a": col_a,
                            "column_b": col_b,
                            "value": round(float(val), 4),
                            "strength": strength,
                            "direction": direction,
                        })

        strong.sort(key=lambda x: abs(x["value"]), reverse=True)

        return CorrelationResult(
            method=method,
            matrix=matrix_dict,
            strong_correlations=strong,
        )

    except Exception as e:
        print(f"Correlation error ({method}): {e}")
        return CorrelationResult(method=method)
