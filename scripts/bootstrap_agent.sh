#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Anima Fund — Agent Environment Bootstrap
# Pre-installs Conway Terminal, provisions API key, configures
# OpenClaw, and verifies all tools BEFORE the engine starts.
# Each agent gets its own fully isolated environment.
#
# Usage: HOME=/path/to/agent/home bash bootstrap_agent.sh
# ═══════════════════════════════════════════════════════════════════

set -e

AGENT_HOME="${HOME}"
AUTOMATON_DIR="${AGENT_HOME}/.automaton"
CONWAY_DIR="${AGENT_HOME}/.conway"
OPENCLAW_DIR="${AGENT_HOME}/.openclaw"

echo "══════════════════════════════════════════════════════"
echo "  AGENT BOOTSTRAP — ${AGENT_HOME}"
echo "══════════════════════════════════════════════════════"

# ─── Step 1: Ensure directories exist ────────────────────────────
mkdir -p "${AUTOMATON_DIR}" "${CONWAY_DIR}" "${OPENCLAW_DIR}"
echo "[1/5] Directories created"

# ─── Step 2: Install Conway Terminal ─────────────────────────────
echo "[2/5] Installing Conway Terminal..."

if command -v conway-terminal &>/dev/null; then
    echo "  Conway Terminal already installed: $(which conway-terminal)"
else
    # Try npm install first
    if command -v npm &>/dev/null; then
        npm install -g conway-terminal 2>/dev/null && echo "  Installed via npm" || true
    fi

    # Fallback: try the install script
    if ! command -v conway-terminal &>/dev/null; then
        if command -v curl &>/dev/null; then
            curl -fsSL https://conway.tech/terminal.sh | sh 2>/dev/null || true
        else
            python3 -c "
import urllib.request, subprocess, tempfile, os
try:
    script = urllib.request.urlopen('https://conway.tech/terminal.sh').read()
    path = os.path.join(tempfile.gettempdir(), 'terminal.sh')
    with open(path, 'wb') as f: f.write(script)
    os.chmod(path, 0o755)
    subprocess.run(['sh', path], check=True)
except Exception as e:
    print(f'  Install script failed: {e}')
" 2>/dev/null || true
        fi
    fi
fi

# Verify installation
if command -v conway-terminal &>/dev/null; then
    echo "  Conway Terminal OK: $(conway-terminal --version 2>/dev/null || echo 'installed')"
else
    echo "  WARNING: Conway Terminal not found in PATH. Engine will attempt self-install."
fi

# ─── Step 3: Provision Conway API Key ────────────────────────────
echo "[3/5] Provisioning Conway API key..."

if [ -f "${CONWAY_DIR}/config.json" ]; then
    echo "  Conway config already exists"
else
    # Try to provision via conway-terminal
    if command -v conway-terminal &>/dev/null; then
        conway-terminal --provision 2>/dev/null || true
    fi

    # Verify config was created
    if [ -f "${CONWAY_DIR}/config.json" ]; then
        echo "  API key provisioned successfully"
    else
        echo "  WARNING: Could not auto-provision API key. Engine wizard will handle this."
    fi
fi

# ─── Step 4: Configure OpenClaw ──────────────────────────────────
echo "[4/5] Configuring OpenClaw..."

OPENCLAW_CONFIG="${OPENCLAW_DIR}/config.json"
if [ -f "${OPENCLAW_CONFIG}" ]; then
    echo "  OpenClaw config already exists"
else
    # Create OpenClaw config pointing to Conway Terminal
    python3 -c "
import json, os

conway_cfg_path = os.path.expanduser('${CONWAY_DIR}/config.json')
api_key = ''
if os.path.exists(conway_cfg_path):
    try:
        with open(conway_cfg_path) as f:
            api_key = json.load(f).get('apiKey', '')
    except:
        pass

# Find conway-terminal binary
import shutil
ct_path = shutil.which('conway-terminal') or 'conway-terminal'

config = {
    'mcpServers': {
        'conway': {
            'command': ct_path,
            'env': {}
        }
    }
}
if api_key:
    config['mcpServers']['conway']['env']['CONWAY_API_KEY'] = api_key

os.makedirs('${OPENCLAW_DIR}', exist_ok=True)
with open('${OPENCLAW_CONFIG}', 'w') as f:
    json.dump(config, f, indent=2)
print('  OpenClaw configured with Conway Terminal')
" 2>/dev/null || echo "  WARNING: OpenClaw config creation failed"
fi

# ─── Step 5: Verify Environment ─────────────────────────────────
echo "[5/5] Verifying environment..."

echo "  Agent HOME: ${AGENT_HOME}"
echo "  Automaton dir: ${AUTOMATON_DIR}"

# Check for required files
for f in "${AUTOMATON_DIR}/auto-config.json" "${AUTOMATON_DIR}/genesis-prompt.md"; do
    if [ -f "$f" ]; then
        echo "  $(basename $f): OK"
    else
        echo "  $(basename $f): MISSING"
    fi
done

# Check Conway config
if [ -f "${CONWAY_DIR}/config.json" ]; then
    echo "  Conway config: OK"
else
    echo "  Conway config: NOT PROVISIONED (will be handled by engine)"
fi

# Check OpenClaw config
if [ -f "${OPENCLAW_CONFIG}" ]; then
    echo "  OpenClaw config: OK"
else
    echo "  OpenClaw config: NOT SET (will be handled by engine)"
fi

echo ""
echo "══════════════════════════════════════════════════════"
echo "  BOOTSTRAP COMPLETE"
echo "══════════════════════════════════════════════════════"
