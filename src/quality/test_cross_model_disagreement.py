#!/usr/bin/env python3
"""
test_cross_model_disagreement.py — CMP/CME のユニットテスト（モック API 使用）
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from quality.cross_model_disagreement import (  # noqa: E402
    compute_cmp,
    compute_cme,
    compute_disagreement,
    CMP_WARNING_THRESHOLD,
    CME_WARNING_THRESHOLD,
    _extract_score,
)


class TestExtractScore(unittest.TestCase):
    def test_simple_number(self):
        self.assertEqual(_extract_score("75"), 75.0)

    def test_number_with_text(self):
        self.assertEqual(_extract_score("スコアは 82 です"), 82.0)

    def test_decimal(self):
        self.assertAlmostEqual(_extract_score("65.5"), 65.5)

    def test_out_of_range_high(self):
        # 200 is out of range, should skip to find valid score
        self.assertEqual(_extract_score("200"), 50.0)

    def test_no_number(self):
        self.assertEqual(_extract_score("回答不能"), 50.0)


class TestCMPWithoutApiKey(unittest.TestCase):
    def test_returns_zero_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_API_KEY", None)
            result = compute_cmp(
                task="テスト", context="コンテキスト", output="出力"
            )
        self.assertEqual(result["cmp_score"], 0.0)
        self.assertFalse(result["warning"])


class TestCMEWithoutApiKey(unittest.TestCase):
    def test_returns_zero_without_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_API_KEY", None)
            result = compute_cme(task="テスト", context="コンテキスト")
        self.assertEqual(result["cme_score"], 0.0)
        self.assertFalse(result["warning"])


class TestCMPWithMockApi(unittest.TestCase):
    def test_low_surprise(self):
        """検証モデルが驚かない → low CMP"""
        with patch("quality.cross_model_disagreement._call_api") as mock_api:
            mock_api.return_value = "15\n出力はコンテキストと整合している"
            result = compute_cmp(
                task="テスト", context="コンテキスト", output="正しい出力",
                api_key="test-key",
            )
        self.assertLess(result["cmp_score"], CMP_WARNING_THRESHOLD)
        self.assertFalse(result["warning"])

    def test_high_surprise(self):
        """検証モデルが驚いている → high CMP"""
        with patch("quality.cross_model_disagreement._call_api") as mock_api:
            mock_api.return_value = "85\nコンテキストと矛盾する記述がある"
            result = compute_cmp(
                task="テスト", context="コンテキスト", output="矛盾した出力",
                api_key="test-key",
            )
        self.assertGreaterEqual(result["cmp_score"], CMP_WARNING_THRESHOLD)
        self.assertTrue(result["warning"])

    def test_api_error_returns_zero(self):
        """API エラー時はスコア 0 (warning なし)"""
        with patch("quality.cross_model_disagreement._call_api") as mock_api:
            mock_api.side_effect = RuntimeError("API error")
            result = compute_cmp(
                task="テスト", context="コンテキスト", output="出力",
                api_key="test-key",
            )
        self.assertEqual(result["cmp_score"], 0.0)
        self.assertFalse(result["warning"])


class TestDisagreementIntegrated(unittest.TestCase):
    def test_confident_error_high_cmp_low_cme(self):
        """CMP高 + CME低 → confident_error_risk = high"""
        with patch("quality.cross_model_disagreement._call_api") as mock_api:
            # CMP call returns high surprise, CME call returns low uncertainty
            mock_api.side_effect = [
                "80\n矛盾あり",   # CMP: high
                "20\nタスクは明確",  # CME: low
            ]
            os.environ["GOOGLE_API_KEY"] = "test-key"
            try:
                result = compute_disagreement(
                    task="テスト", context="コンテキスト", output="出力"
                )
            finally:
                del os.environ["GOOGLE_API_KEY"]

        self.assertEqual(result["confident_error_risk"], "high")
        self.assertTrue(result["combined_warning"])

    def test_ambiguous_task_high_cmp_high_cme(self):
        """CMP高 + CME高 → confident_error_risk = medium"""
        with patch("quality.cross_model_disagreement._call_api") as mock_api:
            mock_api.side_effect = [
                "75\n不自然な部分あり",  # CMP: high
                "70\n情報不足",          # CME: high
            ]
            os.environ["GOOGLE_API_KEY"] = "test-key"
            try:
                result = compute_disagreement(
                    task="テスト", context="コンテキスト", output="出力"
                )
            finally:
                del os.environ["GOOGLE_API_KEY"]

        self.assertEqual(result["confident_error_risk"], "medium")

    def test_low_risk_when_both_low(self):
        """CMP低 + CME低 → confident_error_risk = low"""
        with patch("quality.cross_model_disagreement._call_api") as mock_api:
            mock_api.side_effect = [
                "15\n問題なし",  # CMP: low
                "10\n明確",     # CME: low
            ]
            os.environ["GOOGLE_API_KEY"] = "test-key"
            try:
                result = compute_disagreement(
                    task="テスト", context="コンテキスト", output="出力"
                )
            finally:
                del os.environ["GOOGLE_API_KEY"]

        self.assertEqual(result["confident_error_risk"], "low")
        self.assertFalse(result["combined_warning"])

    def test_no_api_key(self):
        """API key なし → low risk, warning なし"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_API_KEY", None)
            result = compute_disagreement(
                task="テスト", context="コンテキスト", output="出力"
            )
        self.assertEqual(result["confident_error_risk"], "low")
        self.assertFalse(result["combined_warning"])


if __name__ == "__main__":
    unittest.main()
