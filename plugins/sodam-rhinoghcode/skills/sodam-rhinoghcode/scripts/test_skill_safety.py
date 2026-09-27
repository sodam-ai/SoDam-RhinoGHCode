"""Safety checks for the original skill installation workflow."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))

import install_skill


class SkillInstallTests(unittest.TestCase):
    def test_existing_destination_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            target = root / "skills"
            destination = target / "source"
            destination.mkdir(parents=True)
            marker = destination / "custom-rules.md"
            marker.write_text("existing user rule", encoding="utf-8")
            with (mock.patch.object(sys, "argv", ["install", "--source", str(source), "--target", str(target)]),
                  self.assertRaises(SystemExit) as error):
                install_skill.main()
            self.assertIn("left unchanged", str(error.exception))
            self.assertEqual(marker.read_text(encoding="utf-8"), "existing user rule")
            self.assertFalse((destination / "SKILL.md").exists())

    def test_new_destination_installs_without_git_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("skill", encoding="utf-8")
            (source / "rhino7-native-probe-result.json").write_text("{}", encoding="utf-8")
            (source / "rhino7-visible-check-result.json").write_text("{}", encoding="utf-8")
            (source / "references").mkdir()
            (source / "references" / "rhino7-visible-check-result.json").write_text("{}", encoding="utf-8")
            (source / "rhino7-ui-state.json").write_text("{}", encoding="utf-8")
            (source / ".ruff_cache").mkdir()
            (source / ".ruff_cache" / "cache-file").write_text("cache", encoding="utf-8")
            (source / ".git").mkdir()
            (source / ".agents").mkdir()
            (source / ".agents" / "marketplace.json").write_text("{}", encoding="utf-8")
            (source / "plugins").mkdir()
            (source / "plugins" / "plugin.json").write_text("{}", encoding="utf-8")
            target = root / "skills"
            with mock.patch.object(sys, "argv", ["install", "--source", str(source), "--target", str(target)]):
                self.assertEqual(install_skill.main(), 0)
            self.assertEqual((target / "source" / "SKILL.md").read_text(encoding="utf-8"), "skill")
            self.assertFalse((target / "source" / ".git").exists())
            self.assertFalse((target / "source" / "rhino7-native-probe-result.json").exists())
            self.assertFalse((target / "source" / "rhino7-visible-check-result.json").exists())
            self.assertFalse((target / "source" / "references" / "rhino7-visible-check-result.json").exists())
            self.assertFalse((target / "source" / "rhino7-ui-state.json").exists())
            self.assertFalse((target / "source" / ".ruff_cache").exists())
            self.assertFalse((target / "source" / ".agents").exists())
            self.assertFalse((target / "source" / "plugins").exists())

    def test_plan_excludes_generated_cache_and_probe_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("skill", encoding="utf-8")
            (source / "rhino7-visible-check-result.json").write_text("{}", encoding="utf-8")
            (source / "references").mkdir()
            (source / "references" / "rhino7-visible-check-result.json").write_text("{}", encoding="utf-8")
            (source / ".ruff_cache").mkdir()
            (source / ".ruff_cache" / "cache-file").write_text("cache", encoding="utf-8")
            (source / ".agents").mkdir()
            (source / ".agents" / "marketplace.json").write_text("{}", encoding="utf-8")
            (source / "plugins").mkdir()
            (source / "plugins" / "plugin.json").write_text("{}", encoding="utf-8")
            result = install_skill.plan(source, Path(directory) / "skills" / "source")
            self.assertEqual(result["new"], ["SKILL.md"])

    def test_frontmatter_name_avoids_a_second_installation_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "dated-project-folder"
            source.mkdir()
            (source / "SKILL.md").write_text(
                "---\nname: grasshopper-script-nodes\n---\n", encoding="utf-8")
            destination = root / "skills" / "grasshopper-script-nodes"
            destination.mkdir(parents=True)
            with (mock.patch.object(sys, "argv", ["install", "--source", str(source),
                                                "--target", str(root / "skills")]),
                  self.assertRaises(SystemExit) as error):
                install_skill.main()
            self.assertIn(str(destination.resolve()), str(error.exception))
            self.assertFalse((root / "skills" / "dated-project-folder").exists())

    def test_plan_reports_conflicting_rules_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "skills" / "source"
            (source / "references").mkdir(parents=True)
            (destination / "references").mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            (destination / "SKILL.md").write_text("old", encoding="utf-8")
            rules = destination / "references" / "custom-rules.md"
            rules.write_text("user rules", encoding="utf-8")
            (source / "references" / "custom-rules.md").write_text(
                "different rules", encoding="utf-8")
            before = rules.read_bytes()
            result = install_skill.plan(source, destination)
            self.assertTrue(result["custom_rules_conflict"])
            self.assertIn("SKILL.md", result["changed"])
            self.assertEqual(rules.read_bytes(), before)

    def test_sync_backs_up_and_preserves_user_and_installed_only_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "skills" / "source"
            (source / "references").mkdir(parents=True)
            (destination / "references").mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            (destination / "SKILL.md").write_text("old", encoding="utf-8")
            (source / "references" / "custom-rules.md").write_text("user rule", encoding="utf-8")
            rules = destination / "references" / "custom-rules.md"
            rules.write_text("user rule", encoding="utf-8")
            (source / "new.md").write_text("added", encoding="utf-8")
            installed_only = destination / "references" / "keep.md"
            installed_only.write_text("keep", encoding="utf-8")
            backup = root / "backup.zip"

            report = install_skill.sync_existing(source, destination, backup)

            self.assertEqual(report["status"], "pass")
            self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), "new")
            self.assertEqual((destination / "new.md").read_text(encoding="utf-8"), "added")
            self.assertEqual(rules.read_text(encoding="utf-8"), "user rule")
            self.assertEqual(installed_only.read_text(encoding="utf-8"), "keep")
            with zipfile.ZipFile(backup) as archive:
                self.assertEqual(archive.read("SKILL.md"), b"old")
                self.assertEqual(archive.read("references/keep.md"), b"keep")

    def test_sync_refuses_conflicting_custom_rules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "skills" / "source"
            (source / "references").mkdir(parents=True)
            (destination / "references").mkdir(parents=True)
            (source / "references" / "custom-rules.md").write_text("new", encoding="utf-8")
            rules = destination / "references" / "custom-rules.md"
            rules.write_text("user rule", encoding="utf-8")
            backup = root / "backup.zip"

            with self.assertRaises(SystemExit):
                install_skill.sync_existing(source, destination, backup)
            self.assertEqual(rules.read_text(encoding="utf-8"), "user rule")
            self.assertFalse(backup.exists())

    def test_sync_restores_touched_files_after_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            destination = root / "skills" / "source"
            source.mkdir()
            destination.mkdir(parents=True)
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            original = destination / "SKILL.md"
            original.write_text("old", encoding="utf-8")
            (source / "new.md").write_text("added", encoding="utf-8")
            backup = root / "backup.zip"
            real_copy = install_skill.atomic_copy
            calls = 0

            def fail_second_copy(from_path, to_path):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated copy failure")
                real_copy(from_path, to_path)

            with (mock.patch.object(install_skill, "atomic_copy", side_effect=fail_second_copy),
                  self.assertRaises(SystemExit)):
                install_skill.sync_existing(source, destination, backup)
            self.assertEqual(original.read_text(encoding="utf-8"), "old")
            self.assertFalse((destination / "new.md").exists())
            self.assertTrue(backup.is_file())


if __name__ == "__main__":
    unittest.main()
