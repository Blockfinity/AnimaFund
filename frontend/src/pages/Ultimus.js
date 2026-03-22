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
  const [liveFeed, setLiveFeed] = useState([]);
  const [estimate, setEstimate] = useState(null);
  const [showWallet, setShowWallet] = useState(false);
  const [expandedPrediction, setExpandedPrediction] = useState(null);
  const graphRef = useRef();

  const fetchData = useCallback(async () => {
    try {
      const [pRes, aRes] = await Promise.all([
        fetch(`${API}/api/ultimus/predictions`), fetch(`${API}/api/dimensions/live`)
      ]);
      setPredictions((await pRes.json()).predictions || []);
      const liveData = await aRes.json();
      setAgents(liveData.agents || []);
      // Fetch recent actions from all live agents for the live feed
      const newActions = [];
      for (const a of (liveData.agents || []).slice(0, 10)) {
        try {
          const stateRes = await fetch(`${API}/api/webhook/agent/${a.agent_id}`);
          const state = await stateRes.json();
          (state.actions || []).slice(-3).forEach(act => {
            newActions.push({ ...act, agent_id: a.agent_id, agent_name: a.name || a.agent_id });
          });
        } catch {}
      }
      newActions.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
      setLiveFeed(newActions.slice(0, 20));
    } catch {}
  }, []);
  useEffect(() => { fetchData(); const iv = setInterval(fetchData, 6000); return () => clearInterval(iv); }, [fetchData]);

  // Run prediction with SSE
  const runPrediction = async () => {
    if (!goal.trim()) return;
    setLoading(true); setPrediction(null); setSelectedNode(null); setSimEvents([]); setSimRound(0); setTab('graph'); setEstimate(null);
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

  const clearSimulation = () => {
    setPrediction(null); setSelectedNode(null); setSimEvents([]); setSimRound(0);
    setChatMessages([]); setEstimate(null); setShowWallet(false);
  };

  const getEstimate = async () => {
    if (!goal.trim()) return;
    try {
      const r = await fetch(`${API}/api/ultimus/estimate`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, mode: 'quick' }) });
      const d = await r.json();
      if (!d.detail) setEstimate(d);
    } catch {}
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
        {goal.trim() && !loading && !prediction && (
          <button onClick={getEstimate} style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '7px 12px', fontSize: '12px', color: '#6b7280', cursor: 'pointer' }}>
            Estimate
          </button>
        )}
        {prediction && (
          <button onClick={clearSimulation} style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '7px 12px', fontSize: '12px', color: '#ef4444', cursor: 'pointer' }}>
            Clear
          </button>
        )}
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
                  nodeLabel={n => `${n.name} (${n.role})${n.isLive ? ' [LIVE]' : ''}`}
                  nodeColor={n => {
                    if (selectedNode && selectedNode.name === n.name) return '#111';
                    if (n.isLive) {
                      const s = (n.data?.status || '').toLowerCase();
                      if (s === 'running' || s === 'executing') return '#22c55e';
                      if (s === 'completed') return '#3b82f6';
                      if (s === 'error') return '#ef4444';
                      return '#10b981';
                    }
                    return getNodeColor(n);
                  }}
                  nodeVal={n => {
                    if (n.isLive) return 8 + Math.min((n.actions || 0) * 0.5, 20);
                    return 3 + Math.min((n.actions || 0) * 0.3, 15);
                  }}
                  nodeCanvasObjectMode={() => 'after'}
                  nodeCanvasObject={(node, ctx, gs) => {
                    const fontSize = Math.max(9 / gs, 2.5);
                    const isSel = selectedNode && selectedNode.name === node.name;
                    const nodeR = (node.val || 3) / gs;

                    // Live agent: pulsing outer ring
                    if (node.isLive) {
                      const pulse = 0.5 + 0.5 * Math.sin(Date.now() / 500 + node.x);
                      ctx.beginPath();
                      ctx.arc(node.x, node.y, nodeR + 3 / gs, 0, Math.PI * 2);
                      ctx.strokeStyle = `rgba(16, 185, 129, ${0.2 + pulse * 0.3})`;
                      ctx.lineWidth = 2 / gs;
                      ctx.stroke();
                      // Status dot
                      ctx.beginPath();
                      ctx.arc(node.x + nodeR * 0.7, node.y - nodeR * 0.7, 2 / gs, 0, Math.PI * 2);
                      const s = (node.data?.status || '').toLowerCase();
                      ctx.fillStyle = s === 'running' ? '#22c55e' : s === 'error' ? '#ef4444' : '#6b7280';
                      ctx.fill();
                    }

                    // Label
                    ctx.font = `${isSel ? 'bold ' : ''}${fontSize}px sans-serif`;
                    ctx.textAlign = 'center';
                    ctx.fillStyle = isSel ? '#111' : node.isLive ? '#111' : '#6b7280';
                    const label = (node.name || '').length > 20 ? node.name.slice(0, 18) + '..' : node.name;
                    ctx.fillText(label, node.x, node.y + nodeR + fontSize + 1);
                  }}
                  linkColor={l => {
                    const lbl = (l.label || '').toLowerCase();
                    if (lbl.includes('agree')) return 'rgba(34, 197, 94, 0.4)';
                    if (lbl.includes('disagree')) return 'rgba(239, 68, 68, 0.4)';
                    return '#e5e7eb';
                  }}
                  linkWidth={l => {
                    const lbl = (l.label || '').toLowerCase();
                    return (lbl.includes('agree') || lbl.includes('disagree')) ? 1.5 : 0.5;
                  }}
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

              {/* Live Feed — streaming actions from deployed agents */}
              {liveFeed.length > 0 && (
                <div style={{ position: 'absolute', bottom: '12px', right: '12px', background: 'rgba(255,255,255,0.95)', border: '1px solid #e5e7eb', borderRadius: '8px', width: '340px', maxHeight: '200px', overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                  <div style={{ padding: '8px 12px', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: '#22c55e', textTransform: 'uppercase', letterSpacing: '1px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#22c55e', display: 'inline-block', animation: 'pulse 2s infinite' }} />
                      Live Feed
                    </span>
                    <span style={{ fontSize: '10px', color: '#9ca3af' }}>{agents.filter(a => a.engine_running).length} active</span>
                  </div>
                  <div style={{ overflowY: 'auto', maxHeight: '160px', padding: '4px 0' }}>
                    {liveFeed.map((act, i) => (
                      <div key={i} style={{ padding: '4px 12px', fontSize: '11px', borderBottom: '1px solid #fafafa' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ fontWeight: 600, color: '#111' }}>{act.agent_name}</span>
                          <span style={{ color: '#d1d5db', fontSize: '9px' }}>{(act.timestamp || '').slice(11, 19)}</span>
                        </div>
                        <div style={{ color: '#6b7280', marginTop: '1px' }}>
                          {act.tool_name && <span style={{ color: '#9ca3af', marginRight: '4px', fontFamily: 'monospace', fontSize: '10px' }}>{act.tool_name}</span>}
                          {(act.action || '').slice(0, 80)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Node Details card overlay */}
              {selectedNode && (
                <div style={{ position: 'absolute', top: '12px', left: '12px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '16px', width: '340px', maxHeight: '70vh', overflowY: 'auto', boxShadow: '0 4px 16px rgba(0,0,0,0.08)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span style={{ fontSize: '15px', fontWeight: 700 }}>Node Details</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{ background: getNodeColor({ role: selectedNode.role || selectedNode.type }), color: '#fff', fontSize: '10px', fontWeight: 600, padding: '2px 10px', borderRadius: '12px' }}>{selectedNode.role || selectedNode.type || 'Agent'}</span>
                      {selectedNode.agent_id && <button onClick={() => setShowWallet(!showWallet)} style={{ background: showWallet ? '#111' : '#f9fafb', color: showWallet ? '#fff' : '#6b7280', border: '1px solid #e5e7eb', borderRadius: '4px', padding: '2px 8px', fontSize: '10px', cursor: 'pointer' }}>Wallet</button>}
                      <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: '16px' }}>x</button>
                    </div>
                  </div>

                  {/* Wallet view */}
                  {showWallet && selectedNode.agent_id && (
                    <div style={{ background: '#f9fafb', borderRadius: '6px', padding: '12px', marginBottom: '10px', textAlign: 'center' }}>
                      <img src={`https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(selectedNode.wallet_address || selectedNode.agent_id)}`} alt="QR" style={{ width: '120px', height: '120px', borderRadius: '4px' }} />
                      <div style={{ fontSize: '10px', fontFamily: 'monospace', marginTop: '6px', color: '#374151', wordBreak: 'break-all' }}>{selectedNode.wallet_address || 'No wallet assigned'}</div>
                      {selectedNode.financials && (
                        <div style={{ marginTop: '6px', fontSize: '12px' }}>
                          <span style={{ color: '#22c55e', fontWeight: 700 }}>${(selectedNode.financials.usdc_balance || 0).toFixed(2)} USDC</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Agent details */}
                  {!showWallet && (
                    <div style={{ fontSize: '12px', color: '#374151', lineHeight: 1.8 }}>
                      <div><span style={{ color: '#9ca3af' }}>Name:</span> {selectedNode.name || selectedNode.agent_id}</div>
                      {selectedNode.agent_id && <div><span style={{ color: '#9ca3af' }}>ID:</span> <span style={{ fontFamily: 'monospace', fontSize: '10px' }}>{selectedNode.agent_id}</span></div>}
                      {selectedNode.status && <div><span style={{ color: '#9ca3af' }}>Status:</span> <span style={{ color: selectedNode.status === 'running' ? '#22c55e' : '#6b7280', fontWeight: 600 }}>{selectedNode.status}</span></div>}
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
                  )}

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

              {/* Estimate overlay */}
              {estimate && !prediction && !loading && (
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '20px', width: '360px', boxShadow: '0 8px 24px rgba(0,0,0,0.1)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <span style={{ fontSize: '14px', fontWeight: 700 }}>Prediction Estimate</span>
                    <button onClick={() => setEstimate(null)} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>x</button>
                  </div>
                  <div style={{ fontSize: '12px', color: '#374151', lineHeight: 2 }}>
                    <div><span style={{ color: '#9ca3af' }}>Complexity:</span> <span style={{ fontWeight: 600 }}>{estimate.complexity}</span></div>
                    <div><span style={{ color: '#9ca3af' }}>Personas:</span> {estimate.recommended_personas}</div>
                    <div><span style={{ color: '#9ca3af' }}>Rounds:</span> {estimate.recommended_rounds}</div>
                    <div><span style={{ color: '#9ca3af' }}>LLM calls:</span> {estimate.simulation?.llm_calls}</div>
                    <div><span style={{ color: '#9ca3af' }}>Est. cost:</span> ${estimate.simulation?.estimated_cost?.toFixed(4)}</div>
                    <div><span style={{ color: '#9ca3af' }}>Est. time:</span> ~{Math.ceil(estimate.simulation?.estimated_minutes || 0)} min</div>
                    {estimate.persona_types?.length > 0 && (
                      <div style={{ marginTop: '6px' }}><span style={{ color: '#9ca3af' }}>Persona types:</span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                          {estimate.persona_types.map((t, i) => <span key={i} style={{ background: '#f3f4f6', borderRadius: '4px', padding: '2px 8px', fontSize: '10px' }}>{t}</span>)}
                        </div>
                      </div>
                    )}
                  </div>
                  <div style={{ marginTop: '12px', fontSize: '11px', color: '#6b7280' }}>{estimate.reasoning}</div>
                  <button onClick={runPrediction} style={{ marginTop: '12px', width: '100%', background: '#111', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}>
                    Run Simulation ({estimate.recommended_personas} personas, {estimate.recommended_rounds} rounds)
                  </button>
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
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
            {predictions.map((p, i) => {
              const isExpanded = expandedPrediction === p.id;
              return (
                <div key={i} style={{ border: '1px solid #e5e7eb', borderRadius: '8px', marginBottom: '12px', overflow: 'hidden' }}>
                  {/* Header — always visible */}
                  <div onClick={() => setExpandedPrediction(isExpanded ? null : p.id)}
                    style={{ padding: '16px 20px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: isExpanded ? '#f9fafb' : '#fff' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: '#111' }}>{p.goal}</div>
                      <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>
                        {p.personas?.length || 0} personas · {p.num_rounds || 0} rounds · {p.mode || 'quick'}
                        {p.strategy && <span> · {((p.strategy.confidence_score || 0) * 100).toFixed(0)}% confidence</span>}
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ background: p.status === 'completed' ? '#dcfce7' : p.status === 'executing' ? '#dbeafe' : '#fef3c7',
                        color: p.status === 'completed' ? '#166534' : p.status === 'executing' ? '#1e40af' : '#92400e',
                        fontSize: '10px', fontWeight: 600, padding: '2px 10px', borderRadius: '12px', textTransform: 'uppercase' }}>{p.status}</span>
                      <ChevronDown size={14} style={{ color: '#9ca3af', transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
                    </div>
                  </div>

                  {/* Expanded details */}
                  {isExpanded && (
                    <div style={{ padding: '0 20px 20px', borderTop: '1px solid #f3f4f6' }}>
                      {/* Strategy */}
                      {p.strategy && (
                        <div style={{ padding: '12px 0', borderBottom: '1px solid #f3f4f6' }}>
                          <div style={{ fontSize: '11px', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Strategy</div>
                          <div style={{ fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>{p.strategy.summary}</div>
                          {p.strategy.key_actions && (
                            <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                              {p.strategy.key_actions.map((a, j) => <span key={j} style={{ background: '#f3f4f6', borderRadius: '4px', padding: '2px 8px', fontSize: '10px', color: '#374151' }}>{typeof a === 'string' ? a : JSON.stringify(a)}</span>)}
                            </div>
                          )}
                          {p.strategy.risks && <div style={{ marginTop: '6px', fontSize: '11px', color: '#ef4444' }}>Risks: {p.strategy.risks.join(' · ')}</div>}
                          {p.strategy.coalitions_formed && <div style={{ marginTop: '4px', fontSize: '11px', color: '#3b82f6' }}>Coalitions: {p.strategy.coalitions_formed.join(' · ')}</div>}
                        </div>
                      )}

                      {/* Cost model */}
                      {p.cost_model && (
                        <div style={{ padding: '12px 0', borderBottom: '1px solid #f3f4f6', display: 'flex', gap: '20px', fontSize: '12px' }}>
                          <span><span style={{ color: '#9ca3af' }}>Cost/h:</span> ${p.cost_model.total_cost_per_hour || p.cost_model.estimated_cost || 0}</span>
                          <span><span style={{ color: '#9ca3af' }}>Funded:</span> {p.cost_model.hours_funded || '—'}h</span>
                          <span style={{ color: p.cost_model.self_sustaining ? '#22c55e' : '#ef4444' }}>{p.cost_model.self_sustaining ? 'Self-sustaining' : 'Burns out'}</span>
                        </div>
                      )}

                      {/* Personas */}
                      <div style={{ padding: '12px 0', borderBottom: '1px solid #f3f4f6' }}>
                        <div style={{ fontSize: '11px', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
                          Personas ({(p.personas || []).length})
                        </div>
                        {(p.personas || []).map((ps, j) => (
                          <div key={j} style={{ padding: '8px', borderRadius: '6px', marginBottom: '4px', background: '#fafafa' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span style={{ fontWeight: 600, fontSize: '12px' }}>{ps.name}</span>
                              <span style={{ fontSize: '10px', color: '#6b7280', background: '#e5e7eb', padding: '1px 8px', borderRadius: '8px' }}>{ps.role}</span>
                            </div>
                            {ps.personality && <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>{ps.personality}</div>}
                            {ps.strategy && <div style={{ fontSize: '11px', color: '#374151', marginTop: '2px' }}><span style={{ color: '#9ca3af' }}>Strategy:</span> {ps.strategy}</div>}
                            {ps.risk_tolerance && <div style={{ fontSize: '10px', color: '#9ca3af', marginTop: '2px' }}>Risk: {ps.risk_tolerance}</div>}
                          </div>
                        ))}
                      </div>

                      {/* Round summaries */}
                      {p.round_summaries && p.round_summaries.length > 0 && (
                        <div style={{ padding: '12px 0', borderBottom: '1px solid #f3f4f6' }}>
                          <div style={{ fontSize: '11px', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
                            Simulation Rounds ({p.round_summaries.length})
                          </div>
                          {p.round_summaries.map((rs, j) => (
                            <div key={j} style={{ marginBottom: '8px' }}>
                              <div style={{ fontSize: '11px', fontWeight: 600, color: '#111', marginBottom: '4px' }}>Round {rs.round} ({rs.events} actions)</div>
                              {Object.entries(rs.positions || {}).map(([agent, pos], k) => (
                                <div key={k} style={{ fontSize: '11px', color: '#6b7280', paddingLeft: '8px', marginBottom: '2px' }}>
                                  <span style={{ fontWeight: 500, color: '#374151' }}>{agent}:</span> {pos.slice(0, 120)}
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Relationships */}
                      {p.relationships && p.relationships.length > 0 && (
                        <div style={{ padding: '12px 0', borderBottom: '1px solid #f3f4f6' }}>
                          <div style={{ fontSize: '11px', fontWeight: 700, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
                            Relationships ({p.relationships.length})
                          </div>
                          {p.relationships.map((r, j) => (
                            <div key={j} style={{ fontSize: '11px', display: 'flex', gap: '4px', alignItems: 'center', marginBottom: '2px' }}>
                              <span style={{ color: '#374151' }}>{r.from}</span>
                              <span style={{ color: r.type.includes('agree') ? '#22c55e' : r.type.includes('disagree') ? '#ef4444' : '#9ca3af', fontSize: '10px', fontFamily: 'monospace' }}>{r.type}</span>
                              <span style={{ color: '#374151' }}>{r.to}</span>
                              <span style={{ color: '#d1d5db', fontSize: '9px' }}>R{r.round}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Execution results */}
                      {p.execution && (
                        <div style={{ padding: '12px 0' }}>
                          <div style={{ fontSize: '11px', fontWeight: 700, color: '#22c55e', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
                            Deployed Agents ({p.execution.agents_created})
                          </div>
                          {(p.execution.agents || []).map((a, j) => (
                            <div key={j} style={{ fontSize: '11px', display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #fafafa' }}>
                              <span style={{ color: '#374151' }}>{a.name}</span>
                              <span style={{ color: '#9ca3af', fontFamily: 'monospace', fontSize: '10px' }}>{a.agent_id}</span>
                              <span style={{ color: a.status === 'running' ? '#22c55e' : '#6b7280', fontSize: '10px' }}>{a.status}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Actions — view on graph */}
                      <button onClick={() => { setPrediction(p); setTab('graph'); }}
                        style={{ marginTop: '8px', width: '100%', background: '#111', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
                        View on Graph
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
            {!predictions.length && <div style={{ color: '#d1d5db', textAlign: 'center', padding: '60px 0' }}>No predictions yet</div>}
          </div>
        )}
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg) } } @keyframes pulse { 0%,100% { opacity: 0.4 } 50% { opacity: 1 } }`}</style>
    </div>
  );
}
