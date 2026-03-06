import React, { useState, useEffect, useCallback } from 'react';
import { Brain } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Memory() {
  const [facts, setFacts] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/live/memory`);
      const data = await res.json();
      setFacts(data.facts || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 10000); return () => clearInterval(i); }, [fetchData]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  const categories = ['all', ...new Set(facts.map(f => f.category))];
  const filtered = filter === 'all' ? facts : facts.filter(f => f.category === filter);

  return (
    <div data-testid="memory-page" className="space-y-4 animate-slide-in">
      {facts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <Brain className="w-8 h-8 text-border mb-3" />
          <p className="text-sm text-muted-foreground max-w-md">No memory data yet. The AI's 5-tier memory system (working, episodic, semantic, procedural, relationship) populates as it learns and operates.</p>
        </div>
      ) : (
        <>
          {/* Category filters */}
          <div className="flex items-center gap-1 flex-wrap">
            {categories.map(cat => (
              <button key={cat} onClick={() => setFilter(cat)}
                className={`text-xs font-medium px-3 py-1.5 rounded-sm transition-colors capitalize ${filter === cat ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary bg-white border border-border'}`}>
                {cat} {cat !== 'all' && `(${facts.filter(f => f.category === cat).length})`}
              </button>
            ))}
          </div>

          <div className="bg-white border border-border rounded-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-border">
              <h3 className="text-sm font-heading font-semibold text-foreground">Semantic Memory ({filtered.length} facts)</h3>
            </div>
            <table className="w-full">
              <thead><tr className="border-b border-border">
                <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Category</th>
                <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Key</th>
                <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Value</th>
                <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Confidence</th>
                <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Updated</th>
              </tr></thead>
              <tbody>
                {filtered.map((f, i) => (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-secondary/50">
                    <td className="px-4 py-2"><span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">{f.category}</span></td>
                    <td className="px-4 py-2 text-xs font-medium text-foreground">{f.key}</td>
                    <td className="px-4 py-2 text-xs text-muted-foreground max-w-[400px]"><div className="truncate">{f.value}</div></td>
                    <td className="px-4 py-2 text-xs font-mono text-muted-foreground text-right">{(f.confidence * 100).toFixed(0)}%</td>
                    <td className="px-4 py-2 text-xs text-muted-foreground">{f.updated_at?.split('T')[0]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
