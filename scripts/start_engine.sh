#!/bin/bash
# Anima Fund Engine Starter

cd /app/automaton

# ── Swap better-sqlite3 native addon to match current arch ──
ARCH=$(uname -m)
case "$ARCH" in
    x86_64|amd64) PREBUILD_DIR="prebuilds/linux-x64" ;;
    aarch64|arm64) PREBUILD_DIR="prebuilds/linux-arm64" ;;
esac

BSQ_PREBUILD="node_modules/better-sqlite3/${PREBUILD_DIR}/build/Release/better_sqlite3.node"
BSQ_TARGET="node_modules/better-sqlite3/build/Release/better_sqlite3.node"
if [ -f "$BSQ_PREBUILD" ]; then
    cp "$BSQ_PREBUILD" "$BSQ_TARGET" 2>/dev/null && echo "Loaded better-sqlite3 for $ARCH"
fi

# ── Find node ──
for p in /usr/bin/node /usr/local/bin/node; do
    if [ -x "$p" ]; then
        echo "Using system node: $p ($($p --version))"
        yes "" 2>/dev/null | exec "$p" dist/index.js --run
    fi
done

NODE=$(which node 2>/dev/null || command -v node 2>/dev/null)
if [ -n "$NODE" ] && [ -x "$NODE" ]; then
    echo "Using node: $NODE ($($NODE --version))"
    yes "" 2>/dev/null | exec "$NODE" dist/index.js --run
fi

if [ -x "/app/automaton/bin/node" ]; then
    echo "Using bundled node: $(/app/automaton/bin/node --version)"
    yes "" 2>/dev/null | exec /app/automaton/bin/node dist/index.js --run
fi

echo "FATAL: node not found" >&2
exit 1
