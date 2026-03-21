import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Eye, MessageSquare, Send, Zap, Radio, Search } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

/* ─── Force-directed graph on canvas ─── */
function GraphCanvas({ nodes, edges, selectedNode, onSelectNode }) {
  const canvasRef = useRef(null);
  const [positions, setPositions] = useState({});

  useEffect(() => {
    if (!nodes.length) return;
    // Initialize positions in a circle
    const cx = 400, cy = 250, r = 180;
    const pos = {};
    nodes.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / nodes.length;
      pos[n.id] = { x: cx + r * Math.cos(angle) + (Math.random() - 0.5) * 40, y: cy + r * Math.sin(angle) + (Math.random() - 0.5) * 40 };
    });
    setPositions(pos);
  }, [nodes]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !Object.keys(positions).length) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.offsetWidth;
    const h = canvas.height = canvas.offsetHeight;
    ctx.clearRect(0, 0, w, h);

    // Draw edges
    edges.forEach(e => {
      const from = positions[e.from];
      const to = positions[e.to];
      if (!from || !to) return;
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      ctx.stroke();
    });

    // Draw nodes
    nodes.forEach(n => {
      const p = positions[n.id];
      if (!p) return;
      const isSelected = selectedNode && selectedNode.id === n.id;
      const radius = isSelected ? 18 : 12;

      // Glow for selected
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 24, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';
        ctx.fill();
      }

      // Node circle
      ctx.beginPath();
      ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = isSelected ? '#10b981' : (n.active ? '#334155' : '#1e293b');
      ctx.fill();
      ctx.strokeStyle = isSelected ? '#10b981' : '#475569';
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.stroke();

      // Label
      ctx.fillStyle = isSelected ? '#fff' : '#94a3b8';
      ctx.font = `${isSelected ? '11' : '9'}px JetBrains Mono, monospace`;
      ctx.textAlign = 'center';
      ctx.fillText(n.label.slice(0, 12), p.x, p.y + radius + 14);
    });
  }, [positions, nodes, edges, selectedNode]);

  const handleClick = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    for (const n of nodes) {
      const p = positions[n.id];
      if (p && Math.hypot(x - p.x, y - p.y) < 20) { onSelectNode(n); return; }
    }
    onSelectNode(null);
  };

  return <canvas ref={canvasRef} onClick={handleClick} style={{ width: '100%', height: '100%', cursor: 'crosshair' }} />;
}

export default function Dimensions() {
  const [mode, setMode] = useState('simulation');
  const [predictions, setPredictions] = useState([]);
  const [selectedPrediction, setSelectedPrediction] = useState(null);
  const [world, setWorld] = useState(null);
  const [liveAgents, setLiveAgents] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');

  const fetchPredictions = useCallback(async () => {
    try { const r = await fetch(`${API}/api/ultimus/predictions`); const d = await r.json(); setPredictions(d.predictions || []); } catch {}
  }, []);
  const fetchLive = useCallback(async () => {
    try { const r = await fetch(`${API}/api/dimensions/live`); const d = await r.json(); setLiveAgents(d.agents || []); } catch {}
  }, []);
  useEffect(() => { fetchPredictions(); fetchLive(); const iv = setInterval(fetchLive, 8000); return () => clearInterval(iv); }, [fetchPredictions, fetchLive]);

  const loadWorld = async (predId) => {
    try { const r = await fetch(`${API}/api/dimensions/simulation/${predId}`); const d = await r.json(); setWorld(d); setSelectedPrediction(predId); setSelectedEntity(null); setChatMessages([]); } catch {}
  };

  const sendChat = async () => {
    if (!chatInput.trim() || !selectedEntity) return;
    setChatMessages(prev => [...prev, { role: 'user', content: chatInput }]);
    const msg = chatInput; setChatInput(''); setChatLoading(true);
    try {
      const body = mode === 'simulation'
        ? { prediction_id: selectedPrediction, persona_name: selectedEntity.name, message: msg, mode: 'simulation' }
        : { agent_id: selectedEntity.agent_id, message: msg, mode: 'live' };
      const r = await fetch(`${API}/api/dimensions/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const d = await r.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: d.response || d.detail || 'No response' }]);
    } catch (e) { setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + e.message }]); }
    setChatLoading(false);
  };

  // Build graph nodes and edges from world data
  const graphNodes = (mode === 'simulation' ? (world?.personas || []) : liveAgents).map(e => ({
    id: e.name || e.agent_id,
    label: e.name || e.agent_id || '',
    role: e.role || e.status || '',
    active: e.engine_running || (e.actions_count > 0),
    data: e,
  }));
  const graphEdges = (world?.relationships || []).map(r => ({ from: r.from, to: r.to }));

  const filteredEntities = graphNodes.filter(n =>
    !searchFilter || n.label.toLowerCase().includes(searchFilter.toLowerCase()) || (n.role || '').toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div data-testid="dimensions-page" style={{ padding: '16px 20px', height: 'calc(100vh - 32px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Eye size={18} style={{ color: '#10b981' }} />
          <span style={{ fontSize: '18px', fontWeight: 800, color: '#e2e8f0', fontFamily: 'JetBrains Mono, monospace', letterSpacing: '-0.5px' }}>DIMENSIONS</span>
          <span style={{ color: '#475569', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>
            {graphNodes.length} entities {mode === 'live' ? '(live)' : ''}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '2px', background: '#0a0f1a', borderRadius: '4px', padding: '2px' }}>
          {[{ id: 'simulation', label: 'Simulation', icon: Zap }, { id: 'live', label: 'Live', icon: Radio }].map(m => (
            <button key={m.id} onClick={() => { setMode(m.id); setSelectedEntity(null); setChatMessages([]); }}
              style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '5px 12px', borderRadius: '3px', border: 'none', cursor: 'pointer', fontSize: '11px', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace',
                background: mode === m.id ? '#1e293b' : 'transparent', color: mode === m.id ? '#10b981' : '#475569' }}>
              <m.icon size={11} /> {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main 3-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr 280px', gap: '8px', flex: 1, minHeight: 0 }}>
        {/* LEFT: compact entity list */}
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {mode === 'simulation' && (
            <div style={{ marginBottom: '8px' }}>
              {predictions.filter(p => p.status === 'completed').slice(0, 3).map((p, i) => (
                <div key={i} onClick={() => loadWorld(p.id)} style={{ padding: '6px 8px', cursor: 'pointer', borderRadius: '3px', fontSize: '11px', marginBottom: '2px',
                  background: selectedPrediction === p.id ? '#1e293b' : 'transparent', color: selectedPrediction === p.id ? '#e2e8f0' : '#64748b', borderLeft: selectedPrediction === p.id ? '2px solid #10b981' : '2px solid transparent' }}>
                  {(p.goal || '').slice(0, 30)}{(p.goal || '').length > 30 ? '...' : ''}
                </div>
              ))}
            </div>
          )}
          <div style={{ position: 'relative', marginBottom: '6px' }}>
            <Search size={11} style={{ position: 'absolute', left: '8px', top: '7px', color: '#475569' }} />
            <input value={searchFilter} onChange={e => setSearchFilter(e.target.value)} placeholder="Filter..."
              style={{ width: '100%', background: '#0f172a', border: '1px solid #1e293b', borderRadius: '3px', color: '#94a3b8', padding: '5px 8px 5px 24px', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }} />
          </div>
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {filteredEntities.map((n, i) => {
              const isSel = selectedEntity && (selectedEntity.name === n.data.name || selectedEntity.agent_id === n.data.agent_id);
              return (
                <div key={i} onClick={() => { setSelectedEntity(n.data); setChatMessages([]); }}
                  style={{ padding: '5px 8px', cursor: 'pointer', borderRadius: '3px', marginBottom: '1px', display: 'flex', alignItems: 'center', gap: '6px',
                    background: isSel ? '#1e293b' : 'transparent', borderLeft: isSel ? '2px solid #10b981' : '2px solid transparent' }}>
                  <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: n.active ? '#10b981' : '#334155', flexShrink: 0 }} />
                  <div style={{ minWidth: 0, overflow: 'hidden' }}>
                    <div style={{ color: isSel ? '#e2e8f0' : '#94a3b8', fontSize: '11px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{n.label}</div>
                    <div style={{ color: '#475569', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace' }}>{n.role}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* CENTER: graph canvas + selected entity detail */}
        <div style={{ background: '#080c14', border: '1px solid #1e293b', borderRadius: '4px', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {graphNodes.length > 0 ? (
            <div style={{ flex: 1, position: 'relative' }}>
              <GraphCanvas nodes={graphNodes} edges={graphEdges} selectedNode={selectedEntity ? graphNodes.find(n => n.id === (selectedEntity.name || selectedEntity.agent_id)) : null}
                onSelectNode={(n) => { if (n) { setSelectedEntity(n.data); setChatMessages([]); } else setSelectedEntity(null); }} />
              {/* Legend */}
              <div style={{ position: 'absolute', bottom: '8px', left: '8px', display: 'flex', gap: '10px', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace', color: '#475569' }}>
                <span><span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', marginRight: '3px' }}></span>active</span>
                <span><span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: '#334155', marginRight: '3px' }}></span>idle</span>
              </div>
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#334155', fontSize: '12px', fontFamily: 'JetBrains Mono, monospace' }}>
              {mode === 'simulation' ? 'Select a prediction to visualize' : 'No live agents'}
            </div>
          )}
          {/* Bottom detail strip for selected entity */}
          {selectedEntity && (
            <div style={{ borderTop: '1px solid #1e293b', padding: '10px 12px', background: '#0f172a', flexShrink: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ color: '#10b981', fontSize: '12px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>{selectedEntity.name || selectedEntity.agent_id}</span>
                <span style={{ color: '#475569', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>{selectedEntity.role || selectedEntity.status}</span>
                {selectedEntity.tools && <span style={{ color: '#334155', fontSize: '9px' }}>{selectedEntity.tools.join(' | ')}</span>}
              </div>
              {selectedEntity.personality && <div style={{ color: '#64748b', fontSize: '11px', lineHeight: 1.4 }}>{selectedEntity.personality}</div>}
              {selectedEntity.strategy && <div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '4px' }}>{selectedEntity.strategy}</div>}
              <div style={{ display: 'flex', gap: '16px', marginTop: '6px', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>
                <span style={{ color: '#10b981' }}>+${(selectedEntity.revenue || 0).toFixed(2)}</span>
                <span style={{ color: '#f87171' }}>-${(selectedEntity.expenses || 0).toFixed(2)}</span>
                <span style={{ color: '#64748b' }}>{selectedEntity.actions_count || 0} actions</span>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: chat */}
        <div style={{ display: 'flex', flexDirection: 'column', background: '#0a0f1a', border: '1px solid #1e293b', borderRadius: '4px', minHeight: 0 }}>
          <div style={{ padding: '8px 10px', borderBottom: '1px solid #1e293b', display: 'flex', alignItems: 'center', gap: '5px', flexShrink: 0 }}>
            <MessageSquare size={12} style={{ color: '#10b981' }} />
            <span style={{ color: '#94a3b8', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>
              {selectedEntity ? (selectedEntity.name || selectedEntity.agent_id) : 'select entity'}
            </span>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
            {chatMessages.length === 0 && selectedEntity && (
              <div style={{ color: '#334155', fontSize: '10px', textAlign: 'center', padding: '20px 8px', fontFamily: 'JetBrains Mono, monospace' }}>
                Ask about decisions, strategy, predictions, or inject new variables.
              </div>
            )}
            {chatMessages.map((msg, i) => (
              <div key={i} style={{ marginBottom: '8px' }}>
                <div style={{ color: '#475569', fontSize: '9px', fontFamily: 'JetBrains Mono, monospace', marginBottom: '2px' }}>{msg.role === 'user' ? 'you' : selectedEntity?.name || 'agent'}</div>
                <div style={{ color: msg.role === 'user' ? '#94a3b8' : '#e2e8f0', fontSize: '12px', lineHeight: 1.5, paddingLeft: '8px', borderLeft: `2px solid ${msg.role === 'user' ? '#334155' : '#10b981'}` }}>
                  {msg.content}
                </div>
              </div>
            ))}
            {chatLoading && <div style={{ color: '#475569', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>...</div>}
          </div>
          <div style={{ padding: '6px', borderTop: '1px solid #1e293b', display: 'flex', gap: '4px', flexShrink: 0 }}>
            <input value={chatInput} onChange={e => setChatInput(e.target.value)} disabled={!selectedEntity}
              onKeyDown={e => e.key === 'Enter' && sendChat()} placeholder={selectedEntity ? "Ask..." : "Select entity"}
              style={{ flex: 1, background: '#0f172a', border: '1px solid #1e293b', borderRadius: '3px', color: '#e2e8f0', padding: '6px 8px', fontSize: '11px' }} />
            <button onClick={sendChat} disabled={!selectedEntity || chatLoading}
              style={{ background: '#10b981', border: 'none', borderRadius: '3px', padding: '6px 10px', cursor: 'pointer' }}>
              <Send size={12} style={{ color: '#fff' }} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
