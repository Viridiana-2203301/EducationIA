/**
 * API Service - Axios wrapper for all backend calls.
 */
import axios from 'axios';

// En desarrollo: localhost:8000
// En producción: /api (reescrito por vercel.json a educationia-backend.onrender.com)
const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min for heavy analysis
  headers: { 'Accept': 'application/json' },
});

// --- Upload ---
export async function uploadFiles(files) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  const res = await api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  });
  return res.data;
}

// --- Datasets ---
export async function getDatasets() {
  const res = await api.get('/api/datasets');
  return res.data;
}

export async function getDataset(id) {
  const res = await api.get(`/api/datasets/${id}`);
  return res.data;
}

export async function getDatasetPreview(id, rows = 20) {
  const res = await api.get(`/api/datasets/${id}/preview?rows=${rows}`);
  return res.data;
}

// --- Analysis ---
export async function runAnalysis(options = {}) {
  const res = await api.post('/api/analysis/run', options);
  return res.data;
}

export async function getAnalysisResults(id) {
  const res = await api.get(`/api/analysis/results/${id}`);
  return res.data;
}

export async function getLatestAnalysis() {
  const res = await api.get('/api/analysis/latest');
  return res.data;
}

// --- Relationships ---
export async function getRelationships() {
  const res = await api.get('/api/relationships');
  return res.data;
}

export async function getRelationshipGraph() {
  const res = await api.get('/api/relationships/graph');
  return res.data;
}

// --- Insights ---
export async function getInsights() {
  const res = await api.get('/api/insights');
  return res.data;
}

// --- Fused/Concatenated Datasets ---
export async function getFusedDatasets() {
  const res = await api.get('/api/fused');
  return res.data;
}

export async function getFusedPreview(key, rows = 50) {
  const res = await api.get(`/api/fused/${encodeURIComponent(key)}/preview?rows=${rows}`);
  return res.data;
}

export function getFusedDownloadUrl(key) {
  return `${API_BASE}/api/fused/${encodeURIComponent(key)}/download`;
}
