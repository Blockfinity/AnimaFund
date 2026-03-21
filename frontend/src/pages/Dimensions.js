import React, { useState, useEffect, useCallback } from 'react';
import { Eye, MessageSquare, Send, Zap, Users, Activity, Radio, ChevronRight } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Dimensions() {
  const [mode, setMode] = useState('simulation'); // simulation or live
  const [predictions, setPredictions] = useState([]);
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [world, setWorld] = useState(null);
  const [liveAgents, setLiveAgents] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const fetchPredictions = useCallback(async () => {
    try { const r = await fetch(`${API}/api/ultimus/predictions`); const d = await r.json(); setPredictions(d.predictions || []); } catch {}
  }, []);

  const fetchLiveAgents = useCallback(async () => {
    try { const r = await fetch(`${API}/api/dimensions/live`); const d = await r.json(); setLiveAgents(d.agents || []); } catch {}
  }, []);

  useEffect(() => { fetchPredictions(); fetchLiveAgents(); const iv = setInterval(fetchLiveAgents, 10000); return () => clearInterval(iv); }, [fetchPredictions, fetchLiveAgents]);

  const loadWorld = async (predId) => {
    try {
      const r = await fetch(`${API}/api/dimensions/simulation/${predId}`);
      const d = await r.json();
      setWorld(d);
      setSelectedPrediction(predId);
      setSelectedEntity(null);
      setChatMessages([]);
    } catch (e) { console.error(e); }
  };

  const sendChat = async () => {
    if (!chatInput.trim() || !selectedEntity) return;
    const userMsg = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);
    try {
      const body = mode === 'simulation'
        ? { prediction_id: selectedPrediction, persona_name: selectedEntity.name, message: chatInput, mode: 'simulation' }
        : { agent_id: selectedEntity.agent_id, message: chatInput, mode: 'live' };
      const r = await fetch(`${API}/api/dimensions/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const d = await r.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: d.response || d.detail || 'No response' }]);
    } catch (e) { setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + e.message }]); }
    setChatLoading(false);
  };

  const entities = mode === 'simulation' ? (world?.personas || []) : liveAgents;

  return (
    <div data-testid="dimensions-page" style={{ padding: '20px', height: 'calc(100vh - 40px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Eye size={20} style={{ color: '#10b981' }} />
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#e2e8f0', margin: 0, fontFamily: 'JetBrains Mono, monospace' }}>DIMENSIONS</h1>
          <span style={{ background: '#064e3b', color: '#10b981', fontSize: '9px', fontWeight: 700, padding: '2px 8px', borderRadius: '3px', fontFamily: 'JetBrains Mono, monospace' }}>GOD'S-EYE VIEW</span>
        </div>
        <div style={{ display: 'flex', gap: '4px' }}>
          {[{ id: 'simulation', label: 'Simulation', icon: Zap }, { id: 'live', label: 'Live', icon: Radio }].map(m => (
            <button key={m.id} onClick={() => { setMode(m.id); setSelectedEntity(null); setChatMessages([]); }}
              style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '6px 12px', borderRadius: '4px', border: 'none', cursor: 'pointer', fontSize: '11px', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace',
                background: mode === m.id ? '#1e293b' : 'transparent', color: mode === m.id ? '#10b981' : '#64748b' }}>
              <m.icon size={12} /> {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr 320px', gap: '12px', flex: 1, minHeight: 0 }}>
        {/* Left: Entity list */}
        <div style={{ background: '#0a0f1a', border: '1px solid #1e293b', borderRadius: '6px', padding: '12px', overflowY: 'auto' }}>
          {mode === 'simulation' && (
            <>
              <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>Worlds</div>
              {predictions.filter(p => p.status === 'completed').map((p, i) => (
                <div key={i} onClick={() => loadWorld(p.id)}
                  style={{ padding: '8px', borderRadius: '4px', marginBottom: '4px', cursor: 'pointer',
                    background: selectedPrediction === p.id ? '#1e293b' : 'transparent', border: selectedPrediction === p.id ? '1px solid #334155' : '1px solid transparent' }}>
                  <div style={{ color: '#e2e8f0', fontSize: '11px', fontWeight: 500 }}>{(p.goal || '').slice(0, 40)}</div>
                  <div style={{ color: '#475569', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace' }}>{p.personas?.length || 0} personas</div>
                </div>
              ))}
              {predictions.filter(p => p.status === 'completed').length === 0 && (
                <div style={{ color: '#475569', fontSize: '11px', padding: '8px' }}>No simulations yet. Run a prediction in Ultimus first.</div>
              )}
            </>
          )}

          <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '8px', marginTop: mode === 'simulation' ? '16px' : 0, textTransform: 'uppercase', letterSpacing: '1px' }}>
            {mode === 'simulation' ? 'Personas' : 'Live Animas'}
          </div>
          {entities.map((e, i) => {
            const name = e.name || e.agent_id || `Entity ${i}`;
            const role = e.role || e.status || '';
            const isSelected = selectedEntity && (selectedEntity.name === name || selectedEntity.agent_id === e.agent_id);
            return (
              <div key={i} onClick={() => { setSelectedEntity(e); setChatMessages([]); }}
                style={{ padding: '8px', borderRadius: '4px', marginBottom: '3px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px',
                  background: isSelected ? '#1e293b' : 'transparent', borderLeft: isSelected ? '2px solid #10b981' : '2px solid transparent' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: e.engine_running ? '#10b981' : (e.actions_count > 0 ? '#fbbf24' : '#475569'), flexShrink: 0 }} />
                <div style={{ minWidth: 0 }}>
                  <div style={{ color: '#e2e8f0', fontSize: '11px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{name}</div>
                  <div style={{ color: '#475569', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace' }}>{role}</div>
                </div>
              </div>
            );
          })}
          {entities.length === 0 && (
            <div style={{ color: '#475569', fontSize: '11px', padding: '8px' }}>
              {mode === 'simulation' ? 'Select a world above' : 'No live Animas reporting'}
            </div>
          )}
        </div>

        {/* Center: Entity detail / Network visualization */}
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '6px', padding: '16px', overflowY: 'auto' }}>
          {selectedEntity ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981' }} />
                <h2 style={{ color: '#e2e8f0', fontSize: '16px', fontWeight: 700, margin: 0 }}>{selectedEntity.name || selectedEntity.agent_id}</h2>
                <span style={{ color: '#10b981', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', background: '#064e3b', padding: '2px 8px', borderRadius: '3px' }}>
                  {selectedEntity.role || selectedEntity.status || 'active'}
                </span>
              </div>

              {/* Persona details */}
              {selectedEntity.personality && (
                <div style={{ background: '#1e293b', borderRadius: '4px', padding: '12px', marginBottom: '10px' }}>
                  <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '4px' }}>PERSONALITY</div>
                  <div style={{ color: '#cbd5e1', fontSize: '12px', lineHeight: 1.5 }}>{selectedEntity.personality}</div>
                </div>
              )}
              {selectedEntity.strategy && (
                <div style={{ background: '#1e293b', borderRadius: '4px', padding: '12px', marginBottom: '10px' }}>
                  <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '4px' }}>STRATEGY</div>
                  <div style={{ color: '#cbd5e1', fontSize: '12px', lineHeight: 1.5 }}>{selectedEntity.strategy}</div>
                </div>
              )}

              {/* Tools */}
              {selectedEntity.tools && (
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '10px' }}>
                  {selectedEntity.tools.map((t, i) => (
                    <span key={i} style={{ background: '#0a0f1a', border: '1px solid #334155', borderRadius: '3px', padding: '2px 8px', fontSize: '10px', color: '#94a3b8', fontFamily: 'JetBrains Mono, monospace' }}>{t}</span>
                  ))}
                </div>
              )}

              {/* Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '12px' }}>
                {[
                  { label: 'Actions', value: selectedEntity.actions_count || 0, color: '#e2e8f0' },
                  { label: 'Revenue', value: `$${(selectedEntity.revenue || 0).toFixed(2)}`, color: '#10b981' },
                  { label: 'Expenses', value: `$${(selectedEntity.expenses || 0).toFixed(2)}`, color: '#f87171' },
                ].map((s, i) => (
                  <div key={i} style={{ background: '#1e293b', borderRadius: '4px', padding: '8px', textAlign: 'center' }}>
                    <div style={{ color: '#475569', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace' }}>{s.label}</div>
                    <div style={{ color: s.color, fontSize: '14px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>{s.value}</div>
                  </div>
                ))}
              </div>

              {/* Relationships */}
              {world?.relationships && (
                <div>
                  <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '6px' }}>CONNECTIONS</div>
                  {world.relationships.filter(r => r.from === selectedEntity.name || r.to === selectedEntity.name).map((r, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 0', fontSize: '11px' }}>
                      <span style={{ color: '#94a3b8' }}>{r.from === selectedEntity.name ? r.to : r.from}</span>
                      <span style={{ color: '#334155', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace' }}>{r.type}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569' }}>
              <Eye size={32} style={{ marginBottom: '12px', opacity: 0.3 }} />
              <div style={{ fontSize: '13px', textAlign: 'center' }}>
                {mode === 'simulation' ? 'Select a simulated world, then click a persona to observe' : 'Select a live Anima to observe'}
              </div>
            </div>
          )}
        </div>

        {/* Right: Chat panel */}
        <div style={{ background: '#0a0f1a', border: '1px solid #1e293b', borderRadius: '6px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '12px', borderBottom: '1px solid #1e293b', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <MessageSquare size={14} style={{ color: '#10b981' }} />
            <span style={{ color: '#e2e8f0', fontSize: '12px', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace' }}>
              {selectedEntity ? `Chat with ${selectedEntity.name || selectedEntity.agent_id}` : 'Select an entity to chat'}
            </span>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
            {chatMessages.length === 0 && selectedEntity && (
              <div style={{ color: '#475569', fontSize: '11px', textAlign: 'center', padding: '20px 0' }}>
                Ask {selectedEntity.name || selectedEntity.agent_id} about their decisions, strategy, or what they predict next.
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div key={i} style={{ marginBottom: '10px', display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                <div style={{ background: msg.role === 'user' ? '#1e293b' : '#0f172a', border: '1px solid #334155', borderRadius: '6px', padding: '8px 12px', maxWidth: '90%', fontSize: '12px', color: '#e2e8f0', lineHeight: 1.5 }}>
                  {msg.content}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div style={{ color: '#64748b', fontSize: '11px', fontStyle: 'italic' }}>Thinking...</div>
            )}
          </div>
          <div style={{ padding: '8px', borderTop: '1px solid #1e293b', display: 'flex', gap: '6px' }}>
            <input value={chatInput} onChange={e => setChatInput(e.target.value)} disabled={!selectedEntity}
              onKeyDown={e => e.key === 'Enter' && sendChat()}
              placeholder={selectedEntity ? "Ask a question..." : "Select an entity first"}
              style={{ flex: 1, background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', padding: '8px', fontSize: '12px' }} />
            <button onClick={sendChat} disabled={!selectedEntity || chatLoading}
              style={{ background: '#10b981', border: 'none', borderRadius: '4px', padding: '8px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
              <Send size={14} style={{ color: '#fff' }} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
