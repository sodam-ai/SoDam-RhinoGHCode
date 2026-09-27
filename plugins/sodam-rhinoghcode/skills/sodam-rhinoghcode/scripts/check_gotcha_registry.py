from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_TOP_LEVEL_KEYS = {"schema_version", "last_reviewed_utc", "entries"}
REQUIRED_ENTRY_KEYS = {
    "id",
    "topic",
    "risk",
    "triggers",
    "rule",
    "implication",
    "source_kind",
    "source_ref",
}
ALLOWED_RISKS = {"low", "medium", "high"}


def fail(message: str) -> int:
    print(f"ERROR: {message}")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: check_gotcha_registry.py <path-to-json>")

    path = Path(sys.argv[1])
    if not path.exists():
        return fail(f"file not found: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return fail(f"invalid json: {exc}")

    missing_top = REQUIRED_TOP_LEVEL_KEYS - set(payload)
    if missing_top:
        return fail(f"missing top-level keys: {sorted(missing_top)}")

    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        return fail("entries must be a non-empty list")

    ids: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            return fail(f"entry {index} must be an object")

        missing_entry = REQUIRED_ENTRY_KEYS - set(entry)
        if missing_entry:
            return fail(f"entry {index} missing keys: {sorted(missing_entry)}")

        entry_id = entry["id"]
        if not isinstance(entry_id, str) or not entry_id.strip():
            return fail(f"entry {index} has invalid id")
        if entry_id in ids:
            return fail(f"duplicate entry id: {entry_id}")
        ids.add(entry_id)

        risk = entry["risk"]
        if risk not in ALLOWED_RISKS:
            return fail(f"entry {entry_id} has invalid risk: {risk}")

        triggers = entry["triggers"]
        if not isinstance(triggers, list) or not triggers or not all(isinstance(item, str) and item.strip() for item in triggers):
            return fail(f"entry {entry_id} must have a non-empty string triggers list")

        for key in REQUIRED_ENTRY_KEYS - {"triggers", "risk"}:
            value = entry[key]
            if not isinstance(value, str) or not value.strip():
                return fail(f"entry {entry_id} has invalid value for {key}")

    print(f"OK: {path} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
