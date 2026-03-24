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
# Pre-A: GNI インデックス鮮度確認
# ─────────────────────────────────────
echo "━━━ Pre-A: GNI インデックス鮮度確認 ━━━"
echo ""

REPO_PATH="$DEV_DIR/products/$REPO"

if command -v gitnexus &>/dev/null; then
  echo "▶ gitnexus status 確認: $REPO_PATH"
  GNI_STATUS_OUT=$(gitnexus status --json 2>/dev/null || echo '{}')
  IS_STALE=$(echo "$GNI_STATUS_OUT" | python3 -c "
import json, sys, os
data = json.load(sys.stdin)
repo_name = os.environ.get('REPO', '')
repos = data.get('repos', [])
for r in repos:
    if repo_name in r.get('name', '') or repo_name in r.get('path', ''):
        print('stale' if r.get('isStale', False) else 'fresh')
        sys.exit(0)
print('unknown')
" REPO="$REPO" 2>/dev/null || echo "unknown")

  case "$IS_STALE" in
    stale)
      echo "  ⚠️  インデックスが stale → 自動 reindex 開始"
      gitnexus analyze --path "$REPO_PATH" 2>/dev/null && \
        echo "  ✅ reindex 完了" || \
        echo "  ❌ reindex 失敗（手動実行: gitnexus analyze --path ${REPO_PATH}）"
      ;;
    fresh)
      echo "  ✅ インデックス最新 (fresh)"
      ;;
    *)
      echo "  ℹ️  インデックス未生成または確認不可（初回: gitnexus analyze --path ${REPO_PATH}）"
      ;;
  esac
else
  echo "  ❌ gitnexus 未インストール: npm install -g gitnexus"
fi
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
# Phase B: コンテキスト品質ゲート
# ─────────────────────────────────────
echo "━━━ Phase B: コンテキスト品質ゲート ━━━"
echo ""

# スコア計算
CODE_COUNT=$(echo "$CODE_HITS" | grep -c . 2>/dev/null || echo 0)
OBS_COUNT=$(echo "$OBS_HITS"  | grep -c . 2>/dev/null || echo 0)
GNI_OK=0; command -v gitnexus &>/dev/null && GNI_OK=1

QUALITY_SCORE=${QUALITY_SCORE:-0}
if [ "$QUALITY_SCORE" -eq 0 ]; then
  # 自動スコアリング
  # L1 コード: +25 (1件以上) / +10 ボーナス (4件以上)
  # L1 ノート: +20 (1件以上) / +5  ボーナス (4件以上)
  # L2a GNI : +25 (インストール済み)
  # L2b/L3  : +15 (gitnexus 利用可能)
  SCORE=0
  [ "$CODE_COUNT" -gt 0 ] && SCORE=$((SCORE + 25))
  [ "$CODE_COUNT" -gt 3 ] && SCORE=$((SCORE + 10))
  [ "$OBS_COUNT"  -gt 0 ] && SCORE=$((SCORE + 20))
  [ "$OBS_COUNT"  -gt 3 ] && SCORE=$((SCORE + 5))
  [ "$GNI_OK"     -eq 1 ] && SCORE=$((SCORE + 25))
  [ "$GNI_OK"     -eq 1 ] && SCORE=$((SCORE + 15))
  QUALITY_SCORE=$SCORE
fi

echo "  スコア内訳:"
echo "    L1 コードファイル : ${CODE_COUNT} 件"
echo "    L1 Obsidian ノート: ${OBS_COUNT} 件"
echo "    L2a GNI 利用可否  : $([ "$GNI_OK" -eq 1 ] && echo 'YES' || echo 'NO')"
echo ""
echo "  quality_score = ${QUALITY_SCORE} / 100"
echo ""

if [ "${FORCE:-0}" = "1" ]; then
  echo "  [FORCE=1] 品質スコアに関わらず続行します"
elif [ "$QUALITY_SCORE" -ge 85 ]; then
  echo "  判定: 高品質 ✅ → Phase C へ進みます"
elif [ "$QUALITY_SCORE" -ge 70 ]; then
  echo "  判定: 標準 ⚠️  → auto_optimize 推奨"
  echo "        Context Engineering MCP: mcp__context_engineering__auto_optimize_context"
  echo "        続行します（FORCE=1 不要）"
else
  echo "  判定: 要改善 ❌ (スコア ${QUALITY_SCORE} < 70)"
  echo ""
  echo "  推奨アクション:"
  echo "    1. 追加クエリで L1 再検索"
  echo "    2. gitnexus analyze --path ${REPO_PATH} でインデックス生成"
  echo "    3. FORCE=1 bash $0 \"$QUERY\" $REPO  (強制続行)"
  echo ""
  if [ "${FORCE:-0}" != "1" ]; then
    echo "  中断します（FORCE=1 で強制続行可）"
    exit 1
  fi
fi
echo ""

# ─────────────────────────────────────
# Phase C: GNI-First DAG 生成
# ─────────────────────────────────────
echo "━━━ Phase C: GNI-First DAG 生成 ━━━"
echo ""

TASKS_JSON="${ROOT_DIR}/project_memory/tasks.json"
mkdir -p "${ROOT_DIR}/project_memory"

echo "▶ GNI ブラストラジアス → tasks.json 生成"

# GNI impact 結果を取得
if command -v gitnexus &>/dev/null; then
  GNI_IMPACT=$(gitnexus impact "$KEYWORD" --repo "$REPO" --json 2>/dev/null || echo '{}')
  AFFECTED_FILES=$(echo "$GNI_IMPACT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
files = set()
for node in data.get('nodes', []):
    fp = node.get('filePath', '')
    if fp:
        files.add(fp)
for entry in data.get('affected', []):
    fp = entry.get('filePath', '')
    if fp:
        files.add(fp)
print('\n'.join(sorted(files)[:10]))
" 2>/dev/null || true)
else
  AFFECTED_FILES=""
fi

# tasks.json を生成
python3 - <<PYEOF
import json, os, datetime

affected_raw = """${AFFECTED_FILES}"""
affected = [f.strip() for f in affected_raw.strip().splitlines() if f.strip()]

tasks = []
for i, fp in enumerate(affected[:8], start=1):
    fname = os.path.basename(fp)
    agent = "kotowari-dev" if "kotowari" in fp else "kaede"
    tasks.append({
        "id": f"task-{i}",
        "label": f"Review/modify {fname}",
        "file": fp,
        "agent": agent,
        "depends_on": [f"task-{i-1}"] if i > 1 else [],
        "status": "pending"
    })

if not tasks:
    tasks.append({
        "id": "task-1",
        "label": f"Implement: ${QUERY}",
        "agent": "kaede",
        "depends_on": [],
        "status": "pending"
    })

output = {
    "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    "query": "${QUERY}",
    "repo": "${REPO}",
    "quality_score": ${QUALITY_SCORE},
    "tasks": tasks
}

path = "${TASKS_JSON}"
with open(path, "w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"  ✅ tasks.json 生成: {len(tasks)} タスク → {path}")
for t in tasks:
    dep = f" (depends: {t['depends_on']})" if t['depends_on'] else ""
    print(f"    [{t['id']}] {t['label']} @{t['agent']}{dep}")
PYEOF

echo ""

# Agent Skill Bus に実行記録
echo "▶ Agent Skill Bus 実行記録"
if command -v npx &>/dev/null; then
  npx agent-skill-bus record-run \
    --skill context-and-impact \
    --result success \
    --metrics "{\"query\": \"${QUERY}\", \"repo\": \"${REPO}\", \"quality_score\": ${QUALITY_SCORE}, \"dag\": \"${TASKS_JSON}\"}" \
    2>/dev/null && echo "  ✅ 記録完了" || echo "  ⚠️  記録スキップ"
fi
echo ""

# ─────────────────────────────────────
# Phase D: マルチエージェント実行プラン
# ─────────────────────────────────────
echo "━━━ Phase D: マルチエージェント実行プラン ━━━"
echo ""

echo "▶ ai-triad 役割分担（DAG ベース）"
python3 - <<PYEOF2
import json, os

path = "${TASKS_JSON}"
try:
    with open(path) as f:
        dag = json.load(f)
    tasks = dag.get("tasks", [])
    agents = {}
    for t in tasks:
        a = t.get("agent", "kaede")
        agents.setdefault(a, []).append(t["id"])

    print("  Claude Code  (Orchestrator) : DAG監視・品質ゲート・完了報告")
    for agent, ids in agents.items():
        print(f"  {agent:<20}: {', '.join(ids)}")

    # 並行実行可能なタスク（depends_on が空）
    parallel = [t["id"] for t in tasks if not t.get("depends_on")]
    sequential = [t["id"] for t in tasks if t.get("depends_on")]
    print("")
    print(f"  並行実行可能: {parallel if parallel else ['(なし)']}")
    print(f"  直列実行    : {sequential if sequential else ['(なし)']}")
except Exception as e:
    print(f"  ⚠️  tasks.json 読み込みエラー: {e}")
PYEOF2
echo ""

echo "▶ 改善フラグ確認"
if command -v npx &>/dev/null; then
  npx agent-skill-bus flagged 2>/dev/null | head -5 || true
fi
echo ""

# ─────────────────────────────────────
# Phase E: ARIA 監査 + Self-Improve
# ─────────────────────────────────────
echo "━━━ Phase E: ARIA 監査 + Self-Improve ━━━"
echo ""

WORKLOG="${ROOT_DIR}/project_memory/worklog.md"
RUNLOGS_DIR="${ROOT_DIR}/project_memory/runlogs"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
mkdir -p "$RUNLOGS_DIR"

# E1: worklog.md に記録
echo "▶ E1: 実行ログ記録 (${WORKLOG})"
TASK_COUNT=$(python3 -c "
import json
try:
    d=json.load(open('${TASKS_JSON}'))
    print(len(d.get('tasks',[])))
except:
    print(0)
" 2>/dev/null || echo 0)

cat >> "$WORKLOG" <<LOGEOF

## ${TIMESTAMP} — ${QUERY} (${REPO})
- **request**: ${QUERY}
- **project**: ${REPO}
- **quality_score**: ${QUALITY_SCORE}
- **tasks_generated**: ${TASK_COUNT}
- **dag**: ${TASKS_JSON}
- **result**: success
LOGEOF
echo "  ✅ worklog.md に追記完了"

# E2: cycle-ops チェック
echo ""
echo "▶ E2: cycle-ops フィードバックループ"
if command -v miyabi &>/dev/null; then
  miyabi cycle check 2>/dev/null && echo "  ✅ cycle check 完了" || echo "  ⚠️  cycle check スキップ"
else
  echo "  ℹ️  miyabi 未インストール（スキップ）: npm install -g miyabi-hub"
fi

# E3: self-improving スコア記録
echo ""
echo "▶ E3: スキル自己改善スコア記録"
SELF_SCORE=$(python3 -c "print(round(${QUALITY_SCORE}/100, 2))" 2>/dev/null || echo "0.9")
if command -v npx &>/dev/null; then
  npx agent-skill-bus record-run \
    --skill context-and-impact \
    --result success \
    --metrics "{\"query\":\"${QUERY}\",\"repo\":\"${REPO}\",\"quality_score\":${QUALITY_SCORE},\"tasks\":${TASK_COUNT},\"self_score\":${SELF_SCORE}}" \
    2>/dev/null && echo "  ✅ スコア記録完了 (self_score=${SELF_SCORE})" || echo "  ⚠️  記録スキップ"
fi
echo ""

echo "==================================================================="
echo "  完了: context-and-impact v3.1 パイプライン (Phase Pre-A〜E)"
echo "==================================================================="
echo ""
echo "サマリー:"
echo "  Pre-A: GNI 鮮度確認"
echo "  A    : L1/L2a/L2b/L3 コンテキスト収集"
echo "  B    : quality_score=${QUALITY_SCORE}/100"
echo "  C    : tasks.json (${TASK_COUNT} タスク) → ${TASKS_JSON}"
echo "  D    : ai-triad 実行プラン生成"
echo "  E    : worklog.md 記録 + cycle-ops + self-improve"
echo ""
echo "次のアクション:"
echo "  1. ${TASKS_JSON} のタスクをエージェントに割り当てて実行"
echo "  2. 実行後: worklog.md に result を追記"
echo "  3. 品質確認: bash examples/w4-quality-check.sh"
