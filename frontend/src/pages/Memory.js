import React, { useState, useEffect, useCallback } from 'react';
import { Database, Key, Brain, Zap, Clock } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Date.now() - new Date(ts).getTime();
  const s = Math.floor(diff / 1000); if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60); if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60); if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function Memory({ selectedAgent }) {
  const [facts, setFacts] = useState([]);
  const [kv, setKv] = useState([]);
  const [wake, setWake] = useState([]);
  const [tab, setTab] = useState('kv');
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [memRes, kvRes, wakeRes] = await Promise.all([
        fetch(`${API}/api/live/memory`),
        fetch(`${API}/api/live/kv`),
        fetch(`${API}/api/live/wake-events?limit=50`),
      ]);
      const [mem, kvData, wakeData] = await Promise.all([memRes.json(), kvRes.json(), wakeRes.json()]);
      setFacts(mem.facts || []);
      setKv(kvData.items || []);
      setWake(wakeData.events || []);
      if ((mem.facts || []).length > 0 && tab === 'kv') setTab('semantic');
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [tab]);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 8000); return () => clearInterval(i); }, [fetchData, selectedAgent]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  const tabs = [
    ['kv', `Runtime State (${kv.length})`, Key],
    ['wake', `Wake Events (${wake.length})`, Zap],
    ['semantic', `Semantic Memory (${facts.length})`, Brain],
  ];

  return (
    <div data-testid="memory-page" className="space-y-4 animate-slide-in">
      <div className="flex items-center gap-1 bg-white border border-border rounded-sm p-1">
        {tabs.map(([id, label, Icon]) => (
          <button key={id} data-testid={`memory-tab-${id}`} onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-sm text-sm font-medium transition-colors ${tab === id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
            <Icon className="w-3.5 h-3.5" />{label}
          </button>
        ))}
      </div>

      {/* KV Store */}
      {tab === 'kv' && (
        kv.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {kv.map((item, i) => (
              <div key={i} className="px-4 py-3 hover:bg-secondary/30">
                <div className="flex items-start gap-3">
                  <Key className="w-3 h-3 text-muted-foreground mt-1 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <span className="text-xs font-mono font-semibold text-foreground">{item.key}</span>
                    <div className="mt-1 text-[10px] font-mono text-muted-foreground break-all max-h-16 overflow-hidden">
                      {typeof item.value === 'object' ? JSON.stringify(item.value, null, 1) : String(item.raw || item.value).slice(0, 300)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Key} text="No runtime state data yet." />
        )
      )}

      {/* Wake Events */}
      {tab === 'wake' && (
        wake.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {wake.map((e, i) => (
              <div key={i} className="flex items-start gap-4 px-4 py-3 hover:bg-secondary/30">
                <Zap className="w-3.5 h-3.5 text-warning mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[10px] font-semibold text-foreground">{e.source}</span>
                    <span className="text-[10px] text-muted-foreground">{e.reason}</span>
                  </div>
                  {e.metadata && typeof e.metadata === 'object' && Object.keys(e.metadata).length > 0 && (
                    <div className="text-[9px] font-mono text-muted-foreground mt-1">
                      {Object.entries(e.metadata).slice(0, 4).map(([k, v]) => (
                        <span key={k} className="inline-block mr-3">{k}: {typeof v === 'object' ? JSON.stringify(v) : String(v).slice(0, 80)}</span>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-[10px] font-mono text-muted-foreground flex-shrink-0">{timeAgo(e.created_at)}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Zap} text="No wake events yet." />
        )
      )}

      {/* Semantic Memory */}
      {tab === 'semantic' && (
        facts.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {facts.map((f, i) => (
              <div key={i} className="px-4 py-3 hover:bg-secondary/30">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-semibold text-muted-foreground px-1.5 py-0.5 bg-secondary rounded-sm">{f.category}</span>
                  <span className="text-xs font-medium text-foreground">{f.key}</span>
                  <span className="text-[10px] font-mono text-muted-foreground ml-auto">{f.confidence ? `${(f.confidence * 100).toFixed(0)}%` : ''}</span>
                </div>
                <p className="text-xs text-muted-foreground">{f.value?.slice(0, 300)}</p>
                <span className="text-[9px] text-muted-foreground">{timeAgo(f.updated_at)}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Brain} text="No semantic memory facts yet. Memory is built as the agent completes turns and learns from interactions (requires Conway credits)." />
        )
      )}
    </div>
  );
}

function EmptyState({ icon: Icon, text }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <Icon className="w-8 h-8 text-border mb-3" />
      <p className="text-sm text-muted-foreground max-w-md">{text}</p>
    </div>
  );
}
