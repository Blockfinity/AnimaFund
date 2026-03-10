import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { Shield, Server, Package, Terminal, Eye, FileText, CheckCircle2, Play, RotateCcw, ChevronRight, Loader2, XCircle, AlertTriangle } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const STEPS = [
  { id: 'prerequisites', label: 'Check Prerequisites', desc: 'Verify Conway API key and credits', icon: Shield },
  { id: 'create_sandbox', label: 'Create Sandbox VM', desc: 'Provision isolated cloud VM for agent', icon: Server },
  { id: 'install_system_tools', label: 'Install System Tools', desc: 'git, curl, node, python3 inside sandbox', icon: Package },
  { id: 'install_conway_terminal', label: 'Install Conway Terminal', desc: 'Conway CLI tools inside sandbox', icon: Terminal },
  { id: 'install_openclaw', label: 'Install OpenClaw', desc: 'Browser agent inside sandbox', icon: Eye },
  { id: 'configure_agent', label: 'Configure Agent', desc: 'Push genesis prompt, skills, constitution', icon: FileText },
  { id: 'verify_tools', label: 'Verify Tools', desc: 'Run functional tests inside sandbox', icon: CheckCircle2 },
  { id: 'start_agent', label: 'Start Agent', desc: 'Launch autonomous engine in sandbox', icon: Play },
];

function StatusBadge({ status }) {
  if (status === 'complete') return <span data-testid="status-complete" className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-950 text-emerald-400 border border-emerald-800"><CheckCircle2 className="w-3 h-3" /> DONE</span>;
  if (status === 'failed') return <span data-testid="status-failed" className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded bg-red-950 text-red-400 border border-red-800"><XCircle className="w-3 h-3" /> FAILED</span>;
  if (status === 'running') return <span data-testid="status-running" className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded bg-amber-950 text-amber-400 border border-amber-800"><Loader2 className="w-3 h-3 animate-spin" /> RUNNING</span>;
  return <span data-testid="status-pending" className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded bg-zinc-900 text-zinc-500 border border-zinc-800">PENDING</span>;
}

export default function AgentSetup() {
  const [steps, setSteps] = useState(STEPS.map(s => ({ ...s, status: 'pending', detail: '', output: '' })));
  const [sandboxId, setSandboxId] = useState(null);
  const [runningStep, setRunningStep] = useState(null);
  const [expandedStep, setExpandedStep] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/agent-setup/status`);
      const data = await res.json();
      if (data.steps) {
        setSteps(prev => prev.map((step, i) => {
          const remote = data.steps[i];
          if (remote) return { ...step, status: remote.status, detail: remote.detail || '', output: remote.output || '' };
          return step;
        }));
      }
      if (data.sandbox_id) setSandboxId(data.sandbox_id);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const runStep = async (stepId) => {
    setRunningStep(stepId);
    setSteps(prev => prev.map(s => s.id === stepId ? { ...s, status: 'running', detail: 'Executing...', output: '' } : s));
    setExpandedStep(stepId);

    try {
      const res = await fetch(`${API}/api/agent-setup/step/${stepId.replace(/_/g, '-')}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
      const data = await res.json();

      setSteps(prev => prev.map(s => {
        if (s.id !== stepId) return s;
        return {
          ...s,
          status: data.success ? 'complete' : 'failed',
          detail: data.detail || data.error || data.message || (data.success ? 'Complete' : 'Failed'),
          output: data.output || '',
        };
      }));

      if (data.sandbox_id) setSandboxId(data.sandbox_id);
      if (data.success) toast.success(`${stepId.replace(/_/g, ' ')} complete`);
      else toast.error(data.error || 'Step failed');
    } catch (e) {
      setSteps(prev => prev.map(s => s.id === stepId ? { ...s, status: 'failed', detail: e.message } : s));
      toast.error(e.message);
    }
    setRunningStep(null);
  };

  const handleReset = async () => {
    if (!window.confirm('Reset setup wizard state? This will NOT delete the sandbox.')) return;
    try {
      await fetch(`${API}/api/agent-setup/reset`, { method: 'POST' });
      setSteps(STEPS.map(s => ({ ...s, status: 'pending', detail: '', output: '' })));
      setSandboxId(null);
      setExpandedStep(null);
      toast.success('Setup state reset');
    } catch (e) { toast.error(e.message); }
  };

  const completedCount = steps.filter(s => s.status === 'complete').length;
  const allComplete = completedCount === steps.length;

  // Determine which step should be active next
  const nextStepIdx = steps.findIndex(s => s.status !== 'complete');

  return (
    <div data-testid="agent-setup-wizard" className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground tracking-tight">Agent Setup Wizard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Securely provision your agent inside an isolated sandbox VM</p>
        </div>
        <div className="flex items-center gap-3">
          {sandboxId && (
            <div className="text-[10px] font-mono text-muted-foreground bg-secondary px-2 py-1 rounded" data-testid="sandbox-id-display">
              Sandbox: {sandboxId.slice(0, 12)}...
            </div>
          )}
          <button data-testid="reset-setup-btn" onClick={handleReset} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground bg-secondary hover:bg-secondary/80 rounded-md transition-colors">
            <RotateCcw className="w-3 h-3" /> Reset
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="bg-secondary rounded-full h-2 overflow-hidden">
        <div className="bg-foreground h-full transition-all duration-500 rounded-full" style={{ width: `${(completedCount / steps.length) * 100}%` }} data-testid="setup-progress-bar" />
      </div>
      <div className="text-xs text-muted-foreground text-right">{completedCount}/{steps.length} steps complete</div>

      {/* Security notice */}
      <div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
        <div className="text-xs text-amber-800 leading-relaxed">
          <strong>Sandbox isolation:</strong> All tools are installed inside the agent's Conway Cloud VM. Nothing runs on the host system.
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isActive = idx === nextStepIdx;
          const isExpanded = expandedStep === step.id;
          const canRun = idx === 0 || steps[idx - 1].status === 'complete';
          const isRunning = runningStep === step.id;

          return (
            <div key={step.id} data-testid={`setup-step-${step.id}`}
              className={`border rounded-lg overflow-hidden transition-all duration-200 ${
                step.status === 'complete' ? 'border-emerald-200 bg-emerald-50/50' :
                step.status === 'failed' ? 'border-red-200 bg-red-50/30' :
                isActive ? 'border-foreground/30 bg-white shadow-sm' :
                'border-border bg-white/50'
              }`}>
              {/* Step header */}
              <div className="flex items-center gap-3 px-4 py-3 cursor-pointer" onClick={() => setExpandedStep(isExpanded ? null : step.id)}>
                {/* Step number */}
                <div className={`w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 text-xs font-bold ${
                  step.status === 'complete' ? 'bg-emerald-100 text-emerald-700' :
                  step.status === 'failed' ? 'bg-red-100 text-red-700' :
                  isActive ? 'bg-foreground text-white' :
                  'bg-secondary text-muted-foreground'
                }`}>
                  {step.status === 'complete' ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5 text-muted-foreground" />
                    <span className={`text-sm font-semibold ${step.status === 'complete' ? 'text-emerald-700' : 'text-foreground'}`}>{step.label}</span>
                    <StatusBadge status={isRunning ? 'running' : step.status} />
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{step.detail || step.desc}</p>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {canRun && step.status !== 'complete' && (
                    <button
                      data-testid={`run-step-${step.id}`}
                      onClick={(e) => { e.stopPropagation(); runStep(step.id); }}
                      disabled={isRunning || !!runningStep}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                        isRunning || runningStep ? 'bg-secondary text-muted-foreground cursor-not-allowed' :
                        'bg-foreground text-white hover:bg-foreground/90'
                      }`}
                    >
                      {isRunning ? <><Loader2 className="w-3 h-3 animate-spin" /> Running...</> : <><Play className="w-3 h-3" /> Run</>}
                    </button>
                  )}
                  {step.status === 'complete' && canRun && (
                    <button
                      data-testid={`rerun-step-${step.id}`}
                      onClick={(e) => { e.stopPropagation(); runStep(step.id); }}
                      disabled={isRunning || !!runningStep}
                      className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium text-muted-foreground hover:text-foreground bg-secondary rounded transition-colors"
                    >
                      <RotateCcw className="w-2.5 h-2.5" /> Retry
                    </button>
                  )}
                  <ChevronRight className={`w-4 h-4 text-muted-foreground transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                </div>
              </div>

              {/* Expanded output */}
              {isExpanded && step.output && (
                <div className="border-t border-border bg-zinc-950 px-4 py-3">
                  <pre data-testid={`output-${step.id}`} className="text-[11px] font-mono text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">{step.output}</pre>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Completion message */}
      {allComplete && (
        <div data-testid="setup-complete-banner" className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <div>
            <div className="text-sm font-bold text-emerald-800">Agent Fully Provisioned</div>
            <div className="text-xs text-emerald-700">All tools installed inside sandbox. Agent is autonomous.</div>
          </div>
        </div>
      )}
    </div>
  );
}
