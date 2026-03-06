import React, { useState, useEffect, useCallback } from 'react';
import { Briefcase } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Portfolio() {
  const [facts, setFacts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/live/memory`);
      const data = await res.json();
      const portfolioFacts = (data.facts || []).filter(f => f.category === 'domain' || f.key?.toLowerCase().includes('portfolio') || f.key?.toLowerCase().includes('incubat') || f.key?.toLowerCase().includes('funded') || f.key?.toLowerCase().includes('investment'));
      setFacts(portfolioFacts);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 10000); return () => clearInterval(i); }, [fetchData]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div data-testid="portfolio-page" className="space-y-4 animate-slide-in">
      {facts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <Briefcase className="w-8 h-8 text-border mb-3" />
          <p className="text-sm text-muted-foreground max-w-md">No portfolio data yet. The AI will populate this as it funds startups and tracks their incubation progress.</p>
        </div>
      ) : (
        <div className="bg-white border border-border rounded-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-border"><h3 className="text-sm font-heading font-semibold text-foreground">Portfolio ({facts.length} entries)</h3></div>
          <table className="w-full">
            <thead><tr className="border-b border-border">
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Key</th>
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Value</th>
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Confidence</th>
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Updated</th>
            </tr></thead>
            <tbody>
              {facts.map((f, i) => (
                <tr key={i} className="border-b border-border last:border-0 hover:bg-secondary/50">
                  <td className="px-4 py-2 text-xs font-medium text-foreground">{f.key}</td>
                  <td className="px-4 py-2 text-xs text-muted-foreground max-w-[400px] truncate">{f.value}</td>
                  <td className="px-4 py-2 text-xs font-mono text-muted-foreground">{(f.confidence * 100).toFixed(0)}%</td>
                  <td className="px-4 py-2 text-xs text-muted-foreground">{f.updated_at?.split('T')[0]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
