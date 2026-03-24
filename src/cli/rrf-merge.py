#!/usr/bin/env python3
"""
context-and-impact: RRF Retrieval Aggregator
L1(Grep/Glob)・L2b(GitNexus KùzuDB)・L3(SmartConnections) の3層結果を
Reciprocal Rank Fusion でマージし単一ランキングを返す。

Usage:
  python3 rrf-merge.py --l1 l1.json --l2b l2b.json --l3 l3.json --limit 20
  echo '["doc_a","doc_b"]' | python3 rrf-merge.py --l1 - --l2b l2b.json
  python3 rrf-merge.py --inline '{"l1":["doc_a","doc_b"],"l2b":["doc_b","doc_c"],"l3":["doc_a","doc_c"]}'
"""

import sys
import json
import argparse

RRF_K = 60


def rrf_score(rank: int, k: int = RRF_K) -> float:
    """1-indexed rank の RRF スコアを返す"""
    return 1.0 / (k + rank)


def merge(layer_docs: dict[str, list[str]], k: int = RRF_K) -> list[dict]:
    """
    各層のドキュメントリストを Reciprocal Rank Fusion でマージする。

    Args:
        layer_docs: {"l1": ["doc_a", ...], "l2b": [...], "l3": [...]}
        k: RRF 定数（デフォルト 60）

    Returns:
        rrf_score 降順のリスト: [{"doc": str, "rrf_score": float, "sources": list[str]}, ...]
    """
    scores: dict[str, float] = {}
    sources: dict[str, list[str]] = {}

    for layer_name, docs in layer_docs.items():
        if not docs:
            continue
        for rank, doc in enumerate(docs, start=1):
            s = rrf_score(rank, k)
            scores[doc] = scores.get(doc, 0.0) + s
            if doc not in sources:
                sources[doc] = []
            if layer_name not in sources[doc]:
                sources[doc].append(layer_name)

    results = [
        {"doc": doc, "rrf_score": round(score, 6), "sources": sources[doc]}
        for doc, score in scores.items()
    ]
    results.sort(key=lambda x: x["rrf_score"], reverse=True)
    return results


def load_json_arg(value: str | None) -> list[str]:
    """
    CLI 引数からドキュメントリストを読み込む。
    - None または未指定 → 空リスト
    - "-" → stdin から JSON 読み込み
    - それ以外 → ファイルパスとして読み込み
    """
    if not value:
        return []
    if value == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(value, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON パースエラー: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list):
        print("ERROR: JSON はリスト形式である必要があります", file=sys.stderr)
        sys.exit(1)
    if not all(isinstance(item, str) for item in data):
        print("ERROR: JSON リストの要素はすべて文字列である必要があります", file=sys.stderr)
        sys.exit(1)
    return data


def main():
    parser = argparse.ArgumentParser(
        description="RRF Retrieval Aggregator — L1+L2b+L3 multi-layer result fusion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python3 rrf-merge.py --l1 l1.json --l2b l2b.json --l3 l3.json --limit 20
  python3 rrf-merge.py --inline '{"l1":["doc_a","doc_b"],"l2b":["doc_b","doc_c"],"l3":["doc_a","doc_c"]}'
        """,
    )
    parser.add_argument("--l1", metavar="FILE", help="Layer 1 (Grep/Glob) 結果 JSON ファイル（- で stdin）")
    parser.add_argument("--l2b", metavar="FILE", help="Layer 2b (GitNexus) 結果 JSON ファイル（- で stdin）")
    parser.add_argument("--l3", metavar="FILE", help="Layer 3 (SmartConnections) 結果 JSON ファイル（- で stdin）")
    parser.add_argument(
        "--inline",
        metavar="JSON",
        help='全層をインライン JSON で指定: \'{"l1":[...],"l2b":[...],"l3":[...]}\'',
    )
    parser.add_argument("--limit", "-n", type=int, default=20, help="出力件数上限 (default: 20)")
    parser.add_argument("--k", type=int, default=RRF_K, help=f"RRF 定数 k (default: {RRF_K})")
    args = parser.parse_args()

    if args.inline:
        try:
            layer_docs = json.loads(args.inline)
        except json.JSONDecodeError as e:
            print(f"ERROR: --inline JSON パースエラー: {e}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(layer_docs, dict):
            print("ERROR: --inline はオブジェクト形式である必要があります", file=sys.stderr)
            sys.exit(1)
        # 各値がリストであることを確認
        for key, val in layer_docs.items():
            if not isinstance(val, list):
                print(f"ERROR: --inline の '{key}' はリストである必要があります", file=sys.stderr)
                sys.exit(1)
    else:
        layer_docs = {
            "l1": load_json_arg(args.l1),
            "l2b": load_json_arg(args.l2b),
            "l3": load_json_arg(args.l3),
        }

    results = merge(layer_docs, k=args.k)
    output = results[: args.limit] if args.limit > 0 else results
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
