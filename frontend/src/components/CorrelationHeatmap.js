/**
 * CorrelationHeatmap - Mapa de calor de correlaciones.
 * Más legible: solo muestra las 15 correlaciones más fuertes si hay muchas columnas.
 */
import dynamic from 'next/dynamic';
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export default function CorrelationHeatmap({ correlations }) {
  if (!correlations || correlations.length === 0) {
    return <div className="empty-state"><p>No hay datos de correlación</p></div>;
  }

  return (
    <div>
      {correlations.map((corr, idx) => {
        let columns = Object.keys(corr.matrix);
        if (columns.length === 0) return null;

        // Si hay demasiadas columnas, quedarnos con las top 15 que tengan mayor correlación
        if (columns.length > 15) {
          const avgCorr = {};
          columns.forEach(col => {
            const vals = columns.map(row => Math.abs(corr.matrix[col]?.[row] || 0));
            avgCorr[col] = vals.reduce((a, b) => a + b, 0) / vals.length;
          });
          columns = columns.sort((a, b) => avgCorr[b] - avgCorr[a]).slice(0, 15);
        }

        // Acortar nombres largos de columnas
        const shortNames = columns.map(c =>
          c.length > 20 ? c.substring(0, 18) + '…' : c
        );

        const z = columns.map(row =>
          columns.map(col => {
            const val = corr.matrix[col]?.[row] || 0;
            return Math.round(val * 100) / 100;
          })
        );

        // Construir texto de anotaciones
        const annotations = [];
        for (let i = 0; i < columns.length; i++) {
          for (let j = 0; j < columns.length; j++) {
            const val = z[i][j];
            if (Math.abs(val) >= 0.5) {
              annotations.push({
                x: shortNames[j],
                y: shortNames[i],
                text: val.toFixed(2),
                font: { color: Math.abs(val) > 0.7 ? '#fff' : '#cbd5e1', size: 9 },
                showarrow: false,
              });
            }
          }
        }

        return (
          <div key={idx} style={{ marginBottom: '1rem' }}>
            <div className="chart-title">
              🔥 Mapa de Correlación ({corr.method})
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                Top {columns.length} variables más correlacionadas
              </span>
            </div>

            {/* Leyenda explicativa */}
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0.25rem 0 0.75rem' }}>
              🟡 Cercano a 1 = Correlación positiva fuerte • 🔵 Cercano a -1 = Correlación negativa fuerte • ⚫ Cercano a 0 = Sin correlación
            </p>

            <Plot
              data={[{
                type: 'heatmap',
                z: z,
                x: shortNames,
                y: shortNames,
                colorscale: [
                  [0, '#1e3a5f'],
                  [0.25, '#2563eb'],
                  [0.5, '#1e293b'],
                  [0.75, '#ea580c'],
                  [1, '#fbbf24'],
                ],
                zmin: -1,
                zmax: 1,
                hoverongaps: false,
                showscale: true,
                hovertemplate: '%{x} vs %{y}<br>Correlación: %{z:.2f}<extra></extra>',
                colorbar: {
                  tickfont: { color: '#94a3b8', size: 11 },
                  title: { text: 'Coef. r', font: { color: '#94a3b8', size: 12 } },
                  tickvals: [-1, -0.5, 0, 0.5, 1],
                  ticktext: ['-1 (inversa)', '-0.5', '0 (nula)', '0.5', '1 (directa)'],
                },
              }]}
              layout={{
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: '#94a3b8', family: 'Inter', size: 10 },
                margin: { l: 120, r: 60, t: 10, b: 120 },
                xaxis: { tickangle: -45, tickfont: { size: 10 } },
                yaxis: { tickfont: { size: 10 } },
                height: 500,
                annotations: annotations,
              }}
              config={{ displayModeBar: false, responsive: true }}
              style={{ width: '100%' }}
            />

            {/* Correlaciones fuertes */}
            {corr.strong_correlations && corr.strong_correlations.length > 0 && (
              <div style={{ marginTop: '0.75rem' }}>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                  🎯 Correlaciones más fuertes encontradas:
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {corr.strong_correlations.slice(0, 8).map((sc, i) => (
                    <span key={i} style={{
                      background: 'var(--bg-tertiary)',
                      padding: '0.3rem 0.6rem',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      color: sc.correlation > 0 ? '#fbbf24' : '#3b82f6',
                    }}>
                      {sc.col1} ↔ {sc.col2}: <strong>{sc.correlation?.toFixed(2)}</strong>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
