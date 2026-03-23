#!/usr/bin/env bash
# record-run.sh: スキル実行結果を Agent Skill Bus に記録する
# 使い方: bash record-run.sh agent-id skill-name "タスク概要" success 0.9
set -euo pipefail

AGENT="${1:-}"
SKILL="${2:-context-and-impact}"
TASK="${3:-}"
RESULT="${4:-success}"
SCORE="${5:-0.8}"

if [ -z "$AGENT" ] || [ -z "$TASK" ]; then
  echo "使い方: $0 agent-id skill-name \"タスク概要\" [success|fail|partial] [0.0-1.0]" >&2
  exit 1
fi

echo "=== Agent Skill Bus: 実行結果記録 ==="
echo "  エージェント: $AGENT"
echo "  スキル    : $SKILL"
echo "  タスク    : $TASK"
echo "  結果      : $RESULT"
echo "  スコア    : $SCORE"
echo ""

if command -v npx >/dev/null 2>&1; then
  npx agent-skill-bus record-run \
    --agent "$AGENT" \
    --skill "$SKILL" \
    --task "$TASK" \
    --result "$RESULT" \
    --score "$SCORE" \
  && echo "記録しました。"
else
  echo "ERROR: npx が見つかりません。Node.js をインストールしてください。" >&2
  exit 1
fi
