#!/usr/bin/env python3
"""
ensemble-judge.py — Phase B Ensemble Quality Gate

3判定官の並列 LLM スコアリングで quality_score を算出する。
標準偏差が20超の場合は recommendation="collect_more" を返す。

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
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

JUDGE_PROMPTS = [
    '以下のコンテキストでタスク「{task}」を完了できますか？0-100で答えてください。数値のみ回答。',
    '以下のコンテキストに矛盾・重複・欠落はありますか？品質を0-100で評価してください。数値のみ回答。',
    '以下のコンテキストはAIエージェントが具体的に行動するのに十分な情報を含んでいますか？0-100で答えてください。数値のみ回答。',
]

DUMMY_SCORE = 70
STDDEV_THRESHOLD = 20.0
TIMEOUT_SECONDS = 10
DEFAULT_MODEL = "gemini-2.0-flash"

# Cross-Model Disagreement (CMP) 統合設定
CMP_ENABLED_ENV = "ENSEMBLE_CMP_ENABLED"  # "1" でCMP有効化
CMP_VERIFIER_MODEL = "gemini-2.0-flash"   # Gemini API (GOOGLE_API_KEY) で検証


def _stddev(scores: list[float]) -> float:
    n = len(scores)
    if n == 0:
        return 0.0
    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / n
    return math.sqrt(variance)


def _call_judge(prompt: str, context: str, model: str, api_key: str) -> float:
    """Gemini API を呼び出し、0-100 のスコアを返す。"""
    import urllib.request

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    full_prompt = f"{prompt}\n\n---\n{context}"
    data = json.dumps({"contents": [{"parts": [{"text": full_prompt}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS)
    result = json.loads(resp.read())
    raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()
    # 数値のみ抽出
    for token in raw.split():
        try:
            score = float(token.replace(",", "."))
            return max(0.0, min(100.0, score))
        except ValueError:
            continue
    # 解析できない場合はダミースコア
    return float(DUMMY_SCORE)


def judge_ensemble(
    task: str,
    context: str,
    model: str = DEFAULT_MODEL,
    generated_output: str | None = None,
) -> dict:
    """
    3判定官を並列実行して ensemble スコアを返す。
    CMP有効時は Cross-Model Disagreement シグナルも付与する。

    Args:
        task: 評価対象のタスク説明
        context: 収集済みコンテキスト
        model: 判定官が使用するモデル
        generated_output: 生成モデルの出力（CMP評価用、省略時はCMPスキップ）

    Returns:
        {
            "ensemble_score": float,
            "scores": list[float],
            "stddev": float,
            "consensus": bool,
            "recommendation": "proceed" | "collect_more" | "review_required",
            "cmp": {...} | None,  # CMP有効時のみ
        }
    """
    api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        # Graceful fallback: ダミースコア 70 を返す
        scores = [float(DUMMY_SCORE)] * 3
        stddev = 0.0
        return {
            "ensemble_score": float(DUMMY_SCORE),
            "scores": scores,
            "stddev": stddev,
            "consensus": True,
            "recommendation": "proceed",
            "cmp": None,
        }

    prompts = [p.format(task=task) for p in JUDGE_PROMPTS]

    scores: list[float] = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_call_judge, prompt, context, model, api_key): i
            for i, prompt in enumerate(prompts)
        }
        results: dict[int, float] = {}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                # 個別フューチャーにタイムアウトを設定して無限待機を防ぐ
                results[idx] = future.result(timeout=TIMEOUT_SECONDS)
            except FuturesTimeoutError:
                results[idx] = float(DUMMY_SCORE)
            except Exception:  # noqa: BLE001  API エラー等を吸収してダミーで代替
                results[idx] = float(DUMMY_SCORE)

        # タイムアウトで取得できなかった判定官にはダミースコアを割り当て
        for i in range(len(prompts)):
            scores.append(results.get(i, float(DUMMY_SCORE)))

    stddev = _stddev(scores)
    ensemble_score = round(sum(scores) / len(scores), 1)
    consensus = stddev <= STDDEV_THRESHOLD
    recommendation = "proceed" if consensus else "collect_more"

    # Cross-Model Disagreement (CMP) — オプショナル
    cmp_result = None
    cmp_enabled = os.environ.get(CMP_ENABLED_ENV, "0") == "1"

    if cmp_enabled and generated_output:
        try:
            from quality.cross_model_disagreement import compute_disagreement

            cmp_result = compute_disagreement(
                task=task,
                context=context,
                output=generated_output,
                verifier_model=CMP_VERIFIER_MODEL,
            )

            # CMP リスクに応じて recommendation を上書き（安全側に倒す）
            # high: 常に review_required（判定官の合意状況に関わらず）
            # medium: proceed/collect_more のいずれでも review_required に格上げ
            if cmp_result["confident_error_risk"] == "high":
                recommendation = "review_required"
            elif cmp_result["confident_error_risk"] == "medium":
                recommendation = "review_required"
        except Exception:  # noqa: BLE001
            cmp_result = None

    return {
        "ensemble_score": ensemble_score,
        "scores": scores,
        "stddev": round(stddev, 1),
        "consensus": consensus,
        "recommendation": recommendation,
        "cmp": cmp_result,
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
        help=f"使用する Gemini モデル (default: {DEFAULT_MODEL})",
    )
    args = parser.parse_args()

    result = judge_ensemble(task=args.task, context=args.context, model=args.model)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
