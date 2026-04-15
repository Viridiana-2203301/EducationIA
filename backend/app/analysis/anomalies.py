"""
Anomaly Detection Module.
Implements Isolation Forest and Local Outlier Factor.
"""

import pandas as pd
import numpy as np
from typing import List
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from app.schemas.schemas import AnomalyResult


def detect_anomalies(df: pd.DataFrame) -> List[AnomalyResult]:
    """Run anomaly detection using Isolation Forest and LOF."""
    results = []

    numeric_df = df.select_dtypes(include=[np.number])
    numeric_df = numeric_df[[c for c in numeric_df.columns if not c.endswith("_norm")]]
    numeric_df = numeric_df.dropna()

    if numeric_df.shape[0] < 20 or numeric_df.shape[1] < 1:
        return results

    scaler = StandardScaler()
    X = scaler.fit_transform(numeric_df)

    # Sample for large datasets
    sample_indices = None
    if len(X) > 10000:
        sample_indices = np.random.choice(len(X), 10000, replace=False)
        X = X[sample_indices]

    # Isolation Forest
    iso_result = _run_isolation_forest(X, sample_indices)
    if iso_result:
        results.append(iso_result)

    # Local Outlier Factor
    lof_result = _run_lof(X, sample_indices)
    if lof_result:
        results.append(lof_result)

    return results


def _run_isolation_forest(X: np.ndarray, sample_indices=None) -> AnomalyResult:
    """Run Isolation Forest anomaly detection."""
    try:
        contamination = min(0.1, max(0.01, 50 / len(X)))

        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        predictions = iso_forest.fit_predict(X)
        scores = iso_forest.decision_function(X)

        anomaly_mask = predictions == -1
        anomaly_count = int(anomaly_mask.sum())

        anomaly_indices = np.where(anomaly_mask)[0].tolist()
        if sample_indices is not None:
            anomaly_indices = [int(sample_indices[i]) for i in anomaly_indices]

        anomaly_scores = scores[anomaly_mask].tolist()
        anomaly_scores = [round(float(s), 4) for s in anomaly_scores[:100]]

        return AnomalyResult(
            method="isolation_forest",
            n_anomalies=anomaly_count,
            anomaly_indices=anomaly_indices[:500],
            anomaly_scores=anomaly_scores,
            anomaly_percentage=round(anomaly_count / len(X) * 100, 2),
        )

    except Exception as e:
        print(f"Isolation Forest error: {e}")
        return None


def _run_lof(X: np.ndarray, sample_indices=None) -> AnomalyResult:
    """Run Local Outlier Factor anomaly detection."""
    try:
        n_neighbors = min(20, len(X) // 5)
        if n_neighbors < 2:
            return None

        lof = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=min(0.1, max(0.01, 50 / len(X))),
        )
        predictions = lof.fit_predict(X)
        scores = lof.negative_outlier_factor_

        anomaly_mask = predictions == -1
        anomaly_count = int(anomaly_mask.sum())

        anomaly_indices = np.where(anomaly_mask)[0].tolist()
        if sample_indices is not None:
            anomaly_indices = [int(sample_indices[i]) for i in anomaly_indices]

        anomaly_scores = scores[anomaly_mask].tolist()
        anomaly_scores = [round(float(s), 4) for s in anomaly_scores[:100]]

        return AnomalyResult(
            method="lof",
            n_anomalies=anomaly_count,
            anomaly_indices=anomaly_indices[:500],
            anomaly_scores=anomaly_scores,
            anomaly_percentage=round(anomaly_count / len(X) * 100, 2),
        )

    except Exception as e:
        print(f"LOF error: {e}")
        return None
