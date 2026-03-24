#!/usr/bin/env python3
"""
test_ensemble_judge.py — ensemble-judge のユニットテスト（モック API 使用）
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# src/quality を Python パスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from quality.ensemble_judge import judge_ensemble, _stddev, DUMMY_SCORE, STDDEV_THRESHOLD  # noqa: E402


class TestStddev(unittest.TestCase):
    def test_all_same(self):
        self.assertAlmostEqual(_stddev([70, 70, 70]), 0.0)

    def test_known_values(self):
        # [0, 50, 100] → mean=50, variance=((−50)^2+(0)^2+(50)^2)/3=1666.7, stddev≈40.8
        result = _stddev([0.0, 50.0, 100.0])
        self.assertGreater(result, 40.0)

    def test_empty(self):
        self.assertEqual(_stddev([]), 0.0)


class TestFallbackWithoutApiKey(unittest.TestCase):
    def test_returns_dummy_score(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = judge_ensemble(task="テスト", context="コンテキスト")
        self.assertEqual(result["ensemble_score"], float(DUMMY_SCORE))
        self.assertEqual(result["scores"], [float(DUMMY_SCORE)] * 3)
        self.assertTrue(result["consensus"])
        self.assertEqual(result["recommendation"], "proceed")

    def test_json_serialisable(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = judge_ensemble(task="テスト", context="コンテキスト")
        serialised = json.dumps(result)
        parsed = json.loads(serialised)
        self.assertIn("ensemble_score", parsed)


class TestEnsembleWithMockApi(unittest.TestCase):
    def _make_message(self, score: int) -> MagicMock:
        msg = MagicMock()
        msg.content = [MagicMock(text=str(score))]
        return msg

    def test_consensus_when_stddev_low(self):
        """3スコアの標準偏差が20以下 → consensus=True, recommendation=proceed"""
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        try:
            with patch("quality.ensemble_judge._call_judge") as mock_judge:
                mock_judge.side_effect = [78.0, 75.0, 80.0]
                result = judge_ensemble(task="テスト", context="コンテキスト")
        finally:
            del os.environ["ANTHROPIC_API_KEY"]

        self.assertAlmostEqual(result["ensemble_score"], round((78 + 75 + 80) / 3, 1))
        self.assertLessEqual(result["stddev"], STDDEV_THRESHOLD)
        self.assertTrue(result["consensus"])
        self.assertEqual(result["recommendation"], "proceed")

    def test_collect_more_when_stddev_high(self):
        """3スコアの標準偏差が20超 → consensus=False, recommendation=collect_more"""
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        try:
            with patch("quality.ensemble_judge._call_judge") as mock_judge:
                # [10, 60, 95] → stddev ≈ 35 > 20
                mock_judge.side_effect = [10.0, 60.0, 95.0]
                result = judge_ensemble(task="テスト", context="コンテキスト")
        finally:
            del os.environ["ANTHROPIC_API_KEY"]

        self.assertGreater(result["stddev"], STDDEV_THRESHOLD)
        self.assertFalse(result["consensus"])
        self.assertEqual(result["recommendation"], "collect_more")

    def test_scores_list_has_three_elements(self):
        """scores リストは必ず 3 要素"""
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        try:
            with patch("quality.ensemble_judge._call_judge") as mock_judge:
                mock_judge.side_effect = [80.0, 70.0, 60.0]
                result = judge_ensemble(task="テスト", context="コンテキスト")
        finally:
            del os.environ["ANTHROPIC_API_KEY"]

        self.assertEqual(len(result["scores"]), 3)

    def test_judge_exception_uses_dummy_score(self):
        """判定官が例外を送出した場合はダミースコアで代替"""
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        try:
            with patch("quality.ensemble_judge._call_judge") as mock_judge:
                mock_judge.side_effect = [80.0, RuntimeError("API error"), 90.0]
                result = judge_ensemble(task="テスト", context="コンテキスト")
        finally:
            del os.environ["ANTHROPIC_API_KEY"]

        self.assertEqual(len(result["scores"]), 3)
        self.assertIn(float(DUMMY_SCORE), result["scores"])


if __name__ == "__main__":
    unittest.main()
