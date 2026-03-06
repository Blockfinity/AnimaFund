import React, { useState, useEffect, useRef } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

function parseLogLine(line) {
  const trimmed = line.trim();
  if (!trimmed) return null;

  // Try JSON structured log
  try {
    const j = JSON.parse(trimmed);
    return {
      type: 'structured',
      timestamp: j.timestamp,
      level: j.level || 'info',
      module: j.module || '',
      message: j.message || '',
      raw: trimmed,
    };
  } catch {
    // Plain text log (wizard output, banner, etc.)
    // Skip banner art lines
    if (trimmed.match(/^[═╔╗╚╝║█▓░╗╝╚╔─╯╭│╮╰]+$/) || trimmed.match(/^[█╗╚╔═╝║]+/) || trimmed.length < 2) return null;
    return { type: 'text', message: trimmed, raw: trimmed };
  }
}

function getLogColor(entry) {
  if (!entry) return '#71717a';
  const msg = entry.message.toLowerCase();
  if (entry.level === 'error' || msg.includes('error') || msg.includes('fatal')) return '#f87171';
  if (msg.includes('critical') || msg.includes('insufficient')) return '#fb923c';
  if (msg.includes('wallet created') || msg.includes('api key provisioned') || msg.includes('skills loaded') || msg.includes('success')) return '#34D399';
  if (msg.includes('sleeping') || msg.includes('sleep')) return '#a78bfa';
  if (msg.includes('heartbeat') || msg.includes('wake')) return '#60a5fa';
  if (entry.module === 'loop') return '#fbbf24';
  if (entry.type === 'text') return '#e4e4e7';
  return '#a1a1aa';
}

function getLogIcon(entry) {
  if (!entry) return '';
  const msg = entry.message.toLowerCase();
  if (msg.includes('wallet created')) return '[WALLET]';
  if (msg.includes('api key provisioned')) return '[API KEY]';
  if (msg.includes('skills loaded') || msg.includes('skill')) return '[SKILLS]';
  if (msg.includes('heartbeat')) return '[HEARTBEAT]';
  if (msg.includes('sleeping') || msg.includes('sleep')) return '[SLEEP]';
  if (msg.includes('critical')) return '[CRITICAL]';
  if (msg.includes('error') || msg.includes('fatal')) return '[ERROR]';
  if (msg.includes('think') || msg.includes('inference')) return '[THINK]';
  if (msg.includes('state:')) return '[STATE]';
  if (msg.includes('setup') || msg.includes('first-run')) return '[SETUP]';
  if (msg.includes('starting')) return '[START]';
  if (entry.module === 'loop') return '[LOOP]';
  if (entry.type === 'text') return '[LOG]';
  return '[INFO]';
}

function formatTime(timestamp) {
  if (!timestamp) return '';
  try {
    const d = new Date(timestamp);
    return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch { return ''; }
}

export default function EngineConsole({ isRunning }) {
  const [logs, setLogs] = useState([]);
  const [animaFiles, setAnimaFiles] = useState([]);
  const scrollRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    if (!isRunning && logs.length === 0) return;

    const fetchLogs = async () => {
      try {
        const res = await fetch(`${API}/api/engine/logs?lines=100`);
        const data = await res.json();

        // Parse stdout
        const rawLines = (data.stdout || '').split('\n');
        const parsed = rawLines.map(parseLogLine).filter(Boolean);

        // Parse stderr for errors
        const errLines = (data.stderr || '').split('\n');
        const parsedErrors = errLines.map(l => {
          const trimmed = l.trim();
          if (!trimmed) return null;
          return { type: 'text', level: 'error', message: trimmed, raw: trimmed };
        }).filter(Boolean);

        setLogs([...parsed, ...parsedErrors]);
        setAnimaFiles(data.anima_dir || []);
      } catch { /* ignore fetch errors */ }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [isRunning, logs.length]);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Derive setup progress from logs
  const wizardSteps = [
    { key: 'wallet', label: 'Generate Wallet', pattern: /wallet created|generating identity/i },
    { key: 'apikey', label: 'Provision API Key (SIWE)', pattern: /api key provisioned|provisioning conway/i },
    { key: 'config', label: 'Setup Configuration', pattern: /auto-config detected|setup questions/i },
    { key: 'environment', label: 'Detect Environment', pattern: /detecting environment/i },
    { key: 'write', label: 'Write Configuration', pattern: /writing configuration|configuration written/i },
    { key: 'skills', label: 'Load Skills', pattern: /skills loaded|installing skills/i },
  ];

  const completedSteps = wizardSteps.map(step => {
    return logs.some(log => step.pattern.test(log.message));
  });

  const showWizardProgress = isRunning && logs.some(l => l.message.toLowerCase().includes('first-run'));

  return (
    <div data-testid="engine-console" style={{ background: '#0c0c0e', border: '1px solid #27272a', borderRadius: '8px', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '10px 14px', borderBottom: '1px solid #1e1e22', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: isRunning ? '#34D399' : '#71717a', boxShadow: isRunning ? '0 0 6px #34D399' : 'none' }} />
          <span style={{ fontSize: '11px', fontWeight: 700, color: '#e4e4e7', letterSpacing: '0.5px' }}>ENGINE CONSOLE</span>
          {isRunning && <span style={{ fontSize: '9px', color: '#71717a', fontFamily: 'JetBrains Mono, monospace' }}>LIVE</span>}
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {animaFiles.length > 0 && (
            <span style={{ fontSize: '9px', color: '#52525b', fontFamily: 'JetBrains Mono, monospace' }}>
              {animaFiles.length} files in ~/.anima
            </span>
          )}
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            style={{ fontSize: '9px', padding: '2px 6px', borderRadius: '4px', border: '1px solid #27272a', background: autoScroll ? '#166534' : '#18181b', color: autoScroll ? '#34D399' : '#71717a', cursor: 'pointer' }}>
            {autoScroll ? 'AUTO' : 'SCROLL'}
          </button>
        </div>
      </div>

      {/* Wizard Progress (only during first run) */}
      {showWizardProgress && (
        <div style={{ padding: '8px 14px', borderBottom: '1px solid #1e1e22', background: '#0a0a0c' }}>
          <div style={{ fontSize: '9px', color: '#71717a', marginBottom: '6px', fontWeight: 700, letterSpacing: '0.5px' }}>SETUP WIZARD</div>
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {wizardSteps.map((step, i) => (
              <div key={step.key} style={{
                fontSize: '9px', padding: '2px 8px', borderRadius: '4px',
                background: completedSteps[i] ? '#052e16' : '#18181b',
                border: `1px solid ${completedSteps[i] ? '#166534' : '#27272a'}`,
                color: completedSteps[i] ? '#34D399' : '#52525b',
              }}>
                {completedSteps[i] ? '\u2713' : (i + 1)} {step.label}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Log entries */}
      <div
        ref={scrollRef}
        onScroll={(e) => {
          const { scrollTop, scrollHeight, clientHeight } = e.target;
          setAutoScroll(scrollHeight - scrollTop - clientHeight < 40);
        }}
        style={{ maxHeight: '280px', overflowY: 'auto', padding: '6px 0', fontFamily: 'JetBrains Mono, monospace', fontSize: '10px', lineHeight: '18px' }}>
        {logs.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#52525b', fontSize: '11px' }}>
            {isRunning ? 'Waiting for engine output...' : 'Engine not started. Click "Create Genesis Agent" to begin.'}
          </div>
        ) : (
          logs.map((entry, i) => (
            <div key={i} style={{ padding: '1px 14px', display: 'flex', gap: '8px', color: getLogColor(entry) }}>
              <span style={{ color: '#3f3f46', minWidth: '52px', flexShrink: 0 }}>{formatTime(entry.timestamp)}</span>
              <span style={{ color: '#52525b', minWidth: '70px', flexShrink: 0 }}>{getLogIcon(entry)}</span>
              <span style={{ wordBreak: 'break-word' }}>{entry.message}</span>
            </div>
          ))
        )}
      </div>

      {/* File status bar */}
      {animaFiles.length > 0 && (
        <div style={{ padding: '6px 14px', borderTop: '1px solid #1e1e22', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {animaFiles.map(f => (
            <span key={f.name} style={{
              fontSize: '8px', padding: '1px 5px', borderRadius: '3px',
              background: f.name === 'wallet.json' ? '#052e16' : f.name === 'anima.json' ? '#052e16' : f.name === 'state.db' ? '#172554' : '#18181b',
              border: `1px solid ${f.name === 'wallet.json' || f.name === 'anima.json' ? '#166534' : '#27272a'}`,
              color: f.name === 'wallet.json' || f.name === 'anima.json' ? '#34D399' : '#71717a',
              fontFamily: 'JetBrains Mono, monospace',
            }}>
              {f.name}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
