import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, Users, GitPullRequest, Briefcase, 
  DollarSign, Shield, Zap, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL;

function MetricCard({ label, value, subValue, icon: Icon, trend, color = 'text-foreground' }) {
  return (
    <div data-testid={`metric-${label.toLowerCase().replace(/\s/g, '-')}`} className="bg-white border border-border rounded-sm p-5 hover:shadow-sm transition-shadow duration-200">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</span>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <div className={`text-2xl font-heading font-bold tracking-tight ${color}`}>{value}</div>
      {subValue && (
        <div className="flex items-center gap-1 mt-1">
          {trend === 'up' && <ArrowUpRight className="w-3 h-3 text-success" />}
          {trend === 'down' && <ArrowDownRight className="w-3 h-3 text-error" />}
          <span className={`text-xs font-mono ${trend === 'up' ? 'text-success' : trend === 'down' ? 'text-error' : 'text-muted-foreground'}`}>
            {subValue}
          </span>
        </div>
      )}
    </div>
  );
}

function ActivityItem({ agent, tool, description, timestamp, riskLevel }) {
  const riskColors = { safe: 'bg-success/10 text-success', caution: 'bg-warning/10 text-warning', dangerous: 'bg-error/10 text-error' };
  const timeAgo = getTimeAgo(timestamp);
  
  return (
    <div className="flex items-start gap-3 py-3 border-b border-border last:border-0">
      <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${riskLevel === 'dangerous' ? 'bg-error' : riskLevel === 'caution' ? 'bg-warning' : 'bg-success'}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground truncate">{agent}</span>
          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-sm ${riskColors[riskLevel] || 'bg-secondary text-muted-foreground'}`}>
            {tool}
          </span>
        </div>
        <p className="text-xs text-muted-foreground mt-0.5 truncate">{description}</p>
      </div>
      <span className="text-[10px] font-mono text-muted-foreground flex-shrink-0">{timeAgo}</span>
    </div>
  );
}

function getTimeAgo(timestamp) {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-foreground text-white text-xs font-mono px-3 py-2 rounded-sm shadow-lg">
      <p className="mb-1 opacity-70">{label}</p>
      {payload.map((p, i) => (
        <p key={i}><span className="opacity-70">{p.name}:</span> ${(p.value / 1000000).toFixed(2)}M</p>
      ))}
    </div>
  );
};

export default function Overview({ overview, loading }) {
  const [financials, setFinancials] = useState([]);
  const [activities, setActivities] = useState([]);
  const [pipeline, setPipeline] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [finRes, actRes, pipeRes] = await Promise.all([
          fetch(`${API}/api/financials/history`),
          fetch(`${API}/api/activity?limit=8`),
          fetch(`${API}/api/deals/pipeline`),
        ]);
        const [fin, act, pipe] = await Promise.all([finRes.json(), actRes.json(), pipeRes.json()]);
        setFinancials(fin.history || []);
        setActivities(act.activities || []);
        setPipeline(pipe.pipeline || {});
      } catch (e) {
        console.error('Failed to fetch dashboard data:', e);
      }
    };
    fetchData();
  }, []);

  if (loading || !overview) {
    return (
      <div data-testid="overview-loading" className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-muted-foreground">Loading fund data...</span>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="overview-page" className="space-y-6 animate-slide-in">
      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Assets Under Management"
          value={`$${(overview.current_aum / 1_000_000).toFixed(1)}M`}
          subValue="+12.4% this quarter"
          trend="up"
          icon={TrendingUp}
          color="text-foreground"
        />
        <MetricCard
          label="Active Agents"
          value={`${overview.alive_agents} / ${overview.total_agents}`}
          subValue={`${Math.round((overview.alive_agents / overview.total_agents) * 100)}% operational`}
          trend="up"
          icon={Users}
          color="text-chart-primary"
        />
        <MetricCard
          label="Deal Pipeline"
          value={overview.total_deals}
          subValue={`${overview.funded_deals} funded, ${overview.rejection_rate}% rejection`}
          icon={GitPullRequest}
          color="text-chart-tertiary"
        />
        <MetricCard
          label="Portfolio Companies"
          value={overview.portfolio_companies}
          subValue="Active incubation"
          trend="up"
          icon={Briefcase}
          color="text-chart-secondary"
        />
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="USDC Balance"
          value={`$${(overview.usdc_balance / 1000).toFixed(0)}K`}
          subValue="On-chain (Base)"
          icon={DollarSign}
          color="text-foreground"
        />
        <MetricCard
          label="Conway Credits"
          value={`$${overview.conway_credits.toLocaleString()}`}
          subValue={`Tier: ${overview.survival_tier}`}
          icon={Zap}
          color="text-chart-primary"
        />
        <MetricCard
          label="Management Fee"
          value={`${overview.management_fee}%`}
          subValue="Annual on AUM"
          icon={Shield}
          color="text-foreground"
        />
        <MetricCard
          label="Carried Interest"
          value={`${overview.carried_interest}%`}
          subValue="50% to human wallet"
          icon={TrendingUp}
          color="text-chart-quaternary"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* AUM Chart */}
        <div className="lg:col-span-2 bg-white border border-border rounded-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-medium text-foreground">AUM Growth</h3>
              <p className="text-xs text-muted-foreground mt-0.5">12-month trajectory</p>
            </div>
            <span className="text-xs font-mono text-muted-foreground">${(overview.current_aum / 1_000_000).toFixed(1)}M current</span>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={financials}>
                <defs>
                  <linearGradient id="aumGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2563eb" stopOpacity={0.12} />
                    <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#71717a' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#71717a' }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v/1000000).toFixed(0)}M`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="aum" stroke="#2563eb" strokeWidth={2} fill="url(#aumGrad)" name="AUM" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="bg-white border border-border rounded-sm p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-foreground">Recent Activity</h3>
            <span className="w-2 h-2 bg-success rounded-full animate-pulse-dot" />
          </div>
          <div className="space-y-0 max-h-[260px] overflow-y-auto">
            {activities.map((act, i) => (
              <ActivityItem
                key={i}
                agent={act.agent_name}
                tool={act.tool_used}
                description={act.description}
                timestamp={act.timestamp}
                riskLevel={act.risk_level}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Pipeline + Agent Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Deal Pipeline */}
        <div className="bg-white border border-border rounded-sm p-5">
          <h3 className="text-sm font-medium text-foreground mb-4">Deal Flow Pipeline</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pipeline ? Object.entries(pipeline).map(([stage, count]) => ({ stage: stage.replace(' ', '\n'), count })) : []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e4e4e7" vertical={false} />
                <XAxis dataKey="stage" tick={{ fontSize: 9, fill: '#71717a' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#71717a' }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#09090b', border: 'none', borderRadius: 2, color: '#fff', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                />
                <Bar dataKey="count" fill="#18181b" radius={[2, 2, 0, 0]} name="Deals" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Fund Stats */}
        <div className="bg-white border border-border rounded-sm p-5">
          <h3 className="text-sm font-medium text-foreground mb-4">Fund Metrics</h3>
          <div className="space-y-3">
            {financials.slice(-3).reverse().map((f, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <span className="text-xs font-mono text-muted-foreground">{f.month}</span>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <span className="text-[10px] text-muted-foreground block">Deployed</span>
                    <span className="text-xs font-mono font-medium">${(f.investments_deployed / 1000).toFixed(0)}K</span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-muted-foreground block">Returns</span>
                    <span className="text-xs font-mono font-medium text-success">${(f.returns_received / 1000).toFixed(0)}K</span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-muted-foreground block">Agents</span>
                    <span className="text-xs font-mono font-medium">{f.agent_count}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-muted-foreground block">Deals</span>
                    <span className="text-xs font-mono font-medium">{f.deals_reviewed}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
