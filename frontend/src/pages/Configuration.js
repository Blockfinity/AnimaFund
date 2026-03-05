import React, { useState, useEffect } from 'react';
import { Shield, FileText, Cpu, Settings as SettingsIcon, ExternalLink } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Configuration() {
  const [constitution, setConstitution] = useState('');
  const [config, setConfig] = useState(null);
  const [engineStatus, setEngineStatus] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [activeTab, setActiveTab] = useState('engine');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [constRes, confRes, engRes, deptRes] = await Promise.all([
          fetch(`${API}/api/constitution`),
          fetch(`${API}/api/config`),
          fetch(`${API}/api/engine/status`),
          fetch(`${API}/api/departments`),
        ]);
        const [constData, confData, engData, deptData] = await Promise.all([
          constRes.json(), confRes.json(), engRes.json(), deptRes.json(),
        ]);
        setConstitution(constData.content || '');
        setConfig(confData);
        setEngineStatus(engData);
        setDepartments(deptData.departments || []);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const tabs = [
    { id: 'engine', label: 'Engine Status', icon: Cpu },
    { id: 'constitution', label: 'Constitution', icon: Shield },
    { id: 'fund', label: 'Fund Config', icon: SettingsIcon },
    { id: 'departments', label: 'Departments', icon: FileText },
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
            <button
              key={tab.id}
              data-testid={`config-tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium transition-colors ${
                activeTab === tab.id ? 'bg-foreground text-white' : 'text-muted-foreground hover:text-foreground hover:bg-secondary'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      {activeTab === 'engine' && engineStatus && (
        <div className="bg-white border border-border rounded-sm p-5 space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-heading font-semibold text-foreground">{engineStatus.engine}</h3>
              <p className="text-xs text-muted-foreground mt-0.5">Version {engineStatus.version} | {engineStatus.runtime}</p>
            </div>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-sm ${engineStatus.repo_present ? 'bg-success/10 text-success' : 'bg-error/10 text-error'}`}>
              {engineStatus.repo_present ? 'REPO CLONED' : 'NOT FOUND'}
            </span>
          </div>
          
          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Base Repository</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-sm font-mono text-foreground">{engineStatus.base_repo}</span>
              <a href="https://github.com/Conway-Research/automaton" target="_blank" rel="noopener noreferrer" className="text-chart-primary hover:underline">
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Infrastructure</span>
            <p className="text-sm text-foreground mt-1">{engineStatus.infrastructure}</p>
          </div>

          <div>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2 block">Capabilities</span>
            <div className="flex flex-wrap gap-2">
              {engineStatus.features.map(f => (
                <span key={f} className="text-[10px] font-mono px-2 py-1 bg-secondary rounded-sm text-foreground">{f}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'constitution' && (
        <div className="bg-white border border-border rounded-sm p-5">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-foreground" />
            <h3 className="text-sm font-medium text-foreground">Anima Fund Constitution</h3>
            <span className="text-[10px] px-2 py-0.5 bg-error/10 text-error rounded-sm font-semibold">IMMUTABLE</span>
          </div>
          <div className="font-mono text-xs leading-relaxed whitespace-pre-wrap text-foreground bg-secondary p-4 rounded-sm max-h-[500px] overflow-y-auto" data-testid="constitution-content">
            {constitution}
          </div>
        </div>
      )}

      {activeTab === 'fund' && config && (
        <div className="bg-white border border-border rounded-sm p-5">
          <h3 className="text-sm font-medium text-foreground mb-4">Fund Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ConfigItem label="Fund Name" value={config.fund_name} />
            <ConfigItem label="Thesis" value={config.thesis} />
            <ConfigItem label="Management Fee" value={`${config.management_fee}%`} />
            <ConfigItem label="Carried Interest" value={`${config.carried_interest}%`} />
            <ConfigItem label="Human Carry Share" value={`${config.human_carry_share}%`} />
            <ConfigItem label="Target AUM" value={`$${(config.target_aum / 1000000000).toFixed(1)}B`} />
            <ConfigItem label="Current AUM" value={`$${(config.current_aum / 1000000).toFixed(1)}M`} />
            <ConfigItem label="Rejection Rate" value={`${config.rejection_rate}%`} />
            <ConfigItem label="USDC Balance" value={`$${config.usdc_balance?.toLocaleString()}`} />
            <ConfigItem label="Conway Credits" value={`$${config.conway_credits?.toLocaleString()}`} />
            <ConfigItem label="Survival Tier" value={config.survival_tier?.toUpperCase()} />
            <ConfigItem label="Reviews/Year Target" value={config.reviews_per_year} />
          </div>
          <div className="mt-4 pt-4 border-t border-border">
            <ConfigItem label="Founder Wallet" value={config.founder_wallet} mono />
            <ConfigItem label="Human Wallet" value={config.human_wallet} mono />
          </div>
        </div>
      )}

      {activeTab === 'departments' && (
        <div className="bg-white border border-border rounded-sm overflow-hidden">
          <table className="w-full" data-testid="departments-table">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Department</th>
                <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Head</th>
                <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Current</th>
                <th className="text-right text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Target</th>
                <th className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-3">Fill</th>
              </tr>
            </thead>
            <tbody>
              {departments.map((dept, i) => {
                const fill = Math.min(100, (dept.current_count / dept.target_min) * 100);
                return (
                  <tr key={dept.name} className="border-b border-border last:border-0 hover:bg-secondary/50 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-foreground">{dept.name}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{dept.head}</td>
                    <td className="px-4 py-3 text-xs font-mono text-foreground text-right">{dept.current_count}</td>
                    <td className="px-4 py-3 text-xs font-mono text-muted-foreground text-right">{dept.target_min}-{dept.target_max}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-1.5 bg-secondary rounded-full overflow-hidden">
                          <div 
                            className="h-full rounded-full transition-all" 
                            style={{ 
                              width: `${fill}%`,
                              backgroundColor: fill >= 80 ? '#16a34a' : fill >= 40 ? '#d97706' : '#ef4444'
                            }}
                          />
                        </div>
                        <span className="text-[10px] font-mono text-muted-foreground">{fill.toFixed(0)}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ConfigItem({ label, value, mono = false }) {
  return (
    <div className="py-2">
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</span>
      <p className={`text-sm mt-0.5 ${mono ? 'font-mono text-xs break-all' : 'font-medium'} text-foreground`}>{value || 'N/A'}</p>
    </div>
  );
}
