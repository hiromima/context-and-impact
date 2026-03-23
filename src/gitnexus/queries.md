# GitNexus Cypher クエリライブラリ

**Layer 2b**: Obsidian wikilink グラフ用クエリ集（完全版）。
KùzuDB 使用（`split()` 非対応、`STARTS WITH` で代替）。

> コピペ即使用可。`{プレースホルダー}` を実際の値に置換すること。

---

## KùzuDB 制約一覧（必読）

| 制限 | 代替方法 |
|------|---------|
| `split(str, delim)` 非対応 | `STARTS WITH`, `CONTAINS`, `ENDS WITH` を使用 |
| wikilink エッジの識別 | 必ず `WHERE r.reason = 'obsidian-wikilink'` を付ける |
| 日付計算関数の一部 | 日付文字列を `CONTAINS` で比較 |
| 可変長パスの `*` | 固定ホップ数で代替（2ホップ=2ノード展開） |

---

## W1: キーワード検索（L1 的用途を L2b で代替）

### キーワードでノート検索（名前・パス）

```cypher
MATCH (f:File)
WHERE f.name CONTAINS '{キーワード}'
   OR f.filePath CONTAINS '{キーワード}'
RETURN f.name, f.filePath
LIMIT 20
```

### ドメイン内ノート一覧

```cypher
MATCH (f:File)
WHERE f.filePath STARTS WITH '{ドメイン名}'
RETURN f.name, f.filePath
ORDER BY f.name
LIMIT 50
```

例: ドメイン名 = `Docs-Legal`, `Docs-Financial`, `Docs-OpenClaw`, `Daily`

### タグで検索（フロントマター経由）

```bash
# Grep でフロントマターを検索してから GitNexus でノードを取得
grep -r "tags:.*{タグ}" ~/dev/content/obsidian/ --include="*.md" -l | head -10
```

---

## W2: インパクト分析

### ノートのインパクト分析（参照元・参照先・件数）

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

### 影響度スコアリング（被リンク数 × ドメイン重み）

```cypher
MATCH (inbound:File)-[r]->(doc:File)
WHERE r.reason = 'obsidian-wikilink'
RETURN
  doc.name,
  doc.filePath,
  count(inbound) AS inbound_count,
  CASE
    WHEN doc.filePath STARTS WITH 'Docs-Legal' THEN 'Legal'
    WHEN doc.filePath STARTS WITH 'Docs-Financial' THEN 'Financial'
    WHEN doc.filePath STARTS WITH 'Docs-Operations' THEN 'Operations'
    WHEN doc.filePath STARTS WITH 'MOCs/' THEN 'MOC'
    ELSE 'Other'
  END AS domain
ORDER BY inbound_count DESC
LIMIT 30
```

---

## W3: ドメイン横断リンク探索

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

### 任意2ドメイン間の橋渡しノード

```cypher
MATCH (a:File)-[r1]->(bridge:File)-[r2]->(b:File)
WHERE r1.reason = 'obsidian-wikilink'
  AND r2.reason = 'obsidian-wikilink'
  AND a.filePath STARTS WITH '{ドメインA}'
  AND b.filePath STARTS WITH '{ドメインB}'
RETURN bridge.name, bridge.filePath, count(*) AS bridge_count
ORDER BY bridge_count DESC
LIMIT 20
```

### Daily ノートから参照されているドキュメント（作業ログ追跡）

```cypher
MATCH (daily:File)-[r]->(doc:File)
WHERE daily.filePath STARTS WITH 'Daily/'
  AND r.reason = 'obsidian-wikilink'
  AND NOT doc.filePath STARTS WITH 'Daily/'
RETURN doc.name, count(daily) AS mention_count
ORDER BY mention_count DESC
LIMIT 20
```

---

## W4: 品質チェック

### 孤立ノート検出（どこからもリンクされていない）

```cypher
MATCH (f:File)
WHERE NOT (f)<-[]-(:File)
  AND NOT f.filePath STARTS WITH 'Daily/'
  AND NOT f.filePath STARTS WITH 'Archive/'
  AND NOT f.filePath STARTS WITH '_templates/'
RETURN f.name, f.filePath
LIMIT 20
```

### ドメイン別の孤立ノート

```cypher
MATCH (f:File)
WHERE NOT (f)<-[]-(:File)
  AND f.filePath STARTS WITH '{ドメイン名}'
RETURN f.name, f.filePath
ORDER BY f.name
LIMIT 20
```

### デッドリンク検出（リンク先が存在しないエッジ）

```cypher
MATCH (src:File)-[r]->(dst:File)
WHERE r.reason = 'obsidian-wikilink'
  AND dst.name IS NULL
RETURN src.name, r.target AS broken_link
LIMIT 20
```

### MOC 別ドキュメント数

```cypher
MATCH (moc:File)-[r]->(doc:File)
WHERE moc.filePath STARTS WITH 'MOCs/'
  AND r.reason = 'obsidian-wikilink'
RETURN moc.name AS moc, count(doc) AS linked_docs
ORDER BY linked_docs DESC
```

### MOC にリンクされていないドメインドキュメント

```cypher
MATCH (f:File)
WHERE f.filePath STARTS WITH '{ドメイン名}'
  AND NOT (:File {filePath: 'MOCs/'})-[]-(f)
RETURN f.name, f.filePath
LIMIT 20
```

### 被リンク数 TOP 20（ハブノード）

```cypher
MATCH (inbound:File)-[r]->(doc:File)
WHERE r.reason = 'obsidian-wikilink'
RETURN doc.name, count(inbound) AS inbound_count
ORDER BY inbound_count DESC
LIMIT 20
```

---

## W5: 完全分析（フルパイプライン向け）

### ナレッジグラフ全体統計

```cypher
MATCH (f:File)
RETURN
  count(f) AS total_notes,
  sum(CASE WHEN NOT (f)<-[]-(:File) THEN 1 ELSE 0 END) AS orphan_count
```

### ドメイン別ノード数・リンク数

```cypher
MATCH (f:File)
OPTIONAL MATCH (f)-[r]->(other:File)
  WHERE r.reason = 'obsidian-wikilink'
RETURN
  CASE
    WHEN f.filePath STARTS WITH 'Docs-Legal' THEN 'Legal'
    WHEN f.filePath STARTS WITH 'Docs-Financial' THEN 'Financial'
    WHEN f.filePath STARTS WITH 'Docs-Operations' THEN 'Operations'
    WHEN f.filePath STARTS WITH 'Docs-OpenClaw' THEN 'OpenClaw'
    WHEN f.filePath STARTS WITH 'Daily/' THEN 'Daily'
    WHEN f.filePath STARTS WITH 'MOCs/' THEN 'MOC'
    ELSE 'Other'
  END AS domain,
  count(DISTINCT f) AS note_count,
  count(r) AS link_count
ORDER BY note_count DESC
```

### エージェント別参照ノート分析（OpenClaw エージェント向け）

```cypher
MATCH (agent:File)-[r]->(doc:File)
WHERE agent.filePath STARTS WITH 'Docs-OpenClaw/agents/'
  AND r.reason = 'obsidian-wikilink'
RETURN agent.name AS agent, collect(doc.name) AS linked_docs, count(doc) AS link_count
ORDER BY link_count DESC
```

---

## W6: オーファン有機的リンキング

### 孤立ノートと最も近い被リンクノード（リンキング候補）

```cypher
MATCH (orphan:File)
WHERE NOT (orphan)<-[]-(:File)
  AND NOT orphan.filePath STARTS WITH 'Daily/'
  AND NOT orphan.filePath STARTS WITH 'Archive/'
MATCH (linked:File)-[r]->(other:File)
  WHERE r.reason = 'obsidian-wikilink'
RETURN orphan.name AS orphan, linked.name AS potential_linker
LIMIT 30
```

### Daily ノートから言及されているが孤立しているノート

```cypher
MATCH (daily:File)-[r]->(orphan:File)
WHERE daily.filePath STARTS WITH 'Daily/'
  AND r.reason = 'obsidian-wikilink'
  AND NOT (orphan)<-[:LINK]-(:File)
RETURN daily.name, orphan.name AS potential_orphan
LIMIT 20
```

---

## CLI 使用方法

```bash
# インラインクエリ
gitnexus cypher --repo obsidian "MATCH (f:File) WHERE f.name CONTAINS 'auth' RETURN f.name LIMIT 10"

# Python CLI ラッパー（src/cli/wikilink-search.py）
python3 src/cli/wikilink-search.py --find "auth"
python3 src/cli/wikilink-search.py --impact "auth-design.md"
python3 src/cli/wikilink-search.py --refs-from "auth-design.md"
python3 src/cli/wikilink-search.py --orphans --domain Docs-Legal
python3 src/cli/wikilink-search.py --moc-stats
python3 src/cli/wikilink-search.py --top-linked
python3 src/cli/wikilink-search.py --json --impact "auth-design.md"  # JSON出力

# npm script
npm run w3  # ドメイン横断
npm run w4  # 品質チェック
```

---

*注意*:
- `split()` 関数は KùzuDB で非対応 → `STARTS WITH` で代替
- wikilink エッジは `reason = 'obsidian-wikilink'` でフィルタ必須
- インデックスが古い場合は `gitnexus analyze --force --embeddings` で再構築
- 可変長パス（`*`）は未対応 → 2ホップを `r1`, `r2` で明示的に記述
