#!/usr/bin/env python3
"""
rrf-merge.py のユニットテスト

実行方法:
  python3 src/cli/test_rrf_merge.py
  python3 -m pytest src/cli/test_rrf_merge.py -v
"""

import sys
import os
import unittest

# rrf-merge.py を直接インポートできるようにパスを追加
sys.path.insert(0, os.path.dirname(__file__))

# ハイフン付きモジュール名は importlib で読み込む
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "rrf_merge",
    os.path.join(os.path.dirname(__file__), "rrf-merge.py"),
)
rrf_merge = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rrf_merge)

merge = rrf_merge.merge
rrf_score = rrf_merge.rrf_score
RRF_K = rrf_merge.RRF_K


class TestRrfScore(unittest.TestCase):
    def test_rank1(self):
        """rank=1 は 1/(k+1)"""
        self.assertAlmostEqual(rrf_score(1), 1.0 / (RRF_K + 1))

    def test_rank_increases_decreases_score(self):
        """ランクが上がるほどスコアは下がる"""
        self.assertGreater(rrf_score(1), rrf_score(2))
        self.assertGreater(rrf_score(2), rrf_score(10))


class TestSingleLayer(unittest.TestCase):
    """単一層のみ指定した場合のテスト"""

    def test_single_layer_order_preserved(self):
        docs = merge({"l1": ["doc_a", "doc_b", "doc_c"]})
        names = [d["doc"] for d in docs]
        # 上位ランクのドキュメントが先に来る
        self.assertEqual(names, ["doc_a", "doc_b", "doc_c"])

    def test_single_layer_sources(self):
        docs = merge({"l1": ["doc_a", "doc_b"]})
        for d in docs:
            self.assertEqual(d["sources"], ["l1"])

    def test_single_layer_score_correct(self):
        docs = merge({"l2b": ["doc_x"]})
        self.assertAlmostEqual(docs[0]["rrf_score"], round(rrf_score(1), 6))


class TestMultiLayerPromotion(unittest.TestCase):
    """複数層に登場するドキュメントが上位に来るテスト"""

    def test_doc_b_promoted(self):
        """
        l1=[doc_a, doc_b], l2b=[doc_b, doc_c] のとき
        doc_b は両層に出るため doc_a・doc_c より上位になる。
        """
        result = merge({"l1": ["doc_a", "doc_b"], "l2b": ["doc_b", "doc_c"]})
        top_doc = result[0]["doc"]
        self.assertEqual(top_doc, "doc_b")

    def test_sources_populated_correctly(self):
        result = merge({"l1": ["doc_a", "doc_b"], "l2b": ["doc_b", "doc_c"]})
        by_doc = {d["doc"]: d for d in result}
        self.assertIn("l1", by_doc["doc_b"]["sources"])
        self.assertIn("l2b", by_doc["doc_b"]["sources"])
        self.assertNotIn("l2b", by_doc["doc_a"]["sources"])

    def test_three_layer_example(self):
        """Issue の例: doc_a が l1+l3、doc_b が l1+l2b"""
        result = merge({
            "l1": ["doc_a", "doc_b"],
            "l2b": ["doc_b", "doc_c"],
            "l3": ["doc_a", "doc_c"],
        })
        by_doc = {d["doc"]: d for d in result}
        # doc_a (l1 rank1 + l3 rank1) vs doc_b (l1 rank2 + l2b rank1)
        score_a = 1 / (RRF_K + 1) + 1 / (RRF_K + 1)
        score_b = 1 / (RRF_K + 2) + 1 / (RRF_K + 1)
        self.assertAlmostEqual(by_doc["doc_a"]["rrf_score"], round(score_a, 6))
        self.assertAlmostEqual(by_doc["doc_b"]["rrf_score"], round(score_b, 6))
        self.assertGreater(by_doc["doc_a"]["rrf_score"], by_doc["doc_b"]["rrf_score"])


class TestEmpty(unittest.TestCase):
    """空リスト・空入力のテスト"""

    def test_all_empty(self):
        result = merge({"l1": [], "l2b": [], "l3": []})
        self.assertEqual(result, [])

    def test_some_empty(self):
        result = merge({"l1": ["doc_a"], "l2b": [], "l3": []})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["doc"], "doc_a")

    def test_empty_dict(self):
        result = merge({})
        self.assertEqual(result, [])


class TestLimit(unittest.TestCase):
    """limit パラメータのテスト"""

    def test_limit_applied(self):
        docs = [f"doc_{i}" for i in range(10)]
        result = merge({"l1": docs})
        self.assertEqual(len(result), 10)
        # limit はメインの merge ではなく呼び出し側で適用
        limited = result[:3]
        self.assertEqual(len(limited), 3)

    def test_output_sorted_desc(self):
        docs = [f"doc_{i}" for i in range(5)]
        result = merge({"l1": docs})
        scores = [d["rrf_score"] for d in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_cli_limit_parameter(self):
        """--limit が CLI 出力件数を正しく制限する"""
        import subprocess
        import json as _json

        script = os.path.join(os.path.dirname(__file__), "rrf-merge.py")
        payload = _json.dumps({"l1": [f"doc_{i}" for i in range(10)]})
        result = subprocess.run(
            [sys.executable, script, "--inline", payload, "--limit", "3"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        output = _json.loads(result.stdout)
        self.assertEqual(len(output), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
