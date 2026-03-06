#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Anima Fund — Deployment Script
# ═══════════════════════════════════════════════════════════
#
# This script prepares and starts the Anima Fund founder AI.
#
# Prerequisites:
#   - Node.js >= 20
#   - pnpm (corepack enable && corepack prepare pnpm@latest --activate)
#   - USDC on Base in the agent's wallet (for compute/inference)
#   - USDC on Solana for creator payouts
#
# Usage:
#   ./deploy.sh              # Full setup + start
#   ./deploy.sh --build      # Build only (no start)
#   ./deploy.sh --run        # Start only (assumes already built)
#
# Creator Solana wallet: xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r
# 50% of all fund revenue goes to this wallet automatically.
#
# ═══════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANIMA_DIR="$HOME/.anima"
GENESIS_PROMPT="$SCRIPT_DIR/genesis-prompt.md"
CONSTITUTION="$SCRIPT_DIR/constitution.md"

echo ""
echo "  ═══════════════════════════════════════════════"
echo "  ║          ANIMA FUND — DEPLOYMENT            ║"
echo "  ║    Catalyzing Agentic Economies             ║"
echo "  ║                                             ║"
echo "  ║    Creator: xtmyybmR6b9pw...9sZ2r          ║"
echo "  ║    Revenue split: 50% to creator (Solana)   ║"
echo "  ═══════════════════════════════════════════════"
echo ""

# ─── Step 1: Build ──────────────────────────────────────
if [[ "$1" == "--build" ]] || [[ -z "$1" ]]; then
  echo "  [1/5] Installing dependencies..."
  cd "$SCRIPT_DIR"
  pnpm install 2>&1 | tail -3

  echo "  [2/5] Building Anima Fund runtime..."
  pnpm build 2>&1 | tail -3
  echo "  ✓ Build complete"
  echo ""
fi

if [[ "$1" == "--build" ]]; then
  echo "  Build-only mode. Run ./deploy.sh --run to start."
  exit 0
fi

# ─── Step 2: Prepare ~/.anima/ directory ────────────────
echo "  [3/5] Preparing configuration..."
mkdir -p "$ANIMA_DIR/skills"

# Install constitution (immutable, read-only)
if [ -f "$CONSTITUTION" ]; then
  cp "$CONSTITUTION" "$ANIMA_DIR/constitution.md"
  chmod 444 "$ANIMA_DIR/constitution.md"
  echo "  ✓ Constitution installed (read-only)"
else
  echo "  ⚠ Constitution not found at $CONSTITUTION"
fi

# Copy genesis prompt (the founder AI reads this on first run)
if [ -f "$GENESIS_PROMPT" ]; then
  cp "$GENESIS_PROMPT" "$ANIMA_DIR/genesis-prompt.md"
  echo "  ✓ Genesis prompt staged at $ANIMA_DIR/genesis-prompt.md"
  echo "    ($(wc -l < "$GENESIS_PROMPT") lines — the founder AI's complete operating manual)"
else
  echo "  ⚠ Genesis prompt not found at $GENESIS_PROMPT"
fi

# ─── Step 3: Install fund-specific skills ───────────────
echo ""
echo "  [4/5] Installing fund skills..."
SKILL_COUNT=0
for skill_dir in "$SCRIPT_DIR/skills/"*/; do
  if [ -f "$skill_dir/SKILL.md" ]; then
    skill_name=$(basename "$skill_dir")
    target="$ANIMA_DIR/skills/$skill_name"
    mkdir -p "$target"
    cp "$skill_dir/SKILL.md" "$target/SKILL.md"
    echo "    ✓ $skill_name"
    SKILL_COUNT=$((SKILL_COUNT + 1))
  fi
done
echo "  ✓ $SKILL_COUNT skills installed"

# ─── Step 4: Display pre-flight info ────────────────────
echo ""
echo "  [5/5] Pre-flight check..."
echo ""
echo "  ┌─────────────────────────────────────────────┐"
echo "  │  DEPLOYMENT SUMMARY                         │"
echo "  │                                             │"
echo "  │  Runtime:     Anima Fund (Automaton fork)   │"
echo "  │  Config dir:  $ANIMA_DIR"
echo "  │  Skills:      $SKILL_COUNT fund-specific skills       │"
echo "  │  Genesis:     $(wc -l < "$GENESIS_PROMPT" 2>/dev/null || echo '?') lines                          │"
echo "  │  Constitution: $(wc -l < "$CONSTITUTION" 2>/dev/null || echo '?') lines (immutable)             │"
echo "  │                                             │"
echo "  │  Creator wallet (Solana):                   │"
echo "  │  xtmyybmR6b9pwe4Xpsg6giP4FJFEjB4miCFpNp9sZ2r │"
echo "  │                                             │"
echo "  │  Revenue split: 50% → creator (automatic)   │"
echo "  │  Fee structure: 3% mgmt + 20% carry         │"
echo "  │                                             │"
echo "  │  The founder AI will:                       │"
echo "  │  1. Generate wallet & provision API key     │"
echo "  │  2. Read the genesis prompt                 │"
echo "  │  3. Begin earning to cover its own costs    │"
echo "  │  4. Build the fund when capital is ready    │"
echo "  │  5. Hire agents, fund startups, operate     │"
echo "  │  6. Send 50% of revenue to creator          │"
echo "  └─────────────────────────────────────────────┘"
echo ""

# ─── Step 5: Start the Automaton ────────────────────────
echo "  Starting Anima Fund founder AI..."
echo "  ─────────────────────────────────────────────────"
echo ""

# The Automaton's setup wizard runs on first boot.
# It will ask for name and genesis prompt interactively.
# To automate: pipe the genesis prompt file content.
# The agent reads ~/.anima/genesis-prompt.md during setup.
cd "$SCRIPT_DIR"
node dist/index.js --run
