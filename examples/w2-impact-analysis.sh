#!/usr/bin/env bash
# W2: コード影響分析（GitNexus L2a）
# 使い方: bash examples/w2-impact-analysis.sh authMiddleware kotowari
set -euo pipefail

TARGET="${1:-authMiddleware}"
REPO="${2:-kotowari}"

echo "=== W2: コード影響分析 ==="
echo "対象: $TARGET"
echo "リポジトリ: $REPO"
echo ""

# L2a: GitNexus 影響分析
echo "--- L2a: GitNexus 影響分析 ---"
if command -v gitnexus &>/dev/null; then
  gitnexus impact "$TARGET" --repo "$REPO" 2>/dev/null || {
    echo "⚠️  GitNexus インデックスが未生成の可能性があります"
    echo "  実行: gitnexus analyze --path ~/dev/products/$REPO/"
  }
else
  echo "❌ gitnexus コマンドが見つかりません"
  echo "  インストール: npm install -g gitnexus"
fi

echo ""

# L2a: GitNexus コンテキスト取得
echo "--- L2a: GitNexus コンテキスト ---"
if command -v gitnexus &>/dev/null; then
  gitnexus context "$TARGET" --repo "$REPO" 2>/dev/null | head -30 || true
fi

echo ""
echo "=== 完了 ==="
echo "リスクが LOW の場合: 変更を実行してください"
echo "リスクが HIGH/CRITICAL の場合: 慎重に変更計画を立ててください"
