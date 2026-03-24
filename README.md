# context-and-impact

**The Universal Context-to-Execution Pipeline for AI Agents**

> Before you change code, before you dispatch agents, before you do *anything* — run context-and-impact first.

[![GitHub Issues](https://img.shields.io/github/issues/ShunsukeHayashi/context-and-impact)](https://github.com/ShunsukeHayashi/context-and-impact/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.1.0-brightgreen)](https://github.com/ShunsukeHayashi/context-and-impact/releases)
[![Node.js](https://img.shields.io/badge/node-%3E%3D24.0.0-green)](https://nodejs.org/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-purple)](SKILL.md)

---

## What is this?

`context-and-impact` is a **5-layer context collection + execution pipeline** that integrates multiple intelligence sources before any AI agent takes action.

| Layer | Technology | What it finds |
|-------|-----------|---------------|
| **L0** | ARIA `project_memory/` | Persistent state and decisions from previous runs |
| **L1** | Glob / Grep | Exact text matches, file names, function names |
| **L2a** | **GitNexus** call graph | Code blast radius — what breaks if you change X |
| **L2b** | **GitNexus** KùzuDB | Obsidian wikilink dependencies, cross-domain links |
| **L3** | **SmartConnections** MCP | Conceptually related notes via semantic search |

Then it plans and executes through **5 phases**:

```
PHASE A: Context Assembly  →  PHASE B: Quality Gate  →  PHASE C: GNI-First DAG
                                                               ↓
PHASE E: ARIA Audit + Self-Improvement  ←  PHASE D: Multi-Agent Execution
```

---

## Why this is different

Most AI pipelines start with a prompt. This one starts with **understanding**.

| Problem | What happens without this | What happens with this |
|---------|--------------------------|----------------------|
| Blind code changes | Agent modifies a shared utility, breaks 12 downstream callers | Blast radius analyzed first; only safe changes proceed |
| Context drift | Each agent run starts from zero | `project_memory/` carries state across sessions |
| Shallow search | LLM guesses from training data | Semantic + graph search over your actual codebase |
| Cascading failures | One wrong change triggers chain of errors | Dependency DAG computed before any execution |
| No feedback loop | Same mistakes repeated | ARIA audit records every run; skills self-improve |

---

## Quick Start

### Prerequisites

- **Node.js** v24+
- **Python** 3.10+
- **GitNexus CLI**: `npm install -g gitnexus`
- **Agent Skill Bus**: `npm install -g agent-skill-bus`

### Installation

```bash
git clone https://github.com/ShunsukeHayashi/context-and-impact.git
cd context-and-impact
npm install
cp .env.example .env   # Configure your environment
```

### Basic Usage

```bash
# L1: Text search — find all references to a symbol
grep -r "authMiddleware" ./src -l

# L2a: Code impact analysis — what breaks if I change this?
gitnexus impact authMiddleware --repo my-project

# L2b: Obsidian wikilink analysis — cross-domain knowledge graph
gitnexus cypher --repo obsidian \
  "MATCH (f:File) WHERE f.name CONTAINS 'auth' RETURN f.name LIMIT 10"

# L3: Semantic search — conceptually related notes
python3 src/cli/semantic-search.py --query "JWT authentication design" --limit 10

# Agent Skill Bus dashboard
npx agent-skill-bus dashboard
```

### Run a full workflow

```bash
# W1: Keyword search (lightest)
bash examples/w1-keyword-search.sh "authMiddleware"

# W2: Code impact analysis
bash examples/w2-impact-analysis.sh authMiddleware my-project

# W5: Full pipeline (Pre-A → A → B → C → D → E)
bash examples/w5-full-pipeline.sh "JWT auth refactor" my-project

# Override quality gate threshold
QUALITY_SCORE=85 bash examples/w5-full-pipeline.sh "feature" my-project

# Force-proceed even if quality_score < 70
FORCE=1 bash examples/w5-full-pipeline.sh "hotfix" my-project
```

### v3.1.0 changes

| Phase | What's new |
|-------|-----------|
| **Pre-A** | `gitnexus status` stale check → auto reindex |
| **B** | Real `quality_score` (0–100) with threshold gates (≥85 / 70–84 / <70) |
| **C** | GNI blast radius → `project_memory/tasks.json` DAG auto-generation |
| **D** | ai-triad role matrix from DAG (parallel vs sequential tasks) |
| **E** | ARIA `worklog.md` audit trail + `cycle-ops` + self-improve score |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  context-and-impact v3.1.0                      │
│                                                                 │
│  Phase A: Context Assembly                                      │
│  ┌─────┐  ┌──────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ L1  │  │ L2a  │  │      L2b         │  │      L3        │  │
│  │Grep │  │GitNx │  │GitNx + KùzuDB    │  │SmartConnect    │  │
│  │Find │  │Code  │  │Obsidian wikilink  │  │Semantic Search │  │
│  └──┬──┘  └──┬───┘  └────────┬─────────┘  └───────┬────────┘  │
│     └────────┴───────────────┴────────────────────-┘           │
│                        │                                        │
│  Phase B: Quality Gate (Context Engineering MCP)               │
│  ┌──────────────────────────────────────┐                       │
│  │  quality_score < 70 → auto_optimize  │                       │
│  └──────────────────────────────────────┘                       │
│                        │                                        │
│  Phase C: GNI-First DAG Planning                                │
│  ┌──────────────────────────────────────┐                       │
│  │  blast_radius → tasks.json → DAG    │                       │
│  └──────────────────────────────────────┘                       │
│                        │                                        │
│  Phase D: Multi-Agent Execution                                 │
│  ┌──────────────────────────────────────┐                       │
│  │  Claude Code / Codex / OpenClaw      │                       │
│  └──────────────────────────────────────┘                       │
│                        │                                        │
│  Phase E: ARIA Audit + Self-Improvement                         │
│  ┌──────────────────────────────────────┐                       │
│  │  worklog.md → cycle-ops → improve   │                       │
│  └──────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
context-and-impact/
├── SKILL.md                    # Master skill definition (Claude Code / OpenClaw)
├── CLAUDE.md                   # Claude Code project instructions
├── docs/
│   └── architecture.md         # Detailed architecture diagrams
├── skills/
│   ├── claude-code/
│   │   └── SKILL.md            # Claude Code runtime variant
│   └── openclaw/
│       └── SKILL.md            # OpenClaw agent variant
├── src/
│   ├── cli/
│   │   └── semantic-search.py  # L3 SmartConnections CLI
│   ├── gitnexus/
│   │   └── queries.md          # L2b Cypher query library
│   └── skill-bus/              # Agent Skill Bus integration scripts
│       ├── dispatch-recommend.sh
│       ├── enqueue-task.sh
│       └── record-run.sh
└── examples/
    ├── w1-keyword-search.sh    # W1: Keyword search
    ├── w2-impact-analysis.sh   # W2: Impact analysis
    ├── w3-cross-domain.sh      # W3: Cross-domain link exploration
    ├── w4-quality-check.sh     # W4: Quality check
    ├── w5-full-pipeline.sh     # W5: Full pipeline
    └── w6-orphan-linking.sh    # W6: ARIA audit loop
```

---

## Workflows

### W1: Keyword Search (lightest)

Search file names, function names, and Obsidian notes by text.

```bash
bash examples/w1-keyword-search.sh "authMiddleware"
```

### W2: Code Impact Analysis

Check blast radius with GitNexus before making any code change.

```bash
bash examples/w2-impact-analysis.sh authMiddleware my-project
```

### W3: Cross-Domain Link Exploration

Explore cross-domain links like Legal ↔ Financial in your knowledge graph.

```bash
bash examples/w3-cross-domain.sh Docs-Legal Docs-Financial
```

### W4: Obsidian Quality Check

Detect isolated notes, check MOC coverage, and find high-inbound nodes.

```bash
bash examples/w4-quality-check.sh
```

### W5: Full Pipeline (all phases)

Integrate all 5 layers + Context Engineering + Agent Skill Bus.

```bash
bash examples/w5-full-pipeline.sh "JWT auth refactor" my-project
```

### W6: ARIA Audit Loop (self-improving)

Run the full pipeline with persistent audit trail and self-improvement cycle.

```bash
bash examples/w6-orphan-linking.sh
```

---

## Skill Constellation

`context-and-impact` is the **hub** that integrates 9 specialized skills:

```
             ┌──────────────────────────┐
             │    context-and-impact    │  ← Hub
             │       (v3.0.0)           │
             └──────────┬───────────────┘
                        │
      ┌─────────────────┼─────────────────┐
      │                 │                 │
      ▼                 ▼                 ▼
 gni-first-        task-dag-          aria-ldd-
 agent-orch        planner             add
      │                 │                 │
      ▼                 ▼                 ▼
 multi-agent-      cycle-ops         self-improving-
 orchestration                          skills
      │                 │                 │
      ▼                 ▼                 ▼
gitnexus-          obsidian-         agent-teams
impact-analysis      gni
```

---

## Related Projects

| Repository | Role |
|-----------|------|
| [agent-skill-bus](https://github.com/ShunsukeHayashi/agent-skill-bus) | Phase C execution foundation |
| [gitnexus](https://github.com/ShunsukeHayashi/gitnexus) | L2a / L2b code intelligence |

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## For Japanese Users

> **日本語ユーザーへ**: SKILL.md とドキュメントは日本語で記述されています。
> README は国際コミュニティへの公開のため英語を主とします。

詳細な日本語ドキュメントは [SKILL.md](SKILL.md) を参照してください。

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Hayashi Shunsuke / Miyabi Society
