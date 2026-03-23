# エージェント別クイックリファレンス

> **Progressive Disclosure Level 1** — エージェントはこのファイルを読めば即実行できる

---

## Level 0: エントリーポイント

| ファイル | 目的 |
|---------|------|
| `SKILL.md` | 全エージェント共通の最重要定義 |
| `CLAUDE.md` | Claude Code エージェント向け |
| `skills/claude-code/SKILL.md` | Claude Code ランタイム詳細 |
| `skills/openclaw/SKILL.md` | OpenClaw ランタイム詳細 |

---

## エージェント別コマンドセット

### main エージェント（汎用）

```bash
# 毎回のタスク前に実行
bash examples/w5-full-pipeline.sh "{タスク説明}" kotowari

# 孤立ノートの週次チェック（自動実行設定推奨）
bash examples/w6-orphan-linking.sh --auto
```

### kotowari-dev エージェント（KOTOWARI 専用開発）

```bash
# コード変更前（必須）
gitnexus impact {変更関数} --repo kotowari

# 関連ノート検索
python3 src/cli/semantic-search.py --query "KOTOWARI {機能名}"
```

### scholar / content エージェント（Obsidian ナレッジ）

```bash
# ノート検索（L2b）
gitnexus cypher --repo obsidian \
  "MATCH (f:File) WHERE f.name CONTAINS '{topic}' RETURN f.name LIMIT 20"

# 孤立ノートの解消（定期タスク）
bash examples/w6-orphan-linking.sh --domain Docs-OpenClaw --auto
```

### cc-hayashi エージェント（Claude Code 連携）

```bash
# Agent Skill Bus 状態確認
npx agent-skill-bus dashboard

# スキル実行記録
npx agent-skill-bus record-run \
  --skill context-and-impact \
  --result success
```

---

## 層選択フロー（Progressive Disclosure）

```
タスク開始
  │
  ├── キーワードが明確？
  │     YES → L1（grep）: bash examples/w1-keyword-search.sh "{keyword}"
  │     NO ↓
  │
  ├── コードを変更する？
  │     YES → L2a（gitnexus impact）: bash examples/w2-impact-analysis.sh
  │     NO ↓
  │
  ├── Obsidian ノート間の関係を調べる？
  │     YES → L2b（cypher）: bash examples/w3-cross-domain.sh
  │     NO ↓
  │
  ├── 概念で検索する？
  │     YES → L3（semantic）: npm run search -- --query "{概念}"
  │     NO ↓
  │
  └── 全部必要
        → フルパイプライン: bash examples/w5-full-pipeline.sh
```

---

## 定期タスクスケジュール

| タスク | コマンド | 推奨頻度 |
|--------|---------|---------|
| オーファンリンキング | `npm run orphan-link` | 週1回（月曜朝） |
| 品質チェック | `npm run w4` | 週1回 |
| スキルバス確認 | `npx agent-skill-bus flagged` | 日次 |
| GitNexus 再インデックス | `gitnexus analyze --path ~/dev/` | コミット後 |

---

## エラー別対処（Progressive Disclosure Level 2）

| エラー | 対処 |
|--------|------|
| `gitnexus: command not found` | `npm install -g gitnexus` |
| `SmartConnections: not found` | Obsidian でプラグインを有効化 |
| `KùzuDB split() error` | `STARTS WITH` に書き換え |
| `reason = 'obsidian-wikilink'` フィルタ漏れ | WHERE 句に `AND r.reason = 'obsidian-wikilink'` を追加 |
| L3 coverage < 50% | `Obsidian > Smart Connections > Update embeddings` |
