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
# PHASE 4: FUNCTIONAL TESTS — actually USE every tool
# ═════════════════════════════════════════════════════════
echo ""
echo "[PHASE 4] Functional tests — using every tool for real..."
echo ""

TEST_DIR=$(mktemp -d)

# --- curl: download a real file ---
CURL_OUT=$(curl -s -m 10 -o "${TEST_DIR}/curl_test.html" -w "%{http_code}" "https://api.conway.tech/v1/health" 2>&1)
if [ "$CURL_OUT" = "200" ] || [ -s "${TEST_DIR}/curl_test.html" ]; then
    record "curl" "PASS" "fetched api.conway.tech/v1/health (HTTP ${CURL_OUT})"
elif command -v curl &>/dev/null; then
    # Fallback: try any URL
    CURL_OUT2=$(curl -s -m 10 -o /dev/null -w "%{http_code}" "https://example.com" 2>&1)
    if [ "$CURL_OUT2" = "200" ]; then
        record "curl" "PASS" "fetched example.com (HTTP ${CURL_OUT2})"
    else
        record "curl" "FAIL" "installed but cannot reach any URL"
    fi
else
    record "curl" "FAIL" "not found in PATH"
fi

# --- wget: download a real file ---
if command -v wget &>/dev/null; then
    wget -q -T 10 -O "${TEST_DIR}/wget_test.txt" "https://example.com" 2>/dev/null
    if [ -s "${TEST_DIR}/wget_test.txt" ]; then
        FSIZE=$(wc -c < "${TEST_DIR}/wget_test.txt")
        record "wget" "PASS" "downloaded example.com (${FSIZE} bytes)"
    else
        record "wget" "FAIL" "installed but download failed"
    fi
else
    record "wget" "FAIL" "not found in PATH"
fi

# --- git: init a repo, make a commit ---
if command -v git &>/dev/null; then
    cd "${TEST_DIR}" && git init -q test_repo && cd test_repo && \
        git config user.email "test@boot.local" && git config user.name "boot" && \
        echo "boot test" > README.md && git add . && git commit -q -m "boot test" 2>/dev/null
    if [ $? -eq 0 ]; then
        HASH=$(cd "${TEST_DIR}/test_repo" && git log --oneline -1 2>/dev/null)
        record "git" "PASS" "init + commit: ${HASH}"
    else
        record "git" "FAIL" "installed but commit failed"
    fi
    cd "${AGENT_HOME}"
else
    record "git" "FAIL" "not found in PATH"
fi

# --- jq: parse real JSON ---
if command -v jq &>/dev/null; then
    PARSED=$(echo '{"agent":"anima","status":"booting","tools":3}' | jq -r '.agent + " " + .status' 2>/dev/null)
    if [ "$PARSED" = "anima booting" ]; then
        record "jq" "PASS" "parsed JSON: ${PARSED}"
    else
        record "jq" "FAIL" "installed but parse failed"
    fi
else
    record "jq" "FAIL" "not found in PATH"
fi

# --- python3: run real computation + file I/O ---
if command -v python3 &>/dev/null; then
    PY_OUT=$(python3 -c "
import json, os, hashlib, tempfile
# Write a file
path = os.path.join('${TEST_DIR}', 'py_test.json')
data = {'agent': 'anima', 'boot': True, 'hash': hashlib.sha256(b'boot').hexdigest()[:16]}
with open(path, 'w') as f: json.dump(data, f)
# Read it back and verify
with open(path) as f: loaded = json.load(f)
assert loaded['boot'] == True
assert loaded['hash'] == hashlib.sha256(b'boot').hexdigest()[:16]
print(f'write+read+verify OK (hash={loaded[\"hash\"]})')
" 2>&1)
    if echo "$PY_OUT" | grep -q "OK"; then
        record "python3" "PASS" "$PY_OUT"
    else
        record "python3" "FAIL" "installed but test failed: $PY_OUT"
    fi
else
    record "python3" "FAIL" "not found in PATH"
fi

# --- node: run real JS + npm module check ---
if command -v node &>/dev/null; then
    NODE_OUT=$(node -e "
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
// Write and read a file
const p = path.join('${TEST_DIR}', 'node_test.json');
const data = {agent: 'anima', ts: Date.now(), hash: crypto.createHash('sha256').update('boot').digest('hex').slice(0,16)};
fs.writeFileSync(p, JSON.stringify(data));
const loaded = JSON.parse(fs.readFileSync(p, 'utf8'));
if (loaded.hash === data.hash) {
    console.log('write+read+verify OK (hash=' + loaded.hash + ')');
} else {
    console.log('FAIL: hash mismatch');
}
" 2>&1)
    if echo "$NODE_OUT" | grep -q "OK"; then
        record "node" "PASS" "$NODE_OUT"
    else
        record "node" "FAIL" "installed but test failed: $NODE_OUT"
    fi
else
    record "node" "FAIL" "not found in PATH"
fi

# --- npm: list a global package ---
if command -v npm &>/dev/null; then
    NPM_LIST=$(npm list -g --depth=0 2>/dev/null | grep conway-terminal || echo "")
    if [ -n "$NPM_LIST" ]; then
        record "npm" "PASS" "global: $NPM_LIST"
    else
        NPM_VER=$(npm --version 2>&1)
        record "npm" "PASS" "v${NPM_VER} (no global conway-terminal yet)"
    fi
else
    record "npm" "FAIL" "not found in PATH"
fi

# --- conway-terminal: actually call system_synopsis ---
if command -v conway-terminal &>/dev/null; then
    if [ -f "${ANIMA_DIR}/config.json" ]; then
        CONWAY_KEY=$(python3 -c "import json; print(json.load(open('${ANIMA_DIR}/config.json')).get('apiKey',''))" 2>/dev/null)
        if [ -n "$CONWAY_KEY" ]; then
            # Actually call the Conway API to list tools
            CT_OUT=$(CONWAY_API_KEY="$CONWAY_KEY" conway-terminal system_synopsis 2>&1 | head -5)
            if [ -n "$CT_OUT" ] && ! echo "$CT_OUT" | grep -qi "error\|fail"; then
                record "conway-terminal" "PASS" "system_synopsis returned data"
            else
                record "conway-terminal" "WARN" "installed but system_synopsis returned: ${CT_OUT:0:80}"
            fi
        else
            record "conway-terminal" "WARN" "installed ($(conway-terminal --version 2>&1)) — no API key to test live call"
        fi
    else
        record "conway-terminal" "WARN" "installed ($(conway-terminal --version 2>&1)) — no config.json yet"
    fi
else
    record "conway-terminal" "FAIL" "not found — agent must install via: npm install -g conway-terminal"
fi

# --- Conway API: actually hit the credits endpoint ---
if [ -f "${ANIMA_DIR}/config.json" ]; then
    CONWAY_KEY=$(python3 -c "import json; print(json.load(open('${ANIMA_DIR}/config.json')).get('apiKey',''))" 2>/dev/null)
    if [ -n "$CONWAY_KEY" ]; then
        CREDITS_RAW=$(curl -s -m 10 -H "Authorization: Bearer $CONWAY_KEY" "https://api.conway.tech/v1/credits/balance" 2>/dev/null)
        CVAL=$(echo "$CREDITS_RAW" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('credits_cents',0))" 2>/dev/null)
        if [ -n "$CVAL" ]; then
            DOLLARS=$(python3 -c "print(f'\${int($CVAL)/100:.2f}')" 2>/dev/null)
            record "conway-api" "PASS" "credits: $DOLLARS (${CVAL} cents)"
        else
            record "conway-api" "WARN" "API response: ${CREDITS_RAW:0:100}"
        fi
    else
        record "conway-api" "WARN" "no API key — agent will provision on first run"
    fi
else
    record "conway-api" "WARN" "no config.json — agent will provision on first run"
fi

# --- Wallet: read and validate address format ---
if [ -f "${ANIMA_DIR}/config.json" ]; then
    WALLET=$(python3 -c "
import json
w = json.load(open('${ANIMA_DIR}/config.json')).get('walletAddress','')
if w.startswith('0x') and len(w) == 42:
    print(f'VALID {w}')
elif w:
    print(f'INVALID format: {w}')
else:
    print('EMPTY')
" 2>/dev/null)
    if echo "$WALLET" | grep -q "VALID"; then
        record "wallet" "PASS" "$WALLET"
    elif echo "$WALLET" | grep -q "INVALID"; then
        record "wallet" "FAIL" "$WALLET"
    else
        record "wallet" "WARN" "no wallet in config — engine wizard will generate"
    fi
else
    record "wallet" "WARN" "no config — engine wizard will provision wallet and API key"
fi

# --- OpenClaw: actually run openclaw with a command ---
if command -v openclaw &>/dev/null; then
    OC_OUT=$(openclaw --version 2>&1 || echo "")
    if [ -n "$OC_OUT" ]; then
        # Try to list MCP servers
        OC_LIST=$(openclaw list 2>&1 | head -3 || echo "list not available")
        record "openclaw" "PASS" "${OC_OUT} | list: ${OC_LIST:0:60}"
    else
        record "openclaw" "FAIL" "installed but --version returned nothing"
    fi
else
    record "openclaw" "WARN" "not found — agent can install via: curl -fsSL https://openclaw.ai/install.sh | bash"
fi

# --- OpenClaw MCP config: verify JSON is valid ---
if [ -f "${OPENCLAW_CONFIG}" ]; then
    OC_VALID=$(python3 -c "
import json
with open('${OPENCLAW_CONFIG}') as f:
    cfg = json.load(f)
servers = list(cfg.get('mcpServers', {}).keys())
print(f'servers: {servers}')
" 2>/dev/null)
    if [ -n "$OC_VALID" ]; then
        record "openclaw-mcp" "PASS" "valid JSON — $OC_VALID"
    else
        record "openclaw-mcp" "FAIL" "config exists but invalid JSON"
    fi
else
    record "openclaw-mcp" "WARN" "no MCP config — agent must create"
fi

# --- Skills: count and list first few ---
SKILL_COUNT=$(ls -d "${ANIMA_DIR}/skills/"*/ 2>/dev/null | wc -l)
if [ "$SKILL_COUNT" -gt 0 ]; then
    FIRST_SKILLS=$(ls "${ANIMA_DIR}/skills/" 2>/dev/null | head -5 | tr '\n' ', ')
    record "skills" "PASS" "${SKILL_COUNT} loaded (${FIRST_SKILLS}...)"
else
    record "skills" "WARN" "no skills found"
fi

# --- Telegram: send a real message ---
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    TG_RESULT=$(python3 -c "
import urllib.request, json
data = json.dumps({'chat_id': '$TELEGRAM_CHAT_ID', 'text': 'BOOT: Pre-flight tool tests running...', 'parse_mode': 'HTML'}).encode()
req = urllib.request.Request('https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage', data=data, headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    d = json.loads(resp.read())
    print('sent message_id=' + str(d.get('result',{}).get('message_id','?')) if d.get('ok') else 'fail: ' + str(d))
except Exception as e:
    print('error: ' + str(e)[:80])
" 2>/dev/null)
    if echo "$TG_RESULT" | grep -q "sent"; then
        record "telegram" "PASS" "$TG_RESULT"
    else
        record "telegram" "WARN" "send failed: $TG_RESULT"
    fi
else
    if [ -f "${ANIMA_DIR}/genesis-prompt.md" ]; then
        HAS_TG=$(grep -c "api.telegram.org" "${ANIMA_DIR}/genesis-prompt.md" 2>/dev/null || echo "0")
        if [ "$HAS_TG" -gt 0 ]; then
            record "telegram" "WARN" "credentials in genesis prompt but not in env — agent uses exec"
        else
            record "telegram" "WARN" "no Telegram config found"
        fi
    else
        record "telegram" "WARN" "no Telegram config found"
    fi
fi

# Clean up test artifacts
rm -rf "${TEST_DIR}"

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
