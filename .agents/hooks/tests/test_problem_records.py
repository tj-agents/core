import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from problem_records import (
    RecordError,
    declaration,
    main,
    operation_skill,
    primary_checkout,
)


class ProblemRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="record provider ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        primary = patch("problem_records.primary_checkout", return_value=self.root)
        primary.start()
        self.addCleanup(primary.stop)
        self.selection = self.root / ".problem-records.json"
        self.skill = self.root / "installed provider" / "SKILL.md"
        self.skill.parent.mkdir()
        self.skill.write_text("provider", encoding="utf-8")

    def select(self, value=None):
        self.selection.write_text(json.dumps(value or {"schema_version": 1, "provider": "optional:manage"}), encoding="utf-8")

    def test_absence_preserves_files_and_malformed_selection_fails(self):
        self.assertIsNone(declaration(self.root))
        for value in ({"schema_version": True, "provider": "optional:manage"},
                      {"schema_version": 1, "provider": "manage"},
                      {"schema_version": 1, "provider": "optional:manage", "script": "elsewhere"}):
            self.select(value)
            with self.assertRaises(RecordError):
                declaration(self.root)
        self.selection.write_text("{", encoding="utf-8")
        with self.assertRaises(RecordError):
            declaration(self.root)

    def test_personal_selection_implies_the_personal_provider_and_a_declaration_wins(self):
        agents = self.root / ".agents"
        agents.mkdir()
        (agents / "plugins.json").write_text(json.dumps({"schema_version": 1, "plugins": ["personal@tj-agents"],
                                                         "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}}}), encoding="utf-8")
        self.assertEqual({"schema_version": 1, "provider": "personal:work-item"}, declaration(self.root))
        self.select()
        self.assertEqual("optional:manage", declaration(self.root)["provider"])
        self.selection.unlink()
        for value in ({"schema_version": 1, "plugins": ["personal@tj-agents"], "marketplaces": ["tj-agents"]},
                      {"schema_version": 1, "plugins": ["personal@tj-agents"], "marketplaces": {"tj-agents": {"repository": "fork/marketplace"}}},
                      {"schema_version": True, "plugins": ["personal@tj-agents"], "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}}}):
            with self.subTest(value=value):
                (agents / "plugins.json").write_text(json.dumps(value), encoding="utf-8")
                self.assertIsNone(declaration(self.root))
        (agents / "plugins.json").write_text("{", encoding="utf-8")
        self.assertIsNone(declaration(self.root))

    def test_operation_uses_a_work_item_providers_dedicated_skill_and_never_falls_back(self):
        self.select({"schema_version": 1, "provider": "personal:work-item"})
        installed = {"personal:create-work-item": self.root / "create" / "SKILL.md", "personal:work-item": self.skill}
        with patch("installed_skills.resolved_skill", side_effect=lambda name, host: (installed[name], "") if name in installed else None):
            for operation, expected in (("create", "personal:create-work-item"), ("read", "personal:work-item")):
                with self.subTest(operation=operation):
                    found = operation_skill(self.root, operation, "claude")
                    self.assertEqual((expected, str(installed[expected]), "personal:work-item", str(self.root)),
                                     (found["operation"], found["skill"], found["provider"], found["primary"]))
            with self.assertRaisesRegex(RecordError, "personal:address-work-item is not installed"):
                operation_skill(self.root, "address", "claude")
        self.select({"schema_version": 1, "provider": "fixture:manage"})
        with patch("installed_skills.resolved_skill", return_value=(self.skill, "")) as resolve:
            self.assertEqual("fixture:manage", operation_skill(self.root, "create", "codex")["operation"])
            resolve.assert_called_once_with("fixture:manage", "codex")

    def test_operation_without_selection_or_installed_provider_blocks(self):
        with self.assertRaisesRegex(RecordError, "no selected"):
            operation_skill(self.root, "create", "codex")
        self.select()
        with patch("installed_skills.resolved_skill", return_value=None), self.assertRaisesRegex(RecordError, "not installed"):
            operation_skill(self.root, "create", "codex")
        with self.assertRaises(RecordError):
            operation_skill(self.root, "delete", "codex")

    def test_command_reports_a_missing_helper_as_a_block(self):
        self.select()
        with patch("problem_records.installed_skill", side_effect=ImportError("installed_skills")), patch("sys.stderr") as stderr:
            self.addCleanup(os.chdir, os.getcwd())
            self.assertEqual(2, main(["--root", str(self.root), "--operation", "read", "--harness", "codex"]))
        self.assertIn("write no other record", "".join(call.args[0] for call in stderr.write.call_args_list))

    def test_command_reports_a_block_and_writes_nothing(self):
        self.addCleanup(os.chdir, os.getcwd())
        before = sorted(self.root.rglob("*"))
        with patch("sys.stderr") as stderr:
            self.assertEqual(2, main(["--root", str(self.root), "--operation", "create", "--harness", "claude"]))
        self.assertIn("write no other record", "".join(call.args[0] for call in stderr.write.call_args_list))
        self.assertEqual(before, sorted(self.root.rglob("*")))


class PrimaryCheckoutTests(unittest.TestCase):
    def test_primary_selection_wins_from_feature_and_nested_directory(self):
        with tempfile.TemporaryDirectory(prefix="selected tracker ") as raw:
            root = Path(raw).resolve() / "source é"
            feature = Path(raw).resolve() / "feature é"
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.name=Fixture", "-c",
                            "user.email=fixture@example.invalid", "commit", "-q", "--allow-empty", "-m", "fixture"], check=True)
            subprocess.run(["git", "-C", str(root), "worktree", "add", "-q", "-b", "feature", str(feature)], check=True)
            nested = feature / "nested"
            nested.mkdir()
            selected = {"schema_version": 1, "provider": "fixture:manage"}
            (root / ".problem-records.json").write_text(json.dumps(selected), encoding="utf-8")
            (feature / ".problem-records.json").write_text("invalid override", encoding="utf-8")
            for directory in (root, feature, nested):
                with self.subTest(directory=directory):
                    self.assertEqual(root, primary_checkout(directory))
                    self.assertEqual(selected, declaration(primary_checkout(directory)))

    def test_bare_repository_entry_is_never_the_primary_checkout(self):
        with tempfile.TemporaryDirectory(prefix="bare tracker ") as raw:
            source = Path(raw).resolve() / "source"
            bare = Path(raw).resolve() / "bare.git"
            checkout = Path(raw).resolve() / "checkout"
            subprocess.run(["git", "init", "-q", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "-c", "user.name=Fixture", "-c",
                            "user.email=fixture@example.invalid", "commit", "-q", "--allow-empty", "-m", "fixture"], check=True)
            subprocess.run(["git", "clone", "-q", "--bare", str(source), str(bare)], check=True)
            subprocess.run(["git", "-C", str(bare), "worktree", "add", "-q", "-b", "work", str(checkout)], check=True)
            selected = {"schema_version": 1, "provider": "fixture:manage"}
            (checkout / ".problem-records.json").write_text(json.dumps(selected), encoding="utf-8")
            nested = checkout / "nested"
            nested.mkdir()
            self.assertEqual(checkout, primary_checkout(nested))
            self.assertEqual(selected, declaration(primary_checkout(nested)))

    def test_non_repository_and_unavailable_git_fail_visibly(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(RecordError):
            primary_checkout(directory)
        with patch("problem_records.process.run", side_effect=OSError("unavailable")), self.assertRaises(RecordError):
            primary_checkout(".")


if __name__ == "__main__":
    unittest.main()
