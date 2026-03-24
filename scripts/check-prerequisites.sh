#!/usr/bin/env bash
# check-prerequisites.sh
# Run this first to see which layers are available on your machine.
# Usage: bash scripts/check-prerequisites.sh

set -uo pipefail

PASS=0; WARN=0; FAIL=0

ok()   { echo "  [OK]   $*"; PASS=$((PASS+1)); }
warn() { echo "  [WARN] $*"; WARN=$((WARN+1)); }
fail() { echo "  [FAIL] $*"; FAIL=$((FAIL+1)); }

echo ""
echo "================================================"
echo "  context-and-impact — prerequisite check"
echo "================================================"
echo ""

# ── Core ──────────────────────────────────────────────────────────────────────
echo "[ Core ]"

if command -v node &>/dev/null; then
  NODE_VER=$(node -e "process.stdout.write(process.version)")
  MAJOR=$(echo "$NODE_VER" | sed 's/v\([0-9]*\).*/\1/')
  if [ "$MAJOR" -ge 24 ]; then
    ok "Node.js $NODE_VER"
  else
    fail "Node.js $NODE_VER — v24+ required  (nvm install 24)"
  fi
else
  fail "Node.js not found  (https://nodejs.org)"
fi

if command -v python3 &>/dev/null; then
  PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
  ok "Python $PY_VER"
else
  warn "Python 3 not found — L3 semantic search will be skipped"
fi

if command -v git &>/dev/null; then
  ok "git $(git --version | awk '{print $3}')"
else
  fail "git not found"
fi

echo ""

# ── L2a/L2b: GitNexus ─────────────────────────────────────────────────────────
echo "[ L2a / L2b — GitNexus ]"

if command -v gitnexus &>/dev/null; then
  GNI_VER=$(gitnexus --version 2>/dev/null || echo "unknown")
  ok "gitnexus $GNI_VER"
else
  warn "gitnexus not found — L2a/L2b layers unavailable  (npm install -g gitnexus)"
fi

echo ""

# ── Phase C: Agent Skill Bus ──────────────────────────────────────────────────
echo "[ Phase C — Agent Skill Bus ]"

if command -v npx &>/dev/null && npx agent-skill-bus --version &>/dev/null 2>&1; then
  ok "agent-skill-bus available"
elif npm list -g agent-skill-bus &>/dev/null 2>&1; then
  ok "agent-skill-bus installed globally"
else
  warn "agent-skill-bus not found  (npm install -g agent-skill-bus)"
fi

echo ""

# ── Phase D: optional agents ──────────────────────────────────────────────────
echo "[ Phase D — optional agents ]"

if command -v codex &>/dev/null; then
  ok "codex CLI found"
else
  warn "codex not found — Codex workers unavailable  (npm install -g @openai/codex)"
fi

if command -v cursor-agent &>/dev/null; then
  ok "cursor-agent found"
else
  warn "cursor-agent not found — cursor routing unavailable"
fi

if command -v gh &>/dev/null; then
  ok "gh (GitHub CLI) found"
else
  warn "gh not found — Copilot Coding Agent routing unavailable  (https://cli.github.com)"
fi

echo ""

# ── .env ──────────────────────────────────────────────────────────────────────
echo "[ .env ]"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$ROOT_DIR/.env" ]; then
  ok ".env exists"
else
  warn ".env not found — run: cp .env.example .env  then edit it"
fi

OBSIDIAN_DIR="${OBSIDIAN_DIR:-$HOME/dev/content/obsidian}"
if [ -d "$OBSIDIAN_DIR" ]; then
  NOTE_COUNT=$(find "$OBSIDIAN_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  ok "Obsidian vault found ($NOTE_COUNT notes) at $OBSIDIAN_DIR"
else
  warn "Obsidian vault not found at $OBSIDIAN_DIR — set OBSIDIAN_DIR in .env to fix"
fi

echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
echo "================================================"
echo "  Results: ${PASS} OK  |  ${WARN} warnings  |  ${FAIL} failures"
echo "================================================"

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "  Fix the FAIL items above before running the pipeline."
  exit 1
fi

if [ "$WARN" -eq 0 ]; then
  echo ""
  echo "  All good. Try:  bash examples/w5-full-pipeline.sh \"your task\" your-repo"
fi

echo ""
