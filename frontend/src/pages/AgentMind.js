import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Brain, Terminal, Wrench, DollarSign, AlertTriangle, Clock, Cpu, Eye, ChevronDown, ChevronRight, Search } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

/*
  AGENT MIND — Real-time view of everything the agent is thinking and doing.

  LIVE MODE: Reads from /api/live/turns (full reasoning + tool calls from state.db)
  DEMO MODE: Reads from /api/activity (seeded MongoDB activity data) and formats as turns

  This is not a summary or dashboard — it's the raw stream of consciousness.
*/

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

function ToolCallBlock({ tc, isExpanded, onToggle }) {
  const hasError = !!tc.error;
  const duration = tc.duration_ms ? `${tc.duration_ms}ms` : '';

  return (
    <div style={{ borderLeft: `3px solid ${hasError ? '#FF5252' : '#34D399'}`, marginLeft: '16px', marginBottom: '4px' }}>
      {/* Tool header */}
      <button onClick={onToggle} data-testid={`tool-call-${tc.id || tc.tool}`}
        style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 8px', background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left' }}>
        {isExpanded ? <ChevronDown className="w-3 h-3" style={{ color: '#71717a', flexShrink: 0 }} /> : <ChevronRight className="w-3 h-3" style={{ color: '#71717a', flexShrink: 0 }} />}
        <Wrench className="w-3 h-3" style={{ color: hasError ? '#FF5252' : '#34D399', flexShrink: 0 }} />
        <span style={{ fontSize: '12px', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: hasError ? '#FF5252' : '#16a34a' }}>
          {tc.tool || tc.tool_used}
        </span>
        {duration && <span style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#71717a' }}>{duration}</span>}
        {hasError && <AlertTriangle className="w-3 h-3" style={{ color: '#FF5252', flexShrink: 0 }} />}
      </button>

      {/* Expanded details */}
      {isExpanded && (
        <div style={{ padding: '4px 8px 8px 24px' }}>
          {/* Arguments */}
          {tc.arguments && Object.keys(tc.arguments).length > 0 && (
            <div style={{ marginBottom: '6px' }}>
              <span style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '0.5px' }}>ARGS</span>
              <pre style={{
                fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#d4d4d8',
                background: '#1e1e2e', borderRadius: '4px', padding: '6px 8px', margin: '2px 0 0 0',
                overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '120px', overflowY: 'auto'
              }}>
                {JSON.stringify(tc.arguments, null, 2)}
              </pre>
            </div>
          )}
          {/* Result */}
          {(tc.result || tc.result_preview) && (
            <div>
              <span style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '0.5px' }}>
                {hasError ? 'ERROR' : 'RESULT'}
              </span>
              <pre style={{
                fontSize: '10px', fontFamily: 'JetBrains Mono, monospace',
                color: hasError ? '#FF5252' : '#a1a1aa',
                background: '#1e1e2e', borderRadius: '4px', padding: '6px 8px', margin: '2px 0 0 0',
                overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '200px', overflowY: 'auto'
              }}>
                {tc.error || (tc.result || tc.result_preview || '').slice(0, 1000)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TurnBlock({ turn, index }) {
  const [expanded, setExpanded] = useState(index < 3);
  const [expandedTools, setExpandedTools] = useState({});
  const toolCalls = turn.tool_calls || [];
  const thinking = turn.thinking || '';
  const cost = turn.cost_cents ? `$${(turn.cost_cents / 100).toFixed(4)}` : '';
  const tokens = turn.token_usage || {};
  const totalTokens = tokens.totalTokens || tokens.total_tokens || 0;

  const toggleTool = (id) => setExpandedTools(prev => ({ ...prev, [id]: !prev[id] }));

  const stateColors = {
    running: '#34D399', sleeping: '#5B9CFF', waking: '#FFB347',
    low_compute: '#d97706', critical: '#FF5252', dead: '#71717a',
  };

  return (
    <div data-testid={`turn-${turn.turn_id || index}`}
      style={{ borderBottom: '1px solid #27272a', padding: '12px 0' }}>
      {/* Turn header */}
      <button onClick={() => setExpanded(!expanded)}
        style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', padding: '0' }}>
        {expanded ? <ChevronDown className="w-4 h-4" style={{ color: '#71717a' }} /> : <ChevronRight className="w-4 h-4" style={{ color: '#71717a' }} />}
        <div style={{
          width: '6px', height: '6px', borderRadius: '50%', flexShrink: 0,
          background: stateColors[turn.state] || '#71717a'
        }} />
        <span style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace', color: '#a1a1aa' }}>
          Turn {turn.turn_id ? turn.turn_id.slice(-6) : index + 1}
        </span>
        <span style={{ fontSize: '10px', color: '#52525b' }}>{timeAgo(turn.timestamp)}</span>
        {turn.state && (
          <span style={{
            fontSize: '9px', fontWeight: 700, padding: '1px 6px', borderRadius: '3px',
            background: `${stateColors[turn.state] || '#71717a'}20`,
            color: stateColors[turn.state] || '#71717a',
          }}>{turn.state}</span>
        )}
        {toolCalls.length > 0 && (
          <span style={{ fontSize: '9px', color: '#71717a', fontFamily: 'JetBrains Mono, monospace' }}>
            {toolCalls.length} tool{toolCalls.length > 1 ? 's' : ''}
          </span>
        )}
        {cost && <span style={{ fontSize: '9px', color: '#FFB347', fontFamily: 'JetBrains Mono, monospace' }}>{cost}</span>}
        {totalTokens > 0 && <span style={{ fontSize: '9px', color: '#52525b', fontFamily: 'JetBrains Mono, monospace' }}>{totalTokens.toLocaleString()} tok</span>}
      </button>

      {expanded && (
        <div style={{ marginTop: '8px', paddingLeft: '20px' }}>
          {/* Thinking */}
          {thinking && (
            <div style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                <Brain className="w-3 h-3" style={{ color: '#9B6BFF' }} />
                <span style={{ fontSize: '9px', color: '#9B6BFF', fontWeight: 700, letterSpacing: '0.5px' }}>THINKING</span>
              </div>
              <div style={{
                fontSize: '11px', lineHeight: 1.5, color: '#d4d4d8',
                background: '#1a1a2e', borderRadius: '4px', padding: '8px 10px', borderLeft: '3px solid #9B6BFF',
                maxHeight: '200px', overflowY: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word'
              }}>
                {thinking}
              </div>
            </div>
          )}

          {/* Input (if present) */}
          {turn.input && (
            <div style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                <Eye className="w-3 h-3" style={{ color: '#5B9CFF' }} />
                <span style={{ fontSize: '9px', color: '#5B9CFF', fontWeight: 700, letterSpacing: '0.5px' }}>INPUT</span>
              </div>
              <div style={{
                fontSize: '11px', color: '#a1a1aa', background: '#1a1a2e', borderRadius: '4px',
                padding: '6px 10px', borderLeft: '3px solid #5B9CFF', maxHeight: '100px', overflowY: 'auto',
                whiteSpace: 'pre-wrap', wordBreak: 'break-word'
              }}>
                {turn.input.slice(0, 500)}
              </div>
            </div>
          )}

          {/* Tool calls */}
          {toolCalls.length > 0 && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                <Wrench className="w-3 h-3" style={{ color: '#34D399' }} />
                <span style={{ fontSize: '9px', color: '#34D399', fontWeight: 700, letterSpacing: '0.5px' }}>ACTIONS</span>
              </div>
              {toolCalls.map((tc, i) => (
                <ToolCallBlock
                  key={tc.id || i}
                  tc={tc}
                  isExpanded={expandedTools[tc.id || i] || false}
                  onToggle={() => toggleTool(tc.id || i)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AgentMind() {
  const [turns, setTurns] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('all');
  const [engineState, setEngineState] = useState(null);
  const [demoMode, setDemoMode] = useState(true);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [soul, setSoul] = useState(null);
  const [stats, setStats] = useState(null);
  const feedRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const engineRes = await fetch(`${API}/api/engine/live`);
      const engine = await engineRes.json();
      setEngineState(engine);

      // Always fetch agent list for the selector
      if (!demoMode && engine.live) {
        const [agRes, turnsRes, soulRes] = await Promise.all([
          fetch(`${API}/api/live/agents`),
          fetch(`${API}/api/live/turns?limit=100`),
          fetch(`${API}/api/live/soul`),
        ]);
        const [agData, turnsData, soulData] = await Promise.all([agRes.json(), turnsRes.json(), soulRes.json()]);
        const liveAgents = (agData.agents || []).map(a => ({
          id: a.agent_id, name: a.name, role: a.role, status: a.status,
          wallet: a.wallet_address, sandbox: a.sandbox_id,
        }));
        // Add founder as first entry
        liveAgents.unshift({ id: 'founder', name: engine.fund_name || 'Founder AI', role: 'Founder AI', status: engine.agent_state, wallet: '', sandbox: '' });
        setAgents(liveAgents);
        setTurns(turnsData.turns || []);
        setSoul(soulData.content || null);
        setStats({ total_turns: turnsData.total || 0, source: 'engine', agent_state: engine.agent_state, turn_count: engine.turn_count });
      } else {
        // DEMO: fetch agents + activity
        const [agRes, actRes] = await Promise.all([
          fetch(`${API}/api/agents`),
          fetch(`${API}/api/activity?limit=50`),
        ]);
        const [agData, actData] = await Promise.all([agRes.json(), actRes.json()]);

        // Build agent list from data, labeled by role
        const agentMap = {};
        for (const a of (agData.agents || [])) {
          agentMap[a.name] = { id: a.agent_id, name: a.name, role: a.role, department: a.department, status: a.status };
        }
        setAgents(Object.values(agentMap));

        // Build demo turns from activity, tagged with agent_name
        const demoTurns = (actData.activities || []).map((a, i) => ({
          turn_id: a.activity_id || `demo-${i}`,
          timestamp: a.timestamp,
          state: 'running',
          input: null,
          agent_name: a.agent_name,
          thinking: `${a.description}`,
          tool_calls: [{
            id: `tc-${i}`, tool: a.tool_used, arguments: {},
            result: a.description,
            duration_ms: Math.floor(Math.random() * 2000) + 100, error: null,
          }],
          token_usage: { totalTokens: Math.floor(Math.random() * 3000) + 500 },
          cost_cents: Math.floor(Math.random() * 50) + 5,
        }));
        setTurns(demoTurns);
        setSoul(null);
        setStats({ total_turns: demoTurns.length, source: 'demo', agent_state: 'demo', turn_count: demoTurns.length });
      }
    } catch (e) { console.error('AgentMind fetch error:', e); }
    finally { setLoading(false); }
  }, [demoMode]);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 5000); return () => clearInterval(i); }, [fetchData]);

  // Auto-scroll to latest
  useEffect(() => {
    if (autoScroll && feedRef.current) feedRef.current.scrollTop = 0;
  }, [turns, autoScroll]);

  // Filter turns by agent + type + search
  const filtered = turns.filter(t => {
    // Agent filter
    if (selectedAgent !== 'all') {
      const agentName = t.agent_name || '';
      const selectedAgentObj = agents.find(a => a.id === selectedAgent);
      if (selectedAgentObj && agentName && !agentName.includes(selectedAgentObj.name)) return false;
      if (selectedAgentObj && !agentName && selectedAgent !== 'founder') return false;
    }
    if (filter === 'thinking' && !t.thinking) return false;
    if (filter === 'tools' && (!t.tool_calls || t.tool_calls.length === 0)) return false;
    if (filter === 'errors' && !t.tool_calls?.some(tc => tc.error)) return false;
    if (search) {
      const s = search.toLowerCase();
      const text = `${t.thinking || ''} ${t.agent_name || ''} ${t.tool_calls?.map(tc => `${tc.tool} ${tc.result || ''}`).join(' ') || ''}`.toLowerCase();
      if (!text.includes(s)) return false;
    }
    return true;
  });

  const selectedAgentObj = selectedAgent !== 'all' ? agents.find(a => a.id === selectedAgent) : null;

  if (loading) {
    return (
      <div data-testid="mind-loading" className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-muted-foreground">Connecting to agent mind...</span>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="agent-mind-page" style={{ display: 'flex', gap: '12px', height: 'calc(100vh - 8rem)', fontFamily: 'Manrope, sans-serif' }}>

      {/* ═══ MAIN FEED ═══ */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Header bar */}
        <div style={{
          background: '#09090b', borderRadius: '6px 6px 0 0', padding: '10px 14px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Brain className="w-4 h-4" style={{ color: '#9B6BFF' }} />
            <span style={{ fontSize: '13px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>AGENT MIND</span>
            <div style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: stats?.source === 'engine' ? '#34D399' : '#FFB347',
              boxShadow: `0 0 8px ${stats?.source === 'engine' ? '#34D399' : '#FFB347'}`,
            }} />

            {/* Agent Selector */}
            <select
              data-testid="agent-selector"
              value={selectedAgent}
              onChange={e => setSelectedAgent(e.target.value)}
              style={{
                background: '#18181b', border: '1px solid #27272a', borderRadius: '4px',
                padding: '3px 8px', fontSize: '11px', color: '#d4d4d8', cursor: 'pointer',
                fontFamily: 'JetBrains Mono, monospace', outline: 'none', maxWidth: '260px',
              }}
            >
              <option value="all">All Agents ({agents.length})</option>
              {agents.map(a => (
                <option key={a.id} value={a.id}>
                  {a.role || a.name}{a.department ? ` — ${a.department}` : ''}{a.status ? ` [${a.status}]` : ''}
                </option>
              ))}
            </select>

            <span style={{ fontSize: '10px', color: '#71717a', fontFamily: 'JetBrains Mono, monospace' }}>
              {filtered.length} turns
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Search */}
            <div style={{ position: 'relative' }}>
              <Search className="w-3 h-3" style={{ position: 'absolute', left: '8px', top: '50%', transform: 'translateY(-50%)', color: '#52525b' }} />
              <input
                data-testid="mind-search"
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search thoughts & actions..."
                style={{
                  background: '#18181b', border: '1px solid #27272a', borderRadius: '4px',
                  padding: '4px 8px 4px 26px', fontSize: '10px', color: '#d4d4d8', width: '200px',
                  fontFamily: 'JetBrains Mono, monospace', outline: 'none',
                }}
              />
            </div>

            {/* Filters */}
            {['all', 'thinking', 'tools', 'errors'].map(f => (
              <button key={f} data-testid={`mind-filter-${f}`} onClick={() => setFilter(f)}
                style={{
                  fontSize: '9px', fontWeight: 700, padding: '3px 8px', borderRadius: '3px', border: 'none', cursor: 'pointer',
                  background: filter === f ? '#9B6BFF' : '#18181b', color: filter === f ? '#fff' : '#71717a',
                  textTransform: 'uppercase', letterSpacing: '0.5px', transition: 'all 0.15s',
                }}>
                {f}
              </button>
            ))}

            {/* Auto-scroll toggle */}
            <button onClick={() => setAutoScroll(!autoScroll)} data-testid="auto-scroll-toggle"
              style={{
                fontSize: '9px', fontWeight: 700, padding: '3px 8px', borderRadius: '3px', border: 'none', cursor: 'pointer',
                background: autoScroll ? '#34D399' : '#18181b', color: autoScroll ? '#fff' : '#71717a',
              }}>
              AUTO
            </button>

            {/* Demo toggle */}
            <button data-testid="mind-demo-toggle" onClick={() => { setDemoMode(!demoMode); setLoading(true); }}
              style={{
                fontSize: '9px', fontWeight: 700, padding: '3px 8px', borderRadius: '3px', border: 'none', cursor: 'pointer',
                background: demoMode ? '#FFB347' : '#34D399', color: '#fff',
              }}>
              {demoMode ? 'DEMO' : 'LIVE'}
            </button>
          </div>
        </div>

        {/* Turn feed */}
        <div ref={feedRef} style={{
          flex: 1, background: '#0a0a0f', borderRadius: '0 0 6px 6px', padding: '8px 14px',
          overflowY: 'auto', overflowX: 'hidden',
          scrollbarWidth: 'thin', scrollbarColor: '#27272a #0a0a0f',
        }}>
          {filtered.length > 0 ? filtered.map((turn, i) => (
            <TurnBlock key={turn.turn_id || i} turn={turn} index={i} />
          )) : (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <Brain className="w-8 h-8" style={{ color: '#27272a', margin: '0 auto 12px' }} />
              <p style={{ fontSize: '12px', color: '#52525b' }}>
                {demoMode ? 'No matching activity' : engineState?.live ? 'No turns yet — agent is initializing...' : 'Engine offline. Switch to DEMO to see sample data.'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ═══ RIGHT PANEL: SOUL + Stats ═══ */}
      <div style={{ width: '280px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>

        {/* Engine Status / Selected Agent */}
        <div style={{ background: '#09090b', borderRadius: '6px', padding: '12px' }}>
          {selectedAgentObj ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: selectedAgentObj.status === 'alive' || selectedAgentObj.status === 'running' ? '#34D399' : selectedAgentObj.status === 'sleeping' ? '#5B9CFF' : '#71717a' }} />
                <span style={{ fontSize: '10px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>SELECTED AGENT</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <MiniStat label="Name" value={selectedAgentObj.name} color="#d4d4d8" />
                <MiniStat label="Role" value={selectedAgentObj.role || '—'} color="#9B6BFF" />
                {selectedAgentObj.department && <MiniStat label="Dept" value={selectedAgentObj.department} color="#5B9CFF" />}
                <MiniStat label="Status" value={selectedAgentObj.status || '—'} color={selectedAgentObj.status === 'alive' ? '#34D399' : '#FFB347'} />
                {selectedAgentObj.wallet && <MiniStat label="Wallet" value={`${selectedAgentObj.wallet.slice(0, 8)}...${selectedAgentObj.wallet.slice(-4)}`} color="#71717a" />}
                <MiniStat label="Turns" value={filtered.length} />
              </div>
            </>
          ) : (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                <Cpu className="w-3.5 h-3.5" style={{ color: '#5B9CFF' }} />
                <span style={{ fontSize: '10px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>ENGINE STATUS</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <MiniStat label="State" value={engineState?.agent_state || (demoMode ? 'demo' : 'offline')} color={engineState?.live ? '#34D399' : '#FFB347'} />
                <MiniStat label="DB" value={engineState?.db_exists ? 'Found' : 'Not found'} color={engineState?.db_exists ? '#34D399' : '#FF5252'} />
                <MiniStat label="Turns" value={engineState?.turn_count || 0} />
                <MiniStat label="Agents" value={agents.length} />
                <MiniStat label="Source" value={stats?.source || 'demo'} color={stats?.source === 'engine' ? '#34D399' : '#FFB347'} />
              </div>
            </>
          )}
        </div>

        {/* SOUL.md */}
        <div style={{ background: '#09090b', borderRadius: '6px', padding: '12px', flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Eye className="w-3.5 h-3.5" style={{ color: '#9B6BFF' }} />
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>SOUL.md</span>
          </div>
          <div style={{
            flex: 1, overflowY: 'auto', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace',
            color: '#a1a1aa', lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            background: '#0a0a0f', borderRadius: '4px', padding: '8px',
          }}>
            {soul || (demoMode
              ? 'SOUL.md is generated by the running engine.\n\nSwitch to LIVE mode when the engine is deployed to see the agent\'s evolving self-description — its purpose, values, personality, boundaries, and strategy.'
              : engineState?.live
                ? 'Loading SOUL.md...'
                : 'Engine not running.\n\nDeploy the Anima Fund engine to Conway Cloud to see the agent\'s SOUL.md — its self-authored identity that evolves over time.'
            )}
          </div>
        </div>

        {/* Token/Cost summary */}
        <div style={{ background: '#09090b', borderRadius: '6px', padding: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <DollarSign className="w-3.5 h-3.5" style={{ color: '#FFB347' }} />
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>SESSION COST</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <MiniStat label="Turns shown" value={filtered.length} />
            <MiniStat label="Total tokens" value={(filtered.reduce((s, t) => s + (t.token_usage?.totalTokens || t.token_usage?.total_tokens || 0), 0)).toLocaleString()} />
            <MiniStat label="Total cost" value={`$${(filtered.reduce((s, t) => s + (t.cost_cents || 0), 0) / 100).toFixed(2)}`} color="#FFB347" />
            <MiniStat label="Tool calls" value={filtered.reduce((s, t) => s + (t.tool_calls?.length || 0), 0)} />
          </div>
        </div>
      </div>
    </div>
  );
}

function MiniStat({ label, value, color = '#d4d4d8' }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ fontSize: '9px', color: '#52525b' }}>{label}</span>
      <span style={{ fontSize: '10px', fontWeight: 800, color, fontFamily: 'JetBrains Mono, monospace' }}>{value}</span>
    </div>
  );
}
