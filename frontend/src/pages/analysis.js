/**
 * Analysis Page - Dashboard with all visualizations and insights.
 * Shows correlation heatmaps, clusters, anomalies, trends, graph, and insights.
 */
import { useEffect } from 'react';
import { useAnalysis } from '../hooks/useAnalysis';
import CorrelationHeatmap from '../components/CorrelationHeatmap';
import ClusterPlot from '../components/ClusterPlot';
import AnomalyChart from '../components/AnomalyChart';
import TrendChart from '../components/TrendChart';
import RelationshipGraph from '../components/RelationshipGraph';
import InsightsPanel from '../components/InsightsPanel';
import LoadingSpinner from '../components/LoadingSpinner';

export default function AnalysisPage() {
  const {
    loading, error, results, graph, insights,
    executeAnalysis, fetchLatest,
  } = useAnalysis();

  useEffect(() => {
    fetchLatest();
  }, [fetchLatest]);

  if (loading && !results) {
    return <LoadingSpinner text="Cargando resultados del análisis..." />;
  }

  if (!results) {
    return (
      <div>
        <div className="section-header">
          <h1 className="section-title">Dashboard de Análisis</h1>
          <p className="section-subtitle">
            No hay resultados disponibles. Ejecuta el análisis desde la página de datasets.
          </p>
        </div>
        <div className="empty-state" style={{ marginTop: '2rem' }}>
          <span className="empty-state-icon">🔬</span>
          <p className="empty-state-title">Sin análisis ejecutados</p>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Carga datasets y ejecuta el pipeline de análisis
          </p>
          <button className="btn btn-primary" onClick={() => executeAnalysis()}>
            🚀 Ejecutar Análisis
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="section-header">
          <h1 className="section-title">Dashboard de Análisis</h1>
        </div>
        <div className="error-banner">❌ {error}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Dashboard de Análisis</h1>
        <p className="section-subtitle">
          Estado: {results.status} • Datasets fusionados: {results.fused_datasets?.length || 0}
          {results.completed_at && (
            <span> • Completado: {new Date(results.completed_at).toLocaleString()}</span>
          )}
        </p>
      </div>

      {/* Action bar */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '0.75rem' }}>
        <button className="btn btn-primary" onClick={() => executeAnalysis()} disabled={loading}>
          {loading ? '⏳ Ejecutando...' : '🔄 Re-ejecutar Análisis'}
        </button>
      </div>

      {/* Relationship Graph - Full Width */}
      {graph && graph.nodes && graph.nodes.length > 0 && (
        <div style={{ marginBottom: '1.5rem' }}>
          <RelationshipGraph graph={graph} />
        </div>
      )}

      {/* Dashboard Grid */}
      <div className="dashboard-grid">

        {/* Insights Panel */}
        <div className="glass-card full-width">
          <div className="chart-title">💡 Insights Automáticos</div>
          <InsightsPanel insights={insights} />
        </div>

        {/* Correlation Heatmaps */}
        {results.correlations && results.correlations.length > 0 && (
          <div className="glass-card">
            <CorrelationHeatmap correlations={results.correlations} />
          </div>
        )}

        {/* Clusters + PCA */}
        {(results.clusters?.length > 0 || results.pca?.n_components > 0) && (
          <div className="glass-card">
            <ClusterPlot clusters={results.clusters} pca={results.pca} />
          </div>
        )}

        {/* Anomalies */}
        {results.anomalies && results.anomalies.length > 0 && (
          <div className="glass-card">
            <AnomalyChart anomalies={results.anomalies} />
          </div>
        )}

        {/* Trends */}
        {results.trends && results.trends.length > 0 && (
          <div className="glass-card">
            <TrendChart trends={results.trends} />
          </div>
        )}
      </div>
    </div>
  );
}
