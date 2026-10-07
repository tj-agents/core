import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


HOOKS = Path(__file__).resolve().parents[1]
HOOK = HOOKS / "harness_grant.py"
sys.path.insert(0, str(HOOKS))

import hook_runtime  # noqa: E402


def run_git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


class TrustTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        run_git(self.root, "init", "-q")

    def owner_of(self, url):
        subprocess.run(["git", "-C", str(self.root), "remote", "remove", "origin"], capture_output=True)
        run_git(self.root, "remote", "add", "origin", url)
        return hook_runtime.origin_owner(self.root)

    def test_every_github_remote_form_yields_its_owner(self):
        self.assertEqual("tj-agents", self.owner_of("https://github.com/tj-agents/core.git"))
        self.assertEqual("tj-agents", self.owner_of("git@github.com:tj-agents/core.git"))
        self.assertEqual("tj-agents", self.owner_of("ssh://git@github.com/tj-agents/core"))
        self.assertEqual("tomjseery", self.owner_of("https://token@github.com/TomJSeery/x/"))

    def test_another_host_has_no_owner(self):
        self.assertIsNone(self.owner_of("https://gitlab.com/tj-agents/core.git"))
        self.assertIsNone(self.owner_of("https://github.com.evil.io/tj-agents/core.git"))

    def test_no_origin_has_no_owner(self):
        self.assertIsNone(hook_runtime.origin_owner(self.root))

    def test_the_shipped_list_trusts_personal_owners_only(self):
        owners = hook_runtime.trusted_owners(HOOK)

        self.assertIn("tj-agents", owners)
        self.assertIn("concertable", owners)
        self.assertNotIn("infonetica", owners)

    def test_a_missing_or_malformed_list_trusts_nothing(self):
        stray = self.root / "hook.py"
        self.assertEqual(frozenset(), hook_runtime.trusted_owners(stray))
        (self.root / hook_runtime.TRUST_FILE).write_text("{not json", encoding="utf-8")
        self.assertEqual(frozenset(), hook_runtime.trusted_owners(stray))
        (self.root / hook_runtime.TRUST_FILE).write_text('{"trusted_owners": "x"}', encoding="utf-8")
        self.assertEqual(frozenset(), hook_runtime.trusted_owners(stray))


class HarnessGrantTests(unittest.TestCase):
    """A repo whose origin/main already contains `merged`, with `feature` checked out."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.root = base / "repo"
        self.root.mkdir()
        run_git(self.root, "init", "-q", "-b", "main")
        run_git(self.root, "config", "user.email", "t@example.com")
        run_git(self.root, "config", "user.name", "t")
        run_git(self.root, "commit", "-q", "--allow-empty", "-m", "base")
        run_git(self.root, "branch", "merged")
        run_git(self.root, "commit", "-q", "--allow-empty", "-m", "on main")
        run_git(self.root, "remote", "add", "origin", "https://github.com/tj-agents/sample.git")
        run_git(self.root, "update-ref", "refs/remotes/origin/main", "HEAD")
        run_git(self.root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        run_git(self.root, "branch", "unmerged")
        run_git(self.root, "checkout", "-q", "unmerged")
        run_git(self.root, "commit", "-q", "--allow-empty", "-m", "not on main")
        run_git(self.root, "checkout", "-q", "-b", "feature")
        self.merged_tree = base / "merged-tree"
        self.unmerged_tree = base / "unmerged-tree"
        run_git(self.root, "worktree", "add", "-q", "--detach", str(self.merged_tree), "merged")
        run_git(self.root, "worktree", "add", "-q", "--detach", str(self.unmerged_tree), "unmerged")

    def run_hook(self, command, tool="Bash", codex=False, env=None):
        payload = {"tool_name": tool, "cwd": str(self.root), "tool_input": {"command": command}}
        if codex:
            payload["turn_id"] = "t1"
        return subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
            env=env,
        )

    def assert_granted(self, command, **kwargs):
        result = self.run_hook(command, **kwargs)
        self.assertEqual(0, result.returncode, result.stderr)
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("allow", decision["permissionDecision"])

    def assert_not_granted(self, command, **kwargs):
        result = self.run_hook(command, **kwargs)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def git_c(self, rest):
        return 'git -C "' + str(self.root) + '" ' + rest

    def test_syncing_a_feature_branch_with_its_base_is_granted(self):
        self.assert_granted(self.git_c("merge --no-edit origin/main"))

    def test_powershell_receives_the_same_grant(self):
        self.assert_granted(self.git_c("merge --no-edit origin/main"), tool="PowerShell")

    def test_syncing_while_on_the_default_branch_is_not_granted(self):
        run_git(self.root, "checkout", "-q", "main")
        self.assert_not_granted(self.git_c("merge --no-edit origin/main"))

    def test_merging_anything_but_the_default_is_not_granted(self):
        self.assert_not_granted(self.git_c("merge --no-edit origin/feature"))
        self.assert_not_granted(self.git_c("merge origin/main"))

    def test_an_untrusted_or_foreign_origin_is_not_granted(self):
        run_git(self.root, "remote", "set-url", "origin", "https://github.com/Infonetica/sample.git")
        self.assert_not_granted(self.git_c("merge --no-edit origin/main"))
        run_git(self.root, "remote", "set-url", "origin", "https://gitlab.com/tj-agents/sample.git")
        self.assert_not_granted(self.git_c("merge --no-edit origin/main"))

    def test_a_compound_command_is_never_granted(self):
        self.assert_not_granted(self.git_c("merge --no-edit origin/main") + " && echo hi")
        self.assert_not_granted("cd x && " + self.git_c("merge --no-edit origin/main"))
        self.assert_not_granted(self.git_c("merge --no-edit origin/main") + "; rm -rf x")

    def test_an_unquoted_relative_or_unsafe_path_is_not_granted(self):
        self.assert_not_granted("git -C " + str(self.root) + " merge --no-edit origin/main")
        self.assert_not_granted('git -C "repo" merge --no-edit origin/main')
        self.assert_not_granted('git -C "' + str(self.root) + '$x" merge --no-edit origin/main')

    def test_codex_is_not_granted(self):
        self.assert_not_granted(self.git_c("merge --no-edit origin/main"), codex=True)

    def test_removing_a_merged_linked_worktree_is_granted(self):
        self.assert_granted(self.git_c('worktree remove -- "' + str(self.merged_tree) + '"'))

    def test_removing_an_unmerged_worktree_is_not_granted(self):
        self.assert_not_granted(self.git_c('worktree remove -- "' + str(self.unmerged_tree) + '"'))

    def test_removing_the_main_worktree_or_forcing_is_not_granted(self):
        self.assert_not_granted(self.git_c('worktree remove -- "' + str(self.root) + '"'))
        self.assert_not_granted(
            self.git_c('worktree remove --force -- "' + str(self.merged_tree) + '"')
        )

    def test_deleting_a_merged_branch_is_granted(self):
        self.assert_granted(self.git_c("branch -d merged"))

    def test_deleting_an_unmerged_default_or_missing_branch_is_not_granted(self):
        self.assert_not_granted(self.git_c("branch -d unmerged"))
        self.assert_not_granted(self.git_c("branch -d main"))
        self.assert_not_granted(self.git_c("branch -d nowhere"))
        self.assert_not_granted(self.git_c("branch -D merged"))

    def test_other_tools_and_commands_are_ignored(self):
        self.assert_not_granted(self.git_c("merge --no-edit origin/main"), tool="Edit")
        self.assert_not_granted("git status")


class ReceiptGrantTests(unittest.TestCase):
    """A squash-merge-shaped branch: not an ancestor of origin/main, so only a receipt helps."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.root = base / "repo"
        self.root.mkdir()
        run_git(self.root, "init", "-q", "-b", "main")
        run_git(self.root, "config", "user.email", "t@example.com")
        run_git(self.root, "config", "user.name", "t")
        run_git(self.root, "commit", "-q", "--allow-empty", "-m", "base")
        run_git(self.root, "remote", "add", "origin", "https://github.com/tj-agents/sample.git")
        run_git(self.root, "update-ref", "refs/remotes/origin/main", "HEAD")
        run_git(self.root, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        run_git(self.root, "branch", "squashed")
        run_git(self.root, "checkout", "-q", "squashed")
        run_git(self.root, "commit", "-q", "--allow-empty", "-m", "squashed away")
        self.head = run_git(self.root, "rev-parse", "HEAD")
        run_git(self.root, "checkout", "-q", "main")
        self.squashed_tree = base / "squashed-tree"
        run_git(self.root, "worktree", "add", "-q", str(self.squashed_tree), "squashed")

        self.state = tempfile.TemporaryDirectory()
        self.addCleanup(self.state.cleanup)
        self.env = dict(os.environ, AGENT_STATE_DIRECTORY=self.state.name)

    def write_receipt(self, worktree, branch, head, verdict="removable", age_seconds=0):
        directory = Path(self.state.name) / "merge-cleanup" / "receipts"
        directory.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(Path(worktree).resolve().as_posix().encode("utf-8")).hexdigest()
        data = {
            "worktree": str(Path(worktree).resolve()),
            "branch": branch,
            "head": head,
            "verdict": verdict,
            "recorded_at": time.time() - age_seconds,
        }
        (directory / f"{digest}.json").write_text(json.dumps(data), encoding="utf-8")

    def run_hook(self, command, tool="Bash", env=None):
        payload = {"tool_name": tool, "cwd": str(self.root), "tool_input": {"command": command}}
        return subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
            env=self.env if env is None else env,
        )

    def assert_granted(self, command, **kwargs):
        result = self.run_hook(command, **kwargs)
        self.assertEqual(0, result.returncode, result.stderr)
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("allow", decision["permissionDecision"])

    def assert_not_granted(self, command, **kwargs):
        result = self.run_hook(command, **kwargs)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def git_c(self, rest):
        return 'git -C "' + str(self.root) + '" ' + rest

    def test_removing_a_worktree_with_a_fresh_matching_receipt_is_granted(self):
        self.write_receipt(self.squashed_tree, "squashed", self.head)
        self.assert_granted(self.git_c('worktree remove -- "' + str(self.squashed_tree) + '"'))

    def test_deleting_with_d_or_capital_d_is_granted_by_a_fresh_matching_receipt(self):
        self.write_receipt(self.squashed_tree, "squashed", self.head)
        self.assert_granted(self.git_c("branch -d squashed"))
        self.assert_granted(self.git_c("branch -D squashed"))

    def test_a_stale_receipt_is_not_granted(self):
        self.write_receipt(self.squashed_tree, "squashed", self.head, age_seconds=60 * 60 + 1)
        self.assert_not_granted(self.git_c('worktree remove -- "' + str(self.squashed_tree) + '"'))
        self.assert_not_granted(self.git_c("branch -D squashed"))

    def test_a_head_mismatched_receipt_is_not_granted(self):
        self.write_receipt(self.squashed_tree, "squashed", "0" * 40)
        self.assert_not_granted(self.git_c('worktree remove -- "' + str(self.squashed_tree) + '"'))
        self.assert_not_granted(self.git_c("branch -D squashed"))

    def test_an_absent_receipt_is_not_granted(self):
        self.assert_not_granted(self.git_c('worktree remove -- "' + str(self.squashed_tree) + '"'))
        self.assert_not_granted(self.git_c("branch -D squashed"))

    def test_a_preserve_verdict_receipt_is_not_granted(self):
        self.write_receipt(self.squashed_tree, "squashed", self.head, verdict="preserve")
        self.assert_not_granted(self.git_c('worktree remove -- "' + str(self.squashed_tree) + '"'))
        self.assert_not_granted(self.git_c("branch -D squashed"))


if __name__ == "__main__":
    unittest.main()
