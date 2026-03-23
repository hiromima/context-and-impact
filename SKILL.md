---
name: context-and-impact
version: 2.0.0
description: >
  5層統合 Context-to-Execution パイプライン。
  コンテキスト収集（4層）→ プロンプト最適化 → スキル探索・実行 の完全フロー。
  Obsidian セマンティック検索（SmartConnections）+
  Obsidian wikilink グラフ（GitNexus KùzuDB）+
  コードインパクト分析（GitNexus call graph）+
  Agent Skill Bus（スキル健全性・タスクキュー・自己改善ループ）を統合。
trigger: >
  context, impact, search, インパクト, 影響分析, コンテキスト, 検索, 調査,
  関連, 何が壊れる, 何が関係, blast radius, 変更前, 安全確認,
  セマンティック検索, グラフ検索, vault検索, コード検索,
  スキル探索, プロンプト最適化, パイプライン, 実行計画
runtime: claude-code   # also: openclaw (see skills/openclaw/SKILL.md)
---

# Context & Impact — Context-to-Execution 完全パイプライン

## 全体アーキテクチャ

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE D: Feedback Loop（フィードバック）                         │
│  record-run → score → flagged → auto-improve                     │
├──────────────────────────────────────────────────────────────────┤
│  PHASE C: Execution（スキル探索・実行）                           │
│  ~/.claude/skills/  agentskills.io  OpenClaw 39 agents           │
│  npx agent-skill-bus enqueue/dispatch                            │
├──────────────────────────────────────────────────────────────────┤
│  PHASE B: Prompt Engineering（コンテキスト品質向上）              │
│  Context Engineering MCP (optional / 高精度タスク時)             │
│  analyze_context → auto_optimize_context → render_template       │
├──────────────────────────────────────────────────────────────────┤
│  PHASE A: Context Assembly（4層コンテキスト収集）                 │
│  ─────────────────────────────────────────────────────────────  │
│  Layer 3: Smart Connections（セマンティック）                     │
│           Obsidian vault 4,685+ notes / bge-micro-v2             │
│  ─────────────────────────────────────────────────────────────  │
│  Layer 2b: GitNexus Obsidian（wikilink グラフ / KùzuDB）         │
│  Layer 2a: GitNexus Code（コールグラフ / インパクト分析）         │
│  ─────────────────────────────────────────────────────────────  │
│  Layer 1: Glob / Grep（完全一致・正規表現）                       │
└──────────────────────────────────────────────────────────────────┘
```

---

## ゴールデンルール：どの層を使うか

| やりたいこと | 使う層 | ツール（Claude Code） | ツール（OpenClaw CLI） |
|-------------|--------|----------------------|-----------------------|
| 概念・意味でノートを探す | L3 | `mcp__smart-connections__semantic_search` | `src/cli/semantic-search.py` |
| このノートが変わると何が影響を受けるか | L2b | `gitnexus_cypher` (wikilink) | `gitnexus cypher --repo obsidian` |
| コードのXを変えたら何が壊れるか | L2a | `gitnexus_impact` | `gitnexus impact <symbol>` |
| ファイル名でファイルを探す | L1 | `Glob` | `find ~/dev -name "*keyword*"` |
| テキストを含むファイルを探す | L1 | `Grep` | `grep -rl "keyword" ~/dev/` |
| コード+ドキュメント横断調査 | L2a+L3 | 並行実行 | 並行実行 |
| コンテキスト品質を評価・最適化 | Phase B | Context Engineering MCP | curl /analyze |

---

## PHASE A: Context Assembly（4層コンテキスト収集）

### Layer 1: Glob / Grep（基盤層）

常に利用可能。他の層で見つけた候補の詳細確認に使う。

```bash
# ファイル名検索
find ~/dev/content/obsidian -name "*{キーワード}*" -type f | head -20

# テキスト内容検索（Obsidian vault）
grep -rl "{キーワード}" ~/dev/content/obsidian/ --include="*.md" | head -20

# フロントマター検索
grep -r "tags:.*{タグ名}" ~/dev/content/obsidian/ --include="*.md" | head -10

# コードベース検索
grep -rn "{関数名|クラス名}" ~/dev/products/kotowari/src/ --include="*.ts" | head -30
```

### Layer 2a: GitNexus コードグラフ

**コード変更前に必ず実行する**。

```bash
# インパクト分析（upstream: 「誰が使っているか」）
gitnexus impact {functionName} --direction upstream --min-confidence 0.8 --max-depth 3

# シンボル360°ビュー（呼び出し元・先・参加プロセス）
gitnexus context {functionName}

# コンセプト検索（実行フロー単位で返す）
gitnexus query "{payment processing}" --repo {repo-name}

# コミット前の差分影響確認
gitnexus detect-changes --scope staged
```

**リスク判定**:

| 深さ | 意味 | アクション |
|------|------|------------|
| d=1 | **WILL BREAK**: 直接の呼び出し元 | 必ず更新 |
| d=2 | LIKELY AFFECTED: 間接依存 | テスト実行 |
| d=3 | MAY NEED TESTING: 推移的 | 重要パスなら確認 |

**影響シンボル数によるリスクレベル**:
- < 5 symbols → LOW
- 5〜15 symbols → MEDIUM
- > 15 symbols → HIGH
- 認証・決済経路 → CRITICAL（数に関わらず）

### Layer 2b: GitNexus Obsidian wikilink グラフ

```bash
# キーワードでノート検索
gitnexus cypher --repo obsidian \
  "MATCH (f:File) WHERE f.name CONTAINS '{キーワード}' OR f.filePath CONTAINS '{キーワード}'
   RETURN f.name, f.filePath LIMIT 20"

# ノートのインパクト分析（参照元・参照先を全て取得）
gitnexus cypher --repo obsidian "
MATCH (doc:File) WHERE doc.name = '{filename.md}'
OPTIONAL MATCH (doc)-[out]->(outbound:File) WHERE out.reason = 'obsidian-wikilink'
OPTIONAL MATCH (inbound:File)-[inn]->(doc) WHERE inn.reason = 'obsidian-wikilink'
RETURN
  doc.name AS target,
  collect(DISTINCT outbound.name) AS references_to,
  collect(DISTINCT inbound.name) AS referenced_by,
  size(collect(DISTINCT inbound.name)) AS impact_count
"

# ドメイン横断リンク探索（Legal → Financial 等）
gitnexus cypher --repo obsidian "
MATCH (a:File)-[r1]->(mid:File)-[r2]->(b:File)
WHERE r1.reason = 'obsidian-wikilink' AND r2.reason = 'obsidian-wikilink'
  AND (a.filePath STARTS WITH 'Docs-Legal' OR a.filePath STARTS WITH 'Docs-Financial')
RETURN a.name, mid.name, b.name LIMIT 30
"

# 孤立ノート検出
gitnexus cypher --repo obsidian "
MATCH (f:File) WHERE NOT (f)<-[]-(:File) AND NOT f.filePath STARTS WITH 'Daily/'
RETURN f.name, f.filePath LIMIT 20
"
```

> **注意**: KùzuDB は `split()` 非対応。`STARTS WITH` + `CASE WHEN` で代替。
> Wikilink エッジの `reason = 'obsidian-wikilink'` フィルタ必須。

### Layer 3: Smart Connections セマンティック検索

Claude Code での使用:
```
mcp__smart-connections__semantic_search({"query": "合同会社みやび 設立 必要書類", "limit": 10})
```

OpenClaw CLI での使用（`src/cli/semantic-search.py` 参照）:
```bash
QUERY="合同会社みやび 設立 必要書類" python3 src/cli/semantic-search.py
```

**similarity スコアの目安**:
| similarity | 意味 |
|-----------|------|
| 0.9〜 | ほぼ同一トピック |
| 0.7〜0.9 | 高い関連性 |
| 0.5〜0.7 | 関連あり |
| < 0.5 | 周辺的な関連 |

---

## PHASE B: Context Engineering（プロンプト最適化）

高精度タスク時のみ起動。Context Engineering MCP バックエンドが必要。

```bash
# バックエンド起動
cd ~/dev/platform/_mcp/context_engineering_MCP
uvicorn main:app --port 8888 --reload &
python context_engineering/context_api.py &
node mcp-server/context_mcp_server.js &

# 品質評価
curl -s http://localhost:9003/analyze_context -d '{"context": "..."}' | jq .score
```

**品質スコア基準**:
- < 70点: 改善必要 → `auto_optimize_context` 実行
- 70〜85点: 標準的
- 85点以上: 高品質

---

## PHASE C: Agent Skill Bus（スキル選択・実行）

### C1: ローカルスキル探索（~/.claude/skills/）

Claude Code:
```bash
# スキル一覧
ls ~/.claude/skills/

# スキル内容検索
grep -rl "{キーワード}" ~/.claude/skills/ --include="SKILL.md" | head -10
```

### C2: agentskills.io（外部スキルライブラリ）

```bash
npx agent-skill-bus dashboard        # スキル健全性一覧
npx agent-skill-bus flagged           # スコア低下スキル
npx agent-skill-bus dashboard --days 3  # 直近3日間
```

### C3: タスクキュー投入

```bash
# タスク投入（DAG依存対応）
npx agent-skill-bus enqueue \
  --source human \
  --priority high \
  --agent {agent-id} \
  --task "{タスク内容}" \
  --depends-on "{前提タスクID}"

# ディスパッチ可能タスク確認
npx agent-skill-bus dispatch
```

### C4: OpenClaw 39エージェントへのディスパッチ

**エージェント選択基準**:

| タスク種別 | 推奨エージェント | ノード |
|-----------|-----------------|--------|
| KOTOWARI開発 | kotowari-dev (38) | MacBook Pro |
| SNS投稿・分析 | sns-creator (29) | MainMini |
| コンテンツ生成 | content (2) | MacMini2 |
| 3Dモデリング | forge3d (13) | Mini3 |
| Claude Code連携 | cc-hayashi (37) | MacBook Pro |
| プロンプト最適化 | promptpro (11) | MacMini2 |
| 汎用 | main (0) | Windows Gateway |

```bash
# OpenClaw CLI でエージェントにメッセージ送信
openclaw agent message {agent-id} "[TASK] {context付きタスク内容}"
```

### C5: 実行結果記録（必須）

```bash
npx agent-skill-bus record-run \
  --agent {agent-id} \
  --skill context-and-impact \
  --task "{タスク概要}" \
  --result {success|fail|partial} \
  --score {0.0-1.0}
```

---

## PHASE D: Feedback Loop（自己改善）

```bash
# スコア低下スキルを確認
npx agent-skill-bus flagged

# 自動改善実行
npx agent-skill-bus improve --skill context-and-impact

# 直近の実行履歴
npx agent-skill-bus dashboard --days 7
```

---

## 統合ワークフロー例

### W1: コード変更前の完全チェック（最重要）

```bash
# Step 1: コードグラフでインパクト分析
gitnexus impact AuthController --direction upstream --max-depth 3

# Step 2: 関連ドキュメントをセマンティック検索
QUERY="AuthController 認証 JWT" python3 src/cli/semantic-search.py

# Step 3: wikilink で設計ドキュメントを展開
gitnexus cypher --repo obsidian \
  "MATCH (f:File) WHERE f.name CONTAINS 'auth' RETURN f.name, f.filePath LIMIT 10"

# Step 4: 実装ファイルの確認
grep -rn "AuthController" ~/dev/products/kotowari/src/ | head -20

# Step 5: タスク投入
npx agent-skill-bus enqueue --source human --priority high \
  --agent kotowari-dev --task "認証モジュールの改修（インパクト確認済み）"
```

### W2: Obsidian ノート影響確認

```bash
# Step 1: セマンティック検索で関連ノートを発見
QUERY="{トピック}" python3 src/cli/semantic-search.py

# Step 2: wikilink 依存を展開
gitnexus cypher --repo obsidian \
  "MATCH (inbound:File)-[r]->(doc:File) WHERE doc.name = '{filename.md}'
   AND r.reason = 'obsidian-wikilink' RETURN inbound.name, inbound.filePath"

# Step 3: ファイル内容確認
cat ~/dev/content/obsidian/{path/to/note.md}
```

### W3: 未知領域の探索

```bash
# Step 1: セマンティック検索で概念的に関連するものを発見
QUERY="{未知のトピック}" python3 src/cli/semantic-search.py

# Step 2: コードグラフで実装を発見
gitnexus query "{トピック}"

# Step 3: wikilink追跡で関連ノートを広げる
gitnexus cypher --repo obsidian \
  "MATCH (f:File)-[r]->(related:File) WHERE f.name CONTAINS '{ヒット名}'
   AND r.reason = 'obsidian-wikilink' RETURN related.name, related.filePath"
```

### W4: Agent Skill Bus 健全性診断 → タスク投入

```bash
# Step 1: スキル健全性確認
npx agent-skill-bus dashboard

# Step 2: フラグ状態のスキルを確認
npx agent-skill-bus flagged

# Step 3: タスク投入
npx agent-skill-bus enqueue \
  --source human --priority high \
  --agent {agent} --task "{タスク内容}"

# Step 4: 完了後に記録
npx agent-skill-bus record-run --agent {agent} --skill context-and-impact \
  --task "{タスク}" --result success --score 0.9
```

### W5: KOTOWARI 認証移行（完全統合例）

```bash
# === PHASE A: コンテキスト収集 ===

# L3: セマンティック検索
QUERY="KOTOWARI 認証 JWT リファクタリング" python3 src/cli/semantic-search.py
# → similarity 0.87: docs/auth-design.md
# → similarity 0.82: Daily/2026-03-10.md
# → similarity 0.79: Docs-BusinessPlan/kotowari-roadmap.md

# L2b: wikilink 依存展開
gitnexus cypher --repo obsidian "
MATCH (doc:File) WHERE doc.name = 'auth-design.md'
OPTIONAL MATCH (inbound:File)-[r]->(doc) WHERE r.reason = 'obsidian-wikilink'
RETURN collect(DISTINCT inbound.name) AS referenced_by"
# → ['kotowari-architecture.md', 'api-security.md']

# L2a: コードインパクト分析
gitnexus impact AuthService --direction upstream --max-depth 3
# → d=1: LoginController, TokenRefreshController (WILL BREAK)
# → d=2: UserMiddleware (LIKELY AFFECTED)
# → Risk: MEDIUM (8 symbols)

# L1: 実装ファイル確認
grep -rn "AuthService" ~/dev/products/kotowari/src/ | head -20

# === PHASE B: プロンプト最適化 ===
# (context quality score: 87点 → 高品質なのでスキップ)

# === PHASE C: 実行 ===
npx agent-skill-bus enqueue \
  --source human --priority high \
  --agent kotowari-dev \
  --task "KOTOWARI認証リファクタリング。対象: AuthService, LoginController, TokenRefreshController。インパクト確認済み（MEDIUM）"

# === PHASE D: 記録 ===
npx agent-skill-bus record-run \
  --agent kotowari-dev --skill context-and-impact \
  --task "KOTOWARI認証移行" --result success --score 0.92
```

---

## インデックス管理

```bash
# GNI Obsidian 再インデックス（ノート追加後）
cd ~/dev/content/obsidian && gitnexus analyze --force --embeddings

# GNI コードリポジトリ再インデックス
cd ~/dev/products/kotowari && gitnexus analyze --force

# Smart Connections 埋め込み確認
python3 src/cli/semantic-search.py --status

# GNI インデックス状態確認
gitnexus status --repo obsidian
```

---

## 設定情報

| サービス | パス | 備考 |
|---------|------|------|
| Smart Connections MCP | `~/dev/tools/smart-connections-mcp/` | MacBook Pro ローカル |
| Obsidian Vault | `~/dev/content/obsidian/` | 4,685件 埋め込み済み |
| GNI repo (obsidian) | GNI内部 | 5,824ノード / 5,995エッジ |
| Context Engineering MCP | `~/dev/platform/_mcp/context_engineering_MCP/` | 要別途起動 |
| Agent Skill Bus | `~/dev/tools/agent-skill-bus/` | `npx agent-skill-bus` |
| agentskills.io | https://agentskills.io | 110+ スキル |

---

## ランタイム別実装

| ファイル | 対象 | 特徴 |
|---------|------|------|
| `skills/claude-code/SKILL.md` | Claude Code | MCP ツール使用 |
| `skills/openclaw/SKILL.md` | OpenClaw エージェント | Python CLI + gitnexus CLI |

---

*バージョン: 2.0.0 | 最終更新: 2026-03-24*
