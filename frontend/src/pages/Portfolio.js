import React, { useState, useEffect } from 'react';
import { TrendingUp, Clock, Users, DollarSign, ArrowUpRight } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const phaseOrder = [
  'Acceptance / Onboarding',
  'Validation / Foundation',
  'Team Build / Core Build',
  'GTM / Revenue',
  'Scale / Optimization',
  'Graduation / Exit Prep',
];

const phaseColors = {
  'Acceptance / Onboarding': 'bg-chart-primary',
  'Validation / Foundation': 'bg-chart-quaternary',
  'Team Build / Core Build': 'bg-chart-tertiary',
  'GTM / Revenue': 'bg-success',
  'Scale / Optimization': 'bg-chart-primary',
  'Graduation / Exit Prep': 'bg-foreground',
};

export default function Portfolio() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/portfolio`)
      .then(r => r.json())
      .then(d => setCompanies(d.companies || []))
      .catch(e => console.error(e))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div data-testid="portfolio-loading" className="flex items-center justify-center h-64">
        <div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div data-testid="portfolio-page" className="space-y-6 animate-slide-in">
      {/* Phase Progress Bar */}
      <div className="bg-white border border-border rounded-sm p-5">
        <h3 className="text-sm font-medium text-foreground mb-4">Incubation Phases</h3>
        <div className="flex items-center gap-1">
          {phaseOrder.map((phase, i) => {
            const count = companies.filter(c => c.phase === phase).length;
            return (
              <div key={phase} className="flex-1 group relative">
                <div className={`h-8 ${phaseColors[phase]} ${i === 0 ? 'rounded-l-sm' : ''} ${i === phaseOrder.length - 1 ? 'rounded-r-sm' : ''} flex items-center justify-center transition-opacity ${count === 0 ? 'opacity-20' : ''}`}>
                  <span className="text-[10px] font-semibold text-white">{count}</span>
                </div>
                <span className="text-[9px] text-muted-foreground mt-1 block text-center truncate">{phase.split('/')[0].trim()}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Company Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {companies.map(company => {
          const multiple = company.current_valuation / company.invested_amount;
          return (
            <div 
              key={company.company_id} 
              data-testid={`portfolio-card-${company.name}`}
              className="bg-white border border-border rounded-sm p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="text-sm font-heading font-semibold text-foreground">{company.name}</h4>
                  <span className="text-xs text-muted-foreground">{company.vertical}</span>
                </div>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                  company.status === 'scaling' ? 'bg-success/10 text-success' : 'bg-chart-primary/10 text-chart-primary'
                }`}>
                  {company.status}
                </span>
              </div>

              {/* Phase */}
              <div className="mb-3">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Phase</span>
                <p className="text-xs font-medium text-foreground mt-0.5">{company.phase}</p>
              </div>

              {/* Financials */}
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Invested</span>
                  <p className="text-sm font-mono font-medium text-foreground">${(company.invested_amount / 1000).toFixed(0)}K</p>
                </div>
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Valuation</span>
                  <p className="text-sm font-mono font-medium text-foreground">${(company.current_valuation / 1000000).toFixed(2)}M</p>
                </div>
              </div>

              {/* Multiple */}
              <div className="flex items-center gap-2 mb-3 p-2 bg-secondary rounded-sm">
                <ArrowUpRight className={`w-3 h-3 ${multiple >= 3 ? 'text-success' : 'text-chart-primary'}`} />
                <span className="text-xs font-mono font-semibold">{multiple.toFixed(1)}x</span>
                <span className="text-[10px] text-muted-foreground">return multiple</span>
              </div>

              {/* KPIs */}
              <div className="grid grid-cols-2 gap-2 pt-3 border-t border-border">
                <KPIItem icon={DollarSign} label="MRR" value={`$${(company.kpis.mrr / 1000).toFixed(0)}K`} />
                <KPIItem icon={TrendingUp} label="Growth" value={`${company.kpis.growth_rate}%`} />
                <KPIItem icon={Clock} label="Runway" value={`${company.kpis.runway_months}mo`} />
                <KPIItem icon={Users} label="Team" value={company.team_size} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function KPIItem({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-1.5">
      <Icon className="w-3 h-3 text-muted-foreground" />
      <span className="text-[10px] text-muted-foreground">{label}</span>
      <span className="text-[10px] font-mono font-medium text-foreground ml-auto">{value}</span>
    </div>
  );
}
