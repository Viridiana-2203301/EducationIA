/**
 * TrendChart - Gráficos de tendencias simplificados y explicados.
 */
import dynamic from 'next/dynamic';
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

const TREND_COLORS = {
  creciente: '#10b981',
  decreciente: '#f43f5e',
  estable: '#94a3b8',
  'cíclico': '#8b5cf6',
  increasing: '#10b981',
  decreasing: '#f43f5e',
  stable: '#94a3b8',
  cyclical: '#8b5cf6',
};

const DIRECTION_LABELS = {
  creciente: '📈 Tendencia Creciente',
  decreciente: '📉 Tendencia Decreciente',
  estable: '➡️ Tendencia Estable',
  'cíclico': '🔄 Tendencia Cíclica',
  increasing: '📈 Tendencia Creciente',
  decreasing: '📉 Tendencia Decreciente',
  stable: '➡️ Tendencia Estable',
  cyclical: '🔄 Tendencia Cíclica',
};

const DIRECTION_DESCRIPTIONS = {
  creciente: 'Los valores tienden a subir con el tiempo',
  decreciente: 'Los valores tienden a bajar con el tiempo',
  estable: 'Los valores se mantienen relativamente constantes',
  'cíclico': 'Los valores suben y bajan de forma periódica',
  increasing: 'Los valores tienden a subir con el tiempo',
  decreasing: 'Los valores tienden a bajar con el tiempo',
  stable: 'Los valores se mantienen relativamente constantes',
  cyclical: 'Los valores suben y bajan de forma periódica',
};

export default function TrendChart({ trends }) {
  if (!trends || trends.length === 0) {
    return <div className="empty-state"><p>No hay datos de tendencias</p></div>;
  }

  return (
    <div>
      <div className="chart-title" style={{ marginBottom: '0.5rem' }}>
        📈 Análisis de Tendencias
      </div>
      <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0 0 1rem' }}>
        Se analizaron las variables numéricas para detectar si aumentan, disminuyen o se mantienen estables.
      </p>

      {trends.slice(0, 6).map((trend, idx) => {
        if (!trend.data_points || trend.data_points.length === 0) return null;

        const color = TREND_COLORS[trend.direction] || '#3b82f6';
        const label = DIRECTION_LABELS[trend.direction] || trend.direction;
        const description = DIRECTION_DESCRIPTIONS[trend.direction] || '';

        // Acortar nombre de columna
        const colName = trend.column.length > 30
          ? trend.column.substring(0, 28) + '…'
          : trend.column;

        return (
          <div key={idx} style={{ marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-primary)', fontWeight: '600' }}>
                {label} — {colName}
              </span>
              <span style={{
                fontSize: '0.75rem',
                padding: '0.2rem 0.5rem',
                borderRadius: '4px',
                background: 'var(--bg-tertiary)',
                color: color,
              }}>
                Confianza: {(trend.strength * 100).toFixed(0)}%
              </span>
            </div>
            <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: '0 0 0.5rem' }}>
              {description}
            </p>

            <Plot
              data={[{
                type: 'scatter',
                mode: 'lines+markers',
                x: trend.data_points.map(p => p.x),
                y: trend.data_points.map(p => p.y),
                line: { color, width: 2.5, shape: 'spline' },
                marker: { color, size: 5 },
                fill: 'tozeroy',
                fillcolor: `${color}1A`,
                hovertemplate: '%{x}<br>Valor: %{y:,.2f}<extra></extra>',
              }]}
              layout={{
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(17,24,39,0.5)',
                font: { color: '#94a3b8', family: 'Inter' },
                xaxis: {
                  gridcolor: 'rgba(255,255,255,0.05)',
                  tickangle: -30,
                  tickfont: { size: 10 },
                },
                yaxis: {
                  title: { text: colName, font: { size: 10 } },
                  gridcolor: 'rgba(255,255,255,0.05)',
                  tickfont: { size: 10 },
                },
                margin: { l: 70, r: 20, t: 10, b: 60 },
                height: 260,
                showlegend: false,
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%' }}
            />
          </div>
        );
      })}
    </div>
  );
}
