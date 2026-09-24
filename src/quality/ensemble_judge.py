#!/usr/bin/env python3
"""
ensemble-judge.py — Phase B Ensemble Quality Gate

3判定官の並列 LLM スコアリングで quality_score を算出する。
平均が 70 未満なら recommendation="block"、標準偏差が 20 超なら "collect_more" を返す。
API key が無い・判定官のどれかが失敗した (例外 / タイムアウト / 数値を返さない) 時は
スコアを作らず recommendation="unavailable" を返し、CLI は exit 2 で終わる (fail-closed)。

Usage:
  python3 src/quality/ensemble-judge.py \
    --task "JWT認証をセッションベースに移行" \
    --context "$(cat /tmp/context.txt)" \
    --model claude-haiku-4-5-20251001
"""

import argparse
import json
import math
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

JUDGE_PROMPTS = [
    '以下のコンテキストでタスク「{task}」を完了できますか？0-100で答えてください。数値のみ回答。',
    '以下のコンテキストに矛盾・重複・欠落はありますか？品質を0-100で評価してください。数値のみ回答。',
    '以下のコンテキストはAIエージェントが具体的に行動するのに十分な情報を含んでいますか？0-100で答えてください。数値のみ回答。',
]

PASS_THRESHOLD = 70.0
STDDEV_THRESHOLD = 20.0
TIMEOUT_SECONDS = 10
EXIT_UNAVAILABLE = 2
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def _stddev(scores: list[float]) -> float:
    n = len(scores)
    if n == 0:
        return 0.0
    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / n
    return math.sqrt(variance)


class JudgeError(Exception):
    """判定官がスコアを返せなかった (API エラー / タイムアウト / 数値なし)。"""


def _call_judge(prompt: str, context: str, model: str, api_key: str) -> float:
    """Anthropic API を呼び出し、0-100 のスコアを返す。返せない時は JudgeError。"""
    import anthropic  # type: ignore

    client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SECONDS, max_retries=1)
    message = client.messages.create(
        model=model,
        max_tokens=16,
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\n---\n{context}",
            }
        ],
    )
    raw = message.content[0].text.strip() if message.content else ""
    match = re.search(r"\d+(?:[.,]\d+)?", raw)
    if not match:
        raise JudgeError(f"数値を含まない応答: {raw[:40]!r}")
    score = float(match.group(0).replace(",", "."))
    return max(0.0, min(100.0, score))


def _unavailable(error: str, scores: list, failed: list[int]) -> dict:
    return {
        "ensemble_score": None,
        "scores": scores,
        "stddev": None,
        "consensus": False,
        "recommendation": "unavailable",
        "error": error,
        "failed_judges": failed,
    }


def judge_ensemble(
    task: str,
    context: str,
    model: str = DEFAULT_MODEL,
) -> dict:
    """
    3判定官を並列実行して ensemble スコアを返す。

    Returns:
        {
            "ensemble_score": float | None,
            "scores": list[float | None],
            "stddev": float | None,
            "consensus": bool,
            "recommendation": "proceed" | "collect_more" | "block" | "unavailable",
            # unavailable の時だけ
            "error": str,
            "failed_judges": list[int],  # 1 始まりの判定官番号
        }

    判定官が 1 つでも失敗したら unavailable。代わりのスコアで埋めて通すことはしない。
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return _unavailable("ANTHROPIC_API_KEY が未設定", [None] * len(JUDGE_PROMPTS), [])

    prompts = [p.format(task=task) for p in JUDGE_PROMPTS]

    results: dict[int, float] = {}
    errors: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=len(prompts)) as executor:
        futures = {
            executor.submit(_call_judge, prompt, context, model, api_key): i
            for i, prompt in enumerate(prompts)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception as exc:  # noqa: BLE001  API エラー・タイムアウトを判定官の失敗として記録
                errors[idx] = f"{type(exc).__name__}: {exc}"

    scores = [results.get(i) for i in range(len(prompts))]
    if errors:
        detail = "; ".join(f"judge {i + 1}: {errors[i]}" for i in sorted(errors))
        return _unavailable(f"判定官が失敗: {detail}", scores, [i + 1 for i in sorted(errors)])

    stddev = _stddev(scores)
    mean = sum(scores) / len(scores)
    ensemble_score = round(mean, 1)
    consensus = stddev <= STDDEV_THRESHOLD
    # 丸める前の平均で判定する ([69.9, 70, 70] は 70.0 に丸まるが 70 未満)
    if mean < PASS_THRESHOLD:
        recommendation = "block"
    elif not consensus:
        recommendation = "collect_more"
    else:
        recommendation = "proceed"

    return {
        "ensemble_score": ensemble_score,
        "scores": scores,
        "stddev": round(stddev, 1),
        "consensus": consensus,
        "recommendation": recommendation,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase B Ensemble Quality Gate: 3判定官の並列 LLM スコアリング"
    )
    parser.add_argument("--task", required=True, help="評価対象のタスク説明")
    parser.add_argument("--context", required=True, help="収集済みコンテキスト文字列")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"使用する Anthropic モデル (default: {DEFAULT_MODEL})",
    )
    args = parser.parse_args()

    result = judge_ensemble(task=args.task, context=args.context, model=args.model)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["recommendation"] == "unavailable":
        print(f"ensemble-judge: 判定できないのでゲートを止める ({result['error']})", file=sys.stderr)
        sys.exit(EXIT_UNAVAILABLE)


if __name__ == "__main__":
    main()
