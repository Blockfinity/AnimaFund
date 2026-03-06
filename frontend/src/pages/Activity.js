import React, { useState, useEffect, useCallback } from 'react';
import { Activity as ActivityIcon, Clock } from 'lucide-react';

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
  const [tab, setTab] = useState('tools');
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [actRes, msgRes, hbRes] = await Promise.all([
        fetch(`${API}/api/live/activity?limit=100`),
        fetch(`${API}/api/live/messages?limit=50`),
        fetch(`${API}/api/live/heartbeat?limit=30`),
      ]);
      const [act, msg, hb] = await Promise.all([actRes.json(), msgRes.json(), hbRes.json()]);
      setActivities(act.activities || []);
      setMessages(msg.messages || []);
      setHeartbeat(hb.history || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 8000); return () => clearInterval(i); }, [fetchData]);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>;

  const hasData = activities.length > 0 || messages.length > 0 || heartbeat.length > 0;

  return (
    <div data-testid="activity-page" className="space-y-4 animate-slide-in">
      {/* Tabs */}
      <div className="flex items-center gap-1 bg-white border border-border rounded-sm p-1">
        {[['tools', `Tool Calls (${activities.length})`], ['messages', `Messages (${messages.length})`], ['heartbeat', `Heartbeat (${heartbeat.length})`]].map(([id, label]) => (
          <button key={id} data-testid={`activity-tab-${id}`} onClick={() => setTab(id)}
            className={`px-4 py-2 rounded-sm text-sm font-medium transition-colors ${tab === id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
            {label}
          </button>
        ))}
      </div>

      {!hasData ? (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <ActivityIcon className="w-8 h-8 text-border mb-3" />
          <p className="text-sm text-muted-foreground max-w-md">No activity yet. This page shows every tool call, social message, and heartbeat event from the running engine.</p>
        </div>
      ) : (
        <>
          {tab === 'tools' && (
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
          )}
          {tab === 'messages' && (
            <div className="bg-white border border-border rounded-sm divide-y divide-border">
              {messages.length > 0 ? messages.map((m, i) => (
                <div key={i} className="px-4 py-3 hover:bg-secondary/30">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-foreground">{m.from_address?.slice(0, 10)}...</span>
                    <span className="text-[10px] text-muted-foreground">→</span>
                    <span className="text-xs font-mono text-foreground">{m.to_address?.slice(0, 10)}...</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-sm ${m.status === 'processed' ? 'bg-success/10 text-success' : 'bg-secondary text-muted-foreground'}`}>{m.status}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{m.content?.slice(0, 200)}</p>
                  <span className="text-[9px] text-muted-foreground">{timeAgo(m.created_at)}</span>
                </div>
              )) : <div className="p-4 text-xs text-muted-foreground">No messages yet</div>}
            </div>
          )}
          {tab === 'heartbeat' && (
            <div className="bg-white border border-border rounded-sm divide-y divide-border">
              {heartbeat.length > 0 ? heartbeat.map((h, i) => (
                <div key={i} className="flex items-center gap-4 px-4 py-3 hover:bg-secondary/30">
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${h.result === 'success' ? 'bg-success' : h.result === 'failure' ? 'bg-error' : 'bg-warning'}`} />
                  <span className="text-xs font-mono text-foreground">{h.task}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-sm ${h.result === 'success' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'}`}>{h.result}</span>
                  {h.duration_ms && <span className="text-[10px] font-mono text-muted-foreground">{h.duration_ms}ms</span>}
                  <span className="text-[10px] font-mono text-muted-foreground ml-auto">{timeAgo(h.started_at)}</span>
                </div>
              )) : <div className="p-4 text-xs text-muted-foreground">No heartbeat events yet</div>}
            </div>
          )}
        </>
      )}
    </div>
  );
}
