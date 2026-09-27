"""Regression checks for verifier failure reporting."""

import unittest
from unittest.mock import patch

import verify_tooling


class VerifyToolingTests(unittest.TestCase):
    def test_missing_nested_result_is_reported_as_failure(self):
        with patch.object(verify_tooling, "run_script", return_value=(0, '{"points": []}', "")):
            result = verify_tooling.check_json(
                "sample", ("unused",), lambda payload: payload["points"][0] == [0, 0, 0]
            )
        self.assertEqual(result["status"], "fail")

    def test_failed_command_is_not_reported_as_pass(self):
        with patch.object(verify_tooling, "run_script", return_value=(1, "", "missing Rhino XML")):
            result = verify_tooling.check_json("xml", ("unused",), lambda _: True)
        self.assertEqual(result["status"], "fail")
        self.assertIn("missing Rhino XML", result["detail"])


if __name__ == "__main__":
    unittest.main()
