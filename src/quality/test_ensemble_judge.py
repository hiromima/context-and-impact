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

from quality import ensemble_judge  # noqa: E402
from quality.ensemble_judge import judge_ensemble, _stddev, STDDEV_THRESHOLD, EXIT_UNAVAILABLE  # noqa: E402


class TestStddev(unittest.TestCase):
    def test_all_same(self):
        self.assertAlmostEqual(_stddev([70, 70, 70]), 0.0)

    def test_known_values(self):
        # [0, 50, 100] → mean=50, variance=((−50)^2+(0)^2+(50)^2)/3=1666.7, stddev≈40.8
        result = _stddev([0.0, 50.0, 100.0])
        self.assertGreater(result, 40.0)

    def test_empty(self):
        self.assertEqual(_stddev([]), 0.0)


class TestWithoutApiKey(unittest.TestCase):
    """API key が無い時は、代わりのスコアで通さずに unavailable を返す。"""

    def test_returns_unavailable(self):
        with patch.dict(os.environ, {}, clear=True):
            result = judge_ensemble(task="テスト", context="コンテキスト")
        self.assertEqual(result["recommendation"], "unavailable")
        self.assertIsNone(result["ensemble_score"])
        self.assertEqual(result["scores"], [None, None, None])
        self.assertFalse(result["consensus"])
        self.assertIn("ANTHROPIC_API_KEY", result["error"])

    def test_json_serialisable(self):
        with patch.dict(os.environ, {}, clear=True):
            result = judge_ensemble(task="テスト", context="コンテキスト")
        parsed = json.loads(json.dumps(result))
        self.assertEqual(parsed["recommendation"], "unavailable")

    def test_cli_exits_nonzero(self):
        argv = ["ensemble_judge.py", "--task", "テスト", "--context", "コンテキスト"]
        with patch.dict(os.environ, {}, clear=True), patch.object(sys, "argv", argv), \
                patch("sys.stdout"), patch("sys.stderr"):
            with self.assertRaises(SystemExit) as cm:
                ensemble_judge.main()
        self.assertEqual(cm.exception.code, EXIT_UNAVAILABLE)


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
        """平均 70 以上で標準偏差が20超 → consensus=False, recommendation=collect_more"""
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        try:
            with patch("quality.ensemble_judge._call_judge") as mock_judge:
                # [45, 80, 100] → mean 75, stddev ≈ 22.7 > 20
                mock_judge.side_effect = [45.0, 80.0, 100.0]
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

    def _run(self, side_effect):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}), \
                patch("quality.ensemble_judge._call_judge") as mock_judge:
            mock_judge.side_effect = side_effect
            return judge_ensemble(task="テスト", context="コンテキスト")

    def test_block_when_score_below_threshold(self):
        """平均が 70 未満 → block (標準偏差が小さくても通さない)"""
        result = self._run([55.0, 60.0, 58.0])
        self.assertLess(result["ensemble_score"], 70)
        self.assertEqual(result["recommendation"], "block")

    def test_block_uses_unrounded_mean(self):
        """[69.9, 70, 70] は表示上 70.0 だが、平均は 70 未満なので block"""
        result = self._run([69.9, 70.0, 70.0])
        self.assertEqual(result["ensemble_score"], 70.0)
        self.assertEqual(result["recommendation"], "block")

    def test_block_wins_over_collect_more(self):
        """平均 70 未満かつ割れている → block"""
        result = self._run([10.0, 40.0, 95.0])
        self.assertEqual(result["recommendation"], "block")

    def test_one_judge_exception_is_unavailable(self):
        """判定官が 1 つでも例外を出したら、代わりのスコアで埋めずに unavailable"""
        result = self._run([80.0, RuntimeError("API error"), 90.0])
        self.assertEqual(result["recommendation"], "unavailable")
        self.assertIsNone(result["ensemble_score"])
        self.assertEqual(result["scores"].count(None), 1)
        self.assertEqual(len(result["failed_judges"]), 1)
        self.assertIn("API error", result["error"])

    def test_all_judges_fail_is_unavailable(self):
        """全判定官がタイムアウト → unavailable (proceed にしない)"""
        result = self._run([TimeoutError("t1"), TimeoutError("t2"), TimeoutError("t3")])
        self.assertEqual(result["recommendation"], "unavailable")
        self.assertEqual(result["failed_judges"], [1, 2, 3])
        self.assertEqual(result["scores"], [None, None, None])


class TestCallJudgeParsing(unittest.TestCase):
    def _call(self, text):
        fake = MagicMock()
        fake.Anthropic.return_value.messages.create.return_value.content = [MagicMock(text=text)]
        with patch.dict(sys.modules, {"anthropic": fake}):
            return ensemble_judge._call_judge("p", "c", "m", "k")

    def test_number_with_trailing_punctuation(self):
        self.assertEqual(self._call("85。"), 85.0)

    def test_clamped(self):
        self.assertEqual(self._call("150"), 100.0)

    def test_no_number_raises(self):
        with self.assertRaises(ensemble_judge.JudgeError):
            self._call("判断できません")

if __name__ == "__main__":
    unittest.main()
