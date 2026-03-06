#!/bin/bash
# Anima Fund Engine Starter
# Self-contained: downloads node binary if not available on the system.

cd /app/automaton

NODE_VERSION="v20.18.1"
NODE_BIN="/app/automaton/bin/node"

# ── Try system node first ──
for p in /usr/bin/node /usr/local/bin/node; do
    if [ -x "$p" ]; then
        echo "Using system node: $p ($($p --version))"
        yes "" 2>/dev/null | exec "$p" dist/index.js --run
        exit $?
    fi
done

SYS_NODE=$(which node 2>/dev/null || command -v node 2>/dev/null)
if [ -n "$SYS_NODE" ] && [ -x "$SYS_NODE" ]; then
    echo "Using system node: $SYS_NODE ($($SYS_NODE --version))"
    yes "" 2>/dev/null | exec "$SYS_NODE" dist/index.js --run
    exit $?
fi

# ── Use bundled node if already downloaded ──
if [ -x "$NODE_BIN" ]; then
    echo "Using bundled node: $NODE_BIN ($($NODE_BIN --version))"
    yes "" 2>/dev/null | exec "$NODE_BIN" dist/index.js --run
    exit $?
fi

# ── Download node binary ──
echo "Node.js not found on system. Downloading portable binary..."

ARCH=$(uname -m)
case "$ARCH" in
    x86_64|amd64) ARCH_NAME="x64" ;;
    aarch64|arm64) ARCH_NAME="arm64" ;;
    *) echo "FATAL: unsupported architecture $ARCH" >&2; exit 1 ;;
esac

TARBALL="node-${NODE_VERSION}-linux-${ARCH_NAME}.tar.xz"
URL="https://nodejs.org/dist/${NODE_VERSION}/${TARBALL}"

echo "Downloading $URL ..."
mkdir -p /app/automaton/bin

# Try curl, then wget
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$URL" | tar -xJ --strip-components=1 -C /tmp "node-${NODE_VERSION}-linux-${ARCH_NAME}/bin/node"
    mv /tmp/bin/node "$NODE_BIN" 2>/dev/null || mv /tmp/node "$NODE_BIN" 2>/dev/null
elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$URL" | tar -xJ --strip-components=1 -C /tmp "node-${NODE_VERSION}-linux-${ARCH_NAME}/bin/node"
    mv /tmp/bin/node "$NODE_BIN" 2>/dev/null || mv /tmp/node "$NODE_BIN" 2>/dev/null
else
    echo "FATAL: neither curl nor wget available" >&2
    exit 1
fi

if [ ! -x "$NODE_BIN" ]; then
    chmod +x "$NODE_BIN" 2>/dev/null
fi

if [ ! -x "$NODE_BIN" ]; then
    echo "FATAL: failed to download node binary" >&2
    exit 1
fi

echo "Downloaded node: $($NODE_BIN --version) for $ARCH_NAME"
yes "" 2>/dev/null | exec "$NODE_BIN" dist/index.js --run
