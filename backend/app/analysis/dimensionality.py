"""
Dimensionality Reduction Module.
Implements PCA for feature reduction and visualization.
"""

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from app.schemas.schemas import PCAResult


def compute_pca(df: pd.DataFrame) -> PCAResult:
    """Run PCA on numeric features."""
    numeric_df = df.select_dtypes(include=[np.number])
    numeric_df = numeric_df[[c for c in numeric_df.columns if not c.endswith("_norm")]]
    numeric_df = numeric_df.dropna()

    if numeric_df.shape[0] < 5 or numeric_df.shape[1] < 2:
        return PCAResult()

    # Scale features
    scaler = StandardScaler()
    X = scaler.fit_transform(numeric_df)

    # Sample for large datasets
    if len(X) > 10000:
        indices = np.random.choice(len(X), 10000, replace=False)
        X = X[indices]

    # Determine number of components
    n_components = min(X.shape[1], X.shape[0], 10)
    n_display = min(n_components, 3)  # For visualization

    try:
        pca = PCA(n_components=n_components)
        transformed = pca.fit_transform(X)

        explained = pca.explained_variance_ratio_.tolist()
        total_explained = float(sum(explained[:n_display]))

        # Project to 2D/3D for visualization
        projected = transformed[:, :n_display].tolist()

        components = pca.components_[:n_display].tolist()

        return PCAResult(
            n_components=n_components,
            explained_variance=[round(v, 4) for v in explained],
            total_variance_explained=round(total_explained, 4),
            components=components,
            projected_data=projected,
        )

    except Exception as e:
        print(f"PCA error: {e}")
        return PCAResult()
