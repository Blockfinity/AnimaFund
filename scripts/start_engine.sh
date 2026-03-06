#!/bin/bash
# Anima Fund Engine Starter

cd /app/automaton

# Try system node
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

# Use bundled node binary
if [ -x "/app/automaton/bin/node" ]; then
    echo "Using bundled node: $(/app/automaton/bin/node --version)"
    yes "" 2>/dev/null | exec /app/automaton/bin/node dist/index.js --run
fi

echo "FATAL: node not found" >&2
exit 1
