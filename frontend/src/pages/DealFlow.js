import React, { useState, useEffect } from 'react';
import { Filter, ArrowRight, Search } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const stageColors = {
  Sourced: 'bg-secondary text-secondary-foreground',
  Screening: 'bg-chart-primary/10 text-chart-primary',
  'Deep Dive': 'bg-chart-quaternary/10 text-chart-quaternary',
  'IC Review': 'bg-chart-tertiary/10 text-chart-tertiary',
  'Term Sheet': 'bg-info/10 text-info',
  'Due Diligence': 'bg-warning/10 text-warning',
  Funded: 'bg-success/10 text-success',
  Rejected: 'bg-error/10 text-error',
};

export default function DealFlow() {
  const [deals, setDeals] = useState([]);
  const [pipeline, setPipeline] = useState({});
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dealsRes, pipeRes] = await Promise.all([
          fetch(`${API}/api/deals`),
          fetch(`${API}/api/deals/pipeline`),
        ]);
        const [dealsData, pipeData] = await Promise.all([dealsRes.json(), pipeRes.json()]);
        setDeals(dealsData.deals || []);
        setPipeline(pipeData.pipeline || {});
      } catch (e) {
        console.error('Failed to fetch deals:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredDeals = deals.filter(d => {
    const matchStage = filter === 'All' || d.stage === filter;
    const matchSearch = !search || d.startup_name.toLowerCase().includes(search.toLowerCase());
    return matchStage && matchSearch;
  });

  const stages = ['All', 'Sourced', 'Screening', 'Deep Dive', 'IC Review', 'Term Sheet', 'Due Diligence', 'Funded', 'Rejected'];

  if (loading) {
    return (
      <div data-testid="deals-loading" className="flex items-center justify-center h-64">
        <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div data-testid="deal-flow-page" className="space-y-6 animate-slide-in">
      {/* Pipeline Overview */}
      <div className="bg-white border border-border rounded-sm p-5">
        <h3 className="text-sm font-medium text-foreground mb-4">Pipeline Stages</h3>
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {Object.entries(pipeline).map(([stage, count], i) => (
            <React.Fragment key={stage}>
              <button
                data-testid={`pipeline-stage-${stage.toLowerCase().replace(/\s/g, '-')}`}
                onClick={() => setFilter(stage)}
                className={`flex flex-col items-center px-4 py-3 rounded-sm border transition-all min-w-[100px] ${
                  filter === stage ? 'border-foreground bg-foreground text-white' : 'border-border hover:border-foreground/30'
                }`}
              >
                <span className={`text-xl font-heading font-bold ${filter === stage ? 'text-white' : 'text-foreground'}`}>{count}</span>
                <span className={`text-[10px] mt-1 ${filter === stage ? 'text-white/70' : 'text-muted-foreground'}`}>{stage}</span>
              </button>
              {i < Object.entries(pipeline).length - 1 && (
                <ArrowRight className="w-4 h-4 text-border flex-shrink-0" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            data-testid="deal-search"
            type="text"
            placeholder="Search startups..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm border border-border rounded-sm bg-white focus:outline-none focus:border-foreground transition-colors"
          />
        </div>
        <div className="flex items-center gap-1">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <select
            data-testid="deal-filter"
            value={filter}
            onChange={e => setFilter(e.target.value)}
            className="text-sm border border-border rounded-sm px-3 py-2 bg-white focus:outline-none focus:border-foreground"
          >
            {stages.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {/* Deals Table */}
      <div className="bg-white border border-border rounded-sm overflow-hidden">
        <table className="w-full" data-testid="deals-table">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Startup</th>
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Vertical</th>
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Stage</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Ask</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Equity</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">ROI Proj.</th>
              <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Score</th>
              <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Reviewer</th>
            </tr>
          </thead>
          <tbody>
            {filteredDeals.map((deal, i) => (
              <tr 
                key={deal.deal_id} 
                data-testid={`deal-row-${deal.deal_id}`}
                className="border-b border-border last:border-0 hover:bg-secondary/50 transition-colors"
              >
                <td className="px-4 py-3">
                  <span className="text-sm font-medium text-foreground">{deal.startup_name}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-muted-foreground">{deal.vertical}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${stageColors[deal.stage] || 'bg-secondary text-secondary-foreground'}`}>
                    {deal.stage}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-xs font-mono text-foreground">${(deal.ask_amount / 1000).toFixed(0)}K</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className="text-xs font-mono text-muted-foreground">{deal.equity_offered}%</span>
                </td>
                <td className="px-4 py-3 text-right">
                  <span className={`text-xs font-mono ${deal.roi_projection >= 20 ? 'text-success' : deal.roi_projection >= 10 ? 'text-foreground' : 'text-muted-foreground'}`}>
                    {deal.roi_projection}x
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-12 h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div 
                        className="h-full rounded-full" 
                        style={{ 
                          width: `${deal.score}%`, 
                          backgroundColor: deal.score >= 80 ? '#16a34a' : deal.score >= 50 ? '#d97706' : '#ef4444' 
                        }} 
                      />
                    </div>
                    <span className="text-xs font-mono text-foreground">{deal.score}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-[10px] font-mono text-muted-foreground">{deal.reviewer}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredDeals.length === 0 && (
          <div className="text-center py-8 text-sm text-muted-foreground">No deals match your criteria</div>
        )}
      </div>
    </div>
  );
}
