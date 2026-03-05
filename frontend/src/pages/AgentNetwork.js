import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ReactFlow, { 
  Background, Controls, MiniMap, 
  useNodesState, useEdgesState 
} from 'reactflow';
import 'reactflow/dist/style.css';
import { CircleDot, Shield, Cpu, Zap } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const tierColors = {
  high: '#16a34a',
  normal: '#2563eb',
  low_compute: '#d97706',
  critical: '#ef4444',
  dead: '#71717a',
};

const statusIcons = {
  alive: CircleDot,
  sleeping: Cpu,
};

function AgentNode({ data }) {
  const StatusIcon = statusIcons[data.status] || CircleDot;
  const borderColor = tierColors[data.survival_tier] || '#e4e4e7';

  return (
    <div 
      data-testid={`agent-node-${data.label}`}
      className="bg-white border-2 rounded-sm px-4 py-3 min-w-[180px] shadow-sm hover:shadow-md transition-shadow"
      style={{ borderColor }}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <StatusIcon className="w-3 h-3" style={{ color: borderColor }} />
        <span className="text-xs font-heading font-semibold text-foreground truncate">{data.label}</span>
      </div>
      <div className="text-[10px] text-muted-foreground font-medium">{data.role}</div>
      <div className="text-[10px] text-muted-foreground mt-0.5">{data.department}</div>
      <div className="flex items-center gap-3 mt-2 pt-2 border-t border-border">
        <div className="flex items-center gap-1">
          <Zap className="w-2.5 h-2.5 text-chart-primary" />
          <span className="text-[9px] font-mono text-muted-foreground">${data.credits?.toFixed(0)}</span>
        </div>
        <div className="flex items-center gap-1">
          <Shield className="w-2.5 h-2.5 text-muted-foreground" />
          <span className="text-[9px] font-mono text-muted-foreground">{(data.soul_alignment * 100).toFixed(0)}%</span>
        </div>
        <span className="text-[9px] font-mono text-muted-foreground">{data.turns} turns</span>
      </div>
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

export default function AgentNetwork() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchHierarchy = useCallback(async () => {
    try {
      const [hierRes, agentsRes] = await Promise.all([
        fetch(`${API}/api/agents/hierarchy/tree`),
        fetch(`${API}/api/agents`),
      ]);
      const [hier, agData] = await Promise.all([hierRes.json(), agentsRes.json()]);
      setAgents(agData.agents || []);
      
      // Layout nodes in a tree structure
      const nodeMap = {};
      hier.nodes.forEach(n => { nodeMap[n.id] = { ...n, children: [] }; });
      hier.edges.forEach(e => {
        if (nodeMap[e.source]) nodeMap[e.source].children.push(e.target);
      });

      // Find root (no incoming edges)
      const targets = new Set(hier.edges.map(e => e.target));
      const roots = hier.nodes.filter(n => !targets.has(n.id));
      
      // BFS layout
      const layoutNodes = [];
      const queue = roots.map((r, i) => ({ id: r.id, depth: 0, index: i }));
      const depthCounts = {};
      const visited = new Set();

      while (queue.length > 0) {
        const { id, depth, index } = queue.shift();
        if (visited.has(id)) continue;
        visited.add(id);
        
        if (!depthCounts[depth]) depthCounts[depth] = 0;
        const xIndex = depthCounts[depth]++;
        
        const node = nodeMap[id];
        if (node) {
          layoutNodes.push({
            ...node,
            position: { x: xIndex * 220, y: depth * 140 },
          });
          (node.children || []).forEach((childId, ci) => {
            queue.push({ id: childId, depth: depth + 1, index: ci });
          });
        }
      }

      setNodes(layoutNodes);
      setEdges(hier.edges || []);
    } catch (e) {
      console.error('Failed to fetch hierarchy:', e);
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => { fetchHierarchy(); }, [fetchHierarchy]);

  const onNodeClick = useCallback((_, node) => {
    const agent = agents.find(a => a.wallet_address === node.id);
    setSelectedAgent(agent || node.data);
  }, [agents]);

  if (loading) {
    return (
      <div data-testid="agents-loading" className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
          <span className="text-sm text-muted-foreground">Loading agent network...</span>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="agent-network-page" className="h-[calc(100vh-8rem)] flex gap-4 animate-slide-in">
      {/* Network Canvas */}
      <div className="flex-1 bg-white border border-border rounded-sm overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.2}
          maxZoom={2}
          defaultEdgeOptions={{ type: 'smoothstep' }}
        >
          <Background color="#e4e4e7" gap={20} size={1} />
          <Controls className="!bg-white !border-border !rounded-sm !shadow-none" />
          <MiniMap 
            nodeColor={(n) => tierColors[n.data?.survival_tier] || '#e4e4e7'}
            className="!bg-white !border-border !rounded-sm"
          />
        </ReactFlow>
      </div>

      {/* Agent Detail Sidebar */}
      <div className="w-72 bg-white border border-border rounded-sm p-5 overflow-y-auto flex-shrink-0">
        {selectedAgent ? (
          <div data-testid="agent-detail" className="space-y-4">
            <div>
              <h3 className="text-sm font-heading font-semibold text-foreground">{selectedAgent.name}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">{selectedAgent.role}</p>
              <p className="text-xs text-muted-foreground">{selectedAgent.department}</p>
            </div>
            <div className="space-y-2">
              <DetailRow label="Status" value={selectedAgent.status} />
              <DetailRow label="Survival Tier" value={selectedAgent.survival_tier} />
              <DetailRow label="Credits" value={`$${selectedAgent.credits_balance?.toFixed(2) || '0'}`} />
              <DetailRow label="USDC" value={`$${selectedAgent.usdc_balance?.toLocaleString() || '0'}`} />
              <DetailRow label="Turns" value={selectedAgent.turns_completed?.toLocaleString() || '0'} />
              <DetailRow label="Tools Used" value={selectedAgent.tools_used || '0'} />
              <DetailRow label="Children" value={selectedAgent.children_count || '0'} />
              <DetailRow label="Soul Alignment" value={`${((selectedAgent.soul_alignment || 0) * 100).toFixed(0)}%`} />
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Wallet</span>
              <p className="text-xs font-mono text-foreground mt-1 break-all">{selectedAgent.wallet_address || 'N/A'}</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <CircleDot className="w-8 h-8 text-border mb-3" />
            <p className="text-sm text-muted-foreground">Select an agent node to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}

function DetailRow({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</span>
      <span className="text-xs font-mono font-medium text-foreground">{value}</span>
    </div>
  );
}
