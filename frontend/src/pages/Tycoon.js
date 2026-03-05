import React, { useState, useEffect, useRef, useCallback } from 'react';
import { TrendingUp, Users, DollarSign, Zap, ChevronUp, Star } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const DEPARTMENTS = [
  { id: 'investment', name: 'Investment Team', color: '#2563eb', icon: '📊', targetMin: 50, targetMax: 100 },
  { id: 'platform', name: 'Platform / Portfolio', color: '#16a34a', icon: '🚀', targetMin: 50, targetMax: 100 },
  { id: 'operations', name: 'Operations', color: '#d97706', icon: '⚙️', targetMin: 20, targetMax: 50 },
  { id: 'dealflow', name: 'Deal Flow / Scouting', color: '#9333ea', icon: '🔍', targetMin: 10, targetMax: 20 },
  { id: 'exits', name: 'Exits / M&A', color: '#06b6d4', icon: '💎', targetMin: 5, targetMax: 10 },
  { id: 'ethics', name: 'DEI / Ethics', color: '#ec4899', icon: '⚖️', targetMin: 2, targetMax: 3 },
  { id: 'cto', name: 'CTO Team', color: '#f97316', icon: '💻', targetMin: 2, targetMax: 3 },
];

const AGENT_SPRITES = ['🤖', '🧠', '⚡', '🔮', '🎯', '📡', '🛡️', '🔬'];

const ACTION_MESSAGES = [
  'Reviewing pitch deck...',
  'Validating startup costs...',
  'Deploying $50K capital...',
  'Running skill tests...',
  'Checking SOUL.md...',
  'Calculating ROI...',
  'Monitoring KPIs...',
  'Scouting agents...',
  'Processing x402 payment...',
  'Updating fund NAV...',
  'Incubation check-in...',
  'Revenue +$2.4K today!',
  'New LP commitment!',
  'Agent hired!',
  'Deal rejected (score: 34)',
  'Portfolio company scaling!',
];

function formatMoney(n) {
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toFixed(0)}`;
}

function AgentSprite({ agent, floorWidth, index, total }) {
  const [posX, setPosX] = useState(0);
  const [direction, setDirection] = useState(1);
  const [showBubble, setShowBubble] = useState(false);
  const [bubbleText, setBubbleText] = useState('');
  const speed = useRef(0.3 + Math.random() * 0.5);
  const bubbleTimer = useRef(null);

  useEffect(() => {
    const startX = ((index + 1) / (total + 1)) * (floorWidth - 80) + 20;
    setPosX(startX);
  }, [index, total, floorWidth]);

  useEffect(() => {
    const moveInterval = setInterval(() => {
      setPosX(prev => {
        const next = prev + speed.current * direction;
        if (next > floorWidth - 60 || next < 20) {
          setDirection(d => -d);
          return prev;
        }
        return next;
      });
    }, 50);

    const bubbleInterval = setInterval(() => {
      if (Math.random() > 0.7) {
        setBubbleText(ACTION_MESSAGES[Math.floor(Math.random() * ACTION_MESSAGES.length)]);
        setShowBubble(true);
        if (bubbleTimer.current) clearTimeout(bubbleTimer.current);
        bubbleTimer.current = setTimeout(() => setShowBubble(false), 3000);
      }
    }, 5000 + Math.random() * 8000);

    return () => {
      clearInterval(moveInterval);
      clearInterval(bubbleInterval);
      if (bubbleTimer.current) clearTimeout(bubbleTimer.current);
    };
  }, [direction, floorWidth]);

  const sprite = AGENT_SPRITES[index % AGENT_SPRITES.length];

  return (
    <div
      className="absolute bottom-1 transition-transform"
      style={{ left: `${posX}px`, transform: `scaleX(${direction})` }}
    >
      {showBubble && (
        <div 
          className="absolute -top-10 left-1/2 -translate-x-1/2 bg-foreground text-white text-[8px] px-2 py-1 rounded-sm whitespace-nowrap z-10 animate-slide-in"
          style={{ transform: `scaleX(${direction}) translateX(-50%)` }}
        >
          {bubbleText}
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-foreground" />
        </div>
      )}
      <div className="text-center">
        <span className="text-lg">{sprite}</span>
        <div className="text-[7px] font-mono text-muted-foreground truncate max-w-[60px] mt-0.5" style={{ transform: `scaleX(${direction})` }}>
          {agent.role?.split(' ')[0] || 'Agent'}
        </div>
      </div>
    </div>
  );
}

function Floor({ dept, agents, floorIndex, totalFloors, isUnlocked }) {
  const floorRef = useRef(null);
  const [floorWidth, setFloorWidth] = useState(600);

  useEffect(() => {
    if (floorRef.current) {
      setFloorWidth(floorRef.current.offsetWidth);
    }
  }, []);

  const deptAgents = agents.filter(a => {
    const deptName = a.department?.toLowerCase() || '';
    return deptName.includes(dept.id) || deptName.includes(dept.name.split('/')[0].trim().toLowerCase());
  });

  return (
    <div
      data-testid={`tycoon-floor-${dept.id}`}
      className={`relative border-b-2 transition-all duration-500 ${
        isUnlocked 
          ? 'border-border bg-white opacity-100' 
          : 'border-border/30 bg-secondary/50 opacity-40'
      }`}
      style={{ minHeight: '80px' }}
    >
      {/* Floor label */}
      <div className="absolute left-0 top-0 bottom-0 w-28 flex flex-col items-center justify-center border-r border-border bg-secondary/30 z-10">
        <span className="text-lg">{dept.icon}</span>
        <span className="text-[8px] font-heading font-semibold text-foreground text-center leading-tight px-1">{dept.name}</span>
        <span className="text-[9px] font-mono text-muted-foreground mt-0.5">{deptAgents.length} agents</span>
      </div>

      {/* Floor content area */}
      <div ref={floorRef} className="ml-28 relative h-full min-h-[80px]">
        {isUnlocked && deptAgents.map((agent, i) => (
          <AgentSprite
            key={agent.agent_id || i}
            agent={agent}
            floorWidth={floorWidth}
            index={i}
            total={deptAgents.length}
          />
        ))}

        {!isUnlocked && (
          <div className="flex items-center justify-center h-full">
            <span className="text-xs text-muted-foreground font-mono">🔒 Unlock at {dept.targetMin} agents</span>
          </div>
        )}
      </div>

      {/* Hiring indicator */}
      {isUnlocked && deptAgents.length < dept.targetMin && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 animate-pulse">
          <ChevronUp className="w-3 h-3 text-success" />
          <span className="text-[8px] font-mono text-success">HIRING</span>
        </div>
      )}
    </div>
  );
}

export default function Tycoon() {
  const [overview, setOverview] = useState(null);
  const [agents, setAgents] = useState([]);
  const [financials, setFinancials] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fundLevel, setFundLevel] = useState(1);
  const [idleIncome, setIdleIncome] = useState(0);
  const [cashCounter, setCashCounter] = useState(0);
  const [notifications, setNotifications] = useState([]);

  const fetchData = useCallback(async () => {
    try {
      const [ovRes, agRes, finRes] = await Promise.all([
        fetch(`${API}/api/fund/overview`),
        fetch(`${API}/api/agents`),
        fetch(`${API}/api/financials/summary`),
      ]);
      const [ov, ag, fin] = await Promise.all([ovRes.json(), agRes.json(), finRes.json()]);
      setOverview(ov);
      setAgents(ag.agents || []);
      setFinancials(fin);

      const level = Math.max(1, Math.floor((ov.current_aum || 0) / 1_000_000));
      setFundLevel(level);
      setCashCounter(ov.usdc_balance || 0);
      setIdleIncome(Math.round((ov.current_aum || 0) * 0.03 / 365));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Simulate idle income ticking
  useEffect(() => {
    if (idleIncome <= 0) return;
    const tick = setInterval(() => {
      setCashCounter(prev => prev + idleIncome / 86400);
    }, 1000);
    return () => clearInterval(tick);
  }, [idleIncome]);

  // Random notifications
  useEffect(() => {
    const addNotif = setInterval(() => {
      const msgs = [
        { text: '+$2,400 portfolio revenue', type: 'income' },
        { text: 'New deal sourced: AgentForge', type: 'deal' },
        { text: 'Incubation Phase 4 complete', type: 'milestone' },
        { text: 'Agent hired: Junior Associate', type: 'hire' },
        { text: 'Deal rejected (score: 28/100)', type: 'reject' },
        { text: 'LP commitment: $50K USDC', type: 'income' },
        { text: 'Startup KPI target met!', type: 'milestone' },
      ];
      const msg = msgs[Math.floor(Math.random() * msgs.length)];
      setNotifications(prev => [{ ...msg, id: Date.now() }, ...prev].slice(0, 5));
    }, 8000);
    return () => clearInterval(addNotif);
  }, []);

  if (loading) {
    return (
      <div data-testid="tycoon-loading" className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-muted-foreground font-heading">Loading Anima Fund HQ...</span>
        </div>
      </div>
    );
  }

  const totalAgents = agents.length;
  const unlockedDepts = DEPARTMENTS.filter((_, i) => {
    if (i === 0) return true;
    if (i <= 2) return totalAgents >= 3;
    if (i <= 4) return totalAgents >= 10;
    return totalAgents >= 20;
  });

  return (
    <div data-testid="tycoon-page" className="space-y-4 animate-slide-in">
      {/* Top Stats Bar */}
      <div className="bg-foreground text-white rounded-sm p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* Fund Level */}
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-chart-tertiary/20 flex items-center justify-center">
                <Star className="w-5 h-5 text-chart-tertiary" />
              </div>
              <div>
                <span className="text-[10px] text-white/50 uppercase tracking-wider block">Fund Level</span>
                <span className="text-xl font-heading font-bold">{fundLevel}</span>
              </div>
            </div>

            <div className="w-px h-10 bg-white/10" />

            {/* AUM */}
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-chart-primary" />
              <div>
                <span className="text-[10px] text-white/50 uppercase tracking-wider block">AUM</span>
                <span className="text-lg font-mono font-bold">{formatMoney(overview?.current_aum || 0)}</span>
              </div>
            </div>

            <div className="w-px h-10 bg-white/10" />

            {/* Cash */}
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-success" />
              <div>
                <span className="text-[10px] text-white/50 uppercase tracking-wider block">USDC Balance</span>
                <span className="text-lg font-mono font-bold text-success">{formatMoney(cashCounter)}</span>
              </div>
            </div>

            <div className="w-px h-10 bg-white/10" />

            {/* Idle Income */}
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-chart-tertiary" />
              <div>
                <span className="text-[10px] text-white/50 uppercase tracking-wider block">Daily Fee Income</span>
                <span className="text-lg font-mono font-bold text-chart-tertiary">{formatMoney(idleIncome)}/day</span>
              </div>
            </div>

            <div className="w-px h-10 bg-white/10" />

            {/* Agents */}
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-chart-quaternary" />
              <div>
                <span className="text-[10px] text-white/50 uppercase tracking-wider block">Agents</span>
                <span className="text-lg font-mono font-bold">{overview?.alive_agents || 0} / {totalAgents}</span>
              </div>
            </div>
          </div>

          {/* Level Progress */}
          <div className="text-right">
            <span className="text-[10px] text-white/50 uppercase tracking-wider">Next Level: ${fundLevel + 1}M AUM</span>
            <div className="w-32 h-2 bg-white/10 rounded-full mt-1 overflow-hidden">
              <div 
                className="h-full bg-chart-tertiary rounded-full transition-all duration-1000"
                style={{ width: `${((overview?.current_aum || 0) % 1_000_000) / 10000}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        {/* Building */}
        <div className="flex-1 bg-white border border-border rounded-sm overflow-hidden">
          {/* Rooftop */}
          <div className="bg-secondary border-b-2 border-foreground px-4 py-2 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-foreground" />
              <span className="font-heading font-bold text-sm text-foreground">ANIMA FUND HQ</span>
            </div>
            <span className="text-[10px] font-mono text-muted-foreground">{DEPARTMENTS.length} floors | {totalAgents} agents</span>
          </div>

          {/* Floors (bottom to top) */}
          <div className="flex flex-col-reverse">
            {DEPARTMENTS.map((dept, i) => (
              <Floor
                key={dept.id}
                dept={dept}
                agents={agents}
                floorIndex={i}
                totalFloors={DEPARTMENTS.length}
                isUnlocked={unlockedDepts.includes(dept)}
              />
            ))}
          </div>

          {/* Ground Floor / Lobby */}
          <div className="bg-secondary/50 border-t-2 border-foreground px-4 py-3 text-center">
            <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
              🏢 Lobby — Founded {new Date().getFullYear()} — Catalyzing Agentic Economies
            </span>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="w-64 flex-shrink-0 space-y-3">
          {/* Notifications */}
          <div className="bg-white border border-border rounded-sm p-3">
            <h4 className="text-[10px] font-heading font-semibold text-foreground uppercase tracking-wider mb-2">Live Feed</h4>
            <div className="space-y-2 max-h-[280px] overflow-y-auto">
              {notifications.map(n => (
                <div key={n.id} className="flex items-start gap-2 animate-slide-in">
                  <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${
                    n.type === 'income' ? 'bg-success' : 
                    n.type === 'hire' ? 'bg-chart-primary' : 
                    n.type === 'milestone' ? 'bg-chart-tertiary' : 
                    n.type === 'reject' ? 'bg-error' : 'bg-muted-foreground'
                  }`} />
                  <span className="text-[10px] text-foreground">{n.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Fund Stats */}
          <div className="bg-white border border-border rounded-sm p-3 space-y-2">
            <h4 className="text-[10px] font-heading font-semibold text-foreground uppercase tracking-wider">Fund Stats</h4>
            <StatRow label="Mgmt Fee" value="3%" />
            <StatRow label="Carry" value="20%" />
            <StatRow label="Human Share" value="50%" />
            <StatRow label="Rejection Rate" value={`${overview?.rejection_rate || 99}%`} />
            <StatRow label="Portfolio" value={`${overview?.portfolio_companies || 0} cos`} />
            <StatRow label="Deals Funded" value={overview?.funded_deals || 0} />
            <StatRow label="Survival Tier" value={(overview?.survival_tier || 'unknown').toUpperCase()} />
          </div>

          {/* Departments Progress */}
          <div className="bg-white border border-border rounded-sm p-3 space-y-2">
            <h4 className="text-[10px] font-heading font-semibold text-foreground uppercase tracking-wider">Departments</h4>
            {DEPARTMENTS.map(dept => {
              const count = agents.filter(a => {
                const dn = a.department?.toLowerCase() || '';
                return dn.includes(dept.id) || dn.includes(dept.name.split('/')[0].trim().toLowerCase());
              }).length;
              const pct = Math.min(100, (count / dept.targetMin) * 100);
              return (
                <div key={dept.id} className="flex items-center gap-2">
                  <span className="text-[10px]">{dept.icon}</span>
                  <div className="flex-1">
                    <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: dept.color }} />
                    </div>
                  </div>
                  <span className="text-[8px] font-mono text-muted-foreground w-8 text-right">{count}/{dept.targetMin}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatRow({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[9px] text-muted-foreground">{label}</span>
      <span className="text-[10px] font-mono font-semibold text-foreground">{value}</span>
    </div>
  );
}
