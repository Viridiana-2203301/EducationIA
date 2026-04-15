/**
 * DatasetCard - Card showing profiling summary for one dataset.
 */
export default function DatasetCard({ dataset }) {
  const statusClasses = {
    uploaded: 'status-uploaded',
    profiled: 'status-profiled',
    cleaned: 'status-cleaned',
    analyzed: 'status-analyzed',
    error: 'status-error',
  };

  const statusLabels = {
    uploaded: 'Cargado',
    profiled: 'Perfilado',
    cleaned: 'Limpio',
    analyzed: 'Analizado',
    error: 'Error',
  };

  const formatNumber = (n) => {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return String(n);
  };

  return (
    <div className="glass-card dataset-card">
      <div className="dataset-card-header">
        <h3 className="dataset-card-title" title={dataset.filename}>
          📄 {dataset.filename}
        </h3>
        <span className={`dataset-status ${statusClasses[dataset.status]}`}>
          {statusLabels[dataset.status] || dataset.status}
        </span>
      </div>

      <div className="dataset-stats">
        <div className="stat-item">
          <div className="stat-label">Filas</div>
          <div className="stat-value">{formatNumber(dataset.row_count)}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Columnas</div>
          <div className="stat-value">{dataset.column_count}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Tamaño</div>
          <div className="stat-value">{dataset.file_size_mb?.toFixed(1)} MB</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Estado</div>
          <div className="stat-value" style={{ fontSize: '0.9rem' }}>
            {statusLabels[dataset.status]}
          </div>
        </div>
      </div>

      {dataset.profile && (
        <div style={{ marginTop: '1rem' }}>
          <div className="dataset-stats">
            <div className="stat-item">
              <div className="stat-label">Nulos</div>
              <div className="stat-value">{formatNumber(dataset.profile.total_nulls)}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Duplicados</div>
              <div className="stat-value">{formatNumber(dataset.profile.duplicate_rows)}</div>
            </div>
          </div>
        </div>
      )}

      {dataset.cleaning_stats && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.5rem 0.75rem',
          background: 'rgba(16, 185, 129, 0.1)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.75rem',
          color: 'var(--accent-emerald)',
        }}>
          ✅ Limpieza: {dataset.cleaning_stats.duplicates_removed} dup. eliminados,{' '}
          {dataset.cleaning_stats.nulls_filled} nulos imputados
        </div>
      )}
    </div>
  );
}
