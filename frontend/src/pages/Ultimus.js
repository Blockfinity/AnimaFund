import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Send, Search, Play, Loader2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Ultimus() {
  const [goal, setGoal] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const canvasRef = useRef(null);
  const [positions, setPositions] = useState({});

  const fetchPredictions = useCallback(async () => {
    try { const r = await fetch(`${API}/api/ultimus/predictions`); const d = await r.json(); setPredictions(d.predictions || []); } catch {}
  }, []);
  useEffect(() => { fetchPredictions(); }, [fetchPredictions]);

  // Run prediction
  const runPrediction = async () => {
    if (!goal.trim()) return;
    setLoading(true); setPrediction(null); setSelectedEntity(null); setChatMessages([]);
    try {
      const r = await fetch(`${API}/api/ultimus/predict`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, mode: 'quick', num_personas: 5, num_rounds: 3, seed_capital: 10 }) });
      const d = await r.json();
      if (d.detail) alert(d.detail);
      else { setPrediction(d); fetchPredictions(); }
    } catch (e) { alert(e.message); }
    setLoading(false);
  };

  // Load past prediction
  const loadPrediction = async (pred) => {
    setPrediction(pred); setSelectedEntity(null); setChatMessages([]);
    // Load full world data if available
    if (pred.id) {
      try { const r = await fetch(`${API}/api/dimensions/simulation/${pred.id}`); const d = await r.json();
        if (d.personas) setPrediction(p => ({ ...p, personas: d.personas, relationships: d.relationships }));
      } catch {}
    }
  };

  // Execute
  const executePrediction = async () => {
    if (!prediction?.id) return;
    setExecuting(true);
    try {
      const r = await fetch(`${API}/api/ultimus/execute`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prediction_id: prediction.id }) });
      const d = await r.json();
      if (d.detail) alert(d.detail);
      else setPrediction(p => ({ ...p, execution: d, status: 'executing' }));
      fetchPredictions();
    } catch (e) { alert(e.message); }
    setExecuting(false);
  };

  // Chat
  const sendChat = async () => {
    if (!chatInput.trim() || !selectedEntity) return;
    setChatMessages(prev => [...prev, { role: 'user', content: chatInput }]);
    const msg = chatInput; setChatInput(''); setChatLoading(true);
    try {
      const r = await fetch(`${API}/api/dimensions/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prediction_id: prediction?.id || '', persona_name: selectedEntity.name || '', message: msg, mode: 'simulation' }) });
      const d = await r.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: d.response || 'No response' }]);
    } catch (e) { setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + e.message }]); }
    setChatLoading(false);
  };

  // Draw graph on canvas
  const personas = prediction?.personas || [];
  const relationships = prediction?.relationships || [];

  useEffect(() => {
    if (!personas.length) return;
    const cx = 300, cy = 200, r = 140;
    const pos = {};
    personas.forEach((p, i) => {
      const angle = (2 * Math.PI * i) / personas.length - Math.PI / 2;
      pos[p.name] = { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
    });
    setPositions(pos);
  }, [personas]);

  useEffect(() => {
    const c = canvasRef.current;
    if (!c || !personas.length) return;
    const ctx = c.getContext('2d');
    c.width = c.offsetWidth; c.height = c.offsetHeight;
    ctx.clearRect(0, 0, c.width, c.height);

    // Edges
    relationships.forEach(r => {
      const a = positions[r.from], b = positions[r.to];
      if (!a || !b) return;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 1; ctx.stroke();
    });

    // Nodes
    personas.forEach(p => {
      const pos_p = positions[p.name];
      if (!pos_p) return;
      const sel = selectedEntity?.name === p.name;
      const rad = sel ? 16 : 10;
      if (sel) { ctx.beginPath(); ctx.arc(pos_p.x, pos_p.y, 22, 0, Math.PI * 2); ctx.fillStyle = 'rgba(16,185,129,0.12)'; ctx.fill(); }
      ctx.beginPath(); ctx.arc(pos_p.x, pos_p.y, rad, 0, Math.PI * 2);
      ctx.fillStyle = sel ? '#10b981' : '#334155'; ctx.fill();
      ctx.strokeStyle = sel ? '#10b981' : '#475569'; ctx.lineWidth = sel ? 2 : 1; ctx.stroke();
      ctx.fillStyle = sel ? '#fff' : '#94a3b8'; ctx.font = `${sel ? 10 : 9}px monospace`; ctx.textAlign = 'center';
      ctx.fillText(p.name?.slice(0, 14) || '', pos_p.x, pos_p.y + rad + 12);
    });
  }, [positions, personas, relationships, selectedEntity]);

  const handleCanvasClick = (e) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = e.clientX - rect.left, y = e.clientY - rect.top;
    for (const p of personas) {
      const pos_p = positions[p.name];
      if (pos_p && Math.hypot(x - pos_p.x, y - pos_p.y) < 20) { setSelectedEntity(p); setChatMessages([]); return; }
    }
    setSelectedEntity(null);
  };

  const filteredPersonas = personas.filter(p =>
    !searchFilter || p.name?.toLowerCase().includes(searchFilter.toLowerCase()) || p.role?.toLowerCase().includes(searchFilter.toLowerCase()));

  const strategy = prediction?.strategy;
  const cost = prediction?.cost_model;

  return (
    <div data-testid="ultimus-page" style={{ padding: '16px 20px', height: 'calc(100vh - 32px)', display: 'flex', flexDirection: 'column' }}>
      {/* Input bar — always visible at top */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexShrink: 0 }}>
        <input data-testid="ultimus-goal-input" value={goal} onChange={e => setGoal(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !loading && runPrediction()}
          placeholder="What do you want to predict? Describe in natural language..."
          style={{ flex: 1, background: '#0f172a', border: '1px solid #1e293b', borderRadius: '4px', color: '#e2e8f0', padding: '10px 14px', fontSize: '13px' }} />
        <button data-testid="ultimus-simulate-btn" onClick={runPrediction} disabled={loading || !goal.trim()}
          style={{ background: loading ? '#334155' : '#10b981', color: '#fff', border: 'none', borderRadius: '4px', padding: '10px 20px', fontSize: '13px', fontWeight: 700, cursor: loading ? 'wait' : 'pointer', fontFamily: 'JetBrains Mono, monospace', display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap' }}>
          {loading ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={14} />}
          {loading ? 'Simulating...' : 'Predict'}
        </button>
        {prediction?.status === 'completed' && (
          <button data-testid="ultimus-execute-btn" onClick={executePrediction} disabled={executing}
            style={{ background: executing ? '#334155' : '#dc2626', color: '#fff', border: 'none', borderRadius: '4px', padding: '10px 16px', fontSize: '12px', fontWeight: 700, cursor: executing ? 'wait' : 'pointer', fontFamily: 'JetBrains Mono, monospace', whiteSpace: 'nowrap' }}>
            {executing ? 'Deploying...' : 'Execute'}
          </button>
        )}
      </div>

      {/* Main area */}
      <div style={{ display: 'grid', gridTemplateColumns: prediction ? '180px 1fr 260px' : '1fr', gap: '8px', flex: 1, minHeight: 0 }}>

        {/* Left: entity list (only when prediction loaded) */}
        {prediction && (
          <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div style={{ position: 'relative', marginBottom: '6px' }}>
              <Search size={11} style={{ position: 'absolute', left: '7px', top: '7px', color: '#475569' }} />
              <input value={searchFilter} onChange={e => setSearchFilter(e.target.value)} placeholder="Filter..."
                style={{ width: '100%', background: '#0a0f1a', border: '1px solid #1e293b', borderRadius: '3px', color: '#94a3b8', padding: '5px 8px 5px 22px', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }} />
            </div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {filteredPersonas.map((p, i) => (
                <div key={i} onClick={() => { setSelectedEntity(p); setChatMessages([]); }}
                  style={{ padding: '5px 8px', cursor: 'pointer', borderRadius: '3px', marginBottom: '1px', display: 'flex', alignItems: 'center', gap: '6px',
                    background: selectedEntity?.name === p.name ? '#1e293b' : 'transparent', borderLeft: selectedEntity?.name === p.name ? '2px solid #10b981' : '2px solid transparent' }}>
                  <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: (p.actions_count > 0) ? '#10b981' : '#334155', flexShrink: 0 }} />
                  <div style={{ minWidth: 0 }}>
                    <div style={{ color: selectedEntity?.name === p.name ? '#e2e8f0' : '#94a3b8', fontSize: '11px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{p.name}</div>
                    <div style={{ color: '#475569', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace' }}>{p.role}</div>
                  </div>
                </div>
              ))}
            </div>
            {/* Strategy + cost at bottom of left panel */}
            {strategy && (
              <div style={{ borderTop: '1px solid #1e293b', paddingTop: '8px', marginTop: '4px', fontSize: '10px', color: '#64748b' }}>
                <div style={{ color: '#94a3b8', marginBottom: '4px', lineHeight: 1.3 }}>{strategy.summary?.slice(0, 100)}</div>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  <span style={{ color: '#10b981' }}>{((strategy.confidence_score || 0) * 100).toFixed(0)}%</span>
                  {cost && <><span>${cost.total_cost_per_hour}/h</span><span>{cost.hours_funded}h funded</span><span style={{ color: cost.self_sustaining ? '#10b981' : '#f87171' }}>{cost.self_sustaining ? 'sustainable' : 'burns out'}</span></>}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Center: graph + detail strip OR past predictions */}
        <div style={{ background: '#080c14', border: '1px solid #1e293b', borderRadius: '4px', display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
          {prediction && personas.length > 0 ? (
            <>
              <div style={{ flex: 1, position: 'relative' }}>
                <canvas ref={canvasRef} onClick={handleCanvasClick} style={{ width: '100%', height: '100%', cursor: 'crosshair' }} />
              </div>
              {selectedEntity && (
                <div style={{ borderTop: '1px solid #1e293b', padding: '8px 12px', background: '#0f172a', flexShrink: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ color: '#10b981', fontSize: '12px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>{selectedEntity.name}</span>
                    <span style={{ color: '#475569', fontSize: '10px' }}>{selectedEntity.role}</span>
                    {selectedEntity.tools && <span style={{ color: '#334155', fontSize: '9px' }}>{selectedEntity.tools.join(' ')}</span>}
                  </div>
                  {selectedEntity.strategy && <div style={{ color: '#94a3b8', fontSize: '11px', lineHeight: 1.4 }}>{selectedEntity.strategy}</div>}
                  <div style={{ display: 'flex', gap: '12px', marginTop: '4px', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>
                    <span style={{ color: '#10b981' }}>+${(selectedEntity.revenue || 0).toFixed(2)}</span>
                    <span style={{ color: '#f87171' }}>-${(selectedEntity.expenses || 0).toFixed(2)}</span>
                    <span style={{ color: '#64748b' }}>{selectedEntity.actions_count || 0} actions</span>
                  </div>
                </div>
              )}
              {prediction.execution && (
                <div style={{ borderTop: '1px solid #065f46', padding: '6px 12px', background: '#0a1a0a', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#10b981' }}>
                  Deployed {prediction.execution.agents_created} agents in {prediction.execution.total_waves} waves
                </div>
              )}
            </>
          ) : loading ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px' }}>
              <Loader2 size={24} style={{ color: '#10b981', animation: 'spin 1s linear infinite' }} />
              <span style={{ color: '#475569', fontSize: '12px', fontFamily: 'JetBrains Mono, monospace' }}>Simulating personas...</span>
            </div>
          ) : (
            <div style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
              <div style={{ color: '#475569', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace', marginBottom: '12px' }}>
                {predictions.length} past predictions
              </div>
              {predictions.map((p, i) => (
                <div key={i} onClick={() => loadPrediction(p)}
                  style={{ padding: '8px 10px', cursor: 'pointer', borderRadius: '3px', marginBottom: '2px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    background: 'transparent', borderLeft: '2px solid transparent' }}
                  onMouseEnter={e => { e.currentTarget.style.background = '#0f172a'; e.currentTarget.style.borderLeftColor = '#334155'; }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.borderLeftColor = 'transparent'; }}>
                  <div>
                    <div style={{ color: '#e2e8f0', fontSize: '12px' }}>{p.goal}</div>
                    <div style={{ color: '#475569', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace', marginTop: '2px' }}>
                      {p.personas?.length || 0} personas | {p.rounds_completed || 0} rounds | {((p.strategy?.confidence_score || 0) * 100).toFixed(0)}%
                    </div>
                  </div>
                  <span style={{ color: p.status === 'completed' ? '#10b981' : '#fbbf24', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace' }}>{p.status}</span>
                </div>
              ))}
              {predictions.length === 0 && (
                <div style={{ color: '#334155', fontSize: '12px', textAlign: 'center', padding: '40px 0' }}>
                  Type a prediction goal above and hit Predict
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: chat (only when prediction loaded) */}
        {prediction && (
          <div style={{ display: 'flex', flexDirection: 'column', background: '#0a0f1a', border: '1px solid #1e293b', borderRadius: '4px', minHeight: 0 }}>
            <div style={{ padding: '6px 10px', borderBottom: '1px solid #1e293b', color: '#64748b', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', flexShrink: 0 }}>
              {selectedEntity ? selectedEntity.name : 'click a node to chat'}
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
              {chatMessages.length === 0 && selectedEntity && (
                <div style={{ color: '#334155', fontSize: '10px', textAlign: 'center', padding: '16px 4px' }}>Ask about their strategy, decisions, or predictions.</div>
              )}
              {chatMessages.map((msg, i) => (
                <div key={i} style={{ marginBottom: '8px' }}>
                  <div style={{ color: '#475569', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace', marginBottom: '1px' }}>{msg.role === 'user' ? 'you' : selectedEntity?.name || 'agent'}</div>
                  <div style={{ color: msg.role === 'user' ? '#94a3b8' : '#e2e8f0', fontSize: '12px', lineHeight: 1.5, paddingLeft: '8px', borderLeft: `2px solid ${msg.role === 'user' ? '#334155' : '#10b981'}` }}>{msg.content}</div>
                </div>
              ))}
              {chatLoading && <div style={{ color: '#475569', fontSize: '10px' }}>...</div>}
            </div>
            <div style={{ padding: '6px', borderTop: '1px solid #1e293b', display: 'flex', gap: '4px', flexShrink: 0 }}>
              <input value={chatInput} onChange={e => setChatInput(e.target.value)} disabled={!selectedEntity}
                onKeyDown={e => e.key === 'Enter' && sendChat()} placeholder={selectedEntity ? "Ask..." : "Select node"}
                style={{ flex: 1, background: '#0f172a', border: '1px solid #1e293b', borderRadius: '3px', color: '#e2e8f0', padding: '6px 8px', fontSize: '11px' }} />
              <button onClick={sendChat} disabled={!selectedEntity || chatLoading}
                style={{ background: '#10b981', border: 'none', borderRadius: '3px', padding: '6px 10px', cursor: 'pointer' }}>
                <Send size={12} style={{ color: '#fff' }} />
              </button>
            </div>
          </div>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  );
}
