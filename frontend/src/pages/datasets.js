/**
 * Datasets Page - Shows all uploaded datasets with their profiles.
 * Allows triggering full analysis pipeline.
 */
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import DatasetCard from '../components/DatasetCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { getDatasets } from '../services/api';
import { useAnalysis } from '../hooks/useAnalysis';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { executeAnalysis, loading: analyzing, progress } = useAnalysis();

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      const data = await getDatasets();
      setDatasets(data);
    } catch (err) {
      console.error('Error loading datasets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    await executeAnalysis();
    // Refresh datasets to show updated statuses
    await loadDatasets();
    // Navigate to analysis page
    router.push('/analysis');
  };

  if (loading) return <LoadingSpinner text="Cargando datasets..." />;

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Datasets Cargados</h1>
        <p className="section-subtitle">
          {datasets.length > 0
            ? `${datasets.length} dataset(s) disponibles para análisis`
            : 'No hay datasets cargados. Sube archivos CSV primero.'
          }
        </p>
      </div>

      {datasets.length > 0 && (
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <button
            className="btn btn-success"
            onClick={handleRunAnalysis}
            disabled={analyzing}
          >
            {analyzing ? '⏳ Analizando...' : '🚀 Ejecutar Análisis Completo'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => router.push('/')}
          >
            📤 Subir más archivos
          </button>
        </div>
      )}

      {analyzing && (
        <div className="glass-card" style={{ marginTop: '1rem' }}>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
            ⚙️ Pipeline: profiling → limpieza → relaciones → fusión → ML → insights
          </p>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
        </div>
      )}

      {datasets.length === 0 ? (
        <div className="empty-state" style={{ marginTop: '3rem' }}>
          <span className="empty-state-icon">📁</span>
          <p className="empty-state-title">Sin datasets</p>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
            Sube archivos CSV para comenzar el análisis
          </p>
          <button className="btn btn-primary" onClick={() => router.push('/')}>
            📤 Subir archivos
          </button>
        </div>
      ) : (
        <div className="datasets-grid">
          {datasets.map(ds => (
            <DatasetCard key={ds.id} dataset={ds} />
          ))}
        </div>
      )}
    </div>
  );
}
