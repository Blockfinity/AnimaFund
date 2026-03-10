import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import {
  Server, Terminal, Eye, Rocket, Zap,
  CheckCircle2, Globe, ExternalLink, Send, MessageSquare,
  RefreshCw, AlertCircle, Clock, ArrowRight, Play, Box,
  Wifi, Users, CreditCard, Wrench, Shield, ScrollText,
  Radio, HardDrive, Loader2
} from 'lucide-react';
import { useSSE, useSSETrigger } from '../hooks/useSSE';

const API = process.env.REACT_APP_BACKEND_URL;

const PHASE_LABELS = {
  0: { label: 'Phase 0: Tool Testing', cls: 'text-amber-700 bg-amber-50 border-amber-200' },
  1: { label: 'Phase 1: Earn $5,000', cls: 'text-blue-700 bg-blue-50 border-blue-200' },
  2: { label: 'Phase 2: Earn $10,000', cls: 'text-violet-700 bg-violet-50 border-violet-200' },
  3: { label: 'Phase 3: Create Fund', cls: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
};

/* ─── OpenClaw category mappings ─────────────────────────── */
const CAT_COLORS = {
  vm_provision: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  vm_teardown: 'bg-red-50 text-red-700 border-red-200',
  vm_network: 'bg-sky-50 text-sky-700 border-sky-200',
  openclaw_setup: 'bg-violet-50 text-violet-700 border-violet-200',
  openclaw_action: 'bg-violet-50 text-violet-700 border-violet-200',
  tool_install: 'bg-amber-50 text-amber-700 border-amber-200',
  service_deploy: 'bg-teal-50 text-teal-700 border-teal-200',
  system_setup: 'bg-zinc-50 text-zinc-600 border-zinc-200',
  sandbox_exec: 'bg-zinc-50 text-zinc-600 border-zinc-200',
  sandbox_file: 'bg-zinc-50 text-zinc-600 border-zinc-200',
  browsing: 'bg-blue-50 text-blue-700 border-blue-200',
  payment: 'bg-amber-50 text-amber-700 border-amber-200',
  agent_network: 'bg-purple-50 text-purple-700 border-purple-200',
  other: 'bg-zinc-50 text-zinc-600 border-zinc-200',
};

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Date.now() - new Date(ts).getTime();
  const s = Math.floor(diff / 1000); if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60); if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60); if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

/* ═══════════════════════════════════════════════════════════
   MAIN COMPONENT — Monitoring Dashboard (no provisioning stepper)
   ═══════════════════════════════════════════════════════════ */
export default function AnimaVM({ selectedAgent }) {
  const [provStatus, setProvStatus] = useState(null);
  const [phaseState, setPhaseState] = useState(null);
  const [customNudge, setCustomNudge] = useState('');

  // VM monitoring state
  const [actions, setActions] = useState([]);
  const [categories, setCategories] = useState({});
  const [sandboxData, setSandboxData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [execLog, setExecLog] = useState([]);
  const [ocStatus, setOcStatus] = useState(null);
  const [agentLogs, setAgentLogs] = useState(null);
  const [financials, setFinancials] = useState(null);
  const [monitorTab, setMonitorTab] = useState('live');
  const [terminalUrl, setTerminalUrl] = useState(null);
  const [terminalLoading, setTerminalLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  /* ─── Data fetching — SSE-triggered via shared SSEProvider ─── */
  const fetchAll = useCallback(async () => {
    try {
      const [statusRes, phaseRes, ocStatusRes, actionsRes, sandboxRes, browseRes, execRes, financialsRes] = await Promise.all([
        fetch(`${API}/api/provision/status`),
        fetch(`${API}/api/provision/phase-state`),
        fetch(`${API}/api/openclaw/status`),
        fetch(`${API}/api/openclaw/actions?limit=100`),
        fetch(`${API}/api/openclaw/sandboxes`),
        fetch(`${API}/api/openclaw/browsing?limit=50`),
        fetch(`${API}/api/openclaw/sandbox-exec-log?limit=50`),
        fetch(`${API}/api/live/financials`),
      ]);
      if (statusRes.ok) setProvStatus(await statusRes.json());
      if (phaseRes.ok) {
        const pd = await phaseRes.json();
        if (pd.success) setPhaseState(pd.phase_state);
      }
      if (ocStatusRes.ok) setOcStatus(await ocStatusRes.json());
      if (actionsRes.ok) {
        const d = await actionsRes.json();
        setActions(d.actions || []);
        setCategories(d.categories || {});
      }
      if (sandboxRes.ok) setSandboxData(await sandboxRes.json());
      if (browseRes.ok) setSessions((await browseRes.json()).sessions || []);
      if (execRes.ok) setExecLog((await execRes.json()).log || []);
      if (financialsRes.ok) setFinancials(await financialsRes.json());
    } catch (e) { console.error('AnimaVM fetch:', e); }
    finally { setLoading(false); }
  }, []);

  // SSE: use shared SSEProvider context instead of duplicate EventSource
  const { sseData } = useSSE();
  useSSETrigger(fetchAll, { fallbackMs: 15000, deps: [selectedAgent] });

  // Apply real-time SSE updates to local state
  useEffect(() => {
    if (!sseData) return;
    // Conway credits (source: Conway API)
    if (sseData.conway_credits_cents !== undefined && provStatus) {
      setProvStatus(prev => prev ? { ...prev, credits_cents: sseData.conway_credits_cents } : prev);
    }
    // Agent financials (source: webhook from sandbox daemon)
    if (sseData.total_earned_usd !== undefined || sseData.total_spent_usd !== undefined) {
      setFinancials(prev => ({
        ...prev,
        total_earned_usd: sseData.total_earned_usd || 0,
        total_spent_usd: sseData.total_spent_usd || 0,
      }));
    }
    // Phase state (source: webhook from sandbox daemon)
    if (sseData.phase_state && Object.keys(sseData.phase_state).length > 0) {
      setPhaseState(sseData.phase_state);
    }
  }, [sseData]); // eslint-disable-line react-hooks/exhaustive-deps

  const hasSandbox = provStatus?.sandbox?.status === 'active';
  const tools = provStatus?.tools || {};

  const sendNudge = async () => {
    if (!customNudge.trim()) return;
    try {
      await fetch(`${API}/api/provision/nudge/custom`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: customNudge }) });
      toast.success('Message sent to agent');
      setCustomNudge('');
      await fetchAll();
    } catch (e) { toast.error(e.message); }
  };

  const goAutonomous = async () => {
    try {
      await fetch(`${API}/api/provision/nudge`, { method: 'POST' });
      toast.success('Autonomy nudge sent');
      await fetchAll();
    } catch (e) { toast.error(e.message); }
  };

  const fetchAgentLogs = async () => {
    try {
      const res = await fetch(`${API}/api/provision/agent-logs?lines=40`);
      const data = await res.json();
      if (data.success) setAgentLogs(data);
    } catch {}
  };

  useEffect(() => {
    if (provStatus?.sandbox?.terminal_url && !terminalUrl) {
      setTerminalUrl(provStatus.sandbox.terminal_url);
    }
  }, [provStatus, terminalUrl]);

  const connectTerminal = async () => {
    setTerminalLoading(true);
    try {
      const res = await fetch(`${API}/api/provision/web-terminal`, { method: 'POST' });
      const data = await res.json();
      if (data.success && data.terminal_url) {
        setTerminalUrl(data.terminal_url);
        toast.success('Terminal session created');
      } else {
        toast.error(data.error || 'Failed to create terminal');
      }
    } catch (e) { toast.error(e.message); }
    setTerminalLoading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const oc = ocStatus?.openclaw || {};
  const sb = ocStatus?.sandbox_summary || {};
  const hasVmActivity = ocStatus?.has_activity || false;

  return (
    <div data-testid="anima-vm-page" className="space-y-4 max-w-[1200px] mx-auto">

      {/* ═══════════ STATUS BAR ═══════════ */}
      <div className="bg-white border border-border rounded-sm p-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div className={`w-2 h-2 rounded-full ${hasVmActivity ? 'bg-emerald-500 animate-pulse' : hasSandbox ? 'bg-amber-500' : 'bg-zinc-300'}`} />
              <span className="text-xs font-heading font-semibold text-foreground">Anima VM</span>
            </div>
            <StatusPill label="Sandbox" ok={hasSandbox} />
            <StatusPill label="Terminal" ok={tools['conway-terminal']?.installed} />
            <StatusPill label="OpenClaw" ok={tools['openclaw']?.installed} />
            <StatusPill label="Claude Code" ok={tools['claude-code']?.installed} />
            <StatusPill label="Engine" ok={tools['engine']?.deployed} />
          </div>
          <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
            <span data-testid="wallet-usdc">Wallet: <b className={sseData?.wallet?.usdc > 0 ? "text-emerald-600" : "text-muted-foreground"}>${(sseData?.wallet?.usdc || 0).toFixed(2)} <span className="text-[8px]">USDC</span></b></span>
            <span className="text-border">|</span>
            <span data-testid="conway-credits">Credits: <b className={(sseData?.conway_credits_cents || provStatus?.credits_cents) > 0 ? "text-foreground" : "text-red-500"}>${((sseData?.conway_credits_cents || provStatus?.credits_cents || 0) / 100).toFixed(2)}</b></span>
            <span className="text-border">|</span>
            <span>Phase: <b className="text-foreground">{sseData?.phase ?? phaseState?.current_phase ?? 0}</b></span>
            <span>Earned: <b className="text-emerald-600">${(sseData?.total_earned_usd || financials?.total_earned_usd || 0).toFixed(2)}</b></span>
            <span>Turns: <b className="text-foreground">{sseData?.decision_count || sseData?.engine?.turn_count || 0}</b></span>
            <span>VMs: <b className="text-foreground">{sb.live_sandboxes || 0}</b></span>
            {sseData?.last_update && <span data-testid="live-indicator" className="text-emerald-500 font-bold">LIVE</span>}
            {!sseData?.last_update && sseData?.sandbox_id && <span className="text-amber-500">Connecting...</span>}
            <button data-testid="refresh-all-btn" onClick={fetchAll} className="p-1 rounded border border-border hover:bg-secondary transition-colors">
              <RefreshCw className="w-3 h-3 text-muted-foreground" />
            </button>
          </div>
        </div>

        {/* Phase indicator */}
        {phaseState && (
          <div className={`flex items-center gap-2 mt-2 pt-2 border-t border-border`}>
            <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold border ${PHASE_LABELS[phaseState.current_phase || 0]?.cls || 'border-zinc-200 bg-zinc-50 text-zinc-600'}`}>
              <Rocket className="w-3 h-3" />
              {PHASE_LABELS[phaseState.current_phase || 0]?.label || `Phase ${phaseState.current_phase}`}
            </div>
            {phaseState.current_phase === 0 && phaseState.tool_tests && (
              <span className="text-[10px] font-mono text-muted-foreground">
                {Object.values(phaseState.tool_tests).filter(v => v === 'PASS').length}/15 tools tested
              </span>
            )}
          </div>
        )}
      </div>

      {/* ═══════════ MONITOR TABS ═══════════ */}
      <div className="flex items-center gap-1 bg-white border border-border rounded-sm p-1 overflow-x-auto">
        {[
          { id: 'live', label: 'Live Feed', icon: Eye, count: actions.length },
          { id: 'terminal', label: 'Terminal', icon: Terminal, count: null },
          { id: 'console', label: 'Exec Log', icon: ScrollText, count: execLog.length },
          { id: 'logs', label: 'Agent Logs', icon: ScrollText, count: null },
          { id: 'browsing', label: 'Browsing', icon: Globe, count: sessions.length },
          { id: 'sandboxes', label: 'VMs', icon: Server, count: (sandboxData?.total_live || 0) + (sandboxData?.total_created || 0) },
          { id: 'message', label: 'Message', icon: MessageSquare, count: provStatus?.nudges?.length || 0 },
        ].map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} data-testid={`tab-${t.id}`} onClick={() => setMonitorTab(t.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-medium transition-colors
                ${monitorTab === t.id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
              <Icon className="w-3.5 h-3.5" />
              {t.label}
              {t.count !== null && t.count > 0 && (
                <span className={`ml-0.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold ${monitorTab === t.id ? 'bg-white/20' : 'bg-secondary'}`}>{t.count}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* ═══════════ TAB CONTENT ═══════════ */}
      {monitorTab === 'live' && <LiveFeed actions={actions} categories={categories} sandboxData={sandboxData} sessions={sessions} oc={oc} />}
      {monitorTab === 'terminal' && <LiveTerminal terminalUrl={terminalUrl} onConnect={connectTerminal} loading={terminalLoading} hasSandbox={hasSandbox} />}
      {monitorTab === 'console' && <ConsoleView execLog={execLog} />}
      {monitorTab === 'logs' && <AgentLogsView agentLogs={agentLogs} onRefresh={fetchAgentLogs} deployed={tools['engine']?.deployed} />}
      {monitorTab === 'browsing' && <BrowsingView sessions={sessions} />}
      {monitorTab === 'sandboxes' && <SandboxesView data={sandboxData} />}
      {monitorTab === 'message' && <MessageView customNudge={customNudge} setCustomNudge={setCustomNudge} sendNudge={sendNudge} nudges={provStatus?.nudges || []} />}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════
   SMALL COMPONENTS
   ═══════════════════════════════════════════════════════════ */

function StatusPill({ label, ok }) {
  return (
    <div className="flex items-center gap-1 text-[10px]">
      {ok
        ? <CheckCircle2 className="w-3 h-3 text-emerald-600" />
        : <div className="w-3 h-3 rounded-full border border-zinc-300 bg-zinc-100" />}
      <span className={ok ? 'text-foreground font-medium' : 'text-muted-foreground'}>{label}</span>
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════
   LIVE TERMINAL TAB
   ═══════════════════════════════════════════════════════════ */

function LiveTerminal({ terminalUrl, onConnect, loading, hasSandbox }) {
  const [ptySessions, setPtySessions] = useState([]);
  const [ptyLoading, setPtyLoading] = useState(false);
  const [activePty, setActivePty] = useState(null);
  const [ptyOutput, setPtyOutput] = useState('');
  const [ptyInput, setPtyInput] = useState('');
  const [ptyCreating, setPtyCreating] = useState(false);

  const fetchPtySessions = async () => {
    try {
      const res = await fetch(`${API}/api/provision/pty/list`);
      const data = await res.json();
      if (data.success) setPtySessions(data.sessions || []);
    } catch {}
  };

  const createPty = async (cmd = 'bash') => {
    setPtyCreating(true);
    try {
      const res = await fetch(`${API}/api/provision/pty/create`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd, cols: 120, rows: 40 }),
      });
      const data = await res.json();
      if (data.success) {
        setActivePty(data.session);
        await fetchPtySessions();
        toast.success(`PTY session created (${cmd})`);
      } else toast.error(data.error || 'Failed');
    } catch (e) { toast.error(e.message); }
    setPtyCreating(false);
  };

  const readPty = async (sessionId) => {
    try {
      const res = await fetch(`${API}/api/provision/pty/read?session_id=${sessionId}&full=true`);
      const data = await res.json();
      if (data.success) setPtyOutput(data.output || '');
    } catch {}
  };

  const writePty = async () => {
    if (!activePty || !ptyInput) return;
    try {
      await fetch(`${API}/api/provision/pty/write`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: activePty.session_id, input: ptyInput + '\n' }),
      });
      setPtyInput('');
      setTimeout(() => readPty(activePty.session_id), 500);
    } catch (e) { toast.error(e.message); }
  };

  const closePty = async (sessionId) => {
    try {
      await fetch(`${API}/api/provision/pty/${sessionId}`, { method: 'DELETE' });
      if (activePty?.session_id === sessionId) { setActivePty(null); setPtyOutput(''); }
      await fetchPtySessions();
      toast.success('PTY session closed');
    } catch (e) { toast.error(e.message); }
  };

  // Load sessions on mount
  useEffect(() => { if (hasSandbox) fetchPtySessions(); }, [hasSandbox]);

  // Auto-read active PTY
  useEffect(() => {
    if (!activePty) return;
    readPty(activePty.session_id);
    const interval = setInterval(() => readPty(activePty.session_id), 3000);
    return () => clearInterval(interval);
  }, [activePty]);

  if (!hasSandbox) {
    return (
      <div data-testid="terminal-no-sandbox" className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Terminal className="w-8 h-8 text-zinc-200 mb-2" />
        <p className="text-sm font-medium text-foreground mb-1">No sandbox provisioned</p>
        <p className="text-[10px] text-muted-foreground">Create a sandbox first to access the terminal.</p>
      </div>
    );
  }

  return (
    <div data-testid="terminal-view" className="space-y-3">
      {/* Web Terminal */}
      <div className="bg-white border border-border rounded-sm overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-zinc-950">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${terminalUrl ? 'bg-emerald-500 animate-pulse' : 'bg-zinc-500'}`} />
            <span className="text-[10px] font-mono text-zinc-300">web terminal (30-day sliding session)</span>
          </div>
          <div className="flex items-center gap-2">
            {terminalUrl && (
              <a href={terminalUrl} target="_blank" rel="noopener noreferrer"
                data-testid="terminal-external-link"
                className="text-[10px] text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition-colors">
                <ExternalLink className="w-3 h-3" /> Pop out
              </a>
            )}
            <button data-testid={terminalUrl ? 'reconnect-terminal-btn' : 'connect-terminal-btn'} onClick={onConnect} disabled={loading}
              className="text-[10px] text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition-colors disabled:opacity-50">
              {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
              {terminalUrl ? 'Reconnect' : 'Connect'}
            </button>
          </div>
        </div>
        {terminalUrl ? (
          <iframe data-testid="terminal-iframe" src={terminalUrl} title="Sandbox Terminal" className="w-full bg-zinc-950 border-0" style={{ height: '420px' }}
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups" />
        ) : (
          <div className="flex items-center justify-center h-32 bg-zinc-950">
            <button onClick={onConnect} disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-zinc-200 bg-zinc-800 rounded hover:bg-zinc-700 disabled:opacity-50 transition-colors">
              {loading ? <><Loader2 className="w-3 h-3 animate-spin" /> Connecting...</> : <><Terminal className="w-3 h-3" /> Open Web Terminal</>}
            </button>
          </div>
        )}
      </div>

      {/* PTY Sessions */}
      <div className="bg-white border border-border rounded-sm overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 border-b border-border">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider">PTY Sessions</span>
            <span className="text-[9px] text-muted-foreground">(interactive: REPL, vim, shell)</span>
          </div>
          <div className="flex items-center gap-1.5">
            {['bash', 'python3', 'node'].map(cmd => (
              <button key={cmd} data-testid={`pty-create-${cmd}`} onClick={() => createPty(cmd)} disabled={ptyCreating}
                className="text-[9px] px-2 py-0.5 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors disabled:opacity-50">
                + {cmd}
              </button>
            ))}
            <button data-testid="pty-refresh" onClick={fetchPtySessions} className="p-0.5 text-muted-foreground hover:text-foreground">
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>
        </div>

        {ptySessions.length > 0 && (
          <div className="flex items-center gap-1 px-4 py-1.5 border-b border-border bg-secondary/30 overflow-x-auto">
            {ptySessions.map(s => (
              <div key={s.session_id} className="flex items-center gap-1">
                <button data-testid={`pty-tab-${s.session_id}`}
                  onClick={() => setActivePty(s)}
                  className={`text-[9px] px-2 py-0.5 rounded font-mono transition-colors ${activePty?.session_id === s.session_id ? 'bg-foreground text-white' : 'bg-white border border-border text-muted-foreground hover:text-foreground'}`}>
                  {s.command} ({s.state || 'running'})
                </button>
                <button data-testid={`pty-close-${s.session_id}`} onClick={() => closePty(s.session_id)}
                  className="text-[9px] text-red-400 hover:text-red-600 p-0.5">x</button>
              </div>
            ))}
          </div>
        )}

        {activePty ? (
          <div>
            <div className="bg-zinc-950 px-4 py-2 max-h-[250px] overflow-y-auto">
              <pre data-testid="pty-output" className="text-[10px] font-mono text-green-400 whitespace-pre-wrap leading-relaxed">{ptyOutput || '(waiting for output...)'}</pre>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 border-t border-border bg-zinc-950">
              <span className="text-[9px] font-mono text-zinc-500">$</span>
              <input data-testid="pty-input" type="text" value={ptyInput} onChange={e => setPtyInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && writePty()}
                className="flex-1 bg-transparent border-0 text-[10px] font-mono text-green-400 placeholder:text-zinc-600 focus:outline-none"
                placeholder="Type command and press Enter..." />
              <button data-testid="pty-send" onClick={writePty} disabled={!ptyInput}
                className="text-[9px] text-zinc-400 hover:text-zinc-200 disabled:opacity-30">Send</button>
            </div>
          </div>
        ) : (
          <div className="px-4 py-6 text-center text-[10px] text-muted-foreground">
            {ptySessions.length === 0 ? 'No active PTY sessions. Create one above.' : 'Click a session tab above to interact.'}
          </div>
        )}
      </div>
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════
   LIVE FEED TAB
   ═══════════════════════════════════════════════════════════ */

function LiveFeed({ actions, categories, sandboxData, sessions, oc }) {
  if (actions.length === 0) {
    return (
      <div data-testid="live-feed-empty" className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Server className="w-8 h-8 text-zinc-200 mb-3" />
        <p className="text-sm font-medium text-foreground mb-1">No sandbox activity yet</p>
        <p className="text-xs text-muted-foreground max-w-md">
          Activity will stream here as the agent creates VMs, installs tools, browses, and deploys services.
        </p>
      </div>
    );
  }

  return (
    <div data-testid="live-feed" className="grid grid-cols-3 gap-4">
      <div className="col-span-2 bg-white border border-border rounded-sm">
        <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
          <h3 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider">Action Feed</h3>
          <span className="text-[10px] text-muted-foreground">{actions.length} actions</span>
        </div>
        <div className="max-h-[480px] overflow-y-auto divide-y divide-border">
          {actions.slice(0, 40).map((a, i) => <ActionRow key={a.id || i} action={a} />)}
        </div>
      </div>
      <div className="space-y-3">
        {/* OpenClaw status */}
        <div className="bg-white border border-border rounded-sm p-3">
          <h4 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider mb-2">OpenClaw (in VM)</h4>
          <div className="space-y-1.5">
            <StateRow label="Installed" value={oc.openclaw_installed} />
            <StateRow label="Daemon" value={oc.openclaw_daemon_running} />
            <StateRow label="MCP" value={oc.mcp_configured} />
            <StateRow label="Terminal" value={oc.conway_terminal_in_sandbox} />
          </div>
        </div>
        {/* Categories */}
        {Object.keys(categories).length > 0 && (
          <div className="bg-white border border-border rounded-sm p-3">
            <h4 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider mb-2">Categories</h4>
            <div className="space-y-1">
              {Object.entries(categories).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
                <div key={cat} className="flex items-center justify-between">
                  <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${CAT_COLORS[cat] || CAT_COLORS.other}`}>{cat.replace(/_/g, ' ')}</span>
                  <span className="text-xs font-mono font-bold text-foreground">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {/* Exposed URLs */}
        {sandboxData?.exposed_urls?.length > 0 && (
          <div className="bg-white border border-border rounded-sm p-3">
            <h4 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider mb-2">Public URLs</h4>
            {sandboxData.exposed_urls.map((u, i) => (
              <a key={i} href={u.url} target="_blank" rel="noreferrer" className="text-[10px] text-blue-600 hover:underline flex items-center gap-1 truncate mb-1">
                <ExternalLink className="w-2.5 h-2.5 flex-shrink-0" /> {u.url}
              </a>
            ))}
          </div>
        )}
        {/* Recent Browsing */}
        {sessions.length > 0 && (
          <div className="bg-white border border-border rounded-sm p-3">
            <h4 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider mb-2">Recent Browsing</h4>
            {sessions.slice(0, 4).map((s, i) => (
              <div key={i} className="text-[10px] mb-1">
                <div className="text-foreground font-mono truncate">{s.url}</div>
                <div className="text-muted-foreground">{timeAgo(s.timestamp)}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ActionRow({ action }) {
  const [expanded, setExpanded] = useState(false);
  const catClass = CAT_COLORS[action.category] || CAT_COLORS.other;
  return (
    <div className="px-4 py-2 hover:bg-secondary/30 cursor-pointer transition-colors" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-center gap-2">
        <span className={`text-[8px] font-bold uppercase px-1 py-0.5 rounded border whitespace-nowrap ${catClass}`}>{action.category?.replace(/_/g, ' ')}</span>
        <span className="text-[10px] font-mono font-semibold text-foreground">{action.tool}</span>
        {action.duration_ms > 0 && <span className="text-[9px] text-muted-foreground flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" />{action.duration_ms}ms</span>}
        {action.error && <AlertCircle className="w-3 h-3 text-red-500" />}
        <span className="text-[9px] text-muted-foreground ml-auto">{timeAgo(action.timestamp)}</span>
      </div>
      {Object.keys(action.arguments || {}).length > 0 && (
        <div className="text-[9px] text-muted-foreground mt-0.5 font-mono truncate pl-2">
          {action.tool === 'sandbox_exec' ? (action.arguments.command || '').slice(0, 120) :
           Object.entries(action.arguments).map(([k, v]) => `${k}: ${typeof v === 'string' ? v.slice(0, 60) : JSON.stringify(v)}`).join(' | ')}
        </div>
      )}
      {expanded && action.result && (
        <div className="mt-1.5 ml-2 p-2 bg-zinc-950 rounded border border-zinc-800">
          <pre className="text-[9px] font-mono text-green-400 whitespace-pre-wrap break-all max-h-40 overflow-y-auto">{action.result}</pre>
        </div>
      )}
    </div>
  );
}

function StateRow({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[10px] text-muted-foreground">{label}</span>
      {value
        ? <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">ON</span>
        : <span className="text-[9px] font-bold text-zinc-500 bg-zinc-50 px-1.5 py-0.5 rounded border border-zinc-200">OFF</span>}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════
   CONSOLE TAB
   ═══════════════════════════════════════════════════════════ */

function ConsoleView({ execLog }) {
  const [filter, setFilter] = useState('all');
  const cats = [...new Set(execLog.map(e => e.category))];
  const filtered = filter === 'all' ? execLog : execLog.filter(e => e.category === filter);

  if (execLog.length === 0) {
    return (
      <div data-testid="console-empty" className="flex flex-col items-center justify-center h-48 text-center bg-white border border-border rounded-sm">
        <Terminal className="w-8 h-8 text-zinc-200 mb-2" />
        <p className="text-sm font-medium text-foreground mb-1">No VM commands yet</p>
        <p className="text-[10px] text-muted-foreground">Commands the agent runs via <code className="bg-secondary px-1 rounded">sandbox_exec</code> appear here.</p>
      </div>
    );
  }

  return (
    <div data-testid="console-view" className="bg-white border border-border rounded-sm">
      <div className="px-4 py-2.5 border-b border-border flex items-center gap-2">
        <h3 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider">VM Console</h3>
        <div className="flex items-center gap-1 ml-auto">
          <button onClick={() => setFilter('all')}
            className={`text-[9px] px-2 py-0.5 rounded-sm border transition-colors ${filter === 'all' ? 'bg-foreground text-white border-foreground' : 'border-border text-muted-foreground'}`}>
            All ({execLog.length})
          </button>
          {cats.map(c => (
            <button key={c} onClick={() => setFilter(c)}
              className={`text-[9px] px-2 py-0.5 rounded-sm border transition-colors ${filter === c ? 'bg-foreground text-white border-foreground' : 'border-border text-muted-foreground'}`}>
              {c.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>
      <div className="max-h-[500px] overflow-y-auto divide-y divide-border">
        {filtered.map((entry, i) => <ExecRow key={i} entry={entry} />)}
      </div>
    </div>
  );
}

function ExecRow({ entry }) {
  const [expanded, setExpanded] = useState(false);
  const catClass = CAT_COLORS[entry.category] || CAT_COLORS.other;
  return (
    <div className="px-4 py-2 hover:bg-secondary/30 cursor-pointer transition-colors" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-center gap-2">
        <Terminal className="w-3 h-3 text-muted-foreground flex-shrink-0" />
        <span className={`text-[8px] font-bold uppercase px-1 py-0.5 rounded border whitespace-nowrap ${catClass}`}>{entry.category?.replace(/_/g, ' ')}</span>
        {entry.sandbox_id && <span className="text-[9px] font-mono text-muted-foreground bg-secondary px-1 py-0.5 rounded">{entry.sandbox_id.slice(0, 12)}...</span>}
        {entry.error && <AlertCircle className="w-3 h-3 text-red-500" />}
        {entry.duration_ms > 0 && <span className="text-[9px] text-muted-foreground">{entry.duration_ms}ms</span>}
        <span className="text-[9px] text-muted-foreground ml-auto">{timeAgo(entry.timestamp)}</span>
      </div>
      <div className="mt-1 pl-5">
        <code className="text-[9px] font-mono text-foreground bg-zinc-50 px-1.5 py-0.5 rounded border border-border block truncate">$ {entry.command}</code>
      </div>
      {expanded && entry.output && (
        <div className="mt-1.5 ml-5 p-2 bg-zinc-950 rounded border border-zinc-800">
          <pre className="text-[9px] font-mono text-green-400 whitespace-pre-wrap break-all max-h-40 overflow-y-auto">{entry.output}</pre>
        </div>
      )}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════
   AGENT LOGS TAB
   ═══════════════════════════════════════════════════════════ */

function AgentLogsView({ agentLogs, onRefresh, deployed }) {
  if (!deployed) {
    return (
      <div data-testid="logs-not-deployed" className="flex flex-col items-center justify-center h-48 text-center bg-white border border-border rounded-sm">
        <Rocket className="w-8 h-8 text-zinc-200 mb-2" />
        <p className="text-sm font-medium text-foreground mb-1">Agent not deployed yet</p>
        <p className="text-[10px] text-muted-foreground">Deploy the agent to see its logs.</p>
      </div>
    );
  }

  return (
    <div data-testid="agent-logs-view" className="bg-white border border-border rounded-sm">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
        <h3 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider">Agent Logs (from sandbox)</h3>
        <button data-testid="refresh-logs-btn" onClick={onRefresh}
          className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium text-muted-foreground hover:text-foreground bg-secondary rounded transition-colors">
          <RefreshCw className="w-2.5 h-2.5" /> Refresh
        </button>
      </div>
      {agentLogs ? (
        <div className="bg-zinc-950 px-4 py-3 max-h-[400px] overflow-y-auto">
          <pre className="text-[10px] font-mono text-zinc-300 whitespace-pre-wrap leading-relaxed">
            {agentLogs.stdout || agentLogs.stderr || 'No logs yet'}
          </pre>
        </div>
      ) : (
        <div className="px-4 py-8 text-center text-xs text-muted-foreground">Click Refresh to load logs from sandbox</div>
      )}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════
   BROWSING TAB
   ═══════════════════════════════════════════════════════════ */

function BrowsingView({ sessions }) {
  if (sessions.length === 0) {
    return (
      <div data-testid="browsing-empty" className="flex flex-col items-center justify-center h-48 text-center bg-white border border-border rounded-sm">
        <Globe className="w-8 h-8 text-zinc-200 mb-2" />
        <p className="text-sm font-medium text-foreground mb-1">No browsing sessions</p>
        <p className="text-[10px] text-muted-foreground">URLs visited via OpenClaw will appear here.</p>
      </div>
    );
  }

  return (
    <div data-testid="browsing-view" className="bg-white border border-border rounded-sm">
      <div className="px-4 py-2.5 border-b border-border">
        <h3 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider">Browsing ({sessions.length})</h3>
      </div>
      <div className="max-h-[500px] overflow-y-auto divide-y divide-border">
        {sessions.map((s, i) => <BrowsingRow key={i} session={s} />)}
      </div>
    </div>
  );
}

function BrowsingRow({ session }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="px-4 py-2.5 hover:bg-secondary/30 cursor-pointer transition-colors" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-center gap-2">
        {session.success ? <CheckCircle2 className="w-3 h-3 text-emerald-600 flex-shrink-0" /> : <AlertCircle className="w-3 h-3 text-red-500 flex-shrink-0" />}
        <span className="text-[10px] font-mono text-foreground truncate flex-1">{session.url}</span>
        {session.duration_ms > 0 && <span className="text-[9px] text-muted-foreground">{session.duration_ms}ms</span>}
        <span className="text-[9px] text-muted-foreground">{timeAgo(session.timestamp)}</span>
      </div>
      {expanded && session.result_preview && (
        <div className="mt-1.5 p-2 bg-zinc-950 rounded border border-zinc-800">
          <pre className="text-[9px] font-mono text-green-400 whitespace-pre-wrap break-all max-h-40 overflow-y-auto">{session.result_preview}</pre>
        </div>
      )}
      {session.error && <div className="text-[9px] text-red-600 mt-0.5">{session.error}</div>}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════
   SANDBOXES TAB
   ═══════════════════════════════════════════════════════════ */

function SandboxesView({ data }) {
  if (!data || (data.total_live === 0 && data.total_created === 0)) {
    return (
      <div data-testid="sandboxes-empty" className="flex flex-col items-center justify-center h-48 text-center bg-white border border-border rounded-sm">
        <Server className="w-8 h-8 text-zinc-200 mb-2" />
        <p className="text-sm font-medium text-foreground mb-1">No Conway VMs</p>
        <p className="text-[10px] text-muted-foreground">VMs created by the agent appear here.</p>
      </div>
    );
  }

  return (
    <div data-testid="sandboxes-view" className="space-y-3">
      {data.live_sandboxes?.length > 0 && (
        <div>
          <h3 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider mb-2">Live VMs</h3>
          <div className="grid grid-cols-2 gap-3">
            {data.live_sandboxes.map((sb, i) => <SandboxCard key={i} sandbox={sb} live />)}
          </div>
        </div>
      )}
      {data.created_sandboxes?.length > 0 && (
        <div>
          <h3 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider mb-2">Created VMs</h3>
          <div className="grid grid-cols-2 gap-3">
            {data.created_sandboxes.map((sb, i) => <SandboxCard key={i} sandbox={sb} />)}
          </div>
        </div>
      )}
      {data.exposed_urls?.length > 0 && (
        <div className="bg-white border border-border rounded-sm p-3">
          <h3 className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider mb-2">Public URLs</h3>
          {data.exposed_urls.map((u, i) => (
            <div key={i} className="flex items-center gap-2 mb-1">
              <a href={u.url} target="_blank" rel="noreferrer" className="text-[10px] text-blue-600 hover:underline flex items-center gap-1 font-mono">
                <ExternalLink className="w-2.5 h-2.5" /> {u.url}
              </a>
              {u.port && <span className="text-[9px] text-muted-foreground">port {u.port}</span>}
              <span className="text-[9px] text-muted-foreground ml-auto">{timeAgo(u.timestamp)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SandboxCard({ sandbox, live }) {
  const id = sandbox.id || sandbox.sandbox_id || 'Unknown';
  return (
    <div className={`bg-white border rounded-sm p-3 ${live ? 'border-emerald-200' : 'border-border'}`}>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-1.5">
          <Server className="w-3.5 h-3.5 text-foreground" />
          <span className="text-[10px] font-heading font-semibold text-foreground font-mono">{id.slice(0, 16)}{id.length > 16 ? '...' : ''}</span>
        </div>
        <span className={`text-[8px] px-1.5 py-0.5 rounded-full font-bold uppercase ${live ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-zinc-50 text-zinc-600 border border-zinc-200'}`}>
          {sandbox.status || (live ? 'live' : 'created')}
        </span>
      </div>
      {sandbox.spec && (
        <div className="grid grid-cols-3 gap-1 text-[9px] text-muted-foreground">
          {sandbox.spec.vcpu && <div>CPU: <span className="text-foreground font-mono">{sandbox.spec.vcpu}</span></div>}
          {sandbox.spec.ram_mb && <div>RAM: <span className="text-foreground font-mono">{sandbox.spec.ram_mb}MB</span></div>}
          {sandbox.spec.disk_gb && <div>Disk: <span className="text-foreground font-mono">{sandbox.spec.disk_gb}GB</span></div>}
        </div>
      )}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════
   MESSAGE TAB
   ═══════════════════════════════════════════════════════════ */

function MessageView({ customNudge, setCustomNudge, sendNudge, nudges }) {
  return (
    <div data-testid="message-view" className="space-y-3">
      <div className="bg-white border border-border rounded-sm">
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border">
          <MessageSquare className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider">Message the Agent</span>
          <span className="text-[9px] text-muted-foreground">(sees it next turn)</span>
        </div>
        <div className="flex gap-2 p-3">
          <input
            data-testid="nudge-input"
            type="text"
            value={customNudge}
            onChange={(e) => setCustomNudge(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendNudge()}
            placeholder="e.g. Test your curl, register a domain, deploy on port 3000"
            className="flex-1 px-3 py-2 text-xs border border-border rounded bg-secondary/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-foreground"
          />
          <button data-testid="send-nudge-btn" onClick={sendNudge} disabled={!customNudge.trim()}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-bold bg-foreground text-white rounded hover:bg-foreground/90 disabled:bg-secondary disabled:text-muted-foreground disabled:cursor-not-allowed transition-colors">
            <Send className="w-3 h-3" /> Send
          </button>
        </div>
      </div>
      {nudges.length > 0 && (
        <div className="bg-white border border-border rounded-sm">
          <div className="px-4 py-2.5 border-b border-border">
            <span className="text-[10px] font-heading font-bold text-foreground uppercase tracking-wider">Recent Messages</span>
          </div>
          <div className="divide-y divide-border max-h-[300px] overflow-y-auto">
            {nudges.slice().reverse().map((n, i) => (
              <div key={i} data-testid={`nudge-${i}`} className="flex items-start gap-2 px-4 py-2.5">
                <Send className="w-3 h-3 text-muted-foreground mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-foreground break-words">{n.message}</div>
                  <div className="text-[9px] text-muted-foreground mt-0.5">{new Date(n.timestamp).toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
