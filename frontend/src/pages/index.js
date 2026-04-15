/**
 * Landing / Upload Page.
 * Allows users to upload CSV files and trigger analysis.
 */
import { useState } from 'react';
import { useRouter } from 'next/router';
import FileUpload from '../components/FileUpload';
import { uploadFiles } from '../services/api';

export default function Home() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const router = useRouter();

  const handleUpload = async (files) => {
    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const response = await uploadFiles(files);
      setResult(response);

      // Auto-navigate to datasets after successful upload
      setTimeout(() => {
        router.push('/datasets');
      }, 2000);

    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Error al subir archivos';
      setError(message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <div className="section-header">
        <h1 className="section-title">Análisis Automático de CSV</h1>
        <p className="section-subtitle">
          Sube hasta 36 archivos CSV y descubre automáticamente patrones,
          correlaciones, clusters, anomalías e insights ocultos en tus datos.
        </p>
      </div>

      <div className="glass-card" style={{ marginTop: '2rem' }}>
        <FileUpload onUpload={handleUpload} uploading={uploading} />
      </div>

      {uploading && (
        <div className="glass-card" style={{ marginTop: '1rem' }}>
          <div style={{ textAlign: 'center', padding: '1rem' }}>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              ⏳ Subiendo y validando archivos...
            </p>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: '60%' }}></div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-banner" style={{ marginTop: '1rem' }}>
          ❌ {error}
        </div>
      )}

      {result && (
        <div className="glass-card" style={{
          marginTop: '1rem',
          borderLeft: '3px solid var(--accent-emerald)',
        }}>
          <p style={{ fontWeight: 600, color: 'var(--accent-emerald)' }}>
            ✅ {result.message}
          </p>
          {result.datasets && result.datasets.length > 0 && (
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', fontSize: '0.9rem' }}>
              {result.datasets.map(d => d.filename).join(', ')}
            </p>
          )}
          {result.errors && result.errors.length > 0 && (
            <div style={{ marginTop: '0.5rem' }}>
              {result.errors.map((err, i) => (
                <p key={i} style={{ color: 'var(--accent-rose)', fontSize: '0.85rem' }}>⚠️ {err}</p>
              ))}
            </div>
          )}
          <p style={{ color: 'var(--text-muted)', marginTop: '0.75rem', fontSize: '0.85rem' }}>
            Redirigiendo a datasets en 2 segundos...
          </p>
        </div>
      )}

      {/* Feature highlights */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: '1rem',
        marginTop: '3rem',
      }}>
        {[
          { icon: '🔍', title: 'Profiling Automático', desc: 'Análisis completo de tipos, nulos, duplicados y distribuciones' },
          { icon: '🔗', title: 'Detección de Relaciones', desc: 'Encuentra conexiones entre datasets automáticamente' },
          { icon: '🧹', title: 'Limpieza Inteligente', desc: 'Normalización, imputación y corrección de tipos de datos' },
          { icon: '🤖', title: 'Machine Learning', desc: 'Clustering, PCA, correlaciones y detección de anomalías' },
          { icon: '📈', title: 'Tendencias', desc: 'Detección de patrones temporales y comportamientos' },
          { icon: '💡', title: 'Insights Automáticos', desc: 'Explicaciones en lenguaje natural de los hallazgos' },
        ].map((feature, i) => (
          <div key={i} className="glass-card" style={{ textAlign: 'center' }}>
            <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '0.5rem' }}>
              {feature.icon}
            </span>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.3rem' }}>
              {feature.title}
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              {feature.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
