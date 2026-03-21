import React, { useState, useEffect, useCallback } from 'react';
import { Sparkles, Play, Upload, Zap, Users, DollarSign, Target, ChevronRight, MessageSquare, Eye, Rocket, Clock, TrendingUp, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

/* ─── Phase indicator ─── */
const phases = [
  { id: 'input', label: 'Seed Input', icon: Upload },
  { id: 'simulating', label: 'Simulation', icon: Zap },
  { id: 'results', label: 'Strategy', icon: Target },
  { id: 'cost', label: 'Cost Review', icon: DollarSign },
  { id: 'execute', label: 'Execute', icon: Rocket },
];

function PhaseBar({ current }) {
  const idx = phases.findIndex(p => p.id === current);
  return (
    <div data-testid="ultimus-phase-bar" style={{ display: 'flex', gap: '2px', marginBottom: '20px', background: '#0a0f1a', borderRadius: '6px', padding: '4px' }}>
      {phases.map((p, i) => {
        const Icon = p.icon;
        const active = i <= idx;
        return (
          <div key={p.id} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 12px', borderRadius: '4px',
            background: active ? '#1e293b' : 'transparent', transition: 'all 0.2s' }}>
            <Icon size={14} style={{ color: active ? '#10b981' : '#475569' }} />
            <span style={{ fontSize: '11px', fontWeight: 600, color: active ? '#e2e8f0' : '#475569', fontFamily: 'JetBrains Mono, monospace' }}>{p.label}</span>
            {i < phases.length - 1 && <ChevronRight size={12} style={{ color: '#334155', marginLeft: 'auto' }} />}
          </div>
        );
      })}
    </div>
  );
}

/* ─── Persona Card ─── */
function PersonaCard({ persona, onClick }) {
  return (
    <div onClick={onClick} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '6px', padding: '14px', cursor: 'pointer', transition: 'border-color 0.2s' }}
      onMouseEnter={e => e.currentTarget.style.borderColor = '#10b981'} onMouseLeave={e => e.currentTarget.style.borderColor = '#334155'}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ color: '#10b981', fontSize: '12px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', textTransform: 'uppercase' }}>{persona.role}</span>
        <span style={{ color: '#64748b', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>
          {persona.actions_count || 0} actions
        </span>
      </div>
      <div style={{ color: '#e2e8f0', fontSize: '14px', fontWeight: 600, marginBottom: '4px' }}>{persona.name}</div>
      <div style={{ color: '#94a3b8', fontSize: '11px', lineHeight: 1.4, marginBottom: '8px' }}>
        {(persona.personality || '').slice(0, 80)}{(persona.personality || '').length > 80 ? '...' : ''}
      </div>
      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
        {(persona.tools || []).slice(0, 4).map((t, i) => (
          <span key={i} style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '3px', padding: '2px 6px', fontSize: '9px', color: '#94a3b8', fontFamily: 'JetBrains Mono, monospace' }}>{t}</span>
        ))}
      </div>
      <div style={{ display: 'flex', gap: '12px', marginTop: '8px', borderTop: '1px solid #334155', paddingTop: '8px' }}>
        <span style={{ color: '#10b981', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>+${(persona.revenue || 0).toFixed(2)}</span>
        <span style={{ color: '#f87171', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>-${(persona.expenses || 0).toFixed(2)}</span>
      </div>
    </div>
  );
}

/* ─── System Dashboard Panel ─── */
function SystemDashboard({ prediction }) {
  if (!prediction) return null;
  return (
    <div style={{ background: '#0a0f1a', border: '1px solid #1e293b', borderRadius: '6px', padding: '14px' }}>
      <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>System Dashboard</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <div><span style={{ color: '#475569', fontSize: '10px' }}>Status</span><div style={{ color: prediction.status === 'completed' ? '#10b981' : '#fbbf24', fontSize: '12px', fontWeight: 700 }}>{prediction.status}</div></div>
        <div><span style={{ color: '#475569', fontSize: '10px' }}>Personas</span><div style={{ color: '#e2e8f0', fontSize: '12px', fontWeight: 700 }}>{prediction.personas?.length || 0}</div></div>
        <div><span style={{ color: '#475569', fontSize: '10px' }}>Rounds</span><div style={{ color: '#e2e8f0', fontSize: '12px', fontWeight: 700 }}>{prediction.rounds_completed || 0}</div></div>
        <div><span style={{ color: '#475569', fontSize: '10px' }}>Confidence</span><div style={{ color: '#10b981', fontSize: '12px', fontWeight: 700 }}>{((prediction.strategy?.confidence_score || 0) * 100).toFixed(0)}%</div></div>
      </div>
    </div>
  );
}

/* ─── Main Ultimus Page ─── */
export default function Ultimus() {
  const [goal, setGoal] = useState('');
  const [mode, setMode] = useState('quick');
  const [numPersonas, setNumPersonas] = useState(5);
  const [numRounds, setNumRounds] = useState(3);
  const [seedCapital, setSeedCapital] = useState(10);
  const [prediction, setPrediction] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [phase, setPhase] = useState('input');
  const [selectedPersona, setSelectedPersona] = useState(null);

  const fetchPredictions = useCallback(async () => {
    try { const r = await fetch(`${API}/api/ultimus/predictions`); const d = await r.json(); setPredictions(d.predictions || []); } catch {}
  }, []);
  useEffect(() => { fetchPredictions(); }, [fetchPredictions]);

  const runPrediction = async () => {
    if (!goal.trim()) return;
    setLoading(true); setPhase('simulating');
    try {
      const r = await fetch(`${API}/api/ultimus/predict`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, mode, num_personas: numPersonas, num_rounds: numRounds, seed_capital: seedCapital }) });
      const d = await r.json();
      if (d.detail) { alert(d.detail); setPhase('input'); } else { setPrediction(d); setPhase('results'); fetchPredictions(); }
    } catch (e) { alert('Failed: ' + e.message); setPhase('input'); }
    setLoading(false);
  };

  const executePrediction = async () => {
    if (!prediction?.id) return;
    setExecuting(true); setPhase('execute');
    try {
      const r = await fetch(`${API}/api/ultimus/execute`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prediction_id: prediction.id }) });
      const d = await r.json();
      if (d.detail) alert(d.detail); else setPrediction(prev => ({ ...prev, execution: d }));
      fetchPredictions();
    } catch (e) { alert('Failed: ' + e.message); }
    setExecuting(false);
  };

  return (
    <div data-testid="ultimus-page" style={{ padding: '20px', maxWidth: '1400px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={20} style={{ color: '#10b981' }} />
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#e2e8f0', margin: 0, fontFamily: 'JetBrains Mono, monospace', letterSpacing: '-0.5px' }}>ULTIMUS</h1>
            <span style={{ background: '#064e3b', color: '#10b981', fontSize: '9px', fontWeight: 700, padding: '2px 8px', borderRadius: '3px', fontFamily: 'JetBrains Mono, monospace' }}>PREDICTION ENGINE</span>
          </div>
          <p style={{ color: '#64748b', fontSize: '12px', margin: '4px 0 0', fontFamily: 'JetBrains Mono, monospace' }}>Simulate. Calculate. Execute.</p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ color: '#475569', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>{predictions.length} predictions</span>
        </div>
      </div>

      <PhaseBar current={phase} />

      {/* ═══ PHASE: INPUT ═══ */}
      {phase === 'input' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '16px' }}>
          {/* Main input */}
          <div>
            <div data-testid="ultimus-goal-input" style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '6px', padding: '20px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                <span style={{ color: '#10b981', fontSize: '11px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>01</span>
                <span style={{ color: '#e2e8f0', fontSize: '13px', fontWeight: 600 }}>Describe your prediction goal</span>
              </div>
              <textarea data-testid="ultimus-goal-textarea" value={goal} onChange={e => setGoal(e.target.value)}
                placeholder="What do you want to predict or achieve? Describe in natural language..."
                style={{ width: '100%', minHeight: '100px', background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', padding: '12px', fontSize: '13px', resize: 'vertical', fontFamily: 'inherit' }} />
              <div style={{ display: 'flex', gap: '10px', marginTop: '12px', flexWrap: 'wrap', alignItems: 'end' }}>
                {[{ label: 'Mode', el: <select value={mode} onChange={e => setMode(e.target.value)} style={inputStyle}><option value="quick">Quick</option><option value="deep">Deep</option><option value="expert">Expert</option><option value="iterative">Iterative</option></select> },
                  { label: 'Personas', el: <input type="number" value={numPersonas} onChange={e => setNumPersonas(+e.target.value)} min={2} max={20} style={{ ...inputStyle, width: '60px' }} /> },
                  { label: 'Rounds', el: <input type="number" value={numRounds} onChange={e => setNumRounds(+e.target.value)} min={1} max={10} style={{ ...inputStyle, width: '60px' }} /> },
                  { label: 'Seed $', el: <input type="number" value={seedCapital} onChange={e => setSeedCapital(+e.target.value)} min={1} style={{ ...inputStyle, width: '80px' }} /> },
                ].map((f, i) => (
                  <div key={i}><label style={{ color: '#64748b', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', display: 'block', marginBottom: '3px' }}>{f.label}</label>{f.el}</div>
                ))}
                <button data-testid="ultimus-simulate-btn" onClick={runPrediction} disabled={loading || !goal.trim()}
                  style={{ background: loading ? '#334155' : '#10b981', color: '#fff', border: 'none', borderRadius: '4px', padding: '8px 28px', fontSize: '13px', fontWeight: 700, cursor: loading ? 'wait' : 'pointer', fontFamily: 'JetBrains Mono, monospace', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {loading ? <><Loader2 size={14} className="animate-spin" /> Simulating...</> : <><Play size={14} /> Simulate</>}
                </button>
              </div>
            </div>
            {/* Past predictions */}
            {predictions.length > 0 && (
              <div>
                <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>Past Predictions</div>
                {predictions.slice(0, 5).map((p, i) => (
                  <div key={i} onClick={() => { setPrediction(p); setPhase('results'); }}
                    style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '4px', padding: '10px 14px', marginBottom: '4px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div><div style={{ color: '#e2e8f0', fontSize: '12px', fontWeight: 500 }}>{p.goal?.slice(0, 60)}</div>
                      <div style={{ color: '#475569', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', marginTop: '2px' }}>{p.personas?.length || 0} personas | {p.rounds_completed || 0} rounds</div></div>
                    <span style={{ color: p.status === 'completed' ? '#10b981' : '#fbbf24', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>{p.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          {/* Right sidebar */}
          <div>
            <div style={{ background: '#0a0f1a', border: '1px solid #1e293b', borderRadius: '6px', padding: '16px', marginBottom: '12px' }}>
              <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '1px' }}>Prediction Modes</div>
              {[{ mode: 'quick', title: 'Quick Predict', desc: 'Goal only. LLM generates personas.' },
                { mode: 'deep', title: 'Deep Predict', desc: 'Auto-research via web search.' },
                { mode: 'expert', title: 'Expert Predict', desc: 'Upload documents. GraphRAG builds knowledge.' },
                { mode: 'iterative', title: 'Iterative Predict', desc: 'Quick start, identify gaps, re-run.' }
              ].map(m => (
                <div key={m.mode} onClick={() => setMode(m.mode)} style={{ padding: '8px', borderRadius: '4px', marginBottom: '4px', cursor: 'pointer',
                  background: mode === m.mode ? '#1e293b' : 'transparent', border: mode === m.mode ? '1px solid #334155' : '1px solid transparent' }}>
                  <div style={{ color: mode === m.mode ? '#10b981' : '#94a3b8', fontSize: '12px', fontWeight: 600 }}>{m.title}</div>
                  <div style={{ color: '#475569', fontSize: '10px' }}>{m.desc}</div>
                </div>
              ))}
            </div>
            <div style={{ background: '#0a0f1a', border: '1px solid #1e293b', borderRadius: '6px', padding: '16px' }}>
              <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>Workflow</div>
              {phases.map((p, i) => { const Icon = p.icon; return (
                <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', borderBottom: i < phases.length - 1 ? '1px solid #1e293b' : 'none' }}>
                  <span style={{ color: '#334155', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace', width: '16px' }}>0{i + 1}</span>
                  <Icon size={12} style={{ color: '#475569' }} />
                  <span style={{ color: '#94a3b8', fontSize: '11px' }}>{p.label}</span>
                </div>
              ); })}
            </div>
          </div>
        </div>
      )}

      {/* ═══ PHASE: SIMULATING ═══ */}
      {phase === 'simulating' && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '300px', background: '#0f172a', border: '1px solid #1e293b', borderRadius: '6px', padding: '40px' }}>
          <Loader2 size={32} style={{ color: '#10b981', animation: 'spin 1s linear infinite' }} />
          <div style={{ color: '#e2e8f0', fontSize: '16px', fontWeight: 700, marginTop: '16px', fontFamily: 'JetBrains Mono, monospace' }}>Simulating {numPersonas} personas across {numRounds} rounds</div>
          <p style={{ color: '#64748b', fontSize: '12px', marginTop: '8px', fontFamily: 'JetBrains Mono, monospace' }}>Exploring thousands of paths simultaneously...</p>
          <div style={{ marginTop: '20px', display: 'flex', gap: '20px' }}>
            {['Graph Building', 'Persona Generation', 'Simulation', 'Analysis'].map((s, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981', animation: `pulse 1.5s ease-in-out ${i * 0.3}s infinite` }} />
                <span style={{ color: '#94a3b8', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>{s}</span>
              </div>
            ))}
          </div>
          <style>{`@keyframes spin { to { transform: rotate(360deg) } } @keyframes pulse { 0%,100% { opacity: 0.3 } 50% { opacity: 1 } }`}</style>
        </div>
      )}

      {/* ═══ PHASE: RESULTS ═══ */}
      {phase === 'results' && prediction && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '16px' }}>
          <div>
            {/* Strategy summary */}
            <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '6px', padding: '16px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Target size={16} style={{ color: '#10b981' }} />
                  <span style={{ color: '#e2e8f0', fontSize: '14px', fontWeight: 700 }}>Strategy</span>
                </div>
                <span style={{ background: '#064e3b', color: '#10b981', fontSize: '10px', fontWeight: 700, padding: '2px 8px', borderRadius: '3px', fontFamily: 'JetBrains Mono, monospace' }}>
                  {((prediction.strategy?.confidence_score || 0) * 100).toFixed(0)}% confidence
                </span>
              </div>
              <p style={{ color: '#cbd5e1', fontSize: '13px', lineHeight: 1.5, margin: '0 0 10px' }}>{prediction.strategy?.summary}</p>
              {prediction.strategy?.key_actions && (
                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                  {prediction.strategy.key_actions.map((a, i) => (
                    <span key={i} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '3px', padding: '3px 8px', fontSize: '10px', color: '#94a3b8', fontFamily: 'JetBrains Mono, monospace' }}>#{typeof a === 'string' ? a.replace(/\s+/g, '_').slice(0, 25) : a}</span>
                  ))}
                </div>
              )}
              {prediction.strategy?.risks && prediction.strategy.risks.length > 0 && (
                <div style={{ marginTop: '10px', display: 'flex', alignItems: 'start', gap: '6px' }}>
                  <AlertTriangle size={12} style={{ color: '#f87171', marginTop: '2px', flexShrink: 0 }} />
                  <span style={{ color: '#f87171', fontSize: '11px' }}>{prediction.strategy.risks.join(' | ')}</span>
                </div>
              )}
            </div>

            {/* Personas grid */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Simulated Personas ({prediction.personas?.length || 0})
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '8px' }}>
                {(prediction.personas || []).map((p, i) => (
                  <PersonaCard key={i} persona={p} onClick={() => setSelectedPersona(selectedPersona?.name === p.name ? null : p)} />
                ))}
              </div>
            </div>

            {/* Recommended agents for deployment */}
            {prediction.strategy?.recommended_agents && (
              <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '6px', padding: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                  <Users size={14} style={{ color: '#10b981' }} />
                  <span style={{ color: '#e2e8f0', fontSize: '13px', fontWeight: 600 }}>Deployment Agents ({prediction.strategy.recommended_agents.length})</span>
                </div>
                {prediction.strategy.recommended_agents.map((a, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px', borderRadius: '4px', marginBottom: '4px', background: '#1e293b' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: a.priority === 'high' ? '#f87171' : a.priority === 'medium' ? '#fbbf24' : '#475569' }} />
                      <span style={{ color: '#e2e8f0', fontSize: '12px', fontWeight: 600 }}>{a.role}</span>
                    </div>
                    <span style={{ color: '#64748b', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>{a.priority}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right sidebar */}
          <div>
            <SystemDashboard prediction={prediction} />
            {/* Cost summary */}
            {prediction.cost_model && (
              <div data-testid="ultimus-cost-model" style={{ background: '#0a0f1a', border: '1px solid #1e293b', borderRadius: '6px', padding: '14px', marginTop: '12px' }}>
                <div style={{ color: '#64748b', fontSize: '10px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '1px' }}>Cost Model</div>
                {[{ label: 'Cost/Hour', value: `$${prediction.cost_model.total_cost_per_hour}`, color: '#e2e8f0' },
                  { label: 'Hours Funded', value: `${prediction.cost_model.hours_funded}h`, color: '#e2e8f0' },
                  { label: 'Break Even', value: prediction.cost_model.break_even_hours ? `${prediction.cost_model.break_even_hours}h` : '—', color: '#fbbf24' },
                  { label: 'Self-Sustaining', value: prediction.cost_model.self_sustaining ? 'YES' : 'NO', color: prediction.cost_model.self_sustaining ? '#10b981' : '#f87171' },
                  { label: 'Waves', value: prediction.cost_model.deployment_waves?.length || 0, color: '#e2e8f0' },
                ].map((m, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: i < 4 ? '1px solid #1e293b' : 'none' }}>
                    <span style={{ color: '#475569', fontSize: '11px' }}>{m.label}</span>
                    <span style={{ color: m.color, fontSize: '12px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>{m.value}</span>
                  </div>
                ))}
              </div>
            )}
            {/* Actions */}
            <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <button data-testid="ultimus-execute-btn" onClick={executePrediction} disabled={executing}
                style={{ background: executing ? '#334155' : '#dc2626', color: '#fff', border: 'none', borderRadius: '4px', padding: '10px', fontSize: '13px', fontWeight: 700, cursor: executing ? 'wait' : 'pointer', fontFamily: 'JetBrains Mono, monospace', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', width: '100%' }}>
                {executing ? <><Loader2 size={14} /> Deploying...</> : <><Rocket size={14} /> Execute Prediction</>}
              </button>
              <button onClick={() => { setPrediction(null); setSelectedPersona(null); setPhase('input'); }}
                style={{ background: 'transparent', color: '#94a3b8', border: '1px solid #334155', borderRadius: '4px', padding: '8px', fontSize: '12px', cursor: 'pointer', width: '100%' }}>
                New Prediction
              </button>
            </div>
            {/* Execution result */}
            {prediction.execution && (
              <div style={{ background: '#0a0f1a', border: '1px solid #065f46', borderRadius: '6px', padding: '14px', marginTop: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                  <CheckCircle2 size={14} style={{ color: '#10b981' }} />
                  <span style={{ color: '#10b981', fontSize: '12px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>DEPLOYED</span>
                </div>
                <div style={{ color: '#94a3b8', fontSize: '11px' }}>{prediction.execution.agents_created} agents created in {prediction.execution.total_waves} waves</div>
                {(prediction.execution.agents || []).map((a, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 0', fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>
                    <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: a.status === 'ready_to_deploy' ? '#10b981' : '#fbbf24' }} />
                    <span style={{ color: '#e2e8f0' }}>{a.name}</span>
                    <span style={{ color: '#475569' }}>{a.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Selected persona detail panel */}
      {selectedPersona && (
        <div style={{ position: 'fixed', bottom: '20px', right: '20px', width: '350px', background: '#0f172a', border: '1px solid #10b981', borderRadius: '8px', padding: '16px', zIndex: 100, boxShadow: '0 8px 32px rgba(0,0,0,0.5)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Eye size={14} style={{ color: '#10b981' }} />
              <span style={{ color: '#10b981', fontSize: '12px', fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>DIMENSIONS</span>
            </div>
            <button onClick={() => setSelectedPersona(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '16px' }}>x</button>
          </div>
          <div style={{ color: '#e2e8f0', fontSize: '14px', fontWeight: 700, marginBottom: '4px' }}>{selectedPersona.name}</div>
          <div style={{ color: '#10b981', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace', marginBottom: '8px' }}>{selectedPersona.role}</div>
          <div style={{ color: '#94a3b8', fontSize: '12px', lineHeight: 1.5, marginBottom: '8px' }}>{selectedPersona.personality}</div>
          <div style={{ color: '#cbd5e1', fontSize: '12px', marginBottom: '8px' }}><strong>Strategy:</strong> {selectedPersona.strategy}</div>
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
            {(selectedPersona.tools || []).map((t, i) => (
              <span key={i} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '3px', padding: '2px 6px', fontSize: '9px', color: '#94a3b8', fontFamily: 'JetBrains Mono, monospace' }}>{t}</span>
            ))}
          </div>
          <div style={{ borderTop: '1px solid #1e293b', paddingTop: '8px', display: 'flex', gap: '16px' }}>
            <span style={{ color: '#10b981', fontSize: '12px' }}>Revenue: ${(selectedPersona.revenue || 0).toFixed(2)}</span>
            <span style={{ color: '#f87171', fontSize: '12px' }}>Expenses: ${(selectedPersona.expenses || 0).toFixed(2)}</span>
          </div>
        </div>
      )}
    </div>
  );
}

const inputStyle = { background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', padding: '6px 8px', fontSize: '12px', fontFamily: 'JetBrains Mono, monospace' };
