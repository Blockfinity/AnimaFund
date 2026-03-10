import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import {
  Server, Terminal, Eye, FileText, Play, RotateCcw, Loader2,
  CheckCircle2, XCircle, MessageSquare, Shield, Zap, Send, ChevronDown
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const PROVISIONS = [
  {
    id: 'sandbox',
    label: 'Create Sandbox',
    desc: 'Provision an isolated Conway Cloud VM',
    action: '/api/provision/create-sandbox',
    icon: Server,
    needs: null,
  },
  {
    id: 'terminal',
    label: 'Install Terminal',
    desc: 'Conway CLI tools inside sandbox',
    action: '/api/provision/install-terminal',
    icon: Terminal,
    needs: 'sandbox',
  },
  {
    id: 'openclaw',
    label: 'Install OpenClaw',
    desc: 'Browser agent inside sandbox',
    action: '/api/provision/install-openclaw',
    icon: Eye,
    needs: 'sandbox',
  },
  {
    id: 'skills',
    label: 'Load Skills',
    desc: 'Push skill definitions into sandbox',
    action: '/api/provision/load-skills',
    icon: FileText,
    needs: 'sandbox',
  },
  {
    id: 'nudge',
    label: 'Go Autonomous',
    desc: 'Tell the agent its tools are ready',
    action: '/api/provision/nudge',
    icon: Zap,
    needs: 'sandbox',
  },
];

export default function AgentSetup() {
  const [status, setStatus] = useState(null);
  const [runningAction, setRunningAction] = useState(null);
  const [expandedOutput, setExpandedOutput] = useState(null);
  const [outputs, setOutputs] = useState({});
  const [customNudge, setCustomNudge] = useState('');

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/provision/status`);
      const data = await res.json();
      setStatus(data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const runAction = async (provision) => {
    setRunningAction(provision.id);
    try {
      const res = await fetch(`${API}${provision.action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();

      if (data.output) {
        setOutputs(prev => ({ ...prev, [provision.id]: data.output }));
        setExpandedOutput(provision.id);
      }

      if (data.success) {
        toast.success(`${provision.label} complete`);
      } else {
        toast.error(data.error || 'Action failed');
      }

      await fetchStatus();
    } catch (e) {
      toast.error(e.message);
    }
    setRunningAction(null);
  };

  const sendCustomNudge = async () => {
    if (!customNudge.trim()) return;
    try {
      const res = await fetch(`${API}/api/provision/nudge/custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: customNudge }),
      });
      const data = await res.json();
      if (data.success) {
        toast.success('Nudge sent — agent will see it next turn');
        setCustomNudge('');
        await fetchStatus();
      }
    } catch (e) { toast.error(e.message); }
  };

  const hasSandbox = status?.sandbox?.status === 'active';
  const tools = status?.tools || {};

  const isProvisionDone = (id) => {
    if (id === 'sandbox') return hasSandbox;
    if (id === 'terminal') return tools['conway-terminal']?.installed;
    if (id === 'openclaw') return tools['openclaw']?.installed;
    if (id === 'skills') return status?.skills_loaded;
    if (id === 'nudge') return false; // always allow re-nudge
    return false;
  };

  const canRun = (provision) => {
    if (provision.needs === null) return true;
    if (provision.needs === 'sandbox') return hasSandbox;
    return false;
  };

  return (
    <div data-testid="agent-provision-panel" className="max-w-2xl mx-auto space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-foreground tracking-tight">Agent Provisioning</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Your agent is alive. Equip it with tools — it's aware of each step.
        </p>
      </div>

      {/* Agent awareness indicator */}
      <div className="flex items-start gap-3 p-3 rounded-lg border border-border bg-secondary/50">
        <Shield className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
        <div className="text-xs text-muted-foreground leading-relaxed">
          Everything installs inside the agent's <strong>sandbox VM</strong>. The agent sees a provisioning status file each turn and knows what tools are being built for it. After you click "Go Autonomous", it takes over.
        </div>
      </div>

      {/* Status summary */}
      {status && (
        <div data-testid="provision-status-summary" className="flex flex-wrap gap-3 text-xs">
          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border ${hasSandbox ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-border bg-secondary text-muted-foreground'}`}>
            <Server className="w-3 h-3" />
            Sandbox: {hasSandbox ? status.sandbox.id?.slice(0, 10) + '...' : 'none'}
          </div>
          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border ${tools['conway-terminal']?.installed ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-border bg-secondary text-muted-foreground'}`}>
            <Terminal className="w-3 h-3" />
            Terminal: {tools['conway-terminal']?.installed ? 'installed' : 'none'}
          </div>
          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border ${tools['openclaw']?.installed ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-border bg-secondary text-muted-foreground'}`}>
            <Eye className="w-3 h-3" />
            OpenClaw: {tools['openclaw']?.installed ? 'installed' : 'none'}
          </div>
          <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border ${status.skills_loaded ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-border bg-secondary text-muted-foreground'}`}>
            <FileText className="w-3 h-3" />
            Skills: {status.skills_loaded ? 'loaded' : 'none'}
          </div>
          {status.credits_cents !== undefined && (
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-border bg-secondary text-muted-foreground">
              Credits: ${(status.credits_cents / 100).toFixed(2)}
            </div>
          )}
        </div>
      )}

      {/* Provision buttons */}
      <div className="space-y-2">
        {PROVISIONS.map((p) => {
          const Icon = p.icon;
          const done = isProvisionDone(p.id);
          const enabled = canRun(p);
          const isRunning = runningAction === p.id;
          const hasOutput = outputs[p.id];
          const isExpanded = expandedOutput === p.id;

          return (
            <div key={p.id} data-testid={`provision-${p.id}`} className={`border rounded-lg transition-all ${done ? 'border-emerald-200 bg-emerald-50/40' : enabled ? 'border-border bg-white' : 'border-border/50 bg-secondary/30 opacity-60'}`}>
              <div className="flex items-center gap-3 px-4 py-3">
                {/* Icon */}
                <div className={`w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 ${done ? 'bg-emerald-100 text-emerald-700' : 'bg-secondary text-muted-foreground'}`}>
                  {done ? <CheckCircle2 className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                </div>

                {/* Label */}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-foreground">{p.label}</div>
                  <p className="text-[11px] text-muted-foreground">{p.desc}</p>
                </div>

                {/* Action */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  {hasOutput && (
                    <button
                      data-testid={`toggle-output-${p.id}`}
                      onClick={() => setExpandedOutput(isExpanded ? null : p.id)}
                      className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium text-muted-foreground hover:text-foreground bg-secondary rounded transition-colors"
                    >
                      <ChevronDown className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                      Output
                    </button>
                  )}
                  <button
                    data-testid={`run-provision-${p.id}`}
                    onClick={() => runAction(p)}
                    disabled={!enabled || isRunning || (runningAction && runningAction !== p.id)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                      !enabled || (runningAction && runningAction !== p.id)
                        ? 'bg-secondary text-muted-foreground cursor-not-allowed'
                        : isRunning
                        ? 'bg-secondary text-muted-foreground'
                        : done
                        ? 'bg-secondary text-foreground hover:bg-secondary/80'
                        : 'bg-foreground text-white hover:bg-foreground/90'
                    }`}
                  >
                    {isRunning ? <><Loader2 className="w-3 h-3 animate-spin" /> Running...</> :
                     done ? <><RotateCcw className="w-3 h-3" /> Redo</> :
                     <><Play className="w-3 h-3" /> {p.label}</>}
                  </button>
                </div>
              </div>

              {/* Output panel */}
              {isExpanded && hasOutput && (
                <div className="border-t border-border bg-zinc-950 px-4 py-3">
                  <pre data-testid={`output-${p.id}`} className="text-[11px] font-mono text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">{outputs[p.id]}</pre>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Custom nudge */}
      <div className="border border-border rounded-lg bg-white">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-border">
          <MessageSquare className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-xs font-semibold text-foreground">Message the Agent</span>
          <span className="text-[10px] text-muted-foreground">(agent sees this on its next turn)</span>
        </div>
        <div className="flex gap-2 p-3">
          <input
            data-testid="custom-nudge-input"
            type="text"
            value={customNudge}
            onChange={(e) => setCustomNudge(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendCustomNudge()}
            placeholder="e.g. Test your curl and git, then report back via Telegram"
            className="flex-1 px-3 py-2 text-sm border border-border rounded-md bg-secondary/50 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-foreground"
          />
          <button
            data-testid="send-nudge-btn"
            onClick={sendCustomNudge}
            disabled={!customNudge.trim()}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold bg-foreground text-white rounded-md hover:bg-foreground/90 disabled:bg-secondary disabled:text-muted-foreground disabled:cursor-not-allowed transition-all"
          >
            <Send className="w-3 h-3" /> Send
          </button>
        </div>
      </div>

      {/* Recent nudges */}
      {status?.nudges?.length > 0 && (
        <div className="space-y-1">
          <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-1">Recent messages to agent</div>
          {status.nudges.slice().reverse().map((n, i) => (
            <div key={i} data-testid={`nudge-${i}`} className="flex items-start gap-2 px-3 py-2 text-xs bg-secondary/50 rounded-md border border-border">
              <Send className="w-3 h-3 text-muted-foreground mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <div className="text-foreground">{n.message}</div>
                <div className="text-[10px] text-muted-foreground mt-0.5">{new Date(n.timestamp).toLocaleString()}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
