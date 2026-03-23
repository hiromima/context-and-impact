# GitNexus Cypher クエリライブラリ

Layer 2b: Obsidian wikilink グラフ用クエリ集。
KùzuDB 使用（`split()` 非対応、`STARTS WITH` で代替）。

---

## ノート検索

### キーワードでノート検索
```cypher
MATCH (f:File)
WHERE f.name CONTAINS '{キーワード}'
   OR f.filePath CONTAINS '{キーワード}'
RETURN f.name, f.filePath
LIMIT 20
```

### タグで検索（フロントマター）
```bash
# Grep でフロントマターを検索してから GNI でノードを取得
grep -r "tags:.*{タグ}" ~/dev/content/obsidian/ --include="*.md" -l | head -10
```

---

## インパクト分析

### ノートのインパクト分析（参照元・参照先）
```cypher
MATCH (doc:File) WHERE doc.name = '{filename.md}'
OPTIONAL MATCH (doc)-[out]->(outbound:File)
  WHERE out.reason = 'obsidian-wikilink'
OPTIONAL MATCH (inbound:File)-[inn]->(doc)
  WHERE inn.reason = 'obsidian-wikilink'
RETURN
  doc.name AS target,
  collect(DISTINCT outbound.name) AS references_to,
  collect(DISTINCT inbound.name) AS referenced_by,
  size(collect(DISTINCT inbound.name)) AS impact_count
```

### 参照元のみ（誰がこのノートをリンクしているか）
```cypher
MATCH (inbound:File)-[r]->(doc:File)
WHERE doc.name = '{filename.md}'
  AND r.reason = 'obsidian-wikilink'
RETURN inbound.name, inbound.filePath
ORDER BY inbound.name
```

### 参照先のみ（このノートが参照しているノート）
```cypher
MATCH (doc:File)-[r]->(outbound:File)
WHERE doc.name = '{filename.md}'
  AND r.reason = 'obsidian-wikilink'
RETURN outbound.name, outbound.filePath
ORDER BY outbound.name
```

---

## 依存グラフ探索

### 2ホップ先まで展開
```cypher
MATCH (src:File)-[r1]->(mid:File)-[r2]->(dst:File)
WHERE src.name = '{filename.md}'
  AND r1.reason = 'obsidian-wikilink'
  AND r2.reason = 'obsidian-wikilink'
RETURN src.name, mid.name, dst.name
LIMIT 30
```

### ドメイン横断リンク探索（Legal ↔ Financial）
```cypher
MATCH (a:File)-[r1]->(mid:File)-[r2]->(b:File)
WHERE r1.reason = 'obsidian-wikilink'
  AND r2.reason = 'obsidian-wikilink'
  AND (
    a.filePath STARTS WITH 'Docs-Legal'
    OR a.filePath STARTS WITH 'Docs-Financial'
  )
RETURN a.name, mid.name, b.name
LIMIT 30
```

---

## 品質チェック

### 孤立ノート検出（どこからもリンクされていない）
```cypher
MATCH (f:File)
WHERE NOT (f)<-[]-(:File)
  AND NOT f.filePath STARTS WITH 'Daily/'
RETURN f.name, f.filePath
LIMIT 20
```

### MOC別ドキュメント数
```cypher
MATCH (moc:File)-[r]->(doc:File)
WHERE moc.filePath STARTS WITH 'MOCs/'
  AND r.reason = 'obsidian-wikilink'
RETURN moc.name AS moc, count(doc) AS linked_docs
ORDER BY linked_docs DESC
```

### リンクが多いノート TOP 20
```cypher
MATCH (inbound:File)-[r]->(doc:File)
WHERE r.reason = 'obsidian-wikilink'
RETURN doc.name, count(inbound) AS inbound_count
ORDER BY inbound_count DESC
LIMIT 20
```

---

## 使用方法

```bash
# CLI から実行
gitnexus cypher --repo obsidian "MATCH (f:File) WHERE f.name CONTAINS 'auth' RETURN f.name LIMIT 10"

# ファイルから実行
gitnexus cypher --repo obsidian --file src/gitnexus/queries/{query-file}.cypher
```

---

*注意*:
- `split()` 関数は KùzuDB で非対応 → `STARTS WITH` で代替
- wikilink エッジは `reason = 'obsidian-wikilink'` でフィルタ必須
- インデックスが古い場合は `gitnexus analyze --force --embeddings` で再構築
