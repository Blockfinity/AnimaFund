import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Zap, Search, Filter, Clock, TrendingUp, Users, Cpu, Globe, Wrench, Shield, DollarSign, BarChart3, ChevronDown, ChevronRight, Bot } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const SOURCE_META = {
  anima:          { label: 'Anima Fund', color: '#9B6BFF', bg: '#9B6BFF18' },
  'conway-cloud': { label: 'Conway Cloud', color: '#3B82F6', bg: '#3B82F618' },
  'conway-compute':{ label: 'Conway Compute', color: '#6366F1', bg: '#6366F118' },
  'conway-domains':{ label: 'Conway Domains', color: '#0EA5E9', bg: '#0EA5E918' },
  'conway-x402':  { label: 'Conway x402', color: '#14B8A6', bg: '#14B8A618' },
  'conway-credits':{ label: 'Conway Credits', color: '#22C55E', bg: '#22C55E18' },
  openclaw:       { label: 'OpenClaw', color: '#F59E0B', bg: '#F59E0B18' },
  clawhub:        { label: 'ClawHub', color: '#EF4444', bg: '#EF444418' },
  mcp:            { label: 'MCP Server', color: '#34D399', bg: '#34D39918' },
  engine:         { label: 'Engine', color: '#71717a', bg: '#71717a18' },
  installed:      { label: 'Installed', color: '#5B9CFF', bg: '#5B9CFF18' },
  builtin:        { label: 'Built-in', color: '#71717a', bg: '#71717a18' },
};

const CATEGORY_META = {
  'deal-flow':  { icon: TrendingUp, label: 'Deal Flow' },
  'portfolio':  { icon: BarChart3, label: 'Portfolio' },
  'finance':    { icon: DollarSign, label: 'Finance' },
  'talent':     { icon: Users, label: 'Talent & HR' },
  'compliance': { icon: Shield, label: 'Compliance' },
  'growth':     { icon: Globe, label: 'Growth' },
  'operations': { icon: Wrench, label: 'Operations' },
  'advisory':   { icon: Bot, label: 'Advisory' },
  'compute':    { icon: Cpu, label: 'Compute' },
  'agents':     { icon: Users, label: 'Agents' },
  'social':     { icon: Globe, label: 'Social' },
  'filesystem': { icon: Wrench, label: 'Filesystem' },
  'tools':      { icon: Wrench, label: 'Tools' },
  'planning':   { icon: TrendingUp, label: 'Planning' },
  'inference':  { icon: Cpu, label: 'Inference' },
  'system':     { icon: Cpu, label: 'System' },
  'general':    { icon: Zap, label: 'General' },
};

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Date.now() - new Date(ts).getTime();
  const s = Math.floor(diff / 1000); if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60); if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60); if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function Skills({ selectedAgent }) {
  const [skills, setSkills] = useState([]);
  const [models, setModels] = useState([]);
  const [toolUsage, setToolUsage] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [agentFilter, setAgentFilter] = useState('all');
  const [sortBy, setSortBy] = useState('name'); // name, most-used, recent
  const [expandedSkill, setExpandedSkill] = useState(null);
  const [view, setView] = useState('skills'); // skills, models

  const fetchData = useCallback(async () => {
    try {
      // Fetch from both endpoints — live engine skills + available marketplace skills
      const [liveRes, availRes] = await Promise.all([
        fetch(`${API}/api/live/skills-full`),
        fetch(`${API}/api/skills/available`),
      ]);
      const liveData = await liveRes.json();
      const availData = await availRes.json();

      // Merge: use available skills (has source info) as base, enrich with live engine data
      const availSkills = availData.skills || [];
      const liveSkills = liveData.skills || [];
      const seen = new Set();
      const merged = [];

      // Available skills first (have source + installed info)
      for (const s of availSkills) {
        seen.add(s.name);
        merged.push(s);
      }
      // Add any live engine skills not already in the list
      for (const s of liveSkills) {
        const name = s.name || s.skill_name;
        if (name && !seen.has(name)) {
          seen.add(name);
          merged.push({ ...s, name, source: s.source || 'engine', installed: true });
        }
      }

      setSkills(merged);
      setModels(liveData.models || []);
      setToolUsage(liveData.tool_usage || {});
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 15000); return () => clearInterval(i); }, [fetchData, selectedAgent]);

  // Enrich skills with usage data
  const enriched = useMemo(() => skills.map(s => ({
    ...s,
    use_count: toolUsage[s.name]?.count || s.use_count || 0,
    avg_ms: toolUsage[s.name]?.avg_ms || 0,
    errors: toolUsage[s.name]?.errors || 0,
  })), [skills, toolUsage]);

  // Sources available
  const sources = useMemo(() => {
    const s = {};
    enriched.forEach(sk => { s[sk.source] = (s[sk.source] || 0) + 1; });
    return s;
  }, [enriched]);

  // Agents available
  const agents = useMemo(() => {
    const a = new Set();
    enriched.forEach(sk => (sk.used_by || []).forEach(u => a.add(u)));
    return Array.from(a);
  }, [enriched]);

  // Filter & sort
  const filtered = useMemo(() => {
    let result = enriched;
    if (sourceFilter !== 'all') result = result.filter(s => s.source === sourceFilter);
    if (agentFilter !== 'all') result = result.filter(s => (s.used_by || []).includes(agentFilter));
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(s => s.name.toLowerCase().includes(q) || (s.description || '').toLowerCase().includes(q) || (s.category || '').toLowerCase().includes(q));
    }
    if (sortBy === 'most-used') result = [...result].sort((a, b) => b.use_count - a.use_count);
    else if (sortBy === 'recent') result = [...result].sort((a, b) => (b.installed_at || '').localeCompare(a.installed_at || ''));
    else result = [...result].sort((a, b) => a.name.localeCompare(b.name));
    return result;
  }, [enriched, sourceFilter, agentFilter, search, sortBy]);

  // Group by category
  const grouped = useMemo(() => {
    const g = {};
    filtered.forEach(s => {
      const cat = s.category || 'general';
      if (!g[cat]) g[cat] = [];
      g[cat].push(s);
    });
    return Object.entries(g).sort((a, b) => b[1].length - a[1].length);
  }, [filtered]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div data-testid="skills-page" className="space-y-4 animate-slide-in">
      {/* Header bar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          {/* View toggle */}
          <div className="flex gap-0.5 bg-white border border-border rounded-sm p-0.5">
            <button data-testid="view-skills" onClick={() => setView('skills')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-semibold ${view === 'skills' ? 'bg-foreground text-white' : 'text-muted-foreground hover:bg-secondary'}`}>
              <Zap className="w-3 h-3" /> Skills ({enriched.length})
            </button>
            <button data-testid="view-models" onClick={() => setView('models')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-semibold ${view === 'models' ? 'bg-foreground text-white' : 'text-muted-foreground hover:bg-secondary'}`}>
              <Cpu className="w-3 h-3" /> Models ({models.length})
            </button>
          </div>

          {/* Source badges */}
          {view === 'skills' && (
            <div className="flex gap-1">
              <SourceBadge id="all" label={`All (${enriched.length})`} active={sourceFilter === 'all'} onClick={() => setSourceFilter('all')} color="#a1a1aa" />
              {Object.entries(sources).map(([src, count]) => {
                const meta = SOURCE_META[src] || { label: src, color: '#71717a' };
                return <SourceBadge key={src} id={src} label={`${meta.label} (${count})`} active={sourceFilter === src} onClick={() => setSourceFilter(src)} color={meta.color} />;
              })}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input data-testid="skills-search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search skills..."
              className="bg-white border border-border rounded-sm pl-7 pr-3 py-1.5 text-xs w-48 outline-none focus:border-foreground font-mono" />
          </div>

          {/* Agent filter */}
          {view === 'skills' && agents.length > 0 && (
            <select data-testid="agent-filter" value={agentFilter} onChange={e => setAgentFilter(e.target.value)}
              className="bg-white border border-border rounded-sm px-2 py-1.5 text-xs outline-none cursor-pointer font-mono">
              <option value="all">All Agents</option>
              {agents.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          )}

          {/* Sort */}
          {view === 'skills' && (
            <select data-testid="sort-by" value={sortBy} onChange={e => setSortBy(e.target.value)}
              className="bg-white border border-border rounded-sm px-2 py-1.5 text-xs outline-none cursor-pointer font-mono">
              <option value="name">A-Z</option>
              <option value="most-used">Most Used</option>
              <option value="recent">Recently Acquired</option>
            </select>
          )}
        </div>
      </div>

      {/* Skills View */}
      {view === 'skills' && (
        <div className="space-y-3">
          {grouped.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <Zap className="w-8 h-8 text-border mb-3" />
              <p className="text-sm text-muted-foreground">No skills match your filters.</p>
            </div>
          ) : grouped.map(([category, catSkills]) => {
            const catMeta = CATEGORY_META[category] || CATEGORY_META.general;
            const CatIcon = catMeta.icon;
            return (
              <div key={category} className="bg-white border border-border rounded-sm overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2.5 bg-secondary/30 border-b border-border">
                  <CatIcon className="w-3.5 h-3.5 text-muted-foreground" />
                  <span className="text-xs font-bold text-foreground uppercase tracking-wider">{catMeta.label}</span>
                  <span className="text-[10px] text-muted-foreground font-mono">{catSkills.length}</span>
                </div>
                <div className="divide-y divide-border">
                  {catSkills.map((skill) => {
                    const srcMeta = SOURCE_META[skill.source] || { label: skill.source, color: '#71717a', bg: '#71717a18' };
                    const isExpanded = expandedSkill === skill.name;
                    return (
                      <div key={skill.name} data-testid={`skill-${skill.name}`}>
                        <button onClick={() => setExpandedSkill(isExpanded ? null : skill.name)}
                          className="flex items-center gap-3 w-full text-left px-4 py-2.5 hover:bg-secondary/20 transition-colors">
                          {isExpanded ? <ChevronDown className="w-3 h-3 text-muted-foreground flex-shrink-0" /> : <ChevronRight className="w-3 h-3 text-muted-foreground flex-shrink-0" />}
                          <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${skill.installed !== false ? 'bg-success' : 'bg-amber-400'}`} />
                          <span className="text-xs font-semibold text-foreground min-w-[180px] font-mono">{skill.name}</span>
                          <span className="text-[10px] text-muted-foreground flex-1 truncate">{skill.description}</span>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            {skill.installed === false && (
                              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-sm bg-amber-500/10 text-amber-400">INSTALL</span>
                            )}
                            {skill.use_count > 0 && (
                              <span className="text-[9px] font-mono font-bold text-foreground bg-secondary px-1.5 py-0.5 rounded-sm">{skill.use_count}x</span>
                            )}
                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-sm" style={{ color: srcMeta.color, background: srcMeta.bg }}>{srcMeta.label}</span>
                            {skill.used_by?.map(a => (
                              <span key={a} className="text-[9px] font-mono text-muted-foreground bg-secondary px-1.5 py-0.5 rounded-sm">{a}</span>
                            ))}
                          </div>
                        </button>
                        {isExpanded && (
                          <div className="px-4 py-3 bg-secondary/10 border-t border-border/50">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[10px]">
                              <Detail label="Source" value={srcMeta.label} />
                              <Detail label="Status" value={skill.installed !== false ? 'Installed' : 'Available (clawhub install)'} />
                              <Detail label="Auto-activate" value={skill.auto_activate ? 'Yes' : 'No'} />
                              <Detail label="Installed" value={skill.installed_at ? timeAgo(skill.installed_at) : 'Built-in'} />
                              <Detail label="Usage Count" value={skill.use_count} />
                              {skill.avg_ms > 0 && <Detail label="Avg Duration" value={`${skill.avg_ms}ms`} />}
                              {skill.errors > 0 && <Detail label="Errors" value={skill.errors} />}
                              <Detail label="Used By" value={(skill.used_by || []).join(', ') || 'None'} />
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Models View */}
      {view === 'models' && (
        <div className="bg-white border border-border rounded-sm overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2.5 bg-secondary/30 border-b border-border">
            <Cpu className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="text-xs font-bold text-foreground uppercase tracking-wider">AI Model Registry</span>
            <span className="text-[10px] text-muted-foreground font-mono">{models.length} models</span>
          </div>
          {/* Table header */}
          <div className="grid grid-cols-[1fr_80px_80px_60px_80px_80px_50px_50px] gap-2 px-4 py-2 bg-secondary/20 text-[9px] font-bold text-muted-foreground uppercase tracking-wider border-b border-border">
            <span>Model</span><span>Provider</span><span>Tier</span><span>Input</span><span>Output</span><span>Context</span><span>Tools</span><span>Vision</span>
          </div>
          <div className="divide-y divide-border">
            {models.map((m) => (
              <div key={m.id} data-testid={`model-${m.id}`} className="grid grid-cols-[1fr_80px_80px_60px_80px_80px_50px_50px] gap-2 px-4 py-2.5 hover:bg-secondary/10 items-center">
                <div>
                  <span className="text-xs font-semibold text-foreground">{m.name}</span>
                  <span className="text-[9px] font-mono text-muted-foreground ml-2">{m.id}</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">{m.provider}</span>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-sm w-fit ${m.tier === 'critical' ? 'bg-error/10 text-error' : m.tier === 'low_compute' ? 'bg-warning/10 text-warning' : 'bg-success/10 text-success'}`}>{m.tier}</span>
                <span className="text-[10px] font-mono text-muted-foreground">${m.cost_input}/1k</span>
                <span className="text-[10px] font-mono text-muted-foreground">${m.cost_output}/1k</span>
                <span className="text-[10px] font-mono text-muted-foreground">{(m.context_window / 1000).toFixed(0)}k</span>
                <div className={`w-2 h-2 rounded-full ${m.tools ? 'bg-success' : 'bg-muted'}`} />
                <div className={`w-2 h-2 rounded-full ${m.vision ? 'bg-success' : 'bg-muted'}`} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stats footer */}
      <div className="flex items-center gap-4 text-[10px] text-muted-foreground px-1">
        {Object.entries(sources).map(([src, count]) => {
          const meta = SOURCE_META[src] || { label: src, color: '#71717a' };
          return <span key={src} className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: meta.color }} />{meta.label}: {count}</span>;
        })}
        <span className="ml-auto font-mono">Total: {enriched.length} skills, {models.length} models</span>
      </div>
    </div>
  );
}

function SourceBadge({ id, label, active, onClick, color }) {
  return (
    <button data-testid={`source-filter-${id}`} onClick={onClick}
      className="text-[9px] font-bold px-2 py-1 rounded-sm border transition-colors"
      style={{ borderColor: active ? color : '#e4e4e7', background: active ? `${color}18` : 'white', color: active ? color : '#71717a' }}>
      {label}
    </button>
  );
}

function Detail({ label, value }) {
  return (
    <div>
      <span className="text-muted-foreground font-semibold">{label}</span>
      <div className="font-mono text-foreground mt-0.5">{value}</div>
    </div>
  );
}
