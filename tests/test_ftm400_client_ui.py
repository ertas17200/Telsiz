"""Run real browser-client JS behavior without adding production dependencies."""
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class ClientUiContractTests(unittest.TestCase):
    def test_numeric_input_is_fail_closed(self):
        result = subprocess.run(
            ["node", str(HERE / "ftm400_client_ui_check.js")],
            capture_output=True, text=True, timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("FTM400_JS_UI_NUMERIC_VALIDATION=PASS", result.stdout)
