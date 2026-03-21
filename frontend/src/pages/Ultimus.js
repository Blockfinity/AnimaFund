import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Send, Play, Loader2, RefreshCw, ChevronDown } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';

const API = process.env.REACT_APP_BACKEND_URL;

// Dynamic color palette — assigned to entity types as they appear (not hardcoded)
const PALETTE = [
  '#ef4444', '#3b82f6', '#22c55e', '#a855f7', '#f59e0b', '#ec4899',
  '#06b6d4', '#f97316', '#6366f1', '#14b8a6', '#e11d48', '#84cc16',
  '#8b5cf6', '#0ea5e9', '#d946ef', '#fb923c', '#facc15', '#2dd4bf',
];
const LIVE_COLOR = '#10b981';
const _typeColorCache = {};
let _nextColorIdx = 0;

function getTypeColor(type) {
  if (!type) return '#94a3b8';
  if (!_typeColorCache[type]) {
    _typeColorCache[type] = PALETTE[_nextColorIdx % PALETTE.length];
    _nextColorIdx++;
  }
  return _typeColorCache[type];
}

function getNodeColor(node) {
  if (node.isLive) return LIVE_COLOR;
  return getTypeColor(node.role);
}

export default function Ultimus({ onSelectAgent }) {
  const [tab, setTab] = useState('graph'); // graph | workbench
  const [goal, setGoal] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [simEvents, setSimEvents] = useState([]);
  const [simRound, setSimRound] = useState(0);
  const [selectedNode, setSelectedNode] = useState(null);
  const [showEdgeLabels, setShowEdgeLabels] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [agentDropdownOpen, setAgentDropdownOpen] = useState(false);
  const graphRef = useRef();

  const fetchData = useCallback(async () => {
    try {
      const [pRes, aRes] = await Promise.all([
        fetch(`${API}/api/ultimus/predictions`), fetch(`${API}/api/dimensions/live`)
      ]);
      setPredictions((await pRes.json()).predictions || []);
      setAgents((await aRes.json()).agents || []);
    } catch {}
  }, []);
  useEffect(() => { fetchData(); const iv = setInterval(fetchData, 10000); return () => clearInterval(iv); }, [fetchData]);

  // Run prediction with SSE
  const runPrediction = async () => {
    if (!goal.trim()) return;
    setLoading(true); setPrediction(null); setSelectedNode(null); setSimEvents([]); setSimRound(0); setTab('graph');
    try {
      const response = await fetch(`${API}/api/ultimus/predict/stream`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, mode: 'quick', num_personas: 10, num_rounds: 3, seed_capital: 10 }),
      });
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const evt = JSON.parse(line.slice(6));
              if (evt.type === 'agent_action') setSimEvents(prev => [...prev, evt]);
              else if (evt.type === 'round_start') setSimRound(evt.round);
              else if (evt.id && evt.status) { setPrediction(evt); fetchData(); }
            } catch {}
          }
        }
      }
    } catch {
      try {
        const r = await fetch(`${API}/api/ultimus/predict`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ goal, mode: 'quick', num_personas: 10, num_rounds: 3, seed_capital: 10 }) });
        const d = await r.json();
        if (!d.detail) { setPrediction(d); fetchData(); }
      } catch {}
    }
    setLoading(false);
  };

  const executePrediction = async () => {
    if (!prediction?.id) return;
    setExecuting(true);
    try {
      const r = await fetch(`${API}/api/ultimus/execute`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prediction_id: prediction.id }) });
      const d = await r.json();
      if (!d.detail) setPrediction(p => ({ ...p, execution: d }));
      fetchData();
    } catch {}
    setExecuting(false);
  };

  const sendChat = async () => {
    if (!chatInput.trim() || !selectedNode) return;
    setChatMessages(prev => [...prev, { role: 'user', content: chatInput }]);
    const msg = chatInput; setChatInput(''); setChatLoading(true);
    try {
      const r = await fetch(`${API}/api/dimensions/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prediction_id: prediction?.id || '', persona_name: selectedNode.name || '', agent_id: selectedNode.agent_id || '', message: msg, mode: selectedNode.isLive ? 'live' : 'simulation' }) });
      const d = await r.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: d.response || 'No response' }]);
    } catch (e) { setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + e.message }]); }
    setChatLoading(false);
  };

  // Build graph data
  const graphData = useMemo(() => {
    const nodes = [], links = [], nodeIds = new Set();
    // Live agents
    agents.forEach(a => {
      const id = a.agent_id;
      if (!nodeIds.has(id)) {
        nodes.push({ id, name: a.name || id, role: a.status || 'Live Agent', isLive: true, actions: a.actions_count || 0, data: a });
        nodeIds.add(id);
      }
    });
    // Simulated personas from all predictions
    predictions.forEach(p => {
      (p.personas || []).forEach(ps => {
        const id = `sim:${ps.name}:${p.id}`;
        if (!nodeIds.has(id)) {
          nodes.push({ id, name: ps.name, role: ps.role || 'Simulated', isLive: false, actions: ps.actions_count || 0, data: { ...ps, prediction_id: p.id, is_simulated: true } });
          nodeIds.add(id);
        }
      });
      // Knowledge graph entities
      const kg = p.knowledge_graph || {};
      (kg.entities || []).forEach(e => {
        const id = `kg:${e.name}:${p.id}`;
        if (!nodeIds.has(id)) {
          nodes.push({ id, name: e.name, role: e.type || 'Entity', isLive: false, actions: 0, data: { ...e, prediction_id: p.id, is_kg: true } });
          nodeIds.add(id);
        }
      });
      // Links from knowledge graph relationships
      (kg.relationships || []).forEach(r => {
        const src = `kg:${r.from}:${p.id}`, tgt = `kg:${r.to}:${p.id}`;
        if (nodeIds.has(src) && nodeIds.has(tgt)) links.push({ source: src, target: tgt, label: r.type || '' });
      });
      // Links from simulation relationships (who referenced whom)
      (p.relationships || []).forEach(r => {
        const src = `sim:${r.from}:${p.id}`, tgt = `sim:${r.to}:${p.id}`;
        if (nodeIds.has(src) && nodeIds.has(tgt)) links.push({ source: src, target: tgt, label: r.type || 'interacts' });
      });
    });
    return { nodes, links };
  }, [agents, predictions]);

  // Entity types for legend
  const entityTypes = useMemo(() => {
    const types = {};
    graphData.nodes.forEach(n => { const r = n.role || 'Unknown'; types[r] = (types[r] || 0) + 1; });
    return Object.entries(types).sort((a, b) => b[1] - a[1]);
  }, [graphData]);

  // Relation types
  const relationTypes = useMemo(() => {
    const types = {};
    graphData.links.forEach(l => { if (l.label) types[l.label] = (types[l.label] || 0) + 1; });
    return Object.entries(types).sort((a, b) => b[1] - a[1]);
  }, [graphData]);

  // All entities for dropdown
  const allEntities = graphData.nodes;

  return (
    <div data-testid="ultimus-page" style={{ height: 'calc(100vh - 0px)', display: 'flex', flexDirection: 'column', background: '#fff' }}>
      {/* Top bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '8px 16px', borderBottom: '1px solid #e5e7eb', flexShrink: 0 }}>
        <span style={{ fontSize: '16px', fontWeight: 800 }}>Ultimus</span>
        <div style={{ display: 'flex', gap: '0', background: '#f3f4f6', borderRadius: '6px', padding: '2px' }}>
          {['graph', 'workbench'].map(t => (
            <button key={t} onClick={() => setTab(t)} style={{ padding: '5px 16px', borderRadius: '4px', border: 'none', fontSize: '12px', fontWeight: 600, cursor: 'pointer',
              background: tab === t ? '#fff' : 'transparent', color: tab === t ? '#111' : '#9ca3af', boxShadow: tab === t ? '0 1px 2px rgba(0,0,0,0.05)' : 'none' }}>
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
        <input value={goal} onChange={e => setGoal(e.target.value)} onKeyDown={e => e.key === 'Enter' && !loading && runPrediction()}
          placeholder="Describe your prediction goal..." style={{ flex: 1, background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '7px 12px', fontSize: '13px', color: '#111' }} />
        <button onClick={runPrediction} disabled={loading || !goal.trim()} style={{ background: loading ? '#d1d5db' : '#111', color: '#fff', border: 'none', borderRadius: '6px', padding: '7px 18px', fontSize: '13px', fontWeight: 600, cursor: loading ? 'wait' : 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
          {loading ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={14} />}
          {loading ? `Round ${simRound}...` : 'Predict'}
        </button>
        {prediction?.status === 'completed' && (
          <button onClick={executePrediction} disabled={executing} style={{ background: '#dc2626', color: '#fff', border: 'none', borderRadius: '6px', padding: '7px 14px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
            {executing ? 'Deploying...' : 'Execute'}
          </button>
        )}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        {/* Graph tab */}
        {tab === 'graph' && (
          <>
            <div style={{ flex: 1, position: 'relative' }}>
              {graphData.nodes.length > 0 ? (
                <ForceGraph2D ref={graphRef} graphData={graphData}
                  nodeLabel={n => `${n.name} (${n.role})`}
                  nodeColor={n => (selectedNode && selectedNode.name === n.name) ? '#111' : getNodeColor(n)}
                  nodeVal={n => 3 + Math.min((n.actions || 0) * 0.3, 15)}
                  nodeCanvasObjectMode={() => 'after'}
                  nodeCanvasObject={(node, ctx, gs) => {
                    const fontSize = Math.max(9 / gs, 2.5);
                    const isSel = selectedNode && selectedNode.name === node.name;
                    ctx.font = `${isSel ? 'bold ' : ''}${fontSize}px sans-serif`;
                    ctx.textAlign = 'center';
                    ctx.fillStyle = isSel ? '#111' : '#6b7280';
                    const label = (node.name || '').length > 20 ? node.name.slice(0, 18) + '..' : node.name;
                    ctx.fillText(label, node.x, node.y + (node.val || 3) / gs + fontSize + 1);
                  }}
                  linkColor={() => '#e5e7eb'}
                  linkWidth={0.5}
                  linkLabel={showEdgeLabels ? (l => l.label || '') : undefined}
                  linkDirectionalArrowLength={showEdgeLabels ? 3 : 0}
                  onNodeClick={(node) => { setSelectedNode(node.data); setChatMessages([]); if (node.data.agent_id && onSelectAgent) onSelectAgent(node.data.agent_id); }}
                  cooldownTicks={80}
                />
              ) : loading ? (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <div style={{ padding: '12px 16px', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '13px', fontWeight: 600 }}>Simulating</span>
                    <span style={{ fontSize: '12px', color: '#9ca3af' }}>Round {simRound} | {simEvents.length} actions</span>
                  </div>
                  <div style={{ flex: 1, overflowY: 'auto', padding: '8px 16px' }}>
                    {simEvents.map((evt, i) => (
                      <div key={i} style={{ padding: '4px 0', borderBottom: '1px solid #f9fafb', fontSize: '12px' }}>
                        <span style={{ color: '#9ca3af', marginRight: '6px' }}>R{evt.round}</span>
                        <span style={{ fontWeight: 600 }}>{evt.agent}</span>
                        <div style={{ color: '#6b7280', marginTop: '1px', paddingLeft: '20px' }}>{evt.content?.slice(0, 150)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ padding: '20px', overflowY: 'auto', height: '100%' }}>
                  {predictions.map((p, i) => (
                    <div key={i} onClick={() => setPrediction(p)} style={{ padding: '10px', cursor: 'pointer', borderBottom: '1px solid #f3f4f6' }}
                      onMouseEnter={e => e.currentTarget.style.background = '#f9fafb'} onMouseLeave={e => e.currentTarget.style.background = ''}>
                      <div style={{ fontSize: '13px', color: '#111' }}>{p.goal}</div>
                      <div style={{ fontSize: '10px', color: '#9ca3af', marginTop: '2px' }}>{p.personas?.length || 0} personas · {p.rounds_completed || p.num_rounds || 0} rounds · {p.status}</div>
                    </div>
                  ))}
                  {!predictions.length && <div style={{ color: '#d1d5db', textAlign: 'center', padding: '60px 0' }}>Type a prediction goal and hit Predict</div>}
                </div>
              )}

              {/* Controls overlay */}
              {graphData.nodes.length > 0 && <>
                <div style={{ position: 'absolute', top: '12px', right: '12px', display: 'flex', gap: '8px' }}>
                  <button onClick={() => graphRef.current?.zoomToFit(400)} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '5px 10px', fontSize: '11px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <RefreshCw size={12} /> Fit
                  </button>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '5px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '5px 10px', fontSize: '11px', cursor: 'pointer' }}>
                    <input type="checkbox" checked={showEdgeLabels} onChange={e => setShowEdgeLabels(e.target.checked)} style={{ accentColor: '#111' }} />
                    Show Edge Labels
                  </label>
                </div>
                {/* Entity Types legend */}
                <div style={{ position: 'absolute', bottom: '12px', left: '12px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '10px 14px', maxWidth: '350px' }}>
                  <div style={{ fontSize: '10px', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '6px' }}>Entity Types</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 14px' }}>
                    {entityTypes.slice(0, 12).map(([type]) => (
                      <span key={type} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#374151' }}>
                        <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: getNodeColor({ role: type }), display: 'inline-block' }} />
                        {type}
                      </span>
                    ))}
                  </div>
                </div>
              </>}

              {/* Node Details card overlay */}
              {selectedNode && (
                <div style={{ position: 'absolute', top: '12px', left: '12px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '16px', width: '320px', maxHeight: '60vh', overflowY: 'auto', boxShadow: '0 4px 16px rgba(0,0,0,0.08)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span style={{ fontSize: '15px', fontWeight: 700 }}>Node Details</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ background: getNodeColor({ role: selectedNode.role || selectedNode.type }), color: '#fff', fontSize: '10px', fontWeight: 600, padding: '2px 10px', borderRadius: '12px' }}>{selectedNode.role || selectedNode.type || 'Agent'}</span>
                      <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: '16px' }}>x</button>
                    </div>
                  </div>
                  <div style={{ fontSize: '12px', color: '#374151', lineHeight: 1.8 }}>
                    <div><span style={{ color: '#9ca3af' }}>Name:</span> {selectedNode.name || selectedNode.agent_id}</div>
                    {selectedNode.agent_id && <div><span style={{ color: '#9ca3af' }}>ID:</span> <span style={{ fontFamily: 'monospace', fontSize: '10px' }}>{selectedNode.agent_id}</span></div>}
                    {selectedNode.status && <div><span style={{ color: '#9ca3af' }}>Status:</span> {selectedNode.status}</div>}
                    {selectedNode.personality && <div style={{ marginTop: '8px' }}><span style={{ color: '#9ca3af' }}>Personality:</span><div style={{ marginTop: '2px' }}>{selectedNode.personality}</div></div>}
                    {selectedNode.strategy && <div style={{ marginTop: '6px' }}><span style={{ color: '#9ca3af' }}>Strategy:</span><div style={{ marginTop: '2px' }}>{selectedNode.strategy}</div></div>}
                    {selectedNode.description && <div style={{ marginTop: '6px' }}><span style={{ color: '#9ca3af' }}>Summary:</span><div style={{ marginTop: '2px' }}>{selectedNode.description}</div></div>}
                    {(selectedNode.actions_count > 0 || selectedNode.goal_progress > 0) && (
                      <div style={{ marginTop: '6px' }}>
                        <span style={{ color: '#9ca3af' }}>Actions:</span> {selectedNode.actions_count || 0}
                        {selectedNode.goal_progress > 0 && <span style={{ marginLeft: '12px' }}><span style={{ color: '#9ca3af' }}>Progress:</span> {(selectedNode.goal_progress * 100).toFixed(0)}%</span>}
                      </div>
                    )}
                  </div>
                  {/* Inline chat */}
                  <div style={{ marginTop: '12px', borderTop: '1px solid #f3f4f6', paddingTop: '10px' }}>
                    <div style={{ maxHeight: '120px', overflowY: 'auto', marginBottom: '6px' }}>
                      {chatMessages.map((m, i) => (
                        <div key={i} style={{ fontSize: '11px', marginBottom: '6px' }}>
                          <span style={{ color: '#9ca3af' }}>{m.role === 'user' ? 'You' : selectedNode.name}:</span> {m.content.slice(0, 150)}
                        </div>
                      ))}
                      {chatLoading && <div style={{ fontSize: '11px', color: '#d1d5db' }}>Thinking...</div>}
                    </div>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <input value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendChat()}
                        placeholder="Ask..." style={{ flex: 1, background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '4px', padding: '5px 8px', fontSize: '11px' }} />
                      <button onClick={sendChat} disabled={chatLoading} style={{ background: '#111', border: 'none', borderRadius: '4px', padding: '5px 8px', cursor: 'pointer' }}>
                        <Send size={11} style={{ color: '#fff' }} />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right sidebar */}
            <div style={{ width: '320px', borderLeft: '1px solid #e5e7eb', overflowY: 'auto', flexShrink: 0, padding: '14px' }}>
              {/* Agent dropdown */}
              <div style={{ position: 'relative', marginBottom: '14px' }}>
                <button onClick={() => setAgentDropdownOpen(!agentDropdownOpen)} style={{ width: '100%', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '8px 10px', fontSize: '12px', cursor: 'pointer', color: '#111' }}>
                  <span>{selectedNode ? (selectedNode.name || selectedNode.agent_id) : 'Select agent...'}</span>
                  <ChevronDown size={14} style={{ color: '#9ca3af' }} />
                </button>
                {agentDropdownOpen && (
                  <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: '#fff', border: '1px solid #e5e7eb', borderRadius: '6px', marginTop: '2px', maxHeight: '200px', overflowY: 'auto', zIndex: 10, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
                    {allEntities.map((n, i) => (
                      <div key={i} onClick={() => { setSelectedNode(n.data); setChatMessages([]); setAgentDropdownOpen(false); if (n.data.agent_id && onSelectAgent) onSelectAgent(n.data.agent_id); }}
                        style={{ padding: '6px 10px', cursor: 'pointer', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px', borderBottom: '1px solid #f9fafb' }}
                        onMouseEnter={e => e.currentTarget.style.background = '#f9fafb'} onMouseLeave={e => e.currentTarget.style.background = ''}>
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: getNodeColor(n), flexShrink: 0 }} />
                        <span>{n.name}</span>
                        <span style={{ color: '#d1d5db', marginLeft: 'auto', fontSize: '10px' }}>{n.role}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Stats */}
              <div style={{ display: 'flex', justifyContent: 'space-around', padding: '12px 0', marginBottom: '14px', background: '#f9fafb', borderRadius: '6px' }}>
                <div style={{ textAlign: 'center' }}><div style={{ fontSize: '22px', fontWeight: 800 }}>{graphData.nodes.length}</div><div style={{ fontSize: '9px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Physical Node</div></div>
                <div style={{ textAlign: 'center' }}><div style={{ fontSize: '22px', fontWeight: 800 }}>{graphData.links.length}</div><div style={{ fontSize: '9px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Relationship Side</div></div>
                <div style={{ textAlign: 'center' }}><div style={{ fontSize: '22px', fontWeight: 800 }}>{entityTypes.length}</div><div style={{ fontSize: '9px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Types of Schema</div></div>
              </div>

              {/* Generated Entity Types */}
              <div style={{ marginBottom: '14px' }}>
                <div style={{ fontSize: '10px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>Generated Entity Types</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {entityTypes.map(([type]) => (
                    <span key={type} style={{ border: '1px solid #e5e7eb', borderRadius: '4px', padding: '3px 10px', fontSize: '11px', color: '#374151' }}>{type}</span>
                  ))}
                </div>
              </div>

              {/* Generated Relation Types */}
              {relationTypes.length > 0 && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '10px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>Generated Relation Types</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {relationTypes.map(([type]) => (
                      <span key={type} style={{ border: '1px solid #e5e7eb', borderRadius: '4px', padding: '3px 10px', fontSize: '11px', color: '#374151', fontFamily: 'monospace', textTransform: 'uppercase' }}>{type}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* System Dashboard */}
              <div style={{ background: '#18181b', borderRadius: '6px', padding: '10px 12px', color: '#a1a1aa', fontSize: '11px', fontFamily: 'monospace' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ color: '#71717a' }}>System Dashboard</span>
                  <span style={{ color: '#52525b', fontSize: '10px' }}>{prediction?.id || 'no prediction'}</span>
                </div>
                {simEvents.slice(-5).map((evt, i) => (
                  <div key={i} style={{ marginBottom: '2px', color: '#a1a1aa' }}>
                    <span style={{ color: '#6b7280' }}>{evt.ts?.slice(11, 19) || ''}</span> {evt.agent}: {(evt.content || '').slice(0, 60)}
                  </div>
                ))}
                {!simEvents.length && <div style={{ color: '#52525b' }}>No simulation events yet</div>}
              </div>
            </div>
          </>
        )}

        {/* Workbench tab */}
        {tab === 'workbench' && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px', maxWidth: '800px' }}>
            {predictions.map((p, i) => (
              <div key={i} style={{ border: '1px solid #e5e7eb', borderRadius: '8px', padding: '20px', marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 700 }}>{p.goal}</span>
                  <span style={{ background: p.status === 'completed' ? '#dcfce7' : '#fef3c7', color: p.status === 'completed' ? '#166534' : '#92400e', fontSize: '10px', fontWeight: 600, padding: '2px 10px', borderRadius: '12px', textTransform: 'uppercase' }}>{p.status}</span>
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>{p.personas?.length || 0} personas · {p.num_rounds || 0} rounds · {p.mode || 'quick'}</div>
                {p.strategy && <div style={{ marginTop: '8px', fontSize: '12px', color: '#374151' }}>{p.strategy.summary}</div>}
                {p.cost_model && (
                  <div style={{ marginTop: '8px', display: 'flex', gap: '16px', fontSize: '11px', color: '#6b7280' }}>
                    <span>${p.cost_model.total_cost_per_hour}/h</span>
                    <span>{p.cost_model.hours_funded}h funded</span>
                    <span style={{ color: p.cost_model.self_sustaining ? '#22c55e' : '#ef4444' }}>{p.cost_model.self_sustaining ? 'Self-sustaining' : 'Burns out'}</span>
                  </div>
                )}
              </div>
            ))}
            {!predictions.length && <div style={{ color: '#d1d5db', textAlign: 'center', padding: '60px 0' }}>No predictions yet</div>}
          </div>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  );
}
