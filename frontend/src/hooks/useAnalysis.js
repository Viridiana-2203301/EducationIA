/**
 * useAnalysis hook - manages analysis state and data fetching.
 */
import { useState, useCallback } from 'react';
import { runAnalysis, getLatestAnalysis, getRelationshipGraph, getInsights } from '../services/api';

export function useAnalysis() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [graph, setGraph] = useState(null);
  const [insights, setInsights] = useState([]);
  const [progress, setProgress] = useState(0);

  const executeAnalysis = useCallback(async (options = {}) => {
    setLoading(true);
    setError(null);
    setProgress(10);

    try {
      setProgress(30);
      const analysisResults = await runAnalysis(options);
      setProgress(70);
      setResults(analysisResults);

      // Fetch graph and insights
      try {
        const [graphData, insightsData] = await Promise.all([
          getRelationshipGraph(),
          getInsights(),
        ]);
        setGraph(graphData);
        setInsights(insightsData);
      } catch (e) {
        console.warn('Could not fetch graph/insights:', e);
      }

      setProgress(100);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Error en el análisis';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchLatest = useCallback(async () => {
    try {
      setLoading(true);
      const [latest, graphData, insightsData] = await Promise.all([
        getLatestAnalysis(),
        getRelationshipGraph().catch(() => null),
        getInsights().catch(() => []),
      ]);
      setResults(latest);
      setGraph(graphData);
      setInsights(insightsData);
    } catch (err) {
      // No previous analysis
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading, error, results, graph, insights, progress,
    executeAnalysis, fetchLatest,
  };
}
