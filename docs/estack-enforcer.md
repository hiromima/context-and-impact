# E:Stack Enforcer — Intent→Architecture→Manifestation Execution Order

## Problem

AI agents (Claude Code, subagents) skip planning and jump straight to code changes. Rules written in CLAUDE.md ("MUST plan before implementing") are routinely ignored. Advisory hooks (exit 0) produce warnings that agents dismiss.

## Solution

**Block tool execution via exit 2 + stderr** unless an execution plan exists and has progressed to the correct phase.

```
Intent (what & why) → Architecture (impact & design) → Manifestation (implement)
```

Each phase is gated. Edit/Write/Agent calls are blocked (exit 2) until the plan reaches Manifestation phase with impact analysis completed.

## How It Works

### Claude Code Hook Spec

| Exit Code | Meaning |
|-----------|---------|
| `exit 0` | Allow tool execution |
| `exit 1` | Error (log only, **does NOT block**) |
| `exit 2` + stderr | **BLOCK** tool execution, feedback to Claude |

### Phase Gates

| Plan State | Edit/Write | Agent |
|------------|-----------|-------|
| No plan | **BLOCK** | **BLOCK** |
| Intent phase | **BLOCK** | **BLOCK** |
| Architecture phase | **BLOCK** | Allow |
| Manifestation (no impact) | **BLOCK** | Allow |
| Manifestation (impact done) | Allow | Allow |
| S complexity + Intent done | Allow | Allow |
| Non-code files (.md/.json) | Always allow | — |

### Execution Plan JSON

Stored at `.ai/execution-plan.json`:

```json
{
  "version": "1.0",
  "current_phase": "intent|architecture|manifestation|completed",
  "intent": {
    "status": "completed",
    "summary": "What and why",
    "complexity": "S|M|L|XL"
  },
  "architecture": {
    "status": "pending|completed",
    "files_analyzed": ["src/auth/login.ts"],
    "impact_checked": true,
    "design_decisions": ["Use JWT over session"]
  },
  "manifestation": {
    "status": "pending|in_progress|completed"
  }
}
```

## Quick Start

### 1. Install hooks

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "command": "PROJECT_ROOT=$(git rev-parse --show-toplevel) && \"$PROJECT_ROOT/src/enforcer/estack-enforcer.sh\"",
          "timeout": 3
        }]
      },
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "command": "PROJECT_ROOT=$(git rev-parse --show-toplevel) && \"$PROJECT_ROOT/src/enforcer/estack-enforcer.sh\"",
          "timeout": 3
        }]
      },
      {
        "matcher": "Agent",
        "hooks": [{
          "type": "command",
          "command": "PROJECT_ROOT=$(git rev-parse --show-toplevel) && \"$PROJECT_ROOT/src/enforcer/estack-enforcer.sh\"",
          "timeout": 3
        }]
      }
    ]
  }
}
```

### 2. Use the plan lifecycle

```bash
# Start: Define intent
src/enforcer/estack-plan.sh init "Add JWT auth" M "#123"

# Architecture: Analyze impact, make decisions
src/enforcer/estack-plan.sh advance
src/enforcer/estack-plan.sh add-file "src/auth/login.ts"
src/enforcer/estack-plan.sh set-impact
src/enforcer/estack-plan.sh add-decision "Use RS256 over HS256"

# Manifestation: Now Edit/Write are allowed
src/enforcer/estack-plan.sh advance

# Complete
src/enforcer/estack-plan.sh complete
src/enforcer/estack-plan.sh clean
```

## Integration with context-and-impact Pipeline

```
Phase A: Context Assembly (RRF search, GitNexus impact)
    ↓ feeds into
Architecture phase of execution-plan.json
    ↓ gates
Phase D: Multi-Agent Execution (only after Architecture complete)
```

The E:Stack Enforcer ensures Phase A context is collected before Phase D agents are dispatched.

## Design Principle: E:Stack Theory

From E:Stack (Intent→Architecture→Manifestation):

- **Intent** = Why does this change exist? (Plan)
- **Architecture** = What is the blast radius? What are the design decisions? (Impact analysis)
- **Manifestation** = The actual code change (Implementation)

Expression (how it looks) alone is not design. Structureless implementation is decoration.

## Testing

```bash
# Unit test
echo '{"tool_input":{"file_path":"src/test.ts"}}' | bash src/enforcer/estack-enforcer.sh
echo "Exit: $?"  # Should be 2 (blocked, no plan)

# Integration test: Actually call Edit in Claude Code
# and verify "PreToolUse:Edit hook error" appears
```

**IMPORTANT**: Shell unit tests alone are insufficient. Always verify with a real Claude Code Edit call that returns `PreToolUse:Edit hook error`. exit 1 does NOT block — only exit 2 does.
