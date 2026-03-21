import React, { useState, useEffect, useCallback } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

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
  const [view, setView] = useState('input'); // input, simulating, results, executing

  const fetchPredictions = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ultimus/predictions`);
      const data = await res.json();
      setPredictions(data.predictions || []);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => { fetchPredictions(); }, [fetchPredictions]);

  const runPrediction = async () => {
    if (!goal.trim()) return;
    setLoading(true);
    setView('simulating');
    try {
      const res = await fetch(`${API}/api/ultimus/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, mode, num_personas: numPersonas, num_rounds: numRounds, seed_capital: seedCapital }),
      });
      const data = await res.json();
      if (data.detail) { alert(data.detail); setView('input'); }
      else { setPrediction(data); setView('results'); fetchPredictions(); }
    } catch (e) { alert('Prediction failed: ' + e.message); setView('input'); }
    setLoading(false);
  };

  const executePrediction = async (predId) => {
    setExecuting(true);
    setView('executing');
    try {
      const res = await fetch(`${API}/api/ultimus/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prediction_id: predId }),
      });
      const data = await res.json();
      if (data.detail) alert(data.detail);
      else { setPrediction(prev => ({ ...prev, execution: data })); fetchPredictions(); }
    } catch (e) { alert('Execution failed: ' + e.message); }
    setExecuting(false);
  };

  return (
    <div data-testid="ultimus-page" style={{ padding: '24px', maxWidth: '1200px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '4px', color: '#e2e8f0' }}>Ultimus</h1>
      <p style={{ color: '#94a3b8', marginBottom: '24px', fontSize: '14px' }}>Prediction Engine — Simulate, Calculate, Execute</p>

      {/* Goal Input */}
      {view === 'input' && (
        <div data-testid="ultimus-goal-input" style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', padding: '24px', marginBottom: '20px' }}>
          <label style={{ color: '#cbd5e1', fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '8px' }}>What do you want to achieve?</label>
          <textarea
            data-testid="ultimus-goal-textarea"
            value={goal} onChange={e => setGoal(e.target.value)}
            placeholder="Make $1000 in memecoins within 48 hours..."
            style={{ width: '100%', minHeight: '80px', background: '#1e293b', border: '1px solid #334155', borderRadius: '6px', color: '#e2e8f0', padding: '12px', fontSize: '14px', resize: 'vertical' }}
          />
          <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap', alignItems: 'end' }}>
            <div>
              <label style={{ color: '#94a3b8', fontSize: '11px', display: 'block', marginBottom: '4px' }}>Mode</label>
              <select data-testid="ultimus-mode-select" value={mode} onChange={e => setMode(e.target.value)}
                style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', padding: '6px 10px', fontSize: '13px' }}>
                <option value="quick">Quick Predict</option>
                <option value="deep">Deep Predict</option>
                <option value="expert">Expert Predict</option>
                <option value="iterative">Iterative Predict</option>
              </select>
            </div>
            <div>
              <label style={{ color: '#94a3b8', fontSize: '11px', display: 'block', marginBottom: '4px' }}>Personas</label>
              <input type="number" value={numPersonas} onChange={e => setNumPersonas(+e.target.value)} min={1} max={20}
                style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', padding: '6px 10px', fontSize: '13px', width: '70px' }} />
            </div>
            <div>
              <label style={{ color: '#94a3b8', fontSize: '11px', display: 'block', marginBottom: '4px' }}>Rounds</label>
              <input type="number" value={numRounds} onChange={e => setNumRounds(+e.target.value)} min={1} max={10}
                style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', padding: '6px 10px', fontSize: '13px', width: '70px' }} />
            </div>
            <div>
              <label style={{ color: '#94a3b8', fontSize: '11px', display: 'block', marginBottom: '4px' }}>Seed Capital ($)</label>
              <input type="number" value={seedCapital} onChange={e => setSeedCapital(+e.target.value)} min={1}
                style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', padding: '6px 10px', fontSize: '13px', width: '90px' }} />
            </div>
            <button data-testid="ultimus-simulate-btn" onClick={runPrediction} disabled={loading || !goal.trim()}
              style={{ background: loading ? '#334155' : '#10b981', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 24px', fontSize: '14px', fontWeight: 600, cursor: loading ? 'wait' : 'pointer' }}>
              {loading ? 'Simulating...' : 'Simulate'}
            </button>
          </div>
        </div>
      )}

      {/* Simulating */}
      {view === 'simulating' && (
        <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', padding: '40px', textAlign: 'center' }}>
          <div style={{ fontSize: '24px', color: '#10b981', marginBottom: '12px' }}>Simulating...</div>
          <p style={{ color: '#94a3b8' }}>Ultimus is running {numPersonas} personas across {numRounds} simulation rounds.</p>
          <p style={{ color: '#64748b', fontSize: '13px', marginTop: '8px' }}>This takes 15-60 seconds depending on complexity.</p>
        </div>
      )}

      {/* Results */}
      {view === 'results' && prediction && (
        <div data-testid="ultimus-results">
          <div style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px', padding: '20px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ color: '#e2e8f0', fontSize: '18px', margin: 0 }}>Prediction Results</h2>
              <span style={{ color: '#10b981', fontSize: '13px', background: '#064e3b', padding: '2px 10px', borderRadius: '12px' }}>{prediction.status}</span>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '12px' }}>Goal: {prediction.goal}</p>

            {/* Strategy */}
            {prediction.strategy && (
              <div style={{ background: '#1e293b', borderRadius: '6px', padding: '16px', marginBottom: '16px' }}>
                <h3 style={{ color: '#cbd5e1', fontSize: '14px', margin: '0 0 8px' }}>Strategy</h3>
                <p style={{ color: '#e2e8f0', fontSize: '13px' }}>{prediction.strategy.summary}</p>
                <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                  <span style={{ color: '#94a3b8', fontSize: '12px' }}>Confidence: <strong style={{ color: '#10b981' }}>{(prediction.strategy.confidence_score * 100).toFixed(0)}%</strong></span>
                </div>
                {prediction.strategy.risks && prediction.strategy.risks.length > 0 && (
                  <div style={{ marginTop: '8px' }}>
                    <span style={{ color: '#f87171', fontSize: '11px' }}>Risks: {prediction.strategy.risks.join(', ')}</span>
                  </div>
                )}
              </div>
            )}

            {/* Personas */}
            <div style={{ marginBottom: '16px' }}>
              <h3 style={{ color: '#cbd5e1', fontSize: '14px', marginBottom: '8px' }}>Simulated Personas ({prediction.personas?.length || 0})</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '8px' }}>
                {(prediction.personas || []).map((p, i) => (
                  <div key={i} style={{ background: '#1e293b', borderRadius: '6px', padding: '12px' }}>
                    <div style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '13px' }}>{p.name}</div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>{p.role}</div>
                    <div style={{ color: '#64748b', fontSize: '11px', marginTop: '4px' }}>Actions: {p.actions_count} | Rev: ${(p.revenue || 0).toFixed(2)}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Cost Model */}
            {prediction.cost_model && (
              <div data-testid="ultimus-cost-model" style={{ background: '#1e293b', borderRadius: '6px', padding: '16px', marginBottom: '16px' }}>
                <h3 style={{ color: '#cbd5e1', fontSize: '14px', margin: '0 0 8px' }}>Cost Model</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                  <div><div style={{ color: '#64748b', fontSize: '11px' }}>Cost/Hour</div><div style={{ color: '#e2e8f0', fontSize: '16px', fontWeight: 700 }}>${prediction.cost_model.total_cost_per_hour}</div></div>
                  <div><div style={{ color: '#64748b', fontSize: '11px' }}>Hours Funded</div><div style={{ color: '#e2e8f0', fontSize: '16px', fontWeight: 700 }}>{prediction.cost_model.hours_funded}h</div></div>
                  <div><div style={{ color: '#64748b', fontSize: '11px' }}>Break Even</div><div style={{ color: '#e2e8f0', fontSize: '16px', fontWeight: 700 }}>{prediction.cost_model.break_even_hours || '—'}h</div></div>
                  <div><div style={{ color: '#64748b', fontSize: '11px' }}>Self-Sustaining</div><div style={{ color: prediction.cost_model.self_sustaining ? '#10b981' : '#f87171', fontSize: '16px', fontWeight: 700 }}>{prediction.cost_model.self_sustaining ? 'Yes' : 'No'}</div></div>
                </div>
                {prediction.cost_model.deployment_waves && (
                  <div style={{ marginTop: '12px' }}>
                    <span style={{ color: '#94a3b8', fontSize: '12px' }}>Deployment waves: {prediction.cost_model.deployment_waves.length}</span>
                  </div>
                )}
              </div>
            )}

            {/* Recommended Agents */}
            {prediction.strategy?.recommended_agents && (
              <div style={{ marginBottom: '16px' }}>
                <h3 style={{ color: '#cbd5e1', fontSize: '14px', marginBottom: '8px' }}>Recommended Agents ({prediction.strategy.recommended_agents.length})</h3>
                {prediction.strategy.recommended_agents.map((a, i) => (
                  <div key={i} style={{ background: '#1e293b', borderRadius: '6px', padding: '10px', marginBottom: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '13px' }}>{a.role}</span>
                      <span style={{ color: '#94a3b8', fontSize: '12px', marginLeft: '8px' }}>{a.genesis_prompt_focus}</span>
                    </div>
                    <span style={{ color: a.priority === 'high' ? '#f87171' : a.priority === 'medium' ? '#fbbf24' : '#94a3b8', fontSize: '11px', textTransform: 'uppercase' }}>{a.priority}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Execute Button */}
            <div style={{ display: 'flex', gap: '12px' }}>
              <button data-testid="ultimus-execute-btn" onClick={() => executePrediction(prediction.id)} disabled={executing}
                style={{ background: executing ? '#334155' : '#dc2626', color: '#fff', border: 'none', borderRadius: '6px', padding: '10px 32px', fontSize: '14px', fontWeight: 700, cursor: executing ? 'wait' : 'pointer' }}>
                {executing ? 'Deploying Animas...' : 'Execute Prediction'}
              </button>
              <button onClick={() => { setPrediction(null); setView('input'); }}
                style={{ background: 'transparent', color: '#94a3b8', border: '1px solid #334155', borderRadius: '6px', padding: '10px 20px', fontSize: '13px', cursor: 'pointer' }}>
                New Prediction
              </button>
            </div>
          </div>

          {/* Execution Results */}
          {prediction.execution && (
            <div data-testid="ultimus-execution" style={{ background: '#0f172a', border: '1px solid #065f46', borderRadius: '8px', padding: '20px' }}>
              <h3 style={{ color: '#10b981', fontSize: '16px', margin: '0 0 12px' }}>Execution Started</h3>
              <p style={{ color: '#94a3b8', fontSize: '13px' }}>Created {prediction.execution.agents_created} agents in {prediction.execution.total_waves} waves</p>
              {(prediction.execution.agents || []).map((a, i) => (
                <div key={i} style={{ background: '#1e293b', borderRadius: '4px', padding: '8px', marginTop: '6px', fontSize: '12px' }}>
                  <span style={{ color: '#e2e8f0' }}>{a.name}</span>
                  <span style={{ color: '#64748b', marginLeft: '8px' }}>({a.agent_id})</span>
                  <span style={{ color: a.status === 'ready_to_deploy' ? '#10b981' : '#fbbf24', marginLeft: '8px' }}>{a.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Past Predictions */}
      {predictions.length > 0 && view === 'input' && (
        <div style={{ marginTop: '20px' }}>
          <h3 style={{ color: '#cbd5e1', fontSize: '14px', marginBottom: '8px' }}>Past Predictions</h3>
          {predictions.map((p, i) => (
            <div key={i} onClick={() => { setPrediction(p); setView('results'); }}
              style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: '6px', padding: '12px', marginBottom: '6px', cursor: 'pointer' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#e2e8f0', fontSize: '13px' }}>{p.goal}</span>
                <span style={{ color: '#94a3b8', fontSize: '11px' }}>{p.status}</span>
              </div>
              <div style={{ color: '#64748b', fontSize: '11px', marginTop: '4px' }}>{p.personas?.length || 0} personas, {p.rounds_completed || 0} rounds</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
