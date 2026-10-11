import hashlib
import io
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[2] / "engineering/workflow/merge/scripts/cleanup_proof.py"
SPEC = importlib.util.spec_from_file_location("cleanup_proof", SCRIPT)
CLEANUP_PROOF = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLEANUP_PROOF)


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


def write_fixture(path, pr_view, open_head_prs=None, open_base_prs=None, pr_for_branch=None):
    path.write_text(
        json.dumps({
            "pr_view": pr_view,
            "open_head_prs": open_head_prs if open_head_prs is not None else [],
            "open_base_prs": open_base_prs if open_base_prs is not None else [],
            "pr_for_branch": pr_for_branch,
        }),
        encoding="utf-8",
    )


def write_obligation(state_dir, worktree, pr):
    digest = hashlib.sha256(Path(worktree).resolve().as_posix().encode("utf-8")).hexdigest()
    path = Path(state_dir) / "merge-cleanup" / "obligations" / f"{digest}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pr": pr}), encoding="utf-8")


def write_string_obligation(state_dir, worktree, pr):
    digest = hashlib.sha256(Path(worktree).resolve().as_posix().encode("utf-8")).hexdigest()
    path = Path(state_dir) / "merge-cleanup" / "obligations" / f"{digest}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"pr": str(pr)}), encoding="utf-8")


def load_receipt(state_dir, worktree):
    digest = hashlib.sha256(Path(worktree).resolve().as_posix().encode("utf-8")).hexdigest()
    path = Path(state_dir) / "merge-cleanup" / "receipts" / f"{digest}.json"
    return json.loads(path.read_text(encoding="utf-8"))


class CleanupProofTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.state = tempfile.TemporaryDirectory()
        self.addCleanup(self.state.cleanup)

    def fixture_path(self, name="fixture.json"):
        return self.root / name

    def run_proof(self, primary, worktree, branch, head, pr, default="main", fixture=None, pass_default=True, repo=None):
        env = dict(os.environ, AGENT_STATE_DIRECTORY=self.state.name)
        if fixture is not None:
            env["CLEANUP_PROOF_FORGE_FIXTURE"] = str(fixture)
        branch_argument = ["--branch=" + branch] if branch.startswith("-") else ["--branch", branch]
        args = [
            sys.executable, str(SCRIPT),
            "--worktree", str(worktree), *branch_argument, "--head", head, "--pr", str(pr),
        ]
        if pass_default:
            args += ["--default", default]
        if repo is not None:
            args += ["--repo", repo]
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
            if "--delete-remote" in line:
                continue
            result = subprocess.run(line, shell=True, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)

    def run_remote_delete(self, worktree, branch, head, pr, default, merge_oid, evidence=None, view=None, repo=None):
        arguments = [
            "--delete-remote", "--worktree", str(worktree), "--branch", branch,
            "--head", head, "--pr", str(pr), "--default", default,
        ]
        if repo is not None:
            arguments += ["--repo", repo]
        output = io.StringIO()
        if evidence is None:
            evidence = {"head": [], "base": []}
        if view is None:
            view = {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}}
        observer = (
            mock.patch.object(CLEANUP_PROOF, "observe_open_prs", side_effect=evidence)
            if isinstance(evidence, Exception)
            else mock.patch.object(CLEANUP_PROOF, "observe_open_prs", return_value=evidence)
        )
        dependency = sys.modules["cleanup_dependency"]
        original_run = subprocess.run

        def run(command, *items, **kwargs):
            if command[:3] == ["git", "-C", str(worktree.parent / "primary")] and command[3:] == ["remote", "get-url", "origin"]:
                return subprocess.CompletedProcess(command, 0, "https://github.com/tj-agents/offline.git\n", "")
            return original_run(command, *items, **kwargs)

        with mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": self.state.name}):
            with mock.patch.object(dependency.subprocess, "run", side_effect=run):
                with mock.patch.object(CLEANUP_PROOF, "push_destination", return_value="origin"):
                    with mock.patch.object(CLEANUP_PROOF, "pr_view", return_value=view):
                        with observer:
                            with mock.patch("sys.stdout", output):
                                status = CLEANUP_PROOF.main(arguments)
        return status, output.getvalue()

    def removable_remote_fixture(self):
        case_root = Path(tempfile.mkdtemp(dir=self.root)).resolve()
        bare, primary = init_repo(case_root)
        worktree = add_feature_worktree(primary, case_root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = squash_merge(primary, "feature")
        fixture = case_root / "fixture.json"
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")
        self.assertEqual(0, result.returncode, result.stderr)
        lines = result.stdout.strip().splitlines()
        self.assertIn("--delete-remote", lines[1])
        self.assertIn("worktree remove", lines[2])
        self.assertIn("branch", lines[3])
        self.run_commands(result.stdout)
        return bare, primary, worktree, head, merge_oid

    def test_leading_dash_branch_preserves_without_commands(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")
        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})

        result = self.run_proof(primary, worktree, "-feature", head, 1, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertNotIn("worktree remove", result.stdout)
        self.assertNotIn("--delete-remote", result.stdout)
        self.assertTrue(worktree.exists())
        self.assertEqual(head, git(primary, "rev-parse", "refs/heads/feature"))

    def test_remote_delete_allows_a_fresh_removable_receipt_after_local_cleanup(self):
        bare, primary, worktree, head, merge_oid = self.removable_remote_fixture()

        status, output = self.run_remote_delete(worktree, "feature", head, 1, "main", merge_oid)

        self.assertEqual(0, status, output)
        self.assertEqual("remote-deleted\n", output)
        receipt = load_receipt(self.state.name, worktree)
        self.assertEqual("github.com/tj-agents/offline", receipt["remote_deleted"]["repo"])
        self.assertEqual(head, receipt["remote_deleted"]["head"])
        self.assertEqual(2, subprocess.run(
            ["git", "-C", str(primary), "ls-remote", "--exit-code", "origin", "refs/heads/feature"],
            capture_output=True, text=True,
        ).returncode)

    def test_remote_delete_preserves_with_a_nonfinite_receipt_timestamp(self):
        bare, primary, worktree, head, merge_oid = self.removable_remote_fixture()
        with mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": self.state.name}):
            path = CLEANUP_PROOF.receipt_path(worktree)
            receipt = json.loads(path.read_text(encoding="utf-8"))
            receipt["recorded_at"] = float("nan")
            path.write_text(json.dumps(receipt), encoding="utf-8")

        status, output = self.run_remote_delete(worktree, "feature", head, 1, "main", merge_oid)

        self.assertEqual(1, status)
        self.assertTrue(output.startswith("preserve:"))
        self.assertEqual(head, git(primary, "ls-remote", "origin", "refs/heads/feature").split()[0])

    def test_remote_delete_preserves_when_a_base_dependent_appears_after_receipt(self):
        bare, primary, worktree, head, merge_oid = self.removable_remote_fixture()

        status, output = self.run_remote_delete(
            worktree, "feature", head, 1, "main", merge_oid,
            evidence={"head": [], "base": [{"number": 99, "head_ref_name": "child", "head_ref_oid": "a" * 40}]},
        )

        self.assertEqual(1, status)
        self.assertTrue(output.startswith("preserve:"))
        self.assertEqual(head, git(primary, "ls-remote", "origin", "refs/heads/feature").split()[0])

    def test_remote_delete_preserves_when_remote_head_changes(self):
        bare, primary, worktree, head, merge_oid = self.removable_remote_fixture()
        git(bare, "update-ref", "refs/heads/feature", merge_oid)

        status, output = self.run_remote_delete(worktree, "feature", head, 1, "main", merge_oid)

        self.assertEqual(1, status)
        self.assertTrue(output.startswith("preserve:"))
        self.assertEqual(merge_oid, git(primary, "ls-remote", "origin", "refs/heads/feature").split()[0])

    def test_remote_delete_preserves_when_the_remote_changes_after_observation(self):
        bare, primary, worktree, head, merge_oid = self.removable_remote_fixture()
        original = CLEANUP_PROOF.remote_ref_matches

        def change_remote_after_observation(*arguments):
            matched = original(*arguments)
            git(bare, "update-ref", "refs/heads/feature", merge_oid)
            return matched

        with mock.patch.object(CLEANUP_PROOF, "remote_ref_matches", side_effect=change_remote_after_observation):
            status, output = self.run_remote_delete(worktree, "feature", head, 1, "main", merge_oid)

        self.assertEqual(1, status)
        self.assertTrue(output.startswith("preserve:"))
        self.assertEqual(merge_oid, git(primary, "ls-remote", "origin", "refs/heads/feature").split()[0])

    def test_remote_delete_preserves_on_malformed_or_failed_forge_evidence(self):
        for case in ("missing-merge", "wrong-head", "failed-dependency-query"):
            with self.subTest(case=case):
                bare, primary, worktree, head, merge_oid = self.removable_remote_fixture()
                if case == "missing-merge":
                    view = {"state": "MERGED", "headRefOid": head, "mergeCommit": None}
                    evidence = {"head": [], "base": []}
                elif case == "wrong-head":
                    view = {"state": "MERGED", "headRefOid": "0" * 40, "mergeCommit": {"oid": "bad"}}
                    evidence = {"head": [], "base": []}
                else:
                    view = {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}}
                    evidence = CLEANUP_PROOF.EvidenceError("failed evidence")
                status, output = self.run_remote_delete(
                    worktree, "feature", head, 1, "main", merge_oid, evidence=evidence, view=view,
                )
                self.assertEqual(1, status)
                self.assertTrue(output.startswith("preserve:"))
                self.assertEqual(head, git(primary, "ls-remote", "origin", "refs/heads/feature").split()[0])

    def test_remote_delete_preserves_for_a_different_supplied_repository(self):
        bare, primary, worktree, head, merge_oid = self.removable_remote_fixture()
        with mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": self.state.name}):
            path = CLEANUP_PROOF.receipt_path(worktree)
            receipt = json.loads(path.read_text(encoding="utf-8"))
            receipt["repo"] = "other/repository"
            path.write_text(json.dumps(receipt), encoding="utf-8")

        status, output = self.run_remote_delete(worktree, "feature", head, 1, "main", merge_oid, repo="other/repository")

        self.assertEqual(1, status)
        self.assertTrue(output.startswith("preserve:"))
        self.assertEqual(head, git(primary, "ls-remote", "origin", "refs/heads/feature").split()[0])

    def test_push_destination_rejects_foreign_or_multiple_destinations(self):
        for output in ("https://github.com/other/repository.git\n", "https://github.com/tj-agents/offline.git\nhttps://github.com/tj-agents/other.git\n"):
            with self.subTest(output=output), mock.patch.object(
                    CLEANUP_PROOF, "run_git", return_value=subprocess.CompletedProcess([], 0, output, ""),
            ):
                with self.assertRaises(CLEANUP_PROOF.Preserve):
                    CLEANUP_PROOF.push_destination(self.root, "github.com/tj-agents/offline")

    def test_push_destination_rejects_matching_git_rewrite_before_remote_access(self):
        primary = self.root / "primary"
        primary.mkdir()
        git(primary, "init", "-q")
        git(primary, "remote", "add", "origin", "https://github.com/tj-agents/core.git")
        original_run_git = CLEANUP_PROOF.run_git
        calls = []

        def run_git_with_rewrites(cwd, *args, **kwargs):
            calls.append(args)
            return original_run_git(
                cwd,
                "-c", "url.https://github.com/review-stage-one/.insteadOf=https://github.com/tj-agents/",
                "-c", "url.https://github.com/review-stage-two/.insteadOf=https://github.com/review-stage-one/",
                *args,
                **kwargs,
            )

        with mock.patch.object(CLEANUP_PROOF, "run_git", side_effect=run_git_with_rewrites):
            destination = CLEANUP_PROOF.run_git(primary, "remote", "get-url", "--push", "--all", "origin")
            self.assertEqual("https://github.com/review-stage-one/core.git\n", destination.stdout)
            rules = CLEANUP_PROOF.run_git(
                primary, "config", "-z", "--get-regexp", r"^url\..*\.(insteadof|pushinsteadof)$",
            )
            self.assertEqual(0, rules.returncode)
            self.assertIn("url.https://github.com/review-stage-one/.insteadof\n", rules.stdout)
            self.assertIn("url.https://github.com/review-stage-two/.insteadof\n", rules.stdout)
            calls.clear()
            with self.assertRaises(CLEANUP_PROOF.Preserve):
                CLEANUP_PROOF.push_destination(primary, "github.com/review-stage-one/core")
        self.assertEqual(
            [
                ("remote", "get-url", "--push", "--all", "origin"),
                ("config", "-z", "--get-regexp", r"^url\..*\.(insteadof|pushinsteadof)$"),
            ],
            calls,
        )
    def test_dependency_queries_use_checkout_github_repository_despite_ambient_overrides(self):
        dependency = sys.modules["cleanup_dependency"]
        calls = []

        def run(command, **kwargs):
            calls.append(command)
            if command[3:6] == ["remote", "get-url", "origin"]:
                return subprocess.CompletedProcess(command, 0, "git@github.com:tj-agents/offline.git\n", "")
            return subprocess.CompletedProcess(command, 0, "[]", "")

        with mock.patch.dict(os.environ, {"GH_REPO": "other/repository", "GH_HOST": "other.example"}), \
                mock.patch.object(dependency.subprocess, "run", side_effect=run):
            evidence = dependency.observe_open_prs("feature", cwd=self.root)
        self.assertEqual({"head": [], "base": []}, evidence)
        self.assertEqual("github.com/tj-agents/offline", calls[1][-1])
        self.assertEqual("github.com/tj-agents/offline", calls[2][-1])
    def test_remote_delete_requires_the_exact_option_name(self):
        bare, primary, worktree, head, merge_oid = self.removable_remote_fixture()

        with mock.patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit):
                CLEANUP_PROOF.main([
                    "--delete-rem", "--worktree", str(worktree), "--branch", "feature",
                    "--head", head, "--pr", "1", "--default", "main",
                ])

        self.assertEqual(head, git(primary, "ls-remote", "origin", "refs/heads/feature").split()[0])

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
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

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
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))
        self.assertIn("branch -d feature", result.stdout)

    def test_rebase_variant_passes(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        merge_oid, head = rebase_merge(primary, worktree, "feature")

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

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
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

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
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

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
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

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
            open_head_prs=[{"number": 99, "headRefName": "child", "headRefOid": "a" * 40}],
        )
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertTrue(worktree.exists())

    def test_an_open_base_dependent_retains_the_linked_branch_and_checkout(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            open_base_prs=[{"number": 99, "headRefName": "child", "headRefOid": "a" * 40}],
        )
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("retained-dependency"))
        self.assertTrue(worktree.exists())
        self.assertEqual(head, git(primary, "rev-parse", "refs/heads/feature"))
        receipt = load_receipt(self.state.name, worktree)
        self.assertEqual("retained-dependency", receipt["verdict"])
        self.assertEqual(
            [{"number": 99, "head_ref_name": "child", "head_ref_oid": "a" * 40}],
            receipt["dependencies"],
        )

    def test_primary_branch_route_uses_the_saved_branch_head_after_checkout_moves_to_main(self):
        bare, primary = init_repo(self.root)
        git(primary, "checkout", "-q", "-b", "feature")
        (primary / "feature.txt").write_text("feature\n", encoding="utf-8")
        git(primary, "add", "feature.txt")
        git(primary, "commit", "-q", "-m", "feature")
        git(primary, "push", "-q", "-u", "origin", "feature")
        head = git(primary, "rev-parse", "HEAD")
        merge_oid = squash_merge(primary, "feature")

        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}})
        result = self.run_proof(primary, primary, "feature", head, 1, fixture=fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))
        self.assertNotIn("worktree remove", result.stdout)
        self.assertIn("--delete-remote", result.stdout)
        self.run_commands(result.stdout)
        self.assertEqual(1, subprocess.run(
            ["git", "-C", str(primary), "show-ref", "--verify", "--quiet", "refs/heads/feature"],
            capture_output=True, text=True,
        ).returncode)

    def test_primary_branch_route_retains_a_saved_branch_with_an_open_base_dependent(self):
        bare, primary = init_repo(self.root)
        git(primary, "checkout", "-q", "-b", "feature")
        (primary / "feature.txt").write_text("feature\n", encoding="utf-8")
        git(primary, "add", "feature.txt")
        git(primary, "commit", "-q", "-m", "feature")
        git(primary, "push", "-q", "-u", "origin", "feature")
        head = git(primary, "rev-parse", "HEAD")
        merge_oid = squash_merge(primary, "feature")

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            open_base_prs=[{"number": 99, "headRefName": "child", "headRefOid": "a" * 40}],
        )
        result = self.run_proof(primary, primary, "feature", head, 1, fixture=fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("retained-dependency"))
        self.assertEqual(head, git(primary, "rev-parse", "refs/heads/feature"))

    def test_primary_branch_route_refuses_the_default_branch(self):
        bare, primary = init_repo(self.root)
        head = git(primary, "rev-parse", "HEAD")
        fixture = self.fixture_path()
        write_fixture(fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": head}})

        result = self.run_proof(primary, primary, "main", head, 1, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertIn("default branch", result.stdout)

    def test_missing_or_malformed_base_evidence_preserves(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")
        fixture = self.fixture_path()
        fixture.write_text(json.dumps({
            "pr_view": {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            "open_head_prs": [],
            "open_base_prs": {"number": 99},
        }), encoding="utf-8")

        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

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
        result = self.run_proof(primary, worktree, "feature", head, 1, fixture=fixture, repo="github.com/tj-agents/offline")

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

    def test_argument_less_operation_preserves_on_string_obligation_pr_mismatch(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")
        write_string_obligation(self.state.name, worktree, pr=99)

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

    def test_argument_less_set_aside_archives_dirt_and_is_removable(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        (worktree / "file0.txt").write_text("modified tracked\n", encoding="utf-8")
        (worktree / "staged.txt").write_text("staged new\n", encoding="utf-8")
        git(worktree, "add", "staged.txt")
        (worktree / "untracked.txt").write_bytes(b"dirty\n")

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            pr_for_branch=7,
        )
        result = self.run_proof_bare(worktree, fixture=fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))
        self.assertEqual("", git(worktree, "status", "--porcelain"))

        receipt = load_receipt(self.state.name, worktree)
        self.assertEqual("removable", receipt["verdict"])
        self.assertIsNotNone(receipt["set_aside"])
        archive = Path(receipt["set_aside"])
        self.assertTrue(archive.is_dir())
        set_aside_root = Path(self.state.name) / "merge-cleanup" / "set-aside"
        self.assertEqual([archive], list(set_aside_root.iterdir()))

        patch_text = (archive / "tracked.patch").read_text(encoding="utf-8")
        self.assertIn("file0.txt", patch_text)
        self.assertIn("staged.txt", patch_text)

        self.assertEqual(
            b"dirty\n", (archive / "untracked" / "untracked.txt").read_bytes(),
        )

        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({"untracked.txt"}, {entry["path"] for entry in manifest["untracked"]})
        self.assertIsNotNone(manifest["patch"])

        self.run_commands(result.stdout)
        self.assertFalse(worktree.exists())
        porcelain = git(primary, "worktree", "list", "--porcelain")
        self.assertNotIn(str(worktree), porcelain)

    def test_argument_less_unmerged_dirty_worktree_is_untouched(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_commit_merge(primary, "feature")

        (worktree / "file0.txt").write_text("modified tracked\n", encoding="utf-8")
        (worktree / "staged.txt").write_text("staged new\n", encoding="utf-8")
        git(worktree, "add", "staged.txt")
        (worktree / "untracked.txt").write_text("dirty\n", encoding="utf-8")

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "OPEN", "headRefOid": head, "mergeCommit": None},
            pr_for_branch=7,
        )
        result = self.run_proof_bare(worktree, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertEqual("modified tracked\n", (worktree / "file0.txt").read_text(encoding="utf-8"))
        self.assertEqual("staged new\n", (worktree / "staged.txt").read_text(encoding="utf-8"))
        self.assertEqual("dirty\n", (worktree / "untracked.txt").read_text(encoding="utf-8"))
        set_aside_root = Path(self.state.name) / "merge-cleanup" / "set-aside"
        self.assertFalse(set_aside_root.exists())
        self.assertTrue(worktree.exists())

    def test_argument_less_conflicted_worktree_preserves_and_archives_nothing(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        git(worktree, "checkout", "-q", "-b", "side", "HEAD~1")
        (worktree / "file1.txt").write_text("side change\n", encoding="utf-8")
        git(worktree, "add", "file1.txt")
        git(worktree, "commit", "-qm", "side")
        git(worktree, "checkout", "-q", "feature")
        (worktree / "file1.txt").write_text("feature change\n", encoding="utf-8")
        git(worktree, "commit", "-qam", "feature change")
        git(worktree, "merge", "side", check=False)
        self.assertIn("u ", git(worktree, "status", "--porcelain=v2"))
        head = git(worktree, "rev-parse", "HEAD")

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            pr_for_branch=7,
        )
        result = self.run_proof_bare(worktree, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertIn("unmerged paths", result.stdout)
        self.assertIn("<<<<<<<", (worktree / "file1.txt").read_text(encoding="utf-8"))
        set_aside_root = Path(self.state.name) / "merge-cleanup" / "set-aside"
        self.assertFalse(set_aside_root.exists())

    def test_argument_less_archive_failure_preserves_everything(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        (worktree / "file0.txt").write_text("modified tracked\n", encoding="utf-8")
        (worktree / "untracked.txt").write_text("dirty\n", encoding="utf-8")

        set_aside_root = Path(self.state.name) / "merge-cleanup" / "set-aside"
        set_aside_root.parent.mkdir(parents=True, exist_ok=True)
        set_aside_root.write_text("not a directory", encoding="utf-8")

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            pr_for_branch=7,
        )
        result = self.run_proof_bare(worktree, fixture=fixture)

        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stdout.startswith("preserve:"))
        self.assertEqual("modified tracked\n", (worktree / "file0.txt").read_text(encoding="utf-8"))
        self.assertEqual("dirty\n", (worktree / "untracked.txt").read_text(encoding="utf-8"))
        self.assertTrue(worktree.exists())

    def test_archive_failure_after_creation_records_its_directory(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        (worktree / "file0.txt").write_text("modified tracked\n", encoding="utf-8")
        records = CLEANUP_PROOF.status_entries(worktree)

        failure = subprocess.CompletedProcess([], 1, "", "reset failed")
        with mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": self.state.name}):
            with mock.patch.object(CLEANUP_PROOF, "run_git", return_value=failure):
                with self.assertRaises(CLEANUP_PROOF.Preserve) as raised:
                    CLEANUP_PROOF.set_aside(worktree, records, "feature", "head", 7)

        archive = Path(raised.exception.set_aside)
        self.assertTrue(archive.is_dir())
        self.assertTrue((archive / "manifest.json").is_file())

    def test_final_clean_failure_records_existing_archive(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")
        (worktree / "untracked.txt").write_text("dirty\n", encoding="utf-8")

        fixture = {
            "pr_view": {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            "open_head_prs": [],
            "open_base_prs": [],
        }
        args = CLEANUP_PROOF.argparse.Namespace(
            worktree=str(worktree), branch="feature", head=head, pr=7, default="main", repo=None,
        )
        previous_cwd = Path.cwd()
        try:
            os.chdir(worktree)
            with mock.patch.dict(os.environ, {"AGENT_STATE_DIRECTORY": self.state.name}):
                with mock.patch.object(CLEANUP_PROOF, "load_fixture", return_value=fixture):
                    with mock.patch.object(
                        CLEANUP_PROOF,
                        "require_clean",
                        side_effect=CLEANUP_PROOF.Preserve("final clean check failed"),
                    ):
                        self.assertEqual(1, CLEANUP_PROOF.run(args))
        finally:
            os.chdir(previous_cwd)

        receipt = load_receipt(self.state.name, worktree)
        archive = Path(receipt["set_aside"])
        self.assertEqual("preserve", receipt["verdict"])
        self.assertTrue(archive.is_dir())
        self.assertTrue((archive / "manifest.json").is_file())

    def test_argument_less_ignored_files_neither_block_nor_archive(self):
        bare, primary = init_repo(self.root)
        worktree = add_feature_worktree(primary, self.root, "feature")
        (worktree / ".gitignore").write_text("*.log\n", encoding="utf-8")
        git(worktree, "add", ".gitignore")
        git(worktree, "commit", "-q", "-m", "ignore logs")
        git(worktree, "push", "-q", "origin", "feature")
        head = git(worktree, "rev-parse", "HEAD")
        merge_oid = merge_commit_merge(primary, "feature")

        (worktree / "x.log").write_text("log noise\n", encoding="utf-8")
        (worktree / "note.txt").write_text("keep me\n", encoding="utf-8")

        fixture = self.fixture_path()
        write_fixture(
            fixture, {"state": "MERGED", "headRefOid": head, "mergeCommit": {"oid": merge_oid}},
            pr_for_branch=7,
        )
        result = self.run_proof_bare(worktree, fixture=fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(result.stdout.startswith("removable"))

        receipt = load_receipt(self.state.name, worktree)
        archive = Path(receipt["set_aside"])
        manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual({"note.txt"}, {entry["path"] for entry in manifest["untracked"]})
        self.assertFalse((archive / "untracked" / "x.log").exists())
        self.assertTrue((worktree / "x.log").exists())

        self.run_commands(result.stdout)
        self.assertFalse(worktree.exists())


if __name__ == "__main__":
    unittest.main()
