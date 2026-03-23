#!/usr/bin/env bash
# dispatch-recommend.sh: クエリとリポジトリからエージェントを推薦する
# 使い方: bash dispatch-recommend.sh "JWT 認証" kotowari
set -euo pipefail

QUERY="${1:-}"
REPO="${2:-}"

echo "=== エージェント推薦 ==="
echo "クエリ: $QUERY"
echo ""

# リポジトリ名 or クエリに KOTOWARI が含まれる場合の推薦
if echo "$REPO$QUERY" | grep -qi "kotowari"; then
  echo "  主推奨: kotowari-dev (38) [MacBook Pro] — KOTOWARI専属開発エージェント"
fi

# クエリ内容ベースの推薦
if echo "$QUERY" | grep -qiE "sns|twitter|x\.com|投稿|ポスト"; then
  echo "  SNS系  : sns-creator (29) [MainMini] / x-ops (12) [Windows Gateway]"
fi

if echo "$QUERY" | grep -qiE "content|記事|動画|youtube|ブログ"; then
  echo "  コンテンツ: content (2) [MacMini2]"
fi

if echo "$QUERY" | grep -qiE "3d|blender|モデル|レンダリング"; then
  echo "  3D系   : forge3d (13) [Mini3]"
fi

if echo "$QUERY" | grep -qiE "ppal|教育|コース|レッスン"; then
  echo "  PPAL系 : ppal-coordinator (16) [MacMini2]"
fi

if echo "$QUERY" | grep -qiE "分析|analytics|レポート|集計"; then
  echo "  分析系 : sns-analytics (31) / sigma (3) [MainMini]"
fi

echo ""
echo "  汎用フォールバック: main (0) [Windows Gateway]"
echo "  Claude Code連携   : cc-hayashi (37) [MacBook Pro]"
echo ""

# openclaw コマンドテンプレートを出力
AGENT="${REPO:+kotowari-dev}"
AGENT="${AGENT:-main}"

echo "--- 実行コマンド例 ---"
echo "  openclaw agent message $AGENT \"[TASK] $QUERY\""
echo ""
echo "--- Agent Skill Bus キューへの追加 ---"
echo "  npx agent-skill-bus enqueue \\"
echo "    --source human --priority high \\"
echo "    --agent $AGENT \\"
echo "    --task \"$QUERY\""
