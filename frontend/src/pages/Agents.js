import React, { useState, useEffect, useCallback } from 'react';
import { Users, CircleDot, Shield } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [discovered, setDiscovered] = useState([]);
  const [lifecycle, setLifecycle] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [agRes, relRes, discRes, lcRes] = await Promise.all([
        fetch(`${API}/api/live/agents`),
        fetch(`${API}/api/live/relationships`),
        fetch(`${API}/api/live/discovered`),
        fetch(`${API}/api/live/lifecycle`),
      ]);
      const [ag, rel, disc, lc] = await Promise.all([agRes.json(), relRes.json(), discRes.json(), lcRes.json()]);
      setAgents(ag.agents || []);
      setRelationships(rel.relationships || []);
      setDiscovered(disc.agents || []);
      setLifecycle(lc.events || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); const i = setInterval(fetchData, 10000); return () => clearInterval(i); }, [fetchData]);

  if (loading) return <Loading />;

  const hasData = agents.length > 0 || relationships.length > 0 || discovered.length > 0;

  return (
    <div data-testid="agents-page" className="space-y-4 animate-slide-in">
      {!hasData ? (
        <Empty icon={Users} text="No agents yet. The founder AI will hire and spawn agents as it builds the organization." />
      ) : (
        <>
          {agents.length > 0 && (
            <Section title={`Spawned Agents (${agents.length})`}>
              <Table headers={['Name', 'Role', 'Status', 'Wallet', 'Funded', 'Created']}>
                {agents.map(a => (
                  <tr key={a.agent_id} className="border-b border-border last:border-0 hover:bg-secondary/50">
                    <Td bold>{a.name}</Td>
                    <Td>{a.role}</Td>
                    <Td><StatusBadge status={a.status} /></Td>
                    <Td mono>{a.wallet_address?.slice(0, 10)}...</Td>
                    <Td mono>${((a.funded_cents || 0) / 100).toFixed(2)}</Td>
                    <Td>{a.created_at?.split('T')[0]}</Td>
                  </tr>
                ))}
              </Table>
            </Section>
          )}
          {discovered.length > 0 && (
            <Section title={`Discovered Agents (${discovered.length})`}>
              <Table headers={['Name', 'Address', 'Services', 'Fetched']}>
                {discovered.map((a, i) => (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-secondary/50">
                    <Td bold>{a.name}</Td>
                    <Td mono>{a.address?.slice(0, 10)}...</Td>
                    <Td>{a.services?.length || 0} services</Td>
                    <Td>{a.last_fetched?.split('T')[0]}</Td>
                  </tr>
                ))}
              </Table>
            </Section>
          )}
          {relationships.length > 0 && (
            <Section title={`Relationships (${relationships.length})`}>
              <Table headers={['Agent', 'Type', 'Trust', 'Interactions', 'Notes']}>
                {relationships.map((r, i) => (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-secondary/50">
                    <Td bold>{r.name || r.address?.slice(0, 10)}</Td>
                    <Td>{r.relationship_type}</Td>
                    <Td mono>{(r.trust_score * 100).toFixed(0)}%</Td>
                    <Td>{r.interaction_count}</Td>
                    <Td className="max-w-[200px] truncate">{r.notes}</Td>
                  </tr>
                ))}
              </Table>
            </Section>
          )}
          {lifecycle.length > 0 && (
            <Section title={`Lifecycle Events (${lifecycle.length})`}>
              <Table headers={['Child', 'From', 'To', 'Reason', 'Time']}>
                {lifecycle.map((e, i) => (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-secondary/50">
                    <Td mono>{e.child_id?.slice(0, 8)}</Td>
                    <Td><StatusBadge status={e.from_state} /></Td>
                    <Td><StatusBadge status={e.to_state} /></Td>
                    <Td>{e.reason}</Td>
                    <Td>{e.created_at?.split('T')[0]}</Td>
                  </tr>
                ))}
              </Table>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="bg-white border border-border rounded-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-border"><h3 className="text-sm font-heading font-semibold text-foreground">{title}</h3></div>
      {children}
    </div>
  );
}
function Table({ headers, children }) {
  return (
    <table className="w-full">
      <thead><tr className="border-b border-border">
        {headers.map(h => <th key={h} className="text-left text-[10px] font-medium text-muted-foreground uppercase tracking-wider px-4 py-2">{h}</th>)}
      </tr></thead>
      <tbody>{children}</tbody>
    </table>
  );
}
function Td({ children, bold, mono, className = '' }) {
  return <td className={`px-4 py-2 text-xs ${bold ? 'font-medium text-foreground' : 'text-muted-foreground'} ${mono ? 'font-mono' : ''} ${className}`}>{children || '—'}</td>;
}
function StatusBadge({ status }) {
  const colors = { healthy: 'bg-success/10 text-success', alive: 'bg-success/10 text-success', running: 'bg-success/10 text-success', sleeping: 'bg-info/10 text-info', dead: 'bg-muted text-muted-foreground', failed: 'bg-error/10 text-error' };
  return <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${colors[status] || 'bg-secondary text-secondary-foreground'}`}>{status || '—'}</span>;
}
function Loading() { return <div className="flex items-center justify-center h-64"><div className="w-4 h-4 border-2 border-foreground border-t-transparent rounded-full animate-spin" /></div>; }
function Empty({ icon: Icon, text }) { return <div className="flex flex-col items-center justify-center h-64 text-center"><Icon className="w-8 h-8 text-border mb-3" /><p className="text-sm text-muted-foreground max-w-md">{text}</p></div>; }
