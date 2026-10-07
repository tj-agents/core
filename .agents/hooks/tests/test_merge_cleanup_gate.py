import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path
from unittest import mock


HOOK = Path(__file__).resolve().parents[1] / "merge_cleanup_gate.py"
ADAPTER = Path(__file__).resolve().parents[3] / ".codex" / "adapters" / "pre_tool_use.py"
sys.path.insert(0, str(HOOK.parent))


def load_gate():
    spec = importlib.util.spec_from_file_location("merge_cleanup_gate_under_test", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_gate()


def git(cwd, *args, check=True):
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def init_repo(root):
    bare = root / "origin.git"
    primary = root / "primary"
    subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(bare)], check=True)
    subprocess.run(["git", "clone", "-q", str(bare), str(primary)], check=True)
    git(primary, "config", "user.email", "t@example.com")
    git(primary, "config", "user.name", "t")
    (primary / "README.md").write_text("base\n", encoding="utf-8")
    git(primary, "add", "README.md")
    git(primary, "commit", "-q", "-m", "base")
    git(primary, "push", "-q", "-u", "origin", "main")
    git(primary, "remote", "set-head", "origin", "main")
    return bare, primary


def add_feature_worktree(primary, root, branch):
    git(primary, "branch", branch, "main")
    worktree = root / (branch + "-wt")
    git(primary, "worktree", "add", "-q", str(worktree), branch)
    return worktree


class MergeCleanupGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.state = tempfile.TemporaryDirectory()
        self.addCleanup(self.state.cleanup)
        self.env = dict(os.environ, AGENT_STATE_DIRECTORY=self.state.name, PYTHONIOENCODING="utf-8")

    def obligations_dir(self):
        return Path(self.state.name) / "merge-cleanup" / "obligations"

    def run_hook(self, data=None, argv=None, env=None):
        args = [sys.executable, "-B", str(HOOK), *(argv or [])]
        payload = "" if data is None else json.dumps(data)
        return subprocess.run(
            args, input=payload, capture_output=True, text=True,
            env=env if env is not None else self.env, timeout=20,
        )

    def payload(self, command, tool_name="exec_command", field="cmd", codex=True, session="s1", cwd=None, **extra):
        data = {
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {field: command},
            "session_id": session,
        }
        if codex:
            data["turn_id"] = "t1"
        if cwd is not None:
            data["cwd"] = cwd
        data.update(extra)
        return data

    def obligation_files(self):
        directory = self.obligations_dir()
        if not directory.is_dir():
            return []
        return list(directory.glob("*.json"))

    def sole_obligation(self):
        files = self.obligation_files()
        self.assertEqual(1, len(files), files)
        return files[0], json.loads(files[0].read_text(encoding="utf-8"))

    def edit_obligation(self, path, **fields):
        data = json.loads(path.read_text(encoding="utf-8"))
        data.update(fields)
        path.write_text(json.dumps(data), encoding="utf-8")

    # -- recording ---------------------------------------------------------

    def test_merge_enable_records_obligation_for_canonical_target(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        result = self.run_hook(self.payload(command, session="s1"))
        self.assertEqual(0, result.returncode, result.stderr)
        _, obligation = self.sole_obligation()
        self.assertEqual(str(worktree.resolve()), obligation["worktree"])
        self.assertEqual("feature", obligation["branch"])
        self.assertEqual("3", obligation["pr"])
        self.assertEqual("direct", obligation["merge_mode"])
        self.assertFalse(obligation["confirmed_merged"])
        self.assertIsNone(obligation["transferred_at"])
        self.assertEqual(str(primary.resolve()), obligation["primary"])

    def test_queued_merge_mode_recorded_from_auto_flag(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        command = f'pushd "{worktree}" && gh pr merge 3 --squash --auto'
        result = self.run_hook(self.payload(command))
        self.assertEqual(0, result.returncode, result.stderr)
        _, obligation = self.sole_obligation()
        self.assertEqual("queued", obligation["merge_mode"])

    def test_non_merge_command_writes_nothing_and_exits_zero(self):
        bare, primary = init_repo(self.root)
        result = self.run_hook(self.payload("git status"))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], self.obligation_files())

    def test_grace_selection_direct_vs_queued(self):
        direct = {"merge_mode": "direct"}
        queued = {"merge_mode": "queued"}
        self.assertEqual(gate.DIRECT_GRACE_SECONDS, gate.grace_seconds(direct))
        self.assertEqual(gate.QUEUED_GRACE_SECONDS, gate.grace_seconds(queued))

    # -- codex enforcement ---------------------------------------------------

    def test_deny_once_then_cooldown_then_denies_again_after_cooldown(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, session="s1"))
        path, obligation = self.sole_obligation()
        self.edit_obligation(path, recorded_at=time.time() - gate.DIRECT_GRACE_SECONDS - 1)

        first = self.run_hook(self.payload(
            '[IO.File]::WriteAllText("x.txt", "1")', session="s1", cwd=str(worktree)
        ))
        self.assertEqual(2, first.returncode)
        self.assertIn("MERGE CLEANUP GATE", first.stderr)
        obligation = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsNotNone(obligation["nagged_at"])

        second = self.run_hook(self.payload(
            'Set-Content -Path x.txt -Value 2', session="s1", cwd=str(worktree)
        ))
        self.assertEqual(0, second.returncode, second.stderr)

        self.edit_obligation(path, nagged_at=time.time() - gate.NAG_COOLDOWN_SECONDS - 1)
        third = self.run_hook(self.payload(
            'Set-Content -Path x.txt -Value 3', session="s1", cwd=str(worktree)
        ))
        self.assertEqual(2, third.returncode)
        self.assertIn("MERGE CLEANUP GATE", third.stderr)

    def test_other_session_is_never_denied(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, session="s1"))
        path, _ = self.sole_obligation()
        self.edit_obligation(path, recorded_at=time.time() - gate.DIRECT_GRACE_SECONDS - 1)

        result = self.run_hook(self.payload(
            '[IO.File]::WriteAllText("x.txt", "1")', session="s2", cwd=str(worktree)
        ))
        self.assertEqual(0, result.returncode, result.stderr)

    def test_exempt_commands_pass_even_past_grace(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, session="s1"))
        path, _ = self.sole_obligation()
        self.edit_obligation(path, recorded_at=time.time() - gate.DIRECT_GRACE_SECONDS - 1)

        for command in (
            "git status", "git -C \"" + str(worktree) + "\" fetch", "git worktree list",
            "gh pr view 3", "gh run list", "python cleanup_proof.py --worktree x",
            "pwsh close-tab.ps1 -List",
            "powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\\plugins\\peer-cli\\scripts\\finish.ps1",
            'git commit -am "fix the red sync PR"', "git show HEAD",
            'gh pr create --title "sync" --body "fix"',
            "git commit -am x && git push",
        ):
            with self.subTest(command=command):
                result = self.run_hook(self.payload(command, session="s1", cwd=str(worktree)))
                self.assertEqual(0, result.returncode, result.stderr)

    def test_non_exempt_commands_remain_denied_past_grace(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, session="s1"))
        path, _ = self.sole_obligation()
        self.edit_obligation(path, recorded_at=time.time() - gate.DIRECT_GRACE_SECONDS - 1)

        for command in (
            "git stash push -u -m wip", "git rebase --continue", "git restore --staged x.txt",
            "git reset --hard", "gh api repos/org/repo/pulls/1", "gh workflow run ci.yml",
            "gh release create v1", "gh repo view", "echo hi && git log",
        ):
            with self.subTest(command=command):
                result = self.run_hook(self.payload(command, session="s1", cwd=str(worktree)))
                self.assertEqual(2, result.returncode, command)
                self.edit_obligation(path, nagged_at=time.time() - gate.NAG_COOLDOWN_SECONDS - 1)

    def test_checkpoint_writes_remain_denied_past_grace(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, session="s1"))
        path, _ = self.sole_obligation()
        self.edit_obligation(path, recorded_at=time.time() - gate.DIRECT_GRACE_SECONDS - 1)

        for command in ('[IO.File]::WriteAllText("x.txt", "1")', "Set-Content -Path x.txt -Value 2"):
            with self.subTest(command=command):
                result = self.run_hook(self.payload(command, session="s1", cwd=str(worktree)))
                self.assertEqual(2, result.returncode)
                self.edit_obligation(path, nagged_at=time.time() - gate.NAG_COOLDOWN_SECONDS - 1)

    def test_unmerged_obligation_within_grace_never_denies(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, session="s1"))
        result = self.run_hook(self.payload(
            '[IO.File]::WriteAllText("x.txt", "1")', session="s1", cwd=str(worktree)
        ))
        self.assertEqual(0, result.returncode, result.stderr)

    # -- ownership transfer --------------------------------------------------

    def test_launcher_command_is_exempt_stamps_transfer_and_owner_never_denied_after(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, session="s1"))
        path, _ = self.sole_obligation()
        self.edit_obligation(path, recorded_at=time.time() - gate.DIRECT_GRACE_SECONDS - 1)

        launch = self.run_hook(self.payload(
            'pwsh -File launch-codex.ps1 -Prompt "continue"', session="s1", cwd=str(worktree)
        ))
        self.assertEqual(0, launch.returncode, launch.stderr)
        obligation = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsNotNone(obligation["transferred_at"])
        self.assertEqual("s1", obligation["transferred_by"])

        again = self.run_hook(self.payload(
            '[IO.File]::WriteAllText("x.txt", "1")', session="s1", cwd=str(worktree)
        ))
        self.assertEqual(0, again.returncode, again.stderr)

    def test_post_transfer_rearm_denies_prefix_matched_session_after_3600s(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, session="s1"))
        path, _ = self.sole_obligation()
        self.edit_obligation(
            path,
            transferred_at=time.time() - gate.TRANSFER_REARM_SECONDS - 1,
            transferred_by="s1",
        )

        unmatched = self.run_hook(self.payload(
            '[IO.File]::WriteAllText("x.txt", "1")', session="s2", cwd=str(self.root)
        ))
        self.assertEqual(0, unmatched.returncode, unmatched.stderr)

        matched = self.run_hook(self.payload(
            '[IO.File]::WriteAllText("x.txt", "1")', session="s2", cwd=str(worktree)
        ))
        self.assertEqual(2, matched.returncode)
        self.assertIn("MERGE CLEANUP GATE", matched.stderr)

    # -- reconcile ------------------------------------------------------------

    def test_reconcile_clears_on_worktree_deletion(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command))
        path, _ = self.sole_obligation()

        git(primary, "worktree", "remove", "--force", str(worktree))
        self.run_hook({"hook_event_name": "SessionStart", "cwd": str(primary)}, )
        self.assertFalse(path.exists())

    def test_reconcile_clears_on_branch_deletion_for_primary_checkout_delivery(self):
        bare, primary = init_repo(self.root)
        git(primary, "checkout", "-q", "-b", "feature")
        command = f'pushd "{primary}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(command))
        path, obligation = self.sole_obligation()
        self.assertEqual(str(primary.resolve()), obligation["worktree"])
        self.assertEqual("feature", obligation["branch"])
        git(primary, "checkout", "-q", "main")
        git(primary, "branch", "-D", "feature")

        self.run_hook({"hook_event_name": "SessionStart", "cwd": str(primary)})
        self.assertFalse(path.exists())

    def test_reconcile_clears_on_age(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command))
        path, _ = self.sole_obligation()
        self.edit_obligation(path, recorded_at=time.time() - gate.RECONCILE_MAX_AGE_SECONDS - 1)

        self.run_hook({"hook_event_name": "SessionStart", "cwd": str(primary)})
        self.assertFalse(path.exists())

    # -- Claude PostToolUse / Stop --------------------------------------------

    def test_claude_posttooluse_confirms_and_stop_blocks_while_unconfirmed_and_active_pass(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, codex=False, session="s1"))
        path, obligation = self.sole_obligation()
        self.assertFalse(obligation["confirmed_merged"])

        unconfirmed_stop = self.run_hook({
            "hook_event_name": "Stop", "session_id": "s1",
        })
        self.assertEqual(0, unconfirmed_stop.returncode, unconfirmed_stop.stderr)
        self.assertEqual("", unconfirmed_stop.stdout.strip())

        posttooluse = self.run_hook({
            "hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s1",
            "tool_input": {"command": merge_command},
            "tool_response": "✓ Squashed and merged pull request #3 (feature)",
        })
        self.assertEqual(0, posttooluse.returncode, posttooluse.stderr)
        obligation = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(obligation["confirmed_merged"])

        active_stop = self.run_hook({
            "hook_event_name": "Stop", "session_id": "s1", "stop_hook_active": True,
        })
        self.assertEqual(0, active_stop.returncode, active_stop.stderr)
        self.assertEqual("", active_stop.stdout.strip())

        confirmed_stop = self.run_hook({
            "hook_event_name": "Stop", "session_id": "s1",
        })
        self.assertEqual(0, confirmed_stop.returncode, confirmed_stop.stderr)
        decision = json.loads(confirmed_stop.stdout)
        self.assertEqual("block", decision["decision"])
        self.assertIn("MERGE CLEANUP GATE", decision["reason"])

    def test_real_gh_merge_output_variants_confirm(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        for output in (
            "✓ Merged pull request #3 (feature)",
            "✓ Squashed and merged pull request #3 (feature)",
            "✓ Rebased and merged pull request #3 (feature)",
            "",
        ):
            with self.subTest(output=output):
                self.run_hook(self.payload(merge_command, codex=False, session="s1"))
                path, obligation = self.sole_obligation()
                self.assertFalse(obligation["confirmed_merged"])
                result = self.run_hook({
                    "hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s1",
                    "tool_input": {"command": merge_command},
                    "tool_response": output,
                })
                self.assertEqual(0, result.returncode, result.stderr)
                obligation = json.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(obligation["confirmed_merged"], output)
                path.unlink()

    def test_auto_enqueue_output_does_not_confirm(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash --auto'
        for output in (
            "✓ Pull request #3 will be automatically merged when all requirements are met",
            "✓ Squashed and merged pull request #3 (feature)",
        ):
            with self.subTest(output=output):
                self.run_hook(self.payload(merge_command, codex=False, session="s1"))
                path, _ = self.sole_obligation()
                result = self.run_hook({
                    "hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s1",
                    "tool_input": {"command": merge_command},
                    "tool_response": output,
                })
                self.assertEqual(0, result.returncode, result.stderr)
                obligation = json.loads(path.read_text(encoding="utf-8"))
                self.assertFalse(obligation["confirmed_merged"])
                path.unlink()

    def test_monitor_style_commands_confirm_for_the_owning_session(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash --auto'
        for command, output in (
            ("python .agents/workflows/workflow_ops.py monitor --kind pr --id 3 --head abc123",
             '{"state":"merged"}'),
            ("gh pr view 3 --json state", '{"state": "MERGED"}'),
            ("gh pr checks 3", '{"state": "MERGED"}'),
        ):
            with self.subTest(command=command):
                self.run_hook(self.payload(merge_command, codex=False, session="s1"))
                path, obligation = self.sole_obligation()
                self.assertFalse(obligation["confirmed_merged"])
                result = self.run_hook({
                    "hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s1",
                    "tool_input": {"command": command},
                    "tool_response": output,
                })
                self.assertEqual(0, result.returncode, result.stderr)
                obligation = json.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(obligation["confirmed_merged"], command)
                path.unlink()

    def test_pr_status_no_longer_matches_monitor_pattern(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash --auto'
        self.run_hook(self.payload(merge_command, codex=False, session="s1"))
        path, _ = self.sole_obligation()

        result = self.run_hook({
            "hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s1",
            "tool_input": {"command": "gh pr status"},
            "tool_response": '{"state": "MERGED"}',
        })
        self.assertEqual(0, result.returncode, result.stderr)
        obligation = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(obligation["confirmed_merged"])

    def test_open_pr_mentioning_merged_in_text_does_not_confirm(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash --auto'
        self.run_hook(self.payload(merge_command, codex=False, session="s1"))
        path, _ = self.sole_obligation()

        result = self.run_hook({
            "hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s1",
            "tool_input": {"command": "gh pr view 3 --json state,title"},
            "tool_response": '{"state": "OPEN", "title": "chore: already merged artifacts"}',
        })
        self.assertEqual(0, result.returncode, result.stderr)
        obligation = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(obligation["confirmed_merged"])

    def test_numberless_obligation_confirmed_by_owning_session_state_report(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge --squash --auto'
        self.run_hook(self.payload(merge_command, codex=False, session="s1"))
        path, obligation = self.sole_obligation()
        self.assertIsNone(obligation["pr"])

        result = self.run_hook({
            "hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s1",
            "tool_input": {"command": "gh pr view 3 --json state"},
            "tool_response": '{"state": "MERGED"}',
        })
        self.assertEqual(0, result.returncode, result.stderr)
        obligation = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(obligation["confirmed_merged"])

    def test_monitor_style_command_from_another_session_does_not_confirm(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash --auto'
        self.run_hook(self.payload(merge_command, codex=False, session="s1"))
        path, _ = self.sole_obligation()

        result = self.run_hook({
            "hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "s2",
            "tool_input": {"command": "gh pr view 3 --json state"},
            "tool_response": '{"state": "MERGED"}',
        })
        self.assertEqual(0, result.returncode, result.stderr)
        obligation = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(obligation["confirmed_merged"])

    # -- PostToolUseFailure never deletes; confirms only on merge evidence ----

    def test_posttoolusefailure_without_merge_evidence_leaves_obligation_unconfirmed(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, codex=False, session="s1"))
        path, _ = self.sole_obligation()
        self.assertTrue(path.exists())

        result = self.run_hook({
            "hook_event_name": "PostToolUseFailure", "tool_name": "Bash", "session_id": "s1",
            "tool_input": {"command": merge_command},
            "tool_response": "X Pull request #3 is not mergeable: the merge commit cannot be cleanly created",
        })
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(path.exists())
        obligation = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(obligation["confirmed_merged"])

    def test_posttoolusefailure_with_merge_evidence_confirms_without_deleting(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, codex=False, session="s1"))
        path, _ = self.sole_obligation()

        result = self.run_hook({
            "hook_event_name": "PostToolUseFailure", "tool_name": "Bash", "session_id": "s1",
            "tool_input": {"command": merge_command},
            "tool_response": "✓ Squashed and merged pull request tj-agents/core#3 (feature)\n"
                             "X a later step failed",
        })
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(path.exists())
        obligation = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(obligation["confirmed_merged"])

    def test_posttoolusefailure_from_another_session_never_deletes_the_obligation(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command, codex=False, session="s1"))
        path, _ = self.sole_obligation()

        result = self.run_hook({
            "hook_event_name": "PostToolUseFailure", "tool_name": "Bash", "session_id": "s2",
            "tool_input": {"command": merge_command},
        })
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(path.exists())

    # -- should_reconcile branch-absence precision ----------------------------

    def test_branch_ref_missing_is_false_on_a_non_one_exit_code(self):
        self.assertFalse(gate.branch_ref_missing(self.root / "does-not-exist", "feature"))

    def test_branch_ref_missing_is_false_on_timeout(self):
        with mock.patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git", timeout=5),
        ):
            self.assertFalse(gate.branch_ref_missing(self.root, "feature"))

    def test_should_reconcile_keeps_the_obligation_when_show_ref_errors(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        obligation = {
            "worktree": str(worktree),
            "primary": str(self.root / "does-not-exist"),
            "branch": "feature",
            "recorded_at": time.time(),
        }
        self.assertFalse(gate.should_reconcile(obligation, time.time()))

    def test_should_reconcile_never_disarms_for_the_head_branch_name(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        obligation = {
            "worktree": str(worktree),
            "primary": str(primary),
            "branch": "HEAD",
            "recorded_at": time.time(),
        }
        self.assertFalse(gate.should_reconcile(obligation, time.time()))

    # -- incident replay -------------------------------------------------------

    def test_incident_replay_codex_denies_and_claude_stop_blocks(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash --match-head-commit'
        self.run_hook(self.payload(merge_command, codex=True, session="codex-session"))
        codex_path, obligation = self.sole_obligation()
        self.edit_obligation(codex_path, recorded_at=time.time() - gate.DIRECT_GRACE_SECONDS - 1)

        denied = self.run_hook(self.payload(
            '[IO.File]::WriteAllText("handoff.md", "next steps")',
            session="codex-session", cwd=str(worktree),
        ))
        self.assertEqual(2, denied.returncode)
        self.assertIn("gh pr merge", denied.stderr)
        self.assertIn("cleanup", denied.stderr.lower())
        head = subprocess.run(
            ["git", "-C", str(worktree), "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(head, obligation["head"])
        self.assertIn(f"--head {head}", denied.stderr)
        self.assertNotIn("<head>", denied.stderr)
        self.assertIn("finish.ps1", denied.stderr)

        self.run_hook(self.payload(merge_command, codex=False, session="claude-session"))
        claude_path, _ = self.sole_obligation() if len(self.obligation_files()) == 1 else (None, None)
        self.assertEqual(1, len(self.obligation_files()))
        confirm = self.run_hook({
            "hook_event_name": "PostToolUse", "tool_name": "Bash", "session_id": "claude-session",
            "tool_input": {"command": merge_command},
            "tool_response": "✓ Merged pull request #3 (feature)",
        })
        self.assertEqual(0, confirm.returncode, confirm.stderr)
        stop = self.run_hook({"hook_event_name": "Stop", "session_id": "claude-session"})
        decision = json.loads(stop.stdout)
        self.assertEqual("block", decision["decision"])

    # -- manual clear ----------------------------------------------------------

    def test_clear_removes_obligation(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command))
        path, _ = self.sole_obligation()

        result = self.run_hook(data=None, argv=["--clear", str(worktree)])
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(path.exists())

    # -- reminders ---------------------------------------------------------------

    def test_reminder_prefix_match_and_common_dir_fallback(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        self.run_hook(self.payload(merge_command))

        inside = worktree / "sub"
        inside.mkdir()
        prefix_result = self.run_hook({
            "hook_event_name": "UserPromptSubmit", "cwd": str(inside), "session_id": "s9",
        })
        self.assertEqual(0, prefix_result.returncode, prefix_result.stderr)
        context = json.loads(prefix_result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("PR #3", context)

        sibling_worktree = add_feature_worktree(primary, self.root, "sibling")
        fallback_result = self.run_hook({
            "hook_event_name": "SessionStart", "cwd": str(sibling_worktree), "session_id": "s9",
        })
        self.assertEqual(0, fallback_result.returncode, fallback_result.stderr)
        context = json.loads(fallback_result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("PR #3", context)

        elsewhere = self.root / "unrelated"
        elsewhere.mkdir()
        no_match = self.run_hook({
            "hook_event_name": "UserPromptSubmit", "cwd": str(elsewhere), "session_id": "s9",
        })
        self.assertEqual(0, no_match.returncode, no_match.stderr)
        self.assertEqual("", no_match.stdout.strip())

    # -- fail-open --------------------------------------------------------------

    def test_fail_open_on_garbage_stdin(self):
        result = subprocess.run(
            [sys.executable, "-B", str(HOOK)], input=b"{not json", capture_output=True,
            env=self.env, timeout=20,
        )
        self.assertEqual(0, result.returncode)

    def test_fail_open_on_unwritable_state_directory(self):
        blocked = self.root / "blocked-state-file"
        blocked.write_text("not a directory", encoding="utf-8")
        env = dict(self.env, AGENT_STATE_DIRECTORY=str(blocked))
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        result = self.run_hook(self.payload(command), env=env)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_fail_open_on_missing_git(self):
        stripped = dict(self.env)
        stripped["PATH"] = str(self.root / "no-such-bin")
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        command = f'pushd "{worktree}" && gh pr merge 3 --squash'
        result = self.run_hook(self.payload(command), env=stripped)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_fail_open_through_real_codex_adapter_with_garbage_stdin_and_unwritable_state(self):
        blocked = self.root / "blocked-state-file-adapter"
        blocked.write_text("not a directory", encoding="utf-8")
        env = dict(self.env, AGENT_STATE_DIRECTORY=str(blocked))
        process = subprocess.run(
            [sys.executable, "-B", str(ADAPTER), "--timeout", "8", str(HOOK)],
            input=b"{garbage", capture_output=True, env=env, timeout=20,
        )
        self.assertEqual(0, process.returncode, process.stderr)


if __name__ == "__main__":
    unittest.main()
