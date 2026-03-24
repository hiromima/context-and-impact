#!/usr/bin/env python3
"""
temporal-score.py のユニットテスト
"""

import importlib.util
import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

# src/cli をパスに追加（hyphen 付きモジュール名を importlib で読み込む）
_module_path = Path(__file__).parent / "temporal-score.py"
_spec = importlib.util.spec_from_file_location("temporal_score", _module_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

DEFAULT_LAMBDA = _mod.DEFAULT_LAMBDA
days_ago = _mod.days_ago
parse_date = _mod.parse_date
parse_worklog = _mod.parse_worklog
query_entries = _mod.query_entries
score_entries = _mod.score_entries
tag_entry = _mod.tag_entry
temporal_score = _mod.temporal_score


class TestTemporalScore(unittest.TestCase):
    """時間減衰スコア計算のテスト"""

    def test_score_at_day_zero(self):
        """day=0 のスコアは base_score に等しい"""
        score = temporal_score(0.0)
        self.assertAlmostEqual(score, 1.0, places=6)

    def test_score_decay_7_days(self):
        """7日後のスコアは当日比50%以下になる (lambda=0.1 → exp(-0.7) ≈ 0.4966)"""
        score_day0 = temporal_score(0.0)
        score_day7 = temporal_score(7.0)
        self.assertLess(score_day7, score_day0 * 0.5)

    def test_score_monotonically_decreasing(self):
        """スコアは経過日数が増えるにつれて単調減少する"""
        scores = [temporal_score(float(d)) for d in range(0, 30)]
        for i in range(len(scores) - 1):
            self.assertGreater(scores[i], scores[i + 1])

    def test_parse_date_yyyymmdd_hhmm(self):
        """YYYYMMDD-HHMM 形式の日付をパースできる"""
        dt = parse_date("20260324-1402")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 24)
        self.assertEqual(dt.hour, 14)
        self.assertEqual(dt.minute, 2)

    def test_parse_date_iso(self):
        """ISO 8601 形式の日付をパースできる"""
        dt = parse_date("2026-03-24T03:29:55Z")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 3)
        self.assertEqual(dt.day, 24)

    def test_parse_date_invalid(self):
        """無効な日付文字列は None を返す"""
        self.assertIsNone(parse_date("not-a-date"))

    def test_days_ago_past(self):
        """過去の日時は正の経過日数を返す"""
        now = datetime(2026, 3, 24, 0, 0, 0, tzinfo=timezone.utc)
        past = datetime(2026, 3, 17, 0, 0, 0, tzinfo=timezone.utc)
        self.assertAlmostEqual(days_ago(past, now), 7.0, places=2)

    def test_days_ago_future(self):
        """未来の日時は 0 を返す"""
        now = datetime(2026, 3, 24, 0, 0, 0, tzinfo=timezone.utc)
        future = datetime(2026, 3, 31, 0, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(days_ago(future, now), 0.0)


class TestParseWorklog(unittest.TestCase):
    """worklog.md パースのテスト"""

    def _make_worklog(self, content: str) -> Path:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp.flush()
        return Path(tmp.name)

    def test_parse_yyyymmdd_entry(self):
        """YYYYMMDD-HHMM 形式のエントリをパースできる"""
        wl = self._make_worklog(
            "## 20260324-1402 — JWT移行 [type:decision] [decay:0.1] [refs:#123]\n"
            "- detail line\n"
        )
        entries = parse_worklog(wl)
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["entry"], "20260324-1402")
        self.assertIn("JWT移行", e["description"])
        self.assertEqual(e["tags"].get("type"), "decision")
        self.assertEqual(e["tags"].get("decay"), "0.1")

    def test_parse_iso_entry(self):
        """ISO 8601 形式のエントリをパースできる"""
        wl = self._make_worklog(
            "\n## 2026-03-24T03:29:55Z — 認証 (kotowari)\n"
            "- **result**: success\n"
        )
        entries = parse_worklog(wl)
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertIn("認証", e["description"])

    def test_parse_multiple_entries(self):
        """複数エントリを正しくパースできる"""
        wl = self._make_worklog(
            "## 20260317-1000 — 古いタスク\n"
            "- old content\n"
            "## 20260324-1402 — 新しいタスク\n"
            "- new content\n"
        )
        entries = parse_worklog(wl)
        self.assertEqual(len(entries), 2)

    def test_score_entries_have_required_keys(self):
        """score_entries の結果が必要なキーを持つ"""
        wl = self._make_worklog(
            "## 20260324-1402 — テスト\n"
            "- test\n"
        )
        entries = parse_worklog(wl)
        scored = score_entries(entries)
        required = {"entry", "description", "content", "days_ago", "temporal_score", "tags"}
        for e in scored:
            self.assertTrue(required.issubset(set(e.keys())))


class TestQueryEntries(unittest.TestCase):
    """クエリフィルタのテスト"""

    _ENTRIES = [
        {"entry": "20260324-1000", "description": "JWT authentication", "content": "JWT auth content", "days_ago": 0, "temporal_score": 1.0, "tags": {}},
        {"entry": "20260317-1000", "description": "Database migration", "content": "DB migration content", "days_ago": 7, "temporal_score": 0.496, "tags": {}},
    ]

    def test_query_matches(self):
        """クエリにマッチするエントリのみ返す"""
        result = query_entries(self._ENTRIES, "JWT")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["entry"], "20260324-1000")

    def test_query_case_insensitive(self):
        """クエリは大文字小文字を区別しない"""
        result = query_entries(self._ENTRIES, "jWt")
        self.assertEqual(len(result), 1)

    def test_empty_query_returns_all(self):
        """空クエリは全エントリを返す"""
        result = query_entries(self._ENTRIES, "")
        self.assertEqual(len(result), len(self._ENTRIES))


class TestTagEntry(unittest.TestCase):
    """--tag オプションのテスト"""

    def test_tag_adds_type_and_decay(self):
        """タグのないエントリに [type:task] [decay:0.1] が付与される"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            wl_path = Path(f.name)

        entry_line = "## 20260324-1402 — タスク説明"
        result = tag_entry(wl_path, entry_line)

        self.assertIn("[type:task]", result)
        self.assertIn("[decay:0.1]", result)

        # ファイルに書き込まれていることを確認
        content = wl_path.read_text(encoding="utf-8")
        self.assertIn("[type:task]", content)
        self.assertIn("[decay:0.1]", content)

    def test_tag_preserves_existing_tags(self):
        """既存タグがある場合は重複付与しない"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            wl_path = Path(f.name)

        entry_line = "## 20260324-1402 — 決定事項 [type:decision] [decay:0.2]"
        result = tag_entry(wl_path, entry_line)

        # type:decision が保持され、type:task が重複追加されない
        self.assertNotIn("[type:task]", result)
        self.assertIn("[type:decision]", result)
        self.assertIn("[decay:0.2]", result)
        self.assertEqual(result.count("[decay:"), 1)


class TestDecayFormulaSpec(unittest.TestCase):
    """仕様要件の直接検証"""

    def test_lambda_0_1_gives_50_percent_at_7_days(self):
        """lambda=0.1 のとき 7日で約 50% 減衰 (exp(-0.7) ≈ 0.4966)"""
        ratio = temporal_score(7.0, lam=0.1) / temporal_score(0.0, lam=0.1)
        self.assertLess(ratio, 0.5)
        # exp(-0.7) を確認
        self.assertAlmostEqual(ratio, math.exp(-0.7), places=5)

    def test_custom_lambda(self):
        """カスタム lambda でのスコア計算が正しい"""
        lam = 0.2
        score = temporal_score(5.0, lam=lam)
        expected = math.exp(-lam * 5.0)
        self.assertAlmostEqual(score, expected, places=6)

    def test_score_entries_uses_per_entry_decay_tag(self):
        """エントリの [decay:X] タグが優先される"""
        now = datetime(2026, 3, 24, 0, 0, 0, tzinfo=timezone.utc)
        entries = [
            {
                "entry": "20260317-1000",
                "description": "test",
                "content": "test",
                "tags": {"decay": "0.5"},
                "date": datetime(2026, 3, 17, 0, 0, 0, tzinfo=timezone.utc),
            }
        ]
        scored = score_entries(entries, now=now)
        expected = math.exp(-0.5 * 7.0)
        self.assertAlmostEqual(scored[0]["temporal_score"], expected, places=4)


if __name__ == "__main__":
    unittest.main()
