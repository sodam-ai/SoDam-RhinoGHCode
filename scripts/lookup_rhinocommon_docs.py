from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ALIASES = {
    "Surface.IsoCurve": "M:Rhino.Geometry.Surface.IsoCurve(System.Int32,System.Double)",
    "BrepFace.TrimAwareIsoCurve": "M:Rhino.Geometry.BrepFace.TrimAwareIsoCurve(System.Int32,System.Double)",
    "Curve.DivideByCount": "M:Rhino.Geometry.Curve.DivideByCount(System.Int32,System.Boolean)",
    "BrepFace.OrientationIsReversed": "P:Rhino.Geometry.BrepFace.OrientationIsReversed",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", help="Path to RhinoCommon.xml. If omitted, common Rhino install paths are probed.")
    parser.add_argument("--rhino-major", type=int, choices=(7, 8), help="Select the default XML for this Rhino version. --xml overrides the search.")
    parser.add_argument("--member", action="append", default=[], help="Exact member alias or XML member name to fetch.")
    parser.add_argument("--contains", action="append", default=[], help="Substring search over XML member names.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def find_default_xml(major: int | None) -> Path | None:
    versions = (major,) if major else (8, 7)
    for version in versions:
        candidates = [Path(fr"C:\Program Files\Rhino {version}\System\RhinoCommon.xml")]
        if version == 8:
            candidates.append(Path(r"C:\Program Files\Rhino 8\System\netcore\RhinoCommon.xml"))
        for candidate in candidates:
            if candidate.exists():
                return candidate
    return None


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def xml_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    parts = [element.text or ""]
    for child in element:
        if child.tag == "see":
            parts.append(child.attrib.get("cref", ""))
        elif child.tag == "paramref":
            parts.append(child.attrib.get("name", ""))
        parts.append(xml_text(child))
        parts.append(child.tail or "")
    return normalize_text("".join(parts))


def load_members(xml_path: Path) -> dict[str, ET.Element]:
    root = ET.parse(xml_path).getroot()
    return {
        member.attrib["name"]: member
        for member in root.findall(".//member")
        if "name" in member.attrib
    }


def member_payload(name: str, member: ET.Element) -> dict[str, object]:
    summary = xml_text(member.find("summary"))
    returns = xml_text(member.find("returns"))
    since = xml_text(member.find("since"))
    params = []
    for param in member.findall("param"):
        params.append(
            {
                "name": param.attrib.get("name", ""),
                "text": xml_text(param),
            }
        )
    return {
        "member": name,
        "summary": summary,
        "returns": returns,
        "since": since,
        "params": params,
    }


def resolve_requested_members(members: dict[str, ET.Element], requested: list[str]) -> tuple[list[dict[str, object]], list[str]]:
    results: list[dict[str, object]] = []
    missing: list[str] = []
    for raw_name in requested:
        actual_name = ALIASES.get(raw_name, raw_name)
        member = members.get(actual_name)
        if member is None:
            missing.append(raw_name)
            continue
        results.append(member_payload(actual_name, member))
    return results, missing


def search_members(members: dict[str, ET.Element], terms: list[str]) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    seen: set[str] = set()
    lowered_terms = [term.lower() for term in terms]
    for name, member in members.items():
        haystack = name.lower()
        if any(term in haystack for term in lowered_terms):
            if name in seen:
                continue
            seen.add(name)
            results.append(member_payload(name, member))
    return results


def main() -> int:
    args = parse_args()
    xml_path = Path(args.xml).expanduser() if args.xml else find_default_xml(args.rhino_major)
    if xml_path is None or not xml_path.exists():
        payload = {
            "found": False,
            "error": "RhinoCommon.xml not found for the requested Rhino version. Pass --xml explicitly or install Rhino locally."
        }
        print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
        return 1
    members = load_members(xml_path)
    exact_results, missing = resolve_requested_members(members, args.member)
    contains_results = search_members(members, args.contains)

    payload = {
        "found": True,
        "xml_path": str(xml_path),
        "exact_matches": exact_results,
        "contains_matches": contains_results,
        "missing": missing,
        "alias_keys": sorted(ALIASES)
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
