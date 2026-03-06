import React from 'react';
import { Menu, Bell, CircleDot } from 'lucide-react';

const tierColors = {
  high: 'text-success',
  normal: 'text-chart-primary',
  low_compute: 'text-warning',
  critical: 'text-error',
  dead: 'text-muted-foreground',
};

const pageLabels = {
  overview: 'Fund Overview',
  tycoon: 'Fund HQ — Tycoon View',
  mind: 'Agent Mind — Live Consciousness',
  agents: 'Agent Network',
  deals: 'Deal Flow Pipeline',
  portfolio: 'Portfolio & Incubation',
  financials: 'Financial Management',
  activity: 'Activity Log',
  config: 'Configuration',
};

export default function Header({ overview, currentPage, onToggleSidebar }) {
  const tier = overview?.survival_tier || 'unknown';
  
  return (
    <header data-testid="header" className="h-14 bg-white border-b border-border flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-4">
        <button 
          data-testid="menu-toggle"
          onClick={onToggleSidebar} 
          className="text-muted-foreground hover:text-foreground transition-colors lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="font-heading text-lg font-semibold tracking-tight text-foreground">
          {pageLabels[currentPage] || 'Dashboard'}
        </h1>
      </div>

      <div className="flex items-center gap-5">
        {overview && (
          <>
            <div className="flex items-center gap-2 text-xs font-mono">
              <CircleDot className={`w-3 h-3 ${tierColors[tier]} animate-pulse-dot`} />
              <span className="text-muted-foreground uppercase tracking-wider">{tier}</span>
            </div>
            <div className="h-4 w-px bg-border" />
            <div className="text-xs font-mono text-muted-foreground">
              <span className="text-foreground font-semibold">{overview.alive_agents}</span>
              <span className="ml-1">agents live</span>
            </div>
            <div className="h-4 w-px bg-border" />
            <div className="text-xs font-mono text-muted-foreground">
              <span className="text-foreground font-semibold">${(overview.current_aum / 1_000_000).toFixed(1)}M</span>
              <span className="ml-1">AUM</span>
            </div>
          </>
        )}
        <button data-testid="notifications-btn" className="relative text-muted-foreground hover:text-foreground transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-chart-primary rounded-full" />
        </button>
      </div>
    </header>
  );
}
