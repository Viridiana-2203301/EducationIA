/**
 * Keep-Alive Service - Prevents Render free tier from sleeping
 * Makes a ping request every 10 minutes to keep the backend alive
 */
import axios from 'axios';

const API_BASE = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000';

const keepAliveClient = axios.create({
  baseURL: API_BASE,
  timeout: 5000,
});

export function startKeepAlive() {
  // Ping the backend every 10 minutes
  setInterval(async () => {
    try {
      await keepAliveClient.get('/');
    } catch (error) {
      console.warn('Keep-alive ping failed (backend may be sleeping):', error.message);
    }
  }, 10 * 60 * 1000); // 10 minutes
}
