---
name: context-and-impact
version: 2.0.0
runtime: claude-code
description: |
  4層コンテキスト収集 + Agent Skill Bus + GitNexus 統合パイプライン。
  Claude Code ランタイム専用。
triggers:
  - context
  - impact
  - コンテキスト
  - 影響分析
  - gni
  - skill bus
  - context-and-impact
---

# context-and-impact — Claude Code スキル v2.0.0

## このスキルが行うこと

コード変更・Obsidian ノート参照・スキル実行の前に、4層のコンテキストを自動収集し、
Agent Skill Bus の自己改善ループと GitNexus の影響分析を統合する。

```
Phase A: コンテキスト収集（4層）
  L1 → Grep/Find（テキスト検索）
  L2a → GitNexus（コード依存グラフ）
  L2b → GitNexus Cypher（Obsidian wikilink グラフ）
  L3 → SmartConnections（セマンティック検索）
Phase B: Context Engineering MCP（品質スコアリング）
Phase C: Agent Skill Bus（スキル探索・実行・記録）
Phase D: フィードバックループ（自己改善）
```

---

## 実行手順

### トリガー条件

以下のいずれかで自動起動する：

1. コード変更前（関数・クラス・モジュールを編集する前）
2. Obsidian ノートを参照するとき
3. スキルを選択・実行するとき
4. ユーザーが「コンテキスト」「影響分析」「gni」を言ったとき

### Step 1: L1 テキスト検索

```bash
# キーワードでファイル検索
grep -r "{キーワード}" ~/dev/ --include="*.ts" --include="*.py" -l | head -20

# Obsidian ノート検索
grep -r "{キーワード}" ~/dev/content/obsidian/ --include="*.md" -l | head -10
```

### Step 2: L2a コード依存グラフ（GitNexus）

```bash
# 影響分析（コード変更前に必ず実行）
gitnexus impact {変更対象ファイルまたは関数名}

# コンテキスト取得
gitnexus context {ファイルパス}

# Cypher クエリ（詳細）
gitnexus cypher --repo {repo} "MATCH (f:File) WHERE f.name CONTAINS '{name}' RETURN f"
```

### Step 3: L2b Obsidian wikilink グラフ（GitNexus）

```bash
# ノートのインパクト分析
gitnexus cypher --repo obsidian "
MATCH (doc:File) WHERE doc.name = '{filename.md}'
OPTIONAL MATCH (doc)-[out]->(outbound:File)
  WHERE out.reason = 'obsidian-wikilink'
OPTIONAL MATCH (inbound:File)-[inn]->(doc)
  WHERE inn.reason = 'obsidian-wikilink'
RETURN
  doc.name AS target,
  collect(DISTINCT outbound.name) AS references_to,
  collect(DISTINCT inbound.name) AS referenced_by,
  size(collect(DISTINCT inbound.name)) AS impact_count
"
```

### Step 4: L3 セマンティック検索

```bash
# SmartConnections CLI
QUERY="{検索クエリ}" python3 ~/dev/tools/context-and-impact/src/cli/semantic-search.py

# または
python3 ~/dev/tools/context-and-impact/src/cli/semantic-search.py \
  --query "{検索クエリ}" \
  --limit 10
```

### Step 5: Context Engineering（任意）

```bash
# コンテキスト品質スコアリング
# quality_score < 70 → auto_optimize_context を実行
mcp__context_engineering__analyze_context
mcp__context_engineering__auto_optimize_context
```

### Step 6: Agent Skill Bus

```bash
# スキルバスダッシュボード確認
npx agent-skill-bus dashboard

# スキル実行キュー
npx agent-skill-bus enqueue \
  --skill context-and-impact \
  --params '{"query": "{クエリ}", "target": "{対象}"}'

# 実行結果記録
npx agent-skill-bus record-run \
  --skill context-and-impact \
  --result success \
  --metrics '{"quality_score": 85, "layers_used": ["L1","L2a","L3"]}'
```

---

## 層選択ガイド

| 状況 | 使う層 | コマンド |
|------|--------|---------|
| ファイル名・関数名が分かる | L1 | `grep -r` |
| コード変更前の影響確認 | L2a | `gitnexus impact` |
| Obsidian ノートの関連確認 | L2b | `gitnexus cypher --repo obsidian` |
| 概念・意味での検索 | L3 | `semantic-search.py` |
| 全てを統合したい | A+B+C | フルパイプライン |

---

## 統合ワークフロー例

### W1: コード変更前の安全確認

```bash
# 1. L1: ファイル特定
grep -r "authMiddleware" ~/dev/products/kotowari/src/ -l

# 2. L2a: 影響範囲確認
gitnexus impact authMiddleware

# 3. 変更実行（影響が LOW なら）
# → Edit ツールで変更

# 4. Phase C: 記録
npx agent-skill-bus record-run \
  --skill context-and-impact \
  --result success \
  --metrics '{"task": "code_change", "target": "authMiddleware"}'
```

### W2: Obsidian ノート参照

```bash
# 1. L3: セマンティック検索で関連ノートを発見
python3 src/cli/semantic-search.py --query "JWT 認証 設計" --limit 5

# 2. L2b: wikilink 依存確認
gitnexus cypher --repo obsidian "
  MATCH (inbound:File)-[r]->(doc:File)
  WHERE doc.name = 'auth-design.md' AND r.reason = 'obsidian-wikilink'
  RETURN inbound.name LIMIT 10
"

# 3. 対象ノートを Read で確認
```

---

## フォールバック順序

```
L3 失敗（SmartConnections 未初期化）
  → L2b（wikilink グラフで代替）
  → L1（テキスト検索）

L2a 失敗（GitNexus インデックス未生成）
  → gitnexus analyze --path {dir}
  → L1 で継続
```

---

## 注意事項

- KùzuDB では `split()` が非対応 → `STARTS WITH` を使う
- wikilink エッジには `reason = 'obsidian-wikilink'` フィルタが必須
- コード変更前は必ず L2a を実行する（P0ルール）
- インデックスが古い場合: `gitnexus analyze --force --embeddings`
