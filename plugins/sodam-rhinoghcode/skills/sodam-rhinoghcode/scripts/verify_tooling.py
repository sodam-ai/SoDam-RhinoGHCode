"""Verify this skill's tooling and supported offline examples without starting Rhino.

This is not a Grasshopper runtime or a proof of arbitrary RhinoCommon parity.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_POINTS = [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0],
                 [2.0, 2.0, 0.0], [2.0, 4.0, 0.0]]
API_MEMBERS = ("Surface.IsoCurve", "BrepFace.TrimAwareIsoCurve",
               "Curve.DivideByCount", "BrepFace.OrientationIsReversed")


def run_script(*args: str) -> tuple[int, str, str]:
    command = [sys.executable, "-B", *args]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def check_command(name: str, *args: str) -> dict[str, str]:
    status, stdout, stderr = run_script(*args)
    detail = (stderr or stdout).strip().splitlines()
    return {"name": name, "status": "pass" if status == 0 else "fail",
            "detail": detail[-1][:300] if detail else "No output"}


def check_json(name: str, args: tuple[str, ...], predicate) -> dict[str, str]:
    status, stdout, stderr = run_script(*args)
    if status != 0:
        return {"name": name, "status": "fail", "detail": (stderr or stdout).strip()[:300]}
    try:
        payload = json.loads(stdout)
        valid = predicate(payload)
    except (json.JSONDecodeError, IndexError, KeyError, TypeError, ValueError) as exc:
        return {"name": name, "status": "fail", "detail": str(exc)[:300]}
    return {"name": name, "status": "pass" if valid else "fail",
            "detail": "Expected result confirmed" if valid else "Unexpected output contract"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rhino-major", type=int, choices=(7, 8),
                        help="Also require the selected installed Rhino files and RhinoCommon XML.")
    args = parser.parse_args()

    checks: list[dict[str, str]] = [
        check_command("skill_structure", "scripts/check_skill_md.py", "SKILL.md"),
        check_command("gotcha_registry", "scripts/check_gotcha_registry.py",
                      "references/rhinocommon-gotchas.json"),
        check_command("repo_structure", "scripts/inspect_skill_repo.py", "."),
    ]
    test_status, _, test_stderr = run_script("-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py")
    count = re.search(r"Ran \d+ tests?[^\n]*", test_stderr)
    result_line = next((line for line in reversed(test_stderr.splitlines())
                        if line.startswith(("OK", "FAILED"))), "No test summary")
    checks.append({"name": "regression_tests", "status": "pass" if test_status == 0 else "fail",
                   "detail": ((count.group(0) + "; ") if count else "") + result_line})
    checks.append(check_json(
        "offline_polyline_result",
        ("scripts/offline_node.py", "run", "offline-polyline-sample.json"),
        lambda value: value["operation"] == "divide_polyline" and value["points"] == SAMPLE_POINTS,
    ))
    checks.append(check_json(
        "offline_bounds_result",
        ("scripts/offline_node.py", "run", "offline-bounds-sample.json"),
        lambda value: value == {"operation": "bounds_points",
                                "min": [-1.0, -2.0, -5.0], "max": [4.0, 8.0, 6.0]},
    ))
    for language in ("csharp", "ironpython"):
        checks.append(check_json(
            "rhino7_" + language + "_example",
            ("scripts/offline_node.py", "emit", "--language", language),
            lambda value, language=language: (
                value["operation"] == "divide_polyline"
                and [port["name"] for port in value["ports"]["inputs"]] == ["P", "N"]
                and value["ports"]["outputs"][0]["name"] == "Pts"
                and bool(value["code"].strip())
                and ("GhPython" if language == "ironpython" else "C# Script") in value["target"]
            ),
        ))
        checks.append(check_json(
            "rhino7_" + language + "_bounds_example",
            ("scripts/offline_node.py", "emit", "--operation", "bounds_points",
             "--language", language),
            lambda value, language=language: (
                value["operation"] == "bounds_points"
                and [port["name"] for port in value["ports"]["inputs"]] == ["P"]
                and [port["name"] for port in value["ports"]["outputs"]] == ["Min", "Max"]
                and bool(value["code"].strip())
                and ("GhPython" if language == "ironpython" else "C# Script") in value["target"]
            ),
        ))
    if args.rhino_major is not None:
        major = str(args.rhino_major)
        checks.append(check_json(
            "installed_rhino_" + major,
            ("scripts/detect_rhino_environment.py", "--rhino-major", major),
            lambda value: value["selected"]["rhino_major"] == args.rhino_major,
        ))
        member_args = tuple(part for member in API_MEMBERS for part in ("--member", member))
        checks.append(check_json(
            "rhinocommon_" + major + "_xml",
            ("scripts/lookup_rhinocommon_docs.py", "--rhino-major", major, *member_args),
            lambda value: value["found"] and not value["missing"]
            and len(value["exact_matches"]) == len(API_MEMBERS),
        ))
        if sys.platform == "win32":
            compiler = Path(r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe")
            checks.append({"name": "csharp_stub_compiler", "status": "pass" if compiler.exists() else "fail",
                           "detail": "Installed compiler; stub compile is covered by regression_tests" if compiler.exists()
                           else "Compiler unavailable; C# stub execution remains unverified"})
            if args.rhino_major == 7:
                checks.append(check_json(
                    "rhino7_real_rhinocommon_csharp_compile",
                    ("scripts/verify_rhino7_csharp_api.py",),
                    lambda value: value["status"] == "pass"
                    and value["scope"] == "rhino7_installed_api_compile_only"
                    and value["cases"] == ["divide_polyline", "bounds_points",
                                           "trimmed_brep_isocurves", "tree_paths"]
                    and value["native_grasshopper_execution"] == "not_verified",
                ))
                checks.append(check_json(
                    "rhino7_installed_ironpython_stub_execution",
                    ("scripts/verify_rhino7_ironpython.py",),
                    lambda value: value["status"] == "pass"
                    and value["scope"] == "installed_rhino7_ironpython_with_point_stubs"
                    and value["operations"] == ["divide_polyline", "bounds_points"]
                    and value["native_grasshopper_execution"] == "not_verified",
                ))

    passed = all(check["status"] == "pass" for check in checks)
    report: dict[str, Any] = {
        "scope": "skill_tooling_and_two_supported_offline_operations",
        "tooling_status": "pass" if passed else "fail",
        "native_grasshopper_execution": "not_verified",
        "arbitrary_rhinocommon_parity": "not_implemented",
        "checks": checks,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
