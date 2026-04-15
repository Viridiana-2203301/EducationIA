/**
 * FileUpload - Drag-and-drop multi-file upload component.
 * Supports up to 36 CSV files with file validation preview.
 */
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

export default function FileUpload({ onUpload, uploading }) {
  const [files, setFiles] = useState([]);

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    const csvFiles = acceptedFiles.filter(f =>
      f.name.toLowerCase().endsWith('.csv')
    );

    if (csvFiles.length + files.length > 36) {
      alert('Máximo 36 archivos permitidos');
      return;
    }

    setFiles(prev => [...prev, ...csvFiles]);
  }, [files]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 36,
    disabled: uploading,
  });

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = () => {
    if (files.length > 0 && onUpload) {
      onUpload(files);
    }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div>
      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}
      >
        <input {...getInputProps()} />
        <span className="upload-icon">📁</span>
        <p className="upload-title">
          {isDragActive
            ? '¡Suelta los archivos aquí!'
            : 'Arrastra tus archivos CSV aquí'}
        </p>
        <p className="upload-subtitle">
          o haz clic para seleccionar • Máximo 36 archivos • Solo .csv
        </p>
      </div>

      {files.length > 0 && (
        <>
          <div className="upload-file-list">
            {files.map((file, index) => (
              <div key={index} className="upload-file-item">
                <span className="file-icon">📄</span>
                <span className="file-name" title={file.name}>{file.name}</span>
                <span className="file-size">{formatSize(file.size)}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                  style={{
                    background: 'none', border: 'none', color: '#f43f5e',
                    cursor: 'pointer', fontSize: '1rem', padding: '2px 6px',
                  }}
                  title="Eliminar"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>

          <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={uploading || files.length === 0}
            >
              {uploading ? '⏳ Subiendo...' : `📤 Subir ${files.length} archivo(s)`}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => setFiles([])}
              disabled={uploading}
            >
              🗑️ Limpiar
            </button>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              {files.length}/36 archivos
            </span>
          </div>
        </>
      )}
    </div>
  );
}
