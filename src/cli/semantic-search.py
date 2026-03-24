#!/usr/bin/env python3
"""
context-and-impact: Layer 3 セマンティック検索 CLI
SmartConnectionsDatabase を直接呼び出す。

Usage:
  QUERY="合同会社みやび 設立" python3 semantic-search.py
  python3 semantic-search.py --status
  python3 semantic-search.py --query "認証 JWT" --limit 10
"""

import sys
import os
import argparse

SMART_CONNECTIONS_PATH = os.path.expanduser(
    "~/dev/tools/smart-connections-mcp"
)
OBSIDIAN_VAULT = os.path.expanduser("~/dev/content/obsidian")


def get_db():
    sys.path.insert(0, SMART_CONNECTIONS_PATH)
    try:
        from server import SmartConnectionsDatabase
        db = SmartConnectionsDatabase(OBSIDIAN_VAULT)
        db.load_embeddings()
        return db
    except ImportError as e:
        print(f"ERROR: SmartConnectionsDatabase import failed: {e}", file=sys.stderr)
        print(f"  Check: {SMART_CONNECTIONS_PATH}/server.py", file=sys.stderr)
        sys.exit(1)


def search(query: str, limit: int = 10):
    db = get_db()
    results = db.semantic_search(query, limit=limit)
    for r in results:
        path = r.get("path", r.get("key", "unknown"))
        sim = r.get("similarity", 0)
        print(f"{sim:.3f}  {path}")
    return results


def status():
    db = get_db()
    cache = db.embeddings_cache
    total = len(cache)
    embedded = sum(1 for v in cache.values() if v.get("vector") is not None)
    print(f"Obsidian vault: {OBSIDIAN_VAULT}")
    print(f"Total notes: {total}")
    print(f"Embedded: {embedded}")
    print(f"Coverage: {embedded/total*100:.1f}%" if total > 0 else "Coverage: N/A")


def main():
    parser = argparse.ArgumentParser(description="Layer 3: Obsidian セマンティック検索")
    parser.add_argument("--query", "-q", help="検索クエリ")
    parser.add_argument("--limit", "-n", type=int, default=10, help="結果件数 (default: 10)")
    parser.add_argument("--status", action="store_true", help="埋め込み状態を表示")
    args = parser.parse_args()

    if args.status:
        status()
        return

    query = args.query or os.environ.get("QUERY")
    if not query:
        print("ERROR: クエリを指定してください: --query または QUERY 環境変数", file=sys.stderr)
        sys.exit(1)

    search(query, limit=args.limit)


if __name__ == "__main__":
    main()
