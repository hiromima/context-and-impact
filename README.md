# context-and-impact

**4層コンテキスト収集 × Agent Skill Bus × GitNexus 統合パイプライン**

[![GitHub Issues](https://img.shields.io/github/issues/ShunsukeHayashi/context-and-impact)](https://github.com/ShunsukeHayashi/context-and-impact/issues)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 概要

コード変更・Obsidian ノート参照・スキル実行の前に、4層のコンテキストを自動収集し、
Agent Skill Bus の自己改善ループと GitNexus の影響分析を統合するパイプライン。

```
Phase A: コンテキスト収集（4層）
  L1  → Grep/Find（テキスト検索）
  L2a → GitNexus（コード依存グラフ）
  L2b → GitNexus Cypher（Obsidian wikilink グラフ）
  L3  → SmartConnections（セマンティック検索）

Phase B: Context Engineering MCP（品質スコアリング）
Phase C: Agent Skill Bus（スキル探索・実行・記録）
Phase D: フィードバックループ（自己改善）
```

---

## クイックスタート

### 前提条件

- Node.js v24+
- Python 3.10+
- GitNexus CLI: `npm install -g gitnexus`
- Agent Skill Bus: `npm install -g agent-skill-bus`

### セットアップ

```bash
git clone https://github.com/ShunsukeHayashi/context-and-impact.git
cd context-and-impact
npm install
cp .env.example .env  # 環境変数設定
```

### 基本的な使い方

```bash
# L1: テキスト検索
grep -r "authMiddleware" ~/dev/products/kotowari/src/ -l

# L2a: コード影響分析
gitnexus impact authMiddleware --repo kotowari

# L2b: Obsidian wikilink 分析
gitnexus cypher --repo obsidian \
  "MATCH (f:File) WHERE f.name CONTAINS 'auth' RETURN f.name LIMIT 10"

# L3: セマンティック検索
python3 src/cli/semantic-search.py --query "JWT 認証 設計" --limit 10

# Agent Skill Bus ダッシュボード
npx agent-skill-bus dashboard
```

---

## アーキテクチャ

詳細は [docs/architecture.md](docs/architecture.md) を参照。

```
┌─────────────────────────────────────────────────────────────────┐
│                   context-and-impact v2.0.0                     │
│                                                                 │
│  Phase A: Context Collection                                    │
│  ┌─────┐  ┌──────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ L1  │  │ L2a  │  │      L2b         │  │      L3        │  │
│  │Grep │  │GitNx │  │GitNx + KùzuDB    │  │SmartConnect    │  │
│  │Find │  │Code  │  │Obsidian wikilink  │  │Semantic Search │  │
│  └──┬──┘  └──┬───┘  └────────┬─────────┘  └───────┬────────┘  │
│     └────────┴───────────────┴────────────────────-┘           │
│                        │                                        │
│  Phase B: Context Engineering MCP                               │
│  ┌──────────────────────────────────────┐                       │
│  │ quality_score < 70 → auto_optimize   │                       │
│  └──────────────────────────────────────┘                       │
│                        │                                        │
│  Phase C: Agent Skill Bus                                       │
│  ┌──────────────────────────────────────┐                       │
│  │ dashboard → enqueue → record-run     │                       │
│  └──────────────────────────────────────┘                       │
│                        │                                        │
│  Phase D: Feedback Loop                                         │
│  ┌──────────────────────────────────────┐                       │
│  │ flagged → improve → SKILL.md 更新    │                       │
│  └──────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## ディレクトリ構造

```
context-and-impact/
├── SKILL.md                    # 統合スキル定義（Claude Code / OpenClaw 共通）
├── CLAUDE.md                   # Claude Code プロジェクト指示
├── docs/
│   └── architecture.md         # 詳細アーキテクチャ図
├── skills/
│   ├── claude-code/
│   │   └── SKILL.md            # Claude Code ランタイム専用
│   └── openclaw/
│       └── SKILL.md            # OpenClaw エージェント専用
├── src/
│   ├── cli/
│   │   └── semantic-search.py  # L3 SmartConnections CLI
│   ├── gitnexus/
│   │   └── queries.md          # L2b Cypher クエリライブラリ
│   └── skill-bus/              # Agent Skill Bus 統合
└── examples/
    ├── w1-keyword-search.sh    # W1: キーワード検索
    ├── w2-impact-analysis.sh   # W2: 影響分析
    ├── w3-cross-domain.sh      # W3: ドメイン横断リンク
    ├── w4-quality-check.sh     # W4: 品質チェック
    └── w5-full-pipeline.sh     # W5: 完全パイプライン
```

---

## 統合ワークフロー

### W1: キーワード検索（最軽量）

ファイル名・関数名・Obsidian ノートをテキスト検索する。

```bash
bash examples/w1-keyword-search.sh "authMiddleware"
```

### W2: コード影響分析

コード変更前に GitNexus で blast radius を確認する。

```bash
bash examples/w2-impact-analysis.sh authMiddleware kotowari
```

### W3: ドメイン横断リンク探索

Legal ↔ Financial などのクロスドメインリンクを探索する。

```bash
bash examples/w3-cross-domain.sh Docs-Legal Docs-Financial
```

### W4: Obsidian 品質チェック

孤立ノート検出・MOC カバレッジ確認・高インバウンドノードを分析する。

```bash
bash examples/w4-quality-check.sh
```

### W5: 完全パイプライン（全フェーズ）

4層 + Context Engineering + Agent Skill Bus を全て統合する。

```bash
bash examples/w5-full-pipeline.sh "JWT 認証 KOTOWARI" kotowari
```

---

## 関連リポジトリ

| リポジトリ | 役割 |
|-----------|------|
| [agent-skill-bus](https://github.com/ShunsukeHayashi/agent-skill-bus) | Phase C の実行基盤 |
| [gitnexus-stable-ops](~/dev/tools/gitnexus-stable-ops/) | L2a / L2b の実行基盤 |
| [smart-connections-mcp](~/dev/tools/smart-connections-mcp/) | L3 の実行基盤 |

---

## ライセンス

MIT © Hayashi Shunsuke / Miyabi Society
