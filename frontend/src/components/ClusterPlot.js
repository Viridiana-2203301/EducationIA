/**
 * ClusterPlot - Gráficos de clustering y PCA, simplificados para interpretación.
 */
import dynamic from 'next/dynamic';
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

const CLUSTER_COLORS = [
  '#3b82f6', '#f59e0b', '#10b981', '#f43f5e', '#8b5cf6',
  '#06b6d4', '#ec4899', '#14b8a6', '#6366f1', '#a855f7',
];

export default function ClusterPlot({ clusters, pca }) {
  const hasCluster = clusters && clusters.length > 0;
  const hasPCA = pca && pca.projected_data && pca.projected_data.length > 0;

  if (!hasCluster && !hasPCA) {
    return <div className="empty-state"><p>No hay datos de clustering</p></div>;
  }

  return (
    <div>
      {/* PCA Scatter - con explicación */}
      {hasPCA && (
        <div style={{ marginBottom: '1.5rem' }}>
          <div className="chart-title">
            🎯 Análisis de Componentes Principales (PCA)
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0.25rem 0 0.75rem' }}>
            Cada punto representa un registro. Puntos cercanos = registros similares. Los ejes representan las dos
            combinaciones de variables que mejor separan los datos.
          </p>
          <Plot
            data={[{
              type: 'scatter',
              mode: 'markers',
              x: pca.projected_data.map(p => p[0]),
              y: pca.projected_data.map(p => p[1] || 0),
              marker: {
                color: hasCluster ? clusters[0].labels : '#3b82f6',
                colorscale: hasCluster ? 'Portland' : undefined,
                size: 6,
                opacity: 0.65,
                line: { color: 'rgba(255,255,255,0.15)', width: 0.5 },
              },
              hovertemplate: 'Componente 1: %{x:.2f}<br>Componente 2: %{y:.2f}<extra></extra>',
            }]}
            layout={{
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(17,24,39,0.5)',
              font: { color: '#94a3b8', family: 'Inter' },
              xaxis: {
                title: { text: `Componente 1 (${(pca.explained_variance[0] * 100).toFixed(1)}% de información)`, font: { size: 12 } },
                gridcolor: 'rgba(255,255,255,0.05)',
                zerolinecolor: 'rgba(255,255,255,0.1)',
              },
              yaxis: {
                title: { text: `Componente 2 (${(pca.explained_variance[1] * 100).toFixed(1)}% de información)`, font: { size: 12 } },
                gridcolor: 'rgba(255,255,255,0.05)',
                zerolinecolor: 'rgba(255,255,255,0.1)',
              },
              margin: { l: 70, r: 20, t: 10, b: 60 },
              height: 420,
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem', textAlign: 'center' }}>
            Varianza total explicada: <strong>{(pca.total_variance_explained * 100).toFixed(1)}%</strong> de la información original
          </p>
        </div>
      )}

      {/* Cluster distribution - con explicación */}
      {hasCluster && clusters.map((cluster, idx) => (
        <div key={idx} style={{ marginBottom: '1.5rem' }}>
          <div className="chart-title">
            📊 Grupos de Datos ({cluster.method === 'kmeans' ? 'K-Means' : cluster.method.toUpperCase()})
            {cluster.silhouette_score != null && (
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                Calidad: {(cluster.silhouette_score * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0.25rem 0 0.75rem' }}>
            El algoritmo agrupó los registros en {cluster.n_clusters} grupos según sus similitudes.
            Barras más altas = grupos con más registros.
          </p>
          <Plot
            data={[{
              type: 'bar',
              x: Object.keys(cluster.cluster_sizes).map(k => `Grupo ${parseInt(k) + 1}`),
              y: Object.values(cluster.cluster_sizes),
              text: Object.values(cluster.cluster_sizes).map(v => `${v.toLocaleString()} registros`),
              textposition: 'auto',
              textfont: { color: '#fff', size: 11 },
              marker: {
                color: Object.keys(cluster.cluster_sizes).map((_, i) =>
                  CLUSTER_COLORS[i % CLUSTER_COLORS.length]
                ),
                line: { width: 0 },
              },
              hovertemplate: '%{x}: %{y:,} registros<extra></extra>',
            }]}
            layout={{
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(17,24,39,0.5)',
              font: { color: '#94a3b8', family: 'Inter' },
              xaxis: {
                title: { text: 'Grupo', font: { size: 12 } },
                gridcolor: 'rgba(255,255,255,0.05)',
              },
              yaxis: {
                title: { text: 'Cantidad de registros', font: { size: 12 } },
                gridcolor: 'rgba(255,255,255,0.05)',
              },
              margin: { l: 70, r: 20, t: 10, b: 50 },
              height: 320,
              bargap: 0.3,
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
        </div>
      ))}
    </div>
  );
}
