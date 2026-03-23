# CLAUDE.md — context-and-impact プロジェクト指示

> リポジトリ: `~/dev/tools/context-and-impact/`
> GitHub: `https://github.com/ShunsukeHayashi/context-and-impact`

---

## このプロジェクトの目的

4層コンテキスト収集・Agent Skill Bus・GitNexus を統合するスキルパイプラインの定義・実装・改善。

---

## 作業前の必須確認

1. `SKILL.md` を読む（メインスキル定義）
2. `docs/architecture.md` を読む（全体像）
3. 変更対象ファイルの影響分析: `gitnexus impact {ファイル}`

---

## コーディング規約

- Python: PEP 8 + Black
- Shell: bash、`#!/usr/bin/env bash`、`set -euo pipefail`
- Markdown: GitHub Flavored Markdown
- コメント: 日本語 OK、変数名・関数名は英語

---

## ファイル構成ルール

| 種別 | 場所 | 命名 |
|------|------|------|
| スキル定義（共通） | `SKILL.md` | 固定 |
| スキル定義（Claude Code 専用） | `skills/claude-code/SKILL.md` | 固定 |
| スキル定義（OpenClaw 専用） | `skills/openclaw/SKILL.md` | 固定 |
| CLI スクリプト | `src/cli/` | kebab-case.py / .sh |
| GitNexus クエリ | `src/gitnexus/` | queries.md + *.cypher |
| Agent Skill Bus 統合 | `src/skill-bus/` | kebab-case.ts |
| ワークフロー例 | `examples/` | w{N}-{name}.sh |
| ドキュメント | `docs/` | kebab-case.md |

---

## Agent Skill Bus との連携

```bash
# スキル実行後は必ず記録する
npx agent-skill-bus record-run \
  --skill context-and-impact \
  --result {success|failure|partial} \
  --metrics '{"quality_score": N, "layers_used": [...]}'

# 改善フラグが立ったら確認
npx agent-skill-bus flagged
```

---

## GitNexus との連携

```bash
# このリポジトリのインデックス更新（ファイル追加後）
gitnexus analyze --path ~/dev/tools/context-and-impact/

# コード変更前の影響確認
gitnexus impact {変更ファイル}

# Obsidian wikilink 分析
gitnexus cypher --repo obsidian "{クエリ}"
```

---

## テスト方法

```bash
# L3 テスト
python3 src/cli/semantic-search.py --status
python3 src/cli/semantic-search.py --query "テスト" --limit 3

# ワークフロー全体テスト
bash examples/w5-full-pipeline.sh "テスト" kotowari
```

---

## GitHub Issues / PR

- Issue 作成: `gh issue create --repo ShunsukeHayashi/context-and-impact`
- PR 作成: `gh pr create --repo ShunsukeHayashi/context-and-impact`
- 全 PR は `main` ブランチへのマージ

---

## 重要な注意事項

- KùzuDB `split()` 非対応 → `STARTS WITH` 使用
- wikilink エッジには `reason = 'obsidian-wikilink'` フィルタ必須
- L3（SmartConnections）は Obsidian プラグインのインデックス化が前提
- Agent Skill Bus の実行記録は `record-run` で必ず残す
