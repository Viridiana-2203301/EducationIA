/**
 * InsightsPanel - Displays natural-language insights with severity indicators.
 */
export default function InsightsPanel({ insights }) {
  if (!insights || insights.length === 0) {
    return (
      <div className="empty-state">
        <span className="empty-state-icon">💡</span>
        <p className="empty-state-title">Sin insights todavía</p>
        <p style={{ color: 'var(--text-muted)' }}>
          Ejecuta el análisis para descubrir patrones en tus datos
        </p>
      </div>
    );
  }

  const categoryIcons = {
    correlation: '🔗',
    cluster: '🎯',
    anomaly: '⚠️',
    trend: '📈',
    pattern: '🔍',
  };

  const severityLabels = {
    critical: '🔴 Crítico',
    warning: '🟡 Atención',
    info: '🔵 Info',
  };

  return (
    <div>
      <div style={{
        display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap',
      }}>
        <span style={{
          padding: '4px 12px',
          borderRadius: '12px',
          background: 'var(--bg-glass)',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)',
        }}>
          {insights.length} insight(s) encontrados
        </span>
      </div>

      <div className="insights-list">
        {insights.map((insight, idx) => (
          <div key={idx} className={`insight-item severity-${insight.severity}`}>
            <div className="insight-title">
              {categoryIcons[insight.category] || '📊'}{' '}
              {insight.title}
            </div>
            <p className="insight-description">{insight.description}</p>
            <div className="insight-tags">
              <span className="insight-tag">
                {severityLabels[insight.severity] || insight.severity}
              </span>
              <span className="insight-tag">{insight.category}</span>
              {insight.related_columns?.map((col, i) => (
                <span key={i} className="insight-tag">{col}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
