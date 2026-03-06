import React, { useState, useEffect } from 'react';
import { Shield, Cpu, ExternalLink, Globe, Terminal, Package } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Configuration({ identity }) {
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
        const [constData, engData] = await Promise.all([constRes.json(), engRes.json()]);
        setConstitution(constData.content || '');
        setEngineStatus(engData);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    fetchAll();
  }, []);

  const tabs = [
    { id: 'engine', label: 'Engine', icon: Cpu },
    { id: 'constitution', label: 'Constitution', icon: Shield },
    { id: 'services', label: 'Services', icon: Globe },
  ];

  if (loading) {
    return (
      <div data-testid="config-loading" className="flex items-center justify-center h-64">
        <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div data-testid="config-page" className="space-y-4 animate-slide-in">
      {/* Tabs */}
      <div className="flex items-center gap-1 bg-white border border-border rounded-sm p-1">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} data-testid={`config-tab-${tab.id}`} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                activeTab === tab.id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'}`}>
              <Icon className="w-4 h-4" />{tab.label}
            </button>
          );
        })}
      </div>

      {/* Engine Status */}
      {activeTab === 'engine' && engineStatus && (
        <div className="bg-white border border-border rounded-sm p-5 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-heading font-semibold text-foreground">{identity?.name || engineStatus.engine}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">v{engineStatus.version} | Genesis: {engineStatus.genesis_prompt_lines} lines</p>
            </div>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-sm ${engineStatus.built ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>
              {engineStatus.built ? 'BUILT' : 'NOT BUILT'}
            </span>
          </div>

          {identity?.address && (
            <div>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Agent Wallet</span>
              <p className="text-xs font-mono text-foreground mt-1 break-all">{identity.address}</p>
            </div>
          )}

          {identity?.sandbox && (
            <div>
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Sandbox</span>
              <p className="text-xs font-mono text-foreground mt-1">{identity.sandbox}</p>
            </div>
          )}

          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Creator Wallet (Solana)</span>
            <p className="text-xs font-mono text-foreground mt-1 break-all">{engineStatus.creator_wallet}</p>
          </div>

          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2 block">Skills</span>
            <div className="flex flex-wrap gap-2">
              {engineStatus.skills?.map(s => (
                <span key={s} className="text-[10px] font-mono px-2 py-1 bg-secondary rounded-sm text-foreground">{s}</span>
              ))}
              {(!engineStatus.skills || engineStatus.skills.length === 0) && <span className="text-xs text-muted-foreground">No skills installed</span>}
            </div>
          </div>
        </div>
      )}

      {/* Constitution */}
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

      {/* Deployed Services */}
      {activeTab === 'services' && (
        <div className="space-y-4">
          {/* Domains */}
          <div className="bg-white border border-border rounded-sm p-5">
            <div className="flex items-center gap-2 mb-3">
              <Globe className="w-4 h-4 text-chart-primary" />
              <h3 className="text-sm font-medium text-foreground">Registered Domains</h3>
            </div>
            {identity?.domains?.length > 0 ? (
              <div className="space-y-2">
                {identity.domains.map((d, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                    <a href={`https://${d.domain}`} target="_blank" rel="noopener noreferrer" className="text-sm font-mono text-chart-primary hover:underline flex items-center gap-1">
                      {d.domain} <ExternalLink className="w-3 h-3" />
                    </a>
                    <span className="text-[10px] font-mono text-muted-foreground">{d.timestamp}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No domains registered yet. The agent will register domains when it's ready.</p>
            )}
          </div>

          {/* Child Sandboxes */}
          <div className="bg-white border border-border rounded-sm p-5">
            <div className="flex items-center gap-2 mb-3">
              <Terminal className="w-4 h-4 text-chart-secondary" />
              <h3 className="text-sm font-medium text-foreground">Deployed Sandboxes</h3>
            </div>
            {identity?.children_sandboxes?.length > 0 ? (
              <div className="space-y-2">
                {identity.children_sandboxes.map((c, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                    <div>
                      <span className="text-sm font-medium text-foreground">{c.name}</span>
                      <span className="text-[10px] font-mono text-muted-foreground ml-2">{c.sandbox_id}</span>
                    </div>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      c.status === 'healthy' || c.status === 'running' ? 'bg-success/10 text-success' : 'bg-muted text-muted-foreground'
                    }`}>{c.status}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No sandboxes deployed yet. The agent will spin up Conway Cloud VMs when needed.</p>
            )}
          </div>

          {/* Installed Tools */}
          <div className="bg-white border border-border rounded-sm p-5">
            <div className="flex items-center gap-2 mb-3">
              <Package className="w-4 h-4 text-chart-tertiary" />
              <h3 className="text-sm font-medium text-foreground">Installed Tools & MCP Servers</h3>
            </div>
            {identity?.installed_tools?.length > 0 ? (
              <div className="space-y-2">
                {identity.installed_tools.map((t, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                    <div>
                      <span className="text-sm font-mono text-foreground">{t.name}</span>
                      <span className="text-[10px] text-muted-foreground ml-2">{t.type}</span>
                    </div>
                    <span className={`text-[10px] font-semibold ${t.enabled ? 'text-success' : 'text-muted-foreground'}`}>
                      {t.enabled ? 'ACTIVE' : 'DISABLED'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No additional tools installed yet. The agent will install npm packages and MCP servers as needed.</p>
            )}
          </div>

          {/* Exposed Services */}
          <div className="bg-white border border-border rounded-sm p-5">
            <div className="flex items-center gap-2 mb-3">
              <ExternalLink className="w-4 h-4 text-chart-quaternary" />
              <h3 className="text-sm font-medium text-foreground">Exposed Services & Ports</h3>
            </div>
            {identity?.services?.length > 0 ? (
              <div className="space-y-2">
                {identity.services.map((s, i) => (
                  <div key={i} className="py-2 border-b border-border last:border-0">
                    <pre className="text-[10px] font-mono text-foreground bg-secondary p-2 rounded-sm overflow-x-auto whitespace-pre-wrap">
                      {s.result}
                    </pre>
                    <span className="text-[9px] text-muted-foreground">{s.timestamp}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No services exposed yet. When the agent deploys APIs, websites, or services, they'll appear here with their public URLs.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
