import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_repo_hygiene", ROOT / "scripts" / "check_repo_hygiene.py")
hygiene = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hygiene)


class RepoHygieneTests(unittest.TestCase):
    def test_cache_artifacts_are_detected(self):
        paths = [
            "scripts/__pycache__/validate_knowledge.cpython-311.pyc",
            "tests/x.pyo",
            ".pytest_cache/v/cache/lastfailed",
            ".mypy_cache/3.12/foo.json",
            "a/.ruff_cache/x",
        ]
        self.assertEqual(hygiene.forbidden_paths(paths), paths)

    def test_source_files_are_not_flagged(self):
        paths = ["scripts/validate_knowledge.py", "data/rules.json", "docs/pycache_notes.md"]
        self.assertEqual(hygiene.forbidden_paths(paths), [])

    def test_repository_has_no_tracked_cache_artifacts(self):
        self.assertEqual(hygiene.forbidden_paths(hygiene.tracked_files()), [])


if __name__ == "__main__":
    unittest.main()
