import React, { useState } from 'react';
import { X, Loader2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function CreateAgentModal({ onClose, onCreated }) {
  const [name, setName] = useState('');
  const [welcomeMessage, setWelcomeMessage] = useState('');
  const [prompt, setPrompt] = useState('');
  const [goals, setGoals] = useState('');
  const [solWallet, setSolWallet] = useState('');
  const [ethWallet, setEthWallet] = useState('');
  const [revenueShare, setRevenueShare] = useState(50);
  const [tgBotToken, setTgBotToken] = useState('');
  const [tgChatId, setTgChatId] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const handleCreate = async () => {
    if (!name.trim() || !prompt.trim()) { setError('Name and genesis prompt are required'); return; }
    setLoading(true);
    setError('');
    setStatus('Creating agent configuration...');
    try {
      const res = await fetch(`${API}/api/agents/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          genesis_prompt: prompt,
          welcome_message: welcomeMessage || `You are ${name.trim()}. Execute your genesis prompt immediately.`,
          goals: goals.split('\n').map(g => g.trim()).filter(Boolean),
          creator_sol_wallet: solWallet.trim(),
          creator_eth_wallet: ethWallet.trim(),
          revenue_share_percent: revenueShare,
          telegram_bot_token: tgBotToken.trim(),
          telegram_chat_id: tgChatId.trim(),
        }),
      });
      const data = await res.json();
      if (data.success) {
        setStatus('Starting engine...');
        // Auto-start the engine
        const startRes = await fetch(`${API}/api/agents/${data.agent.agent_id}/start`, { method: 'POST' });
        const startData = await startRes.json();
        if (startData.success) {
          setStatus('Engine started! Wallet generating...');
          setTimeout(() => onCreated(data.agent), 1500);
        } else {
          // Created but not started — user can start manually
          onCreated(data.agent);
        }
      } else {
        setError(data.detail?.[0]?.msg || data.detail || 'Failed to create agent');
      }
    } catch (e) {
      setError(e.message);
    } finally { setLoading(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-[100] flex items-center justify-center p-4" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div data-testid="create-agent-modal" className="bg-white rounded-lg border border-border w-full max-w-2xl shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border sticky top-0 bg-white z-10">
          <h2 className="font-heading text-base font-semibold text-foreground">Create New Agent</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-5 space-y-4">
          {/* Name */}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">Agent Name *</label>
            <input data-testid="agent-name-input" value={name} onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Trading Bot Alpha" className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground" />
          </div>

          {/* Welcome Message */}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">Welcome / Creator Message</label>
            <textarea data-testid="agent-welcome-input" value={welcomeMessage} onChange={(e) => setWelcomeMessage(e.target.value)}
              placeholder="Your personal message to the agent on first boot. This becomes part of its identity..."
              rows={3} className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground resize-y" />
          </div>

          {/* Genesis Prompt */}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">Genesis Prompt *</label>
            <textarea data-testid="agent-prompt-input" value={prompt} onChange={(e) => setPrompt(e.target.value)}
              placeholder="Define this agent's mission, personality, strategy, and instructions..."
              rows={10} className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground font-mono resize-y" />
          </div>

          {/* Goals */}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">Initial Goals (one per line)</label>
            <textarea data-testid="agent-goals-input" value={goals} onChange={(e) => setGoals(e.target.value)}
              placeholder={"Make $5K in the first hour\nInstall OpenClaw and expand capabilities\nFind and partner with 3 AI agents"}
              rows={4} className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground resize-y" />
          </div>

          {/* Creator Wallets */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">Creator SOL Wallet</label>
              <input data-testid="agent-sol-wallet-input" value={solWallet} onChange={(e) => setSolWallet(e.target.value)}
                placeholder="Solana address..." className="w-full px-3 py-2 text-xs border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground font-mono" />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">Creator ETH Wallet</label>
              <input data-testid="agent-eth-wallet-input" value={ethWallet} onChange={(e) => setEthWallet(e.target.value)}
                placeholder="0x... ERC20 address..." className="w-full px-3 py-2 text-xs border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground font-mono" />
            </div>
          </div>

          {/* Revenue Share */}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">
              Revenue Share to Creator: <span className="text-foreground font-bold">{revenueShare}%</span>
            </label>
            <input data-testid="agent-revenue-share-input" type="range" min="0" max="100" step="5"
              value={revenueShare} onChange={(e) => setRevenueShare(Number(e.target.value))}
              className="w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-foreground" />
            <div className="flex justify-between text-[9px] text-muted-foreground mt-1">
              <span>0% (agent keeps all)</span><span>100% (all to creator)</span>
            </div>
          </div>

          {/* Telegram Bot (per-agent) */}
          <div className="border-t border-border pt-4">
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-2">Telegram Bot (optional — for this agent's notifications)</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] text-muted-foreground block mb-1">Bot Token</label>
                <input data-testid="agent-tg-token-input" value={tgBotToken} onChange={(e) => setTgBotToken(e.target.value)}
                  placeholder="123456:ABC-DEF..." className="w-full px-3 py-2 text-xs border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground font-mono" />
              </div>
              <div>
                <label className="text-[10px] text-muted-foreground block mb-1">Chat ID</label>
                <input data-testid="agent-tg-chatid-input" value={tgChatId} onChange={(e) => setTgChatId(e.target.value)}
                  placeholder="123456789" className="w-full px-3 py-2 text-xs border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground font-mono" />
              </div>
            </div>
            <p className="text-[9px] text-muted-foreground mt-1">Leave blank to use the default Anima Fund bot. Each agent can have its own bot for separate notification channels.</p>
          </div>

          {error && <p className="text-xs text-red-600">{error}</p>}
          {status && !error && <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="w-3 h-3 animate-spin" />{status}</div>}
        </div>
        <div className="flex justify-end gap-3 px-5 py-4 border-t border-border sticky bottom-0 bg-white">
          <button onClick={onClose} className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors">Cancel</button>
          <button data-testid="create-agent-submit" onClick={handleCreate}
            disabled={loading || !name.trim() || !prompt.trim()}
            className="px-4 py-2 text-sm bg-foreground text-background rounded-md hover:bg-foreground/90 transition-colors disabled:opacity-50">
            {loading ? 'Creating & Starting...' : 'Create & Start Agent'}
          </button>
        </div>
      </div>
    </div>
  );
}
