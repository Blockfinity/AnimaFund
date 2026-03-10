import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import {
  Server, Terminal, Eye, FileText, Play, RotateCcw, Loader2,
  CheckCircle2, MessageSquare, Shield, Zap, Send,
  ChevronDown, Globe, Cpu, Wallet, ExternalLink,
  HardDrive, Radio, Rocket, ScrollText
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const PHASE_LABELS = {
  0: { label: 'Phase 0: Tool Testing', color: 'text-amber-600 bg-amber-50 border-amber-200' },
  1: { label: 'Phase 1: Earn $5,000', color: 'text-blue-600 bg-blue-50 border-blue-200' },
  2: { label: 'Phase 2: Earn $10,000', color: 'text-purple-600 bg-purple-50 border-purple-200' },
  3: { label: 'Phase 3: Create Fund', color: 'text-emerald-600 bg-emerald-50 border-emerald-200' },
};

/* ─── Provision Actions ────────────────────────────────── */
const SECTIONS = [
  {
    title: 'Infrastructure',
    items: [
      { id: 'sandbox', label: 'Create Sandbox', desc: 'Conway Cloud VM (2 vCPU, 4GB, 40GB)', action: '/api/provision/create-sandbox', icon: Server, needs: null },
      { id: 'terminal', label: 'Install Terminal', desc: 'Conway CLI + MCP server + system tools + Node.js', action: '/api/provision/install-terminal', icon: Terminal, needs: 'sandbox' },
      { id: 'openclaw', label: 'Install OpenClaw', desc: 'Autonomous browser agent with MCP integration', action: '/api/provision/install-openclaw', icon: Eye, needs: 'sandbox' },
    ],
  },
  {
    title: 'Capabilities',
    items: [
      { id: 'compute', label: 'Test Compute', desc: 'Verify Conway inference API (GPT, Claude, Gemini, Kimi)', action: '/api/provision/test-compute', icon: Cpu, needs: null },
      { id: 'expose', label: 'Expose Port', desc: 'Make a sandbox port public with URL', action: null, icon: Globe, needs: 'sandbox', custom: 'expose' },
      { id: 'webterminal', label: 'Web Terminal', desc: 'Browser terminal access to sandbox', action: '/api/provision/web-terminal', icon: HardDrive, needs: 'sandbox' },
    ],
  },
  {
    title: 'Deploy',
    items: [
      { id: 'skills', label: 'Load Skills', desc: 'Push skill definitions into sandbox', action: '/api/provision/load-skills', icon: FileText, needs: 'sandbox' },
      { id: 'deploy', label: 'Deploy Agent', desc: 'Push engine + config into sandbox, start agent (born in Phase 0)', action: '/api/provision/deploy-agent', icon: Rocket, needs: 'sandbox' },
    ],
  },
  {
    title: 'Communicate',
    items: [
      { id: 'nudge', label: 'Go Autonomous', desc: 'Tell the agent all tools are ready', action: '/api/provision/nudge', icon: Zap, needs: null },
    ],
  },
];

function StatusChip({ label, active, icon: Icon }) {
  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-medium border transition-colors ${active ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : 'border-zinc-200 bg-zinc-50 text-zinc-400'}`}>
      {Icon && <Icon className="w-3 h-3" />}
      {label}
    </div>
  );
}

export default function AgentSetup() {
  const [status, setStatus] = useState(null);
  const [phaseState, setPhaseState] = useState(null);
  const [runningAction, setRunningAction] = useState(null);
  const [expandedOutput, setExpandedOutput] = useState(null);
  const [outputs, setOutputs] = useState({});
  const [customNudge, setCustomNudge] = useState('');
  const [portInput, setPortInput] = useState('3000');
  const [subdomainInput, setSubdomainInput] = useState('');
  const [agentLogs, setAgentLogs] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const [statusRes, phaseRes] = await Promise.all([
        fetch(`${API}/api/provision/status`),
        fetch(`${API}/api/provision/phase-state`),
      ]);
      setStatus(await statusRes.json());
      const phaseData = await phaseRes.json();
      if (phaseData.success) setPhaseState(phaseData.phase_state);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const hasSandbox = status?.sandbox?.status === 'active';
  const tools = status?.tools || {};

  const isDone = (id) => {
    if (id === 'sandbox') return hasSandbox;
    if (id === 'terminal') return tools['conway-terminal']?.installed;
    if (id === 'openclaw') return tools['openclaw']?.installed;
    if (id === 'compute') return status?.compute_verified;
    if (id === 'skills') return status?.skills_loaded;
    if (id === 'expose') return (status?.ports?.length || 0) > 0;
    if (id === 'webterminal') return !!status?.sandbox?.terminal_url;
    if (id === 'deploy') return tools['engine']?.deployed;
    return false;
  };

  const canRun = (item) => {
    if (!item.needs) return true;
    if (item.needs === 'sandbox') return hasSandbox;
    return false;
  };

  const fetchAgentLogs = async () => {
    try {
      const res = await fetch(`${API}/api/provision/agent-logs?lines=30`);
      const data = await res.json();
      if (data.success) setAgentLogs(data);
    } catch { /* ignore */ }
  };

  const runAction = async (item) => {
    if (item.custom === 'expose') {
      await exposePort();
      return;
    }
    setRunningAction(item.id);
    try {
      const res = await fetch(`${API}${item.action}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
      const data = await res.json();
      if (data.output) { setOutputs(prev => ({ ...prev, [item.id]: data.output })); setExpandedOutput(item.id); }
      if (data.terminal_url) { setOutputs(prev => ({ ...prev, [item.id]: `Terminal URL: ${data.terminal_url}` })); setExpandedOutput(item.id); }
      if (data.response) { setOutputs(prev => ({ ...prev, [item.id]: `Model: ${data.model}\nResponse: ${data.response}` })); setExpandedOutput(item.id); }
      data.success ? toast.success(`${item.label} done`) : toast.error(data.error || 'Failed');
      await fetchStatus();
    } catch (e) { toast.error(e.message); }
    setRunningAction(null);
  };

  const exposePort = async () => {
    setRunningAction('expose');
    try {
      const body = { port: parseInt(portInput) || 3000 };
      if (subdomainInput.trim()) body.subdomain = subdomainInput.trim();
      const res = await fetch(`${API}/api/provision/expose-port`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const data = await res.json();
      if (data.success) {
        const url = data.port?.public_url || data.port?.custom_url;
        setOutputs(prev => ({ ...prev, expose: `Port ${body.port} exposed:\n${url}${data.port?.custom_url ? '\nCustom: ' + data.port.custom_url : ''}` }));
        setExpandedOutput('expose');
        toast.success(`Port ${body.port} exposed`);
      } else { toast.error(data.error || 'Failed'); }
      await fetchStatus();
    } catch (e) { toast.error(e.message); }
    setRunningAction(null);
  };

  const sendCustomNudge = async () => {
    if (!customNudge.trim()) return;
    try {
      await fetch(`${API}/api/provision/nudge/custom`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: customNudge }) });
      toast.success('Message sent to agent');
      setCustomNudge('');
      await fetchStatus();
    } catch (e) { toast.error(e.message); }
  };

  return (
    <div data-testid="agent-provision-panel" className="max-w-2xl mx-auto space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-foreground tracking-tight">Agent Provisioning</h1>
        <p className="text-sm text-muted-foreground mt-1">Your agent is alive. Equip it with the full Conway ecosystem.</p>
      </div>

      {/* Awareness notice */}
      <div className="flex items-start gap-3 p-3 rounded-lg border border-border bg-secondary/50">
        <Shield className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
        <div className="text-xs text-muted-foreground leading-relaxed">
          Everything installs inside the agent's <strong>sandbox VM</strong>. The agent reads a provisioning status file each turn and knows what's being built for it.
        </div>
      </div>

      {/* Status chips */}
      {status && (
        <div data-testid="provision-status-chips" className="flex flex-wrap gap-2">
          <StatusChip label={hasSandbox ? `VM: ${status.sandbox.short_id || status.sandbox.id?.slice(0, 10) || 'active'}` : 'VM: none'} active={hasSandbox} icon={Server} />
          <StatusChip label={`Terminal: ${tools['conway-terminal']?.installed ? 'yes' : 'no'}`} active={tools['conway-terminal']?.installed} icon={Terminal} />
          <StatusChip label={`OpenClaw: ${tools['openclaw']?.installed ? 'yes' : 'no'}`} active={tools['openclaw']?.installed} icon={Eye} />
          <StatusChip label={`Compute: ${status.compute_verified ? 'verified' : 'no'}`} active={status.compute_verified} icon={Cpu} />
          <StatusChip label={`Ports: ${status.ports?.length || 0}`} active={(status.ports?.length || 0) > 0} icon={Globe} />
          <StatusChip label={`Skills: ${status.skills_loaded ? 'loaded' : 'no'}`} active={status.skills_loaded} icon={FileText} />
          <StatusChip label={`Engine: ${tools['engine']?.deployed ? 'deployed' : 'no'}`} active={tools['engine']?.deployed} icon={Rocket} />
          <StatusChip label={`Credits: $${(status.credits_cents / 100).toFixed(2)}`} active={status.credits_cents > 0} icon={Wallet} />
        </div>
      )}

      {/* Phase state */}
      {phaseState && (
        <div data-testid="phase-state-display" className={`flex items-center justify-between p-3 rounded-lg border ${PHASE_LABELS[phaseState.current_phase || 0]?.color || 'border-zinc-200 bg-zinc-50 text-zinc-600'}`}>
          <div className="flex items-center gap-2">
            <Rocket className="w-4 h-4" />
            <span className="text-sm font-bold">{PHASE_LABELS[phaseState.current_phase || 0]?.label || `Phase ${phaseState.current_phase}`}</span>
          </div>
          {phaseState.current_phase === 0 && phaseState.tool_tests && (
            <span className="text-xs font-mono">{Object.values(phaseState.tool_tests).filter(v => v === 'PASS').length}/10 tools tested</span>
          )}
        </div>
      )}

      {/* Sections */}
      {SECTIONS.map((section) => (
        <div key={section.title} className="space-y-2">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-1">{section.title}</div>
          {section.items.map((item) => {
            const Icon = item.icon;
            const done = isDone(item.id);
            const enabled = canRun(item);
            const isRunning = runningAction === item.id;
            const isExpanded = expandedOutput === item.id;
            const hasOutput = outputs[item.id];

            return (
              <div key={item.id} data-testid={`provision-${item.id}`} className={`border rounded-lg transition-all ${done ? 'border-emerald-200 bg-emerald-50/40' : enabled ? 'border-border bg-white' : 'border-border/50 bg-secondary/30 opacity-50'}`}>
                <div className="flex items-center gap-3 px-4 py-3">
                  <div className={`w-7 h-7 rounded flex items-center justify-center flex-shrink-0 ${done ? 'bg-emerald-100 text-emerald-700' : 'bg-secondary text-muted-foreground'}`}>
                    {done ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Icon className="w-3.5 h-3.5" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold text-foreground">{item.label}</div>
                    <p className="text-[11px] text-muted-foreground">{item.desc}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {/* Port input for expose */}
                    {item.custom === 'expose' && enabled && (
                      <div className="flex items-center gap-1">
                        <input data-testid="port-input" type="number" value={portInput} onChange={e => setPortInput(e.target.value)} className="w-16 px-2 py-1 text-xs border border-border rounded bg-secondary/50 text-foreground" placeholder="Port" />
                        <input data-testid="subdomain-input" type="text" value={subdomainInput} onChange={e => setSubdomainInput(e.target.value)} className="w-24 px-2 py-1 text-xs border border-border rounded bg-secondary/50 text-foreground" placeholder="subdomain" />
                      </div>
                    )}
                    {hasOutput && (
                      <button data-testid={`toggle-output-${item.id}`} onClick={() => setExpandedOutput(isExpanded ? null : item.id)} className="p-1 text-muted-foreground hover:text-foreground">
                        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                      </button>
                    )}
                    <button
                      data-testid={`run-provision-${item.id}`}
                      onClick={() => runAction(item)}
                      disabled={!enabled || isRunning || (runningAction && runningAction !== item.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                        !enabled || (runningAction && runningAction !== item.id) ? 'bg-secondary text-muted-foreground cursor-not-allowed' :
                        isRunning ? 'bg-secondary text-muted-foreground' :
                        done ? 'bg-secondary text-foreground hover:bg-secondary/80' :
                        'bg-foreground text-white hover:bg-foreground/90'
                      }`}
                    >
                      {isRunning ? <><Loader2 className="w-3 h-3 animate-spin" /> Running...</> :
                       done ? <><RotateCcw className="w-3 h-3" /> Redo</> :
                       <><Play className="w-3 h-3" /> Run</>}
                    </button>
                  </div>
                </div>
                {/* Output */}
                {isExpanded && hasOutput && (
                  <div className="border-t border-border bg-zinc-950 px-4 py-3">
                    <pre data-testid={`output-${item.id}`} className="text-[11px] font-mono text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">{outputs[item.id]}</pre>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}

      {/* Exposed ports list */}
      {status?.ports?.length > 0 && (
        <div className="space-y-1">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-1">Exposed Ports</div>
          {status.ports.map((p, i) => (
            <div key={i} data-testid={`exposed-port-${p.port}`} className="flex items-center gap-2 px-3 py-2 text-xs bg-secondary/50 rounded border border-border">
              <Radio className="w-3 h-3 text-emerald-500" />
              <span className="font-mono font-bold">:{p.port}</span>
              <a href={p.public_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline flex items-center gap-1 truncate">
                {p.public_url} <ExternalLink className="w-3 h-3" />
              </a>
              {p.custom_url && <a href={p.custom_url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline text-[10px]">{p.custom_url}</a>}
            </div>
          ))}
        </div>
      )}

      {/* Agent logs viewer */}
      {hasSandbox && tools['engine']?.deployed && (
        <div className="border border-border rounded-lg bg-white">
          <div className="flex items-center justify-between px-4 py-2 border-b border-border">
            <div className="flex items-center gap-2">
              <ScrollText className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-semibold text-foreground">Agent Logs (from sandbox)</span>
            </div>
            <button data-testid="refresh-logs-btn" onClick={fetchAgentLogs} className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium text-muted-foreground hover:text-foreground bg-secondary rounded">
              <RotateCcw className="w-2.5 h-2.5" /> Refresh
            </button>
          </div>
          {agentLogs ? (
            <div className="bg-zinc-950 px-4 py-3 max-h-48 overflow-y-auto">
              <pre className="text-[11px] font-mono text-zinc-300 whitespace-pre-wrap leading-relaxed">{agentLogs.stdout || agentLogs.stderr || 'No logs yet'}</pre>
            </div>
          ) : (
            <div className="px-4 py-3 text-xs text-muted-foreground">Click Refresh to load logs from sandbox</div>
          )}
        </div>
      )}

      {/* Message the Agent */}
      <div className="border border-border rounded-lg bg-white">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-border">
          <MessageSquare className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground">Message the Agent</span>
          <span className="text-[10px] text-muted-foreground">(sees it next turn)</span>
        </div>
        <div className="flex gap-2 p-3">
          <input
            data-testid="custom-nudge-input"
            type="text"
            value={customNudge}
            onChange={(e) => setCustomNudge(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendCustomNudge()}
            placeholder="e.g. Test your curl, register a domain, deploy an app on port 3000"
            className="flex-1 px-3 py-2 text-sm border border-border rounded-md bg-secondary/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-foreground"
          />
          <button
            data-testid="send-nudge-btn"
            onClick={sendCustomNudge}
            disabled={!customNudge.trim()}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold bg-foreground text-white rounded-md hover:bg-foreground/90 disabled:bg-secondary disabled:text-muted-foreground disabled:cursor-not-allowed"
          >
            <Send className="w-3 h-3" /> Send
          </button>
        </div>
      </div>

      {/* Recent nudges */}
      {status?.nudges?.length > 0 && (
        <div className="space-y-1">
          <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest px-1">Recent messages to agent</div>
          {status.nudges.slice().reverse().map((n, i) => (
            <div key={i} data-testid={`nudge-${i}`} className="flex items-start gap-2 px-3 py-2 text-xs bg-secondary/50 rounded border border-border">
              <Send className="w-3 h-3 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="text-foreground break-words">{n.message}</div>
                <div className="text-[10px] text-muted-foreground mt-0.5">{new Date(n.timestamp).toLocaleString()}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
