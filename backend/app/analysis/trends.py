"""
Trend Analysis Module.
Detects temporal patterns and trends in time-series data.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from scipy import stats
from app.schemas.schemas import TrendResult


def analyze_trends(df: pd.DataFrame) -> List[TrendResult]:
    """Detect trends in datetime-indexed numeric columns."""
    results = []

    # Find datetime columns
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    # Also check object columns that might be dates
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            parsed = pd.to_datetime(df[col].head(20), errors="coerce")
            if parsed.notna().mean() > 0.7:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                date_cols.append(col)
        except Exception:
            pass

    if not date_cols:
        # Try numeric index as proxy for time
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                       if not c.endswith("_norm")]
        for col in numeric_cols[:5]:
            trend = _analyze_numeric_trend(df[col], col)
            if trend:
                results.append(trend)
        return results

    # Use the first datetime column as time axis
    time_col = date_cols[0]
    df_sorted = df.sort_values(time_col).dropna(subset=[time_col])

    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                   if not c.endswith("_norm")]

    for col in numeric_cols[:10]:  # Limit to 10 columns
        trend = _analyze_time_series(df_sorted, time_col, col)
        if trend:
            results.append(trend)

    return results


def _analyze_time_series(df: pd.DataFrame, time_col: str, value_col: str) -> TrendResult:
    """Analyze a time series for trend direction and strength."""
    try:
        series = df[[time_col, value_col]].dropna()
        if len(series) < 5:
            return None

        values = series[value_col].values
        x = np.arange(len(values))

        # Linear regression for trend
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)

        # Determine direction
        r_squared = r_value ** 2
        if p_value > 0.05 or r_squared < 0.1:
            direction = "estable"
        elif slope > 0:
            direction = "creciente"
        else:
            direction = "decreciente"

        # Check for cyclical pattern
        if len(values) >= 20:
            try:
                detrended = values - (slope * x + intercept)
                fft = np.fft.fft(detrended)
                power = np.abs(fft[1:len(fft)//2])
                if len(power) > 0:
                    peak_freq = np.argmax(power) + 1
                    period_length = len(values) / peak_freq
                    # If there's a strong periodic component
                    if np.max(power) > np.mean(power) * 3:
                        direction = "cíclico"
            except Exception:
                pass

        # Build data points for charting (sample if too many)
        sample_size = min(100, len(series))
        sample_indices = np.linspace(0, len(series) - 1, sample_size, dtype=int)
        data_points = []
        for idx in sample_indices:
            row = series.iloc[idx]
            data_points.append({
                "x": str(row[time_col]),
                "y": float(row[value_col]) if not np.isnan(row[value_col]) else 0,
            })

        return TrendResult(
            column=value_col,
            direction=direction,
            strength=round(float(r_squared), 4),
            data_points=data_points,
        )

    except Exception as e:
        print(f"Trend analysis error for {value_col}: {e}")
        return None


def _analyze_numeric_trend(series: pd.Series, col_name: str) -> TrendResult:
    """Analyze trend for a numeric column without datetime index."""
    try:
        values = series.dropna().values
        if len(values) < 10:
            return None

        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)

        r_squared = r_value ** 2
        if r_squared < 0.05:
            return None

        direction = "creciente" if slope > 0 else "decreciente"
        if r_squared < 0.1:
            direction = "estable"

        sample_size = min(50, len(values))
        indices = np.linspace(0, len(values) - 1, sample_size, dtype=int)
        data_points = [{"x": int(i), "y": float(values[i])} for i in indices]

        return TrendResult(
            column=col_name,
            direction=direction,
            strength=round(float(r_squared), 4),
            data_points=data_points,
        )

    except Exception:
        return None
