#!/usr/bin/env python3
"""
multi-classifier.py — Phase C タスク分類器（3モデル多数決）CLI エントリーポイント

Python モジュール名にハイフンは使えないため、実装は multi_classifier.py にある。
このスクリプトはその CLI ラッパーとして機能する。

Usage:
  python3 src/routing/multi-classifier.py --task "datetime.utcnow()の非推奨警告を修正"
  python3 src/routing/multi-classifier.py --task "新しい認証機能を追加" --model claude-haiku-4-5-20251001
"""

import os
import sys

# multi_classifier モジュールを同ディレクトリから読み込む
sys.path.insert(0, os.path.dirname(__file__))
from multi_classifier import main  # noqa: E402

if __name__ == "__main__":
    main()
