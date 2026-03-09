#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Anima Fund — Agent Environment Bootstrap
# Pre-installs Conway Terminal, provisions API key, configures
# OpenClaw, and copies credentials to engine directory (.anima/).
# Each agent gets its own fully isolated environment.
#
# Usage: HOME=/path/to/agent/home bash bootstrap_agent.sh
# ═══════════════════════════════════════════════════════════════════

set -e

AGENT_HOME="${HOME}"
ANIMA_DIR="${AGENT_HOME}/.anima"
CONWAY_DIR="${AGENT_HOME}/.conway"
OPENCLAW_DIR="${AGENT_HOME}/.openclaw"

echo "══════════════════════════════════════════════════════"
echo "  AGENT BOOTSTRAP — ${AGENT_HOME}"
echo "══════════════════════════════════════════════════════"

# ─── Step 1: Ensure directories exist ────────────────────────────
mkdir -p "${ANIMA_DIR}" "${CONWAY_DIR}" "${OPENCLAW_DIR}"

# Create .automaton -> .anima symlink if missing
AUTOMATON_LINK="${AGENT_HOME}/.automaton"
if [ ! -e "${AUTOMATON_LINK}" ]; then
    ln -s ".anima" "${AUTOMATON_LINK}" 2>/dev/null || true
fi
echo "[1/6] Directories created"

# ─── Step 2: Install Conway Terminal ─────────────────────────────
echo "[2/6] Installing Conway Terminal..."

if command -v conway-terminal &>/dev/null; then
    echo "  Conway Terminal already installed: $(which conway-terminal)"
else
    if command -v npm &>/dev/null; then
        npm install -g conway-terminal 2>/dev/null && echo "  Installed via npm" || true
    fi

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

if command -v conway-terminal &>/dev/null; then
    echo "  Conway Terminal OK: $(conway-terminal --version 2>/dev/null || echo 'installed')"
else
    echo "  WARNING: Conway Terminal not found in PATH"
fi

# ─── Step 3: Provision Conway API Key ────────────────────────────
echo "[3/6] Provisioning Conway API key..."

if [ -f "${CONWAY_DIR}/config.json" ]; then
    echo "  Conway config already exists"
else
    if command -v conway-terminal &>/dev/null; then
        conway-terminal --provision 2>/dev/null || true
    fi
fi

# ─── Step 4: Copy credentials to engine directory (.anima/) ─────
echo "[4/6] Syncing credentials to engine directory..."

# Copy Conway wallet to .anima/ so the engine reuses it (instead of generating a new one)
if [ -f "${CONWAY_DIR}/wallet.json" ] && [ ! -f "${ANIMA_DIR}/wallet.json" ]; then
    cp "${CONWAY_DIR}/wallet.json" "${ANIMA_DIR}/wallet.json"
    chmod 600 "${ANIMA_DIR}/wallet.json"
    echo "  Wallet synced to .anima/"
fi

# Copy Conway config to .anima/ so the engine finds the API key
if [ -f "${CONWAY_DIR}/config.json" ] && [ ! -f "${ANIMA_DIR}/config.json" ]; then
    cp "${CONWAY_DIR}/config.json" "${ANIMA_DIR}/config.json"
    chmod 600 "${ANIMA_DIR}/config.json"
    echo "  Config synced to .anima/"
fi

# ─── Step 5: Configure OpenClaw ──────────────────────────────────
echo "[5/6] Configuring OpenClaw..."

OPENCLAW_CONFIG="${OPENCLAW_DIR}/openclaw.json"
if [ -f "${OPENCLAW_CONFIG}" ]; then
    echo "  OpenClaw config already exists"
else
    python3 -c "
import json, os, shutil

conway_cfg_path = '${CONWAY_DIR}/config.json'
api_key = ''
if os.path.exists(conway_cfg_path):
    try:
        with open(conway_cfg_path) as f:
            api_key = json.load(f).get('apiKey', '')
    except:
        pass

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

# ─── Step 6: Install Conway Terminal skills & commands ───────────
echo "[6/7] Installing Conway Terminal skills and commands..."

# Conway Automaton skill (for the engine)
CT_SKILLS="$(npm root -g 2>/dev/null)/conway-terminal/plugin/skills"
CT_COMMANDS="$(npm root -g 2>/dev/null)/conway-terminal/plugin/commands"

if [ -d "$CT_SKILLS/conway-automaton" ]; then
    mkdir -p "${ANIMA_DIR}/skills/conway-automaton"
    cp "$CT_SKILLS/conway-automaton/SKILL.md" "${ANIMA_DIR}/skills/conway-automaton/SKILL.md"
    echo "  Installed: conway-automaton skill"
fi

# Conway OpenClaw skill
if [ -d "$CT_SKILLS/conway-openclaw" ]; then
    mkdir -p "${OPENCLAW_DIR}/skills/conway"
    cp "$CT_SKILLS/conway-openclaw/SKILL.md" "${OPENCLAW_DIR}/skills/conway/SKILL.md"
    echo "  Installed: conway-openclaw skill"
fi

# Conway commands
if [ -d "$CT_COMMANDS" ]; then
    mkdir -p "${ANIMA_DIR}/commands"
    cp "$CT_COMMANDS"/*.md "${ANIMA_DIR}/commands/" 2>/dev/null
    echo "  Installed: Conway commands (conway, conway-status, conway-deploy)"
fi

# ─── Step 7: Verify Environment ─────────────────────────────────
echo "[7/7] Verifying environment..."

echo "  Agent HOME: ${AGENT_HOME}"

for f in "${ANIMA_DIR}/auto-config.json" "${ANIMA_DIR}/genesis-prompt.md"; do
    if [ -f "$f" ]; then echo "  $(basename $f): OK"
    else echo "  $(basename $f): MISSING (will be created by agent setup)"
    fi
done

if [ -f "${ANIMA_DIR}/wallet.json" ]; then
    echo "  Wallet: OK (shared between engine and Conway Terminal)"
else
    echo "  Wallet: NOT SET (engine wizard will generate one)"
fi

if [ -f "${ANIMA_DIR}/config.json" ]; then
    echo "  API key: OK"
else
    echo "  API key: NOT SET (engine wizard will provision one)"
fi

if [ -f "${OPENCLAW_CONFIG}" ]; then echo "  OpenClaw: OK"
else echo "  OpenClaw: NOT SET"
fi

echo ""
echo "══════════════════════════════════════════════════════"
echo "  BOOTSTRAP COMPLETE"
echo "══════════════════════════════════════════════════════"
