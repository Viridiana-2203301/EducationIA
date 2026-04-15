"""
Analysis Pipeline Orchestrator.
Executes the full pipeline: load → profile → clean → match → graph → fuse → analyze → insights.
"""

import uuid
from datetime import datetime
from typing import Optional
from app.services.storage import storage
from app.services.profiler import profile_dataset
from app.services.cleaner import clean_dataset
from app.services.matcher import find_relationships
from app.services.graph_builder import build_relationship_graph
from app.services.fusion import auto_fuse_datasets
from app.services.insight_generator import generate_insights
from app.analysis.correlation import compute_correlations
from app.analysis.clustering import compute_clustering
from app.analysis.dimensionality import compute_pca
from app.analysis.anomalies import detect_anomalies
from app.analysis.trends import analyze_trends
from app.schemas.schemas import (
    AnalysisResults, AnalysisRequest, DatasetStatus,
)
import pandas as pd


def run_full_pipeline(request: Optional[AnalysisRequest] = None) -> AnalysisResults:
    """
    Execute the complete analysis pipeline on all loaded datasets.
    Pipeline steps:
    1. Profile datasets
    2. Clean/normalize data
    3. Find relationships
    4. Build graph
    5. Fuse datasets
    6. Run ML analysis
    7. Generate insights
    """
    analysis_id = str(uuid.uuid4())[:8]
    results = AnalysisResults(
        id=analysis_id,
        status="running",
        started_at=datetime.utcnow(),
    )

    if request is None:
        request = AnalysisRequest()

    try:
        datasets = storage.get_all_datasets()
        if not datasets:
            results.status = "error"
            results.error = "No hay datasets cargados"
            return results

        # --- Step 1 & 2: Profile and Clean ---
        for ds_info in datasets:
            df = storage.get_dataframe(ds_info.id)
            if df is None:
                continue

            # Profile
            profile = profile_dataset(df, ds_info.id, ds_info.filename)
            storage.store_profile(ds_info.id, profile)
            ds_info.profile = profile
            ds_info.status = DatasetStatus.PROFILED
            storage.store_dataset_info(ds_info.id, ds_info)

            # Clean
            cleaned_df, cleaning_stats = clean_dataset(df.copy(), ds_info.id, ds_info.filename)
            storage.store_cleaned_dataframe(ds_info.id, cleaned_df)
            storage.store_cleaning_stats(ds_info.id, cleaning_stats)
            ds_info.cleaning_stats = cleaning_stats
            ds_info.status = DatasetStatus.CLEANED
            storage.store_dataset_info(ds_info.id, ds_info)

        # --- Step 3: Find Relationships ---
        cleaned_dfs = {}
        ds_names = {}
        for ds_info in datasets:
            cdf = storage.get_best_dataframe(ds_info.id)
            if cdf is not None:
                cleaned_dfs[ds_info.id] = cdf
                ds_names[ds_info.id] = ds_info.filename.replace(".csv", "")

        relationships = find_relationships(cleaned_dfs, ds_names)
        storage.store_relationships(relationships)

        # --- Step 4: Build Graph ---
        ds_info_map = {ds.id: ds for ds in datasets}
        graph = build_relationship_graph(ds_info_map, relationships)
        storage.store_graph(graph)

        # --- Step 5: Fuse Datasets ---
        from app.services.fusion import auto_concat_datasets, auto_fuse_datasets, reduce_fused_dimensions
        
        # 5a. Concatenate datasets with matching headers
        fused_dfs = auto_concat_datasets(cleaned_dfs, ds_names)
        
        # 5b. Relational fusion for remaining relationships
        relational_dfs = auto_fuse_datasets(cleaned_dfs, relationships, ds_names)
        fused_dfs.update(relational_dfs)
        
        # 5c. Reducir dimensiones con PCA
        pca_dfs = reduce_fused_dimensions(fused_dfs)
        fused_dfs.update(pca_dfs)
        
        for key, fused_df in fused_dfs.items():
            storage.store_fused_dataframe(key, fused_df)
        results.fused_datasets = list(fused_dfs.keys())

        # --- Step 6: ML Analysis ---
        # Choose the best dataframe for analysis
        analysis_df = _select_analysis_dataframe(cleaned_dfs, fused_dfs)

        if analysis_df is not None and len(analysis_df) > 0:
            # Correlation
            if request.run_correlation:
                results.correlations = compute_correlations(analysis_df)

            # Clustering
            if request.run_clustering:
                results.clusters = compute_clustering(analysis_df)

            # PCA
            if request.run_pca:
                results.pca = compute_pca(analysis_df)

            # Anomaly Detection
            if request.run_anomaly_detection:
                results.anomalies = detect_anomalies(analysis_df)

            # Trend Analysis
            if request.run_trend_analysis:
                results.trends = analyze_trends(analysis_df)

        # --- Step 7: Generate Insights ---
        profiles = storage.get_all_profiles()
        results.insights = generate_insights(results, profiles)
        storage.store_insights(results.insights)

        results.status = "completed"
        results.completed_at = datetime.utcnow()

    except Exception as e:
        results.status = "error"
        results.error = str(e)
        import traceback
        traceback.print_exc()

    storage.store_analysis_results(analysis_id, results)
    return results


def _select_analysis_dataframe(
    cleaned_dfs: dict,
    fused_dfs: dict,
) -> Optional[pd.DataFrame]:
    """
    Select the best dataframe for ML analysis.
    Prefers fused datasets (more columns) over individual ones.
    """
    # Try the largest fused dataset first
    if fused_dfs:
        best_fused = max(fused_dfs.values(), key=lambda df: df.shape[1])
        if len(best_fused) > 5:
            return best_fused

    # Fall back to the largest individual dataset
    if cleaned_dfs:
        best_single = max(cleaned_dfs.values(), key=lambda df: df.shape[0] * df.shape[1])
        return best_single

    return None
