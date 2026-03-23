#!/usr/bin/env python3
"""
context-and-impact: Layer 2b — Obsidian wikilink グラフ検索 CLI
gitnexus cypher --repo obsidian をラップし、
インパクト分析・依存グラフ探索・品質チェックを提供する。

Usage:
  python3 wikilink-search.py --find "auth"
  python3 wikilink-search.py --impact "auth-design.md"
  python3 wikilink-search.py --refs-to "auth-design.md"
  python3 wikilink-search.py --refs-from "auth-design.md"
  python3 wikilink-search.py --2hop "auth-design.md"
  python3 wikilink-search.py --orphans [--domain Docs-Legal]
  python3 wikilink-search.py --moc-stats
  python3 wikilink-search.py --top-linked
  python3 wikilink-search.py --query "MATCH (f:File) RETURN f LIMIT 5"

Options:
  --json       : JSON 形式で出力
  --limit N    : 結果件数（デフォルト: 20）
  --domain D   : ドメインフィルタ（例: Docs-Legal）
"""

import sys
import os
import json
import argparse
import subprocess
import shutil

GITNEXUS_CMD = shutil.which("gitnexus") or "gitnexus"
REPO = "obsidian"
WIKILINK_FILTER = "reason = 'obsidian-wikilink'"


def run_cypher(query: str) -> str:
    """gitnexus cypher を実行してテキスト結果を返す"""
    try:
        result = subprocess.run(
            [GITNEXUS_CMD, "cypher", "--repo", REPO, query],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"ERROR: {result.stderr.strip()}", file=sys.stderr)
            return ""
        return result.stdout.strip()
    except FileNotFoundError:
        print(
            f"ERROR: '{GITNEXUS_CMD}' が見つかりません。npm install -g gitnexus を実行してください。",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: タイムアウト（30秒）", file=sys.stderr)
        return ""


def parse_table_output(raw: str) -> list[dict]:
    """gitnexus cypher のテーブル出力を dict リストに変換（簡易パーサー）"""
    lines = [l for l in raw.splitlines() if l.strip() and not l.startswith("---")]
    if not lines:
        return []
    # ヘッダー行を検出（最初の非空行）
    headers = [h.strip() for h in lines[0].split("|") if h.strip()]
    rows = []
    for line in lines[1:]:
        values = [v.strip() for v in line.split("|") if v.strip()]
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))
    return rows


def cmd_find(keyword: str, limit: int, as_json: bool):
    """キーワードでノート検索（L1 的な用途も L2b で代替）"""
    query = f"""
MATCH (f:File)
WHERE f.name CONTAINS '{keyword}'
   OR f.filePath CONTAINS '{keyword}'
RETURN f.name, f.filePath
LIMIT {limit}
"""
    raw = run_cypher(query)
    if as_json:
        print(json.dumps({"query": keyword, "results": parse_table_output(raw)}, ensure_ascii=False, indent=2))
    else:
        print(f"=== キーワード検索: {keyword} ===")
        print(raw or "(ヒットなし)")


def cmd_impact(filename: str, limit: int, as_json: bool):
    """ノートのインパクト分析（参照元・参照先）"""
    query = f"""
MATCH (doc:File) WHERE doc.name = '{filename}'
OPTIONAL MATCH (doc)-[out]->(outbound:File)
  WHERE out.{WIKILINK_FILTER}
OPTIONAL MATCH (inbound:File)-[inn]->(doc)
  WHERE inn.{WIKILINK_FILTER}
RETURN
  doc.name AS target,
  collect(DISTINCT outbound.name) AS references_to,
  collect(DISTINCT inbound.name) AS referenced_by,
  size(collect(DISTINCT inbound.name)) AS impact_count
"""
    raw = run_cypher(query)
    if as_json:
        print(json.dumps({"target": filename, "result": parse_table_output(raw)}, ensure_ascii=False, indent=2))
    else:
        print(f"=== インパクト分析: {filename} ===")
        print(raw or "(ノートが見つからないかリンクなし)")


def cmd_refs_to(filename: str, limit: int, as_json: bool):
    """このノートが参照するノート一覧"""
    query = f"""
MATCH (doc:File)-[r]->(outbound:File)
WHERE doc.name = '{filename}'
  AND r.{WIKILINK_FILTER}
RETURN outbound.name, outbound.filePath
ORDER BY outbound.name
LIMIT {limit}
"""
    raw = run_cypher(query)
    if as_json:
        print(json.dumps({"source": filename, "references_to": parse_table_output(raw)}, ensure_ascii=False, indent=2))
    else:
        print(f"=== 参照先（{filename} → ?）===")
        print(raw or "(参照先なし)")


def cmd_refs_from(filename: str, limit: int, as_json: bool):
    """このノートを参照するノート一覧（被リンク）"""
    query = f"""
MATCH (inbound:File)-[r]->(doc:File)
WHERE doc.name = '{filename}'
  AND r.{WIKILINK_FILTER}
RETURN inbound.name, inbound.filePath
ORDER BY inbound.name
LIMIT {limit}
"""
    raw = run_cypher(query)
    if as_json:
        print(json.dumps({"target": filename, "referenced_by": parse_table_output(raw)}, ensure_ascii=False, indent=2))
    else:
        print(f"=== 参照元（? → {filename}）===")
        print(raw or "(参照元なし)")


def cmd_2hop(filename: str, limit: int, as_json: bool):
    """2ホップ先まで展開"""
    query = f"""
MATCH (src:File)-[r1]->(mid:File)-[r2]->(dst:File)
WHERE src.name = '{filename}'
  AND r1.{WIKILINK_FILTER}
  AND r2.{WIKILINK_FILTER}
RETURN src.name, mid.name, dst.name
LIMIT {limit}
"""
    raw = run_cypher(query)
    if as_json:
        print(json.dumps({"source": filename, "2hop": parse_table_output(raw)}, ensure_ascii=False, indent=2))
    else:
        print(f"=== 2ホップ展開: {filename} ===")
        print(raw or "(2ホップ先なし)")


def cmd_orphans(domain: str, limit: int, as_json: bool):
    """孤立ノート検出（どこからもリンクされていない）"""
    domain_filter = f"AND f.filePath STARTS WITH '{domain}'" if domain else ""
    query = f"""
MATCH (f:File)
WHERE NOT (f)<-[]-(:File)
  AND NOT f.filePath STARTS WITH 'Daily/'
  AND NOT f.filePath STARTS WITH 'Archive/'
  {domain_filter}
RETURN f.name, f.filePath
LIMIT {limit}
"""
    raw = run_cypher(query)
    results = parse_table_output(raw)
    if as_json:
        print(json.dumps({"domain": domain or "all", "orphans": results, "count": len(results)}, ensure_ascii=False, indent=2))
    else:
        print(f"=== 孤立ノート{' (' + domain + ')' if domain else ''} ===")
        print(raw or "(孤立ノートなし — 健全です)")
        if raw:
            count = len([l for l in raw.splitlines() if l.strip() and not l.startswith("---")])
            print(f"\n合計: {count} ノート")


def cmd_moc_stats(limit: int, as_json: bool):
    """MOC 別ドキュメント数"""
    query = f"""
MATCH (moc:File)-[r]->(doc:File)
WHERE moc.filePath STARTS WITH 'MOCs/'
  AND r.{WIKILINK_FILTER}
RETURN moc.name AS moc, count(doc) AS linked_docs
ORDER BY linked_docs DESC
LIMIT {limit}
"""
    raw = run_cypher(query)
    if as_json:
        print(json.dumps({"moc_stats": parse_table_output(raw)}, ensure_ascii=False, indent=2))
    else:
        print("=== MOC 別ドキュメント数 ===")
        print(raw or "(MOCなし)")


def cmd_top_linked(limit: int, as_json: bool):
    """被リンク数が多いノート TOP N"""
    query = f"""
MATCH (inbound:File)-[r]->(doc:File)
WHERE r.{WIKILINK_FILTER}
RETURN doc.name, count(inbound) AS inbound_count
ORDER BY inbound_count DESC
LIMIT {limit}
"""
    raw = run_cypher(query)
    if as_json:
        print(json.dumps({"top_linked": parse_table_output(raw)}, ensure_ascii=False, indent=2))
    else:
        print(f"=== 被リンク数 TOP {limit} ===")
        print(raw or "(データなし)")


def cmd_raw_query(query: str, as_json: bool):
    """任意の Cypher クエリを実行"""
    raw = run_cypher(query)
    if as_json:
        print(json.dumps({"query": query, "result": parse_table_output(raw)}, ensure_ascii=False, indent=2))
    else:
        print(raw)


def main():
    parser = argparse.ArgumentParser(
        description="Layer 2b: Obsidian wikilink グラフ検索 CLI"
    )
    # 操作
    parser.add_argument("--find", "-f", metavar="KEYWORD", help="キーワードでノート検索")
    parser.add_argument("--impact", "-i", metavar="FILE", help="インパクト分析（参照元・参照先）")
    parser.add_argument("--refs-to", metavar="FILE", help="参照先一覧（このノート→?）")
    parser.add_argument("--refs-from", metavar="FILE", help="参照元一覧（?→このノート）")
    parser.add_argument("--2hop", dest="hop2", metavar="FILE", help="2ホップ展開")
    parser.add_argument("--orphans", action="store_true", help="孤立ノート検出")
    parser.add_argument("--moc-stats", action="store_true", help="MOC別ドキュメント数")
    parser.add_argument("--top-linked", action="store_true", help="被リンク数 TOP N")
    parser.add_argument("--query", "-q", metavar="CYPHER", help="任意の Cypher クエリ")
    # オプション
    parser.add_argument("--json", action="store_true", help="JSON 出力")
    parser.add_argument("--limit", "-n", type=int, default=20, help="結果件数 (default: 20)")
    parser.add_argument("--domain", "-d", default="", help="ドメインフィルタ (例: Docs-Legal)")

    args = parser.parse_args()
    as_json = args.json
    limit = args.limit

    if args.find:
        cmd_find(args.find, limit, as_json)
    elif args.impact:
        cmd_impact(args.impact, limit, as_json)
    elif args.refs_to:
        cmd_refs_to(args.refs_to, limit, as_json)
    elif args.refs_from:
        cmd_refs_from(args.refs_from, limit, as_json)
    elif args.hop2:
        cmd_2hop(args.hop2, limit, as_json)
    elif args.orphans:
        cmd_orphans(args.domain, limit, as_json)
    elif args.moc_stats:
        cmd_moc_stats(limit, as_json)
    elif args.top_linked:
        cmd_top_linked(limit, as_json)
    elif args.query:
        cmd_raw_query(args.query, as_json)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
