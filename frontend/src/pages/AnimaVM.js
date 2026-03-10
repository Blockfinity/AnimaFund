import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import {
  Server, Terminal, Eye, Cpu, FileText, Rocket, Zap,
  CheckCircle2, Loader2, ChevronDown, ChevronUp,
  Globe, Wallet, ExternalLink, Send, MessageSquare,
  RefreshCw, AlertCircle, Clock, ArrowRight, Play, Box,
  Wifi, Users, CreditCard, Wrench, Shield, ScrollText,
  RotateCcw, Radio, HardDrive
} from 'lucide-react';
import { useSSETrigger } from '../hooks/useSSE';

const API = process.env.REACT_APP_BACKEND_URL;

/* ─── Provisioning Steps ─────────────────────────────────── */
const PROVISION_STEPS = [
  { id: 'sandbox', label: 'Create Sandbox', desc: 'Conway Cloud VM (2 vCPU, 4GB, 40GB)', action: '/api/provision/create-sandbox', icon: Server },
  { id: 'terminal', label: 'Install Terminal', desc: 'Conway Terminal + wallet + API key + all MCPs', action: '/api/provision/install-terminal', icon: Terminal },
  { id: 'openclaw', label: 'Install OpenClaw', desc: 'Autonomous browser + MCP bridge', action: '/api/provision/install-openclaw', icon: Eye },
  { id: 'claudecode', label: 'Install Claude Code', desc: 'Self-modification via MCP', action: '/api/provision/install-claude-code', icon: Cpu },
  { id: 'skills', label: 'Load Skills', desc: 'Push skill definitions into sandbox', action: '/api/provision/load-skills', icon: FileText },
  { id: 'deploy', label: 'Deploy Agent', desc: 'Push engine into sandbox + start (Phase 0)', action: '/api/provision/deploy-agent', icon: Rocket },
];

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
   MAIN COMPONENT
   ═══════════════════════════════════════════════════════════ */
export default function AnimaVM({ selectedAgent }) {
  // Provision state
  const [provStatus, setProvStatus] = useState(null);
  const [phaseState, setPhaseState] = useState(null);
  const [runningStep, setRunningStep] = useState(null);
  const [stepOutputs, setStepOutputs] = useState({});
  const [expandedStep, setExpandedStep] = useState(null);
  const [stepperOpen, setStepperOpen] = useState(true);
  const [customNudge, setCustomNudge] = useState('');

  // VM monitoring state
  const [actions, setActions] = useState([]);
  const [categories, setCategories] = useState({});
  const [sandboxData, setSandboxData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [execLog, setExecLog] = useState([]);
  const [ocStatus, setOcStatus] = useState(null);
  const [agentLogs, setAgentLogs] = useState(null);
  const [monitorTab, setMonitorTab] = useState('live');
  const [terminalUrl, setTerminalUrl] = useState(null);
  const [terminalLoading, setTerminalLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  /* ─── Data fetching ─────────────────────────────────────── */
  const fetchAll = useCallback(async () => {
    try {
      const [statusRes, phaseRes, ocStatusRes, actionsRes, sandboxRes, browseRes, execRes] = await Promise.all([
        fetch(`${API}/api/provision/status`),
        fetch(`${API}/api/provision/phase-state`),
        fetch(`${API}/api/openclaw/status`),
        fetch(`${API}/api/openclaw/actions?limit=100`),
        fetch(`${API}/api/openclaw/sandboxes`),
        fetch(`${API}/api/openclaw/browsing?limit=50`),
        fetch(`${API}/api/openclaw/sandbox-exec-log?limit=50`),
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
    } catch (e) { console.error('AnimaVM fetch:', e); }
    finally { setLoading(false); }
  }, []);

  useSSETrigger(fetchAll, { fallbackMs: 6000, deps: [selectedAgent] });

  /* ─── Provisioning helpers ──────────────────────────────── */
  const hasSandbox = provStatus?.sandbox?.status === 'active';
  const tools = provStatus?.tools || {};

  const isStepDone = (id) => {
    if (id === 'sandbox') return hasSandbox;
    if (id === 'terminal') return tools['conway-terminal']?.installed;
    if (id === 'openclaw') return tools['openclaw']?.installed;
    if (id === 'claudecode') return tools['claude-code']?.installed;
    if (id === 'skills') return provStatus?.skills_loaded;
    if (id === 'deploy') return tools['engine']?.deployed;
    return false;
  };

  const canRunStep = (step) => {
    if (step.id === 'sandbox') return true;
    return hasSandbox; // all other steps require sandbox
  };

  const allDone = PROVISION_STEPS.every(s => isStepDone(s.id));
  const completedCount = PROVISION_STEPS.filter(s => isStepDone(s.id)).length;

  // Auto-collapse stepper when all done
  useEffect(() => {
    if (allDone && stepperOpen) setStepperOpen(false);
  }, [allDone, stepperOpen]);

  const runStep = async (step) => {
    setRunningStep(step.id);
    try {
      const res = await fetch(`${API}${step.action}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
      const data = await res.json();
      if (data.output) {
        setStepOutputs(prev => ({ ...prev, [step.id]: data.output }));
        setExpandedStep(step.id);
      }
      data.success ? toast.success(`${step.label} complete`) : toast.error(data.error || 'Failed');
      await fetchAll();
    } catch (e) { toast.error(e.message); }
    setRunningStep(null);
  };

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

  // Pick up terminal URL from provision status if already created
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

      {/* ═══════════ PROVISIONING STEPPER ═══════════ */}
      <div data-testid="provision-stepper" className="bg-white border border-border rounded-sm overflow-hidden">
        {/* Stepper header — always visible */}
        <button
          data-testid="stepper-toggle"
          onClick={() => setStepperOpen(!stepperOpen)}
          className="w-full flex items-center justify-between px-4 py-3 hover:bg-secondary/30 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className={`w-2 h-2 rounded-full ${allDone ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
            <span className="text-sm font-heading font-semibold text-foreground">
              {allDone ? 'Sandbox Provisioned' : 'Provision Agent'}
            </span>
            <span className="text-xs text-muted-foreground">
              {completedCount}/{PROVISION_STEPS.length} steps
            </span>
            {/* Mini progress bar */}
            <div className="w-24 h-1.5 bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-foreground rounded-full transition-all duration-500"
                style={{ width: `${(completedCount / PROVISION_STEPS.length) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            {provStatus?.wallet_address && (
              <span className="text-[10px] font-mono text-muted-foreground hidden sm:inline">
                {provStatus.wallet_address.slice(0, 8)}...{provStatus.wallet_address.slice(-4)}
              </span>
            )}
            {stepperOpen ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
          </div>
        </button>

        {/* Stepper body */}
        {stepperOpen && (
          <div className="border-t border-border">
            {/* Sandbox-only notice */}
            <div className="flex items-center gap-2 px-4 py-2 bg-secondary/30 border-b border-border">
              <Shield className="w-3 h-3 text-muted-foreground flex-shrink-0" />
              <span className="text-[10px] text-muted-foreground">
                All tools install inside the agent's <strong>sandbox VM</strong>. Nothing runs on the host.
              </span>
            </div>

            {/* Steps */}
            <div className="divide-y divide-border">
              {PROVISION_STEPS.map((step, i) => {
                const Icon = step.icon;
                const done = isStepDone(step.id);
                const enabled = canRunStep(step);
                const isRunning = runningStep === step.id;
                const hasOutput = stepOutputs[step.id];
                const isExpanded = expandedStep === step.id;

                return (
                  <div key={step.id} data-testid={`step-${step.id}`} className={`${!enabled && !done ? 'opacity-40' : ''}`}>
                    <div className="flex items-center gap-3 px-4 py-2.5">
                      {/* Step number / status */}
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0
                        ${done ? 'bg-emerald-100 text-emerald-700' : isRunning ? 'bg-foreground text-white' : 'bg-secondary text-muted-foreground'}`}>
                        {done ? <CheckCircle2 className="w-3.5 h-3.5" /> : isRunning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : i + 1}
                      </div>
                      {/* Label */}
                      <div className="flex-1 min-w-0">
                        <div className={`text-xs font-semibold ${done ? 'text-emerald-700' : 'text-foreground'}`}>{step.label}</div>
                        <div className="text-[10px] text-muted-foreground">{step.desc}</div>
                      </div>
                      {/* Output toggle */}
                      {hasOutput && (
                        <button data-testid={`toggle-output-${step.id}`} onClick={() => setExpandedStep(isExpanded ? null : step.id)} className="p-1 text-muted-foreground hover:text-foreground">
                          <ChevronDown className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                        </button>
                      )}
                      {/* Run button */}
                      <button
                        data-testid={`run-${step.id}`}
                        onClick={() => runStep(step)}
                        disabled={!enabled || isRunning || (runningStep && runningStep !== step.id)}
                        className={`flex items-center gap-1 px-2.5 py-1 text-[10px] font-bold rounded transition-all flex-shrink-0
                          ${!enabled || (runningStep && runningStep !== step.id) ? 'bg-secondary text-muted-foreground cursor-not-allowed' :
                            isRunning ? 'bg-secondary text-muted-foreground' :
                            done ? 'bg-secondary text-foreground hover:bg-secondary/80' :
                            'bg-foreground text-white hover:bg-foreground/90'}`}
                      >
                        {isRunning ? <><Loader2 className="w-2.5 h-2.5 animate-spin" /> Running...</> :
                         done ? <><RotateCcw className="w-2.5 h-2.5" /> Redo</> :
                         <><Play className="w-2.5 h-2.5" /> Run</>}
                      </button>
                    </div>
                    {/* Output panel */}
                    {isExpanded && hasOutput && (
                      <div className="bg-zinc-950 px-4 py-2 border-t border-zinc-800">
                        <pre data-testid={`output-${step.id}`} className="text-[10px] font-mono text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-32 overflow-y-auto">{stepOutputs[step.id]}</pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Post-provision actions */}
            {allDone && (
              <div className="px-4 py-3 border-t border-border bg-emerald-50/30 flex items-center gap-2">
                <button data-testid="go-autonomous-btn" onClick={goAutonomous}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold bg-foreground text-white rounded hover:bg-foreground/90 transition-colors">
                  <Zap className="w-3 h-3" /> Go Autonomous
                </button>
                <span className="text-[10px] text-muted-foreground">Tell the agent all tools are ready</span>
              </div>
            )}
          </div>
        )}
      </div>

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
            {provStatus?.credits_cents > 0 && <span>Credits: <b className="text-foreground">${(provStatus.credits_cents / 100).toFixed(2)}</b></span>}
            <span>VMs: <b className="text-foreground">{sb.live_sandboxes || 0}</b></span>
            <span>Ops: <b className="text-foreground">{sb.total_operations || 0}</b></span>
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
  if (!hasSandbox) {
    return (
      <div data-testid="terminal-no-sandbox" className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Terminal className="w-8 h-8 text-zinc-200 mb-2" />
        <p className="text-sm font-medium text-foreground mb-1">No sandbox provisioned</p>
        <p className="text-[10px] text-muted-foreground">Create a sandbox first to access the live terminal.</p>
      </div>
    );
  }

  if (!terminalUrl) {
    return (
      <div data-testid="terminal-connect" className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Terminal className="w-8 h-8 text-zinc-200 mb-3" />
        <p className="text-sm font-medium text-foreground mb-1">Live Terminal</p>
        <p className="text-[10px] text-muted-foreground mb-4">Open an interactive shell session into the agent's sandbox VM.</p>
        <button
          data-testid="connect-terminal-btn"
          onClick={onConnect}
          disabled={loading}
          className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold bg-foreground text-white rounded hover:bg-foreground/90 disabled:opacity-50 transition-colors"
        >
          {loading ? <><Loader2 className="w-3 h-3 animate-spin" /> Connecting...</> : <><Terminal className="w-3 h-3" /> Connect</>}
        </button>
      </div>
    );
  }

  return (
    <div data-testid="terminal-view" className="bg-white border border-border rounded-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-zinc-950">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[10px] font-mono text-zinc-300">sandbox shell</span>
        </div>
        <div className="flex items-center gap-2">
          <a href={terminalUrl} target="_blank" rel="noopener noreferrer"
            data-testid="terminal-external-link"
            className="text-[10px] text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition-colors">
            <ExternalLink className="w-3 h-3" /> Open in new tab
          </a>
          <button data-testid="reconnect-terminal-btn" onClick={onConnect} disabled={loading}
            className="text-[10px] text-zinc-400 hover:text-zinc-200 flex items-center gap-1 transition-colors">
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} /> Reconnect
          </button>
        </div>
      </div>
      <iframe
        data-testid="terminal-iframe"
        src={terminalUrl}
        title="Sandbox Terminal"
        className="w-full bg-zinc-950 border-0"
        style={{ height: '520px' }}
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
      />
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
