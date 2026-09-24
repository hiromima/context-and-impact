# context-and-impact

**The Universal Context-to-Execution Pipeline for AI Agents**

> Before you change code, before you dispatch agents, before you do *anything* — run context-and-impact first.

[![GitHub Issues](https://img.shields.io/github/issues/ShunsukeHayashi/context-and-impact)](https://github.com/ShunsukeHayashi/context-and-impact/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.2.0-brightgreen)](https://github.com/ShunsukeHayashi/context-and-impact/releases)
[![Tests](https://img.shields.io/badge/tests-71%20passed-brightgreen)](#testing)
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
 A-0: Temporal Decay            B-0: Ensemble Gate             ↓
 A-5: RRF Fusion                (3 parallel LLM judges)
                                                      PHASE D: Multi-Agent Execution
                                                       D-2: Multi-model Classifier
                                                               ↓
PHASE E: ARIA Audit + Self-Improvement  ←──────────────────────┘
```

---

## Why this is different

Most AI pipelines start with a prompt. This one starts with **understanding**.

| Problem | What happens without this | What happens with this |
|---------|--------------------------|----------------------|
| Blind code changes | Agent modifies a shared utility, breaks 12 downstream callers | Blast radius analyzed first; only safe changes proceed |
| Context drift | Each agent run starts from zero | `project_memory/` carries state across sessions |
| Shallow search | LLM guesses from training data | Semantic + graph search over your actual codebase |
| Stale context | Old decisions outweigh recent ones | Temporal decay scores older entries lower (49.7% at 7 days) |
| Single-source ranking | L1 noise drowns out real hits | RRF fuses L1+L2b+L3 scores — `1/(k+rank)`, k=60 |
| Subjective quality gates | One LLM judge has high variance | 3-judge ensemble; mean < 70 → block, stddev > 20 → collect_more, no API key / judge failure → unavailable (exit 2) |
| Wrong agent for the task | Every task goes to one agent | 3-model majority vote routes fix→cursor / feat→copilot |
| Cascading failures | One wrong change triggers chain of errors | Dependency DAG computed before any execution |
| No feedback loop | Same mistakes repeated | ARIA audit records every run; skills self-improve |

---

## Quick Start

### 1. Clone and verify prerequisites

```bash
git clone https://github.com/ShunsukeHayashi/context-and-impact.git
cd context-and-impact
bash scripts/check-prerequisites.sh   # See what's available on your machine
```

The checker reports OK / WARN / FAIL for each dependency:

| Layer | Required | Install if missing |
|-------|----------|--------------------|
| Core | Node.js v24+, git | `nvm install 24` |
| L2a/L2b | gitnexus CLI | `npm install -g gitnexus` |
| Phase C | agent-skill-bus | `npm install -g agent-skill-bus` |
| Phase D (opt) | codex, gh CLI | `npm install -g @openai/codex` / [cli.github.com](https://cli.github.com) |

WARN items are optional — the pipeline gracefully skips unavailable layers.
FAIL items (Node.js, git) must be fixed before running.

### 2. Configure environment

```bash
cp .env.example .env   # Copy template
$EDITOR .env           # Set DEV_DIR, OBSIDIAN_DIR (optional)
```

Key variables (all optional with sensible defaults):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DEV_DIR` | `~/dev` | Root of your dev workspace |
| `OBSIDIAN_DIR` | `~/dev/content/obsidian` | Obsidian vault for L2b/L3 |
| `QUALITY_SCORE` | auto-detected | Override context quality (0–100) |
| `FORCE` | `0` | Set to `1` to skip quality gate |
| `DRY_RUN` | `0` | Set to `1` to preview without acting |

### 3. Install and run

```bash
npm install
bash examples/w5-full-pipeline.sh "your task description" your-repo
```

### Individual layer commands

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

# A-0: Temporal decay — score worklog.md entries by recency
python3 src/cli/temporal-score.py --worklog project_memory/worklog.md \
  --query "auth refactor" --limit 5

# A-5: RRF fusion — merge L1 + L2b + L3 result files
python3 src/cli/rrf-merge.py \
  --l1 /tmp/ctx-l1.json --l2b /tmp/ctx-l2b.json --l3 /tmp/ctx-l3.json \
  --limit 20

# B-0: Ensemble quality gate — 3-judge scoring
python3 src/quality/ensemble-judge.py \
  --task "refactor auth module" --context "$(cat /tmp/ctx-rrf.json)" \
  --model claude-haiku-4-5-20251001

# D-2: Task classifier — route to the right agent
python3 src/routing/multi-classifier.py --task "fix: handle null response"

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

### v3.2.0 changes (aggregator-v1 sprint)

| Phase | What's new | Module |
|-------|-----------|--------|
| **A-0** | Temporal Memory Decay — `exp(-0.1 × days)` scoring of `worklog.md` entries | `src/cli/temporal-score.py` |
| **A-5** | RRF Fusion — fuse L1+L2b+L3 results via `1/(k+rank)`, k=60 | `src/cli/rrf-merge.py` |
| **B-0** | Ensemble Quality Gate — 3 parallel LLM judges, mean<70 → `block`, stddev>20 → `collect_more`, judge failure → `unavailable` | `src/quality/ensemble_judge.py` |
| **D-2** | Multi-model Task Classifier — 3-model majority vote routing | `src/routing/multi_classifier.py` |
| **All** | 64 unit tests (13 RRF + 19 Temporal + 8 Ensemble + 24 Classifier) | `src/*/test_*.py` |

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
┌───────────────────────────────────────────────────────────────────────┐
│                     context-and-impact v3.2.0                         │
│                                                                       │
│  Phase A: Context Assembly                                            │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │ A-0: Temporal Decay  │  L1   │  L2a  │    L2b    │    L3    │     │
│  │ worklog.md entries   │ Grep  │ GitNx │ KùzuDB    │ Semantic │     │
│  │ exp(-0.1×days) score │ Find  │ Code  │ wikilinks │  Search  │     │
│  └──────────┬───────────┴───────┴───────┴───────────┴──────────┘     │
│             │  A-5: RRF Fusion — 1/(k+rank), k=60                    │
│             │  merge L1 + L2b + L3 into ranked unified list          │
│             ▼                                                         │
│  Phase B: Quality Gate                                                │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │ B-0: Ensemble Gate — 3 parallel LLM judges                   │     │
│  │  avg_score ≥ 70 → proceed  │  stddev > 20 → collect_more     │     │
│  └──────────────────────────────────────────────────────────────┘     │
│             │                                                         │
│  Phase C: GNI-First DAG Planning                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  blast_radius → tasks.json → dependency DAG                  │     │
│  └──────────────────────────────────────────────────────────────┘     │
│             │                                                         │
│  Phase D: Multi-Agent Execution                                       │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │ D-2: Multi-model Classifier — 3-model majority vote          │     │
│  │  fix/bug → cursor-agent  │  feat/docs/test → @copilot        │     │
│  │  kaede/dev-coder → [auto] Pipeline  │  else → manual         │     │
│  └──────────────────────────────────────────────────────────────┘     │
│             │                                                         │
│  Phase E: ARIA Audit + Self-Improvement                               │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  worklog.md → cycle-ops → self-improve → Copilot PR monitor  │     │
│  └──────────────────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
context-and-impact/
├── SKILL.md                    # Master skill definition (Claude Code / OpenClaw)
├── CLAUDE.md                   # Claude Code project instructions
├── .env.example                # Environment variable template (copy to .env)
├── scripts/
│   └── check-prerequisites.sh  # Verify all dependencies before first run
├── docs/
│   └── architecture.md         # Detailed architecture diagrams
├── skills/
│   ├── claude-code/
│   │   └── SKILL.md            # Claude Code runtime variant
│   └── openclaw/
│       └── SKILL.md            # OpenClaw agent variant
├── src/
│   ├── cli/
│   │   ├── semantic-search.py      # L3 SmartConnections CLI
│   │   ├── rrf-merge.py            # A-5: RRF Aggregator (L1+L2b+L3 fusion)
│   │   ├── temporal-score.py       # A-0: Temporal Memory Decay scorer
│   │   ├── test_rrf_merge.py       # 13 unit tests
│   │   └── test_temporal_score.py  # 19 unit tests
│   ├── quality/
│   │   ├── ensemble_judge.py       # B-0: Ensemble Quality Gate (importable)
│   │   ├── ensemble-judge.py       # B-0: CLI shim
│   │   └── test_ensemble_judge.py  # 16 unit tests
│   ├── routing/
│   │   ├── multi_classifier.py     # D-2: Multi-model Task Classifier
│   │   ├── multi-classifier.py     # D-2: CLI wrapper
│   │   └── test_multi_classifier.py # 24 unit tests
│   ├── gitnexus/
│   │   └── queries.md              # L2b Cypher query library
│   └── skill-bus/                  # Agent Skill Bus integration scripts
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

## Testing

All modules ship with unit tests. Run them with:

```bash
python3 -m pytest src/ -q
# 71 passed
```

| Module | Tests | What's covered |
|--------|-------|---------------|
| `src/cli/rrf-merge.py` | 13 | Score formula, multi-layer merge, k parameter, edge cases |
| `src/cli/temporal-score.py` | 19 | Decay curve, 0-day=1.000, 7-day=0.497, 30-day=0.050 |
| `src/quality/ensemble_judge.py` | 16 | Fail-closed without API key / on judge failure, block below 70, stddev gate, score parsing |
| `src/routing/multi_classifier.py` | 24 | fix→cursor-agent, feat→copilot, docs→copilot (100% accuracy) |

---

## Skill Constellation

`context-and-impact` is the **hub** that integrates 9 specialized skills:

```
             ┌──────────────────────────┐
             │    context-and-impact    │  ← Hub
             │       (v3.2.0)           │
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
