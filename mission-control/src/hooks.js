import { useState, useEffect, useCallback } from 'react';

// Use production endpoint directly if built for PROD without Vite proxy, otherwise use relative path
const API_BASE = import.meta.env.PROD ? 'http://95.217.158.7' : '';

export function useApi(path, interval = null) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const r = await fetch(`${API_BASE}${path}`, { cache: 'no-store' });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const json = await r.json();
      setData(json);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    fetchData();
    if (interval) {
      const id = setInterval(fetchData, interval);
      return () => clearInterval(id);
    }
  }, [fetchData, interval]);

  return { data, loading, error, refetch: fetchData };
}

export function relTime(iso) {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
  if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
  return Math.floor(diff / 86400) + 'd ago';
}

export function budgetColor(pct) {
  if (pct < 60) return 'var(--accent-teal)';
  if (pct < 80) return 'var(--accent-amber)';
  return 'var(--accent-coral)';
}

export function getNZTime() {
  return new Date().toLocaleTimeString('en-NZ', {
    timeZone: 'Pacific/Auckland',
    hour: '2-digit', minute: '2-digit', hour12: false
  });
}
