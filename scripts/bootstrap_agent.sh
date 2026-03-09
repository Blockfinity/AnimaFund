#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Anima Fund — Agent Environment Bootstrap
# Pre-installs system tools, Conway Terminal, provisions API key,
# configures OpenClaw, and copies credentials to engine directory.
# Each agent gets its own fully isolated environment.
#
# This script runs BEFORE the LLM engine starts. Every tool
# installed here is available to the agent from Turn 1.
# The LLM cannot skip what this script does mechanically.
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

# ─── Step 0: Install system tools (MECHANICAL — cannot be skipped) ─
echo "[0/8] Installing system tools (curl, git, wget, build-essential)..."

apt-get update -qq 2>/dev/null || true
apt-get install -y -qq curl git wget build-essential jq > /dev/null 2>&1 || true

# Verify each tool
for tool in curl git wget jq; do
    if command -v $tool &>/dev/null; then
        echo "  $tool: OK ($(which $tool))"
    else
        echo "  WARNING: $tool failed to install"
    fi
done

# ─── Step 0.5: Install Node.js if missing ────────────────────────
echo "[0.5/8] Checking Node.js..."

if command -v node &>/dev/null; then
    echo "  Node.js already installed: $(node --version)"
else
    echo "  Installing Node.js 22.x..."
    if command -v curl &>/dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_22.x | bash - > /dev/null 2>&1 || true
        apt-get install -y -qq nodejs > /dev/null 2>&1 || true
    fi
    if command -v node &>/dev/null; then
        echo "  Node.js installed: $(node --version)"
    else
        echo "  WARNING: Node.js installation failed"
    fi
fi

# ─── Step 1: Ensure directories exist ────────────────────────────
mkdir -p "${ANIMA_DIR}" "${CONWAY_DIR}" "${OPENCLAW_DIR}"

# Create .automaton -> .anima symlink if missing
AUTOMATON_LINK="${AGENT_HOME}/.automaton"
if [ ! -e "${AUTOMATON_LINK}" ]; then
    ln -s ".anima" "${AUTOMATON_LINK}" 2>/dev/null || true
fi
echo "[1/8] Directories created"

# ─── Step 2: Install Conway Terminal ─────────────────────────────
echo "[2/8] Installing Conway Terminal..."

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

# ─── Step 3: Conway provisioning ─────────────────────────────────
# The agent provisions its OWN wallet and API key via Conway.
# We do NOT copy the platform's global Conway credentials.
# The engine's setup wizard or conway-terminal --provision handles this.
echo "[3/8] Conway provisioning (agent self-provisions on first run)..."

if [ -f "${CONWAY_DIR}/config.json" ]; then
    echo "  Agent already has Conway config"
elif [ -f "${ANIMA_DIR}/config.json" ]; then
    echo "  Agent already has engine config"
else
    echo "  No Conway config yet — agent will self-provision on first run"
fi

# ─── Step 4: Install & Configure OpenClaw ────────────────────────
# Install OpenClaw binary, then configure MCP to point to Conway Terminal.
echo "[4/8] Installing & configuring OpenClaw..."

if command -v openclaw &>/dev/null; then
    echo "  OpenClaw binary already installed: $(which openclaw)"
else
    echo "  Installing OpenClaw..."
    if command -v curl &>/dev/null; then
        curl -fsSL https://openclaw.ai/install.sh | bash 2>/dev/null && \
            openclaw onboard --install-daemon 2>/dev/null || true
    fi
    if command -v openclaw &>/dev/null; then
        echo "  OpenClaw installed: $(which openclaw)"
    else
        echo "  WARNING: OpenClaw installation failed (agent can retry)"
    fi
fi

OPENCLAW_CONFIG="${OPENCLAW_DIR}/config.json"
if [ -f "${OPENCLAW_CONFIG}" ]; then
    echo "  OpenClaw config already exists"
else
    python3 -c "
import json, os, shutil

ct_path = shutil.which('conway-terminal') or 'conway-terminal'

# Try to read the agent's Conway API key for MCP env
conway_key = ''
for cpath in ['${ANIMA_DIR}/config.json', os.path.expanduser('~/.conway/config.json')]:
    if os.path.exists(cpath):
        try:
            conway_key = json.load(open(cpath)).get('apiKey', '')
            if conway_key:
                break
        except:
            pass

config = {
    'mcpServers': {
        'conway': {
            'command': ct_path,
            'env': {'CONWAY_API_KEY': conway_key} if conway_key else {}
        }
    }
}

os.makedirs('${OPENCLAW_DIR}', exist_ok=True)
with open('${OPENCLAW_CONFIG}', 'w') as f:
    json.dump(config, f, indent=2)
print('  OpenClaw configured with Conway Terminal' + (' + API key' if conway_key else ' (agent provides own key at runtime)'))
" 2>/dev/null || echo "  WARNING: OpenClaw config creation failed"
fi

# ─── Step 5: Install Conway Terminal skills & commands ───────────
echo "[5/8] Installing Conway Terminal skills and commands..."

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

# ─── Step 6: File permission isolation ───────────────────────────
echo "[6/8] Setting file permissions..."

# Lock down agent home so other agents can't read it
chmod 700 "${AGENT_HOME}" 2>/dev/null || true
chmod 700 "${ANIMA_DIR}" 2>/dev/null || true
chmod 700 "${CONWAY_DIR}" 2>/dev/null || true
chmod 700 "${OPENCLAW_DIR}" 2>/dev/null || true
echo "  Agent home locked to owner-only access"

# ─── Step 7: Verify Environment ─────────────────────────────────
echo "[7/8] Verifying environment..."

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

# ─── Step 8: Send Telegram bootstrap notification ─────────────────
echo "[8/8] Sending Telegram bootstrap notification..."

# Read telegram config from genesis prompt or env
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# Try to extract from genesis prompt if not in env
if [ -z "$TELEGRAM_BOT_TOKEN" ] && [ -f "${ANIMA_DIR}/genesis-prompt.md" ]; then
    TELEGRAM_BOT_TOKEN=$(grep -oP 'bot\K[0-9]+:[A-Za-z0-9_-]+' "${ANIMA_DIR}/genesis-prompt.md" | head -1)
    TELEGRAM_BOT_TOKEN="bot${TELEGRAM_BOT_TOKEN}"
fi
if [ -z "$TELEGRAM_CHAT_ID" ] && [ -f "${ANIMA_DIR}/genesis-prompt.md" ]; then
    TELEGRAM_CHAT_ID=$(grep -oP "'chat_id': '\K[0-9]+" "${ANIMA_DIR}/genesis-prompt.md" | head -1)
fi

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    python3 -c "
import urllib.request, json
tools = []
for t in ['curl', 'git', 'wget', 'node', 'npm', 'conway-terminal']:
    import shutil
    tools.append(f'  {t}: {\"OK\" if shutil.which(t) else \"MISSING\"}')
msg = '<b>BOOTSTRAP COMPLETE (mechanical)</b>\n' + '\n'.join(tools) + '\nEngine starting next...'
data = json.dumps({'chat_id': '${TELEGRAM_CHAT_ID}', 'text': msg, 'parse_mode': 'HTML'}).encode()
req = urllib.request.Request('https://api.telegram.org/${TELEGRAM_BOT_TOKEN}/sendMessage', data=data, headers={'Content-Type': 'application/json'})
try: urllib.request.urlopen(req)
except Exception as e: print(f'Telegram notification failed: {e}')
" 2>/dev/null || true
    echo "  Telegram notification sent"
else
    echo "  Telegram credentials not found — skipping notification"
fi
