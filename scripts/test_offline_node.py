"""No-Rhino behavioral tests for the supported offline node operation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))

import offline_node as node


class FakeVector:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.xyz = (x, y, z)

    def __mul__(self, factor: float) -> FakeVector:
        return FakeVector(*(value * factor for value in self.xyz))


class FakePoint:
    IsValid = True

    def __init__(self, x: float, y: float, z: float) -> None:
        self.xyz = (x, y, z)
        self.X, self.Y, self.Z = self.xyz

    def DistanceTo(self, other: FakePoint) -> float:
        return sum((a - b) ** 2 for a, b in zip(self.xyz, other.xyz)) ** 0.5

    def __sub__(self, other: FakePoint) -> FakeVector:
        return FakeVector(*(a - b for a, b in zip(self.xyz, other.xyz)))

    def __add__(self, other: FakeVector) -> FakePoint:
        return FakePoint(*(a + b for a, b in zip(self.xyz, other.xyz)))


class OfflinePolylineTests(unittest.TestCase):
    def test_line_is_divided_into_equal_lengths(self) -> None:
        points, count = node.validate_spec({
            "schema_version": 1, "operation": "divide_polyline",
            "points": [[0, 0, 0], [8, 0, 0]], "segment_count": 4,
        })
        self.assertEqual(node.divide_polyline(points, count),
                         [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [4.0, 0.0, 0.0],
                          [6.0, 0.0, 0.0], [8.0, 0.0, 0.0]])

    def test_unequal_edges_and_duplicate_vertex(self) -> None:
        points = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0),
                  (2.0, 0.0, 0.0), (2.0, 4.0, 0.0)]
        self.assertEqual(node.divide_polyline(points, 3),
                         [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0],
                          [2.0, 2.0, 0.0], [2.0, 4.0, 0.0]])

    def test_rejects_degenerate_and_nonfinite_data(self) -> None:
        with self.assertRaises(ValueError):
            node.divide_polyline([(1.0, 0.0, 0.0)] * 2, 2)
        with self.assertRaises(ValueError):
            node.validate_spec({"schema_version": 1, "operation": "divide_polyline",
                                "points": [[0, 0, 0], [float("nan"), 0, 0]],
                                "segment_count": 2})
        with self.assertRaises(ValueError):
            node.validate_spec({"schema_version": 1, "operation": "divide_polyline",
                                "points": [[0, 0, 0], [1, 0, 0]], "segment_count": True})
        with self.assertRaises(ValueError):
            node.validate_spec({"schema_version": 1, "operation": "divide_polyline",
                                "points": [[0, 0, 0], [10 ** 1000, 0, 0]], "segment_count": 2})
        with self.assertRaises(ValueError):
            node.validate_spec({"schema_version": 1, "operation": "brep_boolean",
                                "points": [[0, 0, 0], [1, 0, 0]], "segment_count": 2})
        with self.assertRaises(ValueError):
            node.divide_polyline([(0.0, 0.0, 0.0), (1e308, 0.0, 0.0),
                                  (0.0, 0.0, 0.0)], 2)

    def test_emitted_code_and_ports_are_bound_to_same_operation(self) -> None:
        self.assertEqual([entry["name"] for entry in node.PORTS["inputs"]], ["P", "N"])
        self.assertEqual(node.PORTS["outputs"][0]["name"], "Pts")
        for code in (node.CSHARP_BODY, node.IRONPYTHON_BODY):
            self.assertIn("Pts", code)
            self.assertIn("lengths", code)
            self.assertIn("target", code)

    def test_emitted_ironpython_body_computes_same_points(self) -> None:
        vertices = [FakePoint(0, 0, 0), FakePoint(2, 0, 0),
                    FakePoint(2, 0, 0), FakePoint(2, 4, 0)]
        context = {"P": vertices, "N": 3}
        # This fixed repository template is the behavior under test.
        exec(compile(node.IRONPYTHON_BODY, "<emitted GhPython>", "exec"), context)  # noqa: S102
        actual = [list(point.xyz) for point in context["Pts"]]
        expected = node.divide_polyline([point.xyz for point in vertices], 3)
        self.assertEqual(actual, expected)

    def test_emitted_ironpython_body_keeps_idle_output_empty(self) -> None:
        for vertices, count in ((None, 3), ([], 3), ([FakePoint(0, 0, 0)], 3),
                                ([FakePoint(0, 0, 0), FakePoint(1, 0, 0)], None)):
            context = {"P": vertices, "N": count}
            exec(compile(node.IRONPYTHON_BODY, "<emitted GhPython>", "exec"), context)  # noqa: S102
            self.assertEqual(context["Pts"], [])

    @unittest.skipUnless(sys.platform == "win32", "Windows .NET Framework C# compiler")
    def test_emitted_csharp_body_compiles_and_matches(self) -> None:
        compiler = Path(r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe")
        if not compiler.exists():
            self.skipTest("C# compiler not installed")
        source = """using System;
using System.Collections.Generic;
using System.Globalization;
struct Vector3d {
  public double X, Y, Z;
  public Vector3d(double x, double y, double z) { X=x; Y=y; Z=z; }
  public static Vector3d operator *(Vector3d v, double f) {
    return new Vector3d(v.X*f, v.Y*f, v.Z*f);
  }
}
struct Point3d {
  public double X, Y, Z;
  public Point3d(double x, double y, double z) { X=x; Y=y; Z=z; }
  public bool IsValid { get { return !double.IsNaN(X) && !double.IsNaN(Y) && !double.IsNaN(Z); } }
  public double DistanceTo(Point3d q) {
    double x=X-q.X, y=Y-q.Y, z=Z-q.Z;
    return Math.Sqrt(x*x+y*y+z*z);
  }
  public static Vector3d operator -(Point3d p, Point3d q) {
    return new Vector3d(p.X-q.X, p.Y-q.Y, p.Z-q.Z);
  }
  public static Point3d operator +(Point3d p, Vector3d v) {
    return new Point3d(p.X+v.X, p.Y+v.Y, p.Z+v.Z);
  }
}
class Program {
  static void RunScript(List<Point3d> P, int N, ref object Pts) {
""" + node.CSHARP_BODY + """
  }
  static void Main() {
    object output = null;
    RunScript(null, 3, ref output);
    if (((List<Point3d>)output).Count != 0) throw new Exception("Idle output was not empty");
    RunScript(new List<Point3d> {new Point3d(0,0,0), new Point3d(2,0,0),
      new Point3d(2,0,0), new Point3d(2,4,0)}, 3, ref output);
    foreach (Point3d p in (List<Point3d>)output)
      Console.WriteLine(p.X.ToString("R", CultureInfo.InvariantCulture) + "," +
        p.Y.ToString("R", CultureInfo.InvariantCulture) + "," +
        p.Z.ToString("R", CultureInfo.InvariantCulture));
  }
}"""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cs = root / "NodeHarness.cs"
            exe = root / "NodeHarness.exe"
            cs.write_text(source, encoding="utf-8")
            build = subprocess.run([str(compiler), "/nologo", "/out:" + str(exe), str(cs)],
                                   capture_output=True, text=True, check=False)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(exe)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            actual = [[float(value) for value in line.split(",")]
                      for line in result.stdout.splitlines()]
        self.assertEqual(actual, node.divide_polyline(
            [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0),
             (2.0, 0.0, 0.0), (2.0, 4.0, 0.0)], 3))


class OfflineBoundsTests(unittest.TestCase):
    def test_bounds_of_mixed_points_and_single_point(self) -> None:
        spec = {"schema_version": 1, "operation": "bounds_points",
                "points": [[4, -2, 6], [-1, 8, 3], [2, 0, -5]]}
        self.assertEqual(node.bounds_points(node.validate_bounds_spec(spec)),
                         {"min": [-1.0, -2.0, -5.0], "max": [4.0, 8.0, 6.0]})
        spec["points"] = [[1, 2, 3]]
        self.assertEqual(node.bounds_points(node.validate_bounds_spec(spec)),
                         {"min": [1.0, 2.0, 3.0], "max": [1.0, 2.0, 3.0]})

    def test_bounds_rejects_empty_nonfinite_and_extra_fields(self) -> None:
        base = {"schema_version": 1, "operation": "bounds_points", "points": []}
        for values in ([], [[float("inf"), 0, 0]], [[True, 0, 0]]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                node.validate_bounds_spec({**base, "points": values})
        with self.assertRaises(ValueError):
            node.validate_bounds_spec({**base, "segment_count": 2})

    def test_bounds_ironpython_body_matches_offline_result_and_idles(self) -> None:
        rhino = types.ModuleType("Rhino")
        geometry = types.ModuleType("Rhino.Geometry")
        geometry.Point3d = FakePoint
        rhino.Geometry = geometry
        with patch.dict(sys.modules, {"Rhino": rhino, "Rhino.Geometry": geometry}):
            vertices = [FakePoint(4, -2, 6), FakePoint(-1, 8, 3), FakePoint(2, 0, -5)]
            context = {"P": vertices}
            # This fixed repository template is the behavior under test.
            exec(compile(node.BOUNDS_IRONPYTHON_BODY, "<bounds GhPython>", "exec"), context)  # noqa: S102
            expected = node.bounds_points([point.xyz for point in vertices])
            self.assertEqual(list(context["Min"].xyz), expected["min"])
            self.assertEqual(list(context["Max"].xyz), expected["max"])
            for idle in (None, []):
                context = {"P": idle}
                exec(compile(node.BOUNDS_IRONPYTHON_BODY, "<bounds GhPython>", "exec"), context)  # noqa: S102
                self.assertIsNone(context["Min"])
                self.assertIsNone(context["Max"])

    @unittest.skipUnless(sys.platform == "win32", "Windows .NET Framework C# compiler")
    def test_bounds_csharp_body_compiles_and_matches(self) -> None:
        compiler = Path(r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe")
        if not compiler.exists():
            self.skipTest("C# compiler not installed")
        source = """using System;
using System.Collections.Generic;
struct Point3d {
  public double X, Y, Z;
  public Point3d(double x, double y, double z) { X=x; Y=y; Z=z; }
  public bool IsValid { get { return !double.IsNaN(X) && !double.IsNaN(Y) && !double.IsNaN(Z); } }
}
class Program {
  static void RunScript(List<Point3d> P, ref object Min, ref object Max) {
""" + node.BOUNDS_CSHARP_BODY + """
  }
  static void Main() {
    object min = new object(), max = new object();
    RunScript(null, ref min, ref max);
    if (min != null || max != null) throw new Exception("Idle output was not empty");
    RunScript(new List<Point3d> {new Point3d(4,-2,6), new Point3d(-1,8,3),
      new Point3d(2,0,-5)}, ref min, ref max);
    Point3d a = (Point3d)min, b = (Point3d)max;
    Console.WriteLine(a.X + "," + a.Y + "," + a.Z);
    Console.WriteLine(b.X + "," + b.Y + "," + b.Z);
  }
}"""
        with tempfile.TemporaryDirectory() as directory:
            cs = Path(directory) / "BoundsHarness.cs"
            exe = Path(directory) / "BoundsHarness.exe"
            cs.write_text(source, encoding="utf-8")
            build = subprocess.run([str(compiler), "/nologo", "/out:" + str(exe), str(cs)],
                                   capture_output=True, text=True, check=False)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            result = subprocess.run([str(exe)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            actual = [[float(value) for value in line.split(",")]
                      for line in result.stdout.splitlines()]
        self.assertEqual(actual, [[-1.0, -2.0, -5.0], [4.0, 8.0, 6.0]])


class EmittedContractTests(unittest.TestCase):
    def test_cli_emits_the_bodies_and_ports_covered_by_tests(self) -> None:
        script = Path(__file__).parent / "offline_node.py"
        cases = (
            ("divide_polyline", "csharp", node.CSHARP_BODY, node.PORTS),
            ("divide_polyline", "ironpython", node.IRONPYTHON_BODY, node.PORTS),
            ("bounds_points", "csharp", node.BOUNDS_CSHARP_BODY, node.BOUNDS_PORTS),
            ("bounds_points", "ironpython", node.BOUNDS_IRONPYTHON_BODY, node.BOUNDS_PORTS),
        )
        for operation, language, body, ports in cases:
            with self.subTest(operation=operation, language=language):
                result = subprocess.run(
                    [sys.executable, "-B", str(script), "emit", "--operation", operation,
                     "--language", language], capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(output["operation"], operation)
                self.assertEqual(output["code"], body)
                self.assertEqual(output["ports"], ports)
                self.assertEqual(output["paste_location"],
                                 "RunScript body" if language == "csharp"
                                 else "whole GhPython script body")
                if language == "csharp":
                    self.assertIn("System", output["imports"])


if __name__ == "__main__":
    unittest.main()
