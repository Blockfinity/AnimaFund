import React, { useState, useEffect } from 'react';
import { X, Loader2, Search, Check } from 'lucide-react';

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
  const [includeConway, setIncludeConway] = useState(true);
  const [allSkills, setAllSkills] = useState([]);
  const [selectedSkills, setSelectedSkills] = useState(new Set());
  const [skillSearch, setSkillSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API}/api/skills/available`).then(r => r.json()).then(d => {
      setAllSkills(d.skills || []);
      // Select all by default
      setSelectedSkills(new Set((d.skills || []).map(s => s.name)));
    }).catch(() => {});
  }, []);

  const toggleSkill = (name) => {
    setSelectedSkills(prev => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  const selectAll = () => setSelectedSkills(new Set(allSkills.map(s => s.name)));
  const selectNone = () => setSelectedSkills(new Set());

  const filteredSkills = allSkills.filter(s =>
    !skillSearch || s.name.toLowerCase().includes(skillSearch.toLowerCase()) || (s.description || '').toLowerCase().includes(skillSearch.toLowerCase())
  );

  const handleCreate = async () => {
    if (!name.trim() || !prompt.trim()) { setError('Name and genesis prompt are required'); return; }
    if (!tgBotToken.trim() || !tgChatId.trim()) { setError('Telegram Bot Token and Chat ID are required for each agent'); return; }
    setLoading(true);
    setError('');
    setStatus('Verifying Telegram bot connection...');

    // Step 1: Verify Telegram bot is reachable
    try {
      const verifyRes = await fetch(`https://api.telegram.org/bot${tgBotToken.trim()}/getMe`);
      const verifyData = await verifyRes.json();
      if (!verifyData.ok) {
        setError(`Telegram bot verification failed: ${verifyData.description || 'Invalid token'}. Get a valid token from @BotFather.`);
        setLoading(false); setStatus(''); return;
      }
      setStatus(`Bot verified: @${verifyData.result.username}. Testing chat delivery...`);
    } catch {
      setError('Could not connect to Telegram API. Check your bot token.');
      setLoading(false); setStatus(''); return;
    }

    // Step 2: Verify chat ID by sending a test message
    try {
      const chatRes = await fetch(`https://api.telegram.org/bot${tgBotToken.trim()}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: tgChatId.trim(), text: `Agent "${name.trim()}" is being created on Anima Fund. Telegram connection verified.` }),
      });
      const chatData = await chatRes.json();
      if (!chatData.ok) {
        setError(`Telegram chat verification failed: ${chatData.description || 'Invalid chat ID'}. Start the bot first and verify the Chat ID.`);
        setLoading(false); setStatus(''); return;
      }
      setStatus('Telegram verified! Creating agent...');
    } catch {
      setError('Could not send test message. Check your Chat ID.');
      setLoading(false); setStatus(''); return;
    }

    // Step 3: Create the agent
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
          include_conway: includeConway,
          selected_skills: [...selectedSkills],
        }),
      });
      const data = await res.json();
      if (data.success) {
        setStatus('Starting engine...');
        const startRes = await fetch(`${API}/api/agents/${data.agent.agent_id}/start`, { method: 'POST' });
        const startData = await startRes.json();
        if (startData.success) {
          setStatus('Engine started! Wallet generating...');
          setTimeout(() => onCreated(data.agent), 1500);
        } else {
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
      <div data-testid="create-agent-modal" className="bg-white rounded-lg border border-border w-full max-w-2xl shadow-xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
          <h2 className="font-heading text-base font-semibold text-foreground">Create New Agent</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-5 space-y-4 overflow-y-auto flex-1">
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
              placeholder="Your personal message to the agent on first boot..."
              rows={2} className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground resize-y" />
          </div>

          {/* Genesis Prompt */}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">Genesis Prompt *</label>
            <textarea data-testid="agent-prompt-input" value={prompt} onChange={(e) => setPrompt(e.target.value)}
              placeholder="Define this agent's mission, personality, strategy, and instructions..."
              rows={8} className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground font-mono resize-y" />
          </div>

          {/* Goals */}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">Initial Goals (one per line)</label>
            <textarea data-testid="agent-goals-input" value={goals} onChange={(e) => setGoals(e.target.value)}
              placeholder={"Make $5K in the first hour\nInstall OpenClaw\nFind 3 AI agents to partner with"}
              rows={3} className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground resize-y" />
          </div>

          {/* Conway Prompt Toggle */}
          <div className="border-t border-border pt-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input data-testid="agent-conway-toggle" type="checkbox" checked={includeConway} onChange={(e) => setIncludeConway(e.target.checked)}
                className="w-4 h-4 rounded accent-foreground cursor-pointer" />
              <div>
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Include Conway Terminal Tools</span>
                <p className="text-[9px] text-muted-foreground mt-0.5">
                  {includeConway
                    ? 'Agent will have access to 35 Conway tools: sandboxes, domains, payments, credits, inference.'
                    : 'Conway tools will be removed from the genesis prompt. Agent will only use OpenClaw and custom skills.'}
                </p>
              </div>
            </label>
          </div>

          {/* Telegram Bot — REQUIRED */}
          <div className="border-t border-border pt-4">
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-2">Telegram Bot *</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] text-muted-foreground block mb-1">Bot Token *</label>
                <input data-testid="agent-tg-token-input" value={tgBotToken} onChange={(e) => setTgBotToken(e.target.value)}
                  placeholder="123456:ABC-DEF..." className={`w-full px-3 py-2 text-xs border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground font-mono ${!tgBotToken.trim() && name.trim() ? 'border-red-400' : 'border-border'}`} />
              </div>
              <div>
                <label className="text-[10px] text-muted-foreground block mb-1">Chat ID *</label>
                <input data-testid="agent-tg-chatid-input" value={tgChatId} onChange={(e) => setTgChatId(e.target.value)}
                  placeholder="123456789" className={`w-full px-3 py-2 text-xs border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground font-mono ${!tgChatId.trim() && name.trim() ? 'border-red-400' : 'border-border'}`} />
              </div>
            </div>
            <p className="text-[9px] text-muted-foreground mt-1">Each agent MUST have its own Telegram bot for isolated reporting. Create one via <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" className="text-foreground underline">@BotFather</a>.</p>
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

          {/* Skill Selector */}
          <div className="border-t border-border pt-4">
            <div className="flex items-center justify-between mb-2">
              <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Skills ({selectedSkills.size}/{allSkills.length} selected)</label>
              <div className="flex gap-2">
                <button data-testid="skills-select-all" onClick={selectAll} className="text-[10px] text-foreground hover:underline">Select All</button>
                <button data-testid="skills-select-none" onClick={selectNone} className="text-[10px] text-muted-foreground hover:underline">None</button>
              </div>
            </div>
            <div className="relative mb-2">
              <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-muted-foreground" />
              <input data-testid="skills-search" value={skillSearch} onChange={(e) => setSkillSearch(e.target.value)}
                placeholder="Search skills..." className="w-full pl-8 pr-3 py-1.5 text-xs border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground" />
            </div>
            <div className="max-h-40 overflow-y-auto border border-border rounded-md divide-y divide-border">
              {filteredSkills.map(s => (
                <div key={s.name} onClick={() => toggleSkill(s.name)}
                  className="flex items-center gap-2.5 px-3 py-1.5 hover:bg-secondary/30 cursor-pointer text-xs select-none"
                  data-testid={`skill-item-${s.name}`}>
                  <div className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 transition-colors ${selectedSkills.has(s.name) ? 'bg-foreground border-foreground' : 'border-border'}`}>
                    {selectedSkills.has(s.name) && <Check className="w-3 h-3 text-background" />}
                  </div>
                  <div className="min-w-0 flex items-center gap-1.5 flex-1">
                    <span className="font-medium text-foreground">{s.name}</span>
                    {s.source && s.source !== 'anima' && (
                      <span className={`text-[8px] px-1 py-0.5 rounded-sm font-bold flex-shrink-0 ${
                        s.source.startsWith('conway') ? 'bg-blue-500/15 text-blue-400' :
                        s.source === 'openclaw' ? 'bg-purple-500/15 text-purple-400' :
                        s.source === 'clawhub' ? 'bg-amber-500/15 text-amber-400' :
                        s.source === 'mcp' ? 'bg-cyan-500/15 text-cyan-400' :
                        'bg-emerald-500/15 text-emerald-400'
                      }`}>
                        {s.source.startsWith('conway') ? s.source.replace('conway-', '').toUpperCase() :
                         s.source.toUpperCase()}
                      </span>
                    )}
                    {s.installed === false && (
                      <span className="text-[8px] px-1 py-0.5 rounded-sm font-bold bg-zinc-500/15 text-zinc-400 flex-shrink-0">MARKETPLACE</span>
                    )}
                  </div>
                </div>
              ))}
              {filteredSkills.length === 0 && <div className="px-3 py-4 text-xs text-muted-foreground text-center">No skills match your search</div>}
            </div>
          </div>

          {error && <p className="text-xs text-red-600">{error}</p>}
          {status && !error && <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="w-3 h-3 animate-spin" />{status}</div>}
        </div>
        <div className="flex justify-end gap-3 px-5 py-4 border-t border-border flex-shrink-0">
          <button onClick={onClose} className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors">Cancel</button>
          <button data-testid="create-agent-submit" onClick={handleCreate}
            disabled={loading || !name.trim() || !prompt.trim() || !tgBotToken.trim() || !tgChatId.trim()}
            className="px-4 py-2 text-sm bg-foreground text-background rounded-md hover:bg-foreground/90 transition-colors disabled:opacity-50">
            {loading ? 'Creating & Starting...' : 'Create & Start Agent'}
          </button>
        </div>
      </div>
    </div>
  );
}
