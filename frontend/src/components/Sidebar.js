import React from 'react';
import { 
  LayoutDashboard, Network, GitPullRequest, Briefcase, 
  DollarSign, Activity, Settings, ChevronLeft, ChevronRight,
  Zap, Building2, Brain
} from 'lucide-react';

const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'tycoon', label: 'Fund HQ', icon: Building2 },
  { id: 'mind', label: 'Agent Mind', icon: Brain },
  { id: 'agents', label: 'Agent Network', icon: Network },
  { id: 'deals', label: 'Deal Flow', icon: GitPullRequest },
  { id: 'portfolio', label: 'Portfolio', icon: Briefcase },
  { id: 'financials', label: 'Financials', icon: DollarSign },
  { id: 'activity', label: 'Activity', icon: Activity },
  { id: 'config', label: 'Configuration', icon: Settings },
];

export default function Sidebar({ currentPage, setCurrentPage, isOpen, onToggle }) {
  return (
    <aside 
      data-testid="sidebar"
      className={`fixed left-0 top-0 h-screen bg-white border-r border-border flex flex-col z-30 transition-all duration-200 ${isOpen ? 'w-60' : 'w-16'}`}
    >
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-sm bg-foreground flex items-center justify-center flex-shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          {isOpen && (
            <div className="animate-slide-in">
              <span className="font-heading font-bold text-sm tracking-tight text-foreground">ANIMA</span>
              <span className="font-heading font-light text-sm tracking-tight text-muted-foreground ml-1">FUND</span>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-2 space-y-0.5">
        {navItems.map(item => {
          const Icon = item.icon;
          const active = currentPage === item.id;
          return (
            <button
              key={item.id}
              data-testid={`nav-${item.id}`}
              onClick={() => setCurrentPage(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-sm text-sm font-medium transition-all duration-150
                ${active 
                  ? 'bg-foreground text-white' 
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
                }`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {isOpen && <span className="animate-slide-in">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <div className="p-2 border-t border-border">
        <button
          data-testid="sidebar-toggle"
          onClick={onToggle}
          className="w-full flex items-center justify-center py-2 rounded-sm text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
        >
          {isOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
}
