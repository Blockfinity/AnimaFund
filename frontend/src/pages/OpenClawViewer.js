import React, { useState, useCallback } from 'react';
import {
  Eye, Globe, Server, Terminal, Zap, ExternalLink, RefreshCw,
  AlertCircle, CheckCircle, Clock, ArrowRight, Play, Box,
  Wifi, Users, CreditCard, Wrench
} from 'lucide-react';
import { useSSETrigger } from '../hooks/useSSE';

const API = process.env.REACT_APP_BACKEND_URL;

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Date.now() - new Date(ts).getTime();
  const s = Math.floor(diff / 1000); if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60); if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60); if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

const TABS = [
  { id: 'live', label: 'Live View', icon: Eye },
  { id: 'sandbox-exec', label: 'VM Console', icon: Terminal },
  { id: 'sandboxes', label: 'Conway VMs', icon: Server },
  { id: 'browsing', label: 'Browsing', icon: Globe },
];

const CAT_ICONS = {
  vm_provision: Server, vm_teardown: Server, vm_network: Wifi,
  openclaw_setup: Zap, openclaw_action: Play,
  tool_install: Wrench, service_deploy: Box, system_setup: Terminal,
  sandbox_exec: Terminal, sandbox_file: Terminal,
  browsing: Globe, payment: CreditCard,
  agent_network: Users, other: Terminal,
};

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

export default function OpenClawViewer({ selectedAgent }) {
  const [tab, setTab] = useState('live');
  const [status, setStatus] = useState(null);
  const [actions, setActions] = useState([]);
  const [categories, setCategories] = useState({});
  const [sandboxData, setSandboxData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [execLog, setExecLog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [statusRes, actionsRes, sandboxRes, browseRes, execRes] = await Promise.all([
        fetch(`${API}/api/openclaw/status`),
        fetch(`${API}/api/openclaw/actions?limit=100`),
        fetch(`${API}/api/openclaw/sandboxes`),
        fetch(`${API}/api/openclaw/browsing?limit=50`),
        fetch(`${API}/api/openclaw/sandbox-exec-log?limit=50`),
      ]);
      if (statusRes.ok) setStatus(await statusRes.json());
      if (actionsRes.ok) {
        const d = await actionsRes.json();
        setActions(d.actions || []);
        setCategories(d.categories || {});
      }
      if (sandboxRes.ok) setSandboxData(await sandboxRes.json());
      if (browseRes.ok) setSessions((await browseRes.json()).sessions || []);
      if (execRes.ok) setExecLog((await execRes.json()).log || []);
    } catch (e) { console.error('OpenClaw fetch error:', e); }
    finally { setLoading(false); }
  }, []);

  // SSE-triggered fetch with fallback. Auto-refresh controlled by SSE connection.
  useSSETrigger(fetchAll, { fallbackMs: autoRefresh ? 5000 : 60000, deps: [selectedAgent] });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const hasActivity = status?.has_activity || false;
  const oc = status?.openclaw || {};
  const sb = status?.sandbox_summary || {};

  return (
    <div data-testid="openclaw-page" className="space-y-4">
      {/* Header Bar */}
      <div className="bg-white border border-border rounded-sm p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-2.5 h-2.5 rounded-full ${hasActivity ? 'bg-green-500 animate-pulse' : 'bg-zinc-300'}`} />
            <h2 className="text-sm font-heading font-semibold text-foreground">
              Conway VM + OpenClaw
            </h2>
            <span className="text-xs text-muted-foreground">
              {hasActivity ? `${sb.total_operations || 0} operations recorded` : 'Idle — agent has not created any sandbox VMs yet'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button data-testid="auto-refresh-toggle" onClick={() => setAutoRefresh(!autoRefresh)}
              className={`text-xs px-2.5 py-1 rounded-sm border transition-colors ${autoRefresh ? 'bg-foreground text-white border-foreground' : 'bg-white text-muted-foreground border-border hover:border-foreground'}`}>
              {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            </button>
            <button data-testid="refresh-btn" onClick={fetchAll} className="p-1.5 rounded-sm border border-border hover:bg-secondary transition-colors">
              <RefreshCw className="w-3.5 h-3.5 text-muted-foreground" />
            </button>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-5 mt-3 pt-3 border-t border-border">
          <StatusPill label="OpenClaw in VM" ok={oc.openclaw_installed} />
          <StatusPill label="Daemon Running" ok={oc.openclaw_daemon_running} />
          <StatusPill label="MCP Configured" ok={oc.mcp_configured} />
          <StatusPill label="Conway Terminal in VM" ok={oc.conway_terminal_in_sandbox} />
          <div className="flex items-center gap-3 ml-auto text-xs text-muted-foreground">
            <span>VMs: <b className="text-foreground">{sb.live_sandboxes || 0}</b> live</span>
            <span>Ports: <b className="text-foreground">{sb.ports_exposed || 0}</b> exposed</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-white border border-border rounded-sm p-1">
        {TABS.map(t => {
          const Icon = t.icon;
          const count = t.id === 'live' ? actions.length :
            t.id === 'sandboxes' ? (sandboxData?.total_live || 0) + (sandboxData?.total_created || 0) :
            t.id === 'browsing' ? sessions.length :
            t.id === 'sandbox-exec' ? execLog.length : null;
          return (
            <button key={t.id} data-testid={`tab-${t.id}`} onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-medium transition-colors
                ${tab === t.id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
              <Icon className="w-3.5 h-3.5" />
              {t.label}
              {count !== null && count > 0 && (
                <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold ${tab === t.id ? 'bg-white/20' : 'bg-secondary'}`}>{count}</span>
              )}
            </button>
          );
        })}
      </div>

      {tab === 'live' && <LiveView actions={actions} categories={categories} sandboxData={sandboxData} sessions={sessions} oc={oc} />}
      {tab === 'sandbox-exec' && <ExecLogView execLog={execLog} />}
      {tab === 'sandboxes' && <SandboxesView data={sandboxData} />}
      {tab === 'browsing' && <BrowsingView sessions={sessions} />}
    </div>
  );
}


function StatusPill({ label, ok }) {
  return (
    <div className="flex items-center gap-1.5 text-xs">
      {ok ? <CheckCircle className="w-3 h-3 text-green-600" /> : <div className="w-3 h-3 rounded-full border border-zinc-300 bg-zinc-100" />}
      <span className={ok ? 'text-foreground font-medium' : 'text-muted-foreground'}>{label}</span>
    </div>
  );
}


function LiveView({ actions, categories, sandboxData, sessions, oc }) {
  if (actions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-72 text-center bg-white border border-border rounded-sm">
        <Server className="w-10 h-10 text-zinc-200 mb-4" />
        <p className="text-sm font-medium text-foreground mb-1">No Conway sandbox activity yet</p>
        <p className="text-xs text-muted-foreground max-w-lg">
          When the agent creates Conway sandbox VMs and installs OpenClaw inside them, all activity will stream here in real-time — sandbox provisioning, OpenClaw setup, browsing sessions, deployments, and agent network communication.
        </p>
        <div className="flex items-center gap-6 mt-5 text-xs text-muted-foreground">
          <span>1. Agent calls <code className="bg-secondary px-1 rounded font-mono">sandbox_create</code></span>
          <ArrowRight className="w-3 h-3" />
          <span>2. Installs OpenClaw inside VM</span>
          <ArrowRight className="w-3 h-3" />
          <span>3. Activity appears here</span>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Action Feed */}
      <div className="col-span-2 bg-white border border-border rounded-sm">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <h3 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider">Live Action Feed</h3>
          <span className="text-[10px] text-muted-foreground">{actions.length} actions</span>
        </div>
        <div className="max-h-[500px] overflow-y-auto divide-y divide-border">
          {actions.slice(0, 40).map((a, i) => <ActionRow key={a.id || i} action={a} />)}
        </div>
      </div>

      {/* Right Panel */}
      <div className="space-y-4">
        {/* OpenClaw State */}
        <div className="bg-white border border-border rounded-sm p-4">
          <h4 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-3">
            OpenClaw State (in VM)
          </h4>
          <div className="space-y-2">
            <StateRow label="Installed" value={oc.openclaw_installed} />
            <StateRow label="Daemon" value={oc.openclaw_daemon_running} />
            <StateRow label="MCP" value={oc.mcp_configured} />
            <StateRow label="Conway Terminal" value={oc.conway_terminal_in_sandbox} />
            {oc.last_openclaw_action && (
              <div className="text-[10px] text-muted-foreground pt-1 border-t border-border">
                Last action: {timeAgo(oc.last_openclaw_action)}
              </div>
            )}
          </div>
        </div>

        {/* Category Breakdown */}
        <div className="bg-white border border-border rounded-sm p-4">
          <h4 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-3">Categories</h4>
          <div className="space-y-1.5">
            {Object.entries(categories).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
              <div key={cat} className="flex items-center justify-between">
                <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded border ${CAT_COLORS[cat] || CAT_COLORS.other}`}>
                  {cat.replace(/_/g, ' ')}
                </span>
                <span className="text-xs font-mono font-bold text-foreground">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Exposed URLs */}
        {sandboxData?.exposed_urls?.length > 0 && (
          <div className="bg-white border border-border rounded-sm p-4">
            <h4 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-3">Public URLs</h4>
            <div className="space-y-2">
              {sandboxData.exposed_urls.map((u, i) => (
                <a key={i} href={u.url} target="_blank" rel="noreferrer"
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1.5 truncate">
                  <ExternalLink className="w-3 h-3 flex-shrink-0" /> {u.url}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Recent Browsing */}
        {sessions.length > 0 && (
          <div className="bg-white border border-border rounded-sm p-4">
            <h4 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-3">Recent Browsing</h4>
            <div className="space-y-2">
              {sessions.slice(0, 5).map((s, i) => (
                <div key={i} className="text-xs">
                  <div className="text-foreground font-mono truncate">{s.url}</div>
                  <div className="text-muted-foreground text-[10px]">{timeAgo(s.timestamp)}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


function StateRow({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-muted-foreground">{label}</span>
      {value
        ? <span className="text-[10px] font-bold text-green-700 bg-green-50 px-1.5 py-0.5 rounded border border-green-200">ACTIVE</span>
        : <span className="text-[10px] font-bold text-zinc-500 bg-zinc-50 px-1.5 py-0.5 rounded border border-zinc-200">PENDING</span>
      }
    </div>
  );
}


function ActionRow({ action }) {
  const [expanded, setExpanded] = useState(false);
  const CatIcon = CAT_ICONS[action.category] || Terminal;
  const catClass = CAT_COLORS[action.category] || CAT_COLORS.other;

  return (
    <div className="px-4 py-2.5 hover:bg-secondary/30 cursor-pointer transition-colors" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-center gap-2.5">
        <CatIcon className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
        <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border whitespace-nowrap ${catClass}`}>
          {action.category.replace(/_/g, ' ')}
        </span>
        <span className="text-xs font-mono font-semibold text-foreground">{action.tool}</span>
        {action.duration_ms > 0 && (
          <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
            <Clock className="w-2.5 h-2.5" /> {action.duration_ms}ms
          </span>
        )}
        {action.error && <AlertCircle className="w-3 h-3 text-red-500" />}
        <span className="text-[10px] text-muted-foreground ml-auto">{timeAgo(action.timestamp)}</span>
        <ArrowRight className={`w-3 h-3 text-muted-foreground transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </div>
      {/* Args preview */}
      {Object.keys(action.arguments).length > 0 && (
        <div className="text-[10px] text-muted-foreground mt-1 font-mono truncate pl-6">
          {action.tool === 'sandbox_exec'
            ? (action.arguments.command || '').slice(0, 120)
            : Object.entries(action.arguments).map(([k, v]) => `${k}: ${typeof v === 'string' ? v.slice(0, 60) : JSON.stringify(v)}`).join(' | ')}
        </div>
      )}
      {expanded && action.result && (
        <div className="mt-2 ml-6 p-2.5 bg-zinc-950 rounded border border-zinc-800">
          <pre className="text-[10px] font-mono text-green-400 whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
            {action.result}
          </pre>
        </div>
      )}
    </div>
  );
}


function ExecLogView({ execLog }) {
  const [filter, setFilter] = useState('all');
  const cats = [...new Set(execLog.map(e => e.category))];
  const filtered = filter === 'all' ? execLog : execLog.filter(e => e.category === filter);

  if (execLog.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Terminal className="w-8 h-8 text-zinc-200 mb-3" />
        <p className="text-sm font-medium text-foreground mb-1">No sandbox commands yet</p>
        <p className="text-xs text-muted-foreground max-w-md">
          Commands the agent runs inside Conway VMs via <code className="bg-secondary px-1 rounded font-mono">sandbox_exec</code> will appear here — including OpenClaw installation, service deployments, and system setup.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-border rounded-sm">
      <div className="px-4 py-3 border-b border-border flex items-center gap-2">
        <h3 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider">VM Console Log</h3>
        <div className="flex items-center gap-1 ml-auto">
          <button onClick={() => setFilter('all')}
            className={`text-[10px] px-2 py-0.5 rounded-sm border transition-colors ${filter === 'all' ? 'bg-foreground text-white border-foreground' : 'border-border text-muted-foreground'}`}>
            All ({execLog.length})
          </button>
          {cats.map(c => (
            <button key={c} onClick={() => setFilter(c)}
              className={`text-[10px] px-2 py-0.5 rounded-sm border transition-colors ${filter === c ? 'bg-foreground text-white border-foreground' : 'border-border text-muted-foreground'}`}>
              {c.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>
      <div className="max-h-[600px] overflow-y-auto divide-y divide-border">
        {filtered.map((entry, i) => (
          <ExecRow key={i} entry={entry} />
        ))}
      </div>
    </div>
  );
}


function ExecRow({ entry }) {
  const [expanded, setExpanded] = useState(false);
  const catClass = CAT_COLORS[entry.category] || CAT_COLORS.other;

  return (
    <div className="px-4 py-2.5 hover:bg-secondary/30 cursor-pointer transition-colors" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-center gap-2.5">
        <Terminal className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
        <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border whitespace-nowrap ${catClass}`}>
          {entry.category.replace(/_/g, ' ')}
        </span>
        {entry.sandbox_id && (
          <span className="text-[10px] font-mono text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
            {entry.sandbox_id.slice(0, 12)}...
          </span>
        )}
        {entry.error && <AlertCircle className="w-3 h-3 text-red-500" />}
        {entry.duration_ms > 0 && (
          <span className="text-[10px] text-muted-foreground">{entry.duration_ms}ms</span>
        )}
        <span className="text-[10px] text-muted-foreground ml-auto">{timeAgo(entry.timestamp)}</span>
      </div>
      <div className="mt-1 pl-6">
        <code className="text-[10px] font-mono text-foreground bg-zinc-50 px-1.5 py-0.5 rounded border border-border block truncate">
          $ {entry.command}
        </code>
      </div>
      {expanded && entry.output && (
        <div className="mt-2 ml-6 p-2.5 bg-zinc-950 rounded border border-zinc-800">
          <pre className="text-[10px] font-mono text-green-400 whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
            {entry.output}
          </pre>
        </div>
      )}
    </div>
  );
}


function SandboxesView({ data }) {
  if (!data || (data.total_live === 0 && data.total_created === 0)) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Server className="w-8 h-8 text-zinc-200 mb-3" />
        <p className="text-sm font-medium text-foreground mb-1">No Conway sandbox VMs</p>
        <p className="text-xs text-muted-foreground max-w-md">
          The agent creates Conway Cloud VMs via <code className="bg-secondary px-1 rounded font-mono">sandbox_create</code>, installs OpenClaw inside them, then deploys services and browses the web. VMs will appear here once created.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Live VMs from Conway API */}
      {data.live_sandboxes?.length > 0 && (
        <div>
          <h3 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-2">Live VMs (Conway API)</h3>
          <div className="grid grid-cols-2 gap-3">
            {data.live_sandboxes.map((sb, i) => (
              <SandboxCard key={i} sandbox={sb} live />
            ))}
          </div>
        </div>
      )}

      {/* Created VMs from agent tool calls */}
      {data.created_sandboxes?.length > 0 && (
        <div>
          <h3 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-2">Created VMs (from agent actions)</h3>
          <div className="grid grid-cols-2 gap-3">
            {data.created_sandboxes.map((sb, i) => (
              <SandboxCard key={i} sandbox={sb} />
            ))}
          </div>
        </div>
      )}

      {/* Exposed URLs */}
      {data.exposed_urls?.length > 0 && (
        <div className="bg-white border border-border rounded-sm p-4">
          <h3 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-3">Exposed Public URLs</h3>
          <div className="space-y-2">
            {data.exposed_urls.map((u, i) => (
              <div key={i} className="flex items-center gap-3">
                <a href={u.url} target="_blank" rel="noreferrer"
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1.5 font-mono">
                  <ExternalLink className="w-3 h-3" /> {u.url}
                </a>
                {u.port && <span className="text-[10px] text-muted-foreground">port {u.port}</span>}
                <span className="text-[10px] text-muted-foreground ml-auto">{timeAgo(u.timestamp)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


function SandboxCard({ sandbox, live }) {
  const id = sandbox.id || sandbox.sandbox_id || 'Unknown';
  return (
    <div className={`bg-white border rounded-sm p-4 ${live ? 'border-green-200' : 'border-border'}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Server className="w-4 h-4 text-foreground" />
          <span className="text-xs font-heading font-semibold text-foreground font-mono">{id.slice(0, 20)}{id.length > 20 ? '...' : ''}</span>
        </div>
        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${live ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-zinc-50 text-zinc-600 border border-zinc-200'}`}>
          {sandbox.status || (live ? 'live' : 'created')}
        </span>
      </div>
      {sandbox.spec && (
        <div className="grid grid-cols-3 gap-2 text-[10px] text-muted-foreground mb-2">
          {sandbox.spec.vcpu && <div>CPU: <span className="text-foreground font-mono">{sandbox.spec.vcpu}</span></div>}
          {sandbox.spec.ram_mb && <div>RAM: <span className="text-foreground font-mono">{sandbox.spec.ram_mb}MB</span></div>}
          {sandbox.spec.disk_gb && <div>Disk: <span className="text-foreground font-mono">{sandbox.spec.disk_gb}GB</span></div>}
        </div>
      )}
      {sandbox.timestamp && (
        <div className="text-[10px] text-muted-foreground">{live ? 'Active' : 'Created'}: {timeAgo(sandbox.timestamp)}</div>
      )}
    </div>
  );
}


function BrowsingView({ sessions }) {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Globe className="w-8 h-8 text-zinc-200 mb-3" />
        <p className="text-sm font-medium text-foreground mb-1">No browsing sessions</p>
        <p className="text-xs text-muted-foreground max-w-md">
          When the agent uses <code className="bg-secondary px-1 rounded font-mono">browse_page</code> through OpenClaw in the Conway VM, visited URLs, extracted content, and timing data will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-border rounded-sm">
      <div className="px-4 py-3 border-b border-border">
        <h3 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider">Browsing Sessions ({sessions.length})</h3>
      </div>
      <div className="max-h-[600px] overflow-y-auto divide-y divide-border">
        {sessions.map((s, i) => <BrowsingRow key={i} session={s} />)}
      </div>
    </div>
  );
}


function BrowsingRow({ session }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="px-4 py-3 hover:bg-secondary/30 cursor-pointer transition-colors" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-center gap-3">
        {session.success
          ? <CheckCircle className="w-3.5 h-3.5 text-green-600 flex-shrink-0" />
          : <AlertCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />}
        <span className="text-xs font-mono text-foreground truncate flex-1">{session.url}</span>
        {session.duration_ms > 0 && <span className="text-[10px] text-muted-foreground">{session.duration_ms}ms</span>}
        <span className="text-[10px] text-muted-foreground">{timeAgo(session.timestamp)}</span>
      </div>
      {expanded && session.result_preview && (
        <div className="mt-2 p-2.5 bg-zinc-950 rounded border border-zinc-800">
          <pre className="text-[10px] font-mono text-green-400 whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
            {session.result_preview}
          </pre>
        </div>
      )}
      {session.error && <div className="text-[10px] text-red-600 mt-1">{session.error}</div>}
    </div>
  );
}
