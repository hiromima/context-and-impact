#!/usr/bin/env python3
"""
cross_model_disagreement.py — Cross-Model Disagreement Signal

arXiv: Cross-Model Disagreement as a Label-Free Correctness Signal (2603.25450v1)

検証モデルが生成モデルの出力を評価し、モデル間の不一致度を
ラベルなし誤り検出シグナルとして算出する。

2つのメトリクス:
  - CMP (Cross-Model Perplexity): 検証モデルが生成出力に「どの程度驚くか」
  - CME (Cross-Model Entropy): 検証モデル自身の不確実性

Usage:
  python3 cross_model_disagreement.py \
    --task "タスク説明" \
    --context "コンテキスト" \
    --output "生成モデルの出力" \
    --generator-model claude-haiku-4-5-20251001 \
    --verifier-model claude-sonnet-4-6
"""

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


# CMP閾値: この値を超えると confident error の疑い
CMP_WARNING_THRESHOLD = 60.0
# CME閾値: 検証モデル自身の不確実性が高い
CME_WARNING_THRESHOLD = 50.0

DEFAULT_GENERATOR = "gemini-2.0-flash"
DEFAULT_VERIFIER = "gemini-2.0-flash"
TIMEOUT_SECONDS = 15


def _call_api(messages: list[dict], model: str, api_key: str, max_tokens: int = 64) -> str:
    """Gemini API を呼び出してテキストを返す。GOOGLE_API_KEY を使用。"""
    import json as _json
    import urllib.request

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    # messages[0]["content"] からプロンプトを取得
    prompt_text = messages[0]["content"] if messages else ""
    data = _json.dumps({"contents": [{"parts": [{"text": prompt_text}]}]}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS)
    result = _json.loads(resp.read())
    return result["candidates"][0]["content"]["parts"][0]["text"].strip()


def _extract_score(text: str) -> float:
    """テキストから 0-100 の数値を抽出する。"""
    for token in re.findall(r"\d+(?:\.\d+)?", text):
        score = float(token)
        if 0.0 <= score <= 100.0:
            return score
    return 50.0  # 抽出できない場合は中間値


def compute_cmp(
    task: str,
    context: str,
    output: str,
    verifier_model: str = DEFAULT_VERIFIER,
    api_key: str | None = None,
) -> dict:
    """
    Cross-Model Perplexity (CMP) を計算する。

    検証モデルに生成出力を見せ、「この出力はタスクとコンテキストに対して
    どの程度予想外（surprising）か」を 0-100 で評価させる。

    高スコア = 検証モデルが「驚いている」= モデル間の不一致が大きい

    Returns:
        {"cmp_score": float, "cmp_reasoning": str, "warning": bool}
    """
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {"cmp_score": 0.0, "cmp_reasoning": "API key not available (set GOOGLE_API_KEY)", "warning": False}

    prompt = (
        "あなたは品質検証官です。以下のタスクとコンテキストに対する出力を評価してください。\n\n"
        f"## タスク\n{task}\n\n"
        f"## コンテキスト\n{context[:2000]}\n\n"
        f"## 評価対象の出力\n{output[:2000]}\n\n"
        "## 評価基準\n"
        "この出力が「予想外」「不自然」「間違っている可能性がある」度合いを 0-100 で評価してください。\n"
        "- 0: 完全に予想通り、正確\n"
        "- 50: やや疑問がある\n"
        "- 100: 明らかに間違っている、または非常に予想外\n\n"
        "形式: まず1行で数値（0-100）、次に1行で理由を書いてください。"
    )

    try:
        raw = _call_api(
            messages=[{"role": "user", "content": prompt}],
            model=verifier_model,
            api_key=api_key,
            max_tokens=128,
        )
        score = _extract_score(raw)
        # 1行目がスコア、残りが理由
        lines = raw.split("\n", 1)
        reasoning = lines[1].strip() if len(lines) > 1 else ""
        return {
            "cmp_score": score,
            "cmp_reasoning": reasoning[:200],
            "warning": score >= CMP_WARNING_THRESHOLD,
        }
    except Exception as e:
        return {"cmp_score": 0.0, "cmp_reasoning": f"Error: {e}", "warning": False}


def compute_cme(
    task: str,
    context: str,
    verifier_model: str = DEFAULT_VERIFIER,
    api_key: str | None = None,
) -> dict:
    """
    Cross-Model Entropy (CME) を計算する。

    検証モデル自身に「このタスクとコンテキストに対して自分がどの程度
    不確実か」を評価させる。CMP の補完シグナル。

    高スコア = 検証モデル自身が不確実 = タスクが本質的に曖昧

    Returns:
        {"cme_score": float, "cme_reasoning": str, "warning": bool}
    """
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {"cme_score": 0.0, "cme_reasoning": "API key not available (set GOOGLE_API_KEY)", "warning": False}

    prompt = (
        "あなたは自己評価を行う品質検証官です。以下のタスクとコンテキストについて、\n"
        "あなた自身がどの程度確信を持って回答できるかを評価してください。\n\n"
        f"## タスク\n{task}\n\n"
        f"## コンテキスト\n{context[:2000]}\n\n"
        "## 評価基準\n"
        "このタスクに対するあなたの不確実性を 0-100 で評価してください。\n"
        "- 0: 完全に確信がある、明確なタスク\n"
        "- 50: 中程度の不確実性\n"
        "- 100: 非常に不確実、情報不足\n\n"
        "形式: まず1行で数値（0-100）、次に1行で理由を書いてください。"
    )

    try:
        raw = _call_api(
            messages=[{"role": "user", "content": prompt}],
            model=verifier_model,
            api_key=api_key,
            max_tokens=128,
        )
        score = _extract_score(raw)
        lines = raw.split("\n", 1)
        reasoning = lines[1].strip() if len(lines) > 1 else ""
        return {
            "cme_score": score,
            "cme_reasoning": reasoning[:200],
            "warning": score >= CME_WARNING_THRESHOLD,
        }
    except Exception as e:
        return {"cme_score": 0.0, "cme_reasoning": f"Error: {e}", "warning": False}


def compute_disagreement(
    task: str,
    context: str,
    output: str,
    verifier_model: str = DEFAULT_VERIFIER,
) -> dict:
    """
    CMP と CME を並列計算し、統合不一致シグナルを返す。

    Returns:
        {
            "cmp": {"cmp_score": float, "cmp_reasoning": str, "warning": bool},
            "cme": {"cme_score": float, "cme_reasoning": str, "warning": bool},
            "combined_warning": bool,
            "confident_error_risk": "low" | "medium" | "high"
        }
    """
    api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        cmp_result = {"cmp_score": 0.0, "cmp_reasoning": "No API key (set GOOGLE_API_KEY)", "warning": False}
        cme_result = {"cme_score": 0.0, "cme_reasoning": "No API key (set GOOGLE_API_KEY)", "warning": False}
    else:
        with ThreadPoolExecutor(max_workers=2) as executor:
            cmp_future = executor.submit(
                compute_cmp, task, context, output, verifier_model, api_key
            )
            cme_future = executor.submit(
                compute_cme, task, context, verifier_model, api_key
            )

            try:
                cmp_result = cmp_future.result(timeout=TIMEOUT_SECONDS)
            except Exception:
                cmp_result = {"cmp_score": 0.0, "cmp_reasoning": "Timeout", "warning": False}

            try:
                cme_result = cme_future.result(timeout=TIMEOUT_SECONDS)
            except Exception:
                cme_result = {"cme_score": 0.0, "cme_reasoning": "Timeout", "warning": False}

    # Confident error risk判定:
    # CMP高 + CME低 = 検証モデルが驚いているが、タスク自体は明確 → confident error
    # CMP高 + CME高 = タスクが曖昧で検証モデルも不確実 → ambiguous task
    # CMP低 = 一致している → low risk
    cmp_score = cmp_result["cmp_score"]
    cme_score = cme_result["cme_score"]

    if cmp_score >= CMP_WARNING_THRESHOLD and cme_score < CME_WARNING_THRESHOLD:
        risk = "high"  # confident error: モデルが確信を持って間違えている可能性
    elif cmp_score >= CMP_WARNING_THRESHOLD and cme_score >= CME_WARNING_THRESHOLD:
        risk = "medium"  # ambiguous: タスク自体が曖昧
    else:
        risk = "low"

    return {
        "cmp": cmp_result,
        "cme": cme_result,
        "combined_warning": cmp_result["warning"] or cme_result["warning"],
        "confident_error_risk": risk,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-Model Disagreement Signal (CMP/CME)"
    )
    parser.add_argument("--task", required=True, help="タスク説明")
    parser.add_argument("--context", required=True, help="コンテキスト")
    parser.add_argument("--output", required=True, help="生成モデルの出力")
    parser.add_argument(
        "--verifier-model",
        default=DEFAULT_VERIFIER,
        help=f"検証モデル (default: {DEFAULT_VERIFIER})",
    )
    args = parser.parse_args()

    result = compute_disagreement(
        task=args.task,
        context=args.context,
        output=args.output,
        verifier_model=args.verifier_model,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
