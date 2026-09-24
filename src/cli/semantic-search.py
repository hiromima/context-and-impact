#!/usr/bin/env python3
"""
context-and-impact: Layer 3 セマンティック検索 CLI

Python 3.14 + torch の SIGSEGV クラッシュを回避するため、
埋め込み処理は Python 3.11（torch 互換）のサブプロセスで実行する。
メインプロセスには torch を一切インポートしない。

Usage:
  QUERY="合同会社みやび 設立" python3 semantic-search.py
  python3 semantic-search.py --status
  python3 semantic-search.py --query "認証 JWT" --limit 10
"""

import sys
import os
import json
import math
import argparse
import subprocess
import shutil
from pathlib import Path

# README の「Key variables」と同じく OBSIDIAN_DIR で vault を指定できる (既定は従来の場所)
OBSIDIAN_VAULT = Path(os.path.expanduser(os.environ.get("OBSIDIAN_DIR") or "~/dev/content/obsidian"))
MULTI_PATH = OBSIDIAN_VAULT / ".smart-env" / "multi"
MODEL_NAME = "TaylorAI/bge-micro-v2"

# torch 互換の Python を優先して探す（3.11 > 3.12 > 3.13 > 現在の python3）
_TORCH_PYTHON: str | None = None


def find_torch_python() -> str:
    """sentence_transformers が動く Python インタープリタを返す"""
    global _TORCH_PYTHON
    if _TORCH_PYTHON is not None:
        return _TORCH_PYTHON

    candidates = ["python3.11", "python3.12", "python3.13", "python3", sys.executable]
    for candidate in candidates:
        path = shutil.which(candidate)
        if path is None:
            continue
        result = subprocess.run(
            [path, "-c", "from sentence_transformers import SentenceTransformer; print('ok')"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            _TORCH_PYTHON = path
            return path

    # フォールバック: 現在の python3 を使う（クラッシュするかもしれないが最善努力）
    _TORCH_PYTHON = sys.executable
    return _TORCH_PYTHON


# ---------------------------------------------------------------------------
# .ajson 直接パース（torch 不要）
# ---------------------------------------------------------------------------

def load_cache() -> dict:
    """
    .ajson ファイルを直接読み込み、埋め込みキャッシュを返す。
    形式: "key": {...},\n  (SmartConnections 独自 AJSON)
    """
    cache = {}
    if not MULTI_PATH.exists():
        return cache

    for ajson_file in MULTI_PATH.glob("*.ajson"):
        try:
            content = ajson_file.read_text(encoding="utf-8").strip()
            if not content:
                continue
            # AJSON → JSON 変換: 末尾カンマを除去してオブジェクトにラップ
            content = content.rstrip(",")
            data = json.loads("{" + content + "}")
            for key, item in data.items():
                try:
                    emb = item.get("embeddings", {}).get(MODEL_NAME, {})
                    vec = emb.get("vec") or emb.get("vector")
                    if vec is not None:
                        path = key
                        if isinstance(item, dict):
                            for pf in ("path", "file_path"):
                                v = item.get(pf)
                                if isinstance(v, str) and v:
                                    path = v
                                    break
                        cache[key] = {"path": path, "_vec": vec}
                except Exception:
                    pass
        except Exception as e:
            print(f"WARN: {ajson_file.name}: {e}", file=sys.stderr)

    return cache


# ---------------------------------------------------------------------------
# 純粋 Python コサイン類似度（torch 不要）
# ---------------------------------------------------------------------------

def cosine_similarity(v1: list, v2: list) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


# ---------------------------------------------------------------------------
# クエリ埋め込み — torch 互換 Python のサブプロセスで実行
# ---------------------------------------------------------------------------

EMBED_SCRIPT = r"""
import os, sys, json
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
query = sys.argv[1]
model_name = sys.argv[2]
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(model_name)
vec = model.encode(query, normalize_embeddings=True).tolist()
print(json.dumps(vec))
"""


def embed_query(query: str) -> list | None:
    """
    sentence_transformers を torch 互換 Python のサブプロセスで実行する。
    メインプロセス（Python 3.14）には torch を一切インポートしない。
    """
    python = find_torch_python()
    try:
        result = subprocess.run(
            [python, "-c", EMBED_SCRIPT, query, MODEL_NAME],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"ERROR: 埋め込みサブプロセスが失敗しました (returncode={result.returncode})", file=sys.stderr)
            if result.stderr:
                lines = result.stderr.strip().splitlines()
                for line in lines[-5:]:
                    print(f"  {line}", file=sys.stderr)
            return None
        return json.loads(result.stdout.strip())
    except subprocess.TimeoutExpired:
        print("ERROR: 埋め込みがタイムアウトしました（120秒）", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: 埋め込み中に例外が発生しました: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# コマンド実装
# ---------------------------------------------------------------------------

def status():
    """埋め込み状態を表示（torch 不要）"""
    cache = load_cache()
    total = len(cache)
    print(f"Obsidian vault: {OBSIDIAN_VAULT}")
    print(f"AJSON ディレクトリ: {MULTI_PATH}")
    print(f"Embedded notes: {total}")
    if total > 0:
        sample = next(iter(cache.values()))
        dim = len(sample.get("_vec", []))
        print(f"Vector dim: {dim}")
        print(f"Model: {MODEL_NAME}")
        python = find_torch_python()
        print(f"Embed Python: {python}")
    else:
        if not MULTI_PATH.exists():
            print(f"WARN: {MULTI_PATH} が存在しません", file=sys.stderr)
            print("  Obsidian の Smart Connections プラグインでインデックス化してください", file=sys.stderr)


def search(query: str, limit: int = 10):
    """セマンティック検索を実行して結果を表示する"""
    cache = load_cache()
    if not cache:
        print("ERROR: 埋め込みキャッシュが空です。`npm run status` で状態を確認してください", file=sys.stderr)
        sys.exit(1)

    print(f"クエリ: {query!r}", file=sys.stderr)
    print(f"インデックス済みノート数: {len(cache)}", file=sys.stderr)
    print("埋め込み中...", file=sys.stderr)

    query_vec = embed_query(query)
    if query_vec is None:
        sys.exit(1)

    scored = []
    for key, item in cache.items():
        vec = item.get("_vec")
        if vec is None:
            continue
        sim = cosine_similarity(query_vec, vec)
        scored.append((sim, item.get("path", key)))

    scored.sort(key=lambda x: x[0], reverse=True)

    for sim, path in scored[:limit]:
        print(f"{sim:.3f}  {path}")

    return scored[:limit]


# ---------------------------------------------------------------------------
# エントリーポイント
# ---------------------------------------------------------------------------

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
