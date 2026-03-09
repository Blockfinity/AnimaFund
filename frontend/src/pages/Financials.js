import React, { useState, useCallback } from 'react';
import { DollarSign, Shield, AlertTriangle, CheckCircle, Wallet } from 'lucide-react';
import { useSSETrigger } from '../hooks/useSSE';

const API = process.env.REACT_APP_BACKEND_URL;

function formatMoney(cents) {
  if (!cents && cents !== 0) return '$0';
  const d = cents / 100;
  if (d >= 1e6) return `$${(d / 1e6).toFixed(2)}M`;
  if (d >= 1e3) return `$${(d / 1e3).toFixed(1)}K`;
  return `$${d.toFixed(2)}`;
}

function formatUSD(val) {
  if (!val && val !== 0) return '$0.00';
  if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  if (val >= 1e3) return `$${(val / 1e3).toFixed(1)}K`;
  return `$${val.toFixed(2)}`;
}

export default function Financials({ selectedAgent }) {
  const [financials, setFinancials] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [finRes, txRes, payRes] = await Promise.all([
        fetch(`${API}/api/live/financials`),
        fetch(`${API}/api/live/transactions?limit=50`),
        fetch(`${API}/api/payments/status`),
      ]);
      const [fin, tx, pay] = await Promise.all([finRes.json(), txRes.json(), payRes.json()]);
      setFinancials(fin);
      setTransactions(tx.transactions || []);
      setPaymentStatus(pay);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useSSETrigger(fetchData, { fallbackMs: 10000, deps: [selectedAgent] });

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  const ps = paymentStatus || {};
  const hasFinData = transactions.length > 0 || (financials && Object.keys(financials).length > 0);
  const hasPaymentData = ps.engine_running;

  return (
    <div data-testid="financials-page" className="space-y-4 animate-slide-in">
      {/* Creator Payout Compliance Card — always show when engine is running */}
      {hasPaymentData && (
        <div data-testid="payout-compliance" className={`border rounded-sm p-5 ${ps.payout_compliant ? 'bg-white border-border' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4" />
            <h3 className="text-sm font-heading font-semibold text-foreground">Creator Payout Compliance (50% Rule)</h3>
            {ps.payout_compliant ? (
              <span className="ml-auto flex items-center gap-1 text-xs text-green-700"><CheckCircle className="w-3 h-3" /> Compliant</span>
            ) : (
              <span className="ml-auto flex items-center gap-1 text-xs text-red-600"><AlertTriangle className="w-3 h-3" /> Outstanding Balance</span>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Metric label="Total Revenue" value={formatUSD(ps.total_revenue)} />
            <Metric label="Sustainability Cost" value={formatUSD(ps.total_sustainability_cost)} />
            <Metric label="Net (After Costs)" value={formatUSD(ps.net_after_sustainability)} />
            <Metric label="Paid to Creator" value={formatUSD(ps.total_creator_payouts)} />
            <Metric label="Owed to Creator" value={formatUSD(ps.owed_to_creator)} highlight={ps.owed_to_creator > 0} />
          </div>
          <div className="mt-3 pt-3 border-t border-border flex flex-wrap gap-4 text-[10px] text-muted-foreground">
            <span>Revenue Events: {ps.revenue_events_count || 0}</span>
            <span>Payout Events: {ps.payout_events_count || 0}</span>
            <span>On-chain TXs: {ps.onchain_transactions || 0}</span>
          </div>
        </div>
      )}

      {/* Fund Launch Readiness */}
      {hasPaymentData && (
        <div data-testid="fund-launch-status" className="bg-white border border-border rounded-sm p-5">
          <div className="flex items-center gap-2 mb-3">
            <Wallet className="w-4 h-4" />
            <h3 className="text-sm font-heading font-semibold text-foreground">Fund Launch Status</h3>
            {ps.fund_launch_ready ? (
              <span className="ml-auto text-xs text-green-700 font-medium">Ready to Launch</span>
            ) : (
              <span className="ml-auto text-xs text-muted-foreground">Raising Capital...</span>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Metric label="Capital Raised" value={formatUSD(ps.capital_raised)} />
            <Metric label="Launch Threshold" value={formatUSD(ps.fund_launch_threshold)} />
            <div>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Progress</span>
              <div className="mt-1 h-2 bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-foreground rounded-full transition-all" style={{ width: `${Math.min(100, ((ps.capital_raised || 0) / (ps.fund_launch_threshold || 10000)) * 100)}%` }} />
              </div>
              <span className="text-xs text-muted-foreground mt-1 block">{((ps.capital_raised || 0) / (ps.fund_launch_threshold || 10000) * 100).toFixed(1)}%</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-border text-[10px] text-muted-foreground">
            <span>Creator Wallets: </span>
            <span className="font-mono">SOL: {ps.creator_wallets?.solana?.slice(0, 8)}...</span>
            <span className="ml-3 font-mono">ETH: {ps.creator_wallets?.ethereum?.slice(0, 10)}...</span>
          </div>
        </div>
      )}

      {/* Financial State from Engine */}
      {!hasFinData && !hasPaymentData ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <DollarSign className="w-8 h-8 text-border mb-3" />
          <p className="text-sm text-muted-foreground max-w-md">No financial data yet. The AI will populate this as it earns revenue, pays for compute, and makes investments.</p>
        </div>
      ) : (
        <>
          {financials && Object.keys(financials).length > 0 && (
            <div className="bg-white border border-border rounded-sm p-5">
              <h3 className="text-sm font-heading font-semibold text-foreground mb-3">Engine Financial State</h3>
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

          {/* Recent Revenue & Payout Events */}
          {ps.recent_revenue?.length > 0 && (
            <div className="bg-white border border-border rounded-sm p-5">
              <h3 className="text-sm font-heading font-semibold text-foreground mb-3">Recent Revenue Events</h3>
              <div className="space-y-2">
                {ps.recent_revenue.map((r, i) => (
                  <div key={i} className="text-xs flex justify-between">
                    <span className="text-muted-foreground truncate max-w-[70%]">{r.fact}</span>
                    <span className="text-muted-foreground font-mono">{r.created_at?.split('T')[0]}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {ps.recent_payouts?.length > 0 && (
            <div className="bg-white border border-border rounded-sm p-5">
              <h3 className="text-sm font-heading font-semibold text-foreground mb-3">Creator Payout History</h3>
              <div className="space-y-2">
                {ps.recent_payouts.map((r, i) => (
                  <div key={i} className="text-xs flex justify-between">
                    <span className="text-muted-foreground truncate max-w-[70%]">{r.fact}</span>
                    <span className="text-muted-foreground font-mono">{r.created_at?.split('T')[0]}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Metric({ label, value, highlight }) {
  return (
    <div>
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</span>
      <div className={`text-lg font-heading font-bold ${highlight ? 'text-red-600' : 'text-foreground'}`}>{value}</div>
    </div>
  );
}
