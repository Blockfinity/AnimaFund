import React, { useState, useEffect } from 'react';
import { Clock, Filter } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const riskBadge = {
  safe: 'bg-success/10 text-success border-success/20',
  caution: 'bg-warning/10 text-warning border-warning/20',
  dangerous: 'bg-error/10 text-error border-error/20',
};

const categoryColors = {
  financial: 'text-chart-primary',
  operational: 'text-muted-foreground',
  investment: 'text-success',
  social: 'text-chart-quaternary',
  technical: 'text-chart-tertiary',
};

function getTimeAgo(timestamp) {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function Activity() {
  const [activities, setActivities] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/activity?limit=100`)
      .then(r => r.json())
      .then(d => setActivities(d.activities || []))
      .catch(e => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  const filtered = activities.filter(a => filter === 'all' || a.category === filter || a.risk_level === filter);
  const categories = ['all', 'financial', 'operational', 'investment', 'social', 'technical'];

  if (loading) {
    return (
      <div data-testid="activity-loading" className="flex items-center justify-center h-64">
        <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div data-testid="activity-page" className="space-y-4 animate-slide-in">
      {/* Filters */}
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-muted-foreground" />
        {categories.map(cat => (
          <button
            key={cat}
            data-testid={`activity-filter-${cat}`}
            onClick={() => setFilter(cat)}
            className={`text-xs font-medium px-3 py-1.5 rounded-sm transition-colors capitalize ${
              filter === cat ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Activity List */}
      <div className="bg-white border border-border rounded-sm divide-y divide-border">
        {filtered.map((act, i) => (
          <div 
            key={act.activity_id || i} 
            data-testid={`activity-item-${i}`}
            className="flex items-start gap-4 px-5 py-4 hover:bg-secondary/30 transition-colors"
          >
            {/* Risk indicator */}
            <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
              act.risk_level === 'dangerous' ? 'bg-error' : act.risk_level === 'caution' ? 'bg-warning' : 'bg-success'
            }`} />
            
            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-sm font-medium text-foreground">{act.agent_name}</span>
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-sm border ${riskBadge[act.risk_level] || ''}`}>
                  {act.tool_used}
                </span>
                <span className={`text-[10px] uppercase tracking-wider ${categoryColors[act.category] || 'text-muted-foreground'}`}>
                  {act.category}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{act.description}</p>
            </div>

            {/* Time */}
            <div className="flex items-center gap-1 flex-shrink-0">
              <Clock className="w-3 h-3 text-muted-foreground" />
              <span className="text-[10px] font-mono text-muted-foreground">{getTimeAgo(act.timestamp)}</span>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="text-center py-8 text-sm text-muted-foreground">No activity matches your filter</div>
        )}
      </div>
    </div>
  );
}
