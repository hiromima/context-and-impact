#!/usr/bin/env bash
# W3: ドメイン横断リンク探索（Obsidian wikilink グラフ L2b）
# 使い方: bash examples/w3-cross-domain.sh Docs-Legal Docs-Financial
set -euo pipefail

DOMAIN_A="${1:-Docs-Legal}"
DOMAIN_B="${2:-Docs-Financial}"

echo "=== W3: ドメイン横断リンク探索 ==="
echo "ドメイン A: $DOMAIN_A"
echo "ドメイン B: $DOMAIN_B"
echo ""

if ! command -v gitnexus &>/dev/null; then
  echo "❌ gitnexus が見つかりません: npm install -g gitnexus"
  exit 1
fi

# L2b: ドメイン横断リンク（2ホップ）
echo "--- L2b: ドメイン横断リンク (2ホップ) ---"
gitnexus cypher --repo obsidian "
MATCH (a:File)-[r1]->(mid:File)-[r2]->(b:File)
WHERE r1.reason = 'obsidian-wikilink'
  AND r2.reason = 'obsidian-wikilink'
  AND (
    a.filePath STARTS WITH '$DOMAIN_A'
    OR a.filePath STARTS WITH '$DOMAIN_B'
  )
RETURN a.name, mid.name, b.name
LIMIT 30
" 2>/dev/null || echo "⚠️  Obsidian GitNexus インデックスが未生成の可能性があります"

echo ""

# L2b: ドメインA の孤立ノート確認
echo "--- L2b: $DOMAIN_A の孤立ノート ---"
gitnexus cypher --repo obsidian "
MATCH (f:File)
WHERE f.filePath STARTS WITH '$DOMAIN_A'
  AND NOT (f)<-[]-(:File)
RETURN f.name, f.filePath
LIMIT 10
" 2>/dev/null || true

echo ""
echo "=== 完了 ==="
