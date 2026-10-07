import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / ".agents" / "hooks" / "worktree_cleanup_gate.py"
sys.path.insert(0, str(HOOK.parent))
import worktree_cleanup_gate


class WorktreeCleanupGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve() / "repo"
        self.assertFalse(self.repo.is_relative_to(ROOT))
        (self.repo / ".agents").mkdir(parents=True)
        self.git_config = Path(self.temp.name) / "empty-git-config"
        self.git_config.write_text("", encoding="utf-8")
        self.git_template = Path(self.temp.name) / "empty-git-template"
        self.git_template.mkdir()

    def git(self, repo, *args):
        environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        environment.update(
            GIT_CONFIG_GLOBAL=str(self.git_config), GIT_CONFIG_SYSTEM=str(self.git_config),
            GIT_CONFIG_NOSYSTEM="1", GIT_TEMPLATE_DIR=str(self.git_template),
        )
        result = subprocess.run(
            ["git", "-C", str(repo), *args], env=environment,
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.strip()

    def initialize(self, repo):
        repo.mkdir(parents=True, exist_ok=True)
        self.git(repo, "init")

    def configure(self, output, exit_code=0, repo=None):
        repo = repo or self.repo
        (repo / ".agents").mkdir(parents=True, exist_ok=True)
        audit = repo / "audit.py"
        audit.write_text(
            f"import sys\nsys.stdout.write({output!r})\nsys.exit({exit_code})\n",
            encoding="utf-8",
        )
        (repo / ".agents" / "worktree-cleanup-gate.json").write_text(
            json.dumps({"audit_command": [sys.executable, str(audit)]}), encoding="utf-8"
        )

    def invoke(self, event="Stop", cwd=None, environment=None, python_options=()):
        cwd = cwd or self.repo
        environment = environment if environment is not None else {
            key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")
        }
        return subprocess.run(
            [sys.executable, *python_options, str(HOOK)],
            input=json.dumps(
                {
                    "hook_event_name": event,
                    "session_id": f"worktree-cleanup-{uuid.uuid4().hex}",
                    "turn_id": "turn-1",
                    "cwd": str(cwd),
                }
            ),
            capture_output=True,
            text=True,
            cwd=cwd,
            env=environment,
            check=False,
        )

    def test_blocks_only_the_audit_states_that_need_human_cleanup(self):
        self.configure("OPEN_PR active\nMERGED_NOT_IN_MAIN stale\nORPHAN_FOLDER old-folder\n")

        result = self.invoke()

        self.assertEqual(0, result.returncode, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual("block", response["decision"])
        self.assertIn("MERGED_NOT_IN_MAIN stale", response["reason"])
        self.assertIn("ORPHAN_FOLDER old-folder", response["reason"])
        self.assertIn("never deletes automatically", response["reason"])

    def test_allows_a_clean_audit_and_unrelated_states(self):
        self.configure("OPEN_PR active\nCLOSED_UNMERGED retained\n")

        result = self.invoke("SessionStart")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_configured_audit_failure_surfaces_loudly(self):
        self.configure("audit unavailable", exit_code=1)

        result = self.invoke()

        self.assertEqual(0, result.returncode, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual("block", response["decision"])
        self.assertIn("cannot run the configured audit", response["reason"])

    def test_no_config_is_not_this_gates_business(self):
        result = self.invoke()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_non_git_descendant_does_not_inherit_ancestor_config(self):
        self.configure("ORPHAN_FOLDER outside\n")
        child = self.repo / "child"
        child.mkdir()

        result = self.invoke(cwd=child)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_nested_repository_does_not_inherit_outer_repository_config(self):
        self.initialize(self.repo)
        self.configure("ORPHAN_FOLDER outside\n")
        nested = self.repo / "nested"
        self.initialize(nested)
        child = nested / "child"
        child.mkdir()

        for cwd in (nested, child):
            with self.subTest(cwd=cwd):
                result = self.invoke(cwd=cwd)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_linked_worktree_does_not_inherit_outer_repository_config(self):
        self.initialize(self.repo)
        tracked = self.repo / "tracked.txt"
        tracked.write_text("fixture", encoding="utf-8")
        self.git(self.repo, "add", "tracked.txt")
        self.git(self.repo, "-c", "user.name=Cleanup Gate Test", "-c",
                 "user.email=cleanup-gate@example.invalid", "commit", "-m", "fixture")
        self.configure("ORPHAN_FOLDER outside\n")
        linked = self.repo / "linked"
        self.git(self.repo, "worktree", "add", "--detach", str(linked))
        child = linked / "child"
        child.mkdir()

        result = self.invoke(cwd=child)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)
        self.configure("ORPHAN_FOLDER linked\n", repo=linked)
        response = json.loads(self.invoke(cwd=child).stdout)
        self.assertIn("ORPHAN_FOLDER linked", response["reason"])

    def test_repository_descendant_finds_root_and_nearest_config(self):
        self.initialize(self.repo)
        self.configure("ORPHAN_FOLDER root\n")
        intermediate = self.repo / "intermediate"
        child = intermediate / "child"
        child.mkdir(parents=True)

        response = json.loads(self.invoke(cwd=child).stdout)
        self.assertIn("ORPHAN_FOLDER root", response["reason"])
        self.configure("ORPHAN_FOLDER nearest\n", repo=intermediate)
        response = json.loads(self.invoke(cwd=child).stdout)
        self.assertIn("ORPHAN_FOLDER nearest", response["reason"])
        self.assertNotIn("ORPHAN_FOLDER root", response["reason"])

    def test_inherited_repository_selectors_do_not_override_cwd(self):
        self.initialize(self.repo)
        self.configure("ORPHAN_FOLDER outside\n")
        nested = self.repo / "nested"
        self.initialize(nested)
        child = nested / "child"
        child.mkdir()
        environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        environment.update(GIT_DIR=str(self.repo / ".git"), GIT_WORK_TREE=str(self.repo))

        result = self.invoke(cwd=child, environment=environment)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)
        self.configure("ORPHAN_FOLDER nested\n", repo=nested)
        response = json.loads(self.invoke(cwd=child, environment=environment).stdout)
        self.assertIn("ORPHAN_FOLDER nested", response["reason"])

    def test_direct_non_git_config_does_not_require_git_discovery(self):
        self.configure("ORPHAN_FOLDER direct\n")
        with mock.patch.object(worktree_cleanup_gate.subprocess, "run") as discovery:
            self.assertEqual(self.repo / ".agents" / "worktree-cleanup-gate.json",
                             worktree_cleanup_gate.find_config(self.repo))
        discovery.assert_not_called()

    def test_discovery_failure_does_not_inherit_ancestor_config(self):
        self.configure("ORPHAN_FOLDER outside\n")
        child = self.repo / "child"
        child.mkdir()
        for error in (OSError("git unavailable"), subprocess.TimeoutExpired("git", 10)):
            with self.subTest(error=error), mock.patch.object(
                worktree_cleanup_gate.subprocess, "run", side_effect=error
            ) as discovery:
                self.assertIsNone(worktree_cleanup_gate.find_config(child))
                self.assertEqual(10, discovery.call_args.kwargs["timeout"])

    def test_discovered_root_must_contain_cwd(self):
        self.configure("ORPHAN_FOLDER outside\n")
        child = self.repo / "child"
        child.mkdir()
        unrelated = Path(self.temp.name) / "unrelated"
        unrelated.mkdir()
        discovery = subprocess.CompletedProcess(["git"], 0, str(unrelated), "")
        with mock.patch.object(worktree_cleanup_gate.subprocess, "run", return_value=discovery):
            self.assertIsNone(worktree_cleanup_gate.find_config(child))

    def test_cwd_and_root_resolution_failures_return_no_config(self):
        for error in (OSError("unavailable"), RuntimeError("symlink loop"), ValueError("invalid path")):
            with self.subTest(error=error), mock.patch.object(Path, "resolve", side_effect=error):
                self.assertIsNone(worktree_cleanup_gate.find_config(self.repo))
        discovery = subprocess.CompletedProcess(["git"], 0, str(self.repo), "")
        with mock.patch.object(worktree_cleanup_gate.subprocess, "run", return_value=discovery), \
                mock.patch.object(Path, "resolve", side_effect=[self.repo, OSError("root unavailable")]):
            self.assertIsNone(worktree_cleanup_gate.find_config(self.repo))

    def test_unicode_repository_with_python_utf8_mode_disabled(self):
        repo = self.repo / "repo-\u00e9"
        self.initialize(repo)
        self.configure("ORPHAN_FOLDER unicode\n", repo=repo)
        child = repo / "child"
        child.mkdir()
        environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        environment["PYTHONUTF8"] = "0"

        result = self.invoke(cwd=child, environment=environment, python_options=("-X", "utf8=0"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotEqual("", result.stdout)
        self.assertIn("ORPHAN_FOLDER unicode", json.loads(result.stdout)["reason"])

    def test_linked_worktree_fixture_ignores_hostile_global_signing_config(self):
        home = Path(self.temp.name) / "hostile-home"
        home.mkdir()
        (home / ".gitconfig").write_text(
            "[commit]\n\tgpgSign = true\n[gpg]\n\tprogram = nonexistent-review-fixture-signer\n",
            encoding="utf-8",
        )
        with mock.patch.dict(os.environ, {"HOME": str(home), "USERPROFILE": str(home),
                                          "XDG_CONFIG_HOME": str(home / "xdg")}):
            self.test_linked_worktree_does_not_inherit_outer_repository_config()

    def test_fixture_ignores_hostile_global_and_environment_templates(self):
        home = Path(self.temp.name) / "hostile-home"
        template = home / "template"
        template.mkdir(parents=True)
        (template / "hostile-template-marker").write_text("fixture", encoding="utf-8")
        (home / ".gitconfig").write_text(
            f'[init]\n\ttemplateDir = "{template.as_posix()}"\n'
            f'[core]\n\thooksPath = "{(home / "hooks").as_posix()}"\n',
            encoding="utf-8",
        )
        with mock.patch.dict(os.environ, {"HOME": str(home), "USERPROFILE": str(home),
                                          "XDG_CONFIG_HOME": str(home / "xdg"),
                                          "GIT_TEMPLATE_DIR": str(template)}):
            self.initialize(self.repo)
            self.assertFalse((self.repo / ".git" / "hostile-template-marker").exists())
            self.assertNotIn("core.hookspath", self.git(self.repo, "config", "--list").lower())


if __name__ == "__main__":
    unittest.main()
