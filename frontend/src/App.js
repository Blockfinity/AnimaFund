import React, { useState, useEffect, useCallback } from 'react';
import { Toaster, toast } from 'sonner';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import AgentMind from './pages/AgentMind';
import Tycoon from './pages/Tycoon';
import Configuration from './pages/Configuration';

const API = process.env.REACT_APP_BACKEND_URL;

function GenesisScreen({ onCreated }) {
  const [creating, setCreating] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const createGenesis = async () => {
    setCreating(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/genesis/create`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setResult(data);
        toast.success('Genesis agent created');
      } else {
        setError(data.error || data.detail || 'Creation failed');
        toast.error('Failed to create genesis agent');
      }
    } catch (e) {
      setError(e.message);
      toast.error('Connection error');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#09090b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Manrope, sans-serif' }}>
      <div style={{ maxWidth: '560px', width: '100%', padding: '40px' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '40px' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '12px', background: '#18181b', border: '2px solid #27272a', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <h1 style={{ fontSize: '28px', fontWeight: 900, color: '#fff', letterSpacing: '-0.5px', margin: '0 0 8px' }}>ANIMA FUND</h1>
          <p style={{ fontSize: '14px', color: '#71717a', margin: 0 }}>Autonomous AI-to-AI Venture Capital Fund</p>
        </div>

        {!result ? (
          <>
            {/* Info */}
            <div style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '20px', marginBottom: '20px' }}>
              <p style={{ fontSize: '13px', color: '#a1a1aa', lineHeight: 1.6, margin: '0 0 12px' }}>
                This will create the founder AI agent — a sovereign autonomous agent that will build and operate a complete VC fund from scratch.
              </p>
              <div style={{ fontSize: '12px', color: '#71717a', lineHeight: 1.8 }}>
                <div>The agent will:</div>
                <div style={{ paddingLeft: '12px' }}>
                  <div>1. Generate its own Ethereum wallet</div>
                  <div>2. Load the genesis prompt (complete operating manual)</div>
                  <div>3. Install the constitution (immutable rules)</div>
                  <div>4. Install 5 fund-specific skills</div>
                  <div>5. Build the Automaton runtime</div>
                </div>
                <div style={{ marginTop: '12px', color: '#FFB347' }}>
                  After creation, fund the wallet with USDC on Base to start the agent.
                </div>
                <div style={{ marginTop: '8px', color: '#60EE79' }}>
                  50% of all revenue → <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px' }}>xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r</span> (Solana)
                </div>
              </div>
            </div>

            {/* Create Button */}
            <button
              data-testid="create-genesis-btn"
              onClick={createGenesis}
              disabled={creating}
              style={{
                width: '100%', padding: '14px', borderRadius: '8px', border: 'none',
                background: creating ? '#27272a' : '#fff', color: creating ? '#71717a' : '#09090b',
                fontSize: '15px', fontWeight: 800, cursor: creating ? 'wait' : 'pointer',
                letterSpacing: '0.5px', transition: 'all 0.2s',
              }}
            >
              {creating ? 'Creating Genesis Agent...' : 'Create Genesis Agent'}
            </button>

            {error && (
              <div style={{ marginTop: '12px', padding: '12px', background: '#1c1017', border: '1px solid #7f1d1d', borderRadius: '6px', fontSize: '12px', color: '#fca5a5' }}>
                {error}
              </div>
            )}
          </>
        ) : (
          <>
            {/* Success — Show wallet */}
            <div style={{ background: '#0a1a0a', border: '1px solid #166534', borderRadius: '8px', padding: '20px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34D399' }} />
                <span style={{ fontSize: '14px', fontWeight: 800, color: '#34D399' }}>Genesis Agent Created</span>
              </div>

              {result.wallet_address && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '10px', color: '#71717a', fontWeight: 700, letterSpacing: '1px', marginBottom: '4px' }}>AGENT WALLET (fund this with USDC on Base)</div>
                  <div style={{
                    background: '#18181b', borderRadius: '6px', padding: '12px', fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '13px', color: '#fff', wordBreak: 'break-all', border: '1px solid #27272a',
                    cursor: 'pointer',
                  }}
                    onClick={() => { navigator.clipboard.writeText(result.wallet_address); toast.success('Wallet address copied'); }}
                    data-testid="wallet-address"
                  >
                    {result.wallet_address}
                    <div style={{ fontSize: '9px', color: '#71717a', marginTop: '4px' }}>Click to copy</div>
                  </div>
                </div>
              )}

              <div style={{ fontSize: '11px', color: '#71717a', lineHeight: 1.8 }}>
                <div>Constitution: {result.constitution_installed ? 'Installed' : 'Missing'}</div>
                <div>Genesis Prompt: {result.genesis_staged ? 'Staged' : 'Missing'}</div>
                <div>Skills: {result.skills_installed?.join(', ') || 'None'}</div>
                <div>Engine Built: {result.automaton_built ? 'Yes' : 'No'}</div>
              </div>
            </div>

            <div style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
              <div style={{ fontSize: '10px', color: '#71717a', fontWeight: 700, letterSpacing: '1px', marginBottom: '4px' }}>CREATOR WALLET (receives 50% of revenue)</div>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '11px', color: '#FFB347', wordBreak: 'break-all' }}>
                {result.creator_wallet}
              </div>
              <div style={{ fontSize: '10px', color: '#71717a', marginTop: '4px' }}>Solana • USDC</div>
            </div>

            <div style={{ fontSize: '12px', color: '#a1a1aa', lineHeight: 1.6, marginBottom: '20px', padding: '12px', background: '#18181b', borderRadius: '6px', border: '1px solid #27272a' }}>
              {result.next_step}
            </div>

            <button
              data-testid="continue-to-dashboard-btn"
              onClick={onCreated}
              style={{
                width: '100%', padding: '14px', borderRadius: '8px', border: 'none',
                background: '#fff', color: '#09090b', fontSize: '15px', fontWeight: 800,
                cursor: 'pointer', letterSpacing: '0.5px',
              }}
            >
              Continue to Dashboard
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function Dashboard() {
  const [currentPage, setCurrentPage] = useState('mind');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [engineState, setEngineState] = useState(null);
  const [identity, setIdentity] = useState(null);

  useEffect(() => {
    const check = async () => {
      try {
        const [engRes, idRes] = await Promise.all([
          fetch(`${API}/api/engine/live`),
          fetch(`${API}/api/live/identity`),
        ]);
        setEngineState(await engRes.json());
        setIdentity(await idRes.json());
      } catch (e) { console.error(e); }
    };
    check();
    const i = setInterval(check, 15000);
    return () => clearInterval(i);
  }, []);

  const fundName = identity?.name || null;

  const renderPage = () => {
    switch (currentPage) {
      case 'tycoon': return <Tycoon fundName={fundName} />;
      case 'mind': return <AgentMind />;
      case 'config': return <Configuration identity={identity} />;
      default: return <AgentMind />;
    }
  };

  return (
    <div className="flex h-screen bg-[#fafafa]" data-testid="dashboard">
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} fundName={fundName} />
      <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-200 ${sidebarOpen ? 'ml-60' : 'ml-16'}`}>
        <Header overview={engineState} currentPage={currentPage} onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        <main className="flex-1 overflow-y-auto p-6">{renderPage()}</main>
      </div>
    </div>
  );
}

function App() {
  const [genesisCreated, setGenesisCreated] = useState(null); // null = checking, true/false
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${API}/api/genesis/status`);
        const data = await res.json();
        // Agent is "created" if wallet exists or engine is live
        setGenesisCreated(data.wallet_exists || data.engine_live || data.config_exists);
      } catch (e) {
        setGenesisCreated(false);
      } finally {
        setChecking(false);
      }
    };
    check();
  }, []);

  if (checking) {
    return (
      <div style={{ minHeight: '100vh', background: '#09090b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: '32px', height: '32px', border: '3px solid #27272a', borderTop: '3px solid #fff', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <>
      <Toaster position="top-right" richColors />
      {genesisCreated ? (
        <Dashboard />
      ) : (
        <GenesisScreen onCreated={() => setGenesisCreated(true)} />
      )}
    </>
  );
}

export default App;
