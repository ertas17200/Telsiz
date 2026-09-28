#!/usr/bin/env python3
"""Fail if generated cache artifacts are tracked by git.

Guards against the PR #5 regression where ``git add -A`` committed
``__pycache__/*.pyc`` files. Runs in CI next to the knowledge validator.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(
    r"(^|/)(__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache)(/|$)|\.py[cod]$"
)


def forbidden_paths(paths: list[str]) -> list[str]:
    return [path for path in paths if FORBIDDEN.search(path)]


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [p for p in result.stdout.decode("utf-8").split("\0") if p]


def main() -> int:
    bad = forbidden_paths(tracked_files())
    if bad:
        for path in bad:
            print(f"FAIL: tracked cache artifact: {path}", file=sys.stderr)
        return 1
    print("PASS: no tracked cache artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
