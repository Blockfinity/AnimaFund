#!/bin/bash
# Anima Fund Engine Starter
# Finds node using multiple strategies — production environments vary.

cd /app/automaton

# Strategy 1: Common absolute paths
for p in /usr/bin/node /usr/local/bin/node /opt/node/bin/node /usr/lib/code-server/lib/node; do
    if [ -x "$p" ]; then
        NODE="$p"
        break
    fi
done

# Strategy 2: which / command -v
if [ -z "$NODE" ]; then
    NODE=$(which node 2>/dev/null || command -v node 2>/dev/null)
fi

# Strategy 3: nvm / volta / fnm paths
if [ -z "$NODE" ] || [ ! -x "$NODE" ]; then
    for d in "$HOME/.nvm/versions/node"/*/bin "$HOME/.volta/bin" "$HOME/.fnm/node-versions"/*/installation/bin /usr/local/lib/nodejs/bin; do
        if [ -x "$d/node" ]; then
            NODE="$d/node"
            break
        fi
    done
fi

# Strategy 4: find from running frontend process PATH
if [ -z "$NODE" ] || [ ! -x "$NODE" ]; then
    FRONTEND_PID=$(pgrep -f "react-scripts\|yarn" | head -1)
    if [ -n "$FRONTEND_PID" ] && [ -f "/proc/$FRONTEND_PID/environ" ]; then
        FPATH=$(tr '\0' '\n' < /proc/$FRONTEND_PID/environ 2>/dev/null | grep "^PATH=" | cut -d= -f2-)
        if [ -n "$FPATH" ]; then
            IFS=':' read -ra DIRS <<< "$FPATH"
            for d in "${DIRS[@]}"; do
                if [ -x "$d/node" ]; then
                    NODE="$d/node"
                    break
                fi
            done
        fi
    fi
fi

# Strategy 5: yarn node (always works if frontend is running)
if [ -z "$NODE" ] || [ ! -x "$NODE" ]; then
    YARN=$(which yarn 2>/dev/null || command -v yarn 2>/dev/null)
    if [ -n "$YARN" ]; then
        echo "Using yarn node as fallback"
        yes "" 2>/dev/null | exec "$YARN" node dist/index.js --run
        exit $?
    fi
fi

# Strategy 6: brute force find
if [ -z "$NODE" ] || [ ! -x "$NODE" ]; then
    NODE=$(find /usr -name node -type f -executable 2>/dev/null | head -1)
fi

if [ -z "$NODE" ] || [ ! -x "$NODE" ]; then
    echo "FATAL: node not found after exhaustive search" >&2
    echo "Searched: standard paths, which, nvm, volta, fnm, frontend process PATH, yarn, find" >&2
    exit 1
fi

echo "Starting Anima Fund engine with $NODE ($(${NODE} --version))"
yes "" 2>/dev/null | exec "$NODE" dist/index.js --run
