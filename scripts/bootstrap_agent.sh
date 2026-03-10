#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Anima Fund — Agent Environment Bootstrap
# Runs BEFORE the LLM engine starts. Installs, tests, and verifies
# every tool the agent needs. Writes a BOOT_REPORT.md that the LLM
# reads on its first turn — no installation instructions needed in
# the genesis prompt because everything is already done.
#
# The LLM cannot skip what this script does mechanically.
# ═══════════════════════════════════════════════════════════════════

set -e

AGENT_HOME="${HOME}"
ANIMA_DIR="${AGENT_HOME}/.anima"
CONWAY_DIR="${AGENT_HOME}/.conway"
OPENCLAW_DIR="${AGENT_HOME}/.openclaw"
REPORT="${ANIMA_DIR}/BOOT_REPORT.md"
PASS=0
FAIL=0
WARN=0

echo "══════════════════════════════════════════════════════"
echo "  AGENT BOOTSTRAP — ${AGENT_HOME}"
echo "══════════════════════════════════════════════════════"

mkdir -p "${ANIMA_DIR}" "${CONWAY_DIR}" "${OPENCLAW_DIR}"

# ─── Helper: record test result ──────────────────────────────────
declare -a RESULTS=()
record() {
    local tool="$1" status="$2" detail="$3"
    if [ "$status" = "PASS" ]; then
        PASS=$((PASS + 1))
        RESULTS+=("| $tool | PASS | $detail |")
    elif [ "$status" = "WARN" ]; then
        WARN=$((WARN + 1))
        RESULTS+=("| $tool | WARN | $detail |")
    else
        FAIL=$((FAIL + 1))
        RESULTS+=("| $tool | FAIL | $detail |")
    fi
    echo "  [$status] $tool: $detail"
}

# ═════════════════════════════════════════════════════════
# PHASE 1: INSTALL SYSTEM TOOLS
# ═════════════════════════════════════════════════════════
echo ""
echo "[PHASE 1] Installing system tools..."

apt-get update -qq 2>/dev/null || true
apt-get install -y -qq curl git wget build-essential jq python3 > /dev/null 2>&1 || true

# Install Node.js if missing
if ! command -v node &>/dev/null; then
    echo "  Installing Node.js 22.x..."
    if command -v curl &>/dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_22.x | bash - > /dev/null 2>&1 || true
        apt-get install -y -qq nodejs > /dev/null 2>&1 || true
    fi
fi

# ═════════════════════════════════════════════════════════
# PHASE 2: INSTALL CONWAY TERMINAL
# ═════════════════════════════════════════════════════════
echo ""
echo "[PHASE 2] Installing Conway Terminal..."

if ! command -v conway-terminal &>/dev/null; then
    if command -v npm &>/dev/null; then
        npm install -g conway-terminal 2>/dev/null || true
    fi
    if ! command -v conway-terminal &>/dev/null && command -v curl &>/dev/null; then
        curl -fsSL https://conway.tech/terminal.sh | sh 2>/dev/null || true
    fi
fi

# ═════════════════════════════════════════════════════════
# PHASE 3: INSTALL OPENCLAW
# ═════════════════════════════════════════════════════════
echo ""
echo "[PHASE 3] Installing OpenClaw..."

if ! command -v openclaw &>/dev/null; then
    if command -v curl &>/dev/null; then
        curl -fsSL https://openclaw.ai/install.sh | bash 2>/dev/null || true
        openclaw onboard --install-daemon 2>/dev/null || true
    fi
fi

# Configure OpenClaw MCP to point at Conway Terminal
OPENCLAW_CONFIG="${OPENCLAW_DIR}/config.json"
if [ ! -f "${OPENCLAW_CONFIG}" ]; then
    python3 -c "
import json, os, shutil
ct_path = shutil.which('conway-terminal') or 'conway-terminal'
conway_key = ''
for cpath in ['${ANIMA_DIR}/config.json', os.path.expanduser('~/.conway/config.json')]:
    if os.path.exists(cpath):
        try:
            conway_key = json.load(open(cpath)).get('apiKey', '')
            if conway_key: break
        except: pass
config = {'mcpServers': {'conway': {'command': ct_path, 'env': {'CONWAY_API_KEY': conway_key} if conway_key else {}}}}
os.makedirs('${OPENCLAW_DIR}', exist_ok=True)
with open('${OPENCLAW_CONFIG}', 'w') as f:
    json.dump(config, f, indent=2)
print('  OpenClaw MCP config written')
" 2>/dev/null || true
fi

# Install Conway skills and commands
CT_SKILLS="$(npm root -g 2>/dev/null)/conway-terminal/plugin/skills"
CT_COMMANDS="$(npm root -g 2>/dev/null)/conway-terminal/plugin/commands"
if [ -d "$CT_SKILLS/conway-automaton" ]; then
    mkdir -p "${ANIMA_DIR}/skills/conway-automaton"
    cp "$CT_SKILLS/conway-automaton/SKILL.md" "${ANIMA_DIR}/skills/conway-automaton/SKILL.md" 2>/dev/null || true
fi
if [ -d "$CT_SKILLS/conway-openclaw" ]; then
    mkdir -p "${OPENCLAW_DIR}/skills/conway"
    cp "$CT_SKILLS/conway-openclaw/SKILL.md" "${OPENCLAW_DIR}/skills/conway/SKILL.md" 2>/dev/null || true
fi
if [ -d "$CT_COMMANDS" ]; then
    mkdir -p "${ANIMA_DIR}/commands"
    cp "$CT_COMMANDS"/*.md "${ANIMA_DIR}/commands/" 2>/dev/null || true
fi

# ═════════════════════════════════════════════════════════
# PHASE 4: TEST EVERY TOOL
# ═════════════════════════════════════════════════════════
echo ""
echo "[PHASE 4] Testing every tool..."
echo ""

# --- System tools ---
for tool in curl git wget jq python3; do
    if command -v $tool &>/dev/null; then
        ver=$($tool --version 2>&1 | head -1 | cut -c1-60)
        record "$tool" "PASS" "$ver"
    else
        record "$tool" "FAIL" "not found in PATH"
    fi
done

# --- Node.js ---
if command -v node &>/dev/null; then
    ver=$(node --version 2>&1)
    record "node" "PASS" "$ver"
else
    record "node" "FAIL" "not found in PATH"
fi

if command -v npm &>/dev/null; then
    ver=$(npm --version 2>&1)
    record "npm" "PASS" "v$ver"
else
    record "npm" "FAIL" "not found in PATH"
fi

# --- Conway Terminal ---
if command -v conway-terminal &>/dev/null; then
    ver=$(conway-terminal --version 2>&1 || echo "installed")
    record "conway-terminal" "PASS" "$ver"
else
    record "conway-terminal" "FAIL" "not found — agent must install via: npm install -g conway-terminal"
fi

# --- Conway API connectivity ---
if [ -f "${ANIMA_DIR}/config.json" ]; then
    CONWAY_KEY=$(python3 -c "import json; print(json.load(open('${ANIMA_DIR}/config.json')).get('apiKey',''))" 2>/dev/null)
    if [ -n "$CONWAY_KEY" ]; then
        CREDITS=$(curl -s -m 5 -H "Authorization: Bearer $CONWAY_KEY" "https://api.conway.tech/v1/credits/balance" 2>/dev/null)
        if echo "$CREDITS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('credits_cents',0))" 2>/dev/null; then
            CVAL=$(echo "$CREDITS" | python3 -c "import sys,json; print(json.load(sys.stdin).get('credits_cents',0))" 2>/dev/null)
            record "conway-api" "PASS" "credits_cents: $CVAL"
        else
            record "conway-api" "WARN" "API returned unexpected response"
        fi
    else
        record "conway-api" "WARN" "no API key found — agent will provision on first run"
    fi
else
    record "conway-api" "WARN" "no config.json yet — agent will provision on first run"
fi

# --- Conway wallet ---
if [ -f "${ANIMA_DIR}/config.json" ]; then
    WALLET=$(python3 -c "import json; print(json.load(open('${ANIMA_DIR}/config.json')).get('walletAddress',''))" 2>/dev/null)
    if [ -n "$WALLET" ]; then
        record "wallet" "PASS" "$WALLET"
    else
        record "wallet" "WARN" "no wallet in config — engine wizard will generate"
    fi
else
    record "wallet" "WARN" "no config — engine wizard will provision wallet and API key"
fi

# --- OpenClaw ---
if command -v openclaw &>/dev/null; then
    ver=$(openclaw --version 2>&1 || echo "installed")
    record "openclaw" "PASS" "$ver"
else
    record "openclaw" "WARN" "not found — agent can install via: curl -fsSL https://openclaw.ai/install.sh | bash"
fi

# --- OpenClaw MCP config ---
if [ -f "${OPENCLAW_CONFIG}" ]; then
    record "openclaw-mcp" "PASS" "config exists at ${OPENCLAW_CONFIG}"
else
    record "openclaw-mcp" "WARN" "no MCP config — agent must create"
fi

# --- Skills ---
SKILL_COUNT=$(ls -d "${ANIMA_DIR}/skills/"*/ 2>/dev/null | wc -l)
if [ "$SKILL_COUNT" -gt 0 ]; then
    record "skills" "PASS" "$SKILL_COUNT skills loaded"
else
    record "skills" "WARN" "no skills found"
fi

# --- Telegram ---
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    # Actually test sending a message
    TG_RESULT=$(python3 -c "
import urllib.request, json
data = json.dumps({'chat_id': '$TELEGRAM_CHAT_ID', 'text': 'BOOT: Pre-flight checks running...', 'parse_mode': 'HTML'}).encode()
req = urllib.request.Request('https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage', data=data, headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    d = json.loads(resp.read())
    print('ok' if d.get('ok') else 'fail')
except Exception as e:
    print(str(e)[:80])
" 2>/dev/null)
    if [ "$TG_RESULT" = "ok" ]; then
        record "telegram" "PASS" "message sent successfully"
    else
        record "telegram" "WARN" "send failed: $TG_RESULT"
    fi
else
    # Try to extract from genesis prompt
    if [ -f "${ANIMA_DIR}/genesis-prompt.md" ]; then
        HAS_TG=$(grep -c "api.telegram.org" "${ANIMA_DIR}/genesis-prompt.md" 2>/dev/null || echo "0")
        if [ "$HAS_TG" -gt 0 ]; then
            record "telegram" "WARN" "credentials in genesis prompt but not in env — agent must use exec"
        else
            record "telegram" "WARN" "no Telegram config found"
        fi
    else
        record "telegram" "WARN" "no Telegram config found"
    fi
fi

# ═════════════════════════════════════════════════════════
# PHASE 5: WRITE BOOT REPORT
# ═════════════════════════════════════════════════════════
echo ""
echo "[PHASE 5] Writing boot report..."

TOTAL=$((PASS + FAIL + WARN))
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$REPORT" << REPORTEOF
# BOOT REPORT — ${TIMESTAMP}

## Summary
- **PASS**: ${PASS}/${TOTAL}
- **FAIL**: ${FAIL}/${TOTAL}
- **WARN**: ${WARN}/${TOTAL}

## Tool Status

| Tool | Status | Detail |
|------|--------|--------|
REPORTEOF

for r in "${RESULTS[@]}"; do
    echo "$r" >> "$REPORT"
done

if [ "$FAIL" -gt 0 ]; then
    cat >> "$REPORT" << 'FAILEOF'

## ACTION REQUIRED
Some tools FAILED verification. Fix them BEFORE doing anything else:
1. Re-run the failed installation commands
2. Verify with `<tool> --version`
3. If still failing, report to Telegram and sleep

DO NOT create goals, write specs, or plan strategies until all tools pass.
FAILEOF
else
    cat >> "$REPORT" << 'PASSEOF'

## ALL TOOLS VERIFIED
All critical tools are installed and tested. You may proceed to your mission.
The boot sequence (Steps 0-7 in genesis prompt) has been completed mechanically.
Skip to post-boot operations — verify your balance, send Telegram boot message, then execute.
PASSEOF
fi

echo ""
cat "$REPORT"

# ═════════════════════════════════════════════════════════
# PHASE 6: SEND TELEGRAM BOOT REPORT
# ═════════════════════════════════════════════════════════
echo ""
echo "[PHASE 6] Sending Telegram boot report..."

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    python3 -c "
import urllib.request, json
msg = '<b>BOOT REPORT</b>\nPASS: ${PASS}/${TOTAL} | FAIL: ${FAIL}/${TOTAL} | WARN: ${WARN}/${TOTAL}\n'
msg += 'Tools verified mechanically before engine start.\n'
msg += 'Engine starting now...'
data = json.dumps({'chat_id': '${TELEGRAM_CHAT_ID}', 'text': msg, 'parse_mode': 'HTML'}).encode()
req = urllib.request.Request('https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage', data=data, headers={'Content-Type': 'application/json'})
try: urllib.request.urlopen(req, timeout=10)
except: pass
" 2>/dev/null || true
fi

# ═════════════════════════════════════════════════════════
# PHASE 7: SET PERMISSIONS
# ═════════════════════════════════════════════════════════
chmod 700 "${AGENT_HOME}" 2>/dev/null || true
chmod 700 "${ANIMA_DIR}" 2>/dev/null || true
chmod 700 "${CONWAY_DIR}" 2>/dev/null || true
chmod 700 "${OPENCLAW_DIR}" 2>/dev/null || true

echo ""
echo "══════════════════════════════════════════════════════"
echo "  BOOTSTRAP COMPLETE — ${PASS} pass, ${FAIL} fail, ${WARN} warn"
echo "══════════════════════════════════════════════════════"
