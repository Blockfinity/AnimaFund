#!/bin/bash
# Install Node.js if not available (needed for Automaton engine)
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
    apt-get install -y nodejs > /dev/null 2>&1
fi

# Enable corepack for pnpm
corepack enable 2>/dev/null

# Install pnpm if not available
if ! command -v pnpm &> /dev/null; then
    npm install -g pnpm > /dev/null 2>&1
fi
