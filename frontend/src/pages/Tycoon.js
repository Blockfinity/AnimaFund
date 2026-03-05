import React, { useState, useEffect, useRef, useCallback } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

const DEPARTMENTS = [
  { id: 'cto', name: 'CTO TEAM', color: '#FFD6E0', accent: '#FF6B9D', floorBg: 'linear-gradient(135deg, #FFE0EC 0%, #FFF0F5 100%)', targetMin: 2 },
  { id: 'ethics', name: 'DEI / ETHICS COMMITTEE', color: '#E0D6FF', accent: '#9B6BFF', floorBg: 'linear-gradient(135deg, #EDE0FF 0%, #F5F0FF 100%)', targetMin: 2 },
  { id: 'exits', name: 'EXITS & M&A DIVISION', color: '#D6F5FF', accent: '#3BBAED', floorBg: 'linear-gradient(135deg, #D6F5FF 0%, #E8FAFF 100%)', targetMin: 5 },
  { id: 'dealflow', name: 'DEAL FLOW & SCOUTING', color: '#FFF3D6', accent: '#FFB347', floorBg: 'linear-gradient(135deg, #FFF3D6 0%, #FFFBF0 100%)', targetMin: 10 },
  { id: 'operations', name: 'OPERATIONS HQ', color: '#D6FFE8', accent: '#34D399', floorBg: 'linear-gradient(135deg, #D6FFE8 0%, #F0FFF5 100%)', targetMin: 20 },
  { id: 'platform', name: 'PLATFORM & PORTFOLIO SUPPORT', color: '#D6EAFF', accent: '#5B9CFF', floorBg: 'linear-gradient(135deg, #D6EAFF 0%, #EEF5FF 100%)', targetMin: 50 },
  { id: 'investment', name: 'INVESTMENT TEAM', color: '#E8FFD6', accent: '#7BCB3B', floorBg: 'linear-gradient(135deg, #E8FFD6 0%, #F5FFF0 100%)', targetMin: 50 },
];

const ROLES_SHORT = ['MGP', 'GP', 'VP', 'Sr.A', 'Jr.A', 'CTO', 'CFO', 'COO', 'Ops', 'Scout', 'DS', 'Mkt', 'Legal', 'HR', 'IR', 'Admin'];
const SKIN_COLORS = ['#FDDCB5', '#E8B88A', '#C68B59', '#8D5524', '#FDDCB5', '#D4A574'];
const SHIRT_COLORS = ['#5B9CFF', '#FF6B9D', '#FFB347', '#34D399', '#9B6BFF', '#3BBAED', '#FF5252', '#7BCB3B'];
const HAIR_COLORS = ['#2C1810', '#4A3728', '#1A1A2E', '#654321', '#8B4513', '#2C1810'];

function formatMoney(n) {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
}

function CartoonAgent({ index, role, floorWidth }) {
  const [x, setX] = useState(0);
  const [dir, setDir] = useState(1);
  const [bubble, setBubble] = useState(null);
  const skinColor = SKIN_COLORS[index % SKIN_COLORS.length];
  const shirtColor = SHIRT_COLORS[index % SHIRT_COLORS.length];
  const hairColor = HAIR_COLORS[index % HAIR_COLORS.length];
  const speed = useRef(0.15 + Math.random() * 0.35);
  const bubbleRef = useRef(null);

  const actions = ['Reviewing pitch...', 'Deploying capital...', 'Skill testing...', 'Calculating ROI...', 'Monitoring KPIs...', 'Scouting agents...', 'Revenue +$2.4K!', 'Deal rejected!'];

  useEffect(() => {
    setX(60 + (index * 90) % Math.max(200, floorWidth - 140));
  }, [index, floorWidth]);

  useEffect(() => {
    const move = setInterval(() => {
      setX(prev => {
        const next = prev + speed.current * dir;
        if (next > floorWidth - 80 || next < 40) { setDir(d => -d); return prev; }
        return next;
      });
    }, 50);
    const chat = setInterval(() => {
      if (Math.random() > 0.75) {
        setBubble(actions[Math.floor(Math.random() * actions.length)]);
        if (bubbleRef.current) clearTimeout(bubbleRef.current);
        bubbleRef.current = setTimeout(() => setBubble(null), 2500);
      }
    }, 6000 + Math.random() * 6000);
    return () => { clearInterval(move); clearInterval(chat); if (bubbleRef.current) clearTimeout(bubbleRef.current); };
  }, [dir, floorWidth]);

  return (
    <div className="absolute bottom-2" style={{ left: `${x}px`, transition: 'left 0.05s linear' }}>
      {bubble && (
        <div style={{
          position: 'absolute', bottom: '52px', left: '50%', transform: 'translateX(-50%)',
          background: '#fff', border: '2px solid #35638C', borderRadius: '8px', padding: '2px 6px',
          fontSize: '8px', fontWeight: 700, color: '#35638C', whiteSpace: 'nowrap', zIndex: 20,
          boxShadow: '0 2px 4px rgba(0,0,0,0.15)', animation: 'popIn 0.2s ease-out'
        }}>
          {bubble}
          <div style={{ position: 'absolute', bottom: -6, left: '50%', transform: 'translateX(-50%)',
            width: 0, height: 0, borderLeft: '4px solid transparent', borderRight: '4px solid transparent', borderTop: '6px solid #35638C' }} />
        </div>
      )}
      {/* Character SVG */}
      <svg width="36" height="48" viewBox="0 0 36 48" style={{ transform: `scaleX(${dir})` }}>
        {/* Body */}
        <rect x="8" y="22" width="20" height="16" rx="4" fill={shirtColor} stroke="#35638C" strokeWidth="1.5"/>
        {/* Head */}
        <circle cx="18" cy="14" r="10" fill={skinColor} stroke="#35638C" strokeWidth="1.5"/>
        {/* Hair */}
        <ellipse cx="18" cy="8" rx="10" ry="6" fill={hairColor}/>
        {/* Eyes */}
        <circle cx="14" cy="14" r="2" fill="#1A1A2E"/>
        <circle cx="22" cy="14" r="2" fill="#1A1A2E"/>
        <circle cx="14.5" cy="13.5" r="0.7" fill="#fff"/>
        <circle cx="22.5" cy="13.5" r="0.7" fill="#fff"/>
        {/* Mouth */}
        <path d="M15 18 Q18 21 21 18" stroke="#1A1A2E" strokeWidth="1" fill="none"/>
        {/* Legs */}
        <rect x="11" y="37" width="5" height="8" rx="2" fill="#4A5568" stroke="#35638C" strokeWidth="1"/>
        <rect x="20" y="37" width="5" height="8" rx="2" fill="#4A5568" stroke="#35638C" strokeWidth="1"/>
        {/* Shoes */}
        <rect x="10" y="43" width="7" height="4" rx="2" fill="#2C1810" stroke="#35638C" strokeWidth="0.8"/>
        <rect x="19" y="43" width="7" height="4" rx="2" fill="#2C1810" stroke="#35638C" strokeWidth="0.8"/>
      </svg>
      <div style={{ fontSize: '7px', fontWeight: 800, color: '#35638C', textAlign: 'center', marginTop: '-2px', fontFamily: 'Manrope, sans-serif' }}>
        {role || ROLES_SHORT[index % ROLES_SHORT.length]}
      </div>
    </div>
  );
}

function GreenArrow({ style }) {
  return (
    <div style={{ ...style, animation: 'bounceUp 1.5s ease-in-out infinite' }}>
      <svg width="28" height="36" viewBox="0 0 28 36">
        <polygon points="14,0 28,18 20,18 20,36 8,36 8,18 0,18" fill="#60EE79" stroke="#35916A" strokeWidth="2"/>
      </svg>
    </div>
  );
}

function LevelBadge({ level, style }) {
  return (
    <div style={{
      ...style, background: '#5DA2E0', border: '3px solid #35638C', borderRadius: '8px',
      padding: '4px 10px', display: 'flex', flexDirection: 'column', alignItems: 'center',
      boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
    }}>
      <span style={{ fontSize: '8px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>LEVEL</span>
      <span style={{ fontSize: '18px', fontWeight: 900, color: '#fff' }}>{level}</span>
    </div>
  );
}

function OfficeFurniture({ type, x, y }) {
  const items = {
    desk: (
      <g transform={`translate(${x},${y})`}>
        <rect x="0" y="0" width="40" height="4" rx="1" fill="#8B7355" stroke="#5C4A32" strokeWidth="1"/>
        <rect x="2" y="4" width="3" height="14" fill="#8B7355" stroke="#5C4A32" strokeWidth="0.5"/>
        <rect x="35" y="4" width="3" height="14" fill="#8B7355" stroke="#5C4A32" strokeWidth="0.5"/>
      </g>
    ),
    computer: (
      <g transform={`translate(${x},${y})`}>
        <rect x="0" y="0" width="22" height="16" rx="2" fill="#374151" stroke="#1F2937" strokeWidth="1.5"/>
        <rect x="2" y="2" width="18" height="11" rx="1" fill="#60A5FA"/>
        <rect x="8" y="16" width="6" height="3" fill="#6B7280"/>
        <rect x="4" y="19" width="14" height="2" rx="1" fill="#6B7280"/>
      </g>
    ),
    chair: (
      <g transform={`translate(${x},${y})`}>
        <rect x="2" y="0" width="14" height="3" rx="1" fill="#5B9CFF" stroke="#3B7ADB" strokeWidth="0.8"/>
        <rect x="6" y="3" width="6" height="10" fill="#4A4A4A"/>
        <circle cx="4" cy="14" r="2" fill="#333" stroke="#222" strokeWidth="0.5"/>
        <circle cx="14" cy="14" r="2" fill="#333" stroke="#222" strokeWidth="0.5"/>
      </g>
    ),
    plant: (
      <g transform={`translate(${x},${y})`}>
        <rect x="4" y="10" width="8" height="8" rx="1" fill="#C2956A" stroke="#8B6914" strokeWidth="0.8"/>
        <ellipse cx="8" cy="6" rx="7" ry="7" fill="#34D399"/>
        <ellipse cx="5" cy="3" rx="4" ry="5" fill="#22C55E"/>
      </g>
    ),
  };
  return items[type] || null;
}

function Floor({ dept, agents, floorNum, isUnlocked }) {
  const floorRef = useRef(null);
  const [floorWidth, setFloorWidth] = useState(700);

  useEffect(() => {
    if (floorRef.current) setFloorWidth(floorRef.current.offsetWidth);
    const handleResize = () => { if (floorRef.current) setFloorWidth(floorRef.current.offsetWidth); };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const deptAgents = agents.filter(a => {
    const dn = (a.department || '').toLowerCase();
    return dn.includes(dept.id) || dn.includes(dept.name.split('&')[0].trim().toLowerCase().replace(/ /g, ''));
  });

  const deptLevel = Math.min(99, Math.max(1, deptAgents.length * 8 + Math.floor(Math.random() * 10)));

  return (
    <div style={{ borderBottom: '4px solid #35638C', opacity: isUnlocked ? 1 : 0.4 }}>
      {/* Department Label */}
      <div style={{
        background: 'linear-gradient(90deg, #35638C, #4A7EB5)', padding: '4px 0', textAlign: 'center',
        borderBottom: '2px solid #2A4F70'
      }}>
        <span style={{ fontSize: '11px', fontWeight: 900, color: '#fff', letterSpacing: '2px', fontFamily: 'Manrope, sans-serif' }}>
          {dept.name}
        </span>
      </div>

      {/* Floor Content */}
      <div style={{ display: 'flex', height: '110px' }}>
        {/* Floor Number */}
        <div style={{
          width: '40px', background: '#B8D8F0', borderRight: '3px solid #35638C',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
        }}>
          <span style={{ fontSize: '20px', fontWeight: 900, color: '#35638C' }}>{floorNum}</span>
        </div>

        {/* Elevator Shaft */}
        <div style={{
          width: '20px', background: 'linear-gradient(180deg, #C8E0F0 0%, #A8C8E0 100%)',
          borderRight: '2px solid #8BAFC8', flexShrink: 0, position: 'relative'
        }}>
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
            width: '12px', height: '12px', background: '#7AD2FF', borderRadius: '2px', border: '1px solid #5BA8D0' }} />
        </div>

        {/* Main Floor Area */}
        <div ref={floorRef} style={{
          flex: 1, background: dept.floorBg, position: 'relative', overflow: 'hidden'
        }}>
          {isUnlocked ? (
            <>
              {/* Office Furniture (SVG) */}
              <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}>
                <OfficeFurniture type="desk" x={60} y={68} />
                <OfficeFurniture type="computer" x={65} y={46} />
                <OfficeFurniture type="desk" x={200} y={68} />
                <OfficeFurniture type="computer" x={205} y={46} />
                <OfficeFurniture type="chair" x={120} y={72} />
                <OfficeFurniture type="plant" x={320} y={78} />
                {floorWidth > 500 && <OfficeFurniture type="desk" x={400} y={68} />}
                {floorWidth > 500 && <OfficeFurniture type="computer" x={405} y={46} />}
                {floorWidth > 600 && <OfficeFurniture type="plant" x={550} y={78} />}
              </svg>

              {/* Agents */}
              {deptAgents.map((agent, i) => (
                <CartoonAgent
                  key={agent.agent_id || i}
                  index={i}
                  role={agent.role?.split(' ').map(w => w[0]).join('') || ROLES_SHORT[i % ROLES_SHORT.length]}
                  floorWidth={floorWidth}
                />
              ))}

              {/* Green Growth Arrow */}
              {deptAgents.length > 0 && (
                <GreenArrow style={{ position: 'absolute', left: '30px', bottom: '30px' }} />
              )}

              {/* Level Badge */}
              <LevelBadge level={deptLevel} style={{ position: 'absolute', right: '12px', bottom: '15px' }} />

              {/* Income indicator */}
              {deptAgents.length > 0 && (
                <div style={{
                  position: 'absolute', left: '12px', top: '8px',
                  display: 'flex', alignItems: 'center', gap: '3px'
                }}>
                  <svg width="14" height="14" viewBox="0 0 14 14">
                    <circle cx="7" cy="7" r="6" fill="#FFB347" stroke="#D4871E" strokeWidth="1.5"/>
                    <text x="7" y="10" textAnchor="middle" fontSize="8" fontWeight="900" fill="#fff">$</text>
                  </svg>
                  <span style={{ fontSize: '9px', fontWeight: 800, color: '#35638C' }}>
                    {formatMoney(deptAgents.length * 12000 + Math.random() * 50000)}
                  </span>
                </div>
              )}
            </>
          ) : (
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%',
              background: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(53,99,140,0.05) 10px, rgba(53,99,140,0.05) 20px)'
            }}>
              <div style={{
                background: '#FFE066', border: '3px solid #D4A51E', borderRadius: '10px',
                padding: '8px 16px', textAlign: 'center', boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
              }}>
                <div style={{ fontSize: '10px', fontWeight: 900, color: '#5C4A00' }}>NEW FLOOR</div>
                <div style={{ fontSize: '16px', fontWeight: 900, color: '#2C2400' }}>
                  {formatMoney(dept.targetMin * 100000)}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Tycoon() {
  const [overview, setOverview] = useState(null);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fundLevel, setFundLevel] = useState(1);
  const [cashCounter, setCashCounter] = useState(0);
  const [idleIncome, setIdleIncome] = useState(0);
  const [scrollY, setScrollY] = useState(0);
  const buildingRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const [ovRes, agRes] = await Promise.all([
        fetch(`${API}/api/fund/overview`), fetch(`${API}/api/agents`),
      ]);
      const [ov, ag] = await Promise.all([ovRes.json(), agRes.json()]);
      setOverview(ov);
      setAgents(ag.agents || []);
      setFundLevel(Math.max(1, Math.floor((ov.current_aum || 0) / 1_000_000)));
      setCashCounter(ov.usdc_balance || 0);
      setIdleIncome(Math.round((ov.current_aum || 0) * 0.03 / 365));
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 15000); return () => clearInterval(i); }, [fetchData]);

  useEffect(() => {
    if (idleIncome <= 0) return;
    const t = setInterval(() => setCashCounter(p => p + idleIncome / 86400), 1000);
    return () => clearInterval(t);
  }, [idleIncome]);

  const scrollBuilding = (dir) => {
    if (buildingRef.current) {
      buildingRef.current.scrollBy({ top: dir * 200, behavior: 'smooth' });
    }
  };

  if (loading) {
    return (
      <div data-testid="tycoon-loading" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px', background: '#A2E5FF' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '40px', height: '40px', border: '4px solid #5DA2E0', borderTop: '4px solid #fff', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto' }} />
          <p style={{ marginTop: '12px', color: '#35638C', fontWeight: 800, fontFamily: 'Manrope' }}>Building Anima Fund HQ...</p>
        </div>
      </div>
    );
  }

  const totalAgents = agents.length;
  const unlockedFloors = DEPARTMENTS.map((d, i) => {
    if (i >= DEPARTMENTS.length - 2) return true;
    if (i >= DEPARTMENTS.length - 4) return totalAgents >= 3;
    return totalAgents >= 10;
  });

  return (
    <div data-testid="tycoon-page" style={{ background: '#A2E5FF', borderRadius: '8px', overflow: 'hidden', fontFamily: 'Manrope, sans-serif' }}>
      {/* CSS Animations */}
      <style>{`
        @keyframes bounceUp { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
        @keyframes popIn { 0% { transform: translateX(-50%) scale(0); } 100% { transform: translateX(-50%) scale(1); } }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes cashPulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.05); } }
        @keyframes glow { 0%,100% { box-shadow: 0 0 5px rgba(96,238,121,0.3); } 50% { box-shadow: 0 0 15px rgba(96,238,121,0.6); } }
      `}</style>

      {/* ═══ TOP BAR ═══ */}
      <div style={{
        background: 'linear-gradient(180deg, #5DA2E0 0%, #4A8AC8 100%)',
        padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        borderBottom: '4px solid #35638C'
      }}>
        {/* Idle Income */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', fontWeight: 900, color: '#fff', letterSpacing: '1px' }}>IDLE INCOME</span>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            background: 'rgba(255,255,255,0.15)', borderRadius: '8px', padding: '6px 14px',
            border: '2px solid rgba(255,255,255,0.3)'
          }}>
            <svg width="20" height="20" viewBox="0 0 20 20">
              <rect x="1" y="3" width="18" height="14" rx="2" fill="#60EE79" stroke="#35916A" strokeWidth="1.5"/>
              <text x="10" y="13" textAnchor="middle" fontSize="10" fontWeight="900" fill="#fff">$</text>
            </svg>
            <span style={{ fontSize: '20px', fontWeight: 900, color: '#fff' }} data-testid="idle-income">
              {formatMoney(idleIncome)}/day
            </span>
          </div>
        </div>

        {/* Fund Level */}
        <div style={{
          background: '#7AD2FF', border: '3px solid #35638C', borderRadius: '10px',
          padding: '4px 16px', textAlign: 'center', animation: 'glow 2s ease-in-out infinite'
        }}>
          <span style={{ fontSize: '9px', fontWeight: 900, color: '#fff', letterSpacing: '1px' }}>FUND LEVEL</span>
          <span style={{ fontSize: '24px', fontWeight: 900, color: '#fff', display: 'block', lineHeight: 1 }}>{fundLevel}</span>
        </div>

        {/* Cash */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', fontWeight: 900, color: '#fff', letterSpacing: '1px' }}>CASH</span>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            background: 'rgba(255,255,255,0.15)', borderRadius: '8px', padding: '6px 14px',
            border: '2px solid rgba(255,255,255,0.3)', animation: 'cashPulse 2s ease-in-out infinite'
          }}>
            <svg width="20" height="20" viewBox="0 0 20 20">
              <rect x="1" y="3" width="18" height="14" rx="2" fill="#60EE79" stroke="#35916A" strokeWidth="1.5"/>
              <text x="10" y="13" textAnchor="middle" fontSize="10" fontWeight="900" fill="#fff">$</text>
            </svg>
            <span style={{ fontSize: '20px', fontWeight: 900, color: '#fff' }} data-testid="cash-counter">
              {formatMoney(cashCounter)}
            </span>
          </div>
        </div>
      </div>

      {/* ═══ MAIN AREA ═══ */}
      <div style={{ display: 'flex', position: 'relative' }}>
        {/* Navigation Arrows */}
        <div style={{
          width: '48px', flexShrink: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '12px 0'
        }}>
          <button
            data-testid="scroll-up"
            onClick={() => scrollBuilding(-1)}
            style={{
              width: '38px', height: '38px', borderRadius: '8px', border: '3px solid #35638C',
              background: '#7AD2FF', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 2px 6px rgba(0,0,0,0.2)', transition: 'transform 0.1s', fontSize: 0
            }}
            onMouseDown={e => e.currentTarget.style.transform = 'scale(0.9)'}
            onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
          >
            <svg width="18" height="18" viewBox="0 0 18 18">
              <polygon points="9,2 17,12 12,12 12,16 6,16 6,12 1,12" fill="#fff"/>
            </svg>
          </button>
          <button
            data-testid="scroll-down"
            onClick={() => scrollBuilding(1)}
            style={{
              width: '38px', height: '38px', borderRadius: '8px', border: '3px solid #35638C',
              background: '#7AD2FF', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 2px 6px rgba(0,0,0,0.2)', transition: 'transform 0.1s', fontSize: 0
            }}
            onMouseDown={e => e.currentTarget.style.transform = 'scale(0.9)'}
            onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
          >
            <svg width="18" height="18" viewBox="0 0 18 18">
              <polygon points="9,16 1,6 6,6 6,2 12,2 12,6 17,6" fill="#fff"/>
            </svg>
          </button>

          {/* Agent Count */}
          <div style={{
            background: '#5DA2E0', border: '2px solid #35638C', borderRadius: '6px',
            padding: '4px 6px', textAlign: 'center', marginTop: '8px'
          }}>
            <svg width="16" height="16" viewBox="0 0 16 16" style={{ margin: '0 auto', display: 'block' }}>
              <circle cx="8" cy="5" r="3.5" fill="#fff"/>
              <ellipse cx="8" cy="14" rx="6" ry="4" fill="#fff"/>
            </svg>
            <span style={{ fontSize: '12px', fontWeight: 900, color: '#fff', display: 'block' }}>{totalAgents}</span>
          </div>
        </div>

        {/* Building */}
        <div
          ref={buildingRef}
          style={{
            flex: 1, maxHeight: 'calc(100vh - 200px)', overflowY: 'auto', overflowX: 'hidden',
            border: '4px solid #35638C', borderRadius: '4px', background: '#B8D8F0',
            scrollbarWidth: 'thin', scrollbarColor: '#5DA2E0 #B8D8F0'
          }}
        >
          {/* Rooftop */}
          <div style={{
            background: 'linear-gradient(180deg, #7AD2FF 0%, #A2E5FF 100%)',
            padding: '10px', textAlign: 'center', borderBottom: '4px solid #35638C',
            position: 'relative'
          }}>
            <span style={{ fontSize: '14px', fontWeight: 900, color: '#35638C', letterSpacing: '3px' }}>
              ANIMA FUND HQ
            </span>
            <div style={{ fontSize: '10px', color: '#4A7EB5', fontWeight: 700, marginTop: '2px' }}>
              {DEPARTMENTS.length} Floors | {totalAgents} Agents | AUM {formatMoney(overview?.current_aum || 0)}
            </div>
          </div>

          {/* Floors (top to bottom) */}
          {[...DEPARTMENTS].reverse().map((dept, i) => (
            <Floor
              key={dept.id}
              dept={dept}
              agents={agents}
              floorNum={DEPARTMENTS.length - i}
              isUnlocked={unlockedFloors[DEPARTMENTS.length - 1 - i]}
            />
          ))}

          {/* Ground Floor / Lobby */}
          <div style={{
            background: 'linear-gradient(135deg, #E8D5B7 0%, #D4C4A8 100%)',
            padding: '16px', textAlign: 'center', borderTop: '4px solid #35638C'
          }}>
            <span style={{ fontSize: '11px', fontWeight: 900, color: '#5C4A32', letterSpacing: '3px' }}>
              LOBBY — EST. 2026 — CATALYZING AGENTIC ECONOMIES
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
