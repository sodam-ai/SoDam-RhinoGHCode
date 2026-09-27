"""Build and check the local Codex plugin from the project skill source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "sodam-rhinoghcode"
PLUGIN_ROOT = ROOT / "plugins" / PLUGIN_NAME
SKILL_ROOT = PLUGIN_ROOT / "skills" / PLUGIN_NAME
ROOT_FILES = (
    "SKILL.md", "README.md", "README.en.md", "LICENSE", "LICENSE.txt", "NOTICE.md", ".gitignore",
    "offline-polyline-sample.json", "offline-bounds-sample.json",
)
SOURCE_DIRS = ("agents", "references", "scripts", ".github")
EXCLUDED_DIRS = {"__pycache__", ".ruff_cache", ".pytest_cache"}
EXCLUDED_PATHS = {Path("references/rhino7-canvas-native.png"),
                  Path("references/rhino7-visible-probe-screen.png")}


def validate_metadata() -> None:
    manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
    entries = [item for item in marketplace["plugins"] if item.get("name") == PLUGIN_NAME]
    if (manifest.get("name") != PLUGIN_NAME or manifest.get("skills") != "./skills/"
            or len(entries) != 1 or entries[0].get("source") != {
                "source": "local", "path": "./plugins/" + PLUGIN_NAME}
            or entries[0].get("policy", {}).get("installation") != "AVAILABLE"
            or entries[0].get("policy", {}).get("authentication") != "ON_INSTALL"):
        raise ValueError("Plugin manifest and marketplace entry do not match")


def source_files() -> dict[Path, Path]:
    files = {Path(name): ROOT / name for name in ROOT_FILES}
    for dirname in SOURCE_DIRS:
        directory = ROOT / dirname
        for path in directory.rglob("*"):
            if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
                continue
            if path.is_symlink():
                raise ValueError("Symlink in plugin source: " + str(path))
            if path.is_file() and path.suffix not in {".pyc", ".pyo"}:
                relative = path.relative_to(ROOT)
                if relative not in EXCLUDED_PATHS:
                    files[relative] = path
    missing = [str(relative) for relative, path in files.items() if not path.is_file()]
    if missing:
        raise ValueError("Missing plugin source: " + ", ".join(missing))
    return files


def content(relative: Path, path: Path) -> bytes:
    data = path.read_bytes()
    if relative == Path("SKILL.md"):
        old = (b"name: grasshopper-script-nodes\r\n" if b"name: grasshopper-script-nodes\r\n" in data
               else b"name: grasshopper-script-nodes\n")
        if data.count(old) != 1:
            raise ValueError("Unexpected source skill name")
        ending = b"\r\n" if old.endswith(b"\r\n") else b"\n"
        data = data.replace(old, b"name: " + PLUGIN_NAME.encode() + ending, 1)
    elif relative == Path("agents/openai.yaml"):
        old = b"$grasshopper-script-nodes"
        if data.count(old) != 1:
            raise ValueError("Unexpected source skill prompt")
        data = data.replace(old, b"$" + PLUGIN_NAME.encode(), 1)
    return data


def expected_files() -> dict[Path, bytes]:
    return {relative: content(relative, path) for relative, path in source_files().items()}


def compare(expected: dict[Path, bytes]) -> tuple[list[str], list[str]]:
    mismatched = sorted(str(relative) for relative, data in expected.items()
                        if not (SKILL_ROOT / relative).is_file()
                        or hashlib.sha256((SKILL_ROOT / relative).read_bytes()).digest()
                        != hashlib.sha256(data).digest())
    extra = sorted(str(path.relative_to(SKILL_ROOT)) for path in SKILL_ROOT.rglob("*")
                   if path.is_file() and path.relative_to(SKILL_ROOT) not in expected
                   and not any(part in EXCLUDED_DIRS for part in path.relative_to(SKILL_ROOT).parts)
                   and path.suffix not in {".pyc", ".pyo"}) if SKILL_ROOT.exists() else []
    return mismatched, extra


def build(expected: dict[Path, bytes]) -> None:
    for relative, data in expected.items():
        target = SKILL_ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file() and target.read_bytes() == data:
            continue
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".skill-build-",
                                         delete=False) as temporary:
            temporary.write(data)
            temporary_path = Path(temporary.name)
        try:
            os.replace(temporary_path, target)
        finally:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify without writing.")
    args = parser.parse_args()
    validate_metadata()
    expected = expected_files()
    if not args.check:
        build(expected)
    mismatched, extra = compare(expected)
    if mismatched or extra:
        print(f"Plugin bundle mismatch: missing/changed={mismatched} extra={extra}")
        return 1
    print(f"Plugin bundle OK: {len(expected)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
