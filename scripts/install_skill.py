from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to the skill repo root.")
    parser.add_argument(
        "--target",
        required=True,
        help="Directory that contains discoverable Codex skills, e.g. %%USERPROFILE%%\\.codex\\skills",
    )
    parser.add_argument("--plan", action="store_true",
                        help="Compare an existing installation without writing files.")
    parser.add_argument("--sync-existing", action="store_true",
                        help="Update an existing installation after backing up every installed file.")
    parser.add_argument("--backup-file", type=Path,
                        help="New zip file outside the skill directory, required for --sync-existing.")
    return parser.parse_args()


def skill_name(source: Path) -> str:
    content = (source / "SKILL.md").read_text(encoding="utf-8-sig")
    if content.startswith("---\n"):
        frontmatter = content.split("---", 2)[1]
        match = re.search(r"^name:\s*([a-z0-9][a-z0-9-]*)\s*$", frontmatter,
                          flags=re.MULTILINE)
        if match:
            return match.group(1)
        raise SystemExit("Invalid or missing skill name in SKILL.md frontmatter")
    return source.name


def files_under(root: Path, *, exclude_probe_result: bool = False) -> dict[str, Path]:
    return {path.relative_to(root).as_posix(): path for path in root.rglob("*")
            if path.is_file() and not any(part in {".git", ".agents", "plugins", "__pycache__", ".ruff_cache", ".pytest_cache"}
                                          for part in path.relative_to(root).parts)
            and path.suffix != ".pyc"
            and not (exclude_probe_result and
                     (path.name == "rhino7-ui-state.json" or
                      (path.name.startswith("rhino7-")
                       and path.name.endswith("-result.json"))))}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan(source: Path, destination: Path) -> dict[str, object]:
    source_files = files_under(source, exclude_probe_result=True)
    installed_files = files_under(destination) if destination.is_dir() else {}
    new = sorted(source_files.keys() - installed_files.keys())
    changed = sorted(name for name in source_files.keys() & installed_files.keys()
                     if digest(source_files[name]) != digest(installed_files[name]))
    return {"destination": str(destination),
            "installed": destination.is_dir(),
            "new": new, "changed": changed,
            "destination_only": sorted(installed_files.keys() - source_files.keys()),
            "custom_rules_conflict": "references/custom-rules.md" in changed}


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".skill-sync-", dir=destination.parent,
                                     delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def sync_existing(source: Path, destination: Path, backup_file: Path) -> dict[str, object]:
    source = source.resolve()
    destination = destination.resolve()
    backup_file = backup_file.resolve()
    if not destination.is_dir() or source == destination or source in destination.parents or destination in source.parents:
        raise SystemExit("Expected separate source and existing skill directories")
    if (not backup_file.parent.is_dir() or backup_file.exists()
            or source in backup_file.parents or destination in backup_file.parents):
        raise SystemExit("Backup must be a new file outside both skill directories")
    if backup_file.suffix.lower() != ".zip":
        raise SystemExit("Backup file must have a .zip extension")
    if any(path.is_symlink() for root in (source, destination) for path in root.rglob("*")):
        raise SystemExit("Symbolic links require manual review before synchronization")

    changes = plan(source, destination)
    if changes["custom_rules_conflict"]:
        raise SystemExit("Installed custom rules differ; resolve the conflict before synchronization")
    installed = files_under(destination)
    original_hashes = {name: digest(path) for name, path in installed.items()}
    source_files = files_under(source, exclude_probe_result=True)
    updates = [name for name in changes["new"] + changes["changed"]
               if name != "references/custom-rules.md"]

    # Write and verify the complete pre-update copy before modifying the skill.
    with zipfile.ZipFile(backup_file, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in installed.items():
            archive.write(path, name)
        archive.comment = json.dumps(original_hashes, sort_keys=True).encode("utf-8")
    with zipfile.ZipFile(backup_file) as archive:
        if set(archive.namelist()) != set(original_hashes) or any(
            hashlib.sha256(archive.read(name)).hexdigest() != expected
            for name, expected in original_hashes.items()
        ):
            raise SystemExit("Backup verification failed; installed skill was not changed")

    touched: list[str] = []
    try:
        for name in updates:
            touched.append(name)
            atomic_copy(source_files[name], destination / name)
        for name in updates:
            if digest(destination / name) != digest(source_files[name]):
                raise RuntimeError("Post-copy hash mismatch: " + name)
        for name, expected in original_hashes.items():
            if name not in updates and digest(destination / name) != expected:
                raise RuntimeError("Preserved file changed during sync: " + name)
    # Restore touched files for every failed update, including unexpected errors.
    except Exception as error:  # noqa: BLE001
        with zipfile.ZipFile(backup_file) as archive:
            for name in reversed(touched):
                path = destination / name
                if name in original_hashes:
                    with tempfile.NamedTemporaryFile(prefix=".skill-restore-", dir=path.parent,
                                                     delete=False) as temporary:
                        temporary.write(archive.read(name))
                        temporary_path = Path(temporary.name)
                    os.replace(temporary_path, path)
                else:
                    path.unlink(missing_ok=True)
        raise SystemExit("Synchronization failed and touched files were restored: " + str(error))
    return {"status": "pass", "destination": str(destination), "backup_file": str(backup_file),
            "updated": sorted(updates), "preserved_destination_only": changes["destination_only"],
            "preserved_custom_rules": "references/custom-rules.md" in installed}


def main() -> int:
    args = parse_args()
    source = Path(args.source).resolve()
    target_root = Path(args.target).expanduser().resolve()
    if not (source / "SKILL.md").exists():
        raise SystemExit(f"Missing SKILL.md in {source}")
    destination = target_root / skill_name(source)

    if args.plan:
        if args.sync_existing or args.backup_file:
            raise SystemExit("--plan cannot be combined with synchronization options")
        print(json.dumps(plan(source, destination), ensure_ascii=False, indent=2))
        return 0

    if args.sync_existing:
        if args.backup_file is None:
            raise SystemExit("--sync-existing requires --backup-file")
        print(json.dumps(sync_existing(source, destination, args.backup_file),
                         ensure_ascii=False, indent=2))
        return 0
    if args.backup_file is not None:
        raise SystemExit("--backup-file requires --sync-existing")

    if destination.exists():
        raise SystemExit(
            f"Destination already exists: {destination}. Existing skill files were left unchanged."
        )

    target_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(
        ".git", ".agents", "plugins", "__pycache__", ".ruff_cache", ".pytest_cache", "*.pyc",
        "rhino7-*-result.json", "rhino7-ui-state.json"))
    print(f"Installed {source.name} to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
