import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Send, Search, Play, Loader2 } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';

const API = process.env.REACT_APP_BACKEND_URL;

const TYPE_COLORS = {
  Person: '#ef4444', Organization: '#22c55e', Technology: '#3b82f6', Market: '#f59e0b',
  Strategy: '#8b5cf6', Risk: '#ec4899', Platform: '#06b6d4', Company: '#f97316',
  MediaOutlet: '#a855f7', GovernmentAgency: '#14b8a6', default: '#6366f1',
};

export default function Ultimus() {
  const [goal, setGoal] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [showEdgeLabels, setShowEdgeLabels] = useState(false);
  const [simEvents, setSimEvents] = useState([]);
  const [simRound, setSimRound] = useState(0);
  const graphRef = useRef();

  const fetchPredictions = useCallback(async () => {
    try { const r = await fetch(`${API}/api/ultimus/predictions`); const d = await r.json(); setPredictions(d.predictions || []); } catch {}
  }, []);
  useEffect(() => { fetchPredictions(); }, [fetchPredictions]);

  // Run prediction with live SSE streaming
  const runPrediction = async () => {
    if (!goal.trim()) return;
    setLoading(true); setPrediction(null); setSelectedNode(null); setChatMessages([]);
    setSimEvents([]); setSimRound(0);
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
              const event = JSON.parse(line.slice(6));
              if (event.type === 'agent_action') setSimEvents(prev => [...prev, event]);
              else if (event.type === 'round_start') setSimRound(event.round);
              else if (event.type === 'complete' || (event.id && event.status)) {
                setPrediction(event); fetchPredictions();
              }
            } catch {}
          }
        }
      }
    } catch (e) {
      // Fallback to non-streaming
      try {
        const r = await fetch(`${API}/api/ultimus/predict`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ goal, mode: 'quick', num_personas: 10, num_rounds: 3, seed_capital: 10 }) });
        const d = await r.json();
        if (d.detail) alert(d.detail); else { setPrediction(d); fetchPredictions(); }
      } catch (e2) { alert(e2.message); }
    }
    setLoading(false);
  };

  const loadPrediction = async (pred) => {
    setPrediction(pred); setSelectedNode(null); setChatMessages([]);
    if (pred.id) {
      try { const r = await fetch(`${API}/api/dimensions/simulation/${pred.id}`); const d = await r.json();
        if (d.personas) setPrediction(p => ({ ...p, personas: d.personas, relationships: d.relationships, knowledge_graph: d.knowledge_graph }));
      } catch {}
    }
  };

  const executePrediction = async () => {
    if (!prediction?.id) return;
    setExecuting(true);
    try {
      const r = await fetch(`${API}/api/ultimus/execute`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prediction_id: prediction.id }) });
      const d = await r.json();
      if (d.detail) alert(d.detail); else setPrediction(p => ({ ...p, execution: d }));
      fetchPredictions();
    } catch (e) { alert(e.message); }
    setExecuting(false);
  };

  const sendChat = async () => {
    if (!chatInput.trim() || !selectedNode) return;
    setChatMessages(prev => [...prev, { role: 'user', content: chatInput }]);
    const msg = chatInput; setChatInput(''); setChatLoading(true);
    try {
      const r = await fetch(`${API}/api/dimensions/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prediction_id: prediction?.id || '', persona_name: selectedNode.name || '', message: msg, mode: 'simulation' }) });
      const d = await r.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: d.response || 'No response' }]);
    } catch (e) { setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + e.message }]); }
    setChatLoading(false);
  };

  // Build graph data from prediction
  const graphData = useMemo(() => {
    if (!prediction) return { nodes: [], links: [] };
    const nodes = [];
    const links = [];
    const nodeSet = new Set();

    // Add personas as nodes
    (prediction.personas || []).forEach(p => {
      if (!nodeSet.has(p.name)) {
        nodes.push({ id: p.name, name: p.name, type: p.role || 'Agent', val: 8 + (p.actions_count || 0) * 2, data: p, isPersona: true });
        nodeSet.add(p.name);
      }
    });

    // Add knowledge graph entities
    const kg = prediction.knowledge_graph || {};
    (kg.entities || []).forEach(e => {
      if (!nodeSet.has(e.name)) {
        nodes.push({ id: e.name, name: e.name, type: e.type || 'Entity', val: 4, data: e, isPersona: false });
        nodeSet.add(e.name);
      }
    });

    // Add relationships from knowledge graph
    (kg.relationships || []).forEach(r => {
      if (nodeSet.has(r.from) && nodeSet.has(r.to)) {
        links.push({ source: r.from, target: r.to, label: r.type || 'related' });
      }
    });

    // Add persona connections
    (prediction.relationships || []).forEach(r => {
      if (nodeSet.has(r.from) && nodeSet.has(r.to)) {
        links.push({ source: r.from, target: r.to, label: r.type || 'connected' });
      }
    });

    return { nodes, links };
  }, [prediction]);

  // Collect entity types for legend
  const entityTypes = useMemo(() => {
    const types = {};
    graphData.nodes.forEach(n => { types[n.type] = (types[n.type] || 0) + 1; });
    return Object.entries(types).sort((a, b) => b[1] - a[1]);
  }, [graphData]);

  const strategy = prediction?.strategy;
  const cost = prediction?.cost_model;

  return (
    <div data-testid="ultimus-page" style={{ height: 'calc(100vh - 0px)', display: 'flex', flexDirection: 'column', background: '#fff' }}>
      {/* Top bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 16px', borderBottom: '1px solid #e5e7eb', flexShrink: 0, background: '#fff' }}>
        <span style={{ fontSize: '16px', fontWeight: 800, color: '#111', fontFamily: 'system-ui' }}>Ultimus</span>
        <input data-testid="ultimus-goal-input" value={goal} onChange={e => setGoal(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !loading && runPrediction()}
          placeholder="Describe what you want to predict..."
          style={{ flex: 1, background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px', color: '#111', padding: '8px 12px', fontSize: '13px' }} />
        <button data-testid="ultimus-simulate-btn" onClick={runPrediction} disabled={loading || !goal.trim()}
          style={{ background: loading ? '#d1d5db' : '#111', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 20px', fontSize: '13px', fontWeight: 600, cursor: loading ? 'wait' : 'pointer', display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap' }}>
          {loading ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={14} />}
          {loading ? 'Simulating...' : 'Predict'}
        </button>
        {prediction?.status === 'completed' && (
          <button data-testid="ultimus-execute-btn" onClick={executePrediction} disabled={executing}
            style={{ background: '#dc2626', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 16px', fontSize: '12px', fontWeight: 600, cursor: executing ? 'wait' : 'pointer', whiteSpace: 'nowrap' }}>
            {executing ? 'Deploying...' : 'Execute →'}
          </button>
        )}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>
        {/* Graph area */}
        <div style={{ flex: 1, position: 'relative', background: '#fff' }}>
          {graphData.nodes.length > 0 ? (
            <>
              <ForceGraph2D ref={graphRef} graphData={graphData} width={undefined} height={undefined}
                nodeLabel={n => `${n.name} (${n.type})`}
                nodeColor={n => TYPE_COLORS[n.type] || TYPE_COLORS.default}
                nodeVal={n => n.val}
                nodeCanvasObjectMode={() => 'after'}
                nodeCanvasObject={(node, ctx, globalScale) => {
                  const label = node.name?.length > 16 ? node.name.slice(0, 14) + '...' : node.name;
                  const fontSize = Math.max(10 / globalScale, 3);
                  ctx.font = `${node.id === selectedNode?.name ? 'bold ' : ''}${fontSize}px sans-serif`;
                  ctx.textAlign = 'center';
                  ctx.fillStyle = node.id === selectedNode?.name ? '#111' : '#6b7280';
                  ctx.fillText(label, node.x, node.y + (node.val || 4) / globalScale + fontSize + 1);
                }}
                linkColor={() => '#d1d5db'}
                linkWidth={1}
                linkLabel={showEdgeLabels ? (l => l.label) : undefined}
                linkDirectionalArrowLength={3}
                linkDirectionalArrowRelPos={1}
                onNodeClick={(node) => { setSelectedNode(node.data); setChatMessages([]); }}
                cooldownTicks={100}
                enableZoomInteraction={true}
                enablePanInteraction={true}
              />
              {/* Controls overlay */}
              <div style={{ position: 'absolute', top: '12px', right: '12px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '12px', color: '#6b7280', background: '#fff', padding: '4px 10px', borderRadius: '16px', border: '1px solid #e5e7eb' }}>
                  <input type="checkbox" checked={showEdgeLabels} onChange={e => setShowEdgeLabels(e.target.checked)} style={{ accentColor: '#111' }} />
                  Show Edge Labels
                </label>
                <button onClick={() => graphRef.current?.zoomToFit(400)} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: '16px', padding: '4px 10px', fontSize: '12px', color: '#6b7280', cursor: 'pointer' }}>
                  Fit
                </button>
              </div>
              {/* Entity type legend */}
              {entityTypes.length > 0 && (
                <div style={{ position: 'absolute', bottom: '12px', left: '12px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '10px 14px' }}>
                  <div style={{ fontSize: '10px', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '6px' }}>Entity Types</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 16px' }}>
                    {entityTypes.map(([type, count]) => (
                      <span key={type} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: '#374151' }}>
                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: TYPE_COLORS[type] || TYPE_COLORS.default, display: 'inline-block' }} />
                        {type}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {/* Stats overlay */}
              {prediction?.knowledge_graph && (
                <div style={{ position: 'absolute', top: '12px', left: '12px', display: 'flex', gap: '16px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '8px 16px' }}>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: '18px', fontWeight: 800, color: '#111' }}>{graphData.nodes.length}</div><div style={{ fontSize: '9px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Nodes</div></div>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: '18px', fontWeight: 800, color: '#111' }}>{graphData.links.length}</div><div style={{ fontSize: '9px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Edges</div></div>
                  <div style={{ textAlign: 'center' }}><div style={{ fontSize: '18px', fontWeight: 800, color: '#111' }}>{entityTypes.length}</div><div style={{ fontSize: '9px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Types</div></div>
                </div>
              )}
            </>
          ) : loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              {/* Live simulation header */}
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Loader2 size={14} style={{ color: '#111', animation: 'spin 1s linear infinite' }} />
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#111' }}>Simulating</span>
                </div>
                <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#6b7280' }}>
                  <span>Round {simRound}</span>
                  <span>{simEvents.length} actions</span>
                </div>
              </div>
              {/* Live event stream */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '8px 16px' }}>
                {simEvents.map((evt, i) => (
                  <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #f3f4f6', fontSize: '12px' }}>
                    <span style={{ color: '#9ca3af', marginRight: '8px' }}>R{evt.round}</span>
                    <span style={{ fontWeight: 600, color: '#111' }}>{evt.agent}</span>
                    <span style={{ color: '#6b7280', marginLeft: '4px' }}>({evt.role})</span>
                    <div style={{ color: '#374151', marginTop: '2px', paddingLeft: '24px', lineHeight: 1.4 }}>{evt.content?.slice(0, 200)}</div>
                  </div>
                ))}
                {simEvents.length === 0 && <div style={{ color: '#d1d5db', textAlign: 'center', padding: '40px 0' }}>Generating personas...</div>}
              </div>
            </div>
          ) : (
            <div style={{ padding: '20px', overflowY: 'auto', height: '100%' }}>
              {predictions.map((p, i) => (
                <div key={i} onClick={() => loadPrediction(p)}
                  style={{ padding: '10px 12px', cursor: 'pointer', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between' }}
                  onMouseEnter={e => e.currentTarget.style.background = '#f9fafb'} onMouseLeave={e => e.currentTarget.style.background = ''}>
                  <div>
                    <div style={{ color: '#111', fontSize: '13px' }}>{p.goal}</div>
                    <div style={{ color: '#9ca3af', fontSize: '11px', marginTop: '2px' }}>{p.personas?.length || 0} personas · {p.rounds_completed || 0} rounds · {((p.strategy?.confidence_score || 0) * 100).toFixed(0)}%</div>
                  </div>
                  <span style={{ color: p.status === 'completed' ? '#22c55e' : '#f59e0b', fontSize: '11px', fontWeight: 600 }}>{p.status}</span>
                </div>
              ))}
              {predictions.length === 0 && <div style={{ color: '#d1d5db', textAlign: 'center', padding: '60px 0', fontSize: '14px' }}>Type a prediction goal and hit Predict</div>}
            </div>
          )}
        </div>

        {/* Right panel — node detail + chat */}
        {prediction && (
          <div style={{ width: '320px', borderLeft: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', background: '#fff', flexShrink: 0 }}>
            {/* Node detail */}
            {selectedNode ? (
              <div style={{ padding: '14px', borderBottom: '1px solid #e5e7eb', overflowY: 'auto', maxHeight: '40%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: '#111' }}>Node Details</span>
                  <span style={{ background: TYPE_COLORS[selectedNode.type || selectedNode.role] || TYPE_COLORS.default, color: '#fff', fontSize: '10px', fontWeight: 600, padding: '2px 8px', borderRadius: '10px' }}>
                    {selectedNode.type || selectedNode.role || 'Entity'}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: '#374151', lineHeight: 1.6 }}>
                  <div><span style={{ color: '#9ca3af' }}>Name:</span> {selectedNode.name}</div>
                  {selectedNode.personality && <div style={{ marginTop: '4px' }}><span style={{ color: '#9ca3af' }}>Personality:</span> {selectedNode.personality}</div>}
                  {selectedNode.strategy && <div style={{ marginTop: '4px' }}><span style={{ color: '#9ca3af' }}>Strategy:</span> {selectedNode.strategy}</div>}
                  {selectedNode.description && <div style={{ marginTop: '4px' }}><span style={{ color: '#9ca3af' }}>Summary:</span> {selectedNode.description}</div>}
                  {selectedNode.tools && <div style={{ marginTop: '4px' }}><span style={{ color: '#9ca3af' }}>Tools:</span> {selectedNode.tools.join(', ')}</div>}
                  {(selectedNode.revenue !== undefined) && (
                    <div style={{ display: 'flex', gap: '12px', marginTop: '6px', fontSize: '11px' }}>
                      <span style={{ color: '#22c55e' }}>+${(selectedNode.revenue || 0).toFixed(2)}</span>
                      <span style={{ color: '#ef4444' }}>-${(selectedNode.expenses || 0).toFixed(2)}</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{ padding: '14px', borderBottom: '1px solid #e5e7eb' }}>
                {strategy && (
                  <div style={{ fontSize: '12px', color: '#374151', lineHeight: 1.5 }}>
                    <div style={{ fontWeight: 600, marginBottom: '4px' }}>{strategy.summary}</div>
                    <div style={{ display: 'flex', gap: '8px', fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>
                      <span>{((strategy.confidence_score || 0) * 100).toFixed(0)}% confidence</span>
                      {cost && <><span>·</span><span>${cost.total_cost_per_hour}/h</span><span>·</span><span>{cost.hours_funded}h funded</span></>}
                    </div>
                    {strategy.risks && <div style={{ fontSize: '11px', color: '#ef4444', marginTop: '4px' }}>{strategy.risks.slice(0, 2).join(' · ')}</div>}
                  </div>
                )}
              </div>
            )}
            {/* Chat */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <div style={{ flex: 1, overflowY: 'auto', padding: '8px 14px' }}>
                {chatMessages.length === 0 && selectedNode && (
                  <div style={{ color: '#d1d5db', fontSize: '11px', textAlign: 'center', padding: '20px 0' }}>Ask {selectedNode.name} about their decisions or predictions</div>
                )}
                {chatMessages.map((m, i) => (
                  <div key={i} style={{ marginBottom: '10px' }}>
                    <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '2px' }}>{m.role === 'user' ? 'You' : selectedNode?.name || 'Agent'}</div>
                    <div style={{ fontSize: '12px', color: '#374151', lineHeight: 1.5 }}>{m.content}</div>
                  </div>
                ))}
                {chatLoading && <div style={{ color: '#d1d5db', fontSize: '11px' }}>Thinking...</div>}
              </div>
              <div style={{ padding: '8px 14px', borderTop: '1px solid #e5e7eb', display: 'flex', gap: '6px' }}>
                <input value={chatInput} onChange={e => setChatInput(e.target.value)} disabled={!selectedNode}
                  onKeyDown={e => e.key === 'Enter' && sendChat()} placeholder={selectedNode ? `Ask ${selectedNode.name?.split(' ')[0]}...` : 'Click a node to chat'}
                  style={{ flex: 1, background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px', color: '#111', padding: '7px 10px', fontSize: '12px' }} />
                <button onClick={sendChat} disabled={!selectedNode || chatLoading}
                  style={{ background: '#111', border: 'none', borderRadius: '6px', padding: '7px 12px', cursor: 'pointer' }}>
                  <Send size={13} style={{ color: '#fff' }} />
                </button>
              </div>
            </div>
            {/* Execution result */}
            {prediction.execution && (
              <div style={{ padding: '8px 14px', borderTop: '1px solid #e5e7eb', fontSize: '11px', color: '#22c55e', background: '#f0fdf4' }}>
                Deployed {prediction.execution.agents_created} agents in {prediction.execution.total_waves} waves
              </div>
            )}
          </div>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  );
}
