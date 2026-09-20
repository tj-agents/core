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

    def write_pr(self, *, files=("README.md",), labels=()):
        self.diff_payload.write_text("\n".join(files) + "\n", encoding="utf-8")
        self.gh_payload.write_text(
            json.dumps(
                {
                    "number": 42,
                    "url": "https://github.com/Concertable/agents/pull/42",
                    "headRefOid": HEAD,
                    "headRefName": "Feature/Thing",
                    "state": "OPEN",
                    "isDraft": True,
                    "changedFiles": len(files),
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
        self.write_pr(files=("README.md", "src/two.txt"))
        self.diff_payload.write_text("README.md\n", encoding="utf-8")
        result = self.run_hook()
        self.assertEqual(2, result.returncode)
        self.assertIn("API returned 1 of 2 changed paths", result.stderr)
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
