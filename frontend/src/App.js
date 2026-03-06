import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Toaster, toast } from 'sonner';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import EngineConsole from './components/EngineConsole';
import AgentMind from './pages/AgentMind';
import FundHQ from './pages/FundHQ';
import Agents from './pages/Agents';
import DealFlow from './pages/DealFlow';
import Portfolio from './pages/Portfolio';
import Financials from './pages/Financials';
import Activity from './pages/Activity';
import Memory from './pages/Memory';
import Configuration from './pages/Configuration';

const API = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [view, setView] = useState('loading');
  const [genesisState, setGenesisState] = useState(null);
  const [creating, setCreating] = useState(false);
  const [engineStarted, setEngineStarted] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState('mind');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [identity, setIdentity] = useState(null);
  const [engineState, setEngineState] = useState(null);
  const creatingRef = useRef(false);

  const checkStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/genesis/status`);
      const data = await res.json();
      setGenesisState(data);

      // Once engine is detected as running or wallet exists, lock it in
      if (data.engine_running || data.wallet_address || data.config_exists) {
        setEngineStarted(true);
      }

      // Fetch live data if engine is known to have started
      if (data.engine_running || data.engine_live || data.wallet_address || data.config_exists) {
        try {
          const [idRes, engRes] = await Promise.all([
            fetch(`${API}/api/live/identity`),
            fetch(`${API}/api/engine/live`),
          ]);
          if (idRes.ok) setIdentity(await idRes.json());
          if (engRes.ok) setEngineState(await engRes.json());
        } catch { /* ignore live data fetch errors */ }
      }

      if (view === 'loading') {
        setView('genesis');
      }
    } catch (e) {
      console.error(e);
      if (view === 'loading') setView('genesis');
    }
  }, [view]);

  useEffect(() => { checkStatus(); const i = setInterval(checkStatus, 5000); return () => clearInterval(i); }, [checkStatus]);

  const handleCreate = async () => {
    if (creatingRef.current) return; // Prevent double-clicks
    creatingRef.current = true;
    setCreating(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/genesis/create`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        toast.success('Genesis agent created — engine starting');
        setEngineStarted(true); // Lock in the started state immediately
        checkStatus();
      } else {
        setError(data.error || data.detail || 'Creation failed');
        creatingRef.current = false;
        setCreating(false);
      }
    } catch (e) {
      setError(e.message);
      creatingRef.current = false;
      setCreating(false);
    }
    // NOTE: We do NOT reset creating to false on success — the status poll will detect engine_running
  };

  const status = genesisState?.status || 'not_created';
  const walletAddr = genesisState?.wallet_address;
  const qrCode = genesisState?.qr_code;
  const isRunning = genesisState?.engine_running || false;
  const isLive = genesisState?.engine_live || engineState?.live || false;
  const fundName = identity?.name || genesisState?.fund_name || null;
  const dbExists = engineState?.db_exists || false;

  // Show the status panel if: engine started, creating, running, wallet exists, or config exists
  const showStatusPanel = engineStarted || creating || isRunning || walletAddr || status === 'running';

  if (view === 'loading') {
    return <div style={{ minHeight: '100vh', background: '#09090b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '32px', height: '32px', border: '3px solid #27272a', borderTop: '3px solid #fff', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>;
  }

  // GENESIS SCREEN
  if (view === 'genesis') {
    return (
      <div style={{ minHeight: '100vh', background: '#09090b', fontFamily: 'Manrope, sans-serif' }}>
        <Toaster position="top-right" richColors />
        <div style={{ maxWidth: '580px', margin: '0 auto', padding: '40px 20px' }}>
          {/* Logo */}
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '12px', background: '#18181b', border: '2px solid #27272a', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            </div>
            <h1 style={{ fontSize: '24px', fontWeight: 900, color: '#fff', margin: '0 0 4px' }}>{fundName || 'ANIMA FUND'}</h1>
            <p style={{ fontSize: '12px', color: '#71717a', margin: 0 }}>Autonomous AI-to-AI Venture Capital Fund</p>
          </div>

          {!showStatusPanel ? (
            <>
              <div style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '16px', marginBottom: '16px', fontSize: '12px', color: '#a1a1aa', lineHeight: 1.7 }}>
                <p style={{ margin: '0 0 8px' }}>This creates and launches the founder AI — a sovereign agent that builds and operates a VC fund from scratch.</p>
                <div style={{ marginTop: '10px', fontSize: '11px', color: '#FFB347' }}>The agent will generate its own wallet, provision its API key, and begin operating.</div>
                <div style={{ marginTop: '4px', fontSize: '10px', color: '#60EE79' }}>50% of all revenue goes to creator on Solana</div>
              </div>
              <button data-testid="create-genesis-btn" onClick={handleCreate} disabled={creating}
                style={{ width: '100%', padding: '14px', borderRadius: '8px', border: 'none', background: creating ? '#52525b' : '#fff', color: '#09090b', fontSize: '14px', fontWeight: 800, cursor: creating ? 'not-allowed' : 'pointer', opacity: creating ? 0.6 : 1 }}>
                {creating ? 'Starting...' : 'Create Genesis Agent'}
              </button>
              {error && <div data-testid="error-message" style={{ marginTop: '10px', padding: '10px', background: '#1c1017', border: '1px solid #7f1d1d', borderRadius: '6px', fontSize: '11px', color: '#fca5a5' }}>{error}</div>}
            </>
          ) : (
            <>
              {/* Engine status panel */}
              <div data-testid="engine-status-panel" style={{ background: '#0a1a0a', border: '1px solid #166534', borderRadius: '8px', padding: '20px', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isLive ? '#34D399' : (isRunning || dbExists) ? '#FFB347' : '#71717a', boxShadow: isLive ? '0 0 8px #34D399' : 'none' }} />
                  <span style={{ fontSize: '13px', fontWeight: 800, color: isLive ? '#34D399' : (isRunning || dbExists) ? '#FFB347' : '#71717a' }}>
                    {isLive ? 'Agent Running' :
                     isRunning && walletAddr ? 'Engine Running — Awaiting Funding' :
                     isRunning ? 'Engine Starting...' :
                     dbExists ? 'Engine Configured — Awaiting Restart' :
                     creating ? 'Starting Engine...' : 'Initializing...'}
                  </span>
                </div>

                {/* QR + Wallet */}
                {walletAddr && walletAddr.startsWith('0x') && (
                  <>
                    {qrCode && (
                      <div style={{ textAlign: 'center', marginBottom: '14px' }}>
                        <img src={qrCode} alt="QR" style={{ width: '160px', height: '160px', borderRadius: '8px', border: '2px solid #27272a' }} data-testid="wallet-qr" />
                        <div style={{ fontSize: '9px', color: '#71717a', marginTop: '4px' }}>Scan to send USDC on Base</div>
                      </div>
                    )}
                    <div style={{ marginBottom: '12px' }}>
                      <div style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '1px', marginBottom: '3px' }}>AGENT WALLET</div>
                      <div data-testid="wallet-address" style={{ background: '#18181b', borderRadius: '6px', padding: '10px', fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', color: '#fff', wordBreak: 'break-all', border: '1px solid #27272a', cursor: 'pointer' }}
                        onClick={() => { navigator.clipboard.writeText(walletAddr); toast.success('Copied'); }}>
                        {walletAddr}
                      </div>
                    </div>
                  </>
                )}

                {/* Status details */}
                <div style={{ fontSize: '10px', color: '#71717a', lineHeight: 1.8 }}>
                  <div>Engine: <span style={{ color: isLive ? '#34D399' : (isRunning || dbExists) ? '#FFB347' : '#71717a' }}>{isLive ? `LIVE (${genesisState?.turn_count || 0} turns)` : isRunning ? 'Running' : dbExists ? 'Configured' : 'Starting'}</span></div>
                  {genesisState?.engine_state && <div>State: {genesisState.engine_state}</div>}
                  {!walletAddr && (isRunning || creating) && <div style={{ color: '#FFB347', marginTop: '4px' }}>Starting engine and generating wallet...</div>}
                </div>
              </div>

              {/* Engine Console */}
              <div style={{ marginBottom: '12px' }}>
                <EngineConsole isRunning={isRunning || creating || engineStarted} />
              </div>

              {/* Creator wallet */}
              <div style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
                <div style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '1px', marginBottom: '2px' }}>CREATOR WALLET (50% revenue)</div>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#FFB347', wordBreak: 'break-all' }}>{genesisState?.creator_wallet}</div>
              </div>

              {/* Dashboard button */}
              <button data-testid="go-to-dashboard-btn" onClick={() => setView('dashboard')}
                style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #27272a', background: 'transparent', color: '#fff', fontSize: '13px', fontWeight: 800, cursor: 'pointer' }}>
                Open Dashboard
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  // DASHBOARD
  const renderPage = () => {
    switch (currentPage) {
      case 'fundhq': return <FundHQ fundName={fundName} />;
      case 'mind': return <AgentMind />;
      case 'agents': return <Agents />;
      case 'deals': return <DealFlow />;
      case 'portfolio': return <Portfolio />;
      case 'financials': return <Financials />;
      case 'activity': return <Activity />;
      case 'memory': return <Memory />;
      case 'config': return <Configuration identity={identity} engineState={engineState} genesisState={genesisState} />;
      default: return <AgentMind />;
    }
  };

  return (
    <div className="flex h-screen bg-[#fafafa]" data-testid="dashboard">
      <Toaster position="top-right" richColors />
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} fundName={fundName} />
      <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-200 ${sidebarOpen ? 'ml-60' : 'ml-16'}`}>
        <Header overview={engineState} currentPage={currentPage} onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />
        <main className="flex-1 overflow-y-auto p-6">{renderPage()}</main>
      </div>
    </div>
  );
}

export default App;
