---
name: context-and-impact
version: 3.1.0
runtime: openclaw
description: |
  5層コンテキスト収集 + Agent Skill Bus + GitNexus 統合パイプライン。
  OpenClaw エージェント（CLI）専用。
triggers:
  - context
  - impact
  - コンテキスト
  - 影響分析
  - gni
  - skill bus
---

# context-and-impact — OpenClaw スキル v3.1.0

## このスキルが行うこと

OpenClaw エージェントがコード変更・ノート参照・タスク実行前に、
4層のコンテキストを収集し Agent Skill Bus と GitNexus を連携する。

---

## OpenClaw エージェントからの利用方法

### 基本コマンド

```
# スキル呼び出し（OpenClaw TUI / CLI）
@main context --query "JWT 認証 設計"
@main impact --target authMiddleware --repo kotowari

# Agent Skill Bus 経由
skill run context-and-impact --query "{クエリ}"
```

### Phase A: コンテキスト収集

エージェントが以下を順次実行する：

**L1（Grep）**
```bash
grep -r "{キーワード}" ~/dev/ --include="*.ts" -l | head -20
```

**L2a（GitNexus コードグラフ）**
```bash
gitnexus impact {対象} --repo {repo}
gitnexus context {ファイルパス}
```

**L2b（Obsidian wikilink グラフ）**
```bash
gitnexus cypher --repo obsidian "
MATCH (doc:File) WHERE doc.name = '{filename.md}'
OPTIONAL MATCH (inbound:File)-[inn]->(doc)
  WHERE inn.reason = 'obsidian-wikilink'
RETURN doc.name, collect(DISTINCT inbound.name) AS referenced_by
"
```

**L3（セマンティック検索）**

> **⚠️ Python 3.14 非対応**: `torch` / `sentence_transformers` が Python 3.14 で
> SIGSEGV クラッシュする。`semantic-search.py` は python3.11 サブプロセスを
> 自動選択するため、**必ず CLI を使うこと**。

```bash
# 状態確認（埋め込みノート数・モデル確認）
python3 ~/dev/tools/context-and-impact/src/cli/semantic-search.py --status

# 検索（推奨）
python3 ~/dev/tools/context-and-impact/src/cli/semantic-search.py --query "{クエリ}" --limit 10

# 環境変数でも可
QUERY="{クエリ}" python3 ~/dev/tools/context-and-impact/src/cli/semantic-search.py
```

### Phase C: Agent Skill Bus 連携

```bash
# スキルダッシュボード（全エージェントから参照可能）
npx agent-skill-bus dashboard

# フラグ付きスキル確認（改善候補）
npx agent-skill-bus flagged

# 実行記録（エージェントが自動記録）
npx agent-skill-bus record-run \
  --skill context-and-impact \
  --result success \
  --metrics '{...}'
```

---

## OpenClaw エージェント別の使い方

### main エージェント（全般）

```
# コンテキスト収集してタスク実行
@main: コンテキスト収集して → KOTOWARI の認証機能を修正して
```

main は自動的に：
1. L1 でコードベースを検索
2. L2a で影響範囲を確認
3. Agent Skill Bus で最適なスキルを選択
4. 実行結果を記録

### kotowari-dev エージェント

```
# KOTOWARI 専用コンテキスト
gitnexus impact {変更ファイル} --repo kotowari
python3 ~/dev/tools/context-and-impact/src/cli/semantic-search.py \
  --query "KOTOWARI {機能名}"
```

### scholar / content エージェント

```
# Obsidian ノート検索
gitnexus cypher --repo obsidian \
  "MATCH (f:File) WHERE f.name CONTAINS '{topic}' RETURN f.name, f.filePath LIMIT 20"
```

---

## ノード別の制約

| ノード | 制約 | 回避策 |
|--------|------|--------|
| Windows Gateway | xurl 依存、Python 要確認 | semantic-search.py は MacBook Pro で実行 |
| MainMini | gitnexus 利用可 | 通常通り |
| MacBook Pro | 全層利用可、python3.11 必須 | L3 は python3.11 サブプロセス自動選択（python3.14 は torch SIGSEGV）|
| Mini3 | ディスク逼迫、3D専用 | context-and-impact は使わない |

---

## 自動改善ループ（Phase D）

エージェントが `record-run` でデータを蓄積すると、
Agent Skill Bus が定期的に改善提案を生成する。

```bash
# 改善提案の確認
npx agent-skill-bus flagged

# 改善案を SKILL.md に反映
npx agent-skill-bus improve --skill context-and-impact
```

---

## 注意事項

- Mini3 は 3D 専用ノード（context-and-impact は MainMini or MacBook Pro で実行）
- **Python 3.14 + torch = SIGSEGV クラッシュ**: `mcp__smart-connections__semantic_search` も同問題で使用不可。`semantic-search.py` は python3.11 サブプロセスを自動選択するため CLI 経由で使うこと
- KùzuDB `split()` 非対応 → `STARTS WITH` 使用
- wikilink エッジは `reason = 'obsidian-wikilink'` フィルタ必須
- Anthropic 429 時は Gemini フォールバック利用（自動）
