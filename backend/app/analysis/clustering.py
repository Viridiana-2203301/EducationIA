"""
Clustering Analysis Module.
Implements K-Means and DBSCAN with automatic parameter selection.
"""

import pandas as pd
import numpy as np
from typing import List
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from app.schemas.schemas import ClusterResult


def compute_clustering(df: pd.DataFrame) -> List[ClusterResult]:
    """Run K-Means and DBSCAN clustering on numeric features."""
    results = []

    numeric_df = df.select_dtypes(include=[np.number])
    numeric_df = numeric_df[[c for c in numeric_df.columns if not c.endswith("_norm")]]
    numeric_df = numeric_df.dropna()

    if numeric_df.shape[0] < 10 or numeric_df.shape[1] < 2:
        return results

    # Scale features
    scaler = StandardScaler()
    X = scaler.fit_transform(numeric_df)

    # Limit sample size for performance
    if len(X) > 10000:
        indices = np.random.choice(len(X), 10000, replace=False)
        X = X[indices]

    # K-Means with auto K selection
    kmeans_result = _run_kmeans(X)
    if kmeans_result:
        results.append(kmeans_result)

    # DBSCAN
    dbscan_result = _run_dbscan(X)
    if dbscan_result:
        results.append(dbscan_result)

    return results


def _run_kmeans(X: np.ndarray) -> ClusterResult:
    """Run K-Means with automatic K selection using silhouette score."""
    try:
        best_k = 3
        best_score = -1

        k_range = range(2, min(8, len(X) // 5 + 1))
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
            labels = kmeans.fit_predict(X)

            if len(set(labels)) < 2:
                continue

            score = silhouette_score(X, labels, sample_size=min(1000, len(X)))
            if score > best_score:
                best_score = score
                best_k = k

        # Final run with best K
        final_kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = final_kmeans.fit_predict(X)

        cluster_sizes = {}
        for label in set(labels):
            cluster_sizes[f"Cluster {label}"] = int((labels == label).sum())

        centers = final_kmeans.cluster_centers_.tolist()

        return ClusterResult(
            method="kmeans",
            n_clusters=best_k,
            labels=labels.tolist(),
            cluster_centers=centers,
            cluster_sizes=cluster_sizes,
            silhouette_score=round(float(best_score), 4),
        )

    except Exception as e:
        print(f"KMeans error: {e}")
        return None


def _run_dbscan(X: np.ndarray) -> ClusterResult:
    """Run DBSCAN with auto-estimated eps."""
    try:
        from sklearn.neighbors import NearestNeighbors

        # Estimate eps using k-distance
        k = min(5, len(X) - 1)
        nn = NearestNeighbors(n_neighbors=k)
        nn.fit(X)
        distances, _ = nn.kneighbors(X)
        sorted_distances = np.sort(distances[:, -1])
        eps = float(np.percentile(sorted_distances, 90))

        dbscan = DBSCAN(eps=eps, min_samples=max(3, len(X) // 100))
        labels = dbscan.fit_predict(X)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

        if n_clusters < 1:
            return None

        cluster_sizes = {}
        for label in set(labels):
            name = f"Ruido" if label == -1 else f"Cluster {label}"
            cluster_sizes[name] = int((labels == label).sum())

        sil_score = None
        if n_clusters >= 2:
            try:
                mask = labels != -1
                if mask.sum() > n_clusters:
                    sil_score = round(float(silhouette_score(X[mask], labels[mask])), 4)
            except Exception:
                pass

        return ClusterResult(
            method="dbscan",
            n_clusters=n_clusters,
            labels=labels.tolist(),
            cluster_sizes=cluster_sizes,
            silhouette_score=sil_score,
        )

    except Exception as e:
        print(f"DBSCAN error: {e}")
        return None
