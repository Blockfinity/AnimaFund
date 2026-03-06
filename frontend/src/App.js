import React, { useState, useEffect, useCallback } from 'react';
import { Toaster, toast } from 'sonner';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import AgentMind from './pages/AgentMind';
import Tycoon from './pages/Tycoon';
import Configuration from './pages/Configuration';

const API = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [page, setPage] = useState('genesis'); // genesis | dashboard
  const [genesisState, setGenesisState] = useState(null);
  const [creating, setCreating] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState('mind');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [identity, setIdentity] = useState(null);
  const [engineState, setEngineState] = useState(null);

  // Poll genesis status
  const checkStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/genesis/status`);
      const data = await res.json();
      setGenesisState(data);

      // If engine is live, go to dashboard
      if (data.engine_live) {
        setPage('dashboard');
      }

      // Also fetch identity if wallet exists
      if (data.wallet_exists) {
        const idRes = await fetch(`${API}/api/live/identity`);
        setIdentity(await idRes.json());
        const engRes = await fetch(`${API}/api/engine/live`);
        setEngineState(await engRes.json());
      }
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { checkStatus(); const i = setInterval(checkStatus, 10000); return () => clearInterval(i); }, [checkStatus]);

  // Create genesis agent
  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/genesis/create`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setGenesisState(prev => ({ ...prev, ...data, wallet_exists: true, wallet_address: data.wallet_address, status: 'created_awaiting_funding' }));
        toast.success('Genesis agent created');
      } else {
        setError(data.build_error || data.detail || 'Creation failed');
        toast.error('Failed to create genesis agent');
      }
    } catch (e) {
      setError(e.message);
      toast.error('Connection error');
    } finally {
      setCreating(false);
    }
  };

  // Start the engine
  const handleStart = async () => {
    setStarting(true);
    try {
      const res = await fetch(`${API}/api/genesis/start`, { method: 'POST' });
      const data = await res.json();
      if (data.started) {
        toast.success('Engine starting...');
        // Poll more frequently to detect when it's live
        const fastPoll = setInterval(async () => {
          const s = await (await fetch(`${API}/api/engine/live`)).json();
          if (s.live) { clearInterval(fastPoll); setPage('dashboard'); checkStatus(); }
        }, 3000);
        setTimeout(() => clearInterval(fastPoll), 120000);
      } else {
        toast.error(data.error || 'Failed to start');
      }
    } catch (e) { toast.error(e.message); }
    finally { setStarting(false); }
  };

  const walletAddr = genesisState?.wallet_address;
  const isCreated = genesisState?.wallet_exists || genesisState?.wallet_address;
  const isLive = genesisState?.engine_live || engineState?.live;
  const fundName = identity?.name || null;

  // ═══ GENESIS SCREEN ═══
  if (page === 'genesis' || !isLive) {
    return (
      <div style={{ minHeight: '100vh', background: '#09090b', fontFamily: 'Manrope, sans-serif' }}>
        <Toaster position="top-right" richColors />
        <div style={{ maxWidth: '580px', margin: '0 auto', padding: '40px 20px' }}>
          {/* Logo */}
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '12px', background: '#18181b', border: '2px solid #27272a', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            </div>
            <h1 style={{ fontSize: '24px', fontWeight: 900, color: '#fff', margin: '0 0 4px' }}>ANIMA FUND</h1>
            <p style={{ fontSize: '12px', color: '#71717a', margin: 0 }}>Autonomous AI-to-AI Venture Capital Fund</p>
          </div>

          {!isCreated ? (
            <>
              {/* Pre-creation info */}
              <div style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '16px', marginBottom: '16px', fontSize: '12px', color: '#a1a1aa', lineHeight: 1.7 }}>
                <p style={{ margin: '0 0 8px' }}>This creates the founder AI — a sovereign agent that builds and operates a VC fund from scratch.</p>
                <div style={{ color: '#71717a', fontSize: '11px' }}>
                  <div>1. Generate Ethereum wallet</div>
                  <div>2. Load genesis prompt (324 lines)</div>
                  <div>3. Install constitution (11 immutable laws)</div>
                  <div>4. Install 5 fund skills</div>
                  <div>5. Build Automaton runtime</div>
                </div>
                <div style={{ marginTop: '10px', fontSize: '11px' }}>
                  <span style={{ color: '#FFB347' }}>After creation, fund the wallet with USDC on Base.</span>
                </div>
                <div style={{ marginTop: '4px', fontSize: '10px', color: '#60EE79' }}>
                  50% of all revenue → <span style={{ fontFamily: 'JetBrains Mono, monospace' }}>xtmyybmR6b9pw...9sZ2r</span> (Solana)
                </div>
              </div>
              <button data-testid="create-genesis-btn" onClick={handleCreate} disabled={creating}
                style={{ width: '100%', padding: '14px', borderRadius: '8px', border: 'none', background: creating ? '#27272a' : '#fff', color: creating ? '#71717a' : '#09090b', fontSize: '14px', fontWeight: 800, cursor: creating ? 'wait' : 'pointer' }}>
                {creating ? 'Creating Genesis Agent...' : 'Create Genesis Agent'}
              </button>
              {error && <div style={{ marginTop: '10px', padding: '10px', background: '#1c1017', border: '1px solid #7f1d1d', borderRadius: '6px', fontSize: '11px', color: '#fca5a5' }}>{error}</div>}
            </>
          ) : (
            <>
              {/* Agent created — show wallet + QR + status */}
              <div style={{ background: '#0a1a0a', border: '1px solid #166534', borderRadius: '8px', padding: '20px', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isLive ? '#34D399' : '#FFB347', boxShadow: isLive ? '0 0 8px #34D399' : 'none' }} />
                  <span style={{ fontSize: '13px', fontWeight: 800, color: isLive ? '#34D399' : '#FFB347' }}>
                    {isLive ? 'Agent Running' : 'Agent Created — Awaiting Funding'}
                  </span>
                </div>

                {/* QR Code */}
                {(genesisState?.qr_code || walletAddr) && (
                  <div style={{ textAlign: 'center', marginBottom: '14px' }}>
                    {genesisState?.qr_code ? (
                      <img src={genesisState.qr_code} alt="QR" style={{ width: '160px', height: '160px', borderRadius: '8px', border: '2px solid #27272a' }} data-testid="wallet-qr" />
                    ) : walletAddr ? (
                      <img src={`${API}/api/genesis/qr/${walletAddr}`} alt="QR" style={{ width: '160px', height: '160px', borderRadius: '8px', border: '2px solid #27272a' }} data-testid="wallet-qr" />
                    ) : null}
                    <div style={{ fontSize: '9px', color: '#71717a', marginTop: '4px' }}>Scan to send USDC on Base</div>
                  </div>
                )}

                {/* Wallet address */}
                {walletAddr && (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '1px', marginBottom: '3px' }}>AGENT WALLET</div>
                    <div style={{ background: '#18181b', borderRadius: '6px', padding: '10px', fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', color: '#fff', wordBreak: 'break-all', border: '1px solid #27272a', cursor: 'pointer' }}
                      onClick={() => { navigator.clipboard.writeText(walletAddr); toast.success('Copied'); }} data-testid="wallet-address">
                      {walletAddr}
                      <span style={{ fontSize: '8px', color: '#52525b', display: 'block', marginTop: '2px' }}>Click to copy</span>
                    </div>
                  </div>
                )}

                {/* Status */}
                <div style={{ fontSize: '10px', color: '#71717a', lineHeight: 1.8 }}>
                  <div>Constitution: {genesisState?.constitution_installed ? '✓' : '—'} | Genesis: {genesisState?.genesis_staged ? '✓' : '—'} | Build: <span style={{ color: genesisState?.build_status === 'built' || genesisState?.build_status === 'already_built' ? '#34D399' : '#FFB347' }}>{genesisState?.build_status || genesisState?.status || '—'}</span></div>
                  {genesisState?.skills_installed?.length > 0 && <div>Skills: {genesisState.skills_installed.join(', ')}</div>}
                  <div>Engine: <span style={{ color: isLive ? '#34D399' : '#71717a' }}>{isLive ? `LIVE (${genesisState?.turn_count || 0} turns)` : 'Not running'}</span></div>
                </div>
              </div>

              {/* Creator wallet */}
              <div style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
                <div style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '1px', marginBottom: '2px' }}>CREATOR WALLET (50% revenue)</div>
                <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#FFB347', wordBreak: 'break-all' }}>{genesisState?.creator_wallet}</div>
                <div style={{ fontSize: '9px', color: '#52525b', marginTop: '2px' }}>Solana — USDC</div>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: '8px' }}>
                {!isLive && (
                  <button data-testid="start-engine-btn" onClick={handleStart} disabled={starting}
                    style={{ flex: 1, padding: '12px', borderRadius: '8px', border: 'none', background: starting ? '#27272a' : '#34D399', color: starting ? '#71717a' : '#000', fontSize: '13px', fontWeight: 800, cursor: starting ? 'wait' : 'pointer' }}>
                    {starting ? 'Starting...' : 'Start Engine'}
                  </button>
                )}
                <button data-testid="go-to-dashboard-btn" onClick={() => setPage('dashboard')}
                  style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid #27272a', background: 'transparent', color: '#fff', fontSize: '13px', fontWeight: 800, cursor: 'pointer' }}>
                  {isLive ? 'Open Dashboard' : 'View Dashboard'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  // ═══ DASHBOARD ═══
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
