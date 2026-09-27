"""Tests for persistent rules using temporary files, never the user's rule file."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))

import update_custom_rules


class CustomRuleTests(unittest.TestCase):
    def test_appends_without_replacing_existing_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "custom-rules.md"
            path.write_text("# Existing\n\n- keep this rule\n", encoding="utf-8")
            before = path.read_text(encoding="utf-8")
            with (mock.patch.object(sys, "argv", ["rules", "--rule", "Use Rhino 7", "--source", "test", "--file", str(path)]),
                  contextlib.redirect_stdout(io.StringIO())):
                self.assertEqual(update_custom_rules.main(), 0)
            after = path.read_text(encoding="utf-8")
            self.assertTrue(after.startswith(before))
            self.assertIn("- Source: test", after)
            self.assertIn("- Rule: Use Rhino 7", after)

    def test_empty_rule_does_not_touch_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "custom-rules.md"
            with (mock.patch.object(sys, "argv", ["rules", "--rule", "   ", "--file", str(path)]),
                  self.assertRaises(SystemExit)):
                update_custom_rules.main()
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
