import React, { useState, useEffect, useCallback } from 'react';
import { DollarSign } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

function formatMoney(cents) {
  if (!cents && cents !== 0) return '$0';
  const d = cents / 100;
  if (d >= 1e6) return `$${(d / 1e6).toFixed(2)}M`;
  if (d >= 1e3) return `$${(d / 1e3).toFixed(1)}K`;
  return `$${d.toFixed(2)}`;
}

export default function Financials() {
  const [financials, setFinancials] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [finRes, txRes] = await Promise.all([
        fetch(`${API}/api/live/financials`),
        fetch(`${API}/api/live/transactions?limit=50`),
      ]);
      const [fin, tx] = await Promise.all([finRes.json(), txRes.json()]);
      setFinancials(fin);
      setTransactions(tx.transactions || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 10000); return () => clearInterval(i); }, [fetchData]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  const hasData = transactions.length > 0 || (financials && Object.keys(financials).length > 0);

  return (
    <div data-testid="financials-page" className="space-y-4 animate-slide-in">
      {!hasData ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <DollarSign className="w-8 h-8 text-border mb-3" />
          <p className="text-sm text-muted-foreground max-w-md">No financial data yet. The AI will populate this as it earns revenue, pays for compute, and makes investments.</p>
        </div>
      ) : (
        <>
          {financials && Object.keys(financials).length > 0 && (
            <div className="bg-white border border-border rounded-sm p-5">
              <h3 className="text-sm font-heading font-semibold text-foreground mb-3">Financial State</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {financials.last_known_balance && <Metric label="Credits" value={formatMoney(parseInt(financials.last_known_balance))} />}
                {financials.last_known_usdc && <Metric label="USDC" value={`$${parseFloat(financials.last_known_usdc).toFixed(2)}`} />}
                {financials.total_inference_cost_cents !== undefined && <Metric label="Inference Cost" value={formatMoney(financials.total_inference_cost_cents)} />}
                {financials.total_inference_calls !== undefined && <Metric label="Inference Calls" value={financials.total_inference_calls} />}
              </div>
              {financials.spend_by_category && Object.keys(financials.spend_by_category).length > 0 && (
                <div className="mt-4 pt-4 border-t border-border">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-2">Spend by Category</span>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(financials.spend_by_category).map(([cat, cents]) => (
                      <div key={cat} className="text-xs"><span className="text-muted-foreground">{cat}:</span> <span className="font-mono font-medium text-foreground">{formatMoney(cents)}</span></div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          {transactions.length > 0 && (
            <div className="bg-white border border-border rounded-sm overflow-hidden">
              <div className="px-4 py-3 border-b border-border"><h3 className="text-sm font-heading font-semibold text-foreground">Transactions ({transactions.length})</h3></div>
              <table className="w-full">
                <thead><tr className="border-b border-border">
                  <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Type</th>
                  <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Amount</th>
                  <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Balance After</th>
                  <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Description</th>
                  <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Time</th>
                </tr></thead>
                <tbody>
                  {transactions.map((tx, i) => (
                    <tr key={i} className="border-b border-border last:border-0 hover:bg-secondary/50">
                      <td className="px-4 py-2"><span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground">{tx.type}</span></td>
                      <td className="px-4 py-2 text-xs font-mono text-right">{formatMoney(tx.amount_cents)}</td>
                      <td className="px-4 py-2 text-xs font-mono text-right text-muted-foreground">{tx.balance_after_cents ? formatMoney(tx.balance_after_cents) : '—'}</td>
                      <td className="px-4 py-2 text-xs text-muted-foreground max-w-[300px] truncate">{tx.description}</td>
                      <td className="px-4 py-2 text-xs text-muted-foreground">{tx.timestamp?.split('T')[0]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div>
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</span>
      <div className="text-lg font-heading font-bold text-foreground">{value}</div>
    </div>
  );
}
