import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Send } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_COLORS = {
  running: '#22c55e', completed: '#3b82f6', stopped: '#6b7280',
  sleeping: '#f59e0b', error: '#ef4444', unknown: '#475569',
};

export default function Dimensions({ onSelectAgent }) {
  const [agents, setAgents] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const graphRef = useRef();

  const fetchData = useCallback(async () => {
    try {
      const [agentsRes, predsRes] = await Promise.all([
        fetch(`${API}/api/dimensions/live`),
        fetch(`${API}/api/ultimus/predictions`),
      ]);
      const agentsData = await agentsRes.json();
      const predsData = await predsRes.json();
      setAgents(agentsData.agents || []);
      setPredictions(predsData.predictions || []);
    } catch {}
  }, []);

  useEffect(() => { fetchData(); const iv = setInterval(fetchData, 8000); return () => clearInterval(iv); }, [fetchData]);

  // Build graph: agents as nodes, prediction links between agents from same prediction
  const graphData = useMemo(() => {
    const nodes = [];
    const links = [];
    const nodeIds = new Set();

    agents.forEach(a => {
      const id = a.agent_id;
      if (!nodeIds.has(id)) {
        nodes.push({ id, name: a.name || id, status: a.status || 'unknown',
          running: a.engine_running, actions: a.actions_count || 0,
          progress: a.goal_progress || 0, prediction_id: a.prediction_id, data: a });
        nodeIds.add(id);
      }
    });

    // Add persona nodes from predictions
    predictions.forEach(p => {
      (p.personas || []).forEach(persona => {
        const id = `sim:${persona.name}`;
        if (!nodeIds.has(id)) {
          nodes.push({ id, name: persona.name, status: 'simulated', running: false,
            actions: persona.actions_count || 0, progress: 0, prediction_id: p.id,
            data: { ...persona, agent_id: id, is_simulated: true } });
          nodeIds.add(id);
        }
      });
      // Link personas from the same prediction
      const pPersonas = (p.personas || []).map(ps => `sim:${ps.name}`);
      for (let i = 0; i < pPersonas.length; i++) {
        for (let j = i + 1; j < pPersonas.length; j++) {
          if (nodeIds.has(pPersonas[i]) && nodeIds.has(pPersonas[j])) {
            links.push({ source: pPersonas[i], target: pPersonas[j] });
          }
        }
      }
    });

    return { nodes, links };
  }, [agents, predictions]);

  const handleNodeClick = (node) => {
    setSelectedNode(node.data);
    setChatMessages([]);
    if (onSelectAgent && node.data.agent_id && !node.data.is_simulated) {
      onSelectAgent(node.data.agent_id);
    }
  };

  const sendChat = async () => {
    if (!chatInput.trim() || !selectedNode) return;
    setChatMessages(prev => [...prev, { role: 'user', content: chatInput }]);
    const msg = chatInput; setChatInput(''); setChatLoading(true);
    try {
      const body = selectedNode.is_simulated
        ? { prediction_id: selectedNode.prediction_id || predictions[0]?.id || '', persona_name: selectedNode.name, message: msg, mode: 'simulation' }
        : { agent_id: selectedNode.agent_id, message: msg, mode: 'live' };
      const r = await fetch(`${API}/api/dimensions/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const d = await r.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: d.response || d.detail || 'No response' }]);
    } catch (e) { setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + e.message }]); }
    setChatLoading(false);
  };

  return (
    <div data-testid="dimensions-page" style={{ height: 'calc(100vh - 0px)', display: 'flex', background: '#fff' }}>
      {/* Graph fills the screen */}
      <div style={{ flex: 1, position: 'relative' }}>
        <ForceGraph2D ref={graphRef} graphData={graphData}
          nodeLabel={n => `${n.name} (${n.status})`}
          nodeColor={n => {
            if (selectedNode && (selectedNode.agent_id === n.id || selectedNode.name === n.name)) return '#111';
            return STATUS_COLORS[n.status] || STATUS_COLORS.unknown;
          }}
          nodeVal={n => 4 + (n.actions || 0) * 0.5}
          nodeCanvasObjectMode={() => 'after'}
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = (node.name || '').length > 18 ? node.name.slice(0, 16) + '..' : node.name;
            const fontSize = Math.max(10 / globalScale, 3);
            const isSel = selectedNode && (selectedNode.agent_id === node.id || selectedNode.name === node.name);
            ctx.font = `${isSel ? 'bold ' : ''}${fontSize}px sans-serif`;
            ctx.textAlign = 'center';
            ctx.fillStyle = isSel ? '#111' : '#9ca3af';
            ctx.fillText(label, node.x, node.y + (node.val || 4) / globalScale + fontSize + 2);
            // Running indicator pulse
            if (node.running) {
              ctx.beginPath(); ctx.arc(node.x, node.y, (node.val || 4) / globalScale + 4, 0, Math.PI * 2);
              ctx.strokeStyle = 'rgba(34,197,94,0.3)'; ctx.lineWidth = 2; ctx.stroke();
            }
          }}
          linkColor={() => '#e5e7eb'}
          linkWidth={0.5}
          onNodeClick={handleNodeClick}
          cooldownTicks={80}
          enableZoomInteraction={true}
          enablePanInteraction={true}
        />

        {/* Stats overlay */}
        <div style={{ position: 'absolute', top: '12px', left: '12px', display: 'flex', gap: '16px', background: 'rgba(255,255,255,0.9)', borderRadius: '6px', padding: '8px 14px', border: '1px solid #e5e7eb' }}>
          <div style={{ textAlign: 'center' }}><div style={{ fontSize: '18px', fontWeight: 800 }}>{agents.length}</div><div style={{ fontSize: '9px', color: '#9ca3af', textTransform: 'uppercase' }}>Live</div></div>
          <div style={{ textAlign: 'center' }}><div style={{ fontSize: '18px', fontWeight: 800 }}>{graphData.nodes.length - agents.length}</div><div style={{ fontSize: '9px', color: '#9ca3af', textTransform: 'uppercase' }}>Simulated</div></div>
          <div style={{ textAlign: 'center' }}><div style={{ fontSize: '18px', fontWeight: 800 }}>{graphData.links.length}</div><div style={{ fontSize: '9px', color: '#9ca3af', textTransform: 'uppercase' }}>Links</div></div>
        </div>

        {/* Legend */}
        <div style={{ position: 'absolute', bottom: '12px', left: '12px', display: 'flex', gap: '12px', fontSize: '10px', color: '#6b7280', background: 'rgba(255,255,255,0.9)', padding: '6px 12px', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
          {Object.entries(STATUS_COLORS).map(([s, c]) => (
            <span key={s} style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: c, display: 'inline-block' }} />{s}
            </span>
          ))}
        </div>

        {/* Fit button */}
        <button onClick={() => graphRef.current?.zoomToFit(400)}
          style={{ position: 'absolute', top: '12px', right: '12px', background: '#fff', border: '1px solid #e5e7eb', borderRadius: '6px', padding: '6px 12px', fontSize: '11px', color: '#6b7280', cursor: 'pointer' }}>
          Fit
        </button>
      </div>

      {/* Right panel — selected node detail + chat (only when node selected) */}
      {selectedNode && (
        <div style={{ width: '300px', borderLeft: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
          {/* Node info */}
          <div style={{ padding: '14px', borderBottom: '1px solid #e5e7eb' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '14px', fontWeight: 700 }}>{selectedNode.name || selectedNode.agent_id}</span>
              <button onClick={() => setSelectedNode(null)} style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: '14px' }}>x</button>
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280', lineHeight: 1.6 }}>
              <div><span style={{ color: '#9ca3af' }}>Status:</span> <span style={{ color: STATUS_COLORS[selectedNode.status] || '#6b7280', fontWeight: 600 }}>{selectedNode.status || 'unknown'}</span></div>
              {selectedNode.role && <div><span style={{ color: '#9ca3af' }}>Role:</span> {selectedNode.role}</div>}
              {selectedNode.personality && <div style={{ marginTop: '4px' }}>{selectedNode.personality}</div>}
              {selectedNode.strategy && <div style={{ marginTop: '4px', color: '#374151' }}>{selectedNode.strategy}</div>}
              <div style={{ marginTop: '4px' }}><span style={{ color: '#9ca3af' }}>Actions:</span> {selectedNode.actions_count || 0}</div>
              {selectedNode.goal_progress > 0 && <div><span style={{ color: '#9ca3af' }}>Progress:</span> {(selectedNode.goal_progress * 100).toFixed(0)}%</div>}
            </div>
          </div>
          {/* Chat */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '8px 14px' }}>
            {chatMessages.length === 0 && <div style={{ color: '#d1d5db', fontSize: '11px', textAlign: 'center', padding: '20px 0' }}>Ask about decisions, state, or predictions</div>}
            {chatMessages.map((m, i) => (
              <div key={i} style={{ marginBottom: '10px' }}>
                <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '2px' }}>{m.role === 'user' ? 'You' : selectedNode.name || 'Agent'}</div>
                <div style={{ fontSize: '12px', color: '#374151', lineHeight: 1.5 }}>{m.content}</div>
              </div>
            ))}
            {chatLoading && <div style={{ color: '#d1d5db', fontSize: '11px' }}>Thinking...</div>}
          </div>
          <div style={{ padding: '8px 14px', borderTop: '1px solid #e5e7eb', display: 'flex', gap: '6px' }}>
            <input value={chatInput} onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendChat()} placeholder="Ask..."
              style={{ flex: 1, background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '6px', color: '#111', padding: '7px 10px', fontSize: '12px' }} />
            <button onClick={sendChat} disabled={chatLoading}
              style={{ background: '#111', border: 'none', borderRadius: '6px', padding: '7px 12px', cursor: 'pointer' }}>
              <Send size={13} style={{ color: '#fff' }} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
