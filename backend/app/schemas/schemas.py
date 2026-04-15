"""
Pydantic schemas for API requests and responses.
Defines data contracts for datasets, profiling, analysis results, and insights.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class DatasetStatus(str, Enum):
    UPLOADED = "uploaded"
    PROFILED = "profiled"
    CLEANED = "cleaned"
    ANALYZED = "analyzed"
    ERROR = "error"


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    sample_values: List[Any] = []
    is_numeric: bool = False
    is_categorical: bool = False
    is_datetime: bool = False
    mean: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[Any] = None
    max_val: Optional[Any] = None
    median: Optional[float] = None


class DatasetProfile(BaseModel):
    dataset_id: str
    filename: str
    row_count: int
    column_count: int
    duplicate_rows: int = 0
    total_nulls: int = 0
    columns: List[ColumnProfile] = []
    memory_usage_mb: float = 0.0
    encoding: str = "utf-8"


class CleaningStats(BaseModel):
    dataset_id: str
    rows_before: int
    rows_after: int
    duplicates_removed: int = 0
    nulls_filled: int = 0
    nulls_dropped: int = 0
    types_corrected: int = 0
    columns_normalized: List[str] = []


class DatasetInfo(BaseModel):
    id: str
    filename: str
    status: DatasetStatus = DatasetStatus.UPLOADED
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    row_count: int = 0
    column_count: int = 0
    file_size_mb: float = 0.0
    profile: Optional[DatasetProfile] = None
    cleaning_stats: Optional[CleaningStats] = None


class RelationshipType(str, Enum):
    COLUMN_NAME_MATCH = "column_name_match"
    SEMANTIC_MATCH = "semantic_match"
    VALUE_OVERLAP = "value_overlap"
    TYPE_MATCH = "type_match"


class DatasetRelationship(BaseModel):
    source_dataset: str
    target_dataset: str
    source_column: str
    target_column: str
    relationship_type: RelationshipType
    confidence: float = 0.0
    shared_values_count: int = 0
    suggested_key_type: str = ""  # "primary", "foreign"


class GraphNode(BaseModel):
    id: str
    label: str
    row_count: int = 0
    column_count: int = 0


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = ""
    confidence: float = 0.0
    relationship_type: str = ""


class RelationshipGraph(BaseModel):
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []


class CorrelationResult(BaseModel):
    method: str  # "pearson" or "spearman"
    matrix: Dict[str, Dict[str, float]] = {}
    strong_correlations: List[Dict[str, Any]] = []


class ClusterResult(BaseModel):
    method: str  # "kmeans" or "dbscan"
    n_clusters: int = 0
    labels: List[int] = []
    cluster_centers: Optional[List[List[float]]] = None
    cluster_sizes: Dict[str, int] = {}
    silhouette_score: Optional[float] = None


class PCAResult(BaseModel):
    n_components: int = 0
    explained_variance: List[float] = []
    total_variance_explained: float = 0.0
    components: List[List[float]] = []
    projected_data: List[List[float]] = []


class AnomalyResult(BaseModel):
    method: str  # "isolation_forest" or "lof"
    n_anomalies: int = 0
    anomaly_indices: List[int] = []
    anomaly_scores: List[float] = []
    anomaly_percentage: float = 0.0


class TrendResult(BaseModel):
    column: str = ""
    direction: str = ""  # "increasing", "decreasing", "stable", "cyclical"
    strength: float = 0.0
    period: Optional[str] = None
    data_points: List[Dict[str, Any]] = []


class Insight(BaseModel):
    id: str
    category: str  # "correlation", "cluster", "anomaly", "trend", "pattern"
    severity: str = "info"  # "info", "warning", "critical"
    title: str
    description: str
    related_datasets: List[str] = []
    related_columns: List[str] = []
    evidence: Dict[str, Any] = {}


class AnalysisResults(BaseModel):
    id: str
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    correlations: List[CorrelationResult] = []
    clusters: List[ClusterResult] = []
    pca: Optional[PCAResult] = None
    anomalies: List[AnomalyResult] = []
    trends: List[TrendResult] = []
    insights: List[Insight] = []
    fused_datasets: List[str] = []
    error: Optional[str] = None


class AnalysisRequest(BaseModel):
    dataset_ids: Optional[List[str]] = None  # None = all datasets
    run_correlation: bool = True
    run_clustering: bool = True
    run_pca: bool = True
    run_anomaly_detection: bool = True
    run_trend_analysis: bool = True


class UploadResponse(BaseModel):
    message: str
    datasets: List[DatasetInfo] = []
    errors: List[str] = []
