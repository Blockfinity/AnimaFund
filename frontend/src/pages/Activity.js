import React, { useState, useEffect, useCallback } from 'react';
import { Activity as ActivityIcon, Clock, Heart, MessageSquare, Wrench, Zap } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

function timeAgo(ts) {
  if (!ts) return '';
  const diff = Date.now() - new Date(ts).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function Activity() {
  const [activities, setActivities] = useState([]);
  const [messages, setMessages] = useState([]);
  const [heartbeat, setHeartbeat] = useState([]);
  const [skills, setSkills] = useState([]);
  const [tab, setTab] = useState('heartbeat');
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [actRes, msgRes, hbRes, skRes] = await Promise.all([
        fetch(`${API}/api/live/activity?limit=100`),
        fetch(`${API}/api/live/messages?limit=50`),
        fetch(`${API}/api/live/heartbeat?limit=50`),
        fetch(`${API}/api/live/skills`),
      ]);
      const [act, msg, hb, sk] = await Promise.all([actRes.json(), msgRes.json(), hbRes.json(), skRes.json()]);
      setActivities(act.activities || []);
      setMessages(msg.messages || []);
      setHeartbeat(hb.history || []);
      setSkills(sk.skills || []);
      // Auto-switch to tools tab if there are tool calls
      if ((act.activities || []).length > 0 && tab === 'heartbeat') setTab('tools');
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [tab]);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 8000); return () => clearInterval(i); }, [fetchData]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  const tabs = [
    ['heartbeat', `Heartbeat (${heartbeat.length})`, Heart],
    ['tools', `Tool Calls (${activities.length})`, Wrench],
    ['messages', `Messages (${messages.length})`, MessageSquare],
    ['skills', `Skills (${skills.length})`, Zap],
  ];

  return (
    <div data-testid="activity-page" className="space-y-4 animate-slide-in">
      {/* Tabs */}
      <div className="flex items-center gap-1 bg-white border border-border rounded-sm p-1">
        {tabs.map(([id, label, Icon]) => (
          <button key={id} data-testid={`activity-tab-${id}`} onClick={() => setTab(id)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-sm text-sm font-medium transition-colors ${tab === id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
            <Icon className="w-3.5 h-3.5" />{label}
          </button>
        ))}
      </div>

      {/* Heartbeat Tab */}
      {tab === 'heartbeat' && (
        heartbeat.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {heartbeat.map((h, i) => (
              <div key={i} className="flex items-center gap-4 px-4 py-3 hover:bg-secondary/30">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${h.result === 'success' ? 'bg-success' : h.result === 'failure' ? 'bg-error' : 'bg-warning'}`} />
                <span className="text-xs font-mono font-medium text-foreground min-w-[160px]">{h.task}</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${h.result === 'success' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'}`}>{h.result}</span>
                {h.duration_ms != null && <span className="text-[10px] font-mono text-muted-foreground">{h.duration_ms}ms</span>}
                {h.error && <span className="text-[10px] text-error truncate max-w-[200px]">{h.error}</span>}
                <span className="text-[10px] font-mono text-muted-foreground ml-auto flex-shrink-0">{timeAgo(h.started_at)}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Heart} text="No heartbeat events yet. The heartbeat daemon runs periodic health checks, credit checks, and social inbox scans." />
        )
      )}

      {/* Tool Calls Tab */}
      {tab === 'tools' && (
        activities.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {activities.map((a, i) => (
              <div key={i} className="flex items-start gap-4 px-4 py-3 hover:bg-secondary/30">
                <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${a.error ? 'bg-error' : 'bg-success'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-sm border bg-secondary text-foreground">{a.tool_name}</span>
                    {a.duration_ms && <span className="text-[10px] font-mono text-muted-foreground">{a.duration_ms}ms</span>}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">{a.result_preview}</p>
                </div>
                <span className="text-[10px] font-mono text-muted-foreground flex-shrink-0">{timeAgo(a.timestamp)}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Wrench} text="No tool calls yet. Tool calls appear when the agent completes turns with actions (requires Conway credits)." />
        )
      )}

      {/* Messages Tab */}
      {tab === 'messages' && (
        messages.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {messages.map((m, i) => (
              <div key={i} className="px-4 py-3 hover:bg-secondary/30">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-foreground">{m.from_address?.slice(0, 10)}...</span>
                  <span className="text-[10px] text-muted-foreground">&rarr;</span>
                  <span className="text-xs font-mono text-foreground">{m.to_address?.slice(0, 10)}...</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-sm ${m.status === 'processed' ? 'bg-success/10 text-success' : 'bg-secondary text-muted-foreground'}`}>{m.status}</span>
                </div>
                <p className="text-xs text-muted-foreground">{m.content?.slice(0, 200)}</p>
                <span className="text-[9px] text-muted-foreground">{timeAgo(m.created_at)}</span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={MessageSquare} text="No messages yet. Messages appear when the agent communicates with other agents via the Conway social protocol." />
        )
      )}

      {/* Skills Tab */}
      {tab === 'skills' && (
        skills.length > 0 ? (
          <div className="bg-white border border-border rounded-sm divide-y divide-border">
            {skills.map((s, i) => (
              <div key={i} className="flex items-center gap-4 px-4 py-3 hover:bg-secondary/30">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${s.enabled ? 'bg-success' : 'bg-muted'}`} />
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-medium text-foreground">{s.name}</span>
                  {s.description && <p className="text-[10px] text-muted-foreground truncate mt-0.5">{s.description}</p>}
                </div>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${s.enabled ? 'bg-success/10 text-success' : 'bg-secondary text-muted-foreground'}`}>
                  {s.enabled ? 'enabled' : 'disabled'}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState icon={Zap} text="No skills installed yet." />
        )
      )}
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
