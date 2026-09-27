from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/common-failure-modes.md",
    "references/default-rules.md",
    "references/custom-rules.md",
    "references/official-rhino-notes.md",
    "references/rhinocommon-gotchas.json",
    "scripts/check_gotcha_registry.py",
    "scripts/check_skill_md.py",
    "scripts/detect_rhino_environment.py",
    "scripts/install_skill.py",
    "scripts/lookup_rhinocommon_docs.py",
    "scripts/run_python.ps1",
    "scripts/update_custom_rules.py",
    ".github/workflows/validate.yml",
]


def main() -> int:
    if len(sys.argv) != 2:
        print("ERROR: usage: inspect_skill_repo.py <repo-root>")
        return 1

    root = Path(sys.argv[1]).resolve()
    missing = [rel for rel in REQUIRED_FILES if not (root / rel).exists()]
    if missing:
        print("ERROR: missing required files:")
        for rel in missing:
            print(f" - {rel}")
        return 1

    print(f"OK: inspected {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
