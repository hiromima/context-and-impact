#!/usr/bin/env bash
# l1-keyword-search.sh: Layer 1 — grep/ripgrep ベース高速キーワード検索
# Progressive Disclosure Layer 1: テキスト検索（最軽量）
#
# 使い方:
#   bash l1-keyword-search.sh "auth"
#   bash l1-keyword-search.sh "auth" --type py
#   bash l1-keyword-search.sh "JWT" --repo ~/dev/products/kotowari
#   bash l1-keyword-search.sh "ナレッジ" --obsidian
#   bash l1-keyword-search.sh "auth" --json
#   bash l1-keyword-search.sh "auth" --context 3
set -euo pipefail

# ----- デフォルト設定 -----

KEYWORD=""
TARGET_DIR="${PWD}"
FILE_TYPE=""
CONTEXT_LINES=0
OUTPUT_JSON=false
MODE="code"           # code | obsidian
LIMIT=50
CASE_INSENSITIVE=false

OBSIDIAN_DEFAULT="${HOME}/dev/content/obsidian"
[ -d "${HOME}/dev/06-content/obsidian-vault" ] && \
  OBSIDIAN_DEFAULT="${HOME}/dev/06-content/obsidian-vault"
[ -d "${HOME}/obsidian-vault" ] && \
  OBSIDIAN_DEFAULT="${HOME}/obsidian-vault"

# ----- 引数パース -----

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo|-r)    TARGET_DIR="$2"; shift 2 ;;
    --type|-t)    FILE_TYPE="$2"; shift 2 ;;
    --context|-C) CONTEXT_LINES="$2"; shift 2 ;;
    --limit|-n)   LIMIT="$2"; shift 2 ;;
    --json)       OUTPUT_JSON=true; shift ;;
    --obsidian)   MODE="obsidian"; TARGET_DIR="$OBSIDIAN_DEFAULT"; shift ;;
    --ignore-case|-i) CASE_INSENSITIVE=true; shift ;;
    --help|-h)
      sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
      exit 0 ;;
    -*)
      echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      KEYWORD="$1"; shift ;;
  esac
done

if [ -z "$KEYWORD" ]; then
  echo "使い方: $0 <キーワード> [オプション]" >&2
  echo "  --repo DIR     検索ルートディレクトリ（デフォルト: カレント）" >&2
  echo "  --type EXT     ファイル種別（例: py, ts, md）" >&2
  echo "  --context N    前後 N 行を表示" >&2
  echo "  --limit N      最大件数（デフォルト: 50）" >&2
  echo "  --obsidian     Obsidian vault を検索" >&2
  echo "  --json         JSON 形式で出力" >&2
  echo "  --ignore-case  大文字小文字を区別しない" >&2
  exit 1
fi

# ----- ripgrep/grep 判定 -----

if command -v rg >/dev/null 2>&1; then
  SEARCH_CMD="rg"
else
  SEARCH_CMD="grep"
fi

# ----- 検索実行 -----

build_rg_cmd() {
  local cmd=("rg" "--line-number" "--no-heading" "--color=never")
  $CASE_INSENSITIVE && cmd+=("--ignore-case")
  [ -n "$FILE_TYPE" ] && cmd+=("--type" "$FILE_TYPE")
  [ "$CONTEXT_LINES" -gt 0 ] && cmd+=("--context" "$CONTEXT_LINES")
  cmd+=("--max-count" "$LIMIT")
  [ "$MODE" = "obsidian" ] && cmd+=("--glob" "*.md")
  cmd+=("$KEYWORD" "$TARGET_DIR")
  echo "${cmd[@]}"
}

build_grep_cmd() {
  local cmd=("grep" "-rn" "--color=never")
  $CASE_INSENSITIVE && cmd+=("-i")
  [ -n "$FILE_TYPE" ] && cmd+=("--include=*.${FILE_TYPE}")
  [ "$MODE" = "obsidian" ] && cmd+=("--include=*.md")
  [ "$CONTEXT_LINES" -gt 0 ] && cmd+=("-C" "$CONTEXT_LINES")
  cmd+=("$KEYWORD" "$TARGET_DIR")
  echo "${cmd[@]}"
}

run_search() {
  if [ "$SEARCH_CMD" = "rg" ]; then
    eval "$(build_rg_cmd)" 2>/dev/null | head -"$LIMIT" || true
  else
    eval "$(build_grep_cmd)" 2>/dev/null | head -"$LIMIT" || true
  fi
}

# ----- JSON 出力 -----

output_json() {
  local raw
  raw=$(run_search)
  if [ -z "$raw" ]; then
    echo '{"keyword":"'"$KEYWORD"'","mode":"'"$MODE"'","results":[],"count":0}'
    return
  fi

  local count
  count=$(echo "$raw" | wc -l | tr -d ' ')

  # 各行を "file:line:content" 形式でパース
  local json_items=()
  while IFS= read -r line; do
    local file lnum content
    file=$(echo "$line" | cut -d: -f1)
    lnum=$(echo "$line" | cut -d: -f2)
    content=$(echo "$line" | cut -d: -f3- | sed 's/"/\\"/g' | tr -d '\r')
    json_items+=('{"file":"'"$file"'","line":'"$lnum"',"content":"'"$content"'"}')
  done <<< "$raw"

  local joined
  joined=$(IFS=,; echo "${json_items[*]}")

  echo '{"keyword":"'"$KEYWORD"'","mode":"'"$MODE"'","target":"'"$TARGET_DIR"'","results":['"$joined"'],"count":'"$count"'}'
}

# ----- メイン出力 -----

if $OUTPUT_JSON; then
  output_json
else
  echo "=== L1 キーワード検索: \"${KEYWORD}\" ==="
  echo "  モード    : ${MODE}"
  echo "  ツール    : ${SEARCH_CMD}"
  echo "  ディレクトリ: ${TARGET_DIR}"
  [ -n "$FILE_TYPE" ] && echo "  ファイル種別: ${FILE_TYPE}"
  echo ""

  result=$(run_search)
  if [ -z "$result" ]; then
    echo "(ヒットなし)"
  else
    echo "$result"
    count=$(echo "$result" | wc -l | tr -d ' ')
    echo ""
    echo "--- ${count} 件ヒット（最大 ${LIMIT} 件）---"
  fi
fi
