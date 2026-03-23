#!/usr/bin/env bash
# W4: Obsidian ナレッジグラフ品質チェック
# 使い方: bash examples/w4-quality-check.sh
set -euo pipefail

echo "=== W4: Obsidian 品質チェック ==="
echo ""

if ! command -v gitnexus &>/dev/null; then
  echo "❌ gitnexus が見つかりません: npm install -g gitnexus"
  exit 1
fi

# 1. 孤立ノート検出
echo "--- 孤立ノート（どこからもリンクされていない）---"
gitnexus cypher --repo obsidian "
MATCH (f:File)
WHERE NOT (f)<-[]-(:File)
  AND NOT f.filePath STARTS WITH 'Daily/'
RETURN f.name, f.filePath
LIMIT 20
" 2>/dev/null || echo "エラー（インデックス未生成の可能性）"

echo ""

# 2. MOC別ドキュメント数
echo "--- MOC 別ドキュメント数 ---"
gitnexus cypher --repo obsidian "
MATCH (moc:File)-[r]->(doc:File)
WHERE moc.filePath STARTS WITH 'MOCs/'
  AND r.reason = 'obsidian-wikilink'
RETURN moc.name AS moc, count(doc) AS linked_docs
ORDER BY linked_docs DESC
" 2>/dev/null || true

echo ""

# 3. 被リンク数 TOP 20
echo "--- 被リンク数 TOP 20 ---"
gitnexus cypher --repo obsidian "
MATCH (inbound:File)-[r]->(doc:File)
WHERE r.reason = 'obsidian-wikilink'
RETURN doc.name, count(inbound) AS inbound_count
ORDER BY inbound_count DESC
LIMIT 20
" 2>/dev/null || true

echo ""
echo "=== 完了 ==="
echo "孤立ノートが多い場合: 対応するMOCにwikilink を追加してください"
