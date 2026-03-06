import React from 'react';
import { Menu, CircleDot } from 'lucide-react';

const pageLabels = {
  mind: 'Agent Mind',
  fundhq: 'Fund HQ',
  agents: 'Agents',
  deals: 'Deal Flow',
  portfolio: 'Portfolio',
  financials: 'Financials',
  activity: 'Activity',
  memory: 'Memory',
  config: 'Configuration',
};

export default function Header({ overview, currentPage, onToggleSidebar }) {
  const isLive = overview?.live || false;
  const dbExists = overview?.db_exists || false;
  const agentState = overview?.agent_state;
  return (
    <header data-testid="header" className="h-14 bg-white border-b border-border flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-4">
        <button data-testid="menu-toggle" onClick={onToggleSidebar} className="text-muted-foreground hover:text-foreground transition-colors lg:hidden">
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="font-heading text-lg font-semibold tracking-tight text-foreground">{pageLabels[currentPage] || 'Dashboard'}</h1>
      </div>
      <div className="flex items-center gap-2 text-xs font-mono">
        <CircleDot className={`w-3 h-3 ${isLive ? 'text-success animate-pulse-dot' : dbExists ? 'text-amber-400 animate-pulse-dot' : 'text-muted-foreground'}`} />
        <span className="text-muted-foreground uppercase tracking-wider">
          {isLive ? `LIVE | ${overview.turn_count || 0} turns` : dbExists ? `ENGINE ACTIVE | ${agentState || 'awaiting funding'}` : 'WAITING FOR ENGINE'}
        </span>
      </div>
    </header>
  );
}
