"""
Insight Generator Service.
Reads ML analysis results and generates natural-language insights.
Rule-based engine producing descriptions in Spanish.
"""

import uuid
from typing import List, Dict, Any
from app.schemas.schemas import (
    AnalysisResults, Insight, CorrelationResult, ClusterResult,
    AnomalyResult, TrendResult, PCAResult, DatasetProfile,
)


def generate_insights(
    analysis: AnalysisResults,
    profiles: Dict[str, DatasetProfile],
) -> List[Insight]:
    """Generate natural-language insights from analysis results."""
    insights: List[Insight] = []

    # Profile insights
    for ds_id, profile in profiles.items():
        insights.extend(_profile_insights(profile))

    # Correlation insights
    for corr in analysis.correlations:
        insights.extend(_correlation_insights(corr))

    # Cluster insights
    for cluster in analysis.clusters:
        insights.extend(_cluster_insights(cluster))

    # PCA insights
    if analysis.pca and analysis.pca.n_components > 0:
        insights.extend(_pca_insights(analysis.pca))

    # Anomaly insights
    for anomaly in analysis.anomalies:
        insights.extend(_anomaly_insights(anomaly))

    # Trend insights
    for trend in analysis.trends:
        insights.extend(_trend_insights(trend))

    # Sort by severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    insights.sort(key=lambda i: severity_order.get(i.severity, 2))

    return insights


def _profile_insights(profile: DatasetProfile) -> List[Insight]:
    """Generate insights from data profiling."""
    insights = []

    # Data quality alert
    null_pct = (profile.total_nulls / (profile.row_count * profile.column_count) * 100
                if profile.row_count * profile.column_count > 0 else 0)

    if null_pct > 10:
        insights.append(Insight(
            id=str(uuid.uuid4())[:8],
            category="pattern",
            severity="warning",
            title=f"Alta cantidad de valores nulos en {profile.filename}",
            description=(
                f"El dataset '{profile.filename}' tiene {profile.total_nulls} valores nulos "
                f"({null_pct:.1f}% del total). Esto podría afectar la calidad del análisis. "
                f"Se recomienda revisar las columnas con mayor porcentaje de datos faltantes."
            ),
            related_datasets=[profile.dataset_id],
        ))

    if profile.duplicate_rows > 0:
        dup_pct = profile.duplicate_rows / profile.row_count * 100
        if dup_pct > 5:
            insights.append(Insight(
                id=str(uuid.uuid4())[:8],
                category="pattern",
                severity="warning",
                title=f"Filas duplicadas detectadas en {profile.filename}",
                description=(
                    f"Se encontraron {profile.duplicate_rows} filas duplicadas "
                    f"({dup_pct:.1f}%) en '{profile.filename}'. "
                    f"Esto puede indicar datos redundantes que fueron limpiados durante el preprocesamiento."
                ),
                related_datasets=[profile.dataset_id],
            ))

    return insights


def _correlation_insights(corr: CorrelationResult) -> List[Insight]:
    """Generate insights from correlation analysis."""
    insights = []

    for item in corr.strong_correlations[:5]:
        col_a = item["column_a"]
        col_b = item["column_b"]
        value = item["value"]
        strength = item["strength"]
        direction = item["direction"]

        severity = "critical" if abs(value) > 0.8 else "info"

        insights.append(Insight(
            id=str(uuid.uuid4())[:8],
            category="correlation",
            severity=severity,
            title=f"Correlación {strength} entre {col_a} y {col_b}",
            description=(
                f"Se detectó una correlación {direction} {strength} ({corr.method}: r={value}) "
                f"entre '{col_a}' y '{col_b}'. "
                + (f"Esto sugiere que cuando '{col_a}' aumenta, '{col_b}' también tiende a aumentar."
                   if direction == "positiva" else
                   f"Esto sugiere que cuando '{col_a}' aumenta, '{col_b}' tiende a disminuir.")
            ),
            related_columns=[col_a, col_b],
            evidence={"method": corr.method, "value": value},
        ))

    return insights


def _cluster_insights(cluster: ClusterResult) -> List[Insight]:
    """Generate insights from clustering results."""
    insights = []

    if cluster.n_clusters < 2:
        return insights

    total = sum(cluster.cluster_sizes.values())

    size_descriptions = []
    for name, count in sorted(cluster.cluster_sizes.items(), key=lambda x: -x[1]):
        pct = count / total * 100 if total > 0 else 0
        size_descriptions.append(f"{name}: {count} registros ({pct:.1f}%)")

    sil_text = ""
    if cluster.silhouette_score is not None:
        quality = "excelente" if cluster.silhouette_score > 0.5 else (
            "buena" if cluster.silhouette_score > 0.3 else "moderada"
        )
        sil_text = f" La calidad de separación es {quality} (silhouette: {cluster.silhouette_score})."

    insights.append(Insight(
        id=str(uuid.uuid4())[:8],
        category="cluster",
        severity="info",
        title=f"Se identificaron {cluster.n_clusters} segmentos ({cluster.method.upper()})",
        description=(
            f"El algoritmo {cluster.method.upper()} encontró {cluster.n_clusters} grupos distintos "
            f"en los datos.{sil_text}\n\nDistribución: " + "; ".join(size_descriptions)
        ),
        evidence={"method": cluster.method, "n_clusters": cluster.n_clusters},
    ))

    return insights


def _pca_insights(pca: PCAResult) -> List[Insight]:
    """Generate insights from PCA results."""
    insights = []

    if len(pca.explained_variance) == 0:
        return insights

    top_2 = sum(pca.explained_variance[:2]) * 100
    top_3 = sum(pca.explained_variance[:min(3, len(pca.explained_variance))]) * 100

    insights.append(Insight(
        id=str(uuid.uuid4())[:8],
        category="pattern",
        severity="info",
        title="Reducción de dimensionalidad (PCA)",
        description=(
            f"Los primeros 2 componentes principales capturan el {top_2:.1f}% de la varianza "
            f"total de los datos. Los primeros 3 componentes capturan el {top_3:.1f}%. "
            + (f"Esto indica que los datos son altamente compresibles y tienen estructura subyacente clara."
               if top_2 > 70 else
               f"Los datos tienen una estructura dimensional compleja distribuida entre múltiples variables.")
        ),
        evidence={"explained_variance": pca.explained_variance[:5]},
    ))

    return insights


def _anomaly_insights(anomaly: AnomalyResult) -> List[Insight]:
    """Generate insights from anomaly detection."""
    insights = []

    if anomaly.n_anomalies == 0:
        return insights

    severity = "critical" if anomaly.anomaly_percentage > 5 else "warning"

    method_name = "Isolation Forest" if anomaly.method == "isolation_forest" else "Local Outlier Factor"

    insights.append(Insight(
        id=str(uuid.uuid4())[:8],
        category="anomaly",
        severity=severity,
        title=f"{anomaly.n_anomalies} anomalías detectadas ({method_name})",
        description=(
            f"El algoritmo {method_name} identificó {anomaly.n_anomalies} registros anómalos "
            f"({anomaly.anomaly_percentage}% del total). "
            f"Estos puntos de datos se desvían significativamente del patrón general. "
            f"Se recomienda investigar estos registros para determinar si representan errores "
            f"de datos o eventos legítimos inusuales."
        ),
        evidence={
            "method": anomaly.method,
            "count": anomaly.n_anomalies,
            "percentage": anomaly.anomaly_percentage,
        },
    ))

    return insights


def _trend_insights(trend: TrendResult) -> List[Insight]:
    """Generate insights from trend analysis."""
    insights = []

    if trend.direction == "estable":
        return insights

    direction_text = {
        "creciente": "una tendencia creciente (ascendente)",
        "decreciente": "una tendencia decreciente (descendente)",
        "cíclico": "un patrón cíclico (periódico)",
    }

    desc = direction_text.get(trend.direction, trend.direction)

    insights.append(Insight(
        id=str(uuid.uuid4())[:8],
        category="trend",
        severity="info",
        title=f"Tendencia {trend.direction} en '{trend.column}'",
        description=(
            f"La variable '{trend.column}' muestra {desc} "
            f"con una fuerza de R²={trend.strength}. "
            + (f"Esta tendencia es estadísticamente significativa y podría usarse para proyecciones."
               if trend.strength > 0.3 else
               f"La tendencia es débil y podría no ser confiable para predicciones.")
        ),
        related_columns=[trend.column],
        evidence={"direction": trend.direction, "strength": trend.strength},
    ))

    return insights
