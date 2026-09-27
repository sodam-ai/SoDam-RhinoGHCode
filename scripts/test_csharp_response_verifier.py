"""Catch missing imports in a complete generated Rhino 7 C# response."""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_rhino7_csharp_api.py")
SMOKE_RECORD = SCRIPT.parents[1] / "references" / "codex-response-smoke-test.md"
TREE_EXAMPLE = SCRIPT.parents[1] / "references" / "rhino7-brep-tree-example.md"
RHINO_DLL = Path(r"C:\Program Files\Rhino 7\System\RhinoCommon.dll")
GH_DLL = Path(r"C:\Program Files\Rhino 7\Plug-ins\Grasshopper\Grasshopper.dll")
COMPILER = Path(r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe")


@unittest.skipUnless(sys.platform == "win32" and all(
    path.is_file() for path in (RHINO_DLL, GH_DLL, COMPILER)
), "Installed Rhino 7 C# compile check")
class GeneratedResponseCompileTests(unittest.TestCase):
    def compile_body(self, body, imports, signature, helpers=None):
        with tempfile.TemporaryDirectory(prefix="rhino7-body-") as directory:
            body_file = Path(directory) / "body.cs"
            body_file.write_text(body, encoding="utf-8")
            command = [sys.executable, "-B", str(SCRIPT), "--body-file", str(body_file),
                       "--signature", signature]
            for namespace in imports:
                command.extend(("--using", namespace))
            if helpers is not None:
                helpers_file = Path(directory) / "helpers.cs"
                helpers_file.write_text(helpers, encoding="utf-8")
                command.extend(("--helpers-file", str(helpers_file)))
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def compile_source(self, source):
        with tempfile.TemporaryDirectory(prefix="rhino7-response-") as directory:
            file = Path(directory) / "GeneratedResponse.cs"
            file.write_text(source, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--source-file", str(file)],
                capture_output=True, text=True, check=False)
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def compile_response(self, include_grasshopper_import):
        recorded = SMOKE_RECORD.read_text(encoding="utf-8").split(
            "## Case 6: Rhino 7 trimmed Brep isocurves", 1)[1].split("Assessment:", 1)[0]
        answer = "\n".join(line[2:] if line.startswith("> ") else line[1:]
                           if line == ">" else line for line in recorded.splitlines())
        blocks = re.findall(r"```csharp\s*\n(.*?)\n```", answer, re.DOTALL)
        self.assertEqual(len(blocks), 3, "Expected body, helper and imports in recorded answer")
        body, helper, imports = blocks
        if include_grasshopper_import:
            imports += "\nusing Grasshopper;"
        source = (
            imports + "\n"
            + "public static class GeneratedResponse {\n"
            + "  private static void Print(string message) {}\n"
            + "  public static void RunScript(Brep B, int F, int N, ref object C) {\n"
            + body + "\n  }\n" + helper + "\n}\n"
        )
        return self.compile_source(source)

    def test_missing_grasshopper_import_fails(self):
        code, report = self.compile_response(False)
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "fail")
        self.assertIn("CS0246", report["detail"])

    def test_complete_imports_compile(self):
        code, report = self.compile_response(True)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["cases"], ["provided_source"])
        self.assertEqual(report["native_grasshopper_execution"], "not_verified")

    def test_documented_brep_tree_body_compiles(self):
        blocks = re.findall(r"```csharp\s*\n(.*?)\n```",
                            TREE_EXAMPLE.read_text(encoding="utf-8"), re.DOTALL)
        self.assertEqual(len(blocks), 2, "Expected imports and RunScript body")
        imports, body = blocks
        self.assertLess(body.index("tree.EnsurePath(path)"),
                        body.index("face.TrimAwareIsoCurve(0, u)"))
        source = (imports + "\npublic static class DocumentedTreeExample {\n"
                  + "  private static void Print(string message) {}\n"
                  + "  public static void RunScript(Brep B, int F, int N, ref object C) {\n"
                  + body + "\n  }\n}\n")
        code, report = self.compile_source(source)
        self.assertEqual(code, 0, report["detail"])
        self.assertEqual(report["cases"], ["provided_source"])

    def test_legacy_body_with_exact_ports_and_imports_compiles(self):
        body = ("Pts = new List<Point3d>();\n"
                "if (C == null || N < 1) return;\n"
                "double[] parameters = C.DivideByCount(N, true);\n"
                "if (parameters == null) return;\n"
                "foreach (double t in parameters) ((List<Point3d>)Pts).Add(C.PointAt(t));\n")
        code, report = self.compile_body(body, ("System.Collections.Generic", "Rhino.Geometry"),
                                         "Curve C, int N, ref object Pts")
        self.assertEqual(code, 0, report["detail"])
        self.assertEqual(report["cases"], ["provided_node_body"])
        self.assertEqual(report["native_grasshopper_execution"], "not_verified")

    def test_legacy_body_catches_missing_tree_import(self):
        body = "C = new DataTree<Curve>();\n"
        signature = "Brep B, ref object C"
        code, report = self.compile_body(body, ("Rhino.Geometry",), signature)
        self.assertEqual(code, 1)
        self.assertIn("CS0246", report["detail"])
        code, report = self.compile_body(body, ("Rhino.Geometry", "Grasshopper"), signature)
        self.assertEqual(code, 0, report["detail"])

    def test_legacy_body_includes_helpers(self):
        code, report = self.compile_body(
            "Pts = new List<Point3d>(); if (C == null) return; Pts = Make(C);",
            ("System.Collections.Generic", "Rhino.Geometry"), "Curve C, ref object Pts",
            "private static List<Point3d> Make(Curve curve) { return new List<Point3d>(); }")
        self.assertEqual(code, 0, report["detail"])


if __name__ == "__main__":
    unittest.main()
