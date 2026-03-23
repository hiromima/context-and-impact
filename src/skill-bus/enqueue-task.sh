#!/usr/bin/env bash
# enqueue-task.sh: タスクを Agent Skill Bus キューに追加する
# 使い方: bash enqueue-task.sh "タスク概要" agent-id high
set -euo pipefail

TASK="${1:-}"
AGENT="${2:-main}"
PRIORITY="${3:-normal}"

if [ -z "$TASK" ]; then
  echo "使い方: $0 \"タスク概要\" [agent-id] [low|normal|high]" >&2
  exit 1
fi

echo "=== Agent Skill Bus: タスクキュー追加 ==="
echo "  タスク   : $TASK"
echo "  エージェント: $AGENT"
echo "  優先度   : $PRIORITY"
echo ""

if command -v npx >/dev/null 2>&1; then
  npx agent-skill-bus enqueue \
    --source human \
    --priority "$PRIORITY" \
    --agent "$AGENT" \
    --task "$TASK" \
  && echo "キューに追加しました。"
else
  echo "ERROR: npx が見つかりません。Node.js をインストールしてください。" >&2
  exit 1
fi
