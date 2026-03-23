# 命名規則ガイド — エージェント最適化設計

> **Progressive Disclosure Level 1** — このガイドに従って命名すると、エージェントがファイル名だけで機能を推測できる。

---

## 設計原則

### P1: 動詞+目的語形式

エージェントが「何をするファイルか」を即判断できる。

```
✅ search-code.sh       # コードを検索する
✅ link-orphans.sh      # 孤立ノートをリンクする
✅ analyze-impact.sh    # 影響を分析する
❌ utils.sh             # 何をするか不明
❌ helper.py            # 機能が不明
```

### P2: レイヤー接頭辞

L1/L2a/L2b/L3 を明示してエージェントが最適な層を選択できる。

```
✅ l1-keyword-search.sh
✅ l2a-code-impact.sh
✅ l2b-wikilink-graph.sh
✅ l3-semantic-search.py
```

### P3: フェーズ接頭辞

処理フェーズを明示する（パイプライン全体の位置を示す）。

```
✅ phase-a-context-collect.sh    # Phase A: コンテキスト収集
✅ phase-b-quality-score.sh      # Phase B: 品質スコアリング
✅ phase-c-skillbus-run.sh       # Phase C: Agent Skill Bus
✅ phase-d-feedback-loop.sh      # Phase D: フィードバック
```

### P4: 難易度グレーデッド（ワークフロー）

`w{N}` で複雑度/網羅範囲を示す。数字が大きいほど強力。

```
w1 = 最軽量（L1のみ）
w2 = 軽量（L2a）
w3 = 中程度（L2b）
w4 = 品質チェック
w5 = 完全パイプライン（全層）
w6 = 定期メンテナンス
```

---

## ファイル種別別命名規則

### シェルスクリプト（`.sh`）

```
パターン: {w{N}|phase-{X}|l{N}}-{動詞}-{目的語}.sh
例:
  w1-keyword-search.sh
  w6-orphan-linking.sh
  l2b-cypher-query.sh
  phase-c-skillbus-enqueue.sh
```

### Python スクリプト（`.py`）

```
パターン: {l{N}}-{動詞}-{目的語}.py
例:
  l3-semantic-search.py         # 現: semantic-search.py
  l2b-cypher-runner.py          # 新規
  l1-file-scanner.py            # 新規
```

### Markdown ドキュメント（`.md`）

```
パターン: {layer|phase|topic}-{目的}.md
例:
  l2b-cypher-queries.md         # 現: queries.md
  architecture.md               # 概要（接頭辞不要）
  agent-guide.md                # 対象を明示
  naming-guide.md               # このファイル
```

### SKILL.md（エントリーポイント）

```
固定: SKILL.md（大文字）
ランタイム別: skills/{runtime}/SKILL.md
```

---

## ディレクトリ構造（Progressive Disclosure）

```
context-and-impact/
│
├── Level 0: エントリーポイント（必読）
│   ├── SKILL.md          # 統合スキル定義
│   ├── CLAUDE.md         # エージェント向け指示
│   └── README.md         # 公開向け概要
│
├── Level 1: 詳細ガイド（必要に応じて）
│   ├── skills/
│   │   ├── claude-code/SKILL.md
│   │   └── openclaw/SKILL.md
│   └── docs/
│       ├── architecture.md      # 全体像
│       ├── agent-guide.md       # エージェント別コマンド
│       └── naming-guide.md      # このファイル
│
├── Level 2: 実行可能なワークフロー（コピペして使う）
│   └── examples/
│       ├── w1-keyword-search.sh
│       ├── w2-impact-analysis.sh
│       ├── w3-cross-domain.sh
│       ├── w4-quality-check.sh
│       ├── w5-full-pipeline.sh
│       └── w6-orphan-linking.sh
│
└── Level 3: 実装詳細（開発者・カスタマイズ時）
    └── src/
        ├── cli/
        │   └── l3-semantic-search.py    # レイヤー接頭辞付き（推奨移行先）
        ├── gitnexus/
        │   └── l2b-cypher-queries.md    # レイヤー接頭辞付き（推奨移行先）
        └── skill-bus/
```

---

## エージェントへの推奨アクセスパターン

```
1. SKILL.md を読む（Level 0）
   → トリガー条件・層の選択ガイドを確認

2. 実行する層/ワークフローを決定
   → w1-w6 から選択（Level 2）

3. 詳細が必要なら docs/ を参照（Level 1）
   → agent-guide.md でエージェント別コマンドを確認

4. カスタマイズが必要なら src/ を参照（Level 3）
   → l3-semantic-search.py を直接編集
```

---

## 既存ファイルの命名移行計画

| 現在のファイル | 推奨ファイル名 | 優先度 |
|--------------|-------------|--------|
| `src/cli/semantic-search.py` | `src/cli/l3-semantic-search.py` | P2 |
| `src/gitnexus/queries.md` | `src/gitnexus/l2b-cypher-queries.md` | P2 |
| `src/skill-bus/dispatch-recommend.sh` | `src/skill-bus/phase-c-dispatch.sh` | P2 |
| `src/skill-bus/enqueue-task.sh` | `src/skill-bus/phase-c-enqueue.sh` | P2 |
| `src/skill-bus/record-run.sh` | `src/skill-bus/phase-d-record.sh` | P2 |

**注意**: 移行は後方互換シンボリックリンクを残しながら段階的に行う。
