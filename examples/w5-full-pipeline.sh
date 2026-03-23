#!/usr/bin/env bash
# W5: 完全パイプライン（Phase A + B + C + D）
# 使い方: bash examples/w5-full-pipeline.sh "JWT 認証" kotowari
set -euo pipefail

QUERY="${1:-JWT 認証}"
REPO="${2:-kotowari}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DEV_DIR="${DEV_DIR:-$HOME/dev}"
OBSIDIAN_DIR="${OBSIDIAN_DIR:-$HOME/dev/content/obsidian}"

echo "==================================================================="
echo "  W5: context-and-impact 完全パイプライン"
echo "  クエリ: $QUERY"
echo "  リポジトリ: $REPO"
echo "==================================================================="
echo ""

# ─────────────────────────────────────
# Phase A: コンテキスト収集
# ─────────────────────────────────────
echo "━━━ Phase A: コンテキスト収集 ━━━"
echo ""

# L1: テキスト検索
echo "▶ L1: テキスト検索"
KEYWORD=$(echo "$QUERY" | awk '{print $1}')  # 最初の単語で検索
CODE_HITS=$(grep -r "$KEYWORD" "$DEV_DIR/products/$REPO" \
  --include="*.ts" --include="*.js" --include="*.py" \
  -l 2>/dev/null | head -5) || true
OBS_HITS=$(grep -r "$KEYWORD" "$OBSIDIAN_DIR" \
  --include="*.md" -l 2>/dev/null | head -5) || true

echo "  コードファイル:"
[ -n "$CODE_HITS" ] && echo "$CODE_HITS" | sed 's/^/    /' || echo "    (ヒットなし)"
echo "  Obsidian ノート:"
[ -n "$OBS_HITS" ] && echo "$OBS_HITS" | sed 's/^/    /' || echo "    (ヒットなし)"
echo ""

# L2a: GitNexus コード影響分析
echo "▶ L2a: GitNexus コード影響分析"
if command -v gitnexus &>/dev/null; then
  gitnexus impact "$KEYWORD" --repo "$REPO" 2>/dev/null | head -20 || \
    echo "  ⚠️  インデックス未生成 → gitnexus analyze --path ~/dev/products/$REPO/"
else
  echo "  ❌ gitnexus 未インストール"
fi
echo ""

# L2b: Obsidian wikilink グラフ
echo "▶ L2b: Obsidian wikilink グラフ"
if command -v gitnexus &>/dev/null; then
  gitnexus cypher --repo obsidian "
  MATCH (f:File) WHERE f.name CONTAINS '$(echo "$QUERY" | awk '{print $1}')'
    OR f.filePath CONTAINS '$(echo "$QUERY" | awk '{print $1}')'
  RETURN f.name, f.filePath LIMIT 5
  " 2>/dev/null | head -10 || echo "  ⚠️  Obsidian インデックス未生成"
fi
echo ""

# L3: セマンティック検索
echo "▶ L3: セマンティック検索"
if [ -f "$ROOT_DIR/src/cli/semantic-search.py" ]; then
  python3 "$ROOT_DIR/src/cli/semantic-search.py" \
    --query "$QUERY" --limit 5 2>/dev/null || \
    echo "  ⚠️  SmartConnections インデックス未生成（Obsidianプラグインで初期化してください）"
else
  echo "  ❌ semantic-search.py が見つかりません"
fi
echo ""

# ─────────────────────────────────────
# Phase B: 品質チェック（簡易版）
# ─────────────────────────────────────
echo "━━━ Phase B: コンテキスト品質チェック ━━━"
echo ""
echo "  ✅ コード検索: $(echo "$CODE_HITS" | grep -c . || echo 0) ファイル"
echo "  ✅ ノート検索: $(echo "$OBS_HITS" | grep -c . || echo 0) ファイル"
echo "  注: Context Engineering MCP を使う場合:"
echo "      mcp__context_engineering__analyze_context"
echo ""

# ─────────────────────────────────────
# Phase C: Agent Skill Bus
# ─────────────────────────────────────
echo "━━━ Phase C: Agent Skill Bus ━━━"
echo ""
if command -v npx &>/dev/null; then
  echo "▶ スキルバス ダッシュボード（上位5件）"
  npx agent-skill-bus dashboard 2>/dev/null | head -10 || \
    echo "  ⚠️  agent-skill-bus 未インストール: npm install -g agent-skill-bus"
  echo ""

  # 実行記録
  echo "▶ 実行結果を記録"
  npx agent-skill-bus record-run \
    --skill context-and-impact \
    --result success \
    --metrics "{\"query\": \"$QUERY\", \"repo\": \"$REPO\", \"layers_used\": [\"L1\",\"L2a\",\"L2b\",\"L3\"]}" \
    2>/dev/null && echo "  ✅ 記録完了" || echo "  ⚠️  記録スキップ"
else
  echo "  ❌ npx が見つかりません"
fi
echo ""

# ─────────────────────────────────────
# Phase D: フィードバック確認
# ─────────────────────────────────────
echo "━━━ Phase D: フィードバック確認 ━━━"
echo ""
if command -v npx &>/dev/null; then
  echo "▶ 改善フラグ確認"
  npx agent-skill-bus flagged 2>/dev/null | head -5 || true
fi
echo ""

echo "==================================================================="
echo "  完了: context-and-impact パイプライン実行終了"
echo "==================================================================="
echo ""
echo "次のアクション:"
echo "  1. 上記のコンテキストを参考にタスクを実行"
echo "  2. 実行後: npx agent-skill-bus record-run で記録"
echo "  3. 定期的: bash examples/w4-quality-check.sh で品質確認"
