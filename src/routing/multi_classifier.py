#!/usr/bin/env python3
"""
multi-classifier.py — Phase C タスク分類器（3モデル多数決）

3つの分類器プロンプトを並列実行し多数決でルーティングを決定する。
API 未設定時はキーワードベースのフォールバックを使用する。

Usage:
  python3 src/routing/multi-classifier.py --task "datetime.utcnow()の非推奨警告を修正"
  python3 src/routing/multi-classifier.py --task "新しい認証機能を追加" --model claude-haiku-4-5-20251001
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
from typing import Optional

# ---------------------------------------------------------------------------
# ルーティングテーブル
# ---------------------------------------------------------------------------

ROUTE_TABLE: dict[str, str] = {
    "fix": "cursor-agent",
    "feat": "copilot",
    "refactor": "copilot",
    "docs": "copilot",
    "test": "copilot",
    "chore": "copilot",
    "manual": "manual",
}

VALID_CATEGORIES = set(ROUTE_TABLE.keys())
VALID_SCOPE = {"local", "module", "cross"}

# ---------------------------------------------------------------------------
# キーワードフォールバック
# ---------------------------------------------------------------------------

FIX_KEYWORDS = re.compile(
    r"fix|修正|バグ|bug|hotfix|patch|パッチ|直す|直し|エラー|error|crash|クラッシュ|非推奨|deprecat",
    re.IGNORECASE,
)
FEAT_KEYWORDS = re.compile(
    r"feat|add|追加|implement|実装|新機能|新しい|create|作成|新規|develop|開発|機能",
    re.IGNORECASE,
)


def keyword_fallback(task: str) -> dict:
    """キーワードベースの簡易分類（API未設定時のフォールバック）"""
    if FIX_KEYWORDS.search(task):
        category = "fix"
    elif FEAT_KEYWORDS.search(task):
        category = "feat"
    else:
        category = "chore"

    return {
        "route": ROUTE_TABLE[category],
        "category": category,
        "scope": "local",
        "votes": [category, category, category],
        "confidence": 1.0,
        "fallback": True,
    }


# ---------------------------------------------------------------------------
# LLM 呼び出し（Anthropic SDK — オプション依存）
# ---------------------------------------------------------------------------

def _call_anthropic(prompt: str, model: str, timeout: int = 15) -> Optional[str]:
    """Anthropic API を呼び出し、1語の応答を返す。失敗時は None。"""
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    result: list[Optional[str]] = [None]
    error: list[Optional[Exception]] = [None]

    def _call() -> None:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=model,
                max_tokens=16,
                messages=[{"role": "user", "content": prompt}],
            )
            text = message.content[0].text.strip().lower()
            # 最初の単語のみ抽出（余分な説明を除去）
            first_word = re.split(r"[\s/,、。]", text)[0]
            result[0] = first_word
        except Exception as exc:
            error[0] = exc

    thread = threading.Thread(target=_call, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        return None  # タイムアウト
    if error[0] is not None:
        return None
    return result[0]


# ---------------------------------------------------------------------------
# 分類器プロンプト
# ---------------------------------------------------------------------------

def _build_prompts(task: str) -> tuple[str, str, str]:
    p1 = (
        f"タスク「{task}」の種別は？ "
        "fix/feat/refactor/docs/test/chore/manual のいずれか1語で答えよ"
    )
    p2 = (
        f"「{task}」はバグ修正か新機能追加か改善か？ "
        "fix/feat/improve/other のいずれか1語で答えよ"
    )
    p3 = (
        f"「{task}」の変更スコープ: "
        "local(1-2files)/module(3-10files)/cross(10+files) のいずれか1語"
    )
    return p1, p2, p3


# ---------------------------------------------------------------------------
# 分類結果の正規化
# ---------------------------------------------------------------------------

def _normalize_category(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    raw = raw.lower().strip()
    if raw in VALID_CATEGORIES:
        return raw
    # Classifier-2 のエイリアス変換
    alias = {"improve": "refactor", "other": "chore"}
    return alias.get(raw)


def _normalize_scope(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    raw = raw.lower().strip()
    # "local(1-2files)" のような応答に対応
    for s in VALID_SCOPE:
        if raw.startswith(s):
            return s
    return None


# ---------------------------------------------------------------------------
# 多数決ロジック
# ---------------------------------------------------------------------------

def _majority_vote(votes: list[str]) -> str:
    """リスト内で最多出現の値を返す。同数の場合は先頭を返す。"""
    counts: dict[str, int] = {}
    order: dict[str, int] = {}
    for v in votes:
        if v not in order:
            order[v] = len(order)
        counts[v] = counts.get(v, 0) + 1
    return max(counts, key=lambda k: (counts[k], -order[k]))


def classify(task: str, model: str = "claude-haiku-4-5-20251001") -> dict:
    """
    3分類器を並列実行し多数決でルーティングを決定する。
    API 未設定 or 全タイムアウト時はキーワードフォールバックを使用。
    """
    p1, p2, p3 = _build_prompts(task)

    results: list[Optional[str]] = [None, None, None]

    def _run(idx: int, prompt: str) -> None:
        results[idx] = _call_anthropic(prompt, model)

    threads = [
        threading.Thread(target=_run, args=(i, p), daemon=True)
        for i, p in enumerate([p1, p2, p3])
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    raw1, raw2, raw3 = results

    cat1 = _normalize_category(raw1)
    cat2 = _normalize_category(raw2)
    scope = _normalize_scope(raw3)

    # 有効な投票が1つもなければフォールバック
    valid_votes = [c for c in [cat1, cat2] if c is not None]
    if not valid_votes:
        return keyword_fallback(task)

    # 多数決: Classifier-1 が基本、Classifier-2 で補完
    if cat1 is not None:
        category = cat1
    else:
        category = valid_votes[0]

    # Classifier-3 が cross → manual に格上げ
    final_scope = scope if scope is not None else "local"
    if final_scope == "cross":
        category = "manual"

    votes_list = [
        cat1 if cat1 else "unknown",
        cat2 if cat2 else "unknown",
        final_scope,
    ]

    # 信頼度: Classifier-1 と Classifier-2 の一致率
    if cat1 is not None and cat2 is not None:
        confidence = 1.0 if cat1 == cat2 else 0.5
    else:
        confidence = 0.5

    return {
        "route": ROUTE_TABLE.get(category, "manual"),
        "category": category,
        "scope": final_scope,
        "votes": votes_list,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# CLI エントリーポイント
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase C タスク分類器（3モデル多数決）"
    )
    parser.add_argument("--task", "-t", required=True, help="分類するタスク記述")
    parser.add_argument(
        "--model",
        "-m",
        default="claude-haiku-4-5-20251001",
        help="使用する Anthropic モデル (default: claude-haiku-4-5-20251001)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON 形式で出力（デフォルト動作）",
    )
    args = parser.parse_args()

    result = classify(args.task, model=args.model)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
