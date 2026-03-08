import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Server, Globe, Terminal, Wrench, Network, ChevronDown, ChevronRight, ExternalLink, Copy, RefreshCw } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// ─── Tab definitions ───
const TABS = [
  { id: 'overview', label: 'Overview', icon: Server },
  { id: 'sandboxes', label: 'Sandboxes', icon: Server },
  { id: 'terminal', label: 'Terminal', icon: Terminal },
  { id: 'domains', label: 'Domains', icon: Globe },
  { id: 'tools', label: 'Installed Tools', icon: Wrench },
  { id: 'network', label: 'Agent Network', icon: Network },
];

export default function Infrastructure({ selectedAgent }) {
  const [tab, setTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [sandboxes, setSandboxes] = useState([]);
  const [terminalEntries, setTerminalEntries] = useState([]);
  const [domains, setDomains] = useState([]);
  const [tools, setTools] = useState([]);
  const [discoveredAgents, setDiscoveredAgents] = useState([]);
  const [messages, setMessages] = useState([]);
  const termRef = useRef(null);

  const fetchAll = useCallback(async () => {
    try {
      const [ovRes, sbRes, termRes, domRes, toolRes] = await Promise.all([
        fetch(`${API}/api/infrastructure/overview`),
        fetch(`${API}/api/infrastructure/sandboxes`),
        fetch(`${API}/api/infrastructure/terminal?lines=100`),
        fetch(`${API}/api/infrastructure/domains`),
        fetch(`${API}/api/infrastructure/installed-tools`),
      ]);
      if (ovRes.ok) {
        const d = await ovRes.json();
        setOverview(d);
        setDiscoveredAgents(d.discovered_agents || []);
      }
      if (sbRes.ok) { const d = await sbRes.json(); setSandboxes(d.sandboxes || []); }
      if (termRes.ok) {
        const d = await termRes.json();
        setTerminalEntries(prev => {
          const newEntries = d.entries || [];
          if (prev.length === newEntries.length && prev.length > 0 &&
              prev[prev.length-1]?.timestamp === newEntries[newEntries.length-1]?.timestamp) return prev;
          return newEntries;
        });
      }
      if (domRes.ok) { const d = await domRes.json(); setDomains(d.domains || []); }
      if (toolRes.ok) { const d = await toolRes.json(); setTools(d.tools || []); }
    } catch { /* keep previous state */ }

    // Fetch messages separately
    try {
      const msgRes = await fetch(`${API}/api/live/messages`);
      if (msgRes.ok) { const d = await msgRes.json(); setMessages(d.messages || []); }
    } catch {}
  }, []);

  useEffect(() => {
    fetchAll();
    const i = setInterval(fetchAll, 10000);
    return () => clearInterval(i);
  }, [fetchAll, selectedAgent]);

  // Auto-scroll terminal
  useEffect(() => {
    if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight;
  }, [terminalEntries]);

  return (
    <div data-testid="infrastructure-page" className="space-y-4">
      {/* Tab bar */}
      <div className="flex items-center gap-1 border-b border-border pb-2">
        {TABS.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} data-testid={`infra-tab-${t.id}`}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-medium transition-colors
                ${tab === t.id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
              <Icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          );
        })}
        <button onClick={fetchAll} className="ml-auto text-muted-foreground hover:text-foreground p-1.5" data-testid="infra-refresh">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Tab content */}
      {tab === 'overview' && <OverviewTab overview={overview} sandboxes={sandboxes} tools={tools} domains={domains} discoveredAgents={discoveredAgents} messages={messages} />}
      {tab === 'sandboxes' && <SandboxesTab sandboxes={sandboxes} />}
      {tab === 'terminal' && <TerminalTab entries={terminalEntries} termRef={termRef} />}
      {tab === 'domains' && <DomainsTab domains={domains} />}
      {tab === 'tools' && <ToolsTab tools={tools} />}
      {tab === 'network' && <NetworkTab agents={discoveredAgents} messages={messages} />}
    </div>
  );
}


// ═══════════════════════════════════════════
// OVERVIEW TAB
// ═══════════════════════════════════════════
function OverviewTab({ overview, sandboxes, tools, domains, discoveredAgents, messages }) {
  const stats = [
    { label: 'Sandboxes (VMs)', value: sandboxes.length, color: '#3b82f6' },
    { label: 'Domains', value: domains.length, color: '#8b5cf6' },
    { label: 'Installed Tools', value: tools.length, color: '#10b981' },
    { label: 'Discovered Agents', value: discoveredAgents.length, color: '#f59e0b' },
    { label: 'Messages', value: messages.length, color: '#ec4899' },
    { label: 'Public URLs', value: sandboxes.reduce((sum, s) => sum + (s.public_urls?.length || 0), 0), color: '#06b6d4' },
  ];

  return (
    <div className="space-y-4">
      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {stats.map(s => (
          <div key={s.label} data-testid={`stat-${s.label.toLowerCase().replace(/\s/g, '-')}`}
            className="bg-white border border-border rounded-md p-3">
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">{s.label}</div>
            <div className="text-2xl font-bold mt-1" style={{ color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* Active VMs */}
      {sandboxes.length > 0 && (
        <div className="bg-white border border-border rounded-md p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">Active Sandboxes</h3>
          <div className="space-y-2">
            {sandboxes.filter(s => s.status !== 'deleted').map((s, i) => (
              <SandboxRow key={s.sandbox_id || i} sandbox={s} compact />
            ))}
          </div>
        </div>
      )}

      {/* Children sandboxes from identity */}
      {overview?.children_sandboxes?.length > 0 && (
        <div className="bg-white border border-border rounded-md p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">Child Agent VMs</h3>
          <div className="space-y-2">
            {overview.children_sandboxes.map((c, i) => (
              <div key={c.id || i} className="flex items-center justify-between py-2 px-3 bg-secondary/30 rounded-sm text-xs">
                <div>
                  <span className="font-semibold text-foreground">{c.name}</span>
                  <span className="text-muted-foreground ml-2">({c.sandbox_id?.slice(0, 8)}...)</span>
                </div>
                <StatusBadge status={c.status} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Installed tools summary */}
      {tools.length > 0 && (
        <div className="bg-white border border-border rounded-md p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">Installed Tools</h3>
          <div className="flex flex-wrap gap-1.5">
            {tools.map((t, i) => (
              <span key={i} className="px-2 py-1 bg-secondary text-xs rounded-sm font-medium text-foreground">
                {t.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {sandboxes.length === 0 && tools.length === 0 && domains.length === 0 && (
        <div className="bg-white border border-border rounded-md p-8 text-center">
          <Server className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm text-muted-foreground">No infrastructure deployed yet.</p>
          <p className="text-xs text-muted-foreground mt-1">
            The agent will create sandboxes, register domains, and install tools autonomously.
          </p>
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════
// SANDBOXES TAB
// ═══════════════════════════════════════════
function SandboxesTab({ sandboxes }) {
  if (sandboxes.length === 0) {
    return (
      <div className="bg-white border border-border rounded-md p-8 text-center">
        <Server className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">No sandboxes created yet.</p>
        <p className="text-xs text-muted-foreground mt-1">The agent creates Conway Cloud sandboxes (Linux VMs) to deploy services.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sandboxes.map((s, i) => (
        <SandboxRow key={s.sandbox_id || i} sandbox={s} />
      ))}
    </div>
  );
}

function SandboxRow({ sandbox, compact }) {
  const [expanded, setExpanded] = useState(false);
  const s = sandbox;
  const isActive = s.status === 'running' || s.status === 'active';

  return (
    <div className="bg-white border border-border rounded-md overflow-hidden">
      <div className={`flex items-center justify-between ${compact ? 'p-2.5' : 'p-3'} cursor-pointer hover:bg-secondary/20`}
        onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-2.5">
          {expanded ? <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" /> : <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />}
          <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-500' : 'bg-zinc-300'}`} />
          <span className="text-xs font-semibold text-foreground">{s.name || s.sandbox_id?.slice(0, 12) || 'Sandbox'}</span>
          {s.vcpu && <span className="text-[10px] text-muted-foreground">{s.vcpu} vCPU / {s.memory_mb}MB / {s.disk_gb}GB</span>}
        </div>
        <div className="flex items-center gap-2">
          {s.public_urls?.length > 0 && (
            <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded font-medium">
              {s.public_urls.length} URL{s.public_urls.length > 1 ? 's' : ''}
            </span>
          )}
          <StatusBadge status={s.status} />
        </div>
      </div>
      {expanded && (
        <div className="border-t border-border p-3 bg-secondary/10 space-y-2">
          <KV label="Sandbox ID" value={s.sandbox_id} mono />
          {s.region && <KV label="Region" value={s.region} />}
          {s.created_at && <KV label="Created" value={new Date(s.created_at).toLocaleString()} />}
          {s.public_urls?.length > 0 && (
            <div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-1">Public URLs</div>
              {s.public_urls.map((u, i) => (
                <div key={i} className="flex items-center gap-2 text-xs mb-1">
                  <span className="text-muted-foreground">:{u.port}</span>
                  <a href={u.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline flex items-center gap-1 font-mono text-[11px]">
                    {u.url} <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}


// ═══════════════════════════════════════════
// TERMINAL TAB (read-only)
// ═══════════════════════════════════════════
function TerminalTab({ entries, termRef }) {
  if (entries.length === 0) {
    return (
      <div className="bg-white border border-border rounded-md p-8 text-center">
        <Terminal className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">No terminal activity yet.</p>
        <p className="text-xs text-muted-foreground mt-1">Shows all exec, sandbox_exec, and code_execution outputs.</p>
      </div>
    );
  }

  return (
    <div className="bg-[#0c0c0c] rounded-md border border-zinc-800 overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 bg-[#1a1a1a] border-b border-zinc-800">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
        </div>
        <span className="text-[10px] text-zinc-500 font-mono ml-2">Agent Terminal (read-only)</span>
        <span className="text-[10px] text-zinc-600 ml-auto">{entries.length} entries</span>
      </div>
      <div ref={termRef} data-testid="terminal-output"
        className="p-3 overflow-y-auto font-mono text-[11px] leading-relaxed"
        style={{ maxHeight: '60vh', minHeight: '40vh' }}>
        {entries.map((e, i) => (
          <div key={i} className="mb-2">
            <div className="flex items-center gap-2 text-zinc-500 text-[10px]">
              <span>{new Date(e.timestamp).toLocaleTimeString()}</span>
              {e.sandbox_id && <span className="text-cyan-600">[{e.sandbox_id.slice(0, 8)}]</span>}
              <span className={e.type === 'exec' ? 'text-green-500' : 'text-cyan-500'}>{e.type}</span>
              {e.duration_ms > 0 && <span className="text-zinc-600">{e.duration_ms}ms</span>}
            </div>
            {e.command && (
              <div className="text-green-400 mt-0.5">
                <span className="text-green-600 select-none">$ </span>{e.command}
              </div>
            )}
            {e.output && (
              <div className={`mt-0.5 whitespace-pre-wrap break-all ${e.error ? 'text-red-400' : 'text-zinc-300'}`}>
                {e.output}
              </div>
            )}
            {e.error && <div className="text-red-500 mt-0.5">{e.error}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════
// DOMAINS TAB
// ═══════════════════════════════════════════
function DomainsTab({ domains }) {
  if (domains.length === 0) {
    return (
      <div className="bg-white border border-border rounded-md p-8 text-center">
        <Globe className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">No domains registered yet.</p>
        <p className="text-xs text-muted-foreground mt-1">The agent can register and manage real domains via Conway Domains.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {domains.map((d, i) => (
        <div key={i} className="bg-white border border-border rounded-md p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-purple-500" />
              <span className="text-sm font-semibold text-foreground">{d.domain}</span>
            </div>
            <StatusBadge status={d.status} />
          </div>
          <div className="text-[10px] text-muted-foreground mb-2">
            Registered: {d.registered_at ? new Date(d.registered_at).toLocaleString() : 'N/A'}
          </div>
          {d.dns_records?.length > 0 && (
            <div className="mt-2 border-t border-border pt-2">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mb-1">DNS Records</div>
              {d.dns_records.map((r, j) => (
                <div key={j} className="text-xs font-mono text-foreground py-0.5">
                  {r.type} {r.host} → {r.value}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}


// ═══════════════════════════════════════════
// TOOLS TAB
// ═══════════════════════════════════════════
function ToolsTab({ tools }) {
  if (tools.length === 0) {
    return (
      <div className="bg-white border border-border rounded-md p-8 text-center">
        <Wrench className="w-8 h-8 text-muted-foreground mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">No additional tools installed yet.</p>
        <p className="text-xs text-muted-foreground mt-1">The agent can install MCP servers, npm packages, and ClawHub skills.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tools.map((t, i) => (
        <div key={i} className="bg-white border border-border rounded-md p-3 flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-foreground">{t.name}</div>
            <div className="text-[10px] text-muted-foreground">{t.type} &middot; Installed {t.installed_at ? new Date(t.installed_at).toLocaleString() : ''}</div>
          </div>
          <div className={`text-[10px] font-medium px-2 py-0.5 rounded ${t.enabled ? 'bg-green-50 text-green-600' : 'bg-zinc-100 text-zinc-400'}`}>
            {t.enabled ? 'Active' : 'Disabled'}
          </div>
        </div>
      ))}
    </div>
  );
}


// ═══════════════════════════════════════════
// NETWORK TAB
// ═══════════════════════════════════════════
function NetworkTab({ agents, messages }) {
  return (
    <div className="space-y-4">
      {/* Discovered Agents */}
      <div className="bg-white border border-border rounded-md p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Discovered Agents ({agents.length})
        </h3>
        {agents.length === 0 ? (
          <p className="text-xs text-muted-foreground">No agents discovered yet. The agent uses discover_agents to find other AI agents.</p>
        ) : (
          <div className="space-y-2">
            {agents.map((a, i) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 bg-secondary/30 rounded-sm">
                <div>
                  <span className="text-xs font-semibold text-foreground">{a.name || a.address?.slice(0, 12)}</span>
                  {a.description && <span className="text-[10px] text-muted-foreground ml-2">{a.description.slice(0, 60)}</span>}
                </div>
                <span className="text-[10px] text-muted-foreground font-mono">{a.address?.slice(0, 10)}...</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="bg-white border border-border rounded-md p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Agent Messages ({messages.length})
        </h3>
        {messages.length === 0 ? (
          <p className="text-xs text-muted-foreground">No messages yet. The agent communicates with other agents via send_message.</p>
        ) : (
          <div className="space-y-2">
            {messages.map((m, i) => (
              <div key={i} className="border border-border rounded-sm p-2.5">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono text-muted-foreground">
                    From: {m.from_address?.slice(0, 12)}... → {m.to_address?.slice(0, 12)}...
                  </span>
                  <StatusBadge status={m.status} />
                </div>
                <div className="text-xs text-foreground">{m.content?.slice(0, 200)}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════
// Shared components
// ═══════════════════════════════════════════
function StatusBadge({ status }) {
  const colors = {
    running: 'bg-green-50 text-green-600',
    active: 'bg-green-50 text-green-600',
    deleted: 'bg-red-50 text-red-500',
    error: 'bg-red-50 text-red-500',
    stopped: 'bg-zinc-100 text-zinc-500',
    processed: 'bg-blue-50 text-blue-500',
    pending: 'bg-yellow-50 text-yellow-600',
  };
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${colors[status] || 'bg-zinc-100 text-zinc-500'}`}>
      {status || 'unknown'}
    </span>
  );
}

function KV({ label, value, mono }) {
  return (
    <div className="flex items-start gap-2 text-xs">
      <span className="text-muted-foreground min-w-[80px]">{label}:</span>
      <span className={`text-foreground break-all ${mono ? 'font-mono text-[11px]' : ''}`}>{value || '—'}</span>
      {mono && value && (
        <button onClick={() => navigator.clipboard.writeText(value)} className="text-muted-foreground hover:text-foreground flex-shrink-0">
          <Copy className="w-3 h-3" />
        </button>
      )}
    </div>
  );
}
