#!/usr/bin/env bash
# W1: キーワード検索（最軽量）
# 使い方: bash examples/w1-keyword-search.sh "authMiddleware"
set -euo pipefail

KEYWORD="${1:-authMiddleware}"
DEV_DIR="${DEV_DIR:-$HOME/dev}"
OBSIDIAN_DIR="${OBSIDIAN_DIR:-$HOME/dev/content/obsidian}"

echo "=== W1: キーワード検索 ==="
echo "キーワード: $KEYWORD"
echo ""

# L1a: コードベース検索
echo "--- L1a: コードベース (TS/JS/Python) ---"
grep -r "$KEYWORD" "$DEV_DIR" \
  --include="*.ts" --include="*.js" --include="*.py" \
  -l 2>/dev/null | head -15 || echo "(ヒットなし)"

echo ""

# L1b: Obsidian ノート検索
echo "--- L1b: Obsidian ノート ---"
grep -r "$KEYWORD" "$OBSIDIAN_DIR" \
  --include="*.md" \
  -l 2>/dev/null | head -10 || echo "(ヒットなし)"

echo ""
echo "=== 完了 ==="
echo "次のステップ: bash examples/w2-impact-analysis.sh $KEYWORD {repo}"
