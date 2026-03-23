#!/usr/bin/env bash
# W6: Obsidian オーファン（孤立ノート）有機的リンキングルーチン
#
# 目的:
#   どこからもリンクされていないノートを発見し、
#   L3（セマンティック検索）で意味的に近いノートを見つけて
#   wikilink 追加候補をエージェントに提示する。
#
# 使い方:
#   bash examples/w6-orphan-linking.sh [--auto] [--domain Docs-Legal]
#   npm run orphan-link
#
# オプション:
#   --auto    : 候補を自動で表示するだけ（確認なし）
#   --domain  : 対象ドメイン（デフォルト: 全体）
#   --limit   : 処理するオーファン数（デフォルト: 20）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
OBSIDIAN_DIR="${OBSIDIAN_DIR:-$HOME/dev/content/obsidian}"
AUTO=false
DOMAIN=""
LIMIT=20

# 引数パース
while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto)   AUTO=true; shift ;;
    --domain) DOMAIN="$2"; shift 2 ;;
    --limit)  LIMIT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

echo "==================================================================="
echo "  W6: Obsidian オーファン有機的リンキングルーチン"
echo "  ドメイン: ${DOMAIN:-全体}"
echo "  上限: $LIMIT ノート"
echo "==================================================================="
echo ""

# ─────────────────────────────────────
# Step 1: オーファンノードの発見（L2b）
# ─────────────────────────────────────
echo "━━━ Step 1: 孤立ノート（オーファン）発見 ━━━"
echo ""

if ! command -v gitnexus &>/dev/null; then
  echo "❌ gitnexus が見つかりません: npm install -g gitnexus"
  exit 1
fi

DOMAIN_FILTER=""
if [ -n "$DOMAIN" ]; then
  DOMAIN_FILTER="AND f.filePath STARTS WITH '${DOMAIN}'"
fi

ORPHAN_QUERY="
MATCH (f:File)
WHERE NOT (f)<-[]-(:File)
  AND NOT f.filePath STARTS WITH 'Daily/'
  AND NOT f.filePath STARTS WITH 'Archive/'
  AND NOT f.filePath STARTS WITH '_templates/'
  $DOMAIN_FILTER
RETURN f.name, f.filePath
LIMIT $LIMIT
"

echo "孤立ノートを検索中..."
ORPHANS=$(gitnexus cypher --repo obsidian "$ORPHAN_QUERY" 2>/dev/null) || {
  echo "⚠️  GitNexus Obsidian インデックスが見つかりません"
  echo "  実行: gitnexus analyze --path $OBSIDIAN_DIR"
  exit 1
}

if [ -z "$ORPHANS" ]; then
  echo "✅ 孤立ノートなし！ナレッジグラフは健全です。"
  exit 0
fi

ORPHAN_COUNT=$(echo "$ORPHANS" | grep -c "f.name" || echo 0)
echo "発見した孤立ノート数: $ORPHAN_COUNT"
echo ""
echo "$ORPHANS"
echo ""

# ─────────────────────────────────────
# Step 2: セマンティック類似ノード探索（L3）
# ─────────────────────────────────────
echo "━━━ Step 2: 意味的に近いノードを探索（L3）━━━"
echo ""

if [ ! -f "$ROOT_DIR/src/cli/semantic-search.py" ]; then
  echo "⚠️  semantic-search.py が見つかりません"
  echo "  L2b（wikilink グラフ）のみで代替します"
  echo ""
else
  # オーファンのファイル名からクエリを生成してセマンティック検索
  echo "$ORPHANS" | grep -oP '(?<=f\.name: )[^\s,]+' 2>/dev/null | \
  while IFS= read -r orphan_name; do
    if [ -n "$orphan_name" ]; then
      echo "--- $orphan_name の類似ノート ---"
      # ファイル名から検索クエリを生成（kebab-case → スペース区切り）
      SEARCH_QUERY=$(echo "$orphan_name" | sed 's/-/ /g; s/\.md$//')
      python3 "$ROOT_DIR/src/cli/semantic-search.py" \
        --query "$SEARCH_QUERY" --limit 3 2>/dev/null || \
        echo "  (SmartConnections インデックス未生成)"
      echo ""
    fi
  done
fi

# ─────────────────────────────────────
# Step 3: リンキング候補の提示
# ─────────────────────────────────────
echo "━━━ Step 3: リンキング候補 ━━━"
echo ""
echo "以下のアクションを推奨します:"
echo ""
echo "  A. 最も近いMOCにwikilink を追加"
echo "     → MOCs/ フォルダのノートに [[orphan-note-name]] を追記"
echo ""
echo "  B. 関連するドキュメントに双方向リンクを追加"
echo "     → orphan-note.md に [[related-note]] を追記"
echo "     → related-note.md に [[orphan-note]] を追記"
echo ""
echo "  C. Daily ノートから過去の言及を確認"
gitnexus cypher --repo obsidian "
MATCH (daily:File)-[r]->(orphan:File)
WHERE daily.filePath STARTS WITH 'Daily/'
  AND r.reason = 'obsidian-wikilink'
  AND NOT (orphan)<-[:LINK]-(:File {filePath: {non_daily: true}})
RETURN daily.name, orphan.name
LIMIT 5
" 2>/dev/null || true
echo ""

# ─────────────────────────────────────
# Step 4: 自動修正候補（--auto オプション）
# ─────────────────────────────────────
if [ "$AUTO" = true ]; then
  echo "━━━ Step 4: 自動リンキング候補生成 ━━━"
  echo ""
  echo "注意: 以下はエージェントへの提案です。実際の編集はユーザーが確認してください。"
  echo ""

  # ドメイン別のMOCマッピング
  declare -A MOC_MAP=(
    ["Docs-Legal"]="MOCs/Legal-MOC"
    ["Docs-Financial"]="MOCs/Financial-MOC"
    ["Docs-BusinessPlan"]="MOCs/Business-MOC"
    ["Docs-Operations"]="MOCs/Operations-MOC"
    ["Docs-OpenClaw"]="MOCs/OpenClaw-MOC"
  )

  echo "$ORPHANS" | grep -oP '(?<=f\.filePath: )[^\s,]+' 2>/dev/null | \
  while IFS= read -r orphan_path; do
    if [ -n "$orphan_path" ]; then
      DOMAIN=$(echo "$orphan_path" | cut -d'/' -f1)
      MOC="${MOC_MAP[$DOMAIN]:-MOCs/Index}"
      echo "  提案: $OBSIDIAN_DIR/$MOC.md"
      echo "    に追記: [[${orphan_path%.md}]]"
      echo ""
    fi
  done
fi

echo "==================================================================="
echo "  W6: 完了"
echo ""
echo "  定期実行推奨: 週1回（LaunchAgentまたはcronで自動化）"
echo "  例: 0 9 * * 1 bash $0 --auto >> ~/dev/logs/orphan-linking.log"
echo "==================================================================="
