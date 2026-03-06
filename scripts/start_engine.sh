#!/bin/bash
# Anima Fund Engine Starter
# Uses absolute paths — no dependency on PATH, sudo, or supervisor.
# The piped empty lines handle the setup wizard's readline prompts
# when auto-config.json is staged for non-interactive mode.

cd /app/automaton

# Find node — try common locations
NODE=""
for p in /usr/bin/node /usr/local/bin/node /opt/node/bin/node; do
    if [ -x "$p" ]; then
        NODE="$p"
        break
    fi
done

# Fallback: ask the shell
if [ -z "$NODE" ]; then
    NODE=$(which node 2>/dev/null)
fi

if [ -z "$NODE" ] || [ ! -x "$NODE" ]; then
    echo "FATAL: node not found" >&2
    exit 1
fi

echo "Starting Anima Fund engine with $NODE ($(${NODE} --version))"
yes "" 2>/dev/null | exec "$NODE" dist/index.js --run
