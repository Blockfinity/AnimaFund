import React, { useState, useEffect } from 'react';
import { Shield, Cpu } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Configuration({ identity, engineState, genesisState }) {
  const [constitution, setConstitution] = useState('');
  const [engineStatus, setEngineStatus] = useState(null);
  const [activeTab, setActiveTab] = useState('engine');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [constRes, engRes] = await Promise.all([
          fetch(`${API}/api/constitution`),
          fetch(`${API}/api/engine/status`),
        ]);
        setConstitution((await constRes.json()).content || '');
        setEngineStatus(await engRes.json());
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    fetchAll();
  }, []);

  const isLive = engineState?.live || false;

  if (loading) {
    return <div data-testid="config-loading" className="flex items-center justify-center h-64">
      <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
    </div>;
  }

  return (
    <div data-testid="config-page" className="space-y-4 animate-slide-in">
      {/* Tabs */}
      <div className="flex items-center gap-1 bg-white border border-border rounded-sm p-1">
        <TabBtn id="engine" label="Engine" icon={Cpu} active={activeTab} onClick={setActiveTab} />
        <TabBtn id="constitution" label="Constitution" icon={Shield} active={activeTab} onClick={setActiveTab} />
      </div>

      {/* Engine */}
      {activeTab === 'engine' && (
        <div className="space-y-4">
          {/* Status */}
          <div className="bg-white border border-border rounded-sm p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-heading font-semibold text-foreground">{identity?.name || 'Anima Fund'}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">v{engineStatus?.version || '?'} | Genesis: {engineStatus?.genesis_prompt_lines || 0} lines</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-sm ${isLive ? 'bg-success/10 text-success' : 'bg-muted text-muted-foreground'}`}>
                  {isLive ? 'RUNNING' : 'OFFLINE'}
                </span>
              </div>
            </div>

            {/* Read-only info */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <InfoRow label="Agent Wallet" value={identity?.address || genesisState?.wallet_address || '—'} mono />
              <InfoRow label="Sandbox" value={identity?.sandbox || '—'} mono />
              <InfoRow label="Creator Wallet" value={engineStatus?.creator_wallet || '—'} mono />
              <InfoRow label="Engine State" value={engineState?.agent_state || 'offline'} />
              <InfoRow label="Turns" value={engineState?.turn_count || 0} />
              <InfoRow label="Fund Name" value={identity?.name || 'Not set yet'} />
            </div>

            {/* Skills */}
            {engineStatus?.skills?.length > 0 && (
              <div>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-2">Installed Skills</span>
                <div className="flex flex-wrap gap-2">
                  {engineStatus.skills.map(s => (
                    <span key={s} className="text-[10px] font-mono px-2 py-1 bg-secondary rounded-sm text-foreground">{s}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Constitution — read-only */}
      {activeTab === 'constitution' && (
        <div className="bg-white border border-border rounded-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-foreground" />
            <h3 className="text-sm font-medium text-foreground">Constitution</h3>
            <span className="text-[10px] px-2 py-0.5 bg-error/10 text-error rounded-sm font-semibold">IMMUTABLE</span>
          </div>
          <div className="font-mono text-xs leading-relaxed whitespace-pre-wrap text-foreground bg-secondary p-4 rounded-sm max-h-[500px] overflow-y-auto" data-testid="constitution-content">
            {constitution}
          </div>
        </div>
      )}
    </div>
  );
}

function TabBtn({ id, label, icon: Icon, active, onClick }) {
  return (
    <button data-testid={`config-tab-${id}`} onClick={() => onClick(id)}
      className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
        active === id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
      <Icon className="w-4 h-4" />{label}
    </button>
  );
}

function InfoRow({ label, value, mono }) {
  return (
    <div>
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</span>
      <p className={`text-sm mt-0.5 ${mono ? 'font-mono text-xs break-all' : ''} text-foreground`}>{value}</p>
    </div>
  );
}
