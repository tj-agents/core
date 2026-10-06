import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "engineering/workflow/merge/scripts/cleanup_proof.py"


def git(cwd, *args, check=True):
    result = subprocess.run(
        ["git", "-C", str(cwd), *args], capture_output=True, text=True,
    )
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


def add_feature_worktree(primary, root, branch, base_ref="main", commits=2):
    git(primary, "branch", branch, base_ref)
    worktree = root / (branch + "-wt")
    git(primary, "worktree", "add", "-q", str(worktree), branch)
    for index in range(commits):
        (worktree / f"file{index}.txt").write_text(f"change {index}\n", encoding="utf-8")
        git(worktree, "add", ".")
        git(worktree, "commit", "-q", "-m", f"feature commit {index}")
    git(worktree, "push", "-q", "-u", "origin", branch)
    return worktree


def squash_merge(primary, branch):
    git(primary, "checkout", "-q", "main")
    git(primary, "merge", "-q", "--squash", branch)
    git(primary, "commit", "-q", "-m", "squash merge " + branch)
    merge_oid = git(primary, "rev-parse", "HEAD")
    git(primary, "push", "-q", "origin", "main")
    return merge_oid


def merge_commit_merge(primary, branch):
    git(primary, "checkout", "-q", "main")
    git(primary, "merge", "-q", "--no-ff", "-m", "merge " + branch, branch)
    merge_oid = git(primary, "rev-parse", "HEAD")
    git(primary, "push", "-q", "origin", "main")
    return merge_oid


def rebase_merge(primary, worktree, branch):
    git(worktree, "rebase", "main")
    new_head = git(worktree, "rev-parse", "HEAD")
    git(primary, "checkout", "-q", "main")
    git(primary, "merge", "-q", "--ff-only", branch)
    merge_oid = git(primary, "rev-parse", "HEAD")
    git(primary, "push", "-q", "origin", "main")
    git(worktree, "push", "-q", "--force", "origin", branch)
    return merge_oid, new_head


def write_fixture(path, pr_view, open_prs=None, pr_for_branch=None):
    path.write_text(
        json.dumps({
            "pr_view": pr_view,
            "open_prs": open_prs if open_prs is not None else [],
            "pr_for_branch": pr_for_branch,
        }),
        encoding="utf-8",
    )


def write_obligation(state_dir, worktree, pr):
    digest = hashlib.sha256(Path(worktree).resolve().as_posix().encode("utf-8")).hexdigest()
    path = Path(state_dir) / "merge-cleanup" / "obligations" / f"{digest}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pr": pr}), encoding="utf-8")


class CleanupProofTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.state = tempfile.TemporaryDirectory()
        self.addCleanup(self.state.cleanup)

    def fixture_path(self, name="fixture.json"):
        return self.root / name

    def run_proof(self, primary, worktree, branch, head, pr, default="main", fixture=None, pass_default=True):
        env = dict(os.environ, AGENT_STATE_DIRECTORY=self.state.name)
        if fixture is not None:
            env["CLEANUP_PROOF_FORGE_FIXTURE"] = str(fixture)
        args = [
            sys.executable, str(SCRIPT),
            "--worktree", str(worktree), "--branch", branch, "--head", head, "--pr", str(pr),
        ]
        if pass_default:
            args += ["--default", default]
        return subprocess.run(args, cwd=str(primary), capture_output=True, text=True, env=env)

    def run_proof_bare(self, worktree, fixture=None):
        env = dict(os.environ, AGENT_STATE_DIRECTORY=self.state.name)
        if fixture is not None:
            env["CLEANUP_PROOF_FORGE_FIXTURE"] = str(fixture)
        return subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=str(worktree), capture_output=True, text=True, env=env,
        )

    def run_commands(self, stdout):
        for line in stdout.strip().splitlines()[1:]:
            result = subprocess.run(line, shell=True, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_squash_merge_proof_selects_capital_d_and_the_commands_clean_up(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = squash_merge(primary, "feature")

        self.assertNotEqual(0, subprocess.run(
            ["git", "-C", str(primary), "branch", "-d", "feature"],
            capture_output=True, text=True,
        ).returncode)

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))
        self.assertIn("branch -D feature", result.stdout)

        self.run_commands(result.stdout)

        self.assertFalse(worktree.exists())
        porcelain = git(primary, "worktree", "list", "--porcelain")
        self.assertNotIn(str(worktree), porcelain)
        self.assertEqual(
            1,
            subprocess.run(
                ["git", "-C", str(primary), "show-ref", "--verify", "--quiet", "refs/heads/feature"],
                capture_output=True, text=True,
            ).returncode,
        )

    def test_merge_commit_variant_passes(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))
        self.assertIn("branch -d feature", result.stdout)

    def test_rebase_variant_passes(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_oid, head = rebase_merge(primary, worktree, "feature")

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))

    def test_default_resolves_from_origin_head_when_omitted(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, pass_default=False)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))

    def test_a_dirty_worktree_preserves_and_removes_nothing(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")
        (worktree / "untracked.txt").write_text("dirty\n", encoding="utf-8")

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertTrue(worktree.exists())
        self.assertEqual(
            0,
            subprocess.run(
                ["git", "-C", str(primary), "show-ref", "--verify", "--quiet", "refs/heads/feature"],
                capture_output=True, text=True,
            ).returncode,
        )

    def test_a_head_ref_oid_mismatch_preserves(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": "0" * 40, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertTrue(worktree.exists())

    def test_a_merge_commit_absent_from_default_preserves(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        squash_merge(primary, "feature")

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": head}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertTrue(worktree.exists())

    def test_an_open_pr_for_the_head_preserves(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            open_prs=[{"number": 99}],
        )
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertTrue(worktree.exists())

    def test_the_primary_on_another_branch_keeps_its_head(self):
        bare, primary = init_repo(self.root)
        git(primary, "checkout", "-q", "-b", "other")
        main_worktree = self.root / "main-wt"
        git(primary, "worktree", "add", "-q", str(main_worktree), "main")
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(main_worktree, "feature")

        branch_before = git(primary, "symbolic-ref", "--short", "HEAD")
        head_before = git(primary, "rev-parse", "HEAD")

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))
        self.assertEqual(branch_before, git(primary, "symbolic-ref", "--short", "HEAD"))
        self.assertEqual(head_before, git(primary, "rev-parse", "HEAD"))

    def test_argument_less_operation_derives_everything_from_the_worktree(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            pr_for_branch=7,
        )
        result = self.run_proof_bare(worktree, fixture=fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))
        self.assertIn("worktree remove", result.stdout)

    def test_argument_less_operation_preserves_on_obligation_pr_mismatch(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")
        write_obligation(self.state.name, worktree, pr=99)

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            pr_for_branch=7,
        )
        result = self.run_proof_bare(worktree, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertIn("obligation", result.stdout)
        self.assertTrue(worktree.exists())


if __name__ == "__main__":
    unittest.main()
