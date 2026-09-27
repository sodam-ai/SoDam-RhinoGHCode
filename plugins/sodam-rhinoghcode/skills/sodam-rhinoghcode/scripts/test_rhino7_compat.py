"""Regression checks for Rhino-version selection without a Rhino installation."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))

import lookup_rhinocommon_docs as lookup

if sys.platform == "win32":
    import detect_rhino_environment as detector


class XmlSelectionTests(unittest.TestCase):
    def test_nested_xml_summary_preserves_reference_and_tail(self) -> None:
        member = ET.fromstring(
            '<member name="T:Example"><summary>Use <see cref="T:Rhino.Geometry.Curve"/> here.</summary></member>'
        )
        result = lookup.member_payload("T:Example", member)
        self.assertEqual(result["summary"], "Use T:Rhino.Geometry.Curve here.")

    def test_rhino7_lookup_does_not_choose_rhino8_xml(self) -> None:
        with mock.patch.object(Path, "exists", return_value=True):
            selected = lookup.find_default_xml(7)
        self.assertEqual(selected, Path(r"C:\Program Files\Rhino 7\System\RhinoCommon.xml"))

    def test_unspecified_lookup_preserves_rhino8_preference(self) -> None:
        with mock.patch.object(Path, "exists", return_value=True):
            selected = lookup.find_default_xml(None)
        self.assertEqual(selected, Path(r"C:\Program Files\Rhino 8\System\RhinoCommon.xml"))

    def test_missing_requested_xml_fails_instead_of_falling_back(self) -> None:
        output = io.StringIO()
        with (mock.patch.object(lookup, "find_default_xml", return_value=None),
              mock.patch.object(sys, "argv", ["lookup", "--rhino-major", "8"]),
              contextlib.redirect_stdout(output)):
            status = lookup.main()
        self.assertEqual(status, 1)
        self.assertFalse(json.loads(output.getvalue())["found"])

    def test_missing_exact_member_fails(self) -> None:
        output = io.StringIO()
        with (mock.patch.object(lookup, "find_default_xml", return_value=Path("fixture.xml")),
              mock.patch.object(Path, "exists", return_value=True),
              mock.patch.object(lookup, "load_members", return_value={}),
              mock.patch.object(sys, "argv", ["lookup", "--member", "Missing.Member"]),
              contextlib.redirect_stdout(output)):
            status = lookup.main()
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(output.getvalue())["missing"], ["Missing.Member"])

    @unittest.skipIf(sys.platform == "win32", "Windows is supported by this detector")
    def test_non_windows_detector_fails_explicitly(self) -> None:
        script = Path(__file__).parent / "detect_rhino_environment.py"
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Windows only", result.stdout)


@unittest.skipUnless(sys.platform == "win32", "Windows registry detector")
class DetectorSelectionTests(unittest.TestCase):
    def test_unsupported_rhino6_is_not_selected(self) -> None:
        output = io.StringIO()
        with (mock.patch.object(detector, "gather_install", side_effect=lambda major: {"rhino_major": 6} if major == "6" else None),
              mock.patch.object(sys, "argv", ["detector"]),
              contextlib.redirect_stdout(output)):
            status = detector.main()
        self.assertEqual(status, 1)
        self.assertIsNone(json.loads(output.getvalue())["selected"])

    def test_rhino7_prefers_ironpython(self) -> None:
        install = {
            "rhino_major": 7,
            "python": {
                "python3_runtime_detected": False,
                "python3_runtime_name": None,
                "ironpython_detected": True,
            },
            "csharp": {"recommended_compatibility": "Legacy Grasshopper C# script compatibility"},
        }
        output = io.StringIO()
        with (mock.patch.object(detector, "gather_install", side_effect=lambda major: install if major == "7" else None),
              mock.patch.object(sys, "argv", ["detector", "--rhino-major", "7"]),
              contextlib.redirect_stdout(output)):
            status = detector.main()
        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["guidance"]["preferred_python"], "IronPython 2.7")

    def test_absent_requested_version_is_an_error(self) -> None:
        output = io.StringIO()
        with (mock.patch.object(detector, "gather_install", return_value=None),
              mock.patch.object(sys, "argv", ["detector", "--rhino-major", "8"]),
              contextlib.redirect_stdout(output)):
            status = detector.main()
        payload = json.loads(output.getvalue())
        self.assertEqual(status, 1)
        self.assertIsNone(payload["selected"])
        self.assertIn("Rhino 8", payload["error"])


if __name__ == "__main__":
    unittest.main()
