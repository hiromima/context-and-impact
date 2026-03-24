#!/usr/bin/env python3
"""CLI shim — delegates to the importable ensemble_judge module."""
import os
import runpy
import sys

sys.path.insert(0, os.path.dirname(__file__))
runpy.run_module("ensemble_judge", run_name="__main__", alter_sys=True)
