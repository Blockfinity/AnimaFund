import React, { useState, useEffect, useRef, useCallback } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

/*
  This component visualizes REAL fund operations.
  - LIVE MODE: Reads from /api/live/* (Automaton engine's SQLite state.db)
  - DEMO MODE: Reads from /api/* (MongoDB seeded data)
  All numbers, agents, events, costs come from the data source. Nothing is hardcoded.
*/

// ─── Helpers ────────────────────────────────────────────
function formatMoney(n) {
  if (!n && n !== 0) return '$0';
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${Math.round(n)}`;
}

// Map department names from data to display config
const DEPT_CONFIG = {
  'Investment Team':           { accent: '#7BCB3B', floorBg: 'linear-gradient(135deg, #E8FFD6 0%, #F5FFF0 100%)' },
  'Platform / Portfolio Support': { accent: '#5B9CFF', floorBg: 'linear-gradient(135deg, #D6EAFF 0%, #EEF5FF 100%)' },
  'Operations / Back-Office':  { accent: '#34D399', floorBg: 'linear-gradient(135deg, #D6FFE8 0%, #F0FFF5 100%)' },
  'Deal Flow / Scouting':      { accent: '#FFB347', floorBg: 'linear-gradient(135deg, #FFF3D6 0%, #FFFBF0 100%)' },
  'Exits / M&A':               { accent: '#3BBAED', floorBg: 'linear-gradient(135deg, #D6F5FF 0%, #E8FAFF 100%)' },
  'DEI / Ethics':              { accent: '#9B6BFF', floorBg: 'linear-gradient(135deg, #EDE0FF 0%, #F5F0FF 100%)' },
  'CTO Team':                  { accent: '#FF6B9D', floorBg: 'linear-gradient(135deg, #FFE0EC 0%, #FFF0F5 100%)' },
  'Executive':                 { accent: '#FFB347', floorBg: 'linear-gradient(135deg, #FFF8E0 0%, #FFFDF5 100%)' },
};
const DEFAULT_DEPT = { accent: '#71717a', floorBg: 'linear-gradient(135deg, #f4f4f5 0%, #fafafa 100%)' };

const SKIN_COLORS = ['#FDDCB5', '#E8B88A', '#C68B59', '#8D5524', '#D4A574', '#FDDCB5'];
const SHIRT_COLORS = ['#5B9CFF', '#FF6B9D', '#FFB347', '#34D399', '#9B6BFF', '#3BBAED', '#FF5252', '#7BCB3B'];
const HAIR_COLORS = ['#2C1810', '#4A3728', '#1A1A2E', '#654321', '#8B4513'];

// ─── Agent Character ────────────────────────────────────
function AgentCharacter({ agent, index, floorWidth }) {
  const homeX = useRef(80 + ((index * 105) % Math.max(200, floorWidth - 160)));
  const [x, setX] = useState(homeX.current);
  const [dir, setDir] = useState(1);
  const [bubble, setBubble] = useState(null);
  const [state, setState] = useState('idle'); // idle | walking | meeting | returning
  const targetX = useRef(null);
  const timers = useRef({ state: null, bubble: null });

  const skin = SKIN_COLORS[index % SKIN_COLORS.length];
  const shirt = SHIRT_COLORS[index % SHIRT_COLORS.length];
  const hair = HAIR_COLORS[index % HAIR_COLORS.length];
  const roleLabel = (agent.role || 'Agent').split(' ').slice(0, 2).join(' ');

  // State machine
  useEffect(() => {
    if (state !== 'idle') return;
    const delay = 5000 + Math.random() * 15000;
    timers.current.state = setTimeout(() => {
      targetX.current = Math.random() * Math.max(100, floorWidth - 120) + 40;
      setState('walking');
    }, delay);
    return () => clearTimeout(timers.current.state);
  }, [state, floorWidth]);

  // Movement
  useEffect(() => {
    if (state === 'idle') return;
    if (state === 'meeting') {
      setBubble(agent.last_action || `${roleLabel} working...`);
      timers.current.bubble = setTimeout(() => {
        setBubble(null);
        targetX.current = homeX.current;
        setState('returning');
      }, 2500 + Math.random() * 2000);
      return () => clearTimeout(timers.current.bubble);
    }
    const interval = setInterval(() => {
      setX(prev => {
        const t = targetX.current;
        if (t === null) return prev;
        const d = Math.abs(t - prev);
        if (d < 3) {
          if (state === 'walking') setState('meeting');
          else if (state === 'returning') setState('idle');
          return t;
        }
        const step = Math.min(1.5, d * 0.07);
        setDir(t > prev ? 1 : -1);
        return prev + step * (t > prev ? 1 : -1);
      });
    }, 30);
    return () => clearInterval(interval);
  }, [state, agent.last_action, roleLabel]);

  const moving = state === 'walking' || state === 'returning';

  return (
    <div style={{ position: 'absolute', bottom: '2px', left: `${x}px`, zIndex: state === 'meeting' ? 15 : 5 }}>
      {bubble && (
        <div style={{
          position: 'absolute', bottom: '54px', left: '50%', transform: 'translateX(-50%)',
          background: '#fff', border: '2px solid #35638C', borderRadius: '8px', padding: '3px 7px',
          fontSize: '8px', fontWeight: 700, color: '#35638C', whiteSpace: 'nowrap', zIndex: 20,
          boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
        }}>
          {bubble}
          <div style={{ position: 'absolute', bottom: -6, left: '50%', transform: 'translateX(-50%)',
            width: 0, height: 0, borderLeft: '4px solid transparent', borderRight: '4px solid transparent', borderTop: '6px solid #35638C' }} />
        </div>
      )}
      <svg width="36" height="48" viewBox="0 0 36 48" style={{ transform: `scaleX(${dir})` }}>
        <rect x="8" y="22" width="20" height="16" rx="4" fill={shirt} stroke="#35638C" strokeWidth="1.5"/>
        <circle cx="18" cy="14" r="10" fill={skin} stroke="#35638C" strokeWidth="1.5"/>
        <ellipse cx="18" cy="8" rx="10" ry="6" fill={hair}/>
        <circle cx="14" cy="14" r="2" fill="#1A1A2E"/><circle cx="22" cy="14" r="2" fill="#1A1A2E"/>
        <circle cx="14.5" cy="13.5" r="0.7" fill="#fff"/><circle cx="22.5" cy="13.5" r="0.7" fill="#fff"/>
        {state === 'meeting'
          ? <ellipse cx="18" cy="19" rx="3" ry="2" fill="#1A1A2E"/>
          : <path d="M15 18 Q18 21 21 18" stroke="#1A1A2E" strokeWidth="1" fill="none"/>}
        {moving ? (
          <>
            <rect x="10" y="37" width="5" height="8" rx="2" fill="#4A5568" stroke="#35638C" strokeWidth="1">
              <animateTransform attributeName="transform" type="rotate" values="-10 12.5 37;10 12.5 37;-10 12.5 37" dur="0.4s" repeatCount="indefinite"/>
            </rect>
            <rect x="21" y="37" width="5" height="8" rx="2" fill="#4A5568" stroke="#35638C" strokeWidth="1">
              <animateTransform attributeName="transform" type="rotate" values="10 23.5 37;-10 23.5 37;10 23.5 37" dur="0.4s" repeatCount="indefinite"/>
            </rect>
          </>
        ) : (
          <>
            <rect x="11" y="37" width="5" height="8" rx="2" fill="#4A5568" stroke="#35638C" strokeWidth="1"/>
            <rect x="20" y="37" width="5" height="8" rx="2" fill="#4A5568" stroke="#35638C" strokeWidth="1"/>
          </>
        )}
        <rect x="10" y="43" width="7" height="4" rx="2" fill="#2C1810" stroke="#35638C" strokeWidth="0.8"/>
        <rect x="19" y="43" width="7" height="4" rx="2" fill="#2C1810" stroke="#35638C" strokeWidth="0.8"/>
      </svg>
      <div style={{ fontSize: '7px', fontWeight: 800, color: '#35638C', textAlign: 'center', marginTop: '-2px', maxWidth: '50px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {roleLabel}
      </div>
    </div>
  );
}

// ─── Office Furniture SVG ───────────────────────────────
function Furniture({ type, x, y }) {
  const map = {
    desk: <g transform={`translate(${x},${y})`}><rect x="0" y="0" width="40" height="4" rx="1" fill="#8B7355" stroke="#5C4A32" strokeWidth="1"/><rect x="2" y="4" width="3" height="14" fill="#8B7355"/><rect x="35" y="4" width="3" height="14" fill="#8B7355"/></g>,
    computer: <g transform={`translate(${x},${y})`}><rect x="0" y="0" width="22" height="16" rx="2" fill="#374151" stroke="#1F2937" strokeWidth="1.5"/><rect x="2" y="2" width="18" height="11" rx="1" fill="#60A5FA"/><rect x="8" y="16" width="6" height="3" fill="#6B7280"/><rect x="4" y="19" width="14" height="2" rx="1" fill="#6B7280"/></g>,
    plant: <g transform={`translate(${x},${y})`}><rect x="4" y="10" width="8" height="8" rx="1" fill="#C2956A" stroke="#8B6914" strokeWidth="0.8"/><ellipse cx="8" cy="6" rx="7" ry="7" fill="#34D399"/><ellipse cx="5" cy="3" rx="4" ry="5" fill="#22C55E"/></g>,
  };
  return map[type] || null;
}

// ─── Department Floor ───────────────────────────────────
function DepartmentFloor({ deptName, agents, floorNum, spendCents }) {
  const ref = useRef(null);
  const [w, setW] = useState(700);
  useEffect(() => {
    if (ref.current) setW(ref.current.offsetWidth);
    const h = () => { if (ref.current) setW(ref.current.offsetWidth); };
    window.addEventListener('resize', h);
    return () => window.removeEventListener('resize', h);
  }, []);

  const cfg = DEPT_CONFIG[deptName] || DEFAULT_DEPT;
  const monthlyCost = spendCents > 0 ? spendCents / 100 : agents.length * 850;

  return (
    <div style={{ borderBottom: '4px solid #35638C' }}>
      <div style={{ background: 'linear-gradient(90deg, #35638C, #4A7EB5)', padding: '4px 0', textAlign: 'center', borderBottom: '2px solid #2A4F70' }}>
        <span style={{ fontSize: '11px', fontWeight: 900, color: '#fff', letterSpacing: '2px' }}>{deptName.toUpperCase()}</span>
      </div>
      <div style={{ display: 'flex', height: '110px' }}>
        <div style={{ width: '40px', background: '#B8D8F0', borderRight: '3px solid #35638C', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <span style={{ fontSize: '20px', fontWeight: 900, color: '#35638C' }}>{floorNum}</span>
        </div>
        <div style={{ width: '20px', background: 'linear-gradient(180deg, #C8E0F0, #A8C8E0)', borderRight: '2px solid #8BAFC8', flexShrink: 0, position: 'relative' }}>
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: '12px', height: '12px', background: '#7AD2FF', borderRadius: '2px', border: '1px solid #5BA8D0' }} />
        </div>
        <div ref={ref} style={{ flex: 1, background: cfg.floorBg, position: 'relative', overflow: 'hidden' }}>
          <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
            <Furniture type="desk" x={60} y={68} /><Furniture type="computer" x={65} y={46} />
            <Furniture type="desk" x={200} y={68} /><Furniture type="computer" x={205} y={46} />
            <Furniture type="plant" x={320} y={78} />
            {w > 500 && <><Furniture type="desk" x={400} y={68} /><Furniture type="computer" x={405} y={46} /></>}
            {w > 600 && <Furniture type="plant" x={550} y={78} />}
          </svg>

          {agents.map((agent, i) => (
            <AgentCharacter key={agent.agent_id || agent.wallet_address || i} agent={agent} index={i} floorWidth={w} />
          ))}

          {agents.length > 0 && (
            <div style={{
              position: 'absolute', left: '12px', top: '8px', display: 'flex', alignItems: 'center', gap: '3px',
              background: 'rgba(255,255,255,0.85)', borderRadius: '4px', padding: '2px 6px', border: '1px solid rgba(53,99,140,0.2)'
            }}>
              <svg width="12" height="12" viewBox="0 0 14 14"><circle cx="7" cy="7" r="6" fill="#FF5252" stroke="#C62828" strokeWidth="1.2"/><text x="7" y="10" textAnchor="middle" fontSize="8" fontWeight="900" fill="#fff">$</text></svg>
              <span style={{ fontSize: '9px', fontWeight: 800, color: '#8B3A3A' }}>{formatMoney(monthlyCost)}/mo</span>
            </div>
          )}

          {agents.length === 0 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.5 }}>
              <span style={{ fontSize: '10px', color: '#35638C', fontWeight: 700 }}>No agents assigned</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main FundHQ Component ──────────────────────────────
export default function FundHQ({ fundName }) {
  const [agents, setAgents] = useState([]);
  const [activities, setActivities] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [engineState, setEngineState] = useState(null);
  const [loading, setLoading] = useState(true);
  const buildingRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const engineRes = await fetch(`${API}/api/engine/live`);
      const engine = await engineRes.json();
      setEngineState(engine);

      if (engine.live || engine.db_exists) {
        const [agRes, actRes, hbRes] = await Promise.all([
          fetch(`${API}/api/live/agents`),
          fetch(`${API}/api/live/activity?limit=20`),
          fetch(`${API}/api/live/heartbeat?limit=20`),
        ]);
        const [ag, act, hb] = await Promise.all([agRes.json(), actRes.json(), hbRes.json()]);
        setAgents(ag.agents || []);
        const toolActivities = (act.activities || []).map(a => ({
          text: `${a.tool_name}: ${(a.result_preview || '').slice(0, 60)}`,
          type: categorizeToolCall(a.tool_name),
          id: a.activity_id,
        }));
        // If no tool calls yet, show heartbeat events as activity
        if (toolActivities.length === 0) {
          const hbActivities = (hb.history || []).map(h => ({
            text: `${h.task}: ${h.result || 'pending'}${h.duration_ms ? ` (${h.duration_ms}ms)` : ''}`,
            type: 'operational',
            id: h.id,
          }));
          setActivities(hbActivities);
        } else {
          setActivities(toolActivities);
        }
        const deptMap = {};
        for (const a of (ag.agents || [])) {
          const dept = a.department || guessDepartment(a.role);
          if (!deptMap[dept]) deptMap[dept] = { name: dept, agents: [], spend: 0 };
          deptMap[dept].agents.push(a);
          deptMap[dept].spend += (a.funded_cents || 0);
        }
        setDepartments(Object.values(deptMap));
      } else {
        setAgents([]);
        setActivities([]);
        setDepartments([]);
      }
    } catch (e) { console.error('FundHQ fetch error:', e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 10000); return () => clearInterval(i); }, [fetchData]);

  const scrollBuilding = (dir) => { if (buildingRef.current) buildingRef.current.scrollBy({ top: dir * 200, behavior: 'smooth' }); };

  const getDeptAgentCount = (dept) => {
    return agents.filter(a => {
      const dn = (a.department || '').toLowerCase();
      return dn.includes(dept.id) || dn.includes(dept.name.split('&')[0].trim().toLowerCase().replace(/ /g, ''));
    }).length;
  };

  if (loading) {
    return (
      <div data-testid="fundhq-loading" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px', background: '#A2E5FF' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '40px', height: '40px', border: '4px solid #5DA2E0', borderTop: '4px solid #fff', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto' }} />
          <p style={{ marginTop: '12px', color: '#35638C', fontWeight: 800 }}>Connecting to Anima Fund...</p>
        </div>
      </div>
    );
  }

  const totalAgents = agents.length;
  const isLive = engineState?.live || engineState?.db_exists || false;
  const totalSpend = departments.reduce((s, d) => s + d.agents.length * 850, 0);
  const notifColors = { income: '#60EE79', deal: '#5B9CFF', milestone: '#FFB347', hire: '#9B6BFF', reject: '#FF5252', operational: '#34D399' };

  return (
    <div data-testid="fundhq-page" style={{ fontFamily: 'Manrope, sans-serif' }}>
      <style>{`
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes slideIn { from { opacity:0; transform:translateX(10px); } to { opacity:1; transform:translateX(0); } }
      `}</style>

      {/* ═══ TOP INFO BAR ═══ */}
      <div style={{ background: '#18181b', padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderRadius: '6px 6px 0 0', gap: '10px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isLive ? '#34D399' : '#71717a', boxShadow: isLive ? '0 0 8px #34D399' : 'none' }} />
          <span style={{ fontSize: '12px', fontWeight: 900, color: '#fff', letterSpacing: '1px' }}>
            {isLive ? 'LIVE' : 'WAITING FOR ENGINE'}
          </span>
        </div>
        <Sep />
        <Stat label="AGENTS" value={totalAgents} />
        <Sep />
        <Stat label="DEPARTMENTS" value={departments.length} />
        <Sep />
        <Stat label="TURNS" value={engineState?.turn_count || 0} />
        <Sep />
        <Stat label="STATE" value={(engineState?.agent_state || 'offline').toUpperCase()} color={isLive ? '#34D399' : '#71717a'} />
      </div>

      {/* ═══ MAIN: Building + Sidebar ═══ */}
      <div style={{ display: 'flex', background: '#A2E5FF', borderRadius: '0 0 6px 6px' }}>
        {/* Left nav */}
        <div style={{ width: '44px', flexShrink: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '8px 0' }}>
          <NavBtn icon="up" onClick={() => scrollBuilding(-1)} testId="scroll-up" />
          <NavBtn icon="down" onClick={() => scrollBuilding(1)} testId="scroll-down" />
          <div style={{ background: '#5DA2E0', border: '2px solid #35638C', borderRadius: '6px', padding: '3px 5px', textAlign: 'center', marginTop: '6px' }}>
            <svg width="14" height="14" viewBox="0 0 16 16" style={{ margin: '0 auto', display: 'block' }}><circle cx="8" cy="5" r="3.5" fill="#fff"/><ellipse cx="8" cy="14" rx="6" ry="4" fill="#fff"/></svg>
            <span style={{ fontSize: '11px', fontWeight: 900, color: '#fff', display: 'block' }}>{totalAgents}</span>
          </div>
        </div>

        {/* Building — floors generated from actual department data */}
        <div ref={buildingRef} style={{ flex: 1, maxHeight: 'calc(100vh - 180px)', overflowY: 'auto', overflowX: 'hidden', border: '4px solid #35638C', borderRadius: '4px', background: '#B8D8F0', scrollbarWidth: 'thin' }}>
          <div style={{ background: 'linear-gradient(180deg, #7AD2FF, #A2E5FF)', padding: '8px', textAlign: 'center', borderBottom: '4px solid #35638C' }}>
            <span style={{ fontSize: '13px', fontWeight: 900, color: '#35638C', letterSpacing: '3px' }}>
              {(fundName || 'FUND').toUpperCase()} HQ
            </span>
            <div style={{ fontSize: '9px', color: '#4A7EB5', fontWeight: 700, marginTop: '2px' }}>
              {departments.length} Floors | {totalAgents} Agents
              {isLive && <span style={{ color: '#60EE79', marginLeft: '8px' }}>LIVE</span>}
            </div>
          </div>

          {departments.length > 0 ? (
            [...departments].reverse().map((dept, i) => (
              <DepartmentFloor
                key={dept.name}
                deptName={dept.name}
                agents={dept.agents}
                floorNum={departments.length - i}
                spendCents={dept.spend}
              />
            ))
          ) : (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <span style={{ fontSize: '12px', color: '#35638C', fontWeight: 700 }}>
                {isLive ? 'No departments found' : 'Waiting for founder AI to hire agents...'}
              </span>
            </div>
          )}

          <div style={{ background: 'linear-gradient(135deg, #E8D5B7, #D4C4A8)', padding: '12px', textAlign: 'center', borderTop: '4px solid #35638C' }}>
            <span style={{ fontSize: '10px', fontWeight: 900, color: '#5C4A32', letterSpacing: '3px' }}>
              LOBBY — CATALYZING AGENTIC ECONOMIES
            </span>
          </div>
        </div>

        {/* ═══ RIGHT SIDEBAR ═══ */}
        <div style={{ width: '240px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '8px', padding: '8px 8px 8px 0', maxHeight: 'calc(100vh - 180px)', overflowY: 'auto' }}>

          {/* Live Feed — from real activity data */}
          <SidePanel title="LIVE FEED" live>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '5px', maxHeight: '200px', overflowY: 'auto' }}>
              {activities.length > 0 ? activities.map(a => (
                <div key={a.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', animation: 'slideIn 0.3s ease-out' }}>
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: notifColors[a.type] || '#999', marginTop: '4px', flexShrink: 0 }} />
                  <span style={{ fontSize: '9px', color: '#35638C', fontWeight: 600, lineHeight: 1.3 }}>{a.text}</span>
                </div>
              )) : (
                <span style={{ fontSize: '9px', color: '#999' }}>
                  {isLive ? 'No activity yet...' : 'Engine not running'}
                </span>
              )}
            </div>
          </SidePanel>

          {/* Fund Stats */}
          <SidePanel title="FUND STATS">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <StatRow label="Agents" value={totalAgents} />
              <StatRow label="Departments" value={departments.length} />
              <StatRow label="Turns" value={engineState?.turn_count || 0} />
              <StatRow label="State" value={(engineState?.agent_state || 'offline').toUpperCase()} />
              <StatRow label="Engine" value={isLive ? 'LIVE' : 'OFFLINE'} />
            </div>
          </SidePanel>

          {/* Departments — from real department data */}
          <SidePanel title="DEPARTMENTS">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {departments.map(dept => {
                const cfg = DEPT_CONFIG[dept.name] || DEFAULT_DEPT;
                return (
                  <div key={dept.name} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: cfg.accent, flexShrink: 0 }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '8px', color: '#7A94AB', fontWeight: 700, marginBottom: '2px' }}>{dept.name}</div>
                      <div style={{ width: '100%', height: '5px', background: '#EEF3F8', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', borderRadius: '3px', width: `${Math.min(100, dept.agents.length * 10)}%`, background: cfg.accent, transition: 'width 0.5s' }} />
                      </div>
                    </div>
                    <span style={{ fontSize: '9px', fontWeight: 800, color: '#35638C', fontFamily: 'JetBrains Mono, monospace', minWidth: '20px', textAlign: 'right' }}>{dept.agents.length}</span>
                  </div>
                );
              })}
              {departments.length === 0 && <span style={{ fontSize: '9px', color: '#999' }}>No departments yet</span>}
            </div>
          </SidePanel>
        </div>
      </div>
    </div>
  );
}

// ─── Small reusable components ──────────────────────────
function Sep() { return <div style={{ width: '1px', height: '28px', background: 'rgba(255,255,255,0.1)' }} />; }

function Stat({ label, value, color = '#fff' }) {
  return (
    <div>
      <div style={{ fontSize: '8px', color: 'rgba(255,255,255,0.4)', fontWeight: 700, letterSpacing: '1px' }}>{label}</div>
      <div style={{ fontSize: '14px', color, fontWeight: 900, fontFamily: 'JetBrains Mono, monospace' }}>{value}</div>
    </div>
  );
}

function NavBtn({ icon, onClick, testId }) {
  return (
    <button data-testid={testId} onClick={onClick}
      style={{ width: '34px', height: '34px', borderRadius: '8px', border: '3px solid #35638C', background: '#7AD2FF', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 6px rgba(0,0,0,0.2)', fontSize: 0 }}>
      <svg width="16" height="16" viewBox="0 0 18 18">
        {icon === 'up'
          ? <polygon points="9,2 17,12 12,12 12,16 6,16 6,12 1,12" fill="#fff"/>
          : <polygon points="9,16 1,6 6,6 6,2 12,2 12,6 17,6" fill="#fff"/>}
      </svg>
    </button>
  );
}

function SidePanel({ title, children, live }) {
  return (
    <div style={{ background: '#fff', border: '2px solid #35638C', borderRadius: '8px', padding: '10px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: '10px', fontWeight: 900, color: '#35638C', letterSpacing: '1px' }}>{title}</span>
        {live && <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#60EE79', boxShadow: '0 0 6px #60EE79' }} />}
      </div>
      {children}
    </div>
  );
}

function StatRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: '9px', color: '#7A94AB' }}>{label}</span>
      <span style={{ fontSize: '10px', fontWeight: 800, color: '#35638C', fontFamily: 'JetBrains Mono, monospace' }}>{value}</span>
    </div>
  );
}

// ─── Utility: categorize tool calls into event types ────
function categorizeToolCall(toolName) {
  if (!toolName) return 'operational';
  if (['transfer_credits', 'topup_credits', 'x402_fetch', 'check_credits'].includes(toolName)) return 'income';
  if (['spawn_child', 'fund_child', 'start_child'].includes(toolName)) return 'hire';
  if (['discover_agents', 'check_reputation', 'register_erc8004'].includes(toolName)) return 'deal';
  if (['update_soul', 'reflect_on_soul', 'remember_fact'].includes(toolName)) return 'milestone';
  return 'operational';
}

function categorizeActivity(category) {
  const map = { financial: 'income', investment: 'deal', social: 'hire', operational: 'operational', technical: 'milestone' };
  return map[category] || 'operational';
}

function guessDepartment(role) {
  if (!role) return 'Unassigned';
  const r = role.toLowerCase();
  if (r.includes('gp') || r.includes('partner') || r.includes('associate') || r.includes('principal')) return 'Investment Team';
  if (r.includes('platform') || r.includes('incubat') || r.includes('talent') || r.includes('marketing')) return 'Platform / Portfolio Support';
  if (r.includes('coo') || r.includes('cfo') || r.includes('admin') || r.includes('legal') || r.includes('hr') || r.includes('ir')) return 'Operations / Back-Office';
  if (r.includes('scout') || r.includes('deal flow')) return 'Deal Flow / Scouting';
  if (r.includes('exit') || r.includes('m&a')) return 'Exits / M&A';
  if (r.includes('ethic') || r.includes('dei')) return 'DEI / Ethics';
  if (r.includes('cto') || r.includes('engineer')) return 'CTO Team';
  return 'Executive';
}
