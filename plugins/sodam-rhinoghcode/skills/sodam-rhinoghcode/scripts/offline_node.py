"""License-free execution and Rhino 7 code emission for supported node specs.

Only explicitly listed point-list operations are implemented. This module never loads Rhino.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from itertools import pairwise
from pathlib import Path
from typing import Any

MAX_SPEC_BYTES = 1_000_000
MAX_POINTS = 100_000
MAX_SEGMENTS = 10_000

PORTS = {
    "inputs": [
        {"name": "P", "type_hint": "Point3d", "access": "List", "default": None,
         "description": "Polyline vertices in order."},
        {"name": "N", "type_hint": "Integer", "access": "Item", "default": 10,
         "description": "Number of equal-length segments."},
    ],
    "outputs": [
        {"name": "Pts", "description": "N + 1 points along the polyline."}
    ],
}

BOUNDS_PORTS = {
    "inputs": [{"name": "P", "type_hint": "Point3d", "access": "List",
                "default": None, "description": "Points to enclose."}],
    "outputs": [
        {"name": "Min", "description": "Minimum X, Y, and Z corner."},
        {"name": "Max", "description": "Maximum X, Y, and Z corner."},
    ],
}

CSHARP_BODY = """Pts = new List<Point3d>();
if (P == null || P.Count < 2 || P.Count > 100000 || N < 1 || N > 10000) return;
double[] lengths = new double[P.Count - 1];
double total = 0.0;
for (int j = 0; j < lengths.Length; j++)
{
  if (!P[j].IsValid || !P[j + 1].IsValid) return;
  lengths[j] = P[j].DistanceTo(P[j + 1]);
  total += lengths[j];
}
if (total <= 0.0 || double.IsInfinity(total) || double.IsNaN(total)) return;
List<Point3d> result = new List<Point3d>();
double passed = 0.0;
int edge = 0;
for (int i = 0; i <= N; i++)
{
  if (i == 0) { result.Add(P[0]); continue; }
  if (i == N) { result.Add(P[P.Count - 1]); continue; }
  double target = total * i / N;
  while (edge < lengths.Length - 1 && passed + lengths[edge] < target)
  { passed += lengths[edge]; edge++; }
  while (edge < lengths.Length - 1 && lengths[edge] == 0.0) edge++;
  if (lengths[edge] == 0.0) return;
  double fraction = (target - passed) / lengths[edge];
  result.Add(P[edge] + (P[edge + 1] - P[edge]) * fraction);
}
Pts = result;"""

IRONPYTHON_BODY = """import math

Pts = []
if P is not None and N is not None and 1 <= N <= 10000 and 2 <= len(P) <= 100000:
    lengths = []
    total = 0.0
    valid = True
    for j in range(len(P) - 1):
        if not P[j].IsValid or not P[j + 1].IsValid:
            valid = False
            break
        length = P[j].DistanceTo(P[j + 1])
        lengths.append(length)
        total += length
    if valid and total > 0.0 and not math.isinf(total) and not math.isnan(total):
        result = []
        passed = 0.0
        edge = 0
        for i in range(N + 1):
            if i == 0:
                result.append(P[0])
                continue
            if i == N:
                result.append(P[-1])
                continue
            target = total * i / N
            while edge < len(lengths) - 1 and passed + lengths[edge] < target:
                passed += lengths[edge]
                edge += 1
            while edge < len(lengths) - 1 and lengths[edge] == 0.0:
                edge += 1
            if lengths[edge] == 0.0:
                valid = False
                break
            fraction = (target - passed) / lengths[edge]
            result.append(P[edge] + (P[edge + 1] - P[edge]) * fraction)
        if valid:
            Pts = result"""

BOUNDS_CSHARP_BODY = """Min = null;
Max = null;
if (P == null || P.Count < 1 || P.Count > 100000) return;
double minX = double.PositiveInfinity, minY = double.PositiveInfinity, minZ = double.PositiveInfinity;
double maxX = double.NegativeInfinity, maxY = double.NegativeInfinity, maxZ = double.NegativeInfinity;
foreach (Point3d point in P)
{
  if (!point.IsValid) return;
  minX = Math.Min(minX, point.X); minY = Math.Min(minY, point.Y); minZ = Math.Min(minZ, point.Z);
  maxX = Math.Max(maxX, point.X); maxY = Math.Max(maxY, point.Y); maxZ = Math.Max(maxZ, point.Z);
}
Min = new Point3d(minX, minY, minZ);
Max = new Point3d(maxX, maxY, maxZ);"""

BOUNDS_IRONPYTHON_BODY = """import Rhino.Geometry as rg

Min = None
Max = None
if P is not None and 1 <= len(P) <= 100000:
    valid = True
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    for point in P:
        if not point.IsValid:
            valid = False
            break
        min_x = min(min_x, point.X); min_y = min(min_y, point.Y); min_z = min(min_z, point.Z)
        max_x = max(max_x, point.X); max_y = max(max_y, point.Y); max_z = max(max_z, point.Z)
    if valid:
        Min = rg.Point3d(min_x, min_y, min_z)
        Max = rg.Point3d(max_x, max_y, max_z)"""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def load_spec(path: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_SPEC_BYTES:
        raise ValueError("Spec exceeds the 1 MB limit")
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(value, dict):
        # Invalid user specs are reported as ValueError by the CLI.
        raise ValueError("Spec must be a JSON object")  # noqa: TRY004
    return value


def validate_points(raw: Any, minimum: int) -> list[tuple[float, float, float]]:
    if not isinstance(raw, list) or not minimum <= len(raw) <= MAX_POINTS:
        raise ValueError(f"points must contain {minimum} to 100000 vertices")
    points = []
    for point in raw:
        if not isinstance(point, list) or len(point) != 3:
            raise ValueError("Each vertex must contain three coordinates")
        coordinates = []
        for value in point:
            if type(value) not in (int, float):
                raise ValueError("Coordinates must be finite numbers")
            try:
                number = float(value)
            except OverflowError as exc:
                raise ValueError("Coordinates must be finite numbers") from exc
            if not math.isfinite(number):
                raise ValueError("Coordinates must be finite numbers")
            coordinates.append(number)
        points.append(tuple(coordinates))
    return points


def validate_spec(spec: dict[str, Any]) -> tuple[list[tuple[float, float, float]], int]:
    if set(spec) != {"schema_version", "operation", "points", "segment_count"}:
        raise ValueError("Spec must contain only schema_version, operation, points, segment_count")
    if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
        raise ValueError("Unsupported schema version")
    if spec["operation"] != "divide_polyline":
        raise ValueError("Unsupported operation")
    count = spec["segment_count"]
    if type(count) is not int or not 1 <= count <= MAX_SEGMENTS:
        raise ValueError("segment_count must be an integer from 1 to 10000")
    return validate_points(spec["points"], 2), count


def validate_bounds_spec(spec: dict[str, Any]) -> list[tuple[float, float, float]]:
    if set(spec) != {"schema_version", "operation", "points"}:
        raise ValueError("Bounds spec must contain only schema_version, operation, points")
    if type(spec["schema_version"]) is not int or spec["schema_version"] != 1:
        raise ValueError("Unsupported schema version")
    if spec["operation"] != "bounds_points":
        raise ValueError("Unsupported operation")
    return validate_points(spec["points"], 1)


def bounds_points(points: list[tuple[float, float, float]]) -> dict[str, list[float]]:
    return {"min": [min(point[axis] for point in points) for axis in range(3)],
            "max": [max(point[axis] for point in points) for axis in range(3)]}


def divide_polyline(points: list[tuple[float, float, float]], count: int) -> list[list[float]]:
    lengths = [math.dist(a, b) for a, b in pairwise(points)]
    if any(not math.isfinite(length) for length in lengths):
        raise ValueError("Polyline length must be finite")
    try:
        total = math.fsum(lengths)
    except OverflowError as exc:
        raise ValueError("Polyline length must be finite") from exc
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("Polyline length must be finite and greater than zero")
    result = []
    passed = 0.0
    edge = 0
    for i in range(count + 1):
        if i == 0:
            result.append(list(points[0]))
            continue
        if i == count:
            result.append(list(points[-1]))
            continue
        target = total * i / count
        while edge < len(lengths) - 1 and passed + lengths[edge] < target:
            passed += lengths[edge]
            edge += 1
        while edge < len(lengths) - 1 and lengths[edge] == 0.0:
            edge += 1
        if lengths[edge] == 0.0:
            raise ValueError("No nonzero edge at target")
        fraction = (target - passed) / lengths[edge]
        result.append([a + (b - a) * fraction for a, b in zip(points[edge], points[edge + 1])])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Execute a supported node spec without Rhino")
    run.add_argument("spec", type=Path)
    emit = commands.add_parser("emit", help="Emit a Rhino 7 node body and IO settings")
    emit.add_argument("--language", required=True, choices=("csharp", "ironpython"))
    emit.add_argument("--operation", default="divide_polyline",
                      choices=("divide_polyline", "bounds_points"))
    args = parser.parse_args()
    try:
        if args.command == "run":
            spec = load_spec(args.spec)
            if spec.get("operation") == "bounds_points":
                output = {"operation": "bounds_points", **bounds_points(validate_bounds_spec(spec))}
            else:
                points, count = validate_spec(spec)
                output = {"operation": "divide_polyline", "points": divide_polyline(points, count)}
        else:
            bounds = args.operation == "bounds_points"
            output = {
                "operation": args.operation,
                "target": "Rhino 7 legacy C# Script" if args.language == "csharp" else "Rhino 7 GhPython",
                "ports": BOUNDS_PORTS if bounds else PORTS,
                "paste_location": "RunScript body" if args.language == "csharp" else "whole GhPython script body",
                "imports": ["System", "System.Collections.Generic", "Rhino.Geometry"] if args.language == "csharp" else [],
                "code": (BOUNDS_CSHARP_BODY if bounds else CSHARP_BODY) if args.language == "csharp"
                        else (BOUNDS_IRONPYTHON_BODY if bounds else IRONPYTHON_BODY),
            }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
