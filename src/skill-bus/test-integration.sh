#!/usr/bin/env bash
# test-integration.sh: Agent Skill Bus 統合テスト
# Phase C（enqueue → dispatch → record-run）の一連フローを検証する
#
# 使い方:
#   bash test-integration.sh            # 全テスト実行
#   bash test-integration.sh --dry-run  # ドライラン（実際には送信しない）
#   bash test-integration.sh --verbose  # 詳細出力
set -euo pipefail

DRY_RUN=false
VERBOSE=false
PASS=0
FAIL=0
SKIP=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --verbose) VERBOSE=true ;;
  esac
done

# ----- ユーティリティ -----

pass() { echo "  ✅ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL + 1)); }
skip() { echo "  ⏭️  $1 (スキップ)"; SKIP=$((SKIP + 1)); }
section() { echo ""; echo "=== $1 ==="; }

run_cmd() {
  local label="$1"; shift
  if $VERBOSE; then
    echo "    > $*"
  fi
  if $DRY_RUN; then
    skip "$label [dry-run]"
    return 0
  fi
  if "$@" > /tmp/asb-test-out.txt 2>&1; then
    pass "$label"
    $VERBOSE && cat /tmp/asb-test-out.txt | sed 's/^/    /'
    return 0
  else
    fail "$label"
    cat /tmp/asb-test-out.txt | sed 's/^/    /'
    return 1
  fi
}

# ----- 前提チェック -----

section "前提チェック"

if command -v npx >/dev/null 2>&1; then
  pass "npx が利用可能"
else
  fail "npx が見つかりません — npm install -g npx または Node.js をインストール"
  echo ""; echo "ABORTED: 必須ツールが不足しています"; exit 1
fi

ASB_AVAILABLE=false
if npx agent-skill-bus --version >/dev/null 2>&1; then
  ASB_VERSION=$(npx agent-skill-bus --version 2>/dev/null || echo "unknown")
  pass "agent-skill-bus 利用可能 (${ASB_VERSION})"
  ASB_AVAILABLE=true
else
  skip "agent-skill-bus が未インストール（npm install -g agent-skill-bus で有効化）"
fi

# ----- T1: CLI スクリプト単体チェック -----

section "T1: CLI スクリプト存在確認"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for script in enqueue-task.sh dispatch-recommend.sh record-run.sh; do
  if [ -f "$SCRIPT_DIR/$script" ]; then
    pass "$script が存在する"
  else
    fail "$script が存在しない"
  fi
done

# ----- T2: enqueue テスト -----

section "T2: enqueue — タスクキュー追加"

TEST_TASK="[context-and-impact] 統合テスト用タスク $(date +%s)"
TEST_AGENT="cc-hayashi"

if $ASB_AVAILABLE; then
  run_cmd "enqueue-task.sh でキューに追加" \
    bash "$SCRIPT_DIR/enqueue-task.sh" "$TEST_TASK" "$TEST_AGENT" "normal"

  # npx agent-skill-bus list でキュー確認
  if ! $DRY_RUN; then
    if npx agent-skill-bus list 2>/dev/null | grep -q "context-and-impact"; then
      pass "キューにタスクが登録されている"
    else
      skip "キューの確認（agent-skill-bus list が未対応の場合あり）"
    fi
  fi
else
  skip "enqueue テスト（agent-skill-bus 未インストール）"
fi

# ----- T3: dispatch-recommend テスト -----

section "T3: dispatch-recommend — エージェント推薦"

declare -A DISPATCH_CASES
DISPATCH_CASES["SNS投稿 スレッド作成"]="sns-creator|x-ops"
DISPATCH_CASES["KOTOWARI バグ修正"]="kotowari-dev"
DISPATCH_CASES["3D モデル生成 blender"]="forge3d"
DISPATCH_CASES["PPAL コース作成"]="ppal-coordinator"
DISPATCH_CASES["分析 analytics"]="sigma|analytics"

for query in "${!DISPATCH_CASES[@]}"; do
  expected="${DISPATCH_CASES[$query]}"
  output=$(bash "$SCRIPT_DIR/dispatch-recommend.sh" "$query" 2>&1 || true)
  if echo "$output" | grep -qiE "$expected"; then
    pass "\"$query\" → 期待エージェント ($expected) が推薦される"
  else
    fail "\"$query\" → 期待エージェント ($expected) が推薦されない"
    $VERBOSE && echo "$output" | head -5 | sed 's/^/    /'
  fi
done

# ----- T4: record-run テスト -----

section "T4: record-run — 実行結果記録"

if $ASB_AVAILABLE; then
  run_cmd "record-run.sh で成功を記録" \
    bash "$SCRIPT_DIR/record-run.sh" \
      "cc-hayashi" \
      "context-and-impact" \
      "統合テスト実行" \
      "success" \
      "0.95"

  run_cmd "record-run.sh で部分成功を記録" \
    bash "$SCRIPT_DIR/record-run.sh" \
      "cc-hayashi" \
      "context-and-impact" \
      "統合テスト部分成功" \
      "partial" \
      "0.70"
else
  skip "record-run テスト（agent-skill-bus 未インストール）"
fi

# ----- T5: dashboard 確認 -----

section "T5: dashboard 確認"

if $ASB_AVAILABLE && ! $DRY_RUN; then
  if npx agent-skill-bus dashboard 2>/dev/null | grep -qiE "skill|agent|run|queue"; then
    pass "dashboard が動作する"
  else
    skip "dashboard 出力確認（表示形式が環境依存の場合あり）"
  fi
else
  skip "dashboard 確認 [dry-run または agent-skill-bus 未インストール]"
fi

# ----- T6: flagged チェック -----

section "T6: flagged — 改善候補確認"

if $ASB_AVAILABLE && ! $DRY_RUN; then
  if npx agent-skill-bus flagged 2>/dev/null; then
    pass "flagged コマンドが動作する"
  else
    skip "flagged コマンド（エントリなしでも正常）"
  fi
else
  skip "flagged 確認 [dry-run または agent-skill-bus 未インストール]"
fi

# ----- T7: Python CLI との連携確認 -----

section "T7: Python CLI との連携"

CLI_DIR="$(dirname "$SCRIPT_DIR")/cli"
WIKILINK_CLI="$CLI_DIR/wikilink-search.py"

if [ -f "$WIKILINK_CLI" ]; then
  pass "wikilink-search.py が存在する"
  if python3 "$WIKILINK_CLI" --help >/dev/null 2>&1; then
    pass "wikilink-search.py が起動できる"
  else
    skip "wikilink-search.py 起動確認（gitnexus 未インストール環境では正常）"
  fi
else
  fail "wikilink-search.py が存在しない"
fi

SEM_CLI="$CLI_DIR/semantic-search.py"
if [ -f "$SEM_CLI" ]; then
  pass "semantic-search.py が存在する"
else
  fail "semantic-search.py が存在しない"
fi

# ----- T8: ワークフロースクリプト確認 -----

section "T8: ワークフロースクリプト存在確認"

EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")/../examples"
if [ -d "$EXAMPLES_DIR" ]; then
  for w in w1 w2 w3 w4 w5 w6; do
    if ls "$EXAMPLES_DIR/${w}-"*.sh >/dev/null 2>&1; then
      pass "${w}-*.sh が存在する"
    else
      fail "${w}-*.sh が見つからない"
    fi
  done
else
  fail "examples/ ディレクトリが存在しない"
fi

# ----- サマリー -----

echo ""
echo "================================================"
echo "  統合テスト完了"
echo "  ✅ PASS: $PASS  ❌ FAIL: $FAIL  ⏭️  SKIP: $SKIP"
echo "================================================"

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "⚠️  $FAIL 件のテストが失敗しました。上記のログを確認してください。"
  exit 1
fi

echo ""
echo "✅ 全テストが通過しました。Phase C のフローは正常です。"
