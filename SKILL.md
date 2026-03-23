---
name: context-and-impact
version: 3.0.0
description: >
  The Universal Context-to-Execution Pipeline.
  最強統合スキル: コンテキスト収集（5層）→ 品質保証 → GNI-First DAG計画 →
  マルチエージェント実行 → ARIA監査フィードバックループ の完全自動化。
  Obsidian Semantic Search + GitNexus Code/Wikilink Graph +
  Agent Skill Bus + task-dag-planner + ARIA LDD/ADD +
  cycle-ops self-improvement を一つのパイプラインに統合。
trigger: >
  context, impact, search, インパクト, 影響分析, コンテキスト, 検索, 調査,
  関連, 何が壊れる, 何が関係, blast radius, 変更前, 安全確認,
  セマンティック検索, グラフ検索, vault検索, コード検索,
  スキル探索, プロンプト最適化, パイプライン, 実行計画,
  マルチエージェント, gni first, dag, 並行実装, 監査駆動, ログ駆動,
  self-improving, cycle, フィードバックループ, orchestration
runtime: claude-code   # also: openclaw (see skills/openclaw/SKILL.md)
integrates:
  # ── Tier 1: コアバンドル（必須）──────────────────────────────────
  - gni-first-agent-orchestration  # Phase C: GNI Impact First + DAG
  - task-dag-planner               # Phase C: tasks.json + task-sync.sh
  - aria-ldd-add                   # Phase E: project_memory audit trail
  - cycle-ops                      # Phase E: feedback loop (npx miyabi cycle)
  - multi-agent-orchestration      # Phase D: Codex/OpenClaw role matrix
  - self-improving-skills          # Phase E: skill-runs → SKILL.md update
  - gitnexus-impact-analysis       # Phase A2a: blast radius
  - obsidian-gni                   # Phase A2b: wikilink graph
  - agent-teams                    # Phase D: parallel sub-agents
  # ── Tier 2: 拡張バンドル（推奨）──────────────────────────────────
  - gni-ops                        # Phase A2a前処理: インデックス管理・クエリ実行
  - gitnexus-exploring             # Phase A2a探索: コード構造の理解フェーズ
  - gitnexus-cli                   # Phase A冒頭: インデックス鮮度確認・自動更新
  - obsidian-knowledge             # Phase A L3前処理: Vault同期・整備
  - ai-triad                       # Phase D前段: Claude/Codex/Gemini 最適役割判定
  - codex-workers                  # Phase D: Codex ワーカー詳細定義・運用
  - miso                           # Phase D: ミッションボード進捗リアルタイム可視化
  - graph-master                   # Phase B: ナレッジグラフ品質スコア算出
  - pen1-report                    # Phase E: 完了報告（PEN1 TUI + Telegram + X素材）
  - miyabi-omega                   # Phase A-E対応パイプライン（6段階↔5フェーズ）
---

# Context & Impact v3.0 — The Universal Context-to-Execution Pipeline

> **ゴールデン原則**: 「GNI なしに DAG は作れない。DAG なしにエージェントは動かさない。
> コンテキストなしにタスクは始まらない。」

## 全体アーキテクチャ（5フェーズ）

```
┌──────────────────────────────────────────────────────────────────┐
│  PHASE E: Feedback & Self-Improvement                            │
│  ARIA project_memory + cycle-ops + self-improving-skills         │
│  worklog.md → audit_registry.json → SKILL.md 自動更新           │
├──────────────────────────────────────────────────────────────────┤
│  PHASE D: Multi-Agent Execution（マルチエージェント実行）         │
│  Claude Code (Orchestrator) + Codex (Implementor)               │
│  + OpenClaw 39 agents + agent-teams parallel sub-agents          │
├──────────────────────────────────────────────────────────────────┤
│  PHASE C: GNI-First DAG Planning（実行計画）                     │
│  GNI blast radius → 競合マトリクス → tasks.json DAG              │
│  task-dag-planner + gni-first-agent-orchestration                │
├──────────────────────────────────────────────────────────────────┤
│  PHASE B: Context Quality Engineering（品質保証）                │
│  Context Engineering MCP (optional / 高精度タスク時)             │
│  analyze_context → auto_optimize_context → render_template       │
├──────────────────────────────────────────────────────────────────┤
│  PHASE A: Context Assembly（5層コンテキスト収集）                 │
│  ─────────────────────────────────────────────────────────────  │
│  Layer 3: Smart Connections（セマンティックベクトル検索）         │
│           Obsidian vault 4,685+ notes / bge-micro-v2             │
│  ─────────────────────────────────────────────────────────────  │
│  Layer 2b: GitNexus Obsidian（wikilink グラフ / KùzuDB）         │
│  Layer 2a: GitNexus Code（コールグラフ / blast radius）           │
│  ─────────────────────────────────────────────────────────────  │
│  Layer 1: Glob / Grep（完全一致・正規表現）                       │
│  ─────────────────────────────────────────────────────────────  │
│  Layer 0: project_memory/（ARIA 永続状態 / 前回実行ログ）         │
└──────────────────────────────────────────────────────────────────┘
```

---

## スキルコンステレーション（統合スキル全体図）

```
                    ┌─────────────────────┐
                    │  context-and-impact │ ← 本スキル（ハブ）
                    │     v3.0.0          │
                    └──────────┬──────────┘
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
    ┌─────────────┐   ┌─────────────────┐  ┌──────────────┐
    │  PHASE A    │   │   PHASE C/D     │  │   PHASE E    │
    │  コンテキスト│   │   実行計画+実行  │  │ フィードバック│
    ├─────────────┤   ├─────────────────┤  ├──────────────┤
    │gitnexus-    │   │gni-first-agent- │  │aria-ldd-add  │
    │impact-      │   │orchestration    │  │              │
    │analysis     │   ├─────────────────┤  ├──────────────┤
    ├─────────────┤   │task-dag-planner │  │cycle-ops     │
    │obsidian-gni │   ├─────────────────┤  ├──────────────┤
    ├─────────────┤   │multi-agent-     │  │self-improving│
    │gitnexus-    │   │orchestration    │  │-skills       │
    │exploring    │   ├─────────────────┤  └──────────────┘
    ├─────────────┤   │agent-teams      │
    │gitnexus-    │   ├─────────────────┤
    │debugging    │   │githubops-       │
    └─────────────┘   │workflow         │
                      └─────────────────┘
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

> **[Tier 2 gitnexus-cli] Phase A 冒頭のインデックス鮮度確認**:
> ```bash
> # インデックス状態を確認（stale なら自動更新）
> gitnexus status --repo {repo}
> # → stale の場合: gitnexus analyze --path {path} --embeddings
> # → fresh の場合: そのまま L2a 影響分析へ
> ```
> stale 判定基準: 最終インデックスから 24 時間以上経過、または未コミット変更あり。
> `gni-ops` スキルを参照してクエリ最適化・再インデックスを実行。

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

> **[Tier 2 obsidian-knowledge] Vault 鮮度確認**:
> ```bash
> # Vault の最終更新日を確認
> git -C ~/dev/content/obsidian log -1 --format="%ar"
> # → 24時間以上前の場合: obsidian-knowledge スキルで同期後に L3 検索
> # → 新鮮な場合: そのまま L3 セマンティック検索へ
> ```
> L3 ベクトルインデックス（4,685+ ノード）を最新状態で使うため、
> Vault に大量追加があった場合は Obsidian の Smart Connections プラグインで
> 再インデックスを実行してから L3 を使用すること。

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

> **[Tier 2 graph-master]** ナレッジグラフ品質スコア:
> ```bash
> # graph-master でグラフ品質を評価（孤立ノート・MOCカバレッジ確認）
> # quality_score の補正に使用: グラフ品質 < 0.6 → L2b の信頼性低下を警告
> # 詳細: ~/.claude/skills/graph-master/SKILL.md 参照
> ```

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

## PHASE C: GNI-First DAG Planning（実行計画）

> **統合スキル**: `gni-first-agent-orchestration` + `task-dag-planner`

### C-1: Blast Radius 表の作成（変更前に必須）

```bash
# 全変更シンボルについて GNI Impact を実行
gitnexus impact AuthController --direction upstream --max-depth 3
gitnexus impact AuthService --direction upstream --max-depth 3

# Blast Radius 表を作成（例）
# | タスク | シンボル     | リスク   | d=1 影響数 | アクション    |
# | T001  | AuthController | MEDIUM  | 8          | テスト追加    |
# | T002  | AuthService    | HIGH    | 16         | 段階マージ    |
```

### C-2: 競合マトリクスの作成

```
同じシンボルが d=1 に現れる → 直列化
CRITICAL リスク → 先にシグネチャ確定してから後続実装
LOW リスク → 並行可
```

### C-3: tasks.json DAG 設計

```json
{
  "tasks": [
    {
      "id": "T001",
      "title": "AuthController リファクタリング",
      "agent": "kotowari-dev",
      "risk": "MEDIUM",
      "depends_on": []
    },
    {
      "id": "T002",
      "title": "TokenRefreshController 更新（T001依存）",
      "agent": "kotowari-dev",
      "risk": "LOW",
      "depends_on": ["T001"]
    }
  ]
}
```

```bash
# 次の実行可能タスクを取得（task-dag-planner）
AGENT/task-sync.sh next

# タスクをキューに投入（依存関係付き）
npx agent-skill-bus enqueue \
  --source human --priority high \
  --agent kotowari-dev \
  --task "T001: AuthController" \
  --depends-on ""

npx agent-skill-bus enqueue \
  --source human --priority high \
  --agent kotowari-dev \
  --task "T002: TokenRefreshController" \
  --depends-on "T001"
```

---

## PHASE D: Multi-Agent Execution（マルチエージェント実行）

> **統合スキル**: `multi-agent-orchestration` + `agent-teams` + `openclaw-agents`
> **[Tier 2]**: `ai-triad` (役割判定) + `codex-workers` (Codex詳細定義) + `miso` (進捗可視化)

### D-0: エージェント役割判定（ai-triad）— Phase D 前段

> **[Tier 2 ai-triad]** タスク種別を判定し最適なエージェントを選択する:
>
> | タスク種別 | 推奨エージェント | 根拠 |
> |-----------|----------------|------|
> | コード実装・バグ修正 | Codex (`codex-workers` 参照) | 自律コーディング特化 |
> | リサーチ・調査・設計 | Claude Code | 文脈理解・推論が必要 |
> | 定型自動化・通知 | OpenClaw | 並列実行・外部連携 |
> | 画像生成 | Gemini | マルチモーダル特化 |
>
> ```bash
> # ai-triad でタスク分類（擬似コード）
> # task_type = classify(task_description)
> # → "code_impl"    → Codex ワーカーに投入（codex-workers SKILL.md 参照）
> # → "research"     → Claude Code が直接実行
> # → "automation"   → openclaw agent message {agent} "[TASK] ..."
> # → "image_gen"    → gemini CLI / Gemini API
> ```

### D-0.5: ミッションボード作成（miso）— Phase D 開始時

> **[Tier 2 miso]** Phase D 開始時に Telegram ミッションボードを作成し進捗可視化:
>
> ```bash
> # miso でミッションボード作成（Telegram 通知付き）
> # → 各エージェントのタスク割り当てをリアルタイムで可視化
> # → タスク完了ごとに Telegram に通知
> # 詳細: ~/.claude/skills/miso/SKILL.md 参照
> ```

### D-1: 役割分担マトリクス（絶対ルール）

```
┌─────────────────────────────────────────┐
│ Claude Code (Orchestrator) ← 本スキルの主体
│ ✅ コンテキスト収集・DAG 設計           │
│ ✅ Codex へのタスク投入                 │
│ ✅ 成果物レビュー・ARIA 監査            │
│ ✅ Git 操作（コミット・PR）             │
│ ✅ OpenClaw エージェント指示            │
│ ❌ コーディング（Codex に委任）         │
├─────────────────────────────────────────┤
│ Codex (Implementor)                     │
│ ✅ コード実装・バグ修正・テスト         │
│ ✅ リファクタリング・型エラー修正       │
│ ❌ アーキテクチャ設計                   │
│ ❌ git push / PR 作成                   │
├─────────────────────────────────────────┤
│ OpenClaw 39 Agents                      │
│ ✅ SNS 投稿・コンテンツ生成             │
│ ✅ 3D モデリング・PPAL 運用             │
│ ✅ Telegram 通信・報告                  │
└─────────────────────────────────────────┘
```

### D-2: エージェント選択基準

| タスク種別 | 推奨エージェント | ノード |
|-----------|-----------------|--------|
| KOTOWARI 開発 | kotowari-dev (38) | MacBook Pro |
| SNS 投稿・分析 | sns-creator (29) | MainMini |
| コンテンツ生成 | content (2) | MacMini2 |
| 3D モデリング | forge3d (13) | Mini3 |
| Claude Code 連携 | cc-hayashi (37) | MacBook Pro |
| プロンプト最適化 | promptpro (11) | MacMini2 |
| 汎用 | main (0) | Windows Gateway |

### D-3: 実行コマンド

```bash
# CPU idle 確認（50%以上が必要）
top -l 1 | grep "CPU usage"

# OpenClaw エージェントへのディスパッチ
openclaw agent message kotowari-dev "[TASK] {context付きタスク}"

# agent-teams を使った並列サブエージェント起動（Claude Code 内）
# → Claude Code の Agent Tool で並行タスクを起動
# 最大2並列（CPU負荷に注意）

# 完了通知
openclaw agent message main "[DONE] T001 完了 → 次: T002"
```

### D-4: 実行結果記録（必須）

```bash
npx agent-skill-bus record-run \
  --agent {agent-id} \
  --skill context-and-impact \
  --task "{タスク概要}" \
  --result {success|fail|partial} \
  --score {0.0-1.0}
```

---

## PHASE E: Feedback & Self-Improvement（監査・自己改善）

> **統合スキル**: `aria-ldd-add` + `cycle-ops` + `self-improving-skills`

### E-1: ARIA 監査トレイル（project_memory/）

```
project_memory/
  logs/worklog.md              ← 実行ログ（一次根拠）
  runlogs/{ts}-{op}.txt        ← 1コマンド = 1ファイル
  audit/audit_registry.json    ← 監査ルール台帳
  state/aria_state.json        ← ループ状態（loop_id, stage）
```

```bash
# ARIA 初期化（プロジェクト初回）
bash ~/dev/tools/aria-ldd-add/scripts/aria-init.sh ~/dev/tools/context-and-impact/

# worklog.md に実行ログを追記
echo "## $(date '+%Y-%m-%d %H:%M') context-and-impact W5 実行
- Phase A: L3→L2b→L2a→L1 コンテキスト収集完了
- Phase C: DAG 設計、kotowari-dev に T001/T002 を投入
- Phase D: T001 完了確認、T002 実行中
" >> project_memory/logs/worklog.md
```

### E-2: cycle-ops フィードバックループ

```bash
# フルサイクル（1回）
npx miyabi cycle full

# 連続自動サイクル（5分間隔）
npx miyabi cycle auto

# 個別フェーズ
npx miyabi cycle check      # インフラ・スキル状態検知
npx miyabi cycle dispatch   # キューから次タスク取得
npx miyabi cycle health     # スキルヘルスチェック
npx miyabi cycle report     # 音声で結果報告
```

### E-3: self-improving-skills ループ

```bash
# スコア低下スキルを確認
npx agent-skill-bus flagged

# 自動改善実行（OBSERVE→ANALYZE→DIAGNOSE→PROPOSE→EVALUATE→APPLY→RECORD）
npx agent-skill-bus improve --skill context-and-impact

# 直近の実行履歴
npx agent-skill-bus dashboard --days 7
```

### E-4: pen1-report 完了報告 — [Tier 2] Phase E 最終ステップ

> **[Tier 2 pen1-report]** Phase E 完了時に自動通知:
>
> ```bash
> # pen1-report でタスク完了を報告
> # → PEN1 TUI に結果サマリー表示
> # → Telegram に完了通知送信
> # → X（Twitter）投稿素材を生成
> # 詳細: ~/.claude/skills/pen1-report/SKILL.md 参照
> ```
>
> | 報告先 | 内容 | 条件 |
> |--------|------|------|
> | PEN1 TUI | タスクID・品質スコア・所要時間 | 常時 |
> | Telegram | 完了通知（Inline Button付き） | Phase D 完了後 |
> | X素材 | 成果サマリー（下書き） | quality_score ≥ 85 時のみ |

---

## 統合ワークフロー例（W1〜W6）

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

### W6: ARIA監査付き完全自動ループ（最高精度モード）

```bash
# === 事前: project_memory 初期化 ===
bash ~/dev/tools/aria-ldd-add/scripts/aria-init.sh .

# === PHASE A: Layer 0 → 前回ログを参照 ===
cat project_memory/logs/worklog.md | tail -30

# === PHASE A: L3 → L1 コンテキスト収集 ===
QUERY="認証リファクタリング JWT" python3 src/cli/semantic-search.py --limit 8
gitnexus cypher --repo obsidian "MATCH (f:File) WHERE f.name CONTAINS 'auth' RETURN f.name LIMIT 10"
gitnexus impact AuthService --direction upstream --max-depth 3
grep -rn "AuthService" ~/dev/products/kotowari/src/ | head -10

# === PHASE C: GNI-First DAG 設計 ===
# (blast radius 確認 → tasks.json 作成 → task-sync.sh で順序確定)
cat << 'EOF' > project_memory/tasks.json
{"tasks": [{"id": "T001", "title": "AuthService 移行", "agent": "kotowari-dev", "depends_on": []}]}
EOF

# === PHASE D: 実行 + 記録 ===
openclaw agent message kotowari-dev "[TASK] #T001 AuthService JWT→Session移行。GNI Risk: MEDIUM。依存: LoginController, TokenRefreshController"
npx agent-skill-bus record-run --agent kotowari-dev --skill context-and-impact --task "T001 AuthService" --result success --score 0.93

# === PHASE E: ARIA 監査ログ追記 ===
echo "## $(date '+%Y-%m-%d %H:%M') W6 完了
- T001: AuthService 移行完了 (score: 0.93)
- GNI blast radius: MEDIUM (8 symbols)
" >> project_memory/logs/worklog.md

# === PHASE E: cycle-ops フィードバック ===
npx miyabi cycle full
```

---

## miyabi-omega との 1:1 マッピング

> **[Tier 2 miyabi-omega]** miyabi-omega の6段階と context-and-impact の対応フェーズ:

```
miyabi-omega の6段階           context-and-impact の対応フェーズ
────────────────────────────────────────────────────────────────
段階1: 分析（Analysis）    ↔   Phase A: Context Assembly (L0-L3)
段階2: 計画（Planning）    ↔   Phase B: Quality Gate + Phase C: GNI-First DAG
段階3: 実行（Execution）   ↔   Phase D: Multi-Agent Execution
段階4: テスト（Testing）   ↔   Phase E: ARIA Audit（一部）
段階5: デプロイ（Deploy）  ↔   miyabi-ship スキル
段階6: 報告（Report）      ↔   pen1-report スキル
```

### 統合呼び出しパターン

```bash
# miyabi-omega からの呼び出し（各段階で context-and-impact を使用）
# 段階1: miyabi omega analyze → Phase A 自動実行
# 段階2: miyabi omega plan   → Phase B + C 自動実行
# 段階3: miyabi omega exec   → Phase D 自動実行
# 段階4: miyabi omega test   → Phase E (audit) 自動実行
# 段階5: miyabi ship
# 段階6: pen1-report

# context-and-impact から miyabi-ship へのハンドオフ
# Phase D 完了後、品質スコア ≥ 70 なら自動的に miyabi-ship に引き渡し
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
| ARIA ldd-add | `~/dev/tools/aria-ldd-add/` | project_memory/ 管理 |
| agentskills.io | https://agentskills.io | 110+ スキル |
| GitHub | https://github.com/ShunsukeHayashi/context-and-impact | 公開リポジトリ |

---

## ランタイム別実装

| ファイル | 対象 | 特徴 |
|---------|------|------|
| `skills/claude-code/SKILL.md` | Claude Code | MCP ツール使用 |
| `skills/openclaw/SKILL.md` | OpenClaw エージェント | Python CLI + gitnexus CLI |

---

*バージョン: 3.0.0 | 最終更新: 2026-03-24 | GitHub: ShunsukeHayashi/context-and-impact*
