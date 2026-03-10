import React from 'react';
import { Menu, CircleDot, ChevronDown, Plus, Wifi, WifiOff, Rocket, Wallet } from 'lucide-react';
import { useSSE } from '../hooks/useSSE';

const API = process.env.REACT_APP_BACKEND_URL;

const pageLabels = {
  animavm: 'Anima VM',
  mind: 'Agent Mind',
  fundhq: 'Fund HQ',
  agents: 'Agents',
  skills: 'Skills',
  deals: 'Deal Flow',
  portfolio: 'Portfolio',
  financials: 'Financials',
  activity: 'Activity',
  memory: 'Memory',
  config: 'Configuration',
  wallet: 'Wallet & Logs',
};

export default function Header({ overview, currentPage, onToggleSidebar, agentList, selectedAgent, onSelectAgent, onCreateAgent, onGoGenesis, onGoWallet }) {
  const isLive = overview?.live || false;
  const dbExists = overview?.db_exists || false;
  const agentState = overview?.agent_state;
  const { connected: sseConnected } = useSSE();
  const [dropdownOpen, setDropdownOpen] = React.useState(false);
  const dropRef = React.useRef(null);

  React.useEffect(() => {
    const handler = (e) => { if (dropRef.current && !dropRef.current.contains(e.target)) setDropdownOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const currentAgentName = (agentList || []).find(a => a.agent_id === selectedAgent)?.name || 'Anima Fund';

  return (
    <header data-testid="header" className="h-14 bg-white border-b border-border flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-4">
        <button data-testid="menu-toggle" onClick={onToggleSidebar} className="text-muted-foreground hover:text-foreground transition-colors lg:hidden">
          <Menu className="w-5 h-5" />
        </button>

        {/* Agent Selector */}
        <div className="relative" ref={dropRef}>
          <button
            data-testid="agent-selector"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-border hover:bg-secondary/50 transition-colors"
          >
            <div className="w-2 h-2 rounded-full bg-success" />
            <span className="font-heading text-sm font-semibold text-foreground max-w-[180px] truncate">{currentAgentName}</span>
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
          </button>

          {dropdownOpen && (
            <div className="absolute top-full left-0 mt-1 w-64 bg-white border border-border rounded-md shadow-lg z-50 overflow-hidden">
              {(agentList || []).map(agent => (
                <button
                  key={agent.agent_id}
                  data-testid={`agent-option-${agent.agent_id}`}
                  onClick={() => { onSelectAgent(agent.agent_id); setDropdownOpen(false); }}
                  className={`w-full text-left px-4 py-2.5 text-sm hover:bg-secondary/50 transition-colors flex items-center gap-3 ${agent.agent_id === selectedAgent ? 'bg-secondary/30 font-semibold' : ''}`}
                >
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${agent.status === 'running' ? 'bg-success' : 'bg-muted-foreground'}`} />
                  <div className="min-w-0">
                    <div className="truncate font-heading">{agent.name}</div>
                    <div className="text-[10px] text-muted-foreground">{agent.status || 'created'}</div>
                  </div>
                </button>
              ))}
              <button
                data-testid="create-new-agent-btn"
                onClick={() => { onCreateAgent(); setDropdownOpen(false); }}
                className="w-full text-left px-4 py-2.5 text-sm hover:bg-secondary/50 transition-colors flex items-center gap-3 border-t border-border text-muted-foreground"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create New Agent</span>
              </button>
            </div>
          )}
        </div>

        <span className="text-muted-foreground text-xs hidden md:inline">/</span>
        <h1 className="font-heading text-sm font-medium text-muted-foreground hidden md:block">{pageLabels[currentPage] || 'Dashboard'}</h1>
      </div>
      <div className="flex items-center gap-3 text-xs font-mono">
        {/* Genesis + Wallet pills */}
        <button data-testid="header-genesis-btn" onClick={onGoGenesis}
          className="flex items-center gap-1 px-2.5 py-1 rounded-full border border-border hover:bg-secondary/50 transition-colors text-muted-foreground hover:text-foreground"
          title="Genesis — Agent Provisioning">
          <Rocket className="w-3 h-3" />
          <span className="text-[10px] font-semibold hidden sm:inline">Genesis</span>
        </button>
        <button data-testid="header-wallet-btn" onClick={onGoWallet}
          className="flex items-center gap-1 px-2.5 py-1 rounded-full border border-border hover:bg-secondary/50 transition-colors text-muted-foreground hover:text-foreground"
          title="Agent Wallet">
          <Wallet className="w-3 h-3" />
          <span className="text-[10px] font-semibold hidden sm:inline">Wallet</span>
        </button>

        <div className="flex items-center gap-1.5" title={sseConnected ? 'Real-time stream connected' : 'Polling (SSE reconnecting...)'}>
          {sseConnected
            ? <Wifi className="w-3 h-3 text-success" data-testid="sse-connected-icon" />
            : <WifiOff className="w-3 h-3 text-muted-foreground animate-pulse" data-testid="sse-disconnected-icon" />}
          <span className="text-muted-foreground text-[10px] hidden sm:inline">{sseConnected ? 'LIVE' : 'POLL'}</span>
        </div>
        <CircleDot className={`w-3 h-3 ${isLive ? 'text-success animate-pulse-dot' : dbExists ? 'text-amber-400 animate-pulse-dot' : 'text-muted-foreground'}`} />
        <span className="text-muted-foreground uppercase tracking-wider">
          {isLive ? `LIVE | ${overview.turn_count || 0} turns` : dbExists ? `ENGINE ACTIVE | ${agentState || 'awaiting funding'}` : 'WAITING FOR ENGINE'}
        </span>
      </div>
    </header>
  );
}
