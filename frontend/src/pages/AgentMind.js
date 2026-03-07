import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Brain, Terminal, Wrench, DollarSign, AlertTriangle, Clock, Cpu, Eye, ChevronDown, ChevronRight, Search, Wallet, Copy, ExternalLink } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

/*
  AGENT MIND — Real-time view of everything the agent is thinking and doing.

  Shows:
  - Live turns (thinking, tool calls, state) when available
  - Real-time engine logs (stdout/stderr) always visible
  - Wallet/funding info in the right panel
  - SOUL.md content
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

// ─── Log parsing (same as EngineConsole) ───
function parseLogLine(line) {
  const trimmed = line.trim();
  if (!trimmed) return null;
  try {
    const j = JSON.parse(trimmed);
    return { type: 'structured', timestamp: j.timestamp, level: j.level || 'info', module: j.module || '', message: j.message || '', raw: trimmed };
  } catch {
    if (trimmed.match(/^[═╔╗╚╝║█▓░╗╝╚╔─╯╭│╮╰]+$/) || trimmed.match(/^[█╗╚╔═╝║]+/) || trimmed.length < 2) return null;
    return { type: 'text', message: trimmed, raw: trimmed };
  }
}

function getLogColor(entry) {
  if (!entry) return '#71717a';
  const msg = entry.message.toLowerCase();
  if (entry.level === 'error' || msg.includes('error') || msg.includes('fatal')) return '#f87171';
  if (msg.includes('critical') || msg.includes('insufficient')) return '#fb923c';
  if (msg.includes('wallet created') || msg.includes('api key provisioned') || msg.includes('success')) return '#34D399';
  if (msg.includes('sleeping') || msg.includes('sleep')) return '#a78bfa';
  if (msg.includes('heartbeat') || msg.includes('wake')) return '#60a5fa';
  if (msg.includes('think') || msg.includes('inference')) return '#fbbf24';
  if (entry.module === 'loop') return '#fbbf24';
  if (entry.type === 'text') return '#e4e4e7';
  return '#a1a1aa';
}

function getLogTag(entry) {
  if (!entry) return '';
  const msg = entry.message.toLowerCase();
  if (msg.includes('wallet created')) return 'WALLET';
  if (msg.includes('api key provisioned')) return 'API KEY';
  if (msg.includes('skill')) return 'SKILLS';
  if (msg.includes('heartbeat')) return 'HEARTBEAT';
  if (msg.includes('sleeping') || msg.includes('sleep')) return 'SLEEP';
  if (msg.includes('critical')) return 'CRITICAL';
  if (msg.includes('error') || msg.includes('fatal')) return 'ERROR';
  if (msg.includes('think') || msg.includes('inference')) return 'THINK';
  if (msg.includes('state:')) return 'STATE';
  if (entry.module === 'loop') return 'LOOP';
  return 'INFO';
}

function formatTime(timestamp) {
  if (!timestamp) return '';
  try { return new Date(timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
  catch { return ''; }
}

// ─── Tool Call Block ───
function ToolCallBlock({ tc, isExpanded, onToggle }) {
  const hasError = !!tc.error;
  const duration = tc.duration_ms ? `${tc.duration_ms}ms` : '';
  return (
    <div style={{ borderLeft: `3px solid ${hasError ? '#FF5252' : '#34D399'}`, marginLeft: '16px', marginBottom: '4px' }}>
      <button onClick={onToggle} data-testid={`tool-call-${tc.id || tc.tool}`}
        style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 8px', background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left' }}>
        {isExpanded ? <ChevronDown className="w-3 h-3" style={{ color: '#71717a', flexShrink: 0 }} /> : <ChevronRight className="w-3 h-3" style={{ color: '#71717a', flexShrink: 0 }} />}
        <Wrench className="w-3 h-3" style={{ color: hasError ? '#FF5252' : '#34D399', flexShrink: 0 }} />
        <span style={{ fontSize: '12px', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color: hasError ? '#FF5252' : '#16a34a' }}>{tc.tool || tc.tool_used}</span>
        {duration && <span style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#71717a' }}>{duration}</span>}
        {hasError && <AlertTriangle className="w-3 h-3" style={{ color: '#FF5252', flexShrink: 0 }} />}
      </button>
      {isExpanded && (
        <div style={{ padding: '4px 8px 8px 24px' }}>
          {tc.arguments && Object.keys(tc.arguments).length > 0 && (
            <div style={{ marginBottom: '6px' }}>
              <span style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '0.5px' }}>ARGS</span>
              <pre style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#d4d4d8', background: '#1e1e2e', borderRadius: '4px', padding: '6px 8px', margin: '2px 0 0 0', overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '120px', overflowY: 'auto' }}>
                {JSON.stringify(tc.arguments, null, 2)}
              </pre>
            </div>
          )}
          {(tc.result || tc.result_preview) && (
            <div>
              <span style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '0.5px' }}>{hasError ? 'ERROR' : 'RESULT'}</span>
              <pre style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: hasError ? '#FF5252' : '#a1a1aa', background: '#1e1e2e', borderRadius: '4px', padding: '6px 8px', margin: '2px 0 0 0', overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', maxHeight: '200px', overflowY: 'auto' }}>
                {tc.error || (tc.result || tc.result_preview || '').slice(0, 1000)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Turn Block ───
function TurnBlock({ turn, index }) {
  const [expanded, setExpanded] = useState(index < 3);
  const [expandedTools, setExpandedTools] = useState({});
  const toolCalls = turn.tool_calls || [];
  const thinking = turn.thinking || '';
  const cost = turn.cost_cents ? `$${(turn.cost_cents / 100).toFixed(4)}` : '';
  const tokens = turn.token_usage || {};
  const totalTokens = tokens.totalTokens || tokens.total_tokens || 0;
  const toggleTool = (id) => setExpandedTools(prev => ({ ...prev, [id]: !prev[id] }));
  const stateColors = { running: '#34D399', sleeping: '#5B9CFF', waking: '#FFB347', low_compute: '#d97706', critical: '#FF5252', dead: '#71717a' };

  return (
    <div data-testid={`turn-${turn.turn_id || index}`} style={{ borderBottom: '1px solid #27272a', padding: '12px 0' }}>
      <button onClick={() => setExpanded(!expanded)}
        style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'none', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', padding: '0' }}>
        {expanded ? <ChevronDown className="w-4 h-4" style={{ color: '#71717a' }} /> : <ChevronRight className="w-4 h-4" style={{ color: '#71717a' }} />}
        <div style={{ width: '6px', height: '6px', borderRadius: '50%', flexShrink: 0, background: stateColors[turn.state] || '#71717a' }} />
        <span style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace', color: '#a1a1aa' }}>Turn {turn.turn_id ? turn.turn_id.slice(-6) : index + 1}</span>
        <span style={{ fontSize: '10px', color: '#52525b' }}>{timeAgo(turn.timestamp)}</span>
        {turn.state && <span style={{ fontSize: '9px', fontWeight: 700, padding: '1px 6px', borderRadius: '3px', background: `${stateColors[turn.state] || '#71717a'}20`, color: stateColors[turn.state] || '#71717a' }}>{turn.state}</span>}
        {toolCalls.length > 0 && <span style={{ fontSize: '9px', color: '#71717a', fontFamily: 'JetBrains Mono, monospace' }}>{toolCalls.length} tool{toolCalls.length > 1 ? 's' : ''}</span>}
        {cost && <span style={{ fontSize: '9px', color: '#FFB347', fontFamily: 'JetBrains Mono, monospace' }}>{cost}</span>}
        {totalTokens > 0 && <span style={{ fontSize: '9px', color: '#52525b', fontFamily: 'JetBrains Mono, monospace' }}>{totalTokens.toLocaleString()} tok</span>}
      </button>
      {expanded && (
        <div style={{ marginTop: '8px', paddingLeft: '20px' }}>
          {thinking && (
            <div style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                <Brain className="w-3 h-3" style={{ color: '#9B6BFF' }} />
                <span style={{ fontSize: '9px', color: '#9B6BFF', fontWeight: 700, letterSpacing: '0.5px' }}>THINKING</span>
              </div>
              <div style={{ fontSize: '11px', lineHeight: 1.5, color: '#d4d4d8', background: '#1a1a2e', borderRadius: '4px', padding: '8px 10px', borderLeft: '3px solid #9B6BFF', maxHeight: '200px', overflowY: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {thinking}
              </div>
            </div>
          )}
          {turn.input && (
            <div style={{ marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                <Eye className="w-3 h-3" style={{ color: '#5B9CFF' }} />
                <span style={{ fontSize: '9px', color: '#5B9CFF', fontWeight: 700, letterSpacing: '0.5px' }}>INPUT</span>
              </div>
              <div style={{ fontSize: '11px', color: '#a1a1aa', background: '#1a1a2e', borderRadius: '4px', padding: '6px 10px', borderLeft: '3px solid #5B9CFF', maxHeight: '100px', overflowY: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {turn.input.slice(0, 500)}
              </div>
            </div>
          )}
          {toolCalls.length > 0 && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                <Wrench className="w-3 h-3" style={{ color: '#34D399' }} />
                <span style={{ fontSize: '9px', color: '#34D399', fontWeight: 700, letterSpacing: '0.5px' }}>ACTIONS</span>
              </div>
              {toolCalls.map((tc, i) => (
                <ToolCallBlock key={tc.id || i} tc={tc} isExpanded={expandedTools[tc.id || i] || false} onToggle={() => toggleTool(tc.id || i)} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Main Component ───
export default function AgentMind({ genesisState }) {
  const [turns, setTurns] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('all');
  const [engineState, setEngineState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const [soul, setSoul] = useState(null);
  const [stats, setStats] = useState(null);
  const [logs, setLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('logs'); // 'logs' or 'turns'
  const [copied, setCopied] = useState(false);
  const feedRef = useRef(null);
  const logRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      const [engineRes, logsRes] = await Promise.all([
        fetch(`${API}/api/engine/live`),
        fetch(`${API}/api/engine/logs?lines=100`),
      ]);
      const engine = await engineRes.json();
      const logsData = await logsRes.json();
      setEngineState(engine);

      // Parse logs
      const rawLines = (logsData.stdout || '').split('\n');
      const parsed = rawLines.map(parseLogLine).filter(Boolean);
      const errLines = (logsData.stderr || '').split('\n');
      const parsedErrors = errLines.map(l => {
        const trimmed = l.trim();
        if (!trimmed) return null;
        return { type: 'text', level: 'error', message: trimmed, raw: trimmed };
      }).filter(Boolean);
      setLogs([...parsed, ...parsedErrors]);

      if (engine.live || engine.db_exists) {
        const [agRes, turnsRes, soulRes] = await Promise.all([
          fetch(`${API}/api/live/agents`),
          fetch(`${API}/api/live/turns?limit=100`),
          fetch(`${API}/api/live/soul`),
        ]);
        const [agData, turnsData, soulData] = await Promise.all([agRes.json(), turnsRes.json(), soulRes.json()]);
        const liveAgents = (agData.agents || []).map(a => ({
          id: a.agent_id, name: a.name, role: a.role, status: a.status, wallet: a.wallet_address, sandbox: a.sandbox_id,
        }));
        liveAgents.unshift({ id: 'founder', name: engine.fund_name || 'Founder AI', role: 'Founder AI', status: engine.agent_state, wallet: '', sandbox: '' });
        setAgents(liveAgents);
        const newTurns = turnsData.turns || [];
        setTurns(newTurns);
        setSoul(soulData.content || null);
        setStats({ total_turns: turnsData.total || 0, source: 'engine', agent_state: engine.agent_state, turn_count: engine.turn_count });
        // Auto-switch to turns tab when turns become available
        if (newTurns.length > 0 && activeTab === 'logs') setActiveTab('turns');
      } else {
        setAgents([]);
        setTurns([]);
        setSoul(null);
        setStats({ total_turns: 0, source: 'waiting', agent_state: 'not_started', turn_count: 0 });
      }
    } catch (e) { console.error('AgentMind fetch error:', e); }
    finally { setLoading(false); }
  }, [activeTab]);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 3000); return () => clearInterval(i); }, [fetchData]);

  // Auto-scroll logs
  useEffect(() => {
    if (autoScroll && logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs, autoScroll]);

  useEffect(() => {
    if (autoScroll && feedRef.current && activeTab === 'turns') feedRef.current.scrollTop = 0;
  }, [turns, autoScroll, activeTab]);

  const walletAddr = genesisState?.wallet_address;
  const qrCode = genesisState?.qr_code;

  const copyWallet = () => {
    if (walletAddr) {
      navigator.clipboard.writeText(walletAddr);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Filter turns
  const filtered = turns.filter(t => {
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

  const hasTurns = turns.length > 0;

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

            {/* Tab switcher */}
            <div style={{ display: 'flex', gap: '2px', background: '#18181b', borderRadius: '4px', padding: '2px' }}>
              <button data-testid="tab-logs" onClick={() => setActiveTab('logs')}
                style={{ fontSize: '10px', fontWeight: 700, padding: '3px 10px', borderRadius: '3px', border: 'none', cursor: 'pointer',
                  background: activeTab === 'logs' ? '#27272a' : 'transparent', color: activeTab === 'logs' ? '#fff' : '#71717a' }}>
                <Terminal className="w-3 h-3" style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />LOGS
              </button>
              <button data-testid="tab-turns" onClick={() => setActiveTab('turns')}
                style={{ fontSize: '10px', fontWeight: 700, padding: '3px 10px', borderRadius: '3px', border: 'none', cursor: 'pointer',
                  background: activeTab === 'turns' ? '#27272a' : 'transparent', color: activeTab === 'turns' ? '#fff' : '#71717a' }}>
                <Brain className="w-3 h-3" style={{ display: 'inline', marginRight: '4px', verticalAlign: 'middle' }} />TURNS {hasTurns && `(${filtered.length})`}
              </button>
            </div>

            {/* Agent selector (only for turns tab) */}
            {activeTab === 'turns' && (
              <select data-testid="agent-selector" value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)}
                style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '4px', padding: '3px 8px', fontSize: '11px', color: '#d4d4d8', cursor: 'pointer', fontFamily: 'JetBrains Mono, monospace', outline: 'none', maxWidth: '200px' }}>
                <option value="all">All Agents ({agents.length})</option>
                {agents.map(a => <option key={a.id} value={a.id}>{a.role || a.name}{a.status ? ` [${a.status}]` : ''}</option>)}
              </select>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {activeTab === 'turns' && (
              <>
                <div style={{ position: 'relative' }}>
                  <Search className="w-3 h-3" style={{ position: 'absolute', left: '8px', top: '50%', transform: 'translateY(-50%)', color: '#52525b' }} />
                  <input data-testid="mind-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..."
                    style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '4px', padding: '4px 8px 4px 26px', fontSize: '10px', color: '#d4d4d8', width: '160px', fontFamily: 'JetBrains Mono, monospace', outline: 'none' }} />
                </div>
                {['all', 'thinking', 'tools', 'errors'].map(f => (
                  <button key={f} data-testid={`mind-filter-${f}`} onClick={() => setFilter(f)}
                    style={{ fontSize: '9px', fontWeight: 700, padding: '3px 8px', borderRadius: '3px', border: 'none', cursor: 'pointer',
                      background: filter === f ? '#9B6BFF' : '#18181b', color: filter === f ? '#fff' : '#71717a', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    {f}
                  </button>
                ))}
              </>
            )}
            <button onClick={() => setAutoScroll(!autoScroll)} data-testid="auto-scroll-toggle"
              style={{ fontSize: '9px', fontWeight: 700, padding: '3px 8px', borderRadius: '3px', border: 'none', cursor: 'pointer',
                background: autoScroll ? '#34D399' : '#18181b', color: autoScroll ? '#fff' : '#71717a' }}>
              AUTO
            </button>
          </div>
        </div>

        {/* Content area */}
        {activeTab === 'logs' ? (
          /* ═══ LIVE LOGS TAB ═══ */
          <div ref={logRef}
            onScroll={(e) => { const { scrollTop, scrollHeight, clientHeight } = e.target; setAutoScroll(scrollHeight - scrollTop - clientHeight < 40); }}
            style={{ flex: 1, background: '#0a0a0f', borderRadius: '0 0 6px 6px', padding: '8px 0', overflowY: 'auto', fontFamily: 'JetBrains Mono, monospace', fontSize: '11px', lineHeight: '20px' }}>
            {logs.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center' }}>
                <Terminal className="w-8 h-8" style={{ color: '#27272a', margin: '0 auto 12px' }} />
                <p style={{ fontSize: '12px', color: '#52525b' }}>Waiting for engine output...</p>
              </div>
            ) : (
              logs.map((entry, i) => {
                const tag = getLogTag(entry);
                const tagColors = {
                  ERROR: '#f87171', CRITICAL: '#fb923c', THINK: '#fbbf24', SLEEP: '#a78bfa',
                  HEARTBEAT: '#60a5fa', WALLET: '#34D399', 'API KEY': '#34D399', SKILLS: '#34D399',
                  STATE: '#818cf8', LOOP: '#fbbf24', INFO: '#71717a',
                };
                return (
                  <div key={i} style={{ padding: '2px 14px', display: 'flex', gap: '8px', color: getLogColor(entry), alignItems: 'flex-start' }}>
                    <span style={{ color: '#3f3f46', minWidth: '55px', flexShrink: 0 }}>{formatTime(entry.timestamp)}</span>
                    <span style={{
                      minWidth: '70px', flexShrink: 0, fontSize: '9px', fontWeight: 800,
                      color: tagColors[tag] || '#71717a', padding: '1px 0',
                    }}>[{tag}]</span>
                    <span style={{ wordBreak: 'break-word' }}>{entry.message}</span>
                  </div>
                );
              })
            )}
          </div>
        ) : (
          /* ═══ TURNS TAB ═══ */
          <div ref={feedRef} style={{ flex: 1, background: '#0a0a0f', borderRadius: '0 0 6px 6px', padding: '8px 14px', overflowY: 'auto', scrollbarWidth: 'thin', scrollbarColor: '#27272a #0a0a0f' }}>
            {filtered.length > 0 ? filtered.map((turn, i) => (
              <TurnBlock key={turn.turn_id || i} turn={turn} index={i} />
            )) : (
              <div style={{ padding: '40px', textAlign: 'center' }}>
                <Brain className="w-8 h-8" style={{ color: '#27272a', margin: '0 auto 12px' }} />
                <p style={{ fontSize: '12px', color: '#52525b' }}>
                  {engineState?.db_exists ? 'No turns yet — check the LOGS tab for real-time engine activity.' : 'Engine not running.'}
                </p>
                {engineState?.db_exists && !hasTurns && (
                  <button onClick={() => setActiveTab('logs')} style={{ marginTop: '8px', fontSize: '11px', color: '#9B6BFF', background: 'none', border: '1px solid #9B6BFF30', borderRadius: '4px', padding: '6px 16px', cursor: 'pointer' }}>
                    View Live Logs
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ RIGHT PANEL ═══ */}
      <div style={{ width: '280px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>

        {/* Wallet & Funding */}
        {walletAddr && (
          <div data-testid="wallet-funding-panel" style={{ background: '#09090b', borderRadius: '6px', padding: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
              <Wallet className="w-3.5 h-3.5" style={{ color: '#FFB347' }} />
              <span style={{ fontSize: '10px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>AGENT WALLET</span>
            </div>
            {/* QR Code */}
            {qrCode && (
              <div style={{ textAlign: 'center', marginBottom: '10px' }}>
                <img src={qrCode} alt="Wallet QR" data-testid="wallet-qr-dashboard"
                  style={{ width: '120px', height: '120px', borderRadius: '6px', border: '1px solid #27272a', margin: '0 auto' }} />
                <div style={{ fontSize: '8px', color: '#52525b', marginTop: '4px' }}>Scan to send USDC on Base</div>
              </div>
            )}
            {/* Address */}
            <button onClick={copyWallet} data-testid="copy-wallet-btn"
              style={{ width: '100%', display: 'flex', alignItems: 'center', gap: '6px', background: '#18181b', border: '1px solid #27272a', borderRadius: '4px', padding: '8px', cursor: 'pointer', textAlign: 'left' }}>
              <span style={{ flex: 1, fontSize: '9px', fontFamily: 'JetBrains Mono, monospace', color: '#d4d4d8', wordBreak: 'break-all' }}>{walletAddr}</span>
              <Copy className="w-3 h-3" style={{ color: copied ? '#34D399' : '#71717a', flexShrink: 0 }} />
            </button>
            {copied && <div style={{ fontSize: '9px', color: '#34D399', textAlign: 'center', marginTop: '4px' }}>Copied!</div>}

            {/* Funding Instructions */}
            <div style={{ marginTop: '10px', padding: '8px', background: '#0a1a0a', border: '1px solid #166534', borderRadius: '4px' }}>
              <div style={{ fontSize: '9px', fontWeight: 700, color: '#34D399', marginBottom: '6px', letterSpacing: '0.5px' }}>FUND THIS AGENT</div>
              <div style={{ fontSize: '9px', color: '#a1a1aa', lineHeight: 1.6 }}>
                <div style={{ marginBottom: '4px' }}>1. Transfer Conway credits:</div>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '8px', color: '#71717a', padding: '2px 4px', background: '#18181b', borderRadius: '2px', marginBottom: '6px' }}>
                  conway credits transfer {walletAddr ? `${walletAddr.slice(0, 8)}...` : '<addr>'} &lt;amount&gt;
                </div>
                <div style={{ marginBottom: '4px' }}>2. Send USDC on Base to the address above</div>
                <div style={{ marginBottom: '2px' }}>3. Fund via Conway Cloud:</div>
              </div>
              <a href="https://app.conway.tech" target="_blank" rel="noopener noreferrer" data-testid="conway-cloud-link"
                style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '9px', color: '#5B9CFF', textDecoration: 'none', marginTop: '4px' }}>
                <ExternalLink className="w-3 h-3" /> app.conway.tech
              </a>
            </div>
          </div>
        )}

        {/* Engine Status */}
        <div style={{ background: '#09090b', borderRadius: '6px', padding: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Cpu className="w-3.5 h-3.5" style={{ color: '#5B9CFF' }} />
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>ENGINE STATUS</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <MiniStat label="State" value={(engineState?.agent_state || 'offline').toUpperCase()} color={engineState?.live ? '#34D399' : engineState?.db_exists ? '#FFB347' : '#71717a'} />
            <MiniStat label="DB" value={engineState?.db_exists ? 'Connected' : 'Not found'} color={engineState?.db_exists ? '#34D399' : '#FF5252'} />
            <MiniStat label="Turns" value={engineState?.turn_count || 0} />
            <MiniStat label="Agents" value={agents.length} />
            <MiniStat label="Log lines" value={logs.length} />
          </div>
        </div>

        {/* SOUL.md */}
        <div style={{ background: '#09090b', borderRadius: '6px', padding: '12px', flex: 1, minHeight: '120px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Eye className="w-3.5 h-3.5" style={{ color: '#9B6BFF' }} />
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>SOUL.md</span>
          </div>
          <div style={{
            flex: 1, overflowY: 'auto', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace',
            color: '#a1a1aa', lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            background: '#0a0a0f', borderRadius: '4px', padding: '8px',
          }}>
            {soul || (engineState?.db_exists
              ? 'Loading SOUL.md...'
              : 'The agent\'s SOUL.md will appear here when the engine is live.'
            )}
          </div>
        </div>

        {/* Session Cost */}
        <div style={{ background: '#09090b', borderRadius: '6px', padding: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <DollarSign className="w-3.5 h-3.5" style={{ color: '#FFB347' }} />
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#fff', letterSpacing: '1px' }}>SESSION COST</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <MiniStat label="Turns" value={filtered.length} />
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
