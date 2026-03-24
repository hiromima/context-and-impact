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
DRY_RUN="${DRY_RUN:-0}"   # 1 にするとルーティング確認のみ（実際には起動しない）

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

# L1〜L3 を全て並列実行
echo "▶ L1/L2a/L2b/L3: 並列コンテキスト収集"
KEYWORD=$(echo "$QUERY" | awk '{print $1}')  # 最初の単語で検索

TMP_L1C=$(mktemp)  # L1 コード
TMP_L1O=$(mktemp)  # L1 Obsidian
TMP_L2A=$(mktemp)
TMP_L2B=$(mktemp)
TMP_L3=$(mktemp)

# 異常終了時も tmpfile を確実に削除
trap 'rm -f "$TMP_L1C" "$TMP_L1O" "$TMP_L2A" "$TMP_L2B" "$TMP_L3"' EXIT

# L1: テキスト検索（dist/node_modules 除外で高速化）
grep -r "$KEYWORD" "$DEV_DIR/products/$REPO" \
  --include="*.ts" --include="*.js" --include="*.py" \
  --exclude-dir=dist --exclude-dir=node_modules --exclude-dir=.git \
  -l 2>/dev/null | head -5 > "$TMP_L1C" &
PID_L1C=$!

grep -r "$KEYWORD" "$OBSIDIAN_DIR" \
  --include="*.md" \
  --exclude-dir=.git --exclude-dir=.trash \
  -l 2>/dev/null | head -5 > "$TMP_L1O" &
PID_L1O=$!

# L2a: GitNexus コード影響分析（バックグラウンド）
if command -v gitnexus &>/dev/null; then
  (gitnexus impact "$KEYWORD" --repo "$REPO" 2>/dev/null | head -20 \
    || echo "  ⚠️  インデックス未生成 → gitnexus analyze --path ~/dev/products/$REPO/") > "$TMP_L2A" &
  PID_L2A=$!
else
  echo "  ❌ gitnexus 未インストール" > "$TMP_L2A"
  PID_L2A=""
fi

# L2b: Obsidian wikilink グラフ（バックグラウンド）
if command -v gitnexus &>/dev/null; then
  (gitnexus cypher --repo obsidian "
  MATCH (f:File) WHERE f.name CONTAINS '$(echo "$QUERY" | awk '{print $1}')'
    OR f.filePath CONTAINS '$(echo "$QUERY" | awk '{print $1}')'
  RETURN f.name, f.filePath LIMIT 5
  " 2>/dev/null | head -10 || echo "  ⚠️  Obsidian インデックス未生成") > "$TMP_L2B" &
  PID_L2B=$!
else
  echo "(gitnexus なし)" > "$TMP_L2B"
  PID_L2B=""
fi

# L3: セマンティック検索（バックグラウンド）
if [ -f "$ROOT_DIR/src/cli/semantic-search.py" ]; then
  (python3 "$ROOT_DIR/src/cli/semantic-search.py" \
    --query "$QUERY" --limit 5 2>/dev/null \
    || echo "  ⚠️  SmartConnections インデックス未生成") > "$TMP_L3" &
  PID_L3=$!
else
  echo "  ❌ semantic-search.py が見つかりません" > "$TMP_L3"
  PID_L3=""
fi

# 全並列処理を待機
[ -n "${PID_L1C:-}" ] && wait "$PID_L1C" 2>/dev/null || true
[ -n "${PID_L1O:-}" ] && wait "$PID_L1O" 2>/dev/null || true
[ -n "${PID_L2A:-}" ] && wait "$PID_L2A" 2>/dev/null || true
[ -n "${PID_L2B:-}" ] && wait "$PID_L2B" 2>/dev/null || true
[ -n "${PID_L3:-}"  ] && wait "$PID_L3"  2>/dev/null || true

# L1 結果をシェル変数に読み込む（Phase B のスコア計算に使用）
CODE_HITS=$(cat "$TMP_L1C")
OBS_HITS=$(cat "$TMP_L1O")

# 結果表示
echo "▶ L1: テキスト検索"
echo "  コードファイル:"
[ -n "$CODE_HITS" ] && echo "$CODE_HITS" | sed 's/^/    /' || echo "    (ヒットなし)"
echo "  Obsidian ノート:"
[ -n "$OBS_HITS" ] && echo "$OBS_HITS" | sed 's/^/    /' || echo "    (ヒットなし)"
echo ""

echo "▶ L2a: GitNexus コード影響分析"
cat "$TMP_L2A"
echo ""

echo "▶ L2b: Obsidian wikilink グラフ"
cat "$TMP_L2B"
echo ""

echo "▶ L3: セマンティック検索"
cat "$TMP_L3"
echo ""

rm -f "$TMP_L1C" "$TMP_L1O" "$TMP_L2A" "$TMP_L2B" "$TMP_L3"

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
    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
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

# Agent Skill Bus に実行記録（バックグラウンド — パイプラインをブロックしない）
echo "▶ Agent Skill Bus 実行記録 (bg)"
if command -v npx &>/dev/null; then
  npx agent-skill-bus record-run \
    --skill context-and-impact \
    --result success \
    --metrics "{\"query\": \"${QUERY}\", \"repo\": \"${REPO}\", \"quality_score\": ${QUALITY_SCORE}, \"dag\": \"${TASKS_JSON}\"}" \
    2>/dev/null &
  echo "  ✅ 記録開始 (バックグラウンド)"
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
# Phase D-2: Execution Router
# tasks.json のタスクをキーワード/agent で自動振り分け:
#   fix/修正/警告系  → cursor-agent   (ローカル, ~8秒)
#   feat/docs/test系 → @copilot Issue (クラウド, ~2分)
#   kaede/dev-coder  → [auto] Pipeline (webhook-gate)
#   それ以外         → 表示のみ (手動)
# DRY_RUN=1 で起動せずルーティング確認のみ
# ─────────────────────────────────────
echo "▶ D-2: Execution Router — 自動起動 (DRY_RUN=${DRY_RUN})"
python3 - <<'ROUTEREOF'
import json, subprocess, os, sys

tasks_path = os.environ.get("TASKS_JSON", "")
repo       = os.environ.get("REPO", "context-and-impact")
query      = os.environ.get("QUERY", "")
dry_run    = os.environ.get("DRY_RUN", "0") == "1"

try:
    dag   = json.load(open(tasks_path))
    tasks = dag.get("tasks", [])
except Exception as e:
    print(f"  (tasks.json なし, スキップ: {e})")
    sys.exit(0)

if not tasks:
    print("  (タスク 0 件, スキップ)")
    sys.exit(0)

FIX_KW  = ["fix", "修正", "バグ", "警告", "deprecated", "utcnow", "warning", "error", "bug"]
FEAT_KW = ["feat", "add", "追加", "docs", "test", "chore", "implement", "refactor", "review"]
MAN_AG  = ["kaede", "dev-coder", "kotowari-dev", "cc-agent-1"]

def route(task):
    label = task.get("label", "").lower()
    agent = task.get("agent", "")
    if any(k in label for k in FIX_KW):
        return "cursor-agent"
    if any(k in label for k in FEAT_KW):
        return "copilot"
    if agent in MAN_AG:
        return "auto-pipeline"
    return "manual"

tiers = {"cursor-agent": [], "copilot": [], "auto-pipeline": [], "manual": []}
for task in tasks:
    t = route(task)
    tiers[t].append(task)
    flag = "(dry)" if dry_run else ""
    print(f"  [{t:14s}] {task.get('id','?')}: {task.get('label','')[:55]} {flag}")

print("")

if dry_run:
    print("  DRY_RUN=1: 実際には起動しません")
    sys.exit(0)

# cursor-agent: ローカル即時実行
import shutil
for task in tiers["cursor-agent"]:
    label = task.get("label", "")
    print(f"  cursor-agent 起動: {label[:45]}")
    if shutil.which("cursor-agent") is None:
        print("  ⚠️  cursor-agent 未インストール (スキップ): npm install -g @cursor/agent")
        continue
    try:
        r = subprocess.run(
            ["cursor-agent", "--print", "--trust"],
            input=label,
            capture_output=True, text=True, timeout=90
        )
        out = (r.stdout + r.stderr).strip()
        print(f"    => {out[:100]}" if out else "    => 完了")
    except subprocess.TimeoutExpired:
        print("    => タイムアウト（90秒）スキップ")
    except Exception as e:
        print(f"    => エラー: {e}")

# Copilot Coding Agent: クラウド非同期
for task in tiers["copilot"]:
    label = task.get("label", "")
    body  = (f"## コンテキスト\nクエリ: {query}\n\n"
             f"## タスク\n{label}\n\n"
             f"## 完了条件\n- [ ] テストが通る\n- [ ] 既存動作に影響なし")
    title = f"[copilot] {label[:60]}"
    try:
        r = subprocess.run(
            ["gh", "issue", "create",
             "--repo", f"ShunsukeHayashi/{repo}",
             "--title", title,
             "--assignee", "@copilot",
             "--body", body],
            capture_output=True, text=True, timeout=30
        )
        url = r.stdout.strip()
        print(f"  @copilot Issue: {url[:80]}" if url else f"  @copilot Issue 作成試行: {label[:45]}")
    except subprocess.TimeoutExpired:
        print(f"  @copilot Issue タイムアウト: {label[:45]}")
    except Exception as e:
        print(f"  @copilot Issue エラー: {e}")

# [auto] Pipeline: webhook-gate 経由
for task in tiers["auto-pipeline"]:
    label = task.get("label", "")
    title = f"[auto] {label[:60]}"
    try:
        r = subprocess.run(
            ["gh", "issue", "create",
             "--repo", f"ShunsukeHayashi/{repo}",
             "--title", title,
             "--label", "auto",
             "--body", f"自動生成\n{label}"],
            capture_output=True, text=True, timeout=30
        )
        url = r.stdout.strip()
        print(f"  [auto] Issue: {url[:80]}" if url else f"  [auto] Issue 作成試行: {label[:45]}")
    except subprocess.TimeoutExpired:
        print(f"  [auto] Issue タイムアウト: {label[:45]}")
    except Exception as e:
        print(f"  [auto] Issue エラー: {e}")
ROUTEREOF
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
    2>/dev/null &
  echo "  ✅ スコア記録開始 (self_score=${SELF_SCORE}, バックグラウンド)"
fi
echo ""

# E4: Copilot Draft PR 確認
echo "▶ E4: Copilot Draft PR 監視"
COPILOT_PRS=$(gh pr list \
  --repo "ShunsukeHayashi/${REPO}" \
  --author @copilot \
  --draft \
  --json number,title,createdAt \
  --limit 5 2>/dev/null)

if [ -n "$COPILOT_PRS" ] && [ "$COPILOT_PRS" != "[]" ]; then
    echo "  レビュー待ち Draft PR:"
    echo "$COPILOT_PRS" | REPO_NAME="${REPO}" python3 -c "
import json, sys, os
repo = os.environ.get('REPO_NAME', '')
for pr in json.load(sys.stdin):
    print(f'  #{pr[\"number\"]}: {pr[\"title\"][:55]}')
    print(f'    作成: {pr[\"createdAt\"]}')
    print(f'    確認: gh pr view {pr[\"number\"]} --repo ShunsukeHayashi/{repo}')
    "
    echo "" >> "$WORKLOG"
    echo "- **pending_copilot_prs**: $(echo "$COPILOT_PRS" | python3 -c 'import json,sys; print([p["number"] for p in json.load(sys.stdin)])' 2>/dev/null)" >> "$WORKLOG"
else
    echo "  待機中の Copilot Draft PR なし"
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
echo "  D-1  : ai-triad 実行プラン表示"
echo "  D-2  : Execution Router (cursor-agent / @copilot / [auto] 自動振り分け)"
echo "  E    : worklog.md 記録 + cycle-ops + self-improve + Copilot PR 監視"
echo ""
echo "次のアクション:"
echo "  1. ${TASKS_JSON} のタスクは D-2 Execution Router が自動起動済み"
echo "  2. 実行後: worklog.md に result を追記"
echo "  3. 品質確認: bash examples/w4-quality-check.sh"
echo "  4. Copilot Draft PR レビュー: gh pr list --repo ShunsukeHayashi/${REPO} --author @copilot"
echo "  5. DRY_RUN モード: DRY_RUN=1 bash examples/w5-full-pipeline.sh \"クエリ\" ${REPO}"
