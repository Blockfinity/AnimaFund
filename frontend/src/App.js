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
import EngineConsole from './components/EngineConsole';
import { SSEProvider, useSSE, useSSETrigger } from './hooks/useSSE';
import {
  Server, Terminal, Eye, Cpu, FileText, Rocket,
  CheckCircle2, Loader2, ChevronDown, Play, RotateCcw, Shield, Zap,
  Wallet, RefreshCw, ExternalLink, Copy, DollarSign
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

/* ─── Provisioning Steps (used on genesis screen) ─── */
const PROVISION_STEPS = [
  { id: 'sandbox', label: 'Create Sandbox', desc: 'Conway Cloud VM (2 vCPU, 4GB, 40GB)', action: '/api/provision/create-sandbox', icon: Server },
  { id: 'terminal', label: 'Install Terminal', desc: 'Conway Terminal + wallet + API key + all MCPs', action: '/api/provision/install-terminal', icon: Terminal },
  { id: 'openclaw', label: 'Install OpenClaw', desc: 'Autonomous browser + MCP bridge', action: '/api/provision/install-openclaw', icon: Eye },
  { id: 'claudecode', label: 'Install Claude Code', desc: 'Self-modification via MCP', action: '/api/provision/install-claude-code', icon: Cpu },
  { id: 'skills', label: 'Load Skills', desc: 'Push skill definitions into sandbox', action: '/api/provision/load-skills', icon: FileText },
  { id: 'deploy', label: 'Create Anima', desc: 'Push engine into sandbox + launch autonomous agent', action: '/api/provision/deploy-agent', icon: Rocket },
];

function AppInner() {
  const [view, setView] = useState('loading');
  const [genesisState, setGenesisState] = useState(null);
  const [engineStarted, setEngineStarted] = useState(false);
  const [currentPage, setCurrentPage] = useState('mind');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [identity, setIdentity] = useState(null);
  const [engineState, setEngineState] = useState(null);

  // Multi-agent state
  const [agentList, setAgentList] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('anima-fund');
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Provisioning stepper state (for genesis screen)
  const [provStatus, setProvStatus] = useState(null);
  const [runningStep, setRunningStep] = useState(null);
  const [stepOutputs, setStepOutputs] = useState({});
  const [expandedStep, setExpandedStep] = useState(null);

  // Credits funding state
  const [creditBalance, setCreditBalance] = useState(null);
  const [creditTiers, setCreditTiers] = useState([]);
  const [vmPricing, setVmPricing] = useState([]);
  const [selectedTier, setSelectedTier] = useState(25);
  const [purchaseData, setPurchaseData] = useState(null);
  const [fundingLoading, setFundingLoading] = useState(false);
  const [balancePolling, setBalancePolling] = useState(false);

  // Fetch agent list
  const fetchAgents = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/agents`);
      const data = await res.json();
      setAgentList(data.agents || []);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchAgents(); }, [fetchAgents]);

  // Fetch provision status
  const fetchProvStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/provision/status`);
      if (res.ok) setProvStatus(await res.json());
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { fetchProvStatus(); }, [fetchProvStatus]);

  // Fetch credit balance
  const fetchCreditBalance = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/credits/balance`);
      if (res.ok) {
        const data = await res.json();
        setCreditBalance(data.credits_cents ?? 0);
      }
    } catch { /* ignore */ }
  }, []);

  // Fetch pricing tiers on mount
  useEffect(() => {
    fetchCreditBalance();
    (async () => {
      try {
        const res = await fetch(`${API}/api/credits/pricing`);
        if (res.ok) {
          const data = await res.json();
          setCreditTiers(data.tiers || []);
          setVmPricing(data.pricing || []);
        }
      } catch { /* ignore */ }
    })();
  }, [fetchCreditBalance]);

  // Poll balance when funding panel is open
  useEffect(() => {
    if (!balancePolling) return;
    const interval = setInterval(fetchCreditBalance, 5000);
    return () => clearInterval(interval);
  }, [balancePolling, fetchCreditBalance]);

  // Handle purchase — get payment QR from backend
  const handlePurchase = async () => {
    setFundingLoading(true);
    try {
      const res = await fetch(`${API}/api/credits/purchase`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: selectedTier }),
      });
      const data = await res.json();
      if (data.success) {
        setPurchaseData(data);
        setBalancePolling(true);
        toast.success('Payment details ready — scan QR to send USDC');
      } else {
        toast.error(data.error || 'Failed to get payment details');
      }
    } catch (e) { toast.error(e.message); }
    setFundingLoading(false);
  };

  const handleSelectAgent = async (agentId) => {
    try {
      const res = await fetch(`${API}/api/agents/${agentId}/select`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || `Failed to switch to agent: ${res.status}`);
        fetchAgents();
        return;
      }
      const data = await res.json();
      if (data.success) {
        setSelectedAgent(agentId);
        setGenesisState(null);
        setIdentity(null);
        setEngineState(null);
        setEngineStarted(false);
        setProvStatus(null);
        setStepOutputs({});
        setView('loading');
        toast.success(`Switched to ${data.active_agent || agentId}`);
      }
    } catch (e) { toast.error(e.message); }
  };

  const handleAgentCreated = async (agent) => {
    await fetchAgents();
    setShowCreateModal(false);
    toast.success(`Agent "${agent.name}" created — provision it now`);
    await handleSelectAgent(agent.agent_id);
  };

  // Use a ref for view to avoid re-creating checkStatus when view changes
  const viewRef = useRef(view);
  useEffect(() => { viewRef.current = view; }, [view]);

  const checkStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/genesis/status`);
      if (!res.ok) return;
      const data = await res.json();

      setGenesisState(prev => {
        if (prev && prev.wallet_address && !data.wallet_address) return prev;
        if (prev && prev.wallet_address === data.wallet_address &&
            prev.engine_live === data.engine_live &&
            prev.engine_running === data.engine_running &&
            prev.status === data.status &&
            prev.turn_count === data.turn_count) return prev;
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

      // Also refresh provision status
      fetchProvStatus();

      const currentView = viewRef.current;
      if (currentView === 'loading') {
        if (data.config_exists || data.wallet_address || data.engine_live) {
          setView('dashboard');
          setEngineStarted(true);
        } else {
          setView('genesis');
        }
      }
    } catch (e) {
      console.error('Status poll failed:', e);
      if (viewRef.current === 'loading') setView('genesis');
    }
  }, [fetchProvStatus]);

  useSSETrigger(checkStatus, { fallbackMs: 8000, deps: [selectedAgent] });

  /* ─── Provisioning stepper helpers ─── */
  const hasSandbox = provStatus?.sandbox?.status === 'active';
  const tools = provStatus?.tools || {};

  const isStepDone = (id) => {
    if (id === 'sandbox') return hasSandbox;
    if (id === 'terminal') return tools['conway-terminal']?.installed;
    if (id === 'openclaw') return tools['openclaw']?.installed;
    if (id === 'claudecode') return tools['claude-code']?.installed;
    if (id === 'skills') return provStatus?.skills_loaded;
    if (id === 'deploy') return tools['engine']?.deployed;
    return false;
  };

  const canRunStep = (step) => {
    if (step.id === 'sandbox') {
      // Need at least 2500 cents ($25) for X-Large VM
      return creditBalance !== null && creditBalance >= 2500;
    }
    return hasSandbox;
  };

  const hasEnoughCredits = creditBalance !== null && creditBalance >= 2500;

  const allProvDone = PROVISION_STEPS.every(s => isStepDone(s.id));
  const completedCount = PROVISION_STEPS.filter(s => isStepDone(s.id)).length;
  const walletAddress = provStatus?.wallet_address || '';

  const runStep = async (step) => {
    setRunningStep(step.id);
    try {
      const res = await fetch(`${API}${step.action}`, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
      const data = await res.json();
      if (data.output) {
        setStepOutputs(prev => ({ ...prev, [step.id]: data.output }));
        setExpandedStep(step.id);
      }
      data.success ? toast.success(`${step.label} complete`) : toast.error(data.error || 'Failed');
      await fetchProvStatus();
    } catch (e) { toast.error(e.message); }
    setRunningStep(null);
  };

  // After all provisioning done, auto-transition to dashboard
  useEffect(() => {
    if (allProvDone && view === 'genesis' && engineStarted) {
      // Don't auto-transition — let user click "Open Dashboard"
    }
  }, [allProvDone, view, engineStarted]);

  const fundName = identity?.name || genesisState?.fund_name || null;
  const selectedAgentName = (agentList || []).find(a => a.agent_id === selectedAgent)?.name || fundName || 'ANIMA FUND';
  const isRunning = genesisState?.engine_running || false;
  const isLive = genesisState?.engine_live || engineState?.live || false;
  const dbExists = engineState?.db_exists || false;
  const agentState = genesisState?.engine_state || engineState?.agent_state || '';
  const isSleeping = agentState === 'sleeping';
  const isCritical = agentState === 'critical';
  const walletAddr = walletAddress || genesisState?.wallet_address || '';
  const qrCode = genesisState?.qr_code;

  if (view === 'loading') {
    return <div style={{ minHeight: '100vh', background: '#09090b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '32px', height: '32px', border: '3px solid #27272a', borderTop: '3px solid #fff', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>;
  }

  // ═══════════════════════════════════════════
  // GENESIS / ONBOARDING SCREEN
  // ═══════════════════════════════════════════
  if (view === 'genesis') {
    return (
      <div style={{ minHeight: '100vh', background: '#09090b', fontFamily: 'Manrope, sans-serif' }}>
        <Toaster position="top-right" richColors />

        {/* Agent switcher bar */}
        {agentList.length > 1 && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '16px 20px 0' }}>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center' }}>
              {agentList.map(a => (
                <button key={a.agent_id} data-testid={`genesis-agent-switch-${a.agent_id}`}
                  onClick={() => handleSelectAgent(a.agent_id)}
                  style={{ padding: '6px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 700, cursor: 'pointer',
                    background: a.agent_id === selectedAgent ? '#fff' : '#18181b',
                    color: a.agent_id === selectedAgent ? '#09090b' : '#a1a1aa',
                    border: `1px solid ${a.agent_id === selectedAgent ? '#fff' : '#27272a'}` }}>
                  {a.name}
                </button>
              ))}
            </div>
          </div>
        )}

        <div style={{ maxWidth: '580px', margin: '0 auto', padding: '40px 20px' }}>
          {/* Logo */}
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '12px', background: '#18181b', border: '2px solid #27272a', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            </div>
            <h1 style={{ fontSize: '24px', fontWeight: 900, color: '#fff', margin: '0 0 4px' }}>{selectedAgentName}</h1>
            <p style={{ fontSize: '12px', color: '#71717a', margin: 0 }}>Autonomous AI-to-AI Venture Capital Fund</p>
          </div>

          {/* Info box */}
          <div style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '14px', marginBottom: '16px', fontSize: '11px', color: '#a1a1aa', lineHeight: 1.7 }}>
            <p style={{ margin: '0 0 6px' }}>Provision a sandboxed VM and deploy the founder AI — a sovereign agent that builds and operates a VC fund from scratch.</p>
            <div style={{ fontSize: '10px', color: '#FFB347' }}>The agent generates its own wallet, provisions tools, and begins operating autonomously.</div>
            <div style={{ fontSize: '10px', color: '#60EE79', marginTop: '3px' }}>50% of all profit (fees, carry, revenue) to creator. $10K threshold to launch fund.</div>
          </div>

          {/* ═══════ CREDITS FUNDING ═══════ */}
          <div data-testid="credits-funding-panel" style={{ background: '#18181b', border: `1px solid ${hasEnoughCredits ? '#166534' : '#92400e'}`, borderRadius: '8px', overflow: 'hidden', marginBottom: '16px' }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '1px solid #27272a' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Wallet style={{ width: '14px', height: '14px', color: hasEnoughCredits ? '#34D399' : '#FBBF24' }} />
                <span style={{ fontSize: '12px', fontWeight: 800, color: '#fff' }}>Conway Credits</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span data-testid="credit-balance" style={{ fontSize: '13px', fontWeight: 900, fontFamily: 'JetBrains Mono, monospace', color: hasEnoughCredits ? '#34D399' : creditBalance === 0 ? '#EF4444' : '#FBBF24' }}>
                  ${creditBalance !== null ? (creditBalance / 100).toFixed(2) : '...'}
                </span>
                <button data-testid="refresh-balance-btn" onClick={fetchCreditBalance} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', display: 'flex' }}>
                  <RefreshCw style={{ width: '12px', height: '12px', color: '#71717a' }} />
                </button>
              </div>
            </div>

            {/* Status message */}
            {!hasEnoughCredits && (
              <div style={{ padding: '10px 14px', borderBottom: '1px solid #27272a', background: '#1c1917' }}>
                <div style={{ fontSize: '11px', color: '#FBBF24', lineHeight: 1.6 }}>
                  <strong>Fund your account</strong> to create a sandbox VM. The X-Large VM (2 vCPU, 4GB, 40GB) costs <strong>$25/mo</strong>.
                  {creditBalance !== null && creditBalance > 0 && <span> You have ${(creditBalance / 100).toFixed(2)} — need ${((2500 - creditBalance) / 100).toFixed(2)} more.</span>}
                </div>
              </div>
            )}
            {hasEnoughCredits && !hasSandbox && (
              <div style={{ padding: '8px 14px', borderBottom: '1px solid #27272a', background: '#052e16' }}>
                <div style={{ fontSize: '11px', color: '#34D399' }}>Credits loaded. You can now create your sandbox below.</div>
              </div>
            )}

            {/* Tier selector + Purchase button */}
            {!hasEnoughCredits && (
              <div style={{ padding: '12px 14px' }}>
                {/* Tier buttons */}
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '10px' }}>
                  {(creditTiers.length > 0 ? creditTiers : [{ amount: 5 }, { amount: 25 }, { amount: 100 }]).map(t => (
                    <button key={t.amount} data-testid={`tier-${t.amount}`}
                      onClick={() => { setSelectedTier(t.amount); setPurchaseData(null); }}
                      style={{
                        padding: '6px 12px', borderRadius: '6px', border: `1px solid ${selectedTier === t.amount ? '#fff' : '#27272a'}`,
                        background: selectedTier === t.amount ? '#fff' : '#09090b',
                        color: selectedTier === t.amount ? '#09090b' : '#a1a1aa',
                        fontSize: '11px', fontWeight: 800, cursor: 'pointer',
                      }}>
                      ${t.amount}
                    </button>
                  ))}
                </div>

                {/* Get Payment Details button */}
                {!purchaseData && (
                  <button data-testid="get-payment-btn" onClick={handlePurchase} disabled={fundingLoading}
                    style={{
                      width: '100%', padding: '10px', borderRadius: '6px', border: 'none',
                      background: fundingLoading ? '#27272a' : '#FBBF24', color: '#09090b',
                      fontSize: '12px', fontWeight: 800, cursor: fundingLoading ? 'not-allowed' : 'pointer',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                    }}>
                    {fundingLoading ? <><Loader2 style={{ width: '12px', height: '12px', animation: 'spin 1s linear infinite' }} /> Loading...</> :
                     <><DollarSign style={{ width: '12px', height: '12px' }} /> Add ${selectedTier} Credits</>}
                  </button>
                )}

                {/* Payment QR + Instructions */}
                {purchaseData && (
                  <div data-testid="payment-details" style={{ background: '#09090b', borderRadius: '8px', border: '1px solid #27272a', padding: '16px', marginTop: '8px' }}>
                    <div style={{ textAlign: 'center', marginBottom: '12px' }}>
                      <div style={{ fontSize: '11px', fontWeight: 800, color: '#FBBF24', marginBottom: '8px' }}>
                        Send {purchaseData.amount_usdc} USDC on Base
                      </div>
                      <img
                        src={purchaseData.qr_code}
                        alt="Payment QR"
                        style={{ width: '180px', height: '180px', borderRadius: '8px', border: '2px solid #27272a', margin: '0 auto' }}
                        data-testid="payment-qr"
                      />
                    </div>

                    {/* Pay-to address */}
                    <div style={{ marginBottom: '10px' }}>
                      <div style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '1px', marginBottom: '2px' }}>PAY TO (USDC on Base)</div>
                      <div data-testid="pay-to-address"
                        onClick={() => { navigator.clipboard.writeText(purchaseData.pay_to); toast.success('Address copied'); }}
                        style={{
                          background: '#18181b', borderRadius: '6px', padding: '8px 10px',
                          fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#FBBF24',
                          wordBreak: 'break-all', border: '1px solid #27272a', cursor: 'pointer',
                          display: 'flex', alignItems: 'center', gap: '6px',
                        }}>
                        <span style={{ flex: 1 }}>{purchaseData.pay_to}</span>
                        <Copy style={{ width: '12px', height: '12px', color: '#71717a', flexShrink: 0 }} />
                      </div>
                    </div>

                    {/* Instructions */}
                    <div style={{ fontSize: '10px', color: '#71717a', lineHeight: 1.8 }}>
                      {(purchaseData.instructions || []).map((inst, i) => (
                        <div key={i} style={{ display: 'flex', gap: '6px' }}>
                          <span style={{ color: '#52525b' }}>{i + 1}.</span>
                          <span>{inst}</span>
                        </div>
                      ))}
                    </div>

                    {/* Polling indicator */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '10px', padding: '8px', background: '#18181b', borderRadius: '6px' }}>
                      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#FBBF24', animation: 'pulse 2s infinite' }} />
                      <span style={{ fontSize: '10px', color: '#a1a1aa' }}>Watching for payment... balance updates every 5s</span>
                    </div>

                    {/* Link to Conway dashboard */}
                    <a href="https://app.conway.tech" target="_blank" rel="noopener noreferrer"
                      data-testid="conway-dashboard-link"
                      style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', marginTop: '8px', fontSize: '10px', color: '#71717a', textDecoration: 'none' }}>
                      <span>Or buy credits at app.conway.tech</span>
                      <ExternalLink style={{ width: '10px', height: '10px' }} />
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ═══════ PROVISIONING STEPPER ═══════ */}
          <div data-testid="provision-stepper" style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px', overflow: 'hidden', marginBottom: '16px' }}>
            {/* Security notice */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px', borderBottom: '1px solid #27272a', background: '#111' }}>
              <Shield style={{ width: '12px', height: '12px', color: '#71717a', flexShrink: 0 }} />
              <span style={{ fontSize: '10px', color: '#71717a' }}>All tools install inside the agent's <strong style={{ color: '#a1a1aa' }}>sandbox VM</strong>. Nothing runs on the host.</span>
            </div>

            {/* Progress */}
            <div style={{ padding: '10px 14px', borderBottom: '1px solid #27272a', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: allProvDone ? '#34D399' : '#fff' }}>
                {allProvDone ? 'Agent Provisioned' : 'Provision Agent'}
              </span>
              <span style={{ fontSize: '10px', color: '#71717a' }}>{completedCount}/{PROVISION_STEPS.length}</span>
              <div style={{ flex: 1, height: '4px', background: '#27272a', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{ height: '100%', background: allProvDone ? '#34D399' : '#fff', borderRadius: '2px', transition: 'width 0.5s', width: `${(completedCount / PROVISION_STEPS.length) * 100}%` }} />
              </div>
            </div>

            {/* Steps */}
            {PROVISION_STEPS.map((step, i) => {
              const done = isStepDone(step.id);
              const enabled = canRunStep(step);
              const isActive = runningStep === step.id;
              const hasOutput = stepOutputs[step.id];
              const isExpanded = expandedStep === step.id;
              const Icon = step.icon;

              return (
                <div key={step.id} data-testid={`step-${step.id}`} style={{ borderBottom: '1px solid #1a1a1f', opacity: !enabled && !done ? 0.35 : 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px' }}>
                    {/* Number/status */}
                    <div style={{ width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', fontWeight: 700, flexShrink: 0,
                      background: done ? '#064e3b' : isActive ? '#fff' : '#27272a',
                      color: done ? '#34D399' : isActive ? '#09090b' : '#71717a' }}>
                      {done ? <CheckCircle2 style={{ width: '14px', height: '14px' }} /> :
                       isActive ? <Loader2 style={{ width: '14px', height: '14px', animation: 'spin 1s linear infinite' }} /> :
                       i + 1}
                    </div>
                    {/* Label + desc */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '12px', fontWeight: 700, color: done ? '#34D399' : '#fff' }}>{step.label}</div>
                      <div style={{ fontSize: '10px', color: '#52525b' }}>{step.desc}</div>
                    </div>
                    {/* Output toggle */}
                    {hasOutput && (
                      <button onClick={() => setExpandedStep(isExpanded ? null : step.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}>
                        <ChevronDown style={{ width: '12px', height: '12px', color: '#71717a', transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
                      </button>
                    )}
                    {/* Run button */}
                    <button
                      data-testid={`run-${step.id}`}
                      onClick={() => runStep(step)}
                      disabled={!enabled || isActive || (runningStep && runningStep !== step.id)}
                      style={{ display: 'flex', alignItems: 'center', gap: '4px', padding: '5px 10px', borderRadius: '6px', border: 'none', fontSize: '10px', fontWeight: 800, cursor: (!enabled || isActive || (runningStep && runningStep !== step.id)) ? 'not-allowed' : 'pointer', flexShrink: 0,
                        background: (!enabled || (runningStep && runningStep !== step.id)) ? '#27272a' : isActive ? '#27272a' : done ? '#27272a' : '#fff',
                        color: (!enabled || (runningStep && runningStep !== step.id)) ? '#52525b' : isActive ? '#52525b' : done ? '#a1a1aa' : '#09090b',
                        opacity: (!enabled || (runningStep && runningStep !== step.id)) ? 0.5 : 1 }}>
                      {isActive ? <><Loader2 style={{ width: '10px', height: '10px', animation: 'spin 1s linear infinite' }} /> Running...</> :
                       done ? <><RotateCcw style={{ width: '10px', height: '10px' }} /> Redo</> :
                       <><Play style={{ width: '10px', height: '10px' }} /> Run</>}
                    </button>
                  </div>
                  {/* Output */}
                  {isExpanded && hasOutput && (
                    <div style={{ background: '#0a0a0a', padding: '8px 14px', borderTop: '1px solid #1a1a1f' }}>
                      <pre style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', color: '#a1a1aa', whiteSpace: 'pre-wrap', lineHeight: 1.6, maxHeight: '120px', overflowY: 'auto', margin: 0 }}>{stepOutputs[step.id]}</pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* ═══════ WALLET / QR CODE ═══════ */}
          {walletAddr && (
            <div data-testid="wallet-panel" style={{ background: '#0a1a0a', border: '1px solid #166534', borderRadius: '8px', padding: '20px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isLive ? '#34D399' : (isRunning || dbExists || allProvDone) ? '#FFB347' : '#71717a', boxShadow: isLive ? '0 0 8px #34D399' : 'none' }} />
                <span style={{ fontSize: '13px', fontWeight: 800, color: isLive ? '#34D399' : (isRunning || dbExists || allProvDone) ? '#FFB347' : '#71717a' }}>
                  {isLive ? 'Agent Running' :
                   allProvDone ? 'Agent Deployed — Fund Wallet to Operate' :
                   isRunning && isSleeping ? 'Agent Sleeping — Send USDC to wake' :
                   isRunning && isCritical ? 'Agent Active — Credits Low' :
                   isRunning ? 'Engine Running' :
                   'Wallet Created — Continue Provisioning'}
                </span>
              </div>

              {/* QR Code */}
              <div style={{ textAlign: 'center', marginBottom: '14px' }}>
                <img
                  src={qrCode || `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(walletAddr)}&bgcolor=0a1a0a&color=34D399`}
                  alt="Wallet QR"
                  style={{ width: '160px', height: '160px', borderRadius: '8px', border: '2px solid #27272a' }}
                  data-testid="wallet-qr"
                />
                <div style={{ fontSize: '9px', color: '#71717a', marginTop: '4px' }}>Scan to send USDC on Base</div>
              </div>

              {/* Wallet address */}
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '1px', marginBottom: '3px' }}>AGENT WALLET</div>
                <div data-testid="wallet-address" style={{ background: '#18181b', borderRadius: '6px', padding: '10px', fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', color: '#fff', wordBreak: 'break-all', border: '1px solid #27272a', cursor: 'pointer' }}
                  onClick={() => { navigator.clipboard.writeText(walletAddr); toast.success('Copied'); }}>
                  {walletAddr}
                </div>
              </div>

              {/* Status */}
              <div style={{ fontSize: '10px', color: '#71717a', lineHeight: 1.8 }}>
                <div>Engine: <span style={{ color: isLive ? '#34D399' : (isRunning || dbExists) ? '#FFB347' : '#71717a' }}>{isLive ? `LIVE (${genesisState?.turn_count || 0} turns)` : isRunning ? 'Running' : allProvDone ? 'Deployed in Sandbox' : dbExists ? 'Configured' : 'Pending'}</span></div>
                {genesisState?.engine_state && <div>State: {genesisState.engine_state}</div>}
              </div>
            </div>
          )}

          {/* Engine Console */}
          {(isRunning || engineStarted || allProvDone) && (
            <div style={{ marginBottom: '12px' }}>
              <EngineConsole isRunning={isRunning || engineStarted} />
            </div>
          )}

          {/* Creator wallets */}
          {genesisState?.creator_wallet && (
            <div style={{ background: '#18181b', border: '1px solid #27272a', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
              <div style={{ fontSize: '9px', color: '#71717a', fontWeight: 700, letterSpacing: '1px', marginBottom: '2px' }}>CREATOR WALLETS (50% net revenue)</div>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#FFB347', wordBreak: 'break-all', marginBottom: '4px' }}>SOL: {genesisState?.creator_wallet}</div>
              <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', color: '#5B9CFF', wordBreak: 'break-all' }}>ETH: {genesisState?.creator_eth_address || 'Not configured'}</div>
            </div>
          )}

          {/* Open Dashboard button */}
          <button data-testid="go-to-dashboard-btn" onClick={() => { setCurrentPage('animavm'); setView('dashboard'); }}
            style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #27272a', background: 'transparent', color: '#fff', fontSize: '13px', fontWeight: 800, cursor: 'pointer', marginBottom: '8px' }}>
            Open Dashboard
          </button>
        </div>
      </div>
    );
  }

  // ═══════════════════════════════════════════
  // DASHBOARD
  // ═══════════════════════════════════════════
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
