# context-and-impact: アーキテクチャ詳細

## 全体像

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   context-and-impact v2.0.0                             │
│                   4層コンテキスト × Agent Skill Bus × GitNexus          │
└─────────────────────────────────────────────────────────────────────────┘

入力: クエリ / 変更対象ファイル / タスク説明
  │
  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase A: Context Collection（コンテキスト収集）                          │
│                                                                         │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌───────┐ │
│  │     L1         │  │     L2a        │  │     L2b        │  │  L3   │ │
│  │  Grep / Find   │  │   GitNexus     │  │ GitNexus Cypher│  │Smart  │ │
│  │  テキスト検索   │  │  コードグラフ   │  │Obsidian wikilink│ │Connect│ │
│  │                │  │  影響分析       │  │KùzuDB          │  │Semantic││
│  │ grep -r        │  │ gitnexus       │  │ MATCH (f:File) │  │Search  │ │
│  │ find . -name   │  │ impact/context │  │ WHERE ...      │  │       │ │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘  └───┬───┘ │
│          │                   │                   │               │      │
│          └───────────────────┴───────────────────┴───────────────┘      │
│                                       │                                  │
│                            コンテキストバンドル                           │
│                            (ファイル群 + 依存関係 + 意味的関連)            │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase B: Context Engineering（品質スコアリング）                          │
│                                                                         │
│  analyze_context → quality_score                                        │
│  ┌─────────────────────────────────────────────────────┐                │
│  │ quality_score >= 70 → 次フェーズへ                   │                │
│  │ quality_score < 70  → auto_optimize_context → 再評価 │                │
│  └─────────────────────────────────────────────────────┘                │
│                                                                         │
│  ※ Context Engineering MCP は任意。                                      │
│    インストール: npm install -g context-engineering-mcp                   │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase C: Agent Skill Bus（スキル探索・実行・記録）                        │
│                                                                         │
│  dashboard → 適切なスキルを選択                                           │
│  enqueue   → スキルを実行キューに追加                                     │
│  record-run → 実行結果を記録（自己改善の原料）                             │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ 7ステップ自己改善ループ（OBSERVE→ANALYZE→DIAGNOSE→               │   │
│  │   PROPOSE→EVALUATE→APPLY→RECORD）                               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Phase D: Feedback Loop（フィードバック・永続化）                           │
│                                                                         │
│  flagged → 改善フラグ確認                                                │
│  improve → SKILL.md への改善案反映                                       │
│  record  → 実行履歴の永続化                                              │
│                                                                         │
│  → 次回実行時の L3 クエリ精度・Layer 選択精度が向上                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4層の詳細

### L1: テキスト検索（最軽量、常に利用可）

**ツール**: `grep`, `find`, `Glob`
**コスト**: 最小（ローカル実行）
**精度**: ファイル名・関数名が分かる場合は高精度

```bash
# ファイル名検索
grep -r "authMiddleware" ~/dev/ --include="*.ts" -l | head -20

# Obsidian ノート全文検索
grep -r "合同会社みやび" ~/dev/content/obsidian/ --include="*.md" -l
```

**使用タイミング**: キーワードが明確、またはフォールバックとして常時

---

### L2a: コード依存グラフ（GitNexus）

**ツール**: `gitnexus impact`, `gitnexus context`, `gitnexus_impact` (MCP)
**コスト**: 中（GitNexus インデックス必要）
**精度**: 関数・クラス単位の依存関係を高精度で返す

```bash
# 影響分析（blast radius）
gitnexus impact authMiddleware --repo kotowari
# → d=1: WILL BREAK (直接呼び出し元)
# → d=2: LIKELY AFFECTED (間接依存)

# コンテキスト取得（360度ビュー）
gitnexus context src/middleware/auth.ts
```

**インデックス管理**:
```bash
# 初回インデックス化
gitnexus analyze --path ~/dev/products/kotowari/

# インデックス更新（コード変更後）
gitnexus analyze --path ~/dev/products/kotowari/ --embeddings
```

**使用タイミング**: コード変更前（必須）、関数の依存関係が不明な時

---

### L2b: Obsidian wikilink グラフ（GitNexus + KùzuDB）

**ツール**: `gitnexus cypher --repo obsidian`, `gitnexus_cypher` (MCP)
**コスト**: 中（Obsidian vault のインデックス必要）
**精度**: ノート間のリンク関係（双方向）を正確に返す

```bash
# ノートのインパクト分析
gitnexus cypher --repo obsidian "
MATCH (doc:File) WHERE doc.name = 'auth-design.md'
OPTIONAL MATCH (doc)-[out]->(outbound:File)
  WHERE out.reason = 'obsidian-wikilink'
OPTIONAL MATCH (inbound:File)-[inn]->(doc)
  WHERE inn.reason = 'obsidian-wikilink'
RETURN
  doc.name AS target,
  collect(DISTINCT outbound.name) AS references_to,
  collect(DISTINCT inbound.name) AS referenced_by
"

# ドメイン横断リンク探索（Legal ↔ Financial）
gitnexus cypher --repo obsidian "
MATCH (a:File)-[r1]->(mid:File)-[r2]->(b:File)
WHERE r1.reason = 'obsidian-wikilink'
  AND r2.reason = 'obsidian-wikilink'
  AND (a.filePath STARTS WITH 'Docs-Legal'
       OR a.filePath STARTS WITH 'Docs-Financial')
RETURN a.name, mid.name, b.name LIMIT 30
"
```

**KùzuDB の制約**:
- `split()` 関数 → 非対応。`STARTS WITH` で代替
- wikilink エッジは `reason = 'obsidian-wikilink'` フィルタ必須

**使用タイミング**: Obsidian ノートの関連確認、ドキュメント間の依存把握

---

### L3: セマンティック検索（SmartConnections）

**ツール**: `src/cli/semantic-search.py`, SmartConnections MCP
**コスト**: 高（ベクトル埋め込みインデックス必要）
**精度**: 概念・意味での検索。キーワードが不明な場合でも関連コンテンツを返す

```bash
# セマンティック検索
python3 src/cli/semantic-search.py --query "JWT 認証 設計" --limit 10
# → 0.923  Docs-Legal/auth-design.md
# → 0.871  Daily/2026-03-15.md
# → 0.834  Docs-Financial/api-security.md

# ステータス確認
python3 src/cli/semantic-search.py --status
# → Total notes: 1247
# → Embedded: 1189
# → Coverage: 95.3%
```

**前提条件**:
- Obsidian で Smart Connections プラグインをインストール・有効化
- `.smart-env/multi/*.ajson` が生成されていること
- `smart-connections-mcp` がインストール済みであること

**使用タイミング**: キーワードが不明、概念・意味での検索、L2b の補完

---

## Agent Skill Bus の役割

```
Agent Skill Bus (npm package v1.3.0)
├── dashboard  → 全スキルの状態確認・選択
├── enqueue    → スキルを実行キューに追加
├── record-run → 実行結果の記録（改善原料）
├── flagged    → 改善フラグのついたスキル確認
└── improve    → SKILL.md への改善案反映

自己改善ループ（7ステップ）:
1. OBSERVE  → 実行ログを観察
2. ANALYZE  → 失敗/成功パターンを分析
3. DIAGNOSE → 根本原因を特定
4. PROPOSE  → 改善案を提案
5. EVALUATE → 改善案を評価
6. APPLY    → SKILL.md に適用
7. RECORD   → 改善履歴を永続化
```

---

## 3層ナレッジアーキテクチャとの対応

```
┌──────────────────────────────────────────────────────┐
│  Layer 3: Obsidian                                   │  ← L3 (セマンティック) + L2b (wikilink)
│  テキスト・ルール・エージェント・コンテキスト          │
│  docs/, System/, Rules/, Agents/, Projects/          │
├──────────────────────────────────────────────────────┤
│  Layer 2: GitNexus                                   │  ← L2a (コードグラフ)
│  コードベース理解・依存グラフ・影響分析               │
│  各repoに .gitnexus/ インデックス                     │
├──────────────────────────────────────────────────────┤
│  Layer 1: ファイルシステム                            │  ← L1 (テキスト検索)
│  platform/, products/, ops/ 等                      │
└──────────────────────────────────────────────────────┘
```

context-and-impact は、この3層ナレッジアーキテクチャ全体に対するアクセスレイヤーとして機能する。

---

## フォールバック戦略

```
L3 利用不可 (SmartConnections 未初期化)
  └→ L2b で代替 (wikilink グラフ)
      └→ L1 で代替 (テキスト検索)

L2a インデックス未生成
  └→ gitnexus analyze 実行
      └→ L1 で継続

品質スコア < 70
  └→ auto_optimize_context
      └→ 追加層のデータを収集
          └→ 再評価
```

---

## 依存ツール

| ツール | バージョン | インストール |
|--------|-----------|------------|
| GitNexus | latest | `npm install -g gitnexus` |
| Agent Skill Bus | v1.3.0+ | `npm install -g agent-skill-bus` |
| Smart Connections MCP | latest | Obsidian プラグイン + MCP server |
| Context Engineering MCP | latest | `npm install -g context-engineering-mcp` |
| Python | 3.10+ | システム |
| KùzuDB | (GitNexus 依存) | GitNexus に含まれる |

---

## パフォーマンス目安

| 層 | 初回 | キャッシュ後 |
|----|------|------------|
| L1 | 1-5秒 | 即時 |
| L2a | 3-10秒 | 2-5秒 |
| L2b | 2-8秒 | 1-3秒 |
| L3 | 3-15秒 | 1-5秒 |
| フルパイプライン | 10-30秒 | 5-15秒 |
