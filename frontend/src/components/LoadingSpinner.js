/**
 * LoadingSpinner - Loading state component with animated spinner.
 */
export default function LoadingSpinner({ text = 'Cargando...' }) {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p className="loading-text">{text}</p>
    </div>
  );
}
