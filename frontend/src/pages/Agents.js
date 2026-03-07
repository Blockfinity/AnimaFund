import React, { useState, useEffect, useCallback } from 'react';
import { Users, Clock, Bot, Heart, Globe, Shield } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Date.now() - new Date(ts).getTime();
  const s = Math.floor(diff / 1000); if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60); if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60); if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [discovered, setDiscovered] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [identity, setIdentity] = useState(null);
  const [tab, setTab] = useState('founder');
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [agRes, disRes, schRes, idRes] = await Promise.all([
        fetch(`${API}/api/live/agents`),
        fetch(`${API}/api/live/discovered`),
        fetch(`${API}/api/live/heartbeat-schedule`),
        fetch(`${API}/api/live/identity`),
      ]);
      const [ag, dis, sch, id] = await Promise.all([agRes.json(), disRes.json(), schRes.json(), idRes.json()]);
      setAgents(ag.agents || []);
      setDiscovered(dis.agents || []);
      setSchedule(sch.tasks || []);
      setIdentity(id);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 8000); return () => clearInterval(i); }, [fetchData]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  const tabs = [
    ['founder', 'Founder Agent', Bot],
    ['children', `Child Agents (${agents.length})`, Users],
    ['discovered', `Discovered (${discovered.length})`, Globe],
    ['schedule', `Heartbeat Tasks (${schedule.length})`, Clock],
  ];

  return (
    <div data-testid="agents-page" className="space-y-4 animate-slide-in">
      <div className="flex items-center gap-1 bg-white border border-border rounded-sm p-1">
        {tabs.map(([id, label, Icon]) => (
          <button key={id} data-testid={`agents-tab-${id}`} onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-sm text-sm font-medium transition-colors ${tab === id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
            <Icon className="w-3.5 h-3.5" />{label}
          </button>
        ))}
      </div>

      {/* Founder Agent */}
      {tab === 'founder' && identity && (
        <div className="bg-white border border-border rounded-sm p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-sm bg-foreground flex items-center justify-center">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-foreground">{identity.name || 'Founder Agent'}</h3>
              <p className="text-xs font-mono text-muted-foreground">{identity.address}</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <InfoRow label="Sandbox" value={identity.sandbox || 'None'} />
            <InfoRow label="Tools Installed" value={identity.installed_tools?.length || 0} />
            <InfoRow label="Children Deployed" value={identity.children_sandboxes?.length || 0} />
            <InfoRow label="Domains" value={identity.domains?.length || 0} />
            <InfoRow label="Services" value={identity.services?.length || 0} />
          </div>
          {identity.installed_tools?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-border">
              <h4 className="text-xs font-semibold text-muted-foreground mb-2">INSTALLED TOOLS</h4>
              <div className="space-y-1">
                {identity.installed_tools.map((t, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <div className={`w-1.5 h-1.5 rounded-full ${t.enabled ? 'bg-success' : 'bg-muted'}`} />
                    <span className="font-mono">{t.name}</span>
                    <span className="text-muted-foreground">{t.type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Child Agents */}
      {tab === 'children' && (
        agents.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {agents.map((a, i) => (
              <div key={i} className="flex items-center gap-4 px-4 py-3 hover:bg-secondary/30">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${a.status === 'running' ? 'bg-success' : a.status === 'error' ? 'bg-error' : 'bg-muted'}`} />
                <div className="flex-1">
                  <span className="text-xs font-semibold text-foreground">{a.name}</span>
                  <span className="text-[10px] text-muted-foreground ml-2">{a.role}</span>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground">{a.wallet_address?.slice(0, 10)}...</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full ${a.status === 'running' ? 'bg-success/10 text-success' : 'bg-secondary text-muted-foreground'}`}>{a.status}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Users} text="No child agents deployed yet. The founder will hire specialized agents once it has sufficient credits and completes its initial setup." />
        )
      )}

      {/* Discovered Agents */}
      {tab === 'discovered' && (
        discovered.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {discovered.map((d, i) => (
              <div key={i} className="px-4 py-3 hover:bg-secondary/30">
                <div className="flex items-center gap-2 mb-1">
                  <Globe className="w-3 h-3 text-muted-foreground" />
                  <span className="text-xs font-semibold text-foreground">{d.name}</span>
                  <span className="text-[10px] font-mono text-muted-foreground">{d.address?.slice(0, 12)}...</span>
                  <span className="text-[10px] text-muted-foreground ml-auto">seen {d.fetch_count}x</span>
                </div>
                {d.description && <p className="text-[10px] text-muted-foreground ml-5">{d.description.slice(0, 200)}</p>}
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Globe} text="No agents discovered yet. The agent discovers peers through the Conway social protocol during active operation." />
        )
      )}

      {/* Heartbeat Schedule */}
      {tab === 'schedule' && (
        schedule.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {schedule.map((t, i) => (
              <div key={i} className="flex items-center gap-4 px-4 py-3 hover:bg-secondary/30">
                <Heart className={`w-3.5 h-3.5 flex-shrink-0 ${t.enabled ? 'text-success' : 'text-muted-foreground'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-semibold text-foreground">{t.task}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${t.enabled ? 'bg-success/10 text-success' : 'bg-secondary text-muted-foreground'}`}>
                      {t.enabled ? 'active' : 'disabled'}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-0.5 text-[10px] text-muted-foreground">
                    <span>{t.cron || (t.interval_seconds ? `Every ${t.interval_seconds}s` : '')}</span>
                    <span>Runs: {t.run_count}</span>
                    {t.last_result && <span className={t.last_result === 'success' ? 'text-success' : 'text-error'}>Last: {t.last_result}</span>}
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  {t.last_run_at && <div className="text-[9px] font-mono text-muted-foreground">last: {timeAgo(t.last_run_at)}</div>}
                  {t.next_run_at && <div className="text-[9px] font-mono text-muted-foreground">next: {timeAgo(t.next_run_at)}</div>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Clock} text="No heartbeat tasks scheduled." />
        )
      )}
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between items-center py-1.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-xs font-mono font-semibold text-foreground">{value}</span>
    </div>
  );
}

function EmptyState({ icon: Icon, text }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <Icon className="w-8 h-8 text-border mb-3" />
      <p className="text-sm text-muted-foreground max-w-md">{text}</p>
    </div>
  );
}
