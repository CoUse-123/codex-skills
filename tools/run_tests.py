#!/usr/bin/env python3
"""Run all repository test suites under tests/<skill-name>/."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"


def main() -> int:
    if not TESTS.exists():
        print("No tests directory found.")
        return 1

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    test_dirs = sorted(path for path in TESTS.iterdir() if path.is_dir())
    if not test_dirs:
        print("No test suites found.")
        return 1

    failed = 0
    for test_dir in test_dirs:
        print(f"==> {test_dir.relative_to(ROOT)}")
        proc = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(test_dir), "-v"],
            cwd=ROOT,
            env=env,
        )
        if proc.returncode != 0:
            failed = proc.returncode
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
