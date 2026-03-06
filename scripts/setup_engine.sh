#!/bin/bash
# Run this once on deployment to ensure Node.js and pnpm are available
# The Automaton engine requires Node.js 20+ and pnpm

set -e

# Install Node.js if not available
if ! command -v node &> /dev/null; then
    echo "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# Install pnpm if not available
if ! command -v pnpm &> /dev/null; then
    echo "Installing pnpm..."
    npm install -g pnpm
fi

# Install Automaton dependencies if node_modules missing
if [ ! -d "/app/automaton/node_modules" ]; then
    echo "Installing Automaton dependencies..."
    cd /app/automaton && pnpm install --no-frozen-lockfile
fi

# Build if dist missing
if [ ! -f "/app/automaton/dist/index.js" ]; then
    echo "Building Automaton..."
    cd /app/automaton && pnpm build
fi

echo "Setup complete: node $(node --version), pnpm $(pnpm --version)"
