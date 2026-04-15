"""
In-memory storage service.
Stores datasets, profiles, analysis results, and insights.
Can be replaced with PostgreSQL for production scaling.
"""

import pandas as pd
from typing import Dict, Optional, List
from app.schemas.schemas import (
    DatasetInfo, DatasetProfile, AnalysisResults,
    DatasetRelationship, RelationshipGraph, Insight, CleaningStats
)


class StorageService:
    """In-memory storage for the MVP. Thread-safe for single-process usage."""

    def __init__(self):
        self._dataframes: Dict[str, pd.DataFrame] = {}
        self._cleaned_dataframes: Dict[str, pd.DataFrame] = {}
        self._fused_dataframes: Dict[str, pd.DataFrame] = {}
        self._dataset_info: Dict[str, DatasetInfo] = {}
        self._profiles: Dict[str, DatasetProfile] = {}
        self._cleaning_stats: Dict[str, CleaningStats] = {}
        self._relationships: List[DatasetRelationship] = []
        self._graph: Optional[RelationshipGraph] = None
        self._analysis_results: Dict[str, AnalysisResults] = {}
        self._insights: List[Insight] = []

    # --- DataFrames ---
    def store_dataframe(self, dataset_id: str, df: pd.DataFrame):
        self._dataframes[dataset_id] = df

    def get_dataframe(self, dataset_id: str) -> Optional[pd.DataFrame]:
        return self._dataframes.get(dataset_id)

    def store_cleaned_dataframe(self, dataset_id: str, df: pd.DataFrame):
        self._cleaned_dataframes[dataset_id] = df

    def get_cleaned_dataframe(self, dataset_id: str) -> Optional[pd.DataFrame]:
        return self._cleaned_dataframes.get(dataset_id)

    def get_best_dataframe(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """Return cleaned df if available, otherwise raw."""
        cleaned = self._cleaned_dataframes.get(dataset_id)
        if cleaned is not None:
            return cleaned
        return self._dataframes.get(dataset_id)

    def store_fused_dataframe(self, key: str, df: pd.DataFrame):
        self._fused_dataframes[key] = df

    def get_fused_dataframe(self, key: str) -> Optional[pd.DataFrame]:
        return self._fused_dataframes.get(key)

    def get_all_fused_dataframes(self) -> Dict[str, pd.DataFrame]:
        return self._fused_dataframes

    # --- Dataset Info ---
    def store_dataset_info(self, dataset_id: str, info: DatasetInfo):
        self._dataset_info[dataset_id] = info

    def get_dataset_info(self, dataset_id: str) -> Optional[DatasetInfo]:
        return self._dataset_info.get(dataset_id)

    def get_all_datasets(self) -> List[DatasetInfo]:
        return list(self._dataset_info.values())

    # --- Profiles ---
    def store_profile(self, dataset_id: str, profile: DatasetProfile):
        self._profiles[dataset_id] = profile

    def get_profile(self, dataset_id: str) -> Optional[DatasetProfile]:
        return self._profiles.get(dataset_id)

    def get_all_profiles(self) -> Dict[str, DatasetProfile]:
        return self._profiles

    # --- Cleaning Stats ---
    def store_cleaning_stats(self, dataset_id: str, stats: CleaningStats):
        self._cleaning_stats[dataset_id] = stats

    def get_cleaning_stats(self, dataset_id: str) -> Optional[CleaningStats]:
        return self._cleaning_stats.get(dataset_id)

    # --- Relationships ---
    def store_relationships(self, relationships: List[DatasetRelationship]):
        self._relationships = relationships

    def get_relationships(self) -> List[DatasetRelationship]:
        return self._relationships

    # --- Graph ---
    def store_graph(self, graph: RelationshipGraph):
        self._graph = graph

    def get_graph(self) -> Optional[RelationshipGraph]:
        return self._graph

    # --- Analysis Results ---
    def store_analysis_results(self, analysis_id: str, results: AnalysisResults):
        self._analysis_results[analysis_id] = results

    def get_analysis_results(self, analysis_id: str) -> Optional[AnalysisResults]:
        return self._analysis_results.get(analysis_id)

    def get_latest_analysis(self) -> Optional[AnalysisResults]:
        if not self._analysis_results:
            return None
        return list(self._analysis_results.values())[-1]

    # --- Insights ---
    def store_insights(self, insights: List[Insight]):
        self._insights = insights

    def get_insights(self) -> List[Insight]:
        return self._insights

    # --- Reset ---
    def clear_all(self):
        self._dataframes.clear()
        self._cleaned_dataframes.clear()
        self._fused_dataframes.clear()
        self._dataset_info.clear()
        self._profiles.clear()
        self._cleaning_stats.clear()
        self._relationships.clear()
        self._graph = None
        self._analysis_results.clear()
        self._insights.clear()

    def get_dataset_count(self) -> int:
        return len(self._dataset_info)


# Singleton instance
storage = StorageService()
