import React, { useState, useEffect } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { DollarSign, TrendingUp, ArrowDownRight, PieChart } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-foreground text-white text-xs font-mono px-3 py-2 rounded-sm shadow-lg">
      <p className="mb-1 opacity-70">{label}</p>
      {payload.map((p, i) => (
        <p key={i}><span className="opacity-70">{p.name}:</span> ${(p.value / 1000).toFixed(1)}K</p>
      ))}
    </div>
  );
};

export default function Financials() {
  const [history, setHistory] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [histRes, sumRes] = await Promise.all([
          fetch(`${API}/api/financials/history`),
          fetch(`${API}/api/financials/summary`),
        ]);
        const [hist, sum] = await Promise.all([histRes.json(), sumRes.json()]);
        setHistory(hist.history || []);
        setSummary(sum);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div data-testid="financials-loading" className="flex items-center justify-center h-64">
        <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div data-testid="financials-page" className="space-y-6 animate-slide-in">
      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard icon={DollarSign} label="Current AUM" value={`$${(summary.current_aum / 1000000).toFixed(1)}M`} />
          <SummaryCard icon={TrendingUp} label="USDC Balance" value={`$${(summary.usdc_balance / 1000).toFixed(0)}K`} />
          <SummaryCard icon={PieChart} label="Recent Deployed" value={`$${(summary.recent_deployed / 1000).toFixed(0)}K`} />
          <SummaryCard icon={ArrowDownRight} label="Recent Returns" value={`$${(summary.recent_returns / 1000).toFixed(0)}K`} color="text-success" />
        </div>
      )}

      {/* Fee Structure */}
      {summary && (
        <div className="bg-white border border-border rounded-sm p-5">
          <h3 className="text-sm font-medium text-foreground mb-4">Fee Structure</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeeBlock label="Management Fee" value={`${summary.management_fee_rate}%`} desc="Annual on AUM" />
            <FeeBlock label="Carried Interest" value={`${summary.carry_rate}%`} desc="On profits above hurdle" />
            <FeeBlock label="Human Wallet Share" value={`${summary.human_carry_share}%`} desc="Of carried interest" />
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Revenue vs Costs */}
        <div className="bg-white border border-border rounded-sm p-5">
          <h3 className="text-sm font-medium text-foreground mb-4">Revenue vs Costs</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#71717a' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#71717a' }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Bar dataKey="management_fees" name="Fees" fill="#2563eb" radius={[2, 2, 0, 0]} />
                <Bar dataKey="operational_costs" name="Costs" fill="#ef4444" radius={[2, 2, 0, 0]} />
                <Bar dataKey="revenue_from_tasks" name="Task Revenue" fill="#16a34a" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Investment Activity */}
        <div className="bg-white border border-border rounded-sm p-5">
          <h3 className="text-sm font-medium text-foreground mb-4">Investment Activity</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="deployGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity={0.12} />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="returnGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#16a34a" stopOpacity={0.12} />
                    <stop offset="100%" stopColor="#16a34a" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#71717a' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#71717a' }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}K`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                <Area type="monotone" dataKey="investments_deployed" stroke="#2563eb" strokeWidth={2} fill="url(#deployGrad)" name="Deployed" />
                <Area type="monotone" dataKey="returns_received" stroke="#16a34a" strokeWidth={2} fill="url(#returnGrad)" name="Returns" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Monthly Breakdown Table */}
      <div className="bg-white border border-border rounded-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-border">
          <h3 className="text-sm font-medium text-foreground">Monthly Breakdown</h3>
        </div>
        <table className="w-full" data-testid="financials-table">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Month</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">AUM</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Fees</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Costs</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Deployed</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Returns</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Agents</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">Deals</th>
            </tr>
          </thead>
          <tbody>
            {[...history].reverse().map((row, i) => (
              <tr key={row.month} className="border-b border-border last:border-0 hover:bg-secondary/50 transition-colors">
                <td className="px-4 py-2 text-xs font-mono text-foreground">{row.month}</td>
                <td className="px-4 py-2 text-xs font-mono text-foreground text-right">${(row.aum / 1000000).toFixed(2)}M</td>
                <td className="px-4 py-2 text-xs font-mono text-chart-primary text-right">${(row.management_fees / 1000).toFixed(1)}K</td>
                <td className="px-4 py-2 text-xs font-mono text-error text-right">${(row.operational_costs / 1000).toFixed(1)}K</td>
                <td className="px-4 py-2 text-xs font-mono text-foreground text-right">${(row.investments_deployed / 1000).toFixed(0)}K</td>
                <td className="px-4 py-2 text-xs font-mono text-success text-right">${(row.returns_received / 1000).toFixed(0)}K</td>
                <td className="px-4 py-2 text-xs font-mono text-foreground text-right">{row.agent_count}</td>
                <td className="px-4 py-2 text-xs font-mono text-foreground text-right">{row.deals_reviewed}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, color = 'text-foreground' }) {
  return (
    <div className="bg-white border border-border rounded-sm p-5">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-muted-foreground" />
        <span className="text-xs text-muted-foreground uppercase tracking-wider">{label}</span>
      </div>
      <span className={`text-xl font-heading font-bold ${color}`}>{value}</span>
    </div>
  );
}

function FeeBlock({ label, value, desc }) {
  return (
    <div className="text-center p-4 bg-secondary rounded-sm">
      <span className="text-3xl font-heading font-bold text-foreground">{value}</span>
      <p className="text-sm font-medium text-foreground mt-1">{label}</p>
      <p className="text-xs text-muted-foreground mt-0.5">{desc}</p>
    </div>
  );
}
