import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Eye, Globe, Server, Terminal, Zap, ExternalLink, RefreshCw, AlertCircle, CheckCircle, Clock, ArrowRight } from 'lucide-react';

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
  { id: 'actions', label: 'Actions', icon: Terminal },
  { id: 'sandboxes', label: 'Sandbox VMs', icon: Server },
  { id: 'browsing', label: 'Browsing', icon: Globe },
];

export default function OpenClawViewer({ selectedAgent }) {
  const [tab, setTab] = useState('live');
  const [status, setStatus] = useState(null);
  const [actions, setActions] = useState([]);
  const [categories, setCategories] = useState({});
  const [sandboxes, setSandboxes] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const feedRef = useRef(null);

  const fetchAll = useCallback(async () => {
    try {
      const [statusRes, actionsRes, sandboxRes, browseRes] = await Promise.all([
        fetch(`${API}/api/openclaw/status`),
        fetch(`${API}/api/openclaw/actions?limit=100`),
        fetch(`${API}/api/openclaw/sandboxes`),
        fetch(`${API}/api/openclaw/browsing-sessions?limit=50`),
      ]);
      if (statusRes.ok) setStatus(await statusRes.json());
      if (actionsRes.ok) {
        const d = await actionsRes.json();
        setActions(d.actions || []);
        setCategories(d.categories || {});
      }
      if (sandboxRes.ok) setSandboxes((await sandboxRes.json()).sandboxes || []);
      if (browseRes.ok) setSessions((await browseRes.json()).sessions || []);
    } catch (e) { console.error('OpenClaw fetch error:', e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    fetchAll();
    if (autoRefresh) {
      const i = setInterval(fetchAll, 5000);
      return () => clearInterval(i);
    }
  }, [fetchAll, autoRefresh, selectedAgent]);

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = 0;
  }, [actions]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const isActive = actions.length > 0 || sandboxes.length > 0;

  return (
    <div data-testid="openclaw-page" className="space-y-4 animate-slide-in">
      {/* Status Bar */}
      <div className="bg-white border border-border rounded-sm p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-2.5 h-2.5 rounded-full ${isActive ? 'bg-green-500 animate-pulse' : 'bg-zinc-300'}`} />
            <h2 className="text-sm font-heading font-semibold text-foreground">
              OpenClaw VM Viewer
            </h2>
            <span className="text-xs text-muted-foreground">
              {isActive ? 'Active' : 'Idle — waiting for agent activity'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              data-testid="auto-refresh-toggle"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`text-xs px-2.5 py-1 rounded-sm border transition-colors ${autoRefresh ? 'bg-foreground text-white border-foreground' : 'bg-white text-muted-foreground border-border hover:border-foreground'}`}
            >
              {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
            </button>
            <button data-testid="refresh-btn" onClick={fetchAll} className="p-1.5 rounded-sm border border-border hover:bg-secondary transition-colors">
              <RefreshCw className="w-3.5 h-3.5 text-muted-foreground" />
            </button>
          </div>
        </div>

        {/* Tool Status */}
        {status && (
          <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border">
            <StatusPill label="OpenClaw" ok={status.openclaw_installed} />
            <StatusPill label="Conway Terminal" ok={status.conway_terminal_installed} />
            {status.mcp_servers?.map(s => (
              <StatusPill key={s} label={`MCP: ${s}`} ok={true} />
            ))}
            {actions.length > 0 && (
              <span className="text-xs text-muted-foreground ml-auto">
                {actions.length} actions recorded
              </span>
            )}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-white border border-border rounded-sm p-1">
        {TABS.map(t => {
          const Icon = t.icon;
          const count = t.id === 'actions' ? actions.length : t.id === 'sandboxes' ? sandboxes.length : t.id === 'browsing' ? sessions.length : null;
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

      {/* Tab Content */}
      {tab === 'live' && <LiveView actions={actions} sandboxes={sandboxes} sessions={sessions} categories={categories} feedRef={feedRef} />}
      {tab === 'actions' && <ActionsView actions={actions} feedRef={feedRef} />}
      {tab === 'sandboxes' && <SandboxesView sandboxes={sandboxes} />}
      {tab === 'browsing' && <BrowsingView sessions={sessions} />}
    </div>
  );
}


function StatusPill({ label, ok }) {
  return (
    <div className="flex items-center gap-1.5 text-xs">
      {ok
        ? <CheckCircle className="w-3 h-3 text-green-600" />
        : <AlertCircle className="w-3 h-3 text-zinc-400" />
      }
      <span className={ok ? 'text-foreground' : 'text-muted-foreground'}>{label}</span>
    </div>
  );
}


function LiveView({ actions, sandboxes, sessions, categories, feedRef }) {
  if (actions.length === 0 && sandboxes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Eye className="w-8 h-8 text-border mb-3" />
        <p className="text-sm text-muted-foreground max-w-md">
          No OpenClaw activity yet. When the agent uses browse_page, sandbox VMs, or agent network tools, their actions will appear here in real-time.
        </p>
        <p className="text-xs text-muted-foreground mt-2 max-w-sm">
          The agent must complete its boot sequence and start using OpenClaw tools for data to populate.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* Live Action Feed */}
      <div className="col-span-2 bg-white border border-border rounded-sm">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <h3 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider">Live Action Feed</h3>
          <span className="text-[10px] text-muted-foreground">{actions.length} total</span>
        </div>
        <div ref={feedRef} className="max-h-[500px] overflow-y-auto divide-y divide-border">
          {actions.slice(0, 30).map((a, i) => (
            <ActionRow key={a.id || i} action={a} />
          ))}
        </div>
      </div>

      {/* Right Panel — Stats + Active Sandboxes */}
      <div className="space-y-4">
        {/* Category Breakdown */}
        <div className="bg-white border border-border rounded-sm p-4">
          <h4 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-3">Action Categories</h4>
          <div className="space-y-2">
            {Object.entries(categories).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
              <div key={cat} className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground capitalize">{cat}</span>
                <span className="text-xs font-mono font-bold text-foreground">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Active Sandboxes */}
        {sandboxes.length > 0 && (
          <div className="bg-white border border-border rounded-sm p-4">
            <h4 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-3">Active VMs</h4>
            <div className="space-y-2">
              {sandboxes.map((sb, i) => (
                <div key={i} className="p-2 bg-secondary rounded-sm">
                  <div className="text-xs font-mono text-foreground">{sb.id || sb.sandbox_id || `VM-${i + 1}`}</div>
                  {sb.public_url && (
                    <a href={sb.public_url} target="_blank" rel="noreferrer"
                      className="text-[10px] text-blue-600 hover:underline flex items-center gap-1 mt-1">
                      <ExternalLink className="w-2.5 h-2.5" /> {sb.public_url}
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Browsing Sessions Summary */}
        {sessions.length > 0 && (
          <div className="bg-white border border-border rounded-sm p-4">
            <h4 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider mb-3">Recent Browsing</h4>
            <div className="space-y-2">
              {sessions.slice(0, 5).map((s, i) => (
                <div key={i} className="text-xs">
                  <div className="text-foreground font-mono truncate">{s.url}</div>
                  <div className="text-muted-foreground text-[10px]">{timeAgo(s.timestamp)} {s.duration_ms ? `| ${s.duration_ms}ms` : ''}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


function ActionRow({ action }) {
  const [expanded, setExpanded] = useState(false);
  const catColors = {
    browsing: 'bg-blue-50 text-blue-700 border-blue-200',
    sandbox: 'bg-green-50 text-green-700 border-green-200',
    payment: 'bg-amber-50 text-amber-700 border-amber-200',
    network: 'bg-purple-50 text-purple-700 border-purple-200',
    tools: 'bg-rose-50 text-rose-700 border-rose-200',
    other: 'bg-zinc-50 text-zinc-600 border-zinc-200',
  };
  const catClass = catColors[action.category] || catColors.other;

  return (
    <div className="px-4 py-2.5 hover:bg-secondary/30 cursor-pointer transition-colors" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-center gap-3">
        <span className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${catClass}`}>
          {action.category}
        </span>
        <span className="text-xs font-mono font-semibold text-foreground">{action.tool}</span>
        {action.duration_ms && (
          <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
            <Clock className="w-2.5 h-2.5" /> {action.duration_ms}ms
          </span>
        )}
        {action.error && <AlertCircle className="w-3 h-3 text-red-500" />}
        <span className="text-[10px] text-muted-foreground ml-auto">{timeAgo(action.timestamp)}</span>
        <ArrowRight className={`w-3 h-3 text-muted-foreground transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </div>

      {/* Arguments preview */}
      {Object.keys(action.arguments).length > 0 && (
        <div className="text-[10px] text-muted-foreground mt-1 font-mono truncate">
          {Object.entries(action.arguments).map(([k, v]) => `${k}: ${typeof v === 'string' ? v : JSON.stringify(v)}`).join(' | ')}
        </div>
      )}

      {/* Expanded result */}
      {expanded && action.result && (
        <div className="mt-2 p-2 bg-zinc-50 rounded border border-border">
          <pre className="text-[10px] font-mono text-foreground whitespace-pre-wrap break-all max-h-40 overflow-y-auto">
            {action.result}
          </pre>
        </div>
      )}
    </div>
  );
}


function ActionsView({ actions, feedRef }) {
  const [filter, setFilter] = useState('all');
  const cats = [...new Set(actions.map(a => a.category))];
  const filtered = filter === 'all' ? actions : actions.filter(a => a.category === filter);

  return (
    <div className="bg-white border border-border rounded-sm">
      <div className="px-4 py-3 border-b border-border flex items-center gap-2">
        <h3 className="text-xs font-heading font-semibold text-foreground uppercase tracking-wider">All Actions</h3>
        <div className="flex items-center gap-1 ml-auto">
          <button onClick={() => setFilter('all')}
            className={`text-[10px] px-2 py-0.5 rounded-sm border transition-colors ${filter === 'all' ? 'bg-foreground text-white border-foreground' : 'border-border text-muted-foreground hover:text-foreground'}`}>
            All ({actions.length})
          </button>
          {cats.map(c => (
            <button key={c} onClick={() => setFilter(c)}
              className={`text-[10px] px-2 py-0.5 rounded-sm border capitalize transition-colors ${filter === c ? 'bg-foreground text-white border-foreground' : 'border-border text-muted-foreground hover:text-foreground'}`}>
              {c} ({actions.filter(a => a.category === c).length})
            </button>
          ))}
        </div>
      </div>
      <div ref={feedRef} className="max-h-[600px] overflow-y-auto divide-y divide-border">
        {filtered.length === 0 ? (
          <div className="px-4 py-12 text-center text-xs text-muted-foreground">No actions in this category yet.</div>
        ) : (
          filtered.map((a, i) => <ActionRow key={a.id || i} action={a} />)
        )}
      </div>
    </div>
  );
}


function SandboxesView({ sandboxes }) {
  if (sandboxes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Server className="w-8 h-8 text-border mb-3" />
        <p className="text-sm text-muted-foreground max-w-md">
          No sandbox VMs running. When the agent creates sandboxes via Conway Cloud, they will appear here with their public URLs and status.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {sandboxes.map((sb, i) => (
        <div key={i} className="bg-white border border-border rounded-sm p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Server className="w-4 h-4 text-foreground" />
              <span className="text-sm font-heading font-semibold text-foreground">{sb.id || sb.sandbox_id || `Sandbox ${i + 1}`}</span>
            </div>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${sb.status === 'running' ? 'bg-green-50 text-green-700' : 'bg-zinc-100 text-zinc-600'}`}>
              {sb.status || 'unknown'}
            </span>
          </div>
          {sb.spec && (
            <div className="grid grid-cols-3 gap-2 text-[10px] text-muted-foreground mb-3">
              {sb.spec.vcpu && <div>CPU: <span className="text-foreground font-mono">{sb.spec.vcpu} vCPU</span></div>}
              {sb.spec.ram_mb && <div>RAM: <span className="text-foreground font-mono">{sb.spec.ram_mb}MB</span></div>}
              {sb.spec.disk_gb && <div>Disk: <span className="text-foreground font-mono">{sb.spec.disk_gb}GB</span></div>}
            </div>
          )}
          {(sb.exposed_ports || sb.public_url) && (
            <div className="space-y-1">
              {sb.public_url && (
                <a href={sb.public_url} target="_blank" rel="noreferrer"
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                  <ExternalLink className="w-3 h-3" /> {sb.public_url}
                </a>
              )}
              {(sb.exposed_ports || []).map((p, j) => (
                <a key={j} href={p.url || p} target="_blank" rel="noreferrer"
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                  <ExternalLink className="w-3 h-3" /> {p.url || p}
                </a>
              ))}
            </div>
          )}
          {sb.created_at && (
            <div className="text-[10px] text-muted-foreground mt-2">Created: {timeAgo(sb.created_at)}</div>
          )}
        </div>
      ))}
    </div>
  );
}


function BrowsingView({ sessions }) {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center bg-white border border-border rounded-sm">
        <Globe className="w-8 h-8 text-border mb-3" />
        <p className="text-sm text-muted-foreground max-w-md">
          No browsing sessions yet. When the agent uses browse_page to visit websites, the URLs, content, and timing will appear here.
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
        {sessions.map((s, i) => (
          <BrowsingRow key={i} session={s} />
        ))}
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
          : <AlertCircle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
        }
        <span className="text-xs font-mono text-foreground truncate flex-1">{session.url}</span>
        {session.duration_ms && (
          <span className="text-[10px] text-muted-foreground">{session.duration_ms}ms</span>
        )}
        <span className="text-[10px] text-muted-foreground">{timeAgo(session.timestamp)}</span>
      </div>
      {expanded && session.result_preview && (
        <div className="mt-2 p-2 bg-zinc-50 rounded border border-border">
          <pre className="text-[10px] font-mono text-foreground whitespace-pre-wrap break-all max-h-40 overflow-y-auto">
            {session.result_preview}
          </pre>
        </div>
      )}
      {session.error && (
        <div className="text-[10px] text-red-600 mt-1">{session.error}</div>
      )}
    </div>
  );
}
