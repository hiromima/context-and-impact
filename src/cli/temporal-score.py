#!/usr/bin/env python3
"""
context-and-impact: Temporal Memory Scorer
worklog.md エントリに時間減衰スコアを付与し、古い記憶を自動的に低重みにする。

スコア計算式:
  score = base_score * exp(-lambda * days_ago)
  lambda = 0.1  # 7日で約50%減衰

Usage:
  # worklog.md を読んで時間スコア付きで JSON 出力
  python3 src/cli/temporal-score.py \\
    --worklog project_memory/worklog.md \\
    --query "JWT authentication" \\
    --limit 10

  # タグ付きエントリを追記
  python3 src/cli/temporal-score.py --tag \\
    --worklog project_memory/worklog.md \\
    --entry "## 20260324-1402 — タスク説明"
"""

import sys
import os
import re
import json
import math
import argparse
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LAMBDA = 0.1
DEFAULT_BASE_SCORE = 1.0

# エントリのヘッダ形式: ## YYYYMMDD-HHMM — 説明 [オプションタグ...]
# または: ## YYYY-MM-DDTHH:MM:SSZ — 説明
_HEADER_YYYYMMDD_RE = re.compile(
    r"^##\s+(\d{8}-\d{4})\s+(?:—|-{1,2})\s+(.*?)(\[.*\])?\s*$"
)
_HEADER_ISO_RE = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?)\s+(?:—|-{1,2})\s+(.*?)(\[.*\])?\s*$"
)
# タグ抽出: [key:value] 形式
_TAG_RE = re.compile(r"\[([a-zA-Z_]+):([^\]]+)\]")


def parse_date(date_str: str) -> datetime | None:
    """エントリヘッダから日時をパースして UTC datetime を返す"""
    # YYYYMMDD-HHMM 形式
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})", date_str)
    if m:
        y, mo, d, h, mi = (int(x) for x in m.groups())
        try:
            return datetime(y, mo, d, h, mi, tzinfo=timezone.utc)
        except ValueError:
            return None
    # ISO 8601 形式
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(date_str.rstrip("Z"), fmt.rstrip("Z"))
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def days_ago(dt: datetime, now: datetime | None = None) -> float:
    """dt から現在までの経過日数を返す（未来は 0 とする）"""
    if now is None:
        now = datetime.now(timezone.utc)
    delta = (now - dt).total_seconds() / 86400.0
    return max(0.0, delta)


def temporal_score(days: float, base: float = DEFAULT_BASE_SCORE, lam: float = DEFAULT_LAMBDA) -> float:
    """時間減衰スコアを計算する: score = base * exp(-lambda * days)"""
    return base * math.exp(-lam * days)


def _extract_tags(tag_str: str) -> dict:
    """'[key:value] [key2:value2]' 形式の文字列からタグ辞書を返す"""
    return {k: v for k, v in _TAG_RE.findall(tag_str or "")}


def parse_worklog(worklog_path: Path) -> list[dict]:
    """
    worklog.md を読み込み、エントリのリストを返す。

    各エントリは:
      {
        "entry": "YYYYMMDD-HHMM",
        "content": "ヘッダ以下の本文（ヘッダ行を含む）",
        "description": "説明文字列",
        "tags": {"type": "decision", "decay": "0.1", ...},
        "date": datetime,
      }
    """
    text = worklog_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    entries = []
    current: dict | None = None

    for line in lines:
        header_match = _HEADER_YYYYMMDD_RE.match(line) or _HEADER_ISO_RE.match(line)
        if header_match:
            if current is not None:
                entries.append(current)
            date_str, description, tag_block = header_match.groups()
            dt = parse_date(date_str)
            tags = _extract_tags(tag_block or "")
            current = {
                "entry": date_str,
                "description": description.strip(),
                "tags": tags,
                "date": dt,
                "content": line,
            }
        else:
            if current is not None:
                current["content"] += "\n" + line

    if current is not None:
        entries.append(current)

    return entries


def score_entries(entries: list[dict], now: datetime | None = None) -> list[dict]:
    """各エントリに days_ago と temporal_score を付与して返す"""
    if now is None:
        now = datetime.now(timezone.utc)
    result = []
    for entry in entries:
        dt = entry.get("date")
        if dt is None:
            d = 0.0
        else:
            d = days_ago(dt, now)
        lam = DEFAULT_LAMBDA
        try:
            lam = float(entry["tags"].get("decay", DEFAULT_LAMBDA))
        except (ValueError, TypeError):
            lam = DEFAULT_LAMBDA
        ts = temporal_score(d, lam=lam)
        result.append({
            "entry": entry["entry"],
            "description": entry["description"],
            "content": entry["content"],
            "days_ago": round(d, 4),
            "temporal_score": round(ts, 6),
            "tags": entry["tags"],
        })
    return result


def query_entries(entries: list[dict], query: str) -> list[dict]:
    """
    クエリ文字列でエントリをフィルタ（大文字小文字を無視した部分文字列マッチ）。
    クエリが空の場合は全エントリを返す。
    """
    if not query:
        return entries
    q = query.lower()
    return [e for e in entries if q in e.get("content", "").lower()
            or q in e.get("description", "").lower()]


def tag_entry(worklog_path: Path, entry_line: str) -> str:
    """
    エントリ行に [type:task] [decay:0.1] タグを付与して worklog.md に追記し、
    タグ付きの行を返す。
    エントリ行に既存のタグがある場合はそのまま保持する。
    """
    line = entry_line.strip()
    # 既に type タグが無ければ付与
    if "[type:" not in line:
        line += " [type:task]"
    # 既に decay タグが無ければ付与
    if "[decay:" not in line:
        line += f" [decay:{DEFAULT_LAMBDA}]"

    # ファイルに追記
    with worklog_path.open("a", encoding="utf-8") as f:
        f.write("\n" + line + "\n")

    return line


# ---------------------------------------------------------------------------
# CLI エントリーポイント
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Temporal Memory Scorer — worklog.md エントリに時間減衰スコアを付与する"
    )
    parser.add_argument("--worklog", required=True, help="worklog.md のパス")
    parser.add_argument("--query", "-q", default="", help="フィルタ用クエリ文字列")
    parser.add_argument("--limit", "-n", type=int, default=10, help="出力件数 (default: 10)")
    parser.add_argument(
        "--tag",
        action="store_true",
        help="--entry で指定した行にタグを付与して worklog.md に追記する",
    )
    parser.add_argument("--entry", help="--tag モード用のエントリ行")
    args = parser.parse_args()

    worklog_path = Path(args.worklog)

    if args.tag:
        if not args.entry:
            print("ERROR: --tag モードでは --entry が必要です", file=sys.stderr)
            sys.exit(1)
        if not worklog_path.exists():
            worklog_path.touch()
        tagged = tag_entry(worklog_path, args.entry)
        print(tagged)
        return

    if not worklog_path.exists():
        print(f"ERROR: worklog が見つかりません: {worklog_path}", file=sys.stderr)
        sys.exit(1)

    entries = parse_worklog(worklog_path)
    scored = score_entries(entries)
    scored.sort(key=lambda x: x["temporal_score"], reverse=True)
    filtered = query_entries(scored, args.query)
    output = filtered[: args.limit]

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
