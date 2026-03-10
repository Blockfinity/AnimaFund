import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Toaster, toast } from 'sonner';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import CreateAgentModal from './components/CreateAgentModal';
import AgentMind from './pages/AgentMind';
import FundHQ from './pages/FundHQ';
import Agents from './pages/Agents';
import DealFlow from './pages/DealFlow';
import Portfolio from './pages/Portfolio';
import Financials from './pages/Financials';
import Activity from './pages/Activity';
import Memory from './pages/Memory';
import Configuration from './pages/Configuration';
import Skills from './pages/Skills';
import Infrastructure from './pages/Infrastructure';
import AnimaVM from './pages/AnimaVM';
import { SSEProvider, useSSE, useSSETrigger } from './hooks/useSSE';

const API = process.env.REACT_APP_BACKEND_URL;

function AppInner() {
  const [view, setView] = useState('loading');
  const [genesisState, setGenesisState] = useState(null);
  const [engineStarted, setEngineStarted] = useState(false);
  const [currentPage, setCurrentPage] = useState('animavm');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [identity, setIdentity] = useState(null);
  const [engineState, setEngineState] = useState(null);

  // Multi-agent state
  const [agentList, setAgentList] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('anima-fund');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Fetch agent list
  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/agents`);
      const data = await res.json();
      setAgentList(data.agents || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchAgents(); }, [fetchAgents]);

  const handleSelectAgent = async (agentId) => {
    try {
      const res = await fetch(`${API}/api/agents/${agentId}/select`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || `Failed to switch to agent: ${res.status}`);
        // Re-fetch agent list in case the agent was deleted
        fetchAgents();
        return;
      }
      const data = await res.json();
      if (data.success) {
        setSelectedAgent(agentId);
        // Reset ALL agent-specific state before re-fetching
        setGenesisState(null);
        setIdentity(null);
        setEngineState(null);
        setEngineStarted(false);
        // Force view back to loading so checkStatus can determine the correct view
        setView('loading');
        toast.success(`Switched to ${data.active_agent || agentId}`);
      }
    } catch (e) { toast.error(e.message); }
  };

  const handleAgentCreated = async (agent) => {
    // Re-fetch the full agent list from backend to ensure consistency
    await fetchAgents();
    setShowCreateModal(false);
    toast.success(`Agent "${agent.name}" created — provision it in Anima VM`);
    // Auto-select the new agent and navigate to AnimaVM for provisioning
    await handleSelectAgent(agent.agent_id);
    setCurrentPage('animavm');
  };

  // Use a ref for view to avoid re-creating checkStatus when view changes
  const viewRef = useRef(view);
  useEffect(() => { viewRef.current = view; }, [view]);

  const checkStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/genesis/status`);
      if (!res.ok) return;
      const data = await res.json();

      // Only update state if data actually changed — prevents unnecessary re-renders
      setGenesisState(prev => {
        if (prev && prev.wallet_address && !data.wallet_address) {
          return prev; // Never lose wallet data
        }
        // Skip update if nothing meaningful changed
        if (prev && prev.wallet_address === data.wallet_address &&
            prev.engine_live === data.engine_live &&
            prev.engine_running === data.engine_running &&
            prev.status === data.status &&
            prev.turn_count === data.turn_count) {
          return prev;
        }
        return data;
      });

      if (data.engine_running || data.wallet_address || data.config_exists) {
        setEngineStarted(true);
      }

      if (data.engine_running || data.engine_live || data.wallet_address || data.config_exists) {
        try {
          const [idRes, engRes] = await Promise.all([
            fetch(`${API}/api/live/identity`),
            fetch(`${API}/api/engine/live`),
          ]);
          if (idRes.ok) {
            const idData = await idRes.json();
            if (idData && (idData.name || idData.address)) {
              setIdentity(prev => {
                if (prev && prev.name === idData.name && prev.address === idData.address) return prev;
                return idData;
              });
            }
          }
          if (engRes.ok) {
            const engData = await engRes.json();
            setEngineState(prev => {
              if (prev && prev.db_exists && !engData.db_exists) return prev;
              if (prev && prev.agent_state === engData.agent_state &&
                  prev.turn_count === engData.turn_count &&
                  prev.live === engData.live) return prev;
              return engData;
            });
          }
        } catch { /* keep previous state */ }
      }

      const currentView = viewRef.current;
      if (currentView === 'loading') {
        // Always go to dashboard — provisioning stepper in AnimaVM is the onboarding
        setView('dashboard');
        if (data.config_exists || data.wallet_address || data.engine_live) {
          setEngineStarted(true);
        }
      }
    } catch (e) {
      console.error('Status poll failed:', e);
      if (viewRef.current === 'loading') setView('dashboard');
    }
  }, []); // No dependencies — uses refs for mutable values

  // SSE-triggered status check — replaces 8s polling with push-based updates
  useSSETrigger(checkStatus, { fallbackMs: 8000, deps: [selectedAgent] });

  const fundName = identity?.name || genesisState?.fund_name || null;

  if (view === 'loading') {
    return <div style={{ minHeight: '100vh', background: '#09090b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '32px', height: '32px', border: '3px solid #27272a', borderTop: '3px solid #fff', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>;
  }

  // DASHBOARD
  const renderPage = () => {
    switch (currentPage) {
      case 'fundhq': return <FundHQ fundName={fundName} selectedAgent={selectedAgent} />;
      case 'animavm': return <AnimaVM selectedAgent={selectedAgent} />;
      case 'mind': return <AgentMind genesisState={genesisState} selectedAgent={selectedAgent} />;
      case 'agents': return <Agents selectedAgent={selectedAgent} />;
      case 'infra': return <Infrastructure selectedAgent={selectedAgent} />;
      case 'skills': return <Skills selectedAgent={selectedAgent} />;
      case 'deals': return <DealFlow selectedAgent={selectedAgent} />;
      case 'portfolio': return <Portfolio selectedAgent={selectedAgent} />;
      case 'financials': return <Financials selectedAgent={selectedAgent} />;
      case 'activity': return <Activity selectedAgent={selectedAgent} />;
      case 'memory': return <Memory selectedAgent={selectedAgent} />;
      case 'config': return <Configuration identity={identity} engineState={engineState} genesisState={genesisState} selectedAgent={selectedAgent} />;
      case 'wallet': return <AgentMind genesisState={genesisState} showWalletView={true} selectedAgent={selectedAgent} />;
      default: return <AgentMind genesisState={genesisState} selectedAgent={selectedAgent} />;
    }
  };

  return (
    <div className="flex h-screen bg-[#fafafa]" data-testid="dashboard">
      <Toaster position="top-right" richColors />
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} fundName={fundName} />
      <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-200 ${sidebarOpen ? 'ml-60' : 'ml-16'}`}>
        <Header overview={engineState} currentPage={currentPage} onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} agentList={agentList} selectedAgent={selectedAgent} onSelectAgent={handleSelectAgent} onCreateAgent={() => setShowCreateModal(true)} />
        <main className="flex-1 overflow-y-auto p-6">{renderPage()}</main>
      </div>
      {showCreateModal && <CreateAgentModal onClose={() => setShowCreateModal(false)} onCreated={handleAgentCreated} />}
    </div>
  );
}

function App() {
  return (
    <SSEProvider>
      <AppInner />
    </SSEProvider>
  );
}

export default App;
