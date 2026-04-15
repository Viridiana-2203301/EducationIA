/**
 * AnomalyChart - Gráfico de anomalías simplificado y explicado.
 */
import dynamic from 'next/dynamic';
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export default function AnomalyChart({ anomalies }) {
  if (!anomalies || anomalies.length === 0) {
    return <div className="empty-state"><p>No hay datos de anomalías</p></div>;
  }

  return (
    <div>
      {anomalies.map((anomaly, idx) => {
        const methodName = anomaly.method === 'isolation_forest'
          ? 'Isolation Forest' : 'Factor de Outlier Local';

        return (
          <div key={idx} style={{ marginBottom: '1.5rem' }}>
            <div className="chart-title">
              ⚠️ Detección de Datos Atípicos
              <span className="chart-badge badge-anomaly">
                {anomaly.n_anomalies} encontrados ({anomaly.anomaly_percentage}%)
              </span>
            </div>

            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0.25rem 0 0.75rem' }}>
              Se identificaron <strong>{anomaly.n_anomalies}</strong> registros que se comportan distinto al resto
              ({anomaly.anomaly_percentage}% del total). Método: {methodName}.
            </p>

            {/* Summary stats */}
            <div className="dataset-stats" style={{ marginBottom: '1rem' }}>
              <div className="stat-item">
                <div className="stat-label">Datos atípicos</div>
                <div className="stat-value" style={{ color: 'var(--accent-rose)' }}>
                  {anomaly.n_anomalies}
                </div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Porcentaje</div>
                <div className="stat-value">{anomaly.anomaly_percentage}%</div>
              </div>
              <div className="stat-item">
                <div className="stat-label">Interpretación</div>
                <div className="stat-value" style={{ fontSize: '0.85rem' }}>
                  {anomaly.anomaly_percentage < 5 ? '✅ Normal' :
                   anomaly.anomaly_percentage < 15 ? '⚠️ Revisar' : '🔴 Alto'}
                </div>
              </div>
            </div>

            {/* Anomaly scores distribution */}
            {anomaly.anomaly_scores && anomaly.anomaly_scores.length > 0 && (
              <Plot
                data={[{
                  type: 'histogram',
                  x: anomaly.anomaly_scores,
                  marker: {
                    color: 'rgba(244, 63, 94, 0.6)',
                    line: { color: '#f43f5e', width: 1 },
                  },
                  hovertemplate: 'Puntuación: %{x:.3f}<br>Frecuencia: %{y}<extra></extra>',
                }]}
                layout={{
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(17,24,39,0.5)',
                  font: { color: '#94a3b8', family: 'Inter' },
                  xaxis: {
                    title: { text: 'Puntuación de anomalía (más bajo = más atípico)', font: { size: 11 } },
                    gridcolor: 'rgba(255,255,255,0.05)',
                  },
                  yaxis: {
                    title: { text: 'Cantidad de registros', font: { size: 11 } },
                    gridcolor: 'rgba(255,255,255,0.05)',
                  },
                  margin: { l: 70, r: 20, t: 10, b: 60 },
                  height: 300,
                  bargap: 0.05,
                }}
                config={{ displayModeBar: false, responsive: true }}
                style={{ width: '100%' }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
