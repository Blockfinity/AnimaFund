#!/bin/bash
# Setup Automaton engine dependencies
# Works in both development (apt available) and production (K8s container, no apt)

set -e

# Find node — it's already in the container (frontend uses it)
NODE=$(command -v node 2>/dev/null)
if [ -z "$NODE" ]; then
    # Check common container paths
    for p in /usr/bin/node /usr/local/bin/node /opt/node/bin/node; do
        [ -x "$p" ] && NODE="$p" && break
    done
fi

if [ -z "$NODE" ]; then
    echo "ERROR: Node.js not found in container"
    exit 1
fi
echo "Node: $NODE ($($NODE --version))"

# Find or install pnpm
PNPM=$(command -v pnpm 2>/dev/null)
if [ -z "$PNPM" ]; then
    echo "Installing pnpm via npm..."
    NPM=$(command -v npm 2>/dev/null)
    if [ -z "$NPM" ]; then
        echo "ERROR: npm not found"
        exit 1
    fi
    $NPM install -g pnpm --force 2>&1 | tail -2
    PNPM=$(command -v pnpm 2>/dev/null)
fi

if [ -z "$PNPM" ]; then
    echo "ERROR: pnpm not available"
    exit 1
fi
echo "pnpm: $PNPM ($($PNPM --version))"

# Install dependencies if missing
if [ ! -d "/app/automaton/node_modules" ]; then
    echo "Installing Automaton dependencies..."
    cd /app/automaton && $PNPM install --no-frozen-lockfile 2>&1 | tail -3
fi

# Build if dist missing
if [ ! -f "/app/automaton/dist/index.js" ]; then
    echo "Building Automaton..."
    cd /app/automaton && $PNPM build 2>&1 | tail -3
fi

echo "Setup complete"
