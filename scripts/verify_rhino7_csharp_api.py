"""Compile emitted Rhino 7 C# examples and geometry patterns against local DLLs.

Compilation checks actual API types and signatures without loading Rhino or
running the resulting assembly. It does not verify Grasshopper component IO.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from offline_node import BOUNDS_CSHARP_BODY, CSHARP_BODY

ROOT = Path(__file__).resolve().parents[1]
COMPILER = Path(r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe")
CASES = ("divide_polyline", "bounds_points", "trimmed_brep_isocurves", "tree_paths")


def source_text() -> str:
    return ("using System;\nusing System.Collections.Generic;\nusing Rhino.Geometry;\n"
            "using Grasshopper;\nusing Grasshopper.Kernel.Data;\n"
            "public static class Rhino7NodeCompileCheck {\n"
            "  public static void DividePolyline(List<Point3d> P, int N, ref object Pts) {\n"
            + CSHARP_BODY + "\n  }\n"
            "  public static void BoundsPoints(List<Point3d> P, ref object Min, ref object Max) {\n"
            + BOUNDS_CSHARP_BODY + "\n  }\n"
            "  public static void TrimmedBrepIsocurves(Brep B, int F, int N, ref object C) {\n"
            "    var result = new DataTree<Curve>();\n"
            "    C = result;\n"
            "    if (B == null || !B.IsValid || F < 0 || F >= B.Faces.Count || N < 1) return;\n"
            "    BrepFace face = B.Faces[F];\n"
            "    Interval domain = face.Domain(0);\n"
            "    if (!domain.IsValid) return;\n"
            "    for (int i = 0; i < N; i++) {\n"
            "      GH_Path path = new GH_Path(i);\n"
            "      result.EnsurePath(path);\n"
            "      double u = domain.T0 + ((double)(i + 1) / (N + 1)) * (domain.T1 - domain.T0);\n"
            "      Curve[] pieces = face.TrimAwareIsoCurve(0, u);\n"
            "      if (pieces == null) continue;\n"
            "      foreach (Curve piece in pieces)\n"
            "        if (piece != null && piece.IsValid) result.Add(piece, path);\n"
            "    }\n"
            "  }\n"
            "  public static void TranslateTree(DataTree<Point3d> P, double Z, ref object Q) {\n"
            "    var result = new DataTree<Point3d>();\n"
            "    Q = result;\n"
            "    if (P == null) return;\n"
            "    for (int b = 0; b < P.BranchCount; b++) {\n"
            "      GH_Path path = P.Path(b);\n"
            "      result.EnsurePath(path);\n"
            "      List<Point3d> points = P.Branch(b);\n"
            "      if (points == null) continue;\n"
            "      foreach (Point3d point in points)\n"
            "        if (point.IsValid) result.Add(point + new Vector3d(0, 0, Z), path);\n"
            "    }\n"
            "  }\n}\n")


def node_source(body: str, signature: str, namespaces: list[str], helpers: str) -> str:
    """Mirror the legacy editor's generated RunScript shell for a body check."""
    return ("\n".join("using " + namespace + ";" for namespace in namespaces)
            + "\npublic static class Rhino7NodeCompileCheck {\n"
            "  private static void Print(string message) {}\n"
            "  public static void RunScript(" + signature + ") {\n"
            + body + "\n  }\n" + helpers + "\n}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--source-file", type=Path,
                              help="Compile this complete C# source instead of the bundled examples.")
    source_group.add_argument("--body-file", type=Path,
                              help="Compile a legacy RunScript body using --signature and --using.")
    parser.add_argument("--signature", help="Exact Rhino 7 RunScript parameters from the configured ports.")
    parser.add_argument("--using", dest="namespaces", action="append", default=[],
                        help="One namespace stated in the node answer; repeat for each import.")
    parser.add_argument("--helpers-file", type=Path,
                        help="Optional C# helper methods for the legacy editor's custom-code area.")
    args = parser.parse_args()
    report = {"scope": "rhino7_installed_api_compile_only",
              "status": "fail", "native_grasshopper_execution": "not_verified"}
    requested_files = [path for path in (args.source_file, args.body_file, args.helpers_file)
                       if path is not None]
    if any(not path.is_file() for path in requested_files):
        report["detail"] = "Requested C# source, body or helper file does not exist"
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 1
    if (args.body_file is None and (args.signature or args.namespaces or args.helpers_file)
            or args.body_file is not None and not args.signature):
        report["detail"] = "--body-file requires --signature; --using/--helpers-file apply only to a body"
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 1
    if any(not namespace or not all(part.isidentifier() for part in namespace.split("."))
           for namespace in args.namespaces):
        report["detail"] = "Each --using must be a C# namespace name without 'using' or ';'"
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 1
    if sys.platform != "win32":
        report["detail"] = "Windows is required for this installed Rhino 7 check"
    elif not COMPILER.is_file():
        report["detail"] = "Windows .NET Framework C# compiler was not found"
    else:
        detector = subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts" / "detect_rhino_environment.py"),
             "--rhino-major", "7"], cwd=ROOT, capture_output=True, text=True, check=False)
        try:
            selected = json.loads(detector.stdout)["selected"]
            install_dir = Path(selected["install_dir"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            install_dir = None
        assembly = install_dir / "System" / "RhinoCommon.dll" if install_dir else None
        if detector.returncode != 0 or assembly is None or not assembly.is_file():
            report["detail"] = "Rhino 7 RhinoCommon.dll was not detected"
        else:
            grasshopper_dir = install_dir / "Plug-ins" / "Grasshopper"
            grasshopper = grasshopper_dir / "Grasshopper.dll"
            gh_io = grasshopper_dir / "GH_IO.dll"
            if not grasshopper.is_file() or not gh_io.is_file():
                report["detail"] = "Rhino 7 Grasshopper.dll or GH_IO.dll was not detected"
                print(json.dumps(report, ensure_ascii=True, indent=2))
                return 1
            with tempfile.TemporaryDirectory(prefix="rhino7-api-check-") as temp_dir:
                source = Path(temp_dir) / "NodeCompileCheck.cs"
                output = Path(temp_dir) / "NodeCompileCheck.dll"
                if args.source_file is not None:
                    content = args.source_file.read_text(encoding="utf-8")
                elif args.body_file is not None:
                    content = node_source(
                        args.body_file.read_text(encoding="utf-8"), args.signature,
                        args.namespaces,
                        args.helpers_file.read_text(encoding="utf-8")
                        if args.helpers_file is not None else "")
                else:
                    content = source_text()
                source.write_text(content, encoding="utf-8")
                build = subprocess.run(
                    [str(COMPILER), "/nologo", "/target:library", "/out:" + str(output),
                     "/reference:" + str(assembly),
                     "/reference:" + str(grasshopper),
                     "/reference:" + str(gh_io), str(source)],
                    cwd=temp_dir, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", check=False)
                report["status"] = "pass" if build.returncode == 0 and output.is_file() else "fail"
                passed_detail = (
                    "Provided C# source compiled against installed Rhino 7 DLLs"
                    if args.source_file is not None else
                    "Provided RunScript body compiled against installed Rhino 7 DLLs"
                    if args.body_file is not None else
                    "Two emitted bodies and two geometry patterns compiled against installed Rhino 7 DLLs")
                report["detail"] = (build.stdout + build.stderr).strip()[:2000] or (
                    passed_detail if report["status"] == "pass" else "Compilation produced no assembly")
                if report["status"] == "pass":
                    report["cases"] = (["provided_source"] if args.source_file is not None
                                       else ["provided_node_body"] if args.body_file is not None
                                       else list(CASES))
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
