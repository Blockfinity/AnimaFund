#!/bin/bash
# Anima Fund Engine Starter
# Runs the single-file bundle (all deps inlined, no module resolution needed)

cd /app/automaton

# Swap better-sqlite3 native addon for current arch
ARCH=$(uname -m)
case "$ARCH" in
    x86_64|amd64) PREBUILD="node_modules/better-sqlite3/prebuilds/linux-x64/build/Release/better_sqlite3.node" ;;
    aarch64|arm64) PREBUILD="node_modules/better-sqlite3/prebuilds/linux-arm64/build/Release/better_sqlite3.node" ;;
esac
if [ -f "$PREBUILD" ]; then
    cp "$PREBUILD" node_modules/better-sqlite3/build/Release/better_sqlite3.node 2>/dev/null
fi

# Find node and run the bundle
for p in /usr/bin/node /usr/local/bin/node; do
    if [ -x "$p" ]; then
        echo "Using $p ($($p --version))"
        yes "" 2>/dev/null | exec "$p" dist/bundle.mjs --run
    fi
done

NODE=$(which node 2>/dev/null || command -v node 2>/dev/null)
if [ -n "$NODE" ] && [ -x "$NODE" ]; then
    echo "Using $NODE ($($NODE --version))"
    yes "" 2>/dev/null | exec "$NODE" dist/bundle.mjs --run
fi

if [ -x "/app/automaton/bin/node" ]; then
    echo "Using bundled node ($(/app/automaton/bin/node --version))"
    yes "" 2>/dev/null | exec /app/automaton/bin/node dist/bundle.mjs --run
fi

echo "FATAL: node not found" >&2
exit 1
