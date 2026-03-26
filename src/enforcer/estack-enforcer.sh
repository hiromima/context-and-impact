#!/bin/bash
# estack-enforcer.sh — E:Stack Execution Order Enforcer for Claude Code
#
# Enforces Intent→Architecture→Manifestation order via PreToolUse hook.
# Blocks Edit/Write/Agent tool calls (exit 2 + stderr) unless execution plan
# has progressed to the correct phase.
#
# Claude Code hook spec:
#   exit 0 = allow
#   exit 2 + stderr = BLOCK (feedback to Claude)
#   exit 1 = error (log only, does NOT block)
#
# Usage: Register in .claude/settings.json PreToolUse(Edit,Write,Agent)
#   {
#     "matcher": "Edit",
#     "hooks": [{
#       "type": "command",
#       "command": "PROJECT_ROOT=$(git rev-parse --show-toplevel) && \"$PROJECT_ROOT/src/enforcer/estack-enforcer.sh\"",
#       "timeout": 3
#     }]
#   }
#
# Requires: .ai/execution-plan.json (created by estack-plan.sh)
set -uo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
PLAN_FILE="$PROJECT_ROOT/.ai/execution-plan.json"

# Read tool input from stdin
INPUT=$(cat 2>/dev/null) || INPUT="{}"

# Extract file_path for Edit/Write
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    ti = data.get('tool_input', {})
    print(ti.get('file_path', ''))
except:
    pass
" 2>/dev/null)

# Skip non-code files
if [ -n "$FILE_PATH" ]; then
  REL_PATH="${FILE_PATH#$PROJECT_ROOT/}"
  case "$REL_PATH" in
    .claude/*|.ai/*|docs/*|knowledge/*|.gitignore|.env*|*.md|*.json|*.yml|*.yaml|*.txt|*.sh|*.css|*.html)
      exit 0
      ;;
  esac
fi

# No plan file → block
if [ ! -f "$PLAN_FILE" ]; then
  if [ -z "$FILE_PATH" ]; then
    echo "E:STACK ENFORCER: No execution plan found. Create .ai/execution-plan.json before dispatching agents." >&2
    exit 2
  fi
  echo "E:STACK ENFORCER: No execution plan. Code changes blocked. Create .ai/execution-plan.json first. Target: ${REL_PATH}" >&2
  exit 2
fi

# Check phase
PHASE_CHECK=$(python3 -c "
import json, sys
try:
    with open('$PLAN_FILE') as f:
        plan = json.load(f)
except:
    print('error'); sys.exit(0)

phase = plan.get('current_phase', 'unknown')
intent_status = plan.get('intent', {}).get('status', 'pending')
impact = plan.get('architecture', {}).get('impact_checked', False)
complexity = plan.get('intent', {}).get('complexity', 'M')
bypass = plan.get('bypass', False)

if bypass: print('allow:bypass'); sys.exit(0)
if complexity == 'S' and intent_status == 'completed': print('allow:small'); sys.exit(0)
if phase == 'intent': print('block:intent')
elif phase == 'architecture': print('block:architecture')
elif phase == 'manifestation':
    print('allow:manifestation' if impact else 'block:no_impact')
elif phase == 'completed': print('allow:completed')
else: print('block:unknown')
" 2>/dev/null)

case "$PHASE_CHECK" in
  allow:*) exit 0 ;;
  block:intent) echo "E:STACK ENFORCER: Intent phase incomplete. Define what and why before proceeding." >&2; exit 2 ;;
  block:architecture) echo "E:STACK ENFORCER: Architecture phase incomplete. Complete impact analysis and design before implementation." >&2; exit 2 ;;
  block:no_impact) echo "E:STACK ENFORCER: Impact analysis not completed. Run impact analysis before code changes." >&2; exit 2 ;;
  block:*) echo "E:STACK ENFORCER: Unknown phase. Check execution plan." >&2; exit 2 ;;
  error) exit 0 ;;
  *) exit 0 ;;
esac
