#!/bin/bash
# Anima Fund Engine Starter
# 1. Bootstraps the agent environment (Conway Terminal, OpenClaw)
# 2. Runs the single-file bundle (all JS deps inlined, native addon loaded from /app/automaton/native/)

set -e

cd /app/automaton

ARCH=$(uname -m)
echo "Architecture: $ARCH"

# Ensure the correct native addon is in the platform-neutral path as a fallback
case "$ARCH" in
    x86_64|amd64)
        cp -f native/linux-x64/better_sqlite3.node native/better_sqlite3.node 2>/dev/null || true
        ;;
    aarch64|arm64)
        cp -f native/linux-arm64/better_sqlite3.node native/better_sqlite3.node 2>/dev/null || true
        ;;
esac

echo "Native addon ready: $(ls -la native/better_sqlite3.node 2>/dev/null || echo 'NOT FOUND')"

# ─── Bootstrap agent environment (pre-install tools) ─────────────
BOOTSTRAP_SCRIPT="/app/scripts/bootstrap_agent.sh"
if [ -f "$BOOTSTRAP_SCRIPT" ]; then
    echo "Running agent bootstrap..."
    bash "$BOOTSTRAP_SCRIPT" 2>&1 || echo "Bootstrap completed with warnings (non-fatal)"
    echo ""
fi

# Find node and run the bundle
NODE=""
for p in /usr/bin/node /usr/local/bin/node /app/automaton/bin/node; do
    if [ -x "$p" ]; then
        NODE="$p"
        break
    fi
done

if [ -z "$NODE" ]; then
    NODE=$(which node 2>/dev/null || command -v node 2>/dev/null || true)
fi

if [ -z "$NODE" ] || [ ! -x "$NODE" ]; then
    echo "FATAL: node not found" >&2
    exit 1
fi

echo "Using $NODE ($($NODE --version))"
echo "Starting bundle..."

# Export Telegram credentials so agent can use them via exec tool
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
export TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# Pipe "yes" to handle any interactive prompts in the setup wizard
yes "" 2>/dev/null | exec "$NODE" dist/bundle.mjs --run
