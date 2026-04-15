/**
 * Fused Datasets Page - View and download concatenated/fused datasets.
 */
import { useState, useEffect } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';
import { getFusedDatasets, getFusedPreview, getFusedDownloadUrl } from '../services/api';

export default function FusedPage() {
  const [fusedList, setFusedList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedKey, setSelectedKey] = useState(null);
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    loadFused();
  }, []);

  const loadFused = async () => {
    try {
      const data = await getFusedDatasets();
      setFusedList(data);
    } catch (err) {
      console.error('Error loading fused datasets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (key) => {
    if (selectedKey === key) {
      setSelectedKey(null);
      setPreview(null);
      return;
    }
    setSelectedKey(key);
    setPreviewLoading(true);
    try {
      const data = await getFusedPreview(key, 50);
      setPreview(data);
    } catch (err) {
      console.error('Error loading preview:', err);
    } finally {
      setPreviewLoading(false);
    }
  };

  if (loading) return <LoadingSpinner text="Cargando datasets fusionados..." />;

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">📦 Datasets Fusionados</h1>
        <p className="section-subtitle">
          {fusedList.length > 0
            ? `${fusedList.length} dataset(s) fusionado(s) disponibles para descarga`
            : 'No hay datasets fusionados. Ejecuta el análisis primero.'}
        </p>
      </div>

      {fusedList.length === 0 ? (
        <div className="empty-state" style={{ marginTop: '3rem' }}>
          <span className="empty-state-icon">🔗</span>
          <p className="empty-state-title">Sin datasets fusionados</p>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Carga archivos CSV y ejecuta el análisis para generar datasets concatenados
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
          {fusedList.map((ds) => (
            <div key={ds.key} className="glass-card" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                  <h3 style={{ margin: 0, color: 'var(--text-primary)', fontSize: '1.1rem' }}>
                    📊 {ds.key}
                  </h3>
                  <p style={{ margin: '0.25rem 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    {ds.rows.toLocaleString()} filas • {ds.columns} columnas
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    className="btn btn-secondary"
                    onClick={() => handlePreview(ds.key)}
                    style={{ fontSize: '0.85rem' }}
                  >
                    {selectedKey === ds.key ? '🔼 Ocultar' : '👁️ Vista previa'}
                  </button>
                  <a
                    href={getFusedDownloadUrl(ds.key)}
                    className="btn btn-success"
                    style={{ fontSize: '0.85rem', textDecoration: 'none' }}
                    download
                  >
                    ⬇️ Descargar CSV
                  </a>
                </div>
              </div>

              {/* Column names */}
              <div style={{ marginTop: '0.75rem' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Columnas: </span>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  {ds.column_names.slice(0, 10).join(', ')}
                  {ds.column_names.length > 10 ? ` ... y ${ds.column_names.length - 10} más` : ''}
                </span>
              </div>

              {/* Preview Table */}
              {selectedKey === ds.key && (
                <div style={{ marginTop: '1rem' }}>
                  {previewLoading ? (
                    <LoadingSpinner text="Cargando vista previa..." />
                  ) : preview ? (
                    <div style={{ overflowX: 'auto', maxHeight: '400px', overflowY: 'auto', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                        <thead>
                          <tr>
                            {preview.columns.map((col) => (
                              <th
                                key={col}
                                style={{
                                  padding: '0.5rem 0.75rem',
                                  textAlign: 'left',
                                  background: 'var(--bg-tertiary)',
                                  color: 'var(--text-primary)',
                                  borderBottom: '2px solid var(--accent-primary)',
                                  whiteSpace: 'nowrap',
                                  position: 'sticky',
                                  top: 0,
                                  zIndex: 1,
                                }}
                              >
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {preview.data.map((row, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                              {preview.columns.map((col) => (
                                <td
                                  key={col}
                                  style={{
                                    padding: '0.4rem 0.75rem',
                                    color: 'var(--text-secondary)',
                                    whiteSpace: 'nowrap',
                                    maxWidth: '200px',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                  }}
                                >
                                  {row[col] !== null && row[col] !== undefined ? String(row[col]) : '—'}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <p style={{ padding: '0.5rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                        Mostrando {preview.showing_rows} de {preview.total_rows.toLocaleString()} filas totales
                      </p>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
