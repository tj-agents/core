import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
HOOK = ROOT / ".agents" / "hooks" / "worktree_placement_gate.py"
sys.path.insert(0, str(HOOK.parent))
import worktree_placement_gate as gate


class WorktreePlacementGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.git_config = self.base / "empty-git-config"
        self.git_config.write_text("", encoding="utf-8")
        self.git_template = self.base / "empty-git-template"
        self.git_template.mkdir()
        self.initialize(self.repo)
        (self.repo / "tracked.txt").write_text("fixture", encoding="utf-8")
        self.git(self.repo, "add", "tracked.txt")
        self.git(self.repo, "-c", "user.name=Placement Gate Test", "-c",
                 "user.email=placement-gate@example.invalid", "commit", "-m", "fixture")
        (self.repo / ".worktrees").mkdir()

    def git(self, checkout, *arguments):
        environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        environment.update(
            GIT_CONFIG_GLOBAL=str(self.git_config),
            GIT_CONFIG_SYSTEM=str(self.git_config),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_TEMPLATE_DIR=str(self.git_template),
        )
        result = subprocess.run(
            ["git", "-C", str(checkout), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return result

    def initialize(self, checkout):
        checkout.mkdir(parents=True, exist_ok=True)
        self.git(checkout, "init")

    def invoke(self, command, *, codex=False, codex_argv=True, command_argv=None, payload_input=None, tool_name=None, environment=None, shell=None):
        tool_input = payload_input if payload_input is not None else {"command": command_argv} if command_argv is not None else (
            {"command": ["bash", "-lc", command]} if codex and codex_argv else {"command": command}
        )
        if shell is not None:
            tool_input["shell"] = shell
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": f"worktree-placement-{uuid.uuid4().hex}",
            "tool_use_id": uuid.uuid4().hex,
            "tool_name": tool_name or ("shell" if codex else "Bash"),
            "cwd": str(self.repo),
            "tool_input": tool_input,
        }
        if codex:
            payload["turn_id"] = uuid.uuid4().hex
        hook_environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        hook_environment.update(
            GIT_CONFIG_GLOBAL=str(self.git_config),
            GIT_CONFIG_SYSTEM=str(self.git_config),
            GIT_CONFIG_NOSYSTEM="1",
        )
        if environment:
            hook_environment.update(environment)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=self.repo,
            env=hook_environment,
            check=False,
        )

    def add_command(self, destination, *, checkout=None, branch="feature/test", executable="git"):
        checkout = checkout or self.repo
        return (
            f'"{executable}" -c advice.detachedHead=false -C "{checkout}" '
            f'worktree add -b "{branch}" -- "{destination}"'
        )

    def run_shell(self, command):
        environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        environment.update(
            GIT_CONFIG_GLOBAL=str(self.git_config),
            GIT_CONFIG_SYSTEM=str(self.git_config),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_TEMPLATE_DIR=str(self.git_template),
        )
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=self.repo,
            env=environment,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def run_powershell(self, command):
        if os.name != "nt":
            self.skipTest("requires Windows PowerShell")
        executable = shutil.which("powershell") or shutil.which("powershell.exe")
        if executable is None:
            self.skipTest("Windows PowerShell is unavailable")
        environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        environment.update(
            GIT_CONFIG_GLOBAL=str(self.git_config),
            GIT_CONFIG_SYSTEM=str(self.git_config),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_TEMPLATE_DIR=str(self.git_template),
        )
        result = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=self.repo,
            env=environment,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def assert_blocked(self, command, text):
        result = self.invoke(command)
        self.assertEqual(2, result.returncode)
        self.assertIn(text, result.stderr)
        self.assertIn("git -C", result.stderr)

    def test_allows_a_primary_checkout_and_the_native_command_creates_in_the_repository(self):
        destination = self.repo / ".worktrees" / "feature-test"
        command = self.add_command(destination, executable=shutil.which("git") or "git")

        result = self.invoke(command)

        self.assertEqual(0, result.returncode, result.stderr)
        self.run_shell(command)
        self.assertTrue((destination / ".git").exists())

    def test_allows_a_linked_checkout_using_the_common_repository_root(self):
        linked = self.base / "linked"
        self.git(self.repo, "worktree", "add", "--detach", str(linked))
        destination = self.repo / ".worktrees" / "linked-test"
        commit = self.git(self.repo, "rev-parse", "HEAD").stdout.strip()
        command = f'git -C "{linked}" worktree add --detach -- "{destination}" {commit}'

        result = self.invoke(command, codex=True)

        self.assertEqual(0, result.returncode, result.stderr)
        self.run_shell(command)
        self.assertTrue((destination / ".git").exists())

    def test_blocks_sibling_outside_nested_and_existing_destinations(self):
        sibling = self.base / "sibling"
        nested = self.repo / ".worktrees" / "nested" / "child"
        existing = self.repo / ".worktrees" / "existing"
        existing.mkdir()

        for destination, text in (
            (sibling, "direct child"),
            (nested, "direct child"),
            (existing, "already exists"),
        ):
            with self.subTest(destination=destination):
                self.assert_blocked(self.add_command(destination), text)

    def test_blocks_ambiguous_relative_and_compound_creation(self):
        target = self.repo / ".worktrees" / "feature-test"

        for command, text in (
            (f'git -C "$REPO" worktree add --detach -- "{target}"', "ambiguous"),
            (f'git -C . worktree add --detach -- "{target}"', "ambiguous"),
            (self.add_command(target) + " && git status", "compound"),
            (f'git -C "{self.repo}" worktree add --detach "{target}"', "ambiguous"),
            (f'git -C "{self.repo}" worktree add "{target}" -b feature/test', "ambiguous"),
            (f'GIT_DIR=x git -C "{self.repo}" worktree add --detach -- "{target}"', "ambiguous"),
            (f'git -c "$GIT_CONFIG" -C "{self.repo}" worktree add --detach -- "{target}"', "ambiguous"),
            (f'git --git-dir "{self.repo / ".git"}" -C "{self.repo}" worktree add --detach -- "{target}"', "ambiguous"),
            (f'git --work-tree "{self.base}" -C "{self.repo}" worktree add --detach -- "{target}"', "ambiguous"),
        ):
            with self.subTest(command=command):
                self.assert_blocked(command, text)

    def test_blocks_a_branch_that_does_not_match_the_flat_destination(self):
        destination = self.repo / ".worktrees" / "different-name"

        self.assert_blocked(self.add_command(destination), "flattened")

    def test_blocks_a_powershell_sibling_command_with_a_trailing_checkout_backslash(self):
        if os.name != "nt":
            self.skipTest("requires Windows paths")
        executable = shutil.which("git") or "git"
        sibling = self.base / "trailing-sibling"
        checkout = str(self.repo) + "\\"
        command = (
            f"& '{executable}' -C '{checkout}' worktree add -b 'trailing-sibling' -- '{sibling}'"
        )

        result = self.invoke(command, tool_name="PowerShell")

        self.assertEqual(2, result.returncode)
        self.assertIn("direct child", result.stderr)
        self.run_powershell(command)

    def test_blocks_a_symlinked_worktree_root_that_escapes_the_repository(self):
        escaped = self.base / "escaped"
        escaped.mkdir()
        worktrees = self.repo / ".worktrees"
        worktrees.rmdir()
        try:
            worktrees.symlink_to(escaped, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation is unavailable")

        self.assert_blocked(self.add_command(worktrees / "feature-test"), "real directory")

    def test_blocks_a_symlinked_worktree_root_inside_the_repository(self):
        redirected = self.repo / "redirected"
        redirected.mkdir()
        worktrees = self.repo / ".worktrees"
        worktrees.rmdir()
        try:
            worktrees.symlink_to(redirected, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation is unavailable")

        self.assert_blocked(self.add_command(worktrees / "feature-test"), "real directory")

    def test_blocks_when_git_cannot_prove_the_common_root(self):
        non_repository = self.base / "not-a-repository"
        non_repository.mkdir()
        destination = self.repo / ".worktrees" / "feature-test"

        self.assert_blocked(self.add_command(destination, checkout=non_repository), "could not prove")

    def test_blocks_a_file_named_worktrees(self):
        worktrees = self.repo / ".worktrees"
        worktrees.rmdir()
        worktrees.write_text("not a directory", encoding="utf-8")
        destination = worktrees / "feature-test"

        self.assert_blocked(self.add_command(destination), "real directory")

    def test_allows_a_missing_worktrees_directory_when_git_accepts_it(self):
        worktrees = self.repo / ".worktrees"
        worktrees.rmdir()
        destination = worktrees / "feature-test"
        command = self.add_command(destination)

        result = self.invoke(command)

        self.assertEqual(0, result.returncode, result.stderr)
        self.run_shell(command)
        self.assertTrue((destination / ".git").exists())

    def test_blocks_active_inherited_git_repository_routing(self):
        destination = self.repo / ".worktrees" / "feature-test"

        result = self.invoke(
            self.add_command(destination),
            environment={"GIT_COMMON_DIR": str(self.repo / ".git")},
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("GIT_COMMON_DIR is active", result.stderr)

    def test_post_recognition_failures_block(self):
        destination = self.base / "post-recognition-sibling"
        payload = {
            "tool_name": "PowerShell" if os.name == "nt" else "Bash",
            "tool_input": {"command": self.add_command(destination)},
            "session_id": uuid.uuid4().hex,
            "tool_use_id": uuid.uuid4().hex,
        }
        for replacement in (
            {"common_root": mock.Mock(side_effect=RuntimeError("unavailable")), "claim_invocation": mock.Mock(return_value=True)},
            {"common_root": mock.Mock(return_value=self.repo), "claim_invocation": mock.Mock(side_effect=RuntimeError("unavailable"))},
        ):
            with self.subTest(replacement=replacement), \
                    mock.patch.object(gate, "common_root", replacement["common_root"]), \
                    mock.patch.object(gate, "claim_invocation", replacement["claim_invocation"]), \
                    mock.patch.dict(os.environ, {}, clear=True), \
                    mock.patch("sys.stdin", io.StringIO(json.dumps(payload))), \
                    mock.patch("sys.stderr", io.StringIO()) as stderr:
                self.assertEqual(2, gate.main())
                self.assertIn("WORKTREE PLACEMENT GATE", stderr.getvalue())
            replacement["common_root"].assert_called_once_with(str(self.repo))
            replacement["claim_invocation"].assert_called_once()

    def test_blocks_native_creation_in_active_bash_and_powershell_substitutions(self):
        sibling = self.base / "substitution-sibling"
        native = f'git -C "{self.repo}" worktree add -b substitution-sibling -- "{sibling}"'
        cases = (
            (f"echo $({native})", True),
            (f"echo $(echo $({native}))", True),
            (f"echo `{native}`", True),
            (f"Write-Output $({native})", False),
        )
        for command, codex in cases:
            with self.subTest(command=command):
                result = self.invoke(command, codex=codex, tool_name=None if codex else "PowerShell")
                self.assertEqual(2, result.returncode)
                self.assertIn("command substitution", result.stderr)

    def test_detects_codex_exec_command_bash_shells(self):
        sibling = self.base / "codex-substitution-sibling"
        native = f'git -C "{self.repo}" worktree add -b codex-substitution-sibling -- "{sibling}"'
        command = f"echo `{native}`"
        shell = None if os.name != "nt" else r"C:\Program Files\Git\bin\bash.exe"

        result = self.invoke(
            command,
            codex=True,
            codex_argv=False,
            tool_name="exec_command",
            shell=shell,
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("command substitution", result.stderr)

    def test_detects_codex_exec_command_bash_argv_path_without_explicit_shell(self):
        sibling = self.base / "codex-argv-substitution-sibling"
        native = f'git -C "{self.repo}" worktree add -b codex-argv-substitution-sibling -- "{sibling}"'
        command = f"echo `{native}`"

        result = self.invoke(
            command,
            codex=True,
            codex_argv=False,
            command_argv=[r"C:\Program Files\Git\bin\bash.exe", "-lc", command],
            tool_name="exec_command",
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("command substitution", result.stderr)

    def test_extracts_codex_path_bash_argv_for_direct_creation(self):
        executable = r"C:\Program Files\Git\bin\bash.exe"
        internal = self.repo / ".worktrees" / "argv-internal"
        sibling = self.base / "argv-sibling"
        for action, keys in ((False, ("command", "cmd", "script", "input")), (True, ("command", "cmd"))):
            for key in keys:
                for destination, expected in ((sibling, 2), (internal, 0)):
                    command = self.add_command(destination, branch=destination.name)
                    value = [executable, "-lc", command]
                    payload_input = {"action": {key: value}} if action else {key: value}
                    with self.subTest(action=action, key=key, destination=destination):
                        result = self.invoke(
                            command,
                            codex=True,
                            codex_argv=False,
                            payload_input=payload_input,
                            tool_name="exec_command",
                        )
                        self.assertEqual(expected, result.returncode, result.stderr)

    def test_detects_nested_codex_bash_action_argv_substitution(self):
        sibling = self.base / "nested-action-substitution-sibling"
        native = f'git -C "{self.repo}" worktree add -b nested-action-substitution-sibling -- "{sibling}"'
        for key in ("command", "cmd"):
            with self.subTest(key=key):
                result = self.invoke(
                    f"echo `{native}`",
                    codex=True,
                    codex_argv=False,
                    payload_input={"action": {key: [r"C:\Program Files\Git\bin\bash.exe", "-lc", f"echo `{native}`"]}},
                    tool_name="exec_command",
                )
                self.assertEqual(2, result.returncode)
                self.assertIn("command substitution", result.stderr)

    def test_explicit_shell_selects_before_command_list_heuristics(self):
        self.assertEqual(
            "bash",
            gate.shell_kind("exec_command", {"shell": "/bin/bash", "command": ["pwsh", "-c", "echo ok"]}),
        )
        self.assertEqual(
            "powershell",
            gate.shell_kind("exec_command", {"shell": r"C:\Program Files\PowerShell\7\pwsh.exe", "command": ["bash", "-c", "echo ok"]}),
        )

    def test_allows_single_quoted_literal_native_creation_text(self):
        sibling = self.base / "literal-sibling"
        native = f'git -C "{self.repo}" worktree add -b literal-sibling -- "{sibling}"'

        for command, codex in ((f"echo '{native}'", True), (f"Write-Output '{native}'", False)):
            with self.subTest(command=command):
                result = self.invoke(command, codex=codex, tool_name=None if codex else "PowerShell")
                self.assertEqual(0, result.returncode, result.stderr)

    def test_leaves_non_creation_commands_prose_and_file_writes_alone(self):
        commands = (
            "git worktree list",
            "git worktree prune",
            "git worktree remove stale",
            "git status",
            'echo "git worktree add -- /tmp/example"',
        )
        for command in commands:
            with self.subTest(command=command):
                result = self.invoke(command)
                self.assertEqual(0, result.returncode, result.stderr)
        result = self.invoke(
            f'git -C "{self.repo}" worktree add -- "{self.repo / ".worktrees" / "feature-test"}"',
            tool_name="Write",
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_accepts_line_continuations_for_a_valid_creation(self):
        destination = self.repo / ".worktrees" / "feature-test"
        command = (
            f'git -C "{self.repo}" worktree \\\nadd -b feature/test -- "{destination}"'
        )

        result = self.invoke(command)

        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
