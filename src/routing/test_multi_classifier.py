#!/usr/bin/env python3
"""
test_multi_classifier.py — multi-classifier のユニットテスト

API 未設定環境でキーワードフォールバックをテストする。
"""

import sys
import os
import unittest
from unittest.mock import patch

# リポジトリルートから実行できるようにパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.routing.multi_classifier import (
    keyword_fallback,
    classify,
    _normalize_category,
    _normalize_scope,
    _majority_vote,
)


class TestKeywordFallback(unittest.TestCase):
    """キーワードフォールバックのテスト"""

    def test_fix_japanese(self):
        """「修正」「バグ」タスクで route=cursor-agent になる"""
        result = keyword_fallback("datetime.utcnow()の非推奨警告を修正")
        self.assertEqual(result["route"], "cursor-agent")
        self.assertEqual(result["category"], "fix")
        self.assertTrue(result.get("fallback"))

    def test_fix_english(self):
        """fix タスクで route=cursor-agent になる"""
        result = keyword_fallback("fix login bug in auth module")
        self.assertEqual(result["route"], "cursor-agent")
        self.assertEqual(result["category"], "fix")

    def test_feat_japanese(self):
        """「追加」「新機能」タスクで route=copilot になる"""
        result = keyword_fallback("新しい認証機能を追加する")
        self.assertEqual(result["route"], "copilot")
        self.assertEqual(result["category"], "feat")

    def test_feat_english(self):
        """feat/add/implement タスクで route=copilot になる"""
        result = keyword_fallback("implement OAuth2 login")
        self.assertEqual(result["route"], "copilot")
        self.assertEqual(result["category"], "feat")

    def test_unknown_defaults_to_chore(self):
        """マッチしないタスクは chore → copilot"""
        result = keyword_fallback("update readme")
        self.assertEqual(result["route"], "copilot")

    def test_fallback_structure(self):
        """フォールバック結果が必須キーを持つ"""
        result = keyword_fallback("何か作業する")
        for key in ("route", "category", "scope", "votes", "confidence"):
            self.assertIn(key, result)


class TestNormalize(unittest.TestCase):
    """正規化関数のテスト"""

    def test_normalize_category_valid(self):
        self.assertEqual(_normalize_category("fix"), "fix")
        self.assertEqual(_normalize_category("FEAT"), "feat")
        self.assertEqual(_normalize_category("refactor"), "refactor")

    def test_normalize_category_alias(self):
        self.assertEqual(_normalize_category("improve"), "refactor")
        self.assertEqual(_normalize_category("other"), "chore")

    def test_normalize_category_none(self):
        self.assertIsNone(_normalize_category(None))
        self.assertIsNone(_normalize_category("unknown_value"))

    def test_normalize_scope_valid(self):
        self.assertEqual(_normalize_scope("local"), "local")
        self.assertEqual(_normalize_scope("module"), "module")
        self.assertEqual(_normalize_scope("cross"), "cross")

    def test_normalize_scope_with_suffix(self):
        self.assertEqual(_normalize_scope("local(1-2files)"), "local")
        self.assertEqual(_normalize_scope("cross(10+files)"), "cross")

    def test_normalize_scope_none(self):
        self.assertIsNone(_normalize_scope(None))
        self.assertIsNone(_normalize_scope("invalid"))


class TestMajorityVote(unittest.TestCase):
    """多数決ロジックのテスト"""

    def test_unanimous(self):
        self.assertEqual(_majority_vote(["fix", "fix", "fix"]), "fix")

    def test_majority(self):
        self.assertEqual(_majority_vote(["fix", "fix", "feat"]), "fix")

    def test_tie_returns_first(self):
        result = _majority_vote(["fix", "feat"])
        self.assertIn(result, ("fix", "feat"))


class TestClassifyWithMock(unittest.TestCase):
    """classify() のモックテスト（API なし）"""

    def test_api_unavailable_uses_fallback(self):
        """ANTHROPIC_API_KEY 未設定時はキーワードフォールバックを使用"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = classify("バグを修正する")
        self.assertIn("route", result)
        self.assertIn("category", result)
        self.assertTrue(result.get("fallback", False))

    def test_mock_llm_fix(self):
        """LLM が fix を返したとき cursor-agent になる"""
        with patch(
            "src.routing.multi_classifier._call_anthropic",
            side_effect=["fix", "fix", "local"],
        ):
            result = classify("修正タスク")
        self.assertEqual(result["route"], "cursor-agent")
        self.assertEqual(result["category"], "fix")

    def test_mock_llm_feat(self):
        """LLM が feat を返したとき copilot になる"""
        with patch(
            "src.routing.multi_classifier._call_anthropic",
            side_effect=["feat", "feat", "module"],
        ):
            result = classify("新機能追加タスク")
        self.assertEqual(result["route"], "copilot")
        self.assertEqual(result["category"], "feat")

    def test_mock_llm_cross_scope_upgrades_to_manual(self):
        """Classifier-3 が cross のとき manual に格上げされる"""
        with patch(
            "src.routing.multi_classifier._call_anthropic",
            side_effect=["feat", "feat", "cross"],
        ):
            result = classify("大規模リファクタリング")
        self.assertEqual(result["route"], "manual")
        self.assertEqual(result["category"], "manual")
        self.assertEqual(result["scope"], "cross")

    def test_all_timeout_uses_fallback(self):
        """全分類器タイムアウト時はキーワードフォールバックを使用"""
        with patch(
            "src.routing.multi_classifier._call_anthropic",
            return_value=None,
        ):
            result = classify("fix the authentication error")
        self.assertTrue(result.get("fallback", False))
        self.assertEqual(result["route"], "cursor-agent")

    def test_result_structure(self):
        """classify() の結果が必須キーを持つ"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            result = classify("テストタスク")
        for key in ("route", "category", "scope", "votes", "confidence"):
            self.assertIn(key, result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
