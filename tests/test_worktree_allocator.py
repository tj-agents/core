import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/engineering/operation/open-worktree/scripts/worktrees.py"
ALLOCATOR_SPEC = importlib.util.spec_from_file_location("worktrees", SCRIPT)
ALLOCATOR = importlib.util.module_from_spec(ALLOCATOR_SPEC)
ALLOCATOR_SPEC.loader.exec_module(ALLOCATOR)


def run(command, cwd=None, env=None, check=True):
    return subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=check)


def git(cwd, *args):
    result = run(["git", *args], cwd=cwd)
    return result.stdout.strip()


class WorktreeAllocatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="worktree allocator ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.seed = self.root / "seed"
        self.primary = self.root / "primary"
        git(self.root, "init", "--bare", str(self.remote))
        self.seed.mkdir()
        git(self.seed, "init", "-b", "main")
        git(self.seed, "config", "user.email", "test@example.com")
        git(self.seed, "config", "user.name", "Test")
        (self.seed / "README.md").write_text("one\n", encoding="utf-8")
        git(self.seed, "add", "README.md")
        git(self.seed, "commit", "-m", "initial")
        git(self.seed, "remote", "add", "origin", str(self.remote))
        git(self.seed, "push", "-u", "origin", "main")
        git(self.remote, "symbolic-ref", "HEAD", "refs/heads/main")
        git(self.root, "clone", str(self.remote), str(self.primary))
        git(self.primary, "config", "user.email", "test@example.com")
        git(self.primary, "config", "user.name", "Test")

    def invoke(self, repository, branch, *extra, script=SCRIPT, env=None):
        command = [sys.executable, "-B", str(script), "create", "--repository", str(repository), "--branch", branch, *extra]
        result = run(command, env=env, check=False)
        if result.returncode:
            return result, None
        return result, json.loads(result.stdout)

    def advance(self, branch="main"):
        path = self.seed / f"{branch.replace('/', '-')}.txt"
        path.write_text((path.read_text(encoding="utf-8") if path.exists() else path.name + "\n") + "advance\n", encoding="utf-8")
        git(self.seed, "add", path.name)
        git(self.seed, "commit", "-m", "advance " + branch)
        git(self.seed, "push", "origin", branch)
        return git(self.seed, "rev-parse", "HEAD")

    def push_branch(self, branch):
        git(self.seed, "checkout", "-b", branch)
        head = self.advance(branch)
        git(self.seed, "checkout", "main")
        return head

    def test_primary_uses_fetched_remote_default_and_sanitizes_git_selectors(self):
        expected = self.advance()
        env = dict(os.environ, GIT_DIR=str(self.root / "hostile-git-dir"))
        result, payload = self.invoke(self.primary, "Feature/FetchedDefault", env=env)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(expected, payload["head"])
        self.assertEqual("refs/remotes/origin/main", payload["base_ref"])
        self.assertTrue(payload["created"])
        self.assertTrue(os.path.samefile(self.primary / ".worktrees/Feature-FetchedDefault", payload["worktree"]))

    def test_linked_caller_with_relative_registration_allocates_under_common_root(self):
        linked = self.root / "nested/linked"
        linked.parent.mkdir()
        result = run(["git", "worktree", "add", "--relative-paths", "-b", "Fix/Caller", str(linked)], cwd=self.primary, check=False)
        if result.returncode:
            self.skipTest("Git does not support relative worktree registrations")
        result, payload = self.invoke(linked, "Feature/FromLinked")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(os.path.samefile(self.primary, payload["repository"]))
        self.assertTrue(os.path.samefile(self.primary / ".worktrees/Feature-FromLinked", payload["worktree"]))

    def test_stack_parent_is_fetched_and_expected_base_binds_it(self):
        parent = self.push_branch("Feature/Parent")
        git(self.primary, "config", "remote.origin.fetch", "+refs/heads/main:refs/remotes/origin/main")
        result, payload = self.invoke(self.primary, "Feature/Child", "--base", "Feature/Parent", "--expected-base", parent)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(parent, payload["base_head"])
        mismatch, _ = self.invoke(self.primary, "Feature/Mismatch", "--base", "Feature/Parent", "--expected-base", "0" * 40)
        self.assertNotEqual(0, mismatch.returncode)
        self.assertIn("--expected-base", mismatch.stderr)

    def test_explicit_base_does_not_require_a_symbolic_remote_head(self):
        git(self.remote, "symbolic-ref", "HEAD", "refs/heads/missing")
        result, payload = self.invoke(self.primary, "Feature/ExplicitBase", "--base", "main")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("refs/remotes/origin/main", payload["base_ref"])

    def test_non_main_remote_default_is_used_when_no_base_is_supplied(self):
        head = self.push_branch("Feature/Default")
        git(self.remote, "symbolic-ref", "HEAD", "refs/heads/Feature/Default")
        result, payload = self.invoke(self.primary, "Feature/RemoteDefault")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(head, payload["base_head"])
        self.assertEqual("refs/remotes/origin/Feature/Default", payload["base_ref"])

    def test_existing_local_and_remote_branches_restore_only_with_exact_head(self):
        local_head = git(self.primary, "rev-parse", "HEAD")
        git(self.primary, "branch", "Fix/Local")
        result, payload = self.invoke(self.primary, "Fix/Local", "--existing", "--expected-head", local_head)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("refs/heads/Fix/Local", payload["base_ref"])
        remote_head = self.push_branch("Fix/Remote")
        before = git(self.primary, "config", "--get-all", "remote.origin.fetch").splitlines()
        result, payload = self.invoke(self.primary, "Fix/Remote", "--existing", "--expected-head", remote_head)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("refs/remotes/origin/Fix/Remote", payload["base_ref"])
        self.assertEqual(before, git(self.primary, "config", "--get-all", "remote.origin.fetch").splitlines())
        mismatch, _ = self.invoke(self.primary, "Fix/Other", "--existing", "--expected-head", remote_head)
        self.assertNotEqual(0, mismatch.returncode)

    def test_remote_restoration_adds_exact_fetch_mapping_and_sets_upstream(self):
        remote_head = self.push_branch("Fix/NarrowRemote")
        git(self.primary, "config", "--unset-all", "remote.origin.fetch")
        git(self.primary, "config", "--add", "remote.origin.fetch", "+refs/heads/main:refs/remotes/origin/main")
        before = git(self.primary, "config", "--get-all", "remote.origin.fetch").splitlines()
        result, payload = self.invoke(self.primary, "Fix/NarrowRemote", "--existing", "--expected-head", remote_head)
        self.assertEqual(0, result.returncode, result.stderr)
        after = git(self.primary, "config", "--get-all", "remote.origin.fetch").splitlines()
        self.assertEqual(before, [spec for spec in after if spec in before])
        self.assertEqual(1, after.count("+refs/heads/Fix/NarrowRemote:refs/remotes/origin/Fix/NarrowRemote"))
        self.assertEqual("origin/Fix/NarrowRemote", git(payload["worktree"], "rev-parse", "--abbrev-ref", "@{upstream}"))
        git(self.seed, "checkout", "Fix/NarrowRemote")
        advanced = self.advance("Fix/NarrowRemote")
        git(self.seed, "checkout", "main")
        git(self.primary, "fetch", "origin")
        self.assertEqual(advanced, git(self.primary, "rev-parse", "refs/remotes/origin/Fix/NarrowRemote"))

    def test_remote_restoration_refuses_negative_fetch_exclusion_before_creation(self):
        for branch, exclusion in (
            ("Fix/ExcludedWildcard", "^refs/heads/Fix/Excluded*"),
            ("Fix/ExcludedExact", "^refs/heads/Fix/ExcludedExact"),
        ):
            with self.subTest(exclusion=exclusion):
                remote_head = self.push_branch(branch)
                git(self.primary, "config", "--unset-all", "remote.origin.fetch")
                git(self.primary, "config", "--add", "remote.origin.fetch", "+refs/heads/main:refs/remotes/origin/main")
                git(self.primary, "config", "--add", "remote.origin.fetch", exclusion)
                before = git(self.primary, "config", "--get-all", "remote.origin.fetch").splitlines()
                result, _ = self.invoke(self.primary, branch, "--existing", "--expected-head", remote_head)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("excludes", result.stderr)
                self.assertEqual(before, git(self.primary, "config", "--get-all", "remote.origin.fetch").splitlines())
                self.assertFalse((self.primary / ".worktrees" / branch.replace("/", "-")).exists())
                local = run(["git", "show-ref", "--verify", "--quiet", "refs/heads/" + branch], cwd=self.primary, check=False)
                self.assertNotEqual(0, local.returncode)

    def test_registered_and_flattened_or_case_collisions_refuse(self):
        created, _ = self.invoke(self.primary, "Feature/A-B")
        self.assertEqual(0, created.returncode, created.stderr)
        registered, _ = self.invoke(self.primary, "Feature/A-B")
        self.assertNotEqual(0, registered.returncode)
        flattened, _ = self.invoke(self.primary, "Feature/A/B")
        self.assertNotEqual(0, flattened.returncode)
        self.push_branch("Feature/Case")
        casing, _ = self.invoke(self.primary, "Feature/case")
        self.assertNotEqual(0, casing.returncode)

    def test_refuses_tracked_worktree_path_and_existing_lock(self):
        tracked = self.primary / ".worktrees/owned.txt"
        tracked.parent.mkdir()
        tracked.write_text("owned\n", encoding="utf-8")
        git(self.primary, "add", ".worktrees/owned.txt")
        git(self.primary, "commit", "-m", "tracked worktree path")
        result, _ = self.invoke(self.primary, "Feature/Tracked")
        self.assertNotEqual(0, result.returncode)
        git(self.primary, "rm", "-r", ".worktrees")
        git(self.primary, "commit", "-m", "remove tracked worktree path")
        common = Path(git(self.primary, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        lock = common / "agent-worktree-allocation.lock"
        lock.write_text("{}", encoding="utf-8")
        self.addCleanup(lambda: lock.unlink(missing_ok=True))
        result, _ = self.invoke(self.primary, "Feature/Locked")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("lock", result.stderr)

    def test_refuses_empty_target_registered_missing_target_and_negated_ignore(self):
        empty = self.primary / ".worktrees/Feature-Empty"
        empty.parent.mkdir()
        empty.mkdir()
        result, _ = self.invoke(self.primary, "Feature/Empty")
        self.assertNotEqual(0, result.returncode)
        shutil.rmtree(empty)
        created, _ = self.invoke(self.primary, "Feature/Missing")
        self.assertEqual(0, created.returncode, created.stderr)
        shutil.rmtree(self.primary / ".worktrees/Feature-Missing")
        missing, _ = self.invoke(self.primary, "Feature/Missing")
        self.assertNotEqual(0, missing.returncode)
        git(self.primary, "checkout", "--", ".gitignore") if (self.primary / ".gitignore").exists() else None
        (self.primary / ".gitignore").write_text("!/.worktrees/\n", encoding="utf-8")
        git(self.primary, "add", ".gitignore")
        git(self.primary, "commit", "-m", "negate worktree exclusion")
        negated, _ = self.invoke(self.primary, "Feature/Negated")
        self.assertNotEqual(0, negated.returncode)
        self.assertIn("not ignored", negated.stderr)

    def test_refuses_symlinked_worktree_root_when_supported(self):
        outside = self.root / "outside"
        outside.mkdir()
        try:
            (self.primary / ".worktrees").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("The current Windows environment cannot create directory symlinks")
        result, _ = self.invoke(self.primary, "Feature/Symlink")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("worktrees", result.stderr)

    def test_refuses_in_root_junction_when_supported(self):
        if os.name != "nt":
            self.skipTest("Junctions are a Windows filesystem feature")
        outside = self.primary / "junction-target"
        outside.mkdir()
        junction = self.primary / ".worktrees"
        command = "New-Item -ItemType Junction -Path '" + str(junction) + "' -Target '" + str(outside) + "'"
        created = run(["powershell", "-NoProfile", "-Command", command], check=False)
        if created.returncode:
            self.skipTest("The current Windows environment cannot create junctions")
        result, _ = self.invoke(self.primary, "Feature/Junction")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("worktrees", result.stderr)

    def test_dirty_caller_and_post_add_failure_preserve_evidence(self):
        dirty = self.primary / "dirty.txt"
        dirty.write_text("preserve\n", encoding="utf-8")
        result, payload = self.invoke(self.primary, "Feature/DirtyCaller")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("preserve\n", dirty.read_text(encoding="utf-8"))
        args = type("Arguments", (), {
            "repository": str(self.primary), "branch": "Feature/PostAdd", "remote": "origin",
            "base": None, "expected_base": None, "existing": False, "expected_head": None,
        })()
        with mock.patch.object(ALLOCATOR, "verify", side_effect=ALLOCATOR.Refusal("post-add failure")):
            with self.assertRaisesRegex(ALLOCATOR.Refusal, "post-add failure"):
                ALLOCATOR.create(args)
        self.assertTrue((self.primary / ".worktrees/Feature-PostAdd").is_dir())
        self.assertIn("Feature/PostAdd", git(self.primary, "branch", "--format=%(refname:short)"))

    def test_fetch_failure_and_invalid_inputs_leave_no_new_target(self):
        git(self.primary, "remote", "set-url", "origin", str(self.root / "missing.git"))
        failed, _ = self.invoke(self.primary, "Feature/FetchFailure")
        self.assertNotEqual(0, failed.returncode)
        self.assertFalse((self.primary / ".worktrees/Feature-FetchFailure").exists())
        git(self.primary, "remote", "set-url", "origin", str(self.remote))
        for branch, extra in (
            ("feature/lower", ()),
            ("Feature/ExistingWithBase", ("--existing", "--expected-head", "0" * 40, "--base", "main")),
            ("Feature/HeadWithoutExisting", ("--expected-head", "0" * 40)),
        ):
            with self.subTest(branch=branch):
                result, _ = self.invoke(self.primary, branch, *extra)
                self.assertNotEqual(0, result.returncode)

    def test_lock_release_refuses_a_replacement_lock(self):
        common = Path(git(self.primary, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        target = self.primary / ".worktrees/Feature-LockOwner"
        lock, token = ALLOCATOR.acquire_lock(common, "Feature/LockOwner", target)
        lock.unlink()
        lock.write_text('{"token":"replacement"}', encoding="utf-8")
        with self.assertRaises(ALLOCATOR.Refusal):
            ALLOCATOR.release_lock((lock, token))
        lock.unlink()

    def test_refuses_relocated_primary_git_directory(self):
        moved = self.root / "moved/.git"
        moved.parent.mkdir()
        shutil.move(str(self.primary / ".git"), str(moved))
        (self.primary / ".git").write_text("gitdir: ../moved/.git\n", encoding="utf-8")
        result, _ = self.invoke(self.primary, "Feature/Relocated")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("relocated", result.stderr)

    def test_generated_host_copies_run_outside_author_checkout(self):
        generated = self.root / "generated"
        for tree in ("skills", "codex-skills"):
            with self.subTest(tree=tree):
                consumer = self.root / ("consumer-" + tree)
                git(self.root, "clone", str(self.remote), str(consumer))
                script = generated / "plugins/engineering" / tree / "open-worktree/scripts/worktrees.py"
                script.parent.mkdir(parents=True, exist_ok=True)
                shipped = ROOT / "plugins/engineering" / tree / "open-worktree/scripts/worktrees.py"
                self.assertTrue(shipped.is_file())
                script.write_bytes(shipped.read_bytes())
                self.assertEqual(shipped.read_bytes(), script.read_bytes())
                result, payload = self.invoke(consumer, "Feature/Generated" + tree.title().replace("-", ""), script=script)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertTrue(os.path.samefile(consumer / ".worktrees" / payload["branch"].replace("/", "-"), payload["worktree"]))

    def test_unicode_consumer_path_has_registered_worktree_identity(self):
        consumer = self.root / "consumer-\u2603"
        git(self.root, "clone", str(self.remote), str(consumer))
        result, payload = self.invoke(consumer, "Feature/Unicode")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(os.path.samefile(consumer / ".worktrees/Feature-Unicode", payload["worktree"]))


if __name__ == "__main__":
    unittest.main()
