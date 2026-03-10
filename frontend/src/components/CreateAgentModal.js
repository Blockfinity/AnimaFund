import React, { useState, useEffect } from 'react';
import { X, Loader2, Search, ChevronDown, ChevronUp } from 'lucide-react';

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
  const [skillFilter, setSkillFilter] = useState('');
  const [showSkills, setShowSkills] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [templateLoaded, setTemplateLoaded] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/skills/available`).then(r => r.json()).then(d => {
      setAllSkills(d.skills || []);
    }).catch(() => {});
  }, []);

  const loadTemplate = async () => {
    try {
      const res = await fetch(`${API}/api/genesis/prompt-template`);
      if (res.ok) {
        const data = await res.json();
        setPrompt(data.content || '');
        setTemplateLoaded(true);
      }
    } catch {}
  };

  const toggleSkill = (name) => {
    setSelectedSkills(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
  };

  const filteredSkills = allSkills.filter(s =>
    s.name.toLowerCase().includes(skillFilter.toLowerCase()) ||
    (s.description || '').toLowerCase().includes(skillFilter.toLowerCase())
  );

  const handleCreate = async () => {
    if (!name.trim() || !prompt.trim()) { setError('Name and genesis prompt are required'); return; }
    if (!tgBotToken.trim() || !tgChatId.trim()) { setError('Telegram Bot Token and Chat ID are required for each agent'); return; }
    setLoading(true);
    setError('');
    setStatus('Verifying Telegram bot connection...');

    // Step 1: Verify bot token
    try {
      const verifyRes = await fetch(`https://api.telegram.org/bot${tgBotToken.trim()}/getMe`);
      const verifyData = await verifyRes.json();
      if (!verifyData.ok) {
        setError(`Telegram bot verification failed: ${verifyData.description || 'Invalid token'}.`);
        setLoading(false); setStatus(''); return;
      }
      setStatus(`Bot verified: @${verifyData.result.username}. Testing chat...`);
    } catch {
      setError('Could not connect to Telegram API. Check your bot token.');
      setLoading(false); setStatus(''); return;
    }

    // Step 2: Verify chat ID
    try {
      const chatRes = await fetch(`https://api.telegram.org/bot${tgBotToken.trim()}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: tgChatId.trim(), text: `Agent "${name.trim()}" is being created. Telegram verified.` }),
      });
      const chatData = await chatRes.json();
      if (!chatData.ok) {
        setError(`Chat verification failed: ${chatData.description}. Start the bot first.`);
        setLoading(false); setStatus(''); return;
      }
      setStatus('Telegram verified! Creating agent...');
    } catch {
      setError('Could not send test message. Check your Chat ID.');
      setLoading(false); setStatus(''); return;
    }

    // Step 3: Create agent — selected skills go into genesis prompt as priority list
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
        setStatus('Agent created! Redirecting to Anima VM for provisioning...');
        setTimeout(() => onCreated(data.agent), 1000);
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
            <div className="flex items-center justify-between mb-1">
              <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Genesis Prompt *</label>
              <button data-testid="load-template-btn" onClick={loadTemplate} type="button"
                className="text-[10px] px-2 py-0.5 rounded border border-border text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors">
                {templateLoaded ? 'Template Loaded' : 'Load Standard Template'}
              </button>
            </div>
            <textarea data-testid="agent-prompt-input" value={prompt} onChange={(e) => setPrompt(e.target.value)}
              placeholder="Define this agent's mission, personality, strategy, and instructions..."
              rows={8} className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground font-mono resize-y" />
          </div>

          {/* Goals */}
          <div>
            <label className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium block mb-1">Initial Goals (one per line)</label>
            <textarea data-testid="agent-goals-input" value={goals} onChange={(e) => setGoals(e.target.value)}
              placeholder={"Install OpenClaw and verify browser works\nDiscover and install trading skills from ClawHub\nGenerate $5K revenue in first 3 hours"}
              rows={3} className="w-full px-3 py-2 text-sm border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-foreground resize-y" />
          </div>

          {/* Priority Skills Selector */}
          <div className="border-t border-border pt-4">
            <button data-testid="toggle-skills-selector" type="button" onClick={() => setShowSkills(!showSkills)}
              className="flex items-center justify-between w-full text-left">
              <div>
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">
                  Priority Skills {selectedSkills.size > 0 && <span className="text-foreground">({selectedSkills.size} selected)</span>}
                </span>
                <p className="text-[9px] text-muted-foreground mt-0.5">
                  Skills the agent should search for and install FIRST from ClawHub. The agent discovers and installs these autonomously.
                </p>
              </div>
              {showSkills ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
            </button>
            {showSkills && (
              <div className="mt-2 border border-border rounded-md">
                <div className="p-2 border-b border-border flex items-center gap-2">
                  <Search className="w-3 h-3 text-muted-foreground" />
                  <input data-testid="skills-search-input" value={skillFilter} onChange={(e) => setSkillFilter(e.target.value)}
                    placeholder="Search skills..." className="w-full text-xs bg-transparent focus:outline-none" />
                  <button type="button" onClick={() => { if (selectedSkills.size === allSkills.length) setSelectedSkills(new Set()); else setSelectedSkills(new Set(allSkills.map(s => s.name))); }}
                    className="text-[9px] text-muted-foreground hover:text-foreground whitespace-nowrap">
                    {selectedSkills.size === allSkills.length ? 'Clear All' : 'Select All'}
                  </button>
                </div>
                <div className="max-h-40 overflow-y-auto p-1">
                  {filteredSkills.map(skill => (
                    <label key={skill.name} className="flex items-center gap-2 px-2 py-1 rounded hover:bg-secondary/50 cursor-pointer">
                      <input type="checkbox" checked={selectedSkills.has(skill.name)} onChange={() => toggleSkill(skill.name)}
                        className="w-3 h-3 rounded accent-foreground cursor-pointer" />
                      <span className="text-[10px] text-foreground flex-1">{skill.name}</span>
                      <span className="text-[8px] text-muted-foreground">{skill.source}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Conway Toggle */}
          <div className="border-t border-border pt-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input data-testid="agent-conway-toggle" type="checkbox" checked={includeConway} onChange={(e) => setIncludeConway(e.target.checked)}
                className="w-4 h-4 rounded accent-foreground cursor-pointer" />
              <div>
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Include Conway Terminal Tools</span>
                <p className="text-[9px] text-muted-foreground mt-0.5">
                  {includeConway
                    ? 'Agent will have Conway tools reference: sandboxes, domains, payments, credits, inference.'
                    : 'Conway tools will be removed from the genesis prompt.'}
                </p>
              </div>
            </label>
          </div>

          {/* Telegram */}
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
            <p className="text-[9px] text-muted-foreground mt-1">Each agent MUST have its own Telegram bot. Create one via <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" className="text-foreground underline">@BotFather</a>.</p>
          </div>

          {/* Wallets */}
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
          </div>

          {error && <p data-testid="create-agent-error" className="text-xs text-red-600">{error}</p>}
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
