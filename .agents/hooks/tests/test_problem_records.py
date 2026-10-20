import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from problem_records import RecordError, declaration, primary_checkout, read_record


class ProblemRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="record provider ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.selection = self.root / ".problem-records.json"
        self.skill = self.root / "installed provider" / "SKILL.md"
        self.skill.parent.mkdir()
        self.skill.write_text("provider", encoding="utf-8")
        self.reader = self.skill.parent / "scripts/read_problem_record.py"
        self.reader.parent.mkdir()
        self.reader.write_text("provider", encoding="utf-8")
        self.reference = "https://example.invalid/repository/issues/1"
        self.value = {"record": self.reference, "kind": "bug", "state": "open", "body": "current evidence"}

    def select(self, value=None):
        self.selection.write_text(json.dumps(value or {"schema_version": 1, "provider": "optional:manage"}), encoding="utf-8")

    def test_absence_preserves_files_and_malformed_selection_fails(self):
        self.assertIsNone(declaration(self.root))
        with self.assertRaises(RecordError):
            read_record(self.root, self.reference, "codex")
        for value in ({"schema_version": True, "provider": "optional:manage"},
                      {"schema_version": 1, "provider": "manage"},
                      {"schema_version": 1, "provider": "optional:manage", "script": "elsewhere"}):
            self.select(value)
            with self.assertRaises(RecordError):
                declaration(self.root)
        self.selection.write_text("{", encoding="utf-8")
        with self.assertRaises(RecordError):
            declaration(self.root)

    def test_both_hosts_resolve_the_declared_skill_and_run_its_reader_without_shell(self):
        self.select()
        for host in ("codex", "claude"):
            with self.subTest(host=host), patch("skill_router.resolved_skill", return_value=(self.skill, "provider")) as resolve, patch("problem_records.subprocess.run", return_value=subprocess.CompletedProcess([], 0, json.dumps(self.value), "")) as run:
                self.assertEqual(self.value, read_record(self.root, self.reference, host))
                resolve.assert_called_once_with("optional:manage", host)
                self.assertEqual([sys.executable, "-B", str(self.reader), "--root", str(self.root), "--record", self.reference], run.call_args.args[0])
                self.assertNotIn("shell", run.call_args.kwargs)
                self.assertEqual("utf-8", run.call_args.kwargs["encoding"])

    def test_missing_provider_reader_and_host_fail_without_fallback(self):
        self.select()
        with patch("skill_router.resolved_skill", return_value=None), self.assertRaises(RecordError):
            read_record(self.root, self.reference, "codex")
        self.reader.unlink()
        with patch("skill_router.resolved_skill", return_value=(self.skill, "provider")), self.assertRaises(RecordError):
            read_record(self.root, self.reference, "claude")
        with self.assertRaises(RecordError):
            read_record(self.root, self.reference, "unknown")
        with self.assertRaises(RecordError):
            read_record(self.root, "relative/file.md", "codex")

    def test_native_discovery_failure_becomes_an_actionable_provider_error(self):
        from skill_router import NativePluginDiscoveryError
        self.select()
        with patch("skill_router.resolved_skill", side_effect=NativePluginDiscoveryError("codex", "unavailable")), self.assertRaisesRegex(RecordError, "could not be resolved"):
            read_record(self.root, self.reference, "codex")

    def test_invalid_closed_and_unrelated_provider_results_fail(self):
        self.select()
        values = ["invalid", "[]", json.dumps({**self.value, "state": "closed"}),
                  json.dumps({**self.value, "record": "another"}), json.dumps({**self.value, "kind": []}),
                  json.dumps({**self.value, "body": " "}), json.dumps({**self.value, "extra": True})]
        with patch("skill_router.resolved_skill", return_value=(self.skill, "provider")):
            for value in values:
                with self.subTest(value=value), patch("problem_records.subprocess.run", return_value=subprocess.CompletedProcess([], 0, value, "")), self.assertRaises(RecordError):
                    read_record(self.root, self.reference, "codex")
            with patch("problem_records.subprocess.run", side_effect=subprocess.TimeoutExpired("reader", 15)), self.assertRaises(RecordError):
                read_record(self.root, self.reference, "codex")
            with patch("problem_records.subprocess.run", return_value=subprocess.CompletedProcess([], 1, "", "private details")), self.assertRaisesRegex(RecordError, "could not read"):
                read_record(self.root, self.reference, "codex")


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
        with patch("problem_records.subprocess.run", side_effect=OSError("unavailable")), self.assertRaises(RecordError):
            primary_checkout(".")


if __name__ == "__main__":
    unittest.main()
