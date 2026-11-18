import importlib.util
import io
import json
import subprocess
import sys
import unittest
import uuid
from contextlib import ExitStack, redirect_stderr
from pathlib import Path
from unittest.mock import Mock, patch


HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOOKS))


def load_gate():
    spec = importlib.util.spec_from_file_location(
        "git_auth_scope_gate", HOOKS / "git_auth_scope_gate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_gate()


class ViolationTests(unittest.TestCase):
    def test_the_exact_command_that_prompted_this_gate_is_refused(self):
        self.assertEqual(
            "refresh",
            gate.find_violation("gh auth refresh -h github.com -s admin:org"),
        )

    def test_every_shape_that_mints_or_widens_a_credential_is_refused(self):
        for command, expected in (
            ("gh auth refresh", "refresh"),
            ("gh auth refresh -s read:packages", "refresh"),
            ("gh auth login", "login"),
            ("gh auth login --scopes admin:org", "login"),
            ("cd /some/repo && gh auth refresh -s admin:org", "refresh"),
            ("SCOPES=admin:org; gh auth refresh -s $SCOPES", "refresh"),
            ("gh  auth   login  -h github.com", "login"),
        ):
            with self.subTest(command=command):
                self.assertEqual(expected, gate.find_violation(command))

    def test_the_binary_named_any_way_a_shell_names_it_is_refused(self):
        """`\\bgh\\s+` alone missed every one of these, and `.exe` is the Windows default."""
        for command, expected in (
            ("gh.exe auth refresh -s admin:org", "refresh"),
            ('"C:\\Program Files\\GitHub CLI\\gh.exe" auth refresh -s admin:org', "refresh"),
            ("'/c/Program Files/GitHub CLI/gh.exe' auth login", "login"),
            ("GH.EXE auth login", "login"),
            ("/usr/bin/gh auth refresh", "refresh"),
            ("command gh auth refresh", "refresh"),
            ("cd /repo && gh.exe auth refresh -s admin:org", "refresh"),
        ):
            with self.subTest(command=command):
                self.assertEqual(expected, gate.find_violation(command))

    def test_a_word_merely_ending_in_gh_is_not_the_binary(self):
        self.assertIsNone(gate.find_violation("weigh auth refresh options"))

    def test_scopes_arriving_indirectly_are_still_refused(self):
        """Matching on -s/--scopes would miss these; refusing the subcommand does not."""
        self.assertIsNotNone(gate.find_violation("gh auth refresh $FLAGS"))


class AllowedTests(unittest.TestCase):
    def test_reading_or_selecting_an_existing_credential_is_allowed(self):
        for command in (
            "gh auth status",
            "gh auth token",
            "gh auth setup-git",
            "gh auth switch --user someone",
        ):
            with self.subTest(command=command):
                self.assertIsNone(gate.find_violation(command))

    def test_the_refused_call_itself_is_allowed(self):
        """A 403 is a finding to report; the gate must not also block re-reading it."""
        self.assertIsNone(gate.find_violation("gh api orgs/Concertable/actions/permissions"))

    def test_ordinary_work_is_never_in_the_way(self):
        for command in (
            "gh pr create --title x --body y",
            "gh run list --workflow publish.yml",
            "git push origin main",
            "dotnet test",
        ):
            with self.subTest(command=command):
                self.assertIsNone(gate.find_violation(command))

    def test_reading_the_flags_is_allowed_because_help_executes_nothing(self):
        """The skill asks for the org, permission and call by name; reading --help serves that."""
        for command in (
            "gh auth login --help",
            "gh auth refresh --help",
            "gh.exe auth login --help",
        ):
            with self.subTest(command=command):
                self.assertIsNone(gate.find_violation(command))

    def test_help_is_only_read_from_the_invocation_it_belongs_to(self):
        """`--help` on a LATER command must not excuse an earlier real one."""
        self.assertEqual(
            "refresh",
            gate.find_violation("gh auth refresh -s admin:org; gh pr view --help"),
        )

    def test_a_line_continuation_does_not_bridge_past_the_pattern(self):
        """A backtick or backslash before a newline is whitespace to the shell, not to `\\s`."""
        for command, expected in (
            ("gh auth `\n  refresh -s admin:org", "refresh"),
            ("gh auth \\\n  login --scopes admin:org", "login"),
            ("gh `\n auth `\n refresh", "refresh"),
        ):
            with self.subTest(command=command):
                self.assertEqual(expected, gate.find_violation(command))


class KnownLimitationTests(unittest.TestCase):
    """Stated rather than implied. These are what the gate cannot see, asserted so they stay known."""

    def test_prose_quoting_the_command_is_refused_too(self):
        """The gate reads command text, so it cannot tell discussion from execution. It errs closed."""
        self.assertIsNotNone(
            gate.find_violation("echo 'gh auth refresh is what not to do'")
        )

    def test_a_shell_hiding_the_token_pair_is_not_caught(self):
        """Not patchable by matching. Documented in the module docstring as residual risk."""
        for command in (
            "gh auth $(echo refresh)",
            "powershell -EncodedCommand Z2ggYXV0aCBsb2dpbg==",
        ):
            with self.subTest(command=command):
                self.assertIsNone(gate.find_violation(command))

    def test_writing_the_credential_file_directly_is_outside_this_gate(self):
        """Installing a token by writing hosts.yml never says `gh auth`; a shell gate cannot see it."""
        self.assertIsNone(
            gate.find_violation("printf 'github.com:\\n  oauth_token: x\\n' > ~/.config/gh/hosts.yml")
        )


class CommandExtractionTests(unittest.TestCase):
    def test_claude_bash_payload(self):
        self.assertEqual(
            "gh auth refresh -s admin:org",
            gate.extract_command("Bash", {"command": "gh auth refresh -s admin:org"}),
        )

    def test_codex_argv_payload_is_unwrapped(self):
        self.assertEqual(
            "gh auth login",
            gate.extract_command("exec_command", {"command": ["bash", "-lc", "gh auth login"]}),
        )

    def test_a_non_shell_tool_claims_no_jurisdiction(self):
        self.assertIsNone(gate.extract_command("Write", {"command": "gh auth refresh -s admin:org"}))

    def test_declared_unix_profiles_select_only_the_command_operand(self):
        script = "gh auth login"
        cases = (
            ["bash", "--noprofile", "-lc", script, "trailing"],
            ["bash", "+help", "-c", script],
            ["bash", "-ooec", "errexit", "nounset", script],
            ["bash", "-Oc", "completion_strip_exe", script],
            ["dash", "-p", "-c", script],
            ["dash", "-o", "priv", "-c", script],
            ["zsh", "--sh-word-split", "-c", script],
            ["zsh", "--emulate", "sh", "-e", "-b", "-c", script],
            ["zsh", "--emulate", "sh", "-bc", script],
            ["zsh", "-co", "errexit", script],
        )
        for payload in cases:
            with self.subTest(payload=payload):
                self.assertEqual(script, gate.extract_command("exec_command", {"command": payload}))

    def test_known_nonliteral_boundaries_are_not_scanned(self):
        script = "gh auth login"
        cases = (
            ["bash", "script.sh", "-c", script],
            ["bash", "--", "-c", script],
            ["dash", "-", "-c", script],
            ["zsh", "--emulate", "sh", "-b", "-c", script],
            ["pwsh", "script.ps1", "-Command", script],
            ["powershell", "-File", "script.ps1", "-Command", script],
            ["pwsh", "-EncodedCommand", "Z2ggYXV0aCBsb2dpbg=="],
        )
        for payload in cases:
            with self.subTest(payload=payload):
                self.assertIsNone(gate.extract_command("exec_command", {"command": payload}))

    def test_unresolved_active_launcher_options_refuse(self):
        cases = (
            ["bash", "--future-vendor-option", "-c", "SCRIPT"],
            ["bash", "+future-vendor-option", "-c", "SCRIPT"],
            ["bash", "-o", "future_option", "-c", "SCRIPT"],
            ["dash", "-q", "-c", "SCRIPT"],
            ["dash", "--future", "-c", "SCRIPT"],
            ["zsh", "--future-option", "-c", "SCRIPT"],
            ["zsh", "-o", "sh-word-split", "-c", "SCRIPT"],
            ["sh", "-coerrexit", "errexit", "SCRIPT"],
            ["sh", "-oerrexit", "-c", "SCRIPT"],
            ["pwsh", "-FutureVendorCommand", "-Command", "SCRIPT"],
            ["pwsh", "-CommandWithArg", "SCRIPT"],
            ["powershell", "-CWA", "SCRIPT"],
            ["pwsh", "-ExecutionPol", "FuturePolicy", "-Command", "SCRIPT"],
        )
        for payload in cases:
            with self.subTest(payload=payload), redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as exit_info:
                    gate.extract_command("exec_command", {"command": payload})
            self.assertIn("SHELL EXTRACTION GATE", stderr.getvalue())

    def test_powershell_prefixes_and_host_specific_version_arity(self):
        script = "Write-Output SCRIPT"
        command_prefixes = ("c", "co", "com", "comm", "comma", "comman", "command")
        for prefix in command_prefixes:
            for marker in ("-", "/"):
                with self.subTest(prefix=prefix, marker=marker):
                    self.assertEqual(
                        script + " ;",
                        gate.extract_command(
                            "exec_command",
                            {"command": ["powershell", "-NoProfile", marker + prefix, script, ";"]},
                        ),
                    )
        self.assertEqual(
            script,
            gate.extract_command("exec_command", {"command": ["powershell", "-Version", "5.1", "-Command", script]}),
        )
        self.assertIsNone(gate.extract_command("exec_command", {"command": ["pwsh", "-Version", "-Command", script]}))
        self.assertEqual(
            script,
            gate.extract_command("exec_command", {"command": ["pwsh", "-CWA", script, "trailing"]}),
        )

    def test_sh_agreement_uses_operand_index_and_text(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as exit_info:
                gate.extract_command("exec_command", {"command": ["sh", "-coerrexit", "errexit", "SCRIPT"]})


class EndToEndTests(unittest.TestCase):
    def _run(self, payload):
        return subprocess.run(
            [sys.executable, "-B", str(HOOKS / "git_auth_scope_gate.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
        )

    def test_blocks_with_exit_2_and_an_actionable_message(self):
        result = self._run(
            {
                "session_id": f"test-git-auth-block-{uuid.uuid4().hex}",
                "tool_use_id": f"tool-{uuid.uuid4().hex}",
                "tool_name": "Bash",
                "tool_input": {"command": "gh auth refresh -h github.com -s admin:org"},
            }
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("GIT-AUTH GATE", result.stderr)
        self.assertIn("fine-grained", result.stderr.lower())
        self.assertIn("git-auth", result.stderr)

    def test_allows_an_unrelated_command(self):
        result = self._run(
            {
                "session_id": f"test-git-auth-allow-{uuid.uuid4().hex}",
                "tool_use_id": f"tool-{uuid.uuid4().hex}",
                "tool_name": "Bash",
                "tool_input": {"command": "gh pr view 5 --json state"},
            }
        )
        self.assertEqual(0, result.returncode)

    def test_a_malformed_payload_fails_open(self):
        result = subprocess.run(
            [sys.executable, "-B", str(HOOKS / "git_auth_scope_gate.py")],
            input="not json",
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode)


class FailClosedTests(unittest.TestCase):
    """Recognising a command fails open; refusing one already recognised does not."""

    def _main_with(self, payload, claim=None):
        stderr = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(patch.object(sys, "stdin", io.StringIO(json.dumps(payload))))
            stack.enter_context(patch.object(sys, "stderr", stderr))
            if claim is not None:
                stack.enter_context(patch.object(gate, "claim_invocation", claim))
            with self.assertRaises(SystemExit) as exit_info:
                gate.main()
        return exit_info.exception.code, stderr.getvalue()

    def _blocked_payload(self):
        return {
            "session_id": f"fail-closed-{uuid.uuid4().hex}",
            "tool_use_id": f"tool-{uuid.uuid4().hex}",
            "tool_name": "Bash",
            "tool_input": {"command": "gh auth refresh -s admin:org"},
        }

    def test_a_fault_after_the_match_still_refuses(self):
        """A confirmed match must never be downgraded to an allow by a later exception."""
        code, stderr = self._main_with(
            self._blocked_payload(), claim=Mock(side_effect=RuntimeError("boom"))
        )

        self.assertEqual(2, code)
        self.assertIn("GIT-AUTH GATE", stderr)

    def test_the_fallback_message_needs_nothing_but_a_literal(self):
        """Whatever broke may be the formatting itself, so the fallback interpolates nothing."""
        self.assertNotIn("{", gate.FALLBACK_MESSAGE)
        self.assertIn("git-auth", gate.FALLBACK_MESSAGE)

    def test_an_unrecognised_payload_still_fails_open(self):
        code, stderr = self._main_with(
            {"session_id": "x", "tool_name": "Bash", "tool_input": {"command": "git status"}}
        )

        self.assertEqual(0, code)
        self.assertEqual("", stderr)


if __name__ == "__main__":
    unittest.main()
