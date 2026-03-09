import { useState, useEffect, useRef, useCallback, createContext, useContext } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * SSE Context — single EventSource connection shared across all components.
 * Provides:
 *  - sseData: latest parsed SSE payload
 *  - version: increments on every new SSE event (use as useEffect dependency)
 *  - connected: whether the SSE connection is active
 */
const SSEContext = createContext({
  sseData: null,
  version: 0,
  connected: false,
});

export function SSEProvider({ children }) {
  const [sseData, setSSEData] = useState(null);
  const [version, setVersion] = useState(0);
  const [connected, setConnected] = useState(false);
  const esRef = useRef(null);
  const reconnectTimer = useRef(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
    }

    try {
      const es = new EventSource(`${API}/api/live/stream`);
      esRef.current = es;

      es.onopen = () => {
        if (mountedRef.current) setConnected(true);
      };

      es.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          if (!data.error) {
            setSSEData(data);
            setVersion(v => v + 1);
          }
        } catch {
          // Ignore parse errors (heartbeats, etc.)
        }
      };

      es.onerror = () => {
        if (!mountedRef.current) return;
        setConnected(false);
        es.close();
        esRef.current = null;
        // Reconnect after 5s
        reconnectTimer.current = setTimeout(() => {
          if (mountedRef.current) connect();
        }, 5000);
      };
    } catch {
      // SSE not supported or URL error — silent fail, pages fall back to polling
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (esRef.current) esRef.current.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [connect]);

  return (
    <SSEContext.Provider value={{ sseData, version, connected }}>
      {children}
    </SSEContext.Provider>
  );
}

/**
 * useSSE — access the shared SSE stream data.
 * Returns { sseData, version, connected }
 */
export function useSSE() {
  return useContext(SSEContext);
}

/**
 * useSSETrigger — call a fetch function whenever SSE pushes new data.
 * Falls back to polling at `fallbackMs` if SSE is disconnected.
 *
 * @param {Function} fetchFn - async function to call on SSE update
 * @param {Object} opts
 * @param {number} opts.fallbackMs - polling interval when SSE is down (default: 12000)
 * @param {Array} opts.deps - additional dependencies to trigger a re-fetch
 */
export function useSSETrigger(fetchFn, { fallbackMs = 12000, deps = [] } = {}) {
  const { version, connected } = useSSE();
  const fetchRef = useRef(fetchFn);
  fetchRef.current = fetchFn;
  const initialDone = useRef(false);

  // Initial fetch on mount
  useEffect(() => {
    if (!initialDone.current) {
      initialDone.current = true;
      fetchRef.current();
    }
  }, []);

  // SSE-triggered fetch
  useEffect(() => {
    if (version > 0 && connected) {
      fetchRef.current();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version, connected]);

  // Fallback polling when SSE is disconnected
  useEffect(() => {
    if (connected) return;
    const i = setInterval(() => fetchRef.current(), fallbackMs);
    return () => clearInterval(i);
  }, [connected, fallbackMs]);

  // Re-fetch on deps change
  useEffect(() => {
    if (initialDone.current && deps.length > 0) {
      fetchRef.current();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
