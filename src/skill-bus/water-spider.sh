#!/usr/bin/env bash
# water-spider.sh — miyabi-auto（Water Spider）× context-and-impact 統合スクリプト
# 役割: HEARTBEAT.md から未完了タスクを検知し、context-and-impact Phase A-E を自動実行
# 使い方: bash src/skill-bus/water-spider.sh [--heartbeat PATH] [--repo REPO] [--dry-run]
set -euo pipefail

# ────────────────────────────────────────────
# 設定
# ────────────────────────────────────────────
HEARTBEAT_PATH="${HEARTBEAT_PATH:-$HOME/HEARTBEAT.md}"
REPO="${REPO:-kotowari}"
DRY_RUN=false
AGENT_ID="${AGENT_ID:-cc-hayashi}"
SKILL_BUS_CMD="npx agent-skill-bus"
WORKLOG_DIR="${WORKLOG_DIR:-$HOME/dev/tools/context-and-impact/project_memory}"
MAX_TASKS="${MAX_TASKS:-5}"  # 一度に処理するタスクの最大数

# ────────────────────────────────────────────
# 引数パース
# ────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --heartbeat) HEARTBEAT_PATH="$2"; shift 2 ;;
    --repo)      REPO="$2"; shift 2 ;;
    --dry-run)   DRY_RUN=true; shift ;;
    --agent)     AGENT_ID="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ────────────────────────────────────────────
# ユーティリティ
# ────────────────────────────────────────────
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
worklog() {
  mkdir -p "$WORKLOG_DIR/logs"
  echo "## $(date '+%Y-%m-%d %H:%M') water-spider: $*" >> "$WORKLOG_DIR/logs/worklog.md"
}

# ────────────────────────────────────────────
# Step 1: HEARTBEAT.md から未完了タスクを収集
# ────────────────────────────────────────────
collect_pending_tasks() {
  if [[ ! -f "$HEARTBEAT_PATH" ]]; then
    log "⚠️  HEARTBEAT.md が見つかりません: $HEARTBEAT_PATH"
    return 1
  fi

  # [ ] で始まるタスク行を抽出（markdown チェックボックス）
  grep -n '^\s*- \[ \]' "$HEARTBEAT_PATH" 2>/dev/null \
    | head -"$MAX_TASKS" \
    | sed 's/^\s*[0-9]*:\s*- \[ \] //' \
    | sed 's/^\s*//;s/\s*$//'
}

# ────────────────────────────────────────────
# Step 2: 単一タスクに対して context-and-impact Phase A-E を実行
# ────────────────────────────────────────────
run_pipeline_for_task() {
  local task="$1"
  local task_id
  task_id="WS-$(date '+%Y%m%d%H%M%S')"

  log "🔄 タスク開始: [$task_id] $task"
  worklog "タスク開始: [$task_id] $task"

  if [[ "$DRY_RUN" == "true" ]]; then
    log "  [dry-run] Phase A-E をスキップ"
    return 0
  fi

  # Phase A: インデックス鮮度確認 (gitnexus-cli / Tier 2)
  log "  Phase A: インデックス鮮度確認..."
  if command -v gitnexus &>/dev/null; then
    gitnexus status --repo "$REPO" 2>/dev/null | head -3 || true
  fi

  # Phase A: コンテキスト収集 (L1 + L2a)
  log "  Phase A: コンテキスト収集 (L1 + L2a)..."
  KEYWORD=$(echo "$task" | awk '{print $1}')
  CONTEXT_SCORE=0

  # L1 ヒット数
  L1_HITS=$(grep -r "$KEYWORD" "$HOME/dev" --include="*.ts" --include="*.md" -l 2>/dev/null | wc -l || echo 0)
  [[ "$L1_HITS" -gt 0 ]] && CONTEXT_SCORE=$((CONTEXT_SCORE + 30))

  # L2a GNI 影響分析
  if command -v gitnexus &>/dev/null; then
    GNI_OUT=$(gitnexus impact "$KEYWORD" --repo "$REPO" 2>/dev/null | head -5 || echo "")
    [[ -n "$GNI_OUT" ]] && CONTEXT_SCORE=$((CONTEXT_SCORE + 40))
  fi

  # Phase B: 品質ゲート
  log "  Phase B: quality_score = $CONTEXT_SCORE"
  if [[ "$CONTEXT_SCORE" -lt 40 ]]; then
    log "  ⚠️  quality_score < 40: コンテキスト不足。タスクをスキップ"
    worklog "タスクスキップ (quality_score=$CONTEXT_SCORE): $task"
    return 0
  fi

  # Phase C: タスクキューに投入 (Agent Skill Bus)
  log "  Phase C: タスクキューに投入..."
  if command -v npx &>/dev/null; then
    $SKILL_BUS_CMD enqueue \
      --source "water-spider" \
      --priority high \
      --agent "$AGENT_ID" \
      --task "[$task_id] $task" \
      2>/dev/null && log "  ✅ キュー投入完了" || log "  ⚠️  キュー投入スキップ"
  fi

  # Phase D: 実行記録
  log "  Phase D: 実行記録..."
  if command -v npx &>/dev/null; then
    $SKILL_BUS_CMD record-run \
      --agent "$AGENT_ID" \
      --skill "context-and-impact" \
      --task "$task" \
      --result "partial" \
      --score 0.7 \
      2>/dev/null || true
  fi

  # Phase E: worklog 追記
  worklog "Phase A-D 完了: [$task_id] quality_score=$CONTEXT_SCORE | repo=$REPO"
  log "  ✅ タスク処理完了: [$task_id]"
}

# ────────────────────────────────────────────
# Step 3: 完了報告 (pen1-report / Tier 2)
# ────────────────────────────────────────────
send_completion_report() {
  local task_count="$1"
  log "Phase E: pen1-report 完了報告 ($task_count タスク処理)"
  worklog "water-spider ループ完了: $task_count タスク処理"
  # pen1-report スキルが利用可能な場合は自動起動（Claude Code 経由）
  # /pen1-report コマンドで手動起動も可能
}

# ────────────────────────────────────────────
# メインループ
# ────────────────────────────────────────────
main() {
  log "🕷️  Water Spider 起動 (miyabi-auto × context-and-impact)"
  log "  HEARTBEAT: $HEARTBEAT_PATH"
  log "  REPO: $REPO | AGENT: $AGENT_ID | DRY_RUN: $DRY_RUN"
  echo ""

  # 未完了タスクを収集
  PENDING_TASKS=$(collect_pending_tasks || true)
  if [[ -z "$PENDING_TASKS" ]]; then
    log "✅ 未完了タスクなし。Water Spider 終了。"
    exit 0
  fi

  TASK_COUNT=0
  while IFS= read -r task; do
    [[ -z "$task" ]] && continue
    run_pipeline_for_task "$task"
    TASK_COUNT=$((TASK_COUNT + 1))
  done <<< "$PENDING_TASKS"

  echo ""
  send_completion_report "$TASK_COUNT"
  log "🏁 Water Spider 完了: $TASK_COUNT タスク処理"
}

main "$@"
