from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rule", required=True, help="Rule text to append.")
    parser.add_argument("--source", default="user conversation", help="Where the rule came from.")
    parser.add_argument(
        "--file",
        default=str(Path(__file__).resolve().parents[1] / "references" / "custom-rules.md"),
        help="Target markdown file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.rule.strip():
        raise SystemExit("Rule text must not be empty.")
    path = Path(args.file)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = (
        f"\n### {timestamp}\n\n"
        f"- Source: {args.source}\n"
        f"- Rule: {args.rule.strip()}\n"
    )

    if not path.exists():
        path.write_text("# Custom Grasshopper Rules\n", encoding="utf-8")

    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry)

    print(f"Appended rule to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
