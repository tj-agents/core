import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch


HOOK = Path(__file__).resolve().parents[1] / "delivery_binding_gate.py"
sys.path.insert(0, str(HOOK.parent))
CREATE = "gh pr " + "create"
HEAD = "1111111111111111111111111111111111111111"


def load_gate():
    spec = importlib.util.spec_from_file_location("delivery_binding_gate", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_gate()
sys.path.insert(0, str(HOOK.parents[1] / "workflows"))
import workflow_ops
from delivery_runtime import PersistentDeliveryRouter, binding_from_artifact


class ScopedApprovalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".agents").mkdir()
        self.record = {"repository": "example/test", "pr_number": 42,
                       "worktree": str(self.root), "branch": "feature", "mode": "merge",
                       "instruction": "Merge PR 42 when checks and review pass",
                       "source": "user message in session fixture at 2026-10-04T18:00:00Z"}
        self.record_path = self.root / "approval.json"
        self.value = {"number": 42, "url": "https://github.com/example/test/pull/42",
                      "body": "## What\nChange\n## Why\nReason",
                      "headRefOid": HEAD, "headRefName": "feature", "state": "OPEN",
                      "files": [{"path": "README.md"}], "labels": [], "statusCheckRollup": []}
        for name, kwargs in (
                ("repository_slug", {"return_value": "example/test"}),
                ("pull_request_state", {"side_effect": lambda *args: self.value}),
                ("changed_paths", {"side_effect": lambda *args: [item["path"] for item in self.value["files"]]}),
                ("git", {"return_value": "feature"}),
                ("review_binding", {"side_effect": lambda root, branch, head: {
                    "work_order": "reviews/feature.md", "work_order_order": ["full"], "reviewed_sha": head}}),
                ("append_event", {"return_value": None})):
            started = patch.object(workflow_ops, name, **kwargs)
            started.start()
            self.addCleanup(started.stop)

    def bind(self, explicit=False):
        if explicit:
            self.record_path.write_text(json.dumps(self.record), encoding="utf-8")
        return workflow_ops.delivery_bind(self.root, "fixture", self.value["number"], "PR merged", None,
                                          self.record_path if explicit else None)["binding"]

    def test_no_table_approved_current_head_routes_merge(self):
        bound = self.bind(explicit=True)
        self.assertEqual("merge", bound["merge_authorization"]["mode"])
        self.assertEqual(self.record, bound["scoped_approval"])
        decision = PersistentDeliveryRouter().decide(binding_from_artifact(bound), {
            "pr_number": 42, "remote_head_sha": HEAD, "state": "open", "state_token": "ready",
            "checks_conclusion": "success", "review_judgment": "clean", "reviewed_sha": HEAD})
        self.assertEqual("merge", decision["skill"])

    def test_same_pr_rebind_preserves_wording_source_and_mode_on_new_head(self):
        self.bind(explicit=True)
        self.value["headRefOid"] = "b" * 40
        bound = self.bind()
        self.assertEqual("b" * 40, bound["head"])
        self.assertEqual(self.record, bound["scoped_approval"])
        self.assertEqual({"mode": "merge", "instruction": self.record["instruction"]}, bound["merge_authorization"])

    def test_no_record_keeps_missing_authority(self):
        bound = self.bind()
        self.assertEqual("absent", bound["merge_authorization"]["mode"])
        self.assertNotIn("scoped_approval", bound)

    def test_explicit_mismatch_or_invalid_record_never_falls_back_to_standing(self):
        policy = {"standing_authorization": "auto", "instruction": "Merge green reviewed PRs"}
        (self.root / ".agents/delivery-authorization.json").write_text(json.dumps(policy))
        original = dict(self.record)
        for field, wrong in (("repository", "other/repo"), ("pr_number", 43),
                             ("worktree", str(self.root / "other")), ("branch", "other"),
                             ("mode", "absent"), ("instruction", ""), ("source", "")):
            with self.subTest(field=field):
                self.record = dict(original, **{field: wrong})
                with self.assertRaises(workflow_ops.WorkflowOperationError):
                    self.bind(explicit=True)
                self.assertFalse((self.root / workflow_ops.delivery_runtime.BINDING_FILE).exists())
        self.record_path.write_text("{")
        with self.assertRaisesRegex(workflow_ops.WorkflowOperationError, "could not be read"):
            workflow_ops.delivery_bind(self.root, "fixture", 42, "PR merged", None, self.record_path)

    def test_new_stop_class_on_repair_revokes_delivery_and_keeps_provenance(self):
        self.bind(explicit=True)
        self.value["headRefOid"] = "b" * 40
        self.value["files"] = [{"path": ".github/workflows/verify.yml"}]
        bound = self.bind()
        self.assertEqual("absent", bound["merge_authorization"]["mode"])
        self.assertEqual("ci-workflow", bound["authorization_resolution"]["stopped_by"]["class"])
        self.assertEqual(self.record, bound["scoped_approval"])

    def test_hold_label_blocks_approval_without_table(self):
        self.value["labels"] = [{"name": "human-gate"}]
        bound = self.bind(explicit=True)
        self.assertEqual("absent", bound["merge_authorization"]["mode"])
        self.assertEqual("hold-label", bound["authorization_resolution"]["stopped_by"]["class"])

    def test_repository_stop_path_and_hold_label_block_scoped_approval(self):
        policy = {"standing_authorization": "absent", "instruction": None,
                  "always_stop_paths": [r"^special/"], "hold_label": "delivery-hold"}
        (self.root / ".agents/delivery-authorization.json").write_text(json.dumps(policy))
        self.value["files"] = [{"path": "special/handler.py"}]
        self.assertEqual("absent", self.bind(explicit=True)["merge_authorization"]["mode"])
        self.value["files"] = [{"path": "README.md"}]
        self.value["labels"] = [{"name": "delivery-hold"}]
        self.assertEqual("absent", self.bind()["merge_authorization"]["mode"])

    def test_successor_pr_branch_checkout_or_repository_does_not_inherit(self):
        for change in ("pr", "branch", "checkout", "repository"):
            with self.subTest(change=change):
                self.value.update(number=42, url="https://github.com/example/test/pull/42", headRefName="feature")
                self.bind(explicit=True)
                if change == "pr":
                    self.value.update(number=43, url="https://github.com/example/test/pull/43")
                elif change == "branch":
                    self.value["headRefName"] = "successor"
                elif change == "checkout":
                    bound_path = self.root / workflow_ops.delivery_runtime.BINDING_FILE
                    artifact = json.loads(bound_path.read_text())
                    artifact["scoped_approval"]["worktree"] = str(self.root / "other")
                    bound_path.write_text(json.dumps(artifact))
                else:
                    bound_path = self.root / workflow_ops.delivery_runtime.BINDING_FILE
                    artifact = json.loads(bound_path.read_text())
                    artifact["scoped_approval"]["repository"] = "other/repo"
                    bound_path.write_text(json.dumps(artifact))
                bound = self.bind()
                self.assertEqual("absent", bound["merge_authorization"]["mode"])
                self.assertNotIn("scoped_approval", bound)


class CreatedPullRequestTests(unittest.TestCase):
    def test_the_printed_url_identifies_the_new_pr(self):
        data = {"tool_response": "https://github.com/Concertable/agents/pull/42\n"}
        self.assertEqual("42", gate.created_pr(data))

    def test_a_structured_result_is_read_too(self):
        data = {"tool_response": {"stdout": "https://github.com/o/r/pull/7"}}
        self.assertEqual("7", gate.created_pr(data))

    def test_a_create_that_printed_no_url_did_not_create_anything(self):
        self.assertIsNone(gate.created_pr({"tool_response": "pull request create failed"}))

    def test_a_pr_url_in_the_command_is_never_read_as_a_result(self):
        data = {"tool_input": {"command": CREATE + " --body https://github.com/o/r/pull/9"}}
        self.assertIsNone(gate.created_pr(data))


class BindTests(unittest.TestCase):
    def test_timeout_returns_an_actionable_failure(self):
        with patch.object(gate, "run_command", side_effect=gate.CommandTimeout("delivery-bind timed out")):
            self.assertEqual((None, "delivery-bind timed out"), gate.bind(Path("."), 42))


class AuthorizationMessageTests(unittest.TestCase):
    def test_an_unstopped_resolution_says_the_merge_may_proceed_unattended(self):
        line = gate.authorization_line({"standing": "auto", "stopped_by": None})
        self.assertIn("AUTO", line)
        self.assertIn("without asking", line)

    def test_a_stop_class_names_the_path_that_caused_it(self):
        line = gate.authorization_line(
            {"standing": "auto", "stopped_by": {"class": "migration", "path": "db/Migrations/1.sql"}}
        )
        self.assertIn("ABSENT", line)
        self.assertIn("db/Migrations/1.sql", line)
        self.assertIn("migration", line)

    def test_a_repository_declared_stop_reads_as_this_repositorys_own_list(self):
        line = gate.authorization_line(
            {"standing": "auto", "stopped_by": {"class": "repository-declared", "path": "x.py"}}
        )
        self.assertIn("this repository's own always-stop list", line)

    def test_the_hold_label_is_reported_as_the_reason(self):
        line = gate.authorization_line(
            {"standing": "auto", "stopped_by": {"class": "hold-label", "label": "human-gate"}}
        )
        self.assertIn("human-gate", line)

    def test_a_repository_with_no_table_is_told_so(self):
        line = gate.authorization_line(
            {"standing": "absent", "stopped_by": {"class": "no-recorded-authorization"}}
        )
        self.assertIn("records no standing instruction", line)


class GateSubprocessTests(unittest.TestCase):
    """The hook as a subprocess against a real checkout with a deterministic `gh` shim."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)

        self.repo = base / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "remote", "add", "origin",
             "https://github.com/Concertable/agents.git"],
            check=True,
        )
        (self.repo / ".agents").mkdir()
        self.write_policy()

        self.gh_payload = base / "gh_payload.json"
        self.diff_payload = base / "gh_diff.txt"
        self.write_pr()

        self.bindir = base / "bin"
        self.bindir.mkdir()
        # Two answers, because the bind reads the PR summary and its paginated file list separately.
        if os.name == "nt":
            shim = self.bindir / "gh.cmd"
            shim.write_text(
                "@echo off\r\n"
                'echo %* | findstr /C:"api --paginate" >nul\r\n'
                f'if %errorlevel%==0 (type "{self.diff_payload}") else (type "{self.gh_payload}")\r\n',
                encoding="utf-8",
            )
        else:
            shim = self.bindir / "gh"
            shim.write_text(
                "#!/bin/sh\n"
                'case "$*" in\n'
                f'  *"api --paginate"*) cat "{self.diff_payload}" ;;\n'
                f'  *) cat "{self.gh_payload}" ;;\n'
                "esac\n",
                encoding="utf-8",
            )
            shim.chmod(shim.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def write_policy(self, **overrides):
        policy = {
            "standing_authorization": "auto",
            "instruction": "green and reviewed merges unattended",
            "always_stop_paths": [r"^\.agents/hooks/[^/]+\.py$"],
            "hold_label": "human-gate",
        }
        policy.update(overrides)
        (self.repo / ".agents" / "delivery-authorization.json").write_text(
            json.dumps(policy), encoding="utf-8"
        )

    def write_pr(self, *, files=("README.md",), labels=(), changed_files=None):
        self.diff_payload.write_text("\n".join(files) + "\n", encoding="utf-8")
        self.gh_payload.write_text(
            json.dumps(
                {
                    "number": 42,
                    "body": "## What\nChange\n## Why\nReason",
                    "url": "https://github.com/Concertable/agents/pull/42",
                    "headRefOid": HEAD,
                    "headRefName": "Feature/Thing",
                    "state": "OPEN",
                    "isDraft": True,
                    "changedFiles": len(files) if changed_files is None else changed_files,
                    "labels": [{"name": name} for name in labels],
                    "files": [{"path": path} for path in files],
                    "statusCheckRollup": [
                        {
                            "name": "verify",
                            "status": "IN_PROGRESS",
                            "conclusion": "",
                            "detailsUrl": "https://github.com/Concertable/agents/actions/runs/500/job/900",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def run_hook(self, *, command=None, response=None, cwd=None):
        env = dict(os.environ)
        env["PATH"] = str(self.bindir) + os.pathsep + env["PATH"]
        payload = {
            "session_id": uuid.uuid4().hex,
            "hook_event_name": "PostToolUse",
            "tool_use_id": uuid.uuid4().hex,
            "tool_name": "Bash",
            "cwd": str(cwd or self.repo),
            "tool_input": {"command": command or (CREATE + " --draft --title t --body b")},
            "tool_response": response
            if response is not None
            else "https://github.com/Concertable/agents/pull/42\n",
        }
        return subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload),
            capture_output=True, text=True, cwd=str(self.repo), env=env,
        )

    def binding(self):
        return json.loads(
            (self.repo / ".agents" / "persistent-workflow-binding.json").read_text(encoding="utf-8")
        )

    def test_opening_a_pr_binds_it_without_being_asked(self):
        result = self.run_hook()
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        self.assertIn("now has a delivery owner", result.stderr)
        binding = self.binding()
        self.assertEqual(42, binding["pr"])
        self.assertEqual(HEAD, binding["head"])
        self.assertEqual(str(self.repo.resolve()), binding["worktree"])
        self.assertEqual("auto", binding["merge_authorization"]["mode"])
        self.assertEqual(
            [{"check_id": "900", "run_id": "500", "head_sha": HEAD}], binding["pending_evidence"]
        )

    def test_a_stop_class_diff_is_bound_with_no_authorization(self):
        self.write_pr(files=("README.md", ".github/workflows/verify.yml"))
        result = self.run_hook()
        self.assertEqual(2, result.returncode)
        self.assertIn("ABSENT", result.stderr)
        self.assertEqual("absent", self.binding()["merge_authorization"]["mode"])

    def test_the_hold_label_withholds_authorization_on_an_ordinary_diff(self):
        self.write_pr(labels=("human-gate",))
        self.run_hook()
        self.assertEqual("absent", self.binding()["merge_authorization"]["mode"])

    def test_a_truncated_paginated_file_set_creates_no_binding(self):
        self.write_pr(files=("README.md",), changed_files=2)
        result = self.run_hook()
        self.assertEqual(2, result.returncode)
        self.assertIn("API returned 1 of 2 changed paths", result.stderr)
        self.assertNotIn("missing reported paths", result.stderr)
        self.assertFalse((self.repo / ".agents" / "persistent-workflow-binding.json").exists())

    def test_a_repository_that_records_no_instruction_is_left_alone(self):
        (self.repo / ".agents" / "delivery-authorization.json").unlink()
        result = self.run_hook()
        self.assertEqual(0, result.returncode)
        self.assertFalse((self.repo / ".agents" / "persistent-workflow-binding.json").exists())

    def test_the_same_delivery_is_never_rebound_by_this_hook(self):
        (self.repo / ".agents" / "persistent-workflow-binding.json").write_text(
            json.dumps({"pr": 42}), encoding="utf-8"
        )
        result = self.run_hook()
        self.assertEqual(0, result.returncode)
        self.assertEqual(42, self.binding()["pr"])

    def test_a_binding_left_by_another_pr_is_reported_rather_than_skipped(self):
        # Silently skipping would leave the PR just opened with nothing watching it, which is the
        # failure this gate exists to prevent, reached through a stale file.
        (self.repo / ".agents" / "persistent-workflow-binding.json").write_text(
            json.dumps({"pr": 7}), encoding="utf-8"
        )
        result = self.run_hook()
        self.assertEqual(2, result.returncode)
        self.assertIn("still owns PR #7", result.stderr)
        self.assertIn("delivery-release", result.stderr)
        self.assertEqual(7, self.binding()["pr"])

    def test_a_failed_create_binds_nothing(self):
        result = self.run_hook(response="pull request create failed: a PR already exists")
        self.assertEqual(0, result.returncode)
        self.assertFalse((self.repo / ".agents" / "persistent-workflow-binding.json").exists())

    def test_help_is_not_a_create(self):
        self.assertEqual(0, self.run_hook(command=CREATE + " --help").returncode)

    def test_an_unreadable_table_stops_loudly_instead_of_skipping(self):
        (self.repo / ".agents" / "delivery-authorization.json").write_text("{", encoding="utf-8")
        result = self.run_hook()
        self.assertEqual(2, result.returncode)
        self.assertIn("could not be bound", result.stderr)

    def test_a_merge_command_is_not_this_gates_business(self):
        self.assertEqual(0, self.run_hook(command="gh pr " + "merge 42 --auto").returncode)


if __name__ == "__main__":
    unittest.main()
