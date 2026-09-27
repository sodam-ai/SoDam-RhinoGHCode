from __future__ import annotations

import sys
from pathlib import Path


def fail(message: str) -> int:
    print(f"ERROR: {message}")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
      return fail("usage: check_skill_md.py <path-to-SKILL.md>")

    path = Path(sys.argv[1])
    if not path.exists():
      return fail(f"file not found: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
      return fail("SKILL.md must start with YAML frontmatter")

    try:
      _, frontmatter, body = text.split("---", 2)
    except ValueError:
      return fail("SKILL.md must contain opening and closing frontmatter delimiters")

    lines = [line.strip() for line in frontmatter.splitlines() if line.strip()]
    keys = {}
    for line in lines:
      if ":" not in line:
        return fail(f"invalid frontmatter line: {line}")
      key, value = line.split(":", 1)
      keys[key.strip()] = value.strip()

    if "name" not in keys or not keys["name"]:
      return fail("frontmatter must include a non-empty name")
    if "description" not in keys or not keys["description"]:
      return fail("frontmatter must include a non-empty description")
    if not body.strip():
      return fail("SKILL.md body must not be empty")

    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
