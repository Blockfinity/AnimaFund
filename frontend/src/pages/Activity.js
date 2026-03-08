import React, { useState, useEffect, useCallback } from 'react';
import { Activity as ActivityIcon, Heart, MessageSquare, Wrench, Zap, Server, Globe, DollarSign, Brain, Network, Filter } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Date.now() - new Date(ts).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

const CATEGORY_CONFIG = {
  all: { label: 'All Activity', icon: ActivityIcon, color: '#71717a' },
  infrastructure: { label: 'Infrastructure', icon: Server, color: '#3b82f6' },
  compute: { label: 'Compute', icon: Wrench, color: '#10b981' },
  finance: { label: 'Finance', icon: DollarSign, color: '#f59e0b' },
  network: { label: 'Network', icon: Network, color: '#8b5cf6' },
  domains: { label: 'Domains', icon: Globe, color: '#06b6d4' },
  orchestrator: { label: 'Orchestrator', icon: Brain, color: '#ec4899' },
  tools: { label: 'Tools', icon: Zap, color: '#14b8a6' },
  inference: { label: 'Inference', icon: Brain, color: '#a855f7' },
  memory: { label: 'Memory', icon: Brain, color: '#6366f1' },
  system: { label: 'System', icon: Heart, color: '#71717a' },
  heartbeat: { label: 'Heartbeat', icon: Heart, color: '#60a5fa' },
  other: { label: 'Other', icon: Wrench, color: '#9ca3af' },
};

export default function Activity() {
  const [feed, setFeed] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/infrastructure/activity-feed?limit=200`);
      if (res.ok) {
        const d = await res.json();
        setFeed(d.feed || []);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    fetchData();
    const i = setInterval(fetchData, 8000);
    return () => clearInterval(i);
  }, [fetchData]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  // Count by category
  const counts = {};
  feed.forEach(item => {
    const cat = item.category || 'other';
    counts[cat] = (counts[cat] || 0) + 1;
  });

  const filtered = filter === 'all' ? feed : feed.filter(f => f.category === filter);

  // Category buttons — only show categories that have entries
  const activeCategories = ['all', ...Object.keys(counts).sort()];

  return (
    <div data-testid="activity-page" className="space-y-4 animate-slide-in">
      {/* Filter bar */}
      <div className="flex items-center gap-1 flex-wrap bg-white border border-border rounded-sm p-1">
        {activeCategories.map(cat => {
          const cfg = CATEGORY_CONFIG[cat] || CATEGORY_CONFIG.other;
          const Icon = cfg.icon;
          const count = cat === 'all' ? feed.length : (counts[cat] || 0);
          return (
            <button key={cat} data-testid={`activity-filter-${cat}`} onClick={() => setFilter(cat)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-medium transition-colors
                ${filter === cat ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
              <Icon className="w-3 h-3" />
              {cfg.label} ({count})
            </button>
          );
        })}
      </div>

      {/* Feed */}
      {filtered.length > 0 ? (
        <div className="bg-white border border-border rounded-sm divide-y divide-border">
          {filtered.map((item, i) => (
            <FeedItem key={i} item={item} />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <ActivityIcon className="w-8 h-8 text-border mb-3" />
          <p className="text-sm text-muted-foreground">
            {feed.length === 0 ? 'No activity yet. Activity appears when the agent starts operating.' : `No ${CATEGORY_CONFIG[filter]?.label || filter} activity.`}
          </p>
        </div>
      )}
    </div>
  );
}

function FeedItem({ item }) {
  const cfg = CATEGORY_CONFIG[item.category] || CATEGORY_CONFIG.other;
  const Icon = cfg.icon;
  const hasError = item.error && item.error.length > 0;

  return (
    <div className="flex items-start gap-3 px-4 py-3 hover:bg-secondary/20 transition-colors">
      <div className="flex-shrink-0 mt-0.5">
        <div className="w-6 h-6 rounded-sm flex items-center justify-center" style={{ backgroundColor: cfg.color + '15' }}>
          <Icon className="w-3 h-3" style={{ color: cfg.color }} />
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-sm border bg-secondary text-foreground">
            {item.title}
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-sm" style={{ backgroundColor: cfg.color + '15', color: cfg.color }}>
            {item.category}
          </span>
          {item.type === 'transaction' && item.amount_cents !== undefined && (
            <span className={`text-[10px] font-mono font-semibold ${item.amount_cents > 0 ? 'text-green-600' : 'text-red-500'}`}>
              {item.amount_cents > 0 ? '+' : ''}{(item.amount_cents / 100).toFixed(2)}
            </span>
          )}
          {item.duration_ms > 0 && (
            <span className="text-[10px] font-mono text-muted-foreground">{item.duration_ms}ms</span>
          )}
          {hasError && <span className="text-[10px] text-red-500 font-medium">ERROR</span>}
        </div>
        <p className="text-xs text-muted-foreground truncate">{item.detail}</p>
        {item.result && !hasError && (
          <p className="text-[10px] text-muted-foreground/70 truncate mt-0.5 font-mono">{item.result.slice(0, 120)}</p>
        )}
        {hasError && (
          <p className="text-[10px] text-red-400 truncate mt-0.5">{item.error}</p>
        )}
      </div>
      <span className="text-[10px] font-mono text-muted-foreground flex-shrink-0 mt-1">
        {timeAgo(item.timestamp)}
      </span>
    </div>
  );
}
