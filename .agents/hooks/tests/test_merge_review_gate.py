import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "merge_review_gate.py"
sys.path.insert(0, str(HOOK.parent))
M = "gh pr " + "merge"  # assembled so this file never contains the gated literal


def load_gate():
    spec = importlib.util.spec_from_file_location("merge_review_gate", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load_gate()


class InvocationTests(unittest.TestCase):
    """Only a command that RUNS the merge is gated. A substring test blocked any command
    quoting the string - including edits to this file and the PR body describing them."""

    def test_a_real_invocation_is_detected(self):
        self.assertTrue(gate.invokes_merge(M + " 613 --merge --auto"))

    def test_a_chained_invocation_is_detected(self):
        self.assertTrue(gate.invokes_merge("git fetch && " + M + " 613 --auto"))

    def test_an_env_prefixed_invocation_is_detected(self):
        self.assertTrue(gate.invokes_merge("GH_TOKEN=x " + M + " 613 --auto"))

    def test_merely_quoting_the_command_is_not_a_merge(self):
        self.assertFalse(gate.invokes_merge('echo "run ' + M + ' 613 --merge --auto to land it"'))

    def test_writing_it_into_a_file_is_not_a_merge(self):
        self.assertFalse(gate.invokes_merge("cat > pr.md <<'EOF'\nUse " + M + " 613 --admin\nEOF"))


class EnablingTokenTests(unittest.TestCase):
    def test_disable_auto_alone_is_not_an_enable(self):
        self.assertFalse(gate.is_merge_enable(M + " 613 --disable-auto"))

    def test_auto_is_an_enable(self):
        self.assertTrue(gate.is_merge_enable(M + " 613 --merge --auto"))

    def test_the_documented_re_assert_compound_still_gates(self):
        self.assertTrue(
            gate.is_merge_enable(M + " 613 --disable-auto && " + M + " 613 --merge --auto")
        )

    def test_a_bare_merge_still_gates(self):
        self.assertTrue(gate.is_merge_enable(M + " 613"))


class ReviewWorkOrderStateTests(unittest.TestCase):
    def test_legacy_complete_work_orders_remain_compatible(self):
        self.assertIsNone(gate.review_status("**Reviewed up to commit:** `abc1234`"))

    def test_review_status_is_normalized(self):
        self.assertEqual("complete", gate.review_status("**Review status:** `COMPLETE`"))
        self.assertEqual("in-progress", gate.review_status("**Review status:** `in-progress`"))

    def test_malformed_review_status_fails_closed(self):
        self.assertEqual("invalid", gate.review_status("**Review status:** complete"))

    def test_duplicate_review_status_fails_closed(self):
        review = "\n".join(
            ("**Review status:** `complete`", "**Review status:** `in-progress`")
        )

        self.assertEqual("invalid", gate.review_status(review))

    def test_valid_status_plus_malformed_duplicate_fails_closed(self):
        review = "\n".join(
            ("**Review status:** `complete`", "**Review status:** complete")
        )

        self.assertEqual("invalid", gate.review_status(review))

    def test_indented_status_and_judgment_fields_fail_closed(self):
        self.assertEqual(
            "invalid",
            gate.review_status(" **Review status:** `complete`"),
        )
        self.assertEqual(
            "invalid",
            gate.review_judgment(" **Judgment:** `approved`"),
        )
        review = "\n".join(
            ("**Review status:** `complete`", " **Review status:** `in-progress`")
        )
        self.assertEqual("invalid", gate.review_status(review))

    def test_markdown_code_examples_are_not_metadata_fields(self):
        review = "\n".join(
            (
                "**Review status:** `complete`",
                "**Judgment:** `approved`",
                "**Reviewed up to commit:** `abc1234`  `(2026-08-26)`",
                "```markdown",
                "```not-a-closing-fence",
                "**Review status:** `in-progress`",
                "**Judgment:** `pending`",
                "**Reviewed up to commit:** `def5678`",
                "**Security-reviewed up to commit:** `def5678`",
                "```",
                "    **Review status:** `in-progress`",
                "    **Judgment:** `pending`",
            )
        )

        self.assertEqual("complete", gate.review_status(review))
        self.assertEqual("approved", gate.review_judgment(review))
        self.assertEqual(
            "abc1234", gate.work_order_sha_field(review, "Reviewed up to commit")
        )
        self.assertIsNone(
            gate.work_order_sha_field(review, "Security-reviewed up to commit")
        )
        self.assertIsNone(gate.review_completion_problem(review))

    def test_completion_markers_are_unique_top_level_metadata(self):
        duplicate = "\n".join(
            (
                "**Reviewed up to commit:** `abc1234`",
                "**Reviewed up to commit:** `def5678`",
            )
        )

        self.assertEqual(
            "invalid", gate.work_order_sha_field(duplicate, "Reviewed up to commit")
        )
        self.assertEqual(
            "invalid",
            gate.work_order_sha_field(
                " **Security-reviewed up to commit:** `abc1234`",
                "Security-reviewed up to commit",
            ),
        )

    def test_final_judgment_is_normalized_and_malformed_values_fail_closed(self):
        self.assertEqual("approved", gate.review_judgment("**Judgment:** `APPROVED`"))
        self.assertEqual("invalid", gate.review_judgment("**Judgment:** approved"))
        self.assertIsNone(gate.review_judgment("legacy work order"))

    def test_new_judgment_without_status_is_not_legacy(self):
        review = "\n".join(
            ("**Judgment:** `pending`", "**Reviewed up to commit:** `abc1234`")
        )

        self.assertIn("no `Review status`", gate.review_completion_problem(review))
        staged = "\n".join(
            (
                "**Cross-area notes status:** `pending`",
                "**Parent summary status:** `pending`",
                "**Reviewed up to commit:** `abc1234`",
            )
        )
        self.assertIn("no `Review status`", gate.review_completion_problem(staged))

    def test_truly_legacy_review_state_remains_compatible(self):
        self.assertIsNone(
            gate.review_completion_problem("**Reviewed up to commit:** `abc1234`")
        )

    def test_complete_review_requires_one_final_parent_judgment(self):
        cases = (
            ("**Judgment:** `approved`", False),
            ("**Judgment:** `changes-requested`", False),
            ("", True),
            ("**Judgment:** `pending`", True),
            ("**Judgment:** approved", True),
            (
                "\n".join(
                    (
                        "**Judgment:** `approved`",
                        "**Judgment:** `changes-requested`",
                    )
                ),
                True,
            ),
        )
        for judgment, has_problem in cases:
            with self.subTest(judgment=judgment):
                review = "**Review status:** `complete`"
                if judgment:
                    review += "\n" + judgment
                self.assertEqual(
                    has_problem,
                    gate.review_completion_problem(review) is not None,
                )

    def test_staged_review_requires_complete_parent_finalization_state(self):
        prefix = "\n".join(
            (
                "**Review status:** `complete`",
                "**Judgment:** `approved`",
            )
        )
        complete = prefix + "\n" + "\n".join(
            (
                "**Cross-area notes status:** `complete`",
                "**Parent summary status:** `complete`",
            )
        )
        self.assertIsNone(gate.review_completion_problem(complete))
        for state in (
            "## Coverage\n- [x] runtime\n\n## Parent finalization",
            "## Review pass — 2026-08-26 — staged:runtime",
            "**Cross-area notes status:** `pending`\n**Parent summary status:** `complete`",
            "**Cross-area notes status:** `complete`\n**Parent summary status:** `pending`",
            "**Parent summary status:** `complete`",
            "**Cross-area notes status:** `complete`",
        ):
            with self.subTest(state=state):
                self.assertIn(
                    "incomplete parent finalization",
                    gate.review_completion_problem(prefix + "\n" + state),
                )

    def test_open_and_in_progress_items_are_unresolved(self):
        review = "\n".join(
            (
                "- [ ] R1 open",
                "- [~] R2 being addressed",
                "- [x] R3 fixed",
                "- [wontfix] R4 accepted",
            )
        )

        self.assertEqual(
            ["- [ ] R1 open", "- [~] R2 being addressed"],
            gate.unresolved_review_items(review),
        )


class TargetDirectoryTests(unittest.TestCase):
    """The merge runs where the last `cd` before it points. Without this a
    `cd <worktree> && merge` was judged against the pinned project dir."""

    def test_the_last_cd_before_the_merge_wins(self):
        self.assertEqual("/b", gate.merge_target_dir('cd /a && cd "/b" && ' + M + " 1 --auto", {}))

    def test_a_cd_after_the_merge_is_ignored(self):
        self.assertEqual(
            "/main", gate.merge_target_dir(M + " 1 --auto && cd /elsewhere", {"cwd": "/main"})
        )

    def test_quoted_paths_are_unwrapped(self):
        self.assertEqual(
            "/repos/my wt", gate.merge_target_dir("cd '/repos/my wt' && " + M + " 1 --auto", {})
        )


class CanonicalTargetContractTests(unittest.TestCase):
    """Both harnesses resolve one exact cross-shell envelope.

    Codex's hook payload does not expose exec_command's workdir. A small fail-closed grammar
    is therefore safer than attempting to interpret arbitrary cmd, PowerShell and Bash text.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def command(self, target=None, suffix=" --squash --auto"):
        return 'pushd "' + str(target or self.root) + '" && ' + M + " 17" + suffix

    def test_the_canonical_envelope_proves_an_absolute_existing_checkout(self):
        self.assertEqual(str(self.root), gate.canonical_merge_target_dir(self.command()))

    def test_all_supported_valueless_merge_switches_are_accepted(self):
        command = self.command(
            suffix=" --merge --squash --rebase --auto --admin --delete-branch"
        )

        self.assertEqual(str(self.root), gate.canonical_merge_target_dir(command))

    def test_a_bare_merge_has_no_proven_codex_target(self):
        self.assertIsNone(gate.canonical_merge_target_dir(M + " 17 --squash"))

    def test_a_relative_or_missing_target_is_rejected(self):
        missing = self.root / "missing"

        self.assertIsNone(gate.canonical_merge_target_dir(self.command(Path("relative"))))
        self.assertIsNone(gate.canonical_merge_target_dir(self.command(missing)))

    def test_a_non_numeric_pr_or_value_option_is_rejected(self):
        branch = 'pushd "' + str(self.root) + '" && ' + M + " feature --squash"

        self.assertIsNone(gate.canonical_merge_target_dir(branch))
        self.assertIsNone(gate.canonical_merge_target_dir(self.command(suffix=" --body message")))

    def test_extra_shell_commands_are_rejected(self):
        self.assertIsNone(gate.canonical_merge_target_dir(self.command() + " && echo merged"))

    def test_cross_shell_expansion_characters_are_rejected_in_the_target(self):
        unsafe = self.root / "$expanded"
        unsafe.mkdir()

        self.assertIsNone(gate.canonical_merge_target_dir(self.command(unsafe)))

    def test_any_standalone_pushd_before_the_merge_is_an_attempted_target(self):
        commands = (
            '(pushd "relative" && ' + M + " 17 --squash)",
            'builtin pushd "relative" && ' + M + " 17 --squash",
            'FOO=x pushd "relative" && ' + M + " 17 --squash",
            'FOO="x y" builtin pushd "relative" && ' + M + " 17 --squash",
            'FOO=$(printf x) pushd "relative" && ' + M + " 17 --squash",
            'echo "pushd" && ' + M + " 17 --squash",
        )

        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(gate.invokes_pushd_before_merge(command))

    def test_pushd_before_the_enabling_merge_in_a_re_assert_compound_is_detected(self):
        command = (
            M + " 17 --disable-auto && pushd \"relative\" && " + M + " 17 --squash --auto"
        )

        self.assertTrue(gate.invokes_pushd_before_merge(command))


class CanonicalEnvelopeShellTests(unittest.TestCase):
    """The shared target prefix changes directory under every supported native shell."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.target = self.root / "checkout with spaces"
        self.target.mkdir()

    def assert_target(self, result):
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(self.target, Path(result.stdout.strip().splitlines()[-1]).resolve())

    def bash(self):
        if os.name != "nt":
            return shutil.which("bash")
        git = shutil.which("git")
        if git is None:
            return None
        candidate = next(
            (
                root / "bin" / "bash.exe"
                for root in Path(git).resolve().parents
                if (root / "bin" / "bash.exe").is_file()
            ),
            None,
        )
        return str(candidate) if candidate else None

    def test_command_position_variants_execute_pushd_under_native_bash(self):
        bash = self.bash()
        self.assertIsNotNone(bash)
        probe = self.root / "print-pushd-cwd.py"
        probe.write_text("import os\nprint(os.getcwd())\n", encoding="utf-8")
        interpreter = "python" if os.name == "nt" else f'"{sys.executable}"'
        target = self.target.as_posix() if os.name == "nt" else str(self.target)
        probe_path = probe.as_posix() if os.name == "nt" else str(probe)
        variants = (
            f'(pushd "{target}" >/dev/null && {interpreter} "{probe_path}")',
            f'builtin pushd "{target}" >/dev/null && {interpreter} "{probe_path}"',
            f'FOO=x pushd "{target}" >/dev/null && {interpreter} "{probe_path}"',
            f'FOO=$(printf x) pushd "{target}" >/dev/null && {interpreter} "{probe_path}"',
        )

        for command in variants:
            with self.subTest(command=command):
                self.assert_target(
                    subprocess.run([bash, "-c", command], capture_output=True, text=True)
                )

    @unittest.skipUnless(os.name == "nt", "Windows native shells only")
    def test_the_envelope_prefix_runs_under_cmd_powershell_and_git_bash(self):
        probe = self.root / "print-cwd.py"
        probe.write_text("import os\nprint(os.getcwd())\n", encoding="utf-8")
        command = f'pushd "{self.target.as_posix()}" && python "{probe.as_posix()}"'
        batch = self.root / "run-envelope.cmd"
        batch.write_text("@echo off\r\n" + command + "\r\n", encoding="utf-8")

        self.assert_target(
            subprocess.run(
                ["cmd.exe", "/D", "/C", str(batch)],
                capture_output=True,
                text=True,
            )
        )
        powershell = shutil.which("powershell") or shutil.which("pwsh")
        self.assertIsNotNone(powershell)
        powershell_command = command
        if Path(powershell).stem.casefold() == "powershell":
            powershell_command = command.replace(" && ", "; if ($?) { ", 1) + " }"
        self.assert_target(
            subprocess.run(
                [powershell, "-NoProfile", "-Command", powershell_command],
                capture_output=True,
                text=True,
            )
        )
        bash = self.bash()
        self.assertIsNotNone(bash)
        self.assert_target(
            subprocess.run([str(bash), "-c", command], capture_output=True, text=True)
        )

    @unittest.skipIf(os.name == "nt", "POSIX native shell only")
    def test_the_envelope_prefix_runs_under_bash(self):
        probe = self.root / "print-cwd.sh"
        probe.write_text("#!/bin/sh\npwd\n", encoding="utf-8")
        probe.chmod(0o755)
        command = f'pushd "{self.target}" && "{probe}"'

        self.assert_target(
            subprocess.run(["bash", "-c", command], capture_output=True, text=True)
        )


class SecurityPatternTests(unittest.TestCase):
    """The generic patterns hold everywhere; a repo's own service names are its data."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / ".agents").mkdir()

    def write_config(self, config):
        body = config if isinstance(config, str) else json.dumps(config)
        path = self.root / gate.CONFIG_FILE
        path.write_text(body, encoding="utf-8")
        return path

    def test_a_workflow_change_is_sensitive_without_any_repo_config(self):
        self.assertEqual(
            ".github/workflows/ci.yml", gate.touches_security([".github/workflows/ci.yml"])
        )

    def test_credential_vocabulary_is_sensitive_without_any_repo_config(self):
        self.assertEqual("src/ApiKeyStore.cs", gate.touches_security(["src/ApiKeyStore.cs"]))

    def test_an_ordinary_path_is_not_sensitive(self):
        self.assertIsNone(gate.touches_security(["src/Widget.cs"]))

    def test_a_repo_declared_path_becomes_sensitive(self):
        patterns = gate.security_patterns(self.write_config({"security_paths": [r"(^|/)Acme\.Auth"]}))

        self.assertEqual("api/Acme.Auth/X.cs", gate.touches_security(["api/Acme.Auth/X.cs"], patterns))

    def test_the_generic_patterns_survive_a_repo_declaration(self):
        patterns = gate.security_patterns(self.write_config({"security_paths": [r"nothing"]}))

        self.assertEqual(
            ".github/workflows/ci.yml",
            gate.touches_security([".github/workflows/ci.yml"], patterns),
        )

    def test_a_config_with_no_security_paths_is_valid(self):
        patterns = gate.security_patterns(self.write_config({}))

        self.assertIsNone(gate.touches_security(["src/Widget.cs"], patterns))

    def test_malformed_json_raises_rather_than_failing_open(self):
        path = self.write_config("{ not json")

        with self.assertRaises(gate.ConfigUnusable):
            gate.security_patterns(path)

    def test_security_paths_of_the_wrong_type_raises(self):
        path = self.write_config({"security_paths": "Acme.Auth"})

        with self.assertRaises(gate.ConfigUnusable):
            gate.security_patterns(path)

    def test_an_uncompilable_pattern_raises(self):
        path = self.write_config({"security_paths": ["("]})

        with self.assertRaises(gate.ConfigUnusable):
            gate.security_patterns(path)


class JurisdictionTests(unittest.TestCase):
    """The gate speaks only for a repo that opted in. `reviews/<branch>.md` is a convention a
    repo adopts; gating a sibling repo demanded a review file it never had."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def opt_in(self, directory=None):
        target = (directory or self.root) / ".agents"
        target.mkdir(parents=True, exist_ok=True)
        (target / "merge-gate.json").write_text(json.dumps({"security_paths": []}), encoding="utf-8")

    def run_hook(self, command, cwd=None, codex=False):
        payload_data = {
            "tool_name": "Bash",
            "cwd": str(cwd or self.root),
            "tool_input": {"command": command},
        }
        if codex:
            payload_data["turn_id"] = "codex-" + self._testMethodName
        payload = json.dumps(payload_data)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            cwd=str(cwd or self.root),
        )

    def test_a_repo_that_never_opted_in_is_not_this_gates_business(self):
        self.assertEqual(0, self.run_hook(M + " 1 --squash").returncode)

    def test_an_opted_in_repo_is_gated(self):
        self.opt_in()

        self.assertEqual(2, self.run_hook(M + " 1 --squash").returncode)

    def test_codex_rejects_an_ambiguous_target_before_repo_jurisdiction(self):
        result = self.run_hook(M + " 1 --squash", codex=True)

        self.assertEqual(2, result.returncode)
        self.assertIn("Use exactly `pushd", result.stderr)

    def test_codex_canonical_target_reaches_the_target_repos_review_gate(self):
        self.opt_in()
        command = 'pushd "' + str(self.root) + '" && ' + M + " 1 --squash"

        result = self.run_hook(command, codex=True)

        self.assertEqual(2, result.returncode)
        self.assertIn("cannot resolve PR #1", result.stderr)
        self.assertNotIn("cannot prove this merge's checkout", result.stderr)

    def test_codex_canonical_target_outside_an_opted_repo_is_not_review_gated(self):
        other = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(lambda: None)
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        self.opt_in()
        command = 'pushd "' + str(other) + '" && ' + M + " 1 --squash"

        self.assertEqual(0, self.run_hook(command, codex=True).returncode)

    def test_claude_canonical_target_outside_an_opted_repo_is_not_review_gated(self):
        other_temp = tempfile.TemporaryDirectory()
        self.addCleanup(other_temp.cleanup)
        other = Path(other_temp.name).resolve()
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        self.opt_in()
        command = 'pushd "' + str(other) + '" && ' + M + " 1 --squash"

        self.assertEqual(0, self.run_hook(command).returncode)

    def test_claude_rejects_a_relative_pushd_target_before_repo_jurisdiction(self):
        command = 'pushd "relative-checkout" && ' + M + " 1 --squash"

        result = self.run_hook(command)

        self.assertEqual(2, result.returncode)
        self.assertIn("Claude cannot prove this merge's pushd checkout", result.stderr)

    def test_claude_rejects_an_expansion_based_pushd_target_before_repo_jurisdiction(self):
        command = 'pushd "$MERGE_CHECKOUT" && ' + M + " 1 --squash"

        result = self.run_hook(command)

        self.assertEqual(2, result.returncode)
        self.assertIn("Claude cannot prove this merge's pushd checkout", result.stderr)

    def test_claude_rejects_git_bash_pushd_forms_before_repo_jurisdiction(self):
        commands = (
            '(pushd "relative-checkout" && ' + M + " 1 --squash)",
            'builtin pushd "relative-checkout" && ' + M + " 1 --squash",
            'FOO=x pushd "relative-checkout" && ' + M + " 1 --squash",
            'FOO="x y" builtin pushd "relative-checkout" && ' + M + " 1 --squash",
            'FOO=$(printf x) pushd "relative-checkout" && ' + M + " 1 --squash",
        )

        for command in commands:
            with self.subTest(command=command):
                result = self.run_hook(command)
                self.assertEqual(2, result.returncode)
                self.assertIn("Claude cannot prove this merge's pushd checkout", result.stderr)

    def test_claude_rejects_re_assert_pushd_before_falling_back_to_session_jurisdiction(self):
        other_temp = tempfile.TemporaryDirectory()
        self.addCleanup(other_temp.cleanup)
        other = Path(other_temp.name).resolve()
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        self.opt_in()
        command = (
            M
            + " 1 --disable-auto && pushd \""
            + str(other)
            + "\" && "
            + M
            + " 1 --squash --auto"
        )

        result = self.run_hook(command)

        self.assertEqual(2, result.returncode)
        self.assertIn("Claude cannot prove this merge's pushd checkout", result.stderr)
        self.assertNotIn("cannot resolve PR #1", result.stderr)

    def test_the_opt_in_is_found_from_a_subdirectory(self):
        self.opt_in()
        nested = self.root / "src" / "deep"
        nested.mkdir(parents=True)

        self.assertEqual(2, self.run_hook(M + " 1 --squash", cwd=nested).returncode)

    def test_jurisdiction_follows_the_directory_the_merge_runs_in(self):
        # `cd <other-repo> && merge` is judged by THAT repo's opt-in, not this session's.
        other = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(lambda: None)
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        self.opt_in()

        result = self.run_hook('cd "' + str(other) + '" && ' + M + " 1 --squash")

        self.assertEqual(0, result.returncode)

    def set_origin(self, url):
        subprocess.run(["git", "remote", "add", "origin", url], cwd=str(self.root), check=True)

    def test_a_merge_that_names_another_repository_is_not_this_gates_business(self):
        self.opt_in()
        self.set_origin("https://github.com/owner/this.git")

        result = self.run_hook(M + " 1 --repo other/that --squash")

        self.assertEqual(0, result.returncode)

    def test_a_merge_that_names_this_repository_is_still_gated(self):
        self.opt_in()
        self.set_origin("git@github.com:Owner/This.git")

        result = self.run_hook(M + " 1 --repo owner/this --squash")

        self.assertEqual(2, result.returncode)

    def test_naming_a_repository_with_no_origin_to_compare_blocks(self):
        self.opt_in()

        result = self.run_hook(M + " 1 --repo other/that --squash")

        self.assertEqual(2, result.returncode)
        self.assertIn("cannot be read", result.stderr)

    def test_the_short_flag_and_an_equals_form_are_both_read(self):
        self.assertEqual("other/that", gate.repo_flag(M + " 1 -R other/that --squash"))
        self.assertEqual("other/that", gate.repo_flag(M + " 1 --repo=other/that --squash"))

    def test_a_non_merge_command_is_always_ignored(self):
        self.opt_in()

        self.assertEqual(0, self.run_hook("git status").returncode)

    def test_a_tool_outside_the_hooks_vocabulary_is_ignored(self):
        self.opt_in()
        payload = json.dumps(
            {
                "tool_name": "some_other_shell",
                "cwd": str(self.root),
                "tool_input": {"command": M + " 1 --squash"},
            }
        )

        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            cwd=str(self.root),
        )

        self.assertEqual(0, result.returncode)

    def test_the_tool_name_is_matched_case_insensitively(self):
        self.opt_in()
        payload = json.dumps(
            {
                "tool_name": "bash",
                "cwd": str(self.root),
                "tool_input": {"command": M + " 1 --squash"},
            }
        )

        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            capture_output=True,
            text=True,
            cwd=str(self.root),
        )

        self.assertEqual(2, result.returncode)

    def test_every_wired_shell_is_gated_not_only_bash(self):
        """A shell the script ignores is a bypass: the same merge runs unreviewed just by
        choosing the other tool. Assert each name in the vocabulary actually blocks."""
        self.opt_in()

        for tool in sorted(gate.SHELL_TOOLS):
            payload = json.dumps(
                {
                    "tool_name": tool,
                    "cwd": str(self.root),
                    "tool_input": {"command": M + " 1 --squash"},
                }
            )

            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=payload,
                capture_output=True,
                text=True,
                cwd=str(self.root),
            )

            self.assertEqual(2, result.returncode, tool + " merged without a review")

    def test_a_broken_config_blocks_instead_of_failing_open(self):
        (self.root / ".agents").mkdir(exist_ok=True)
        (self.root / ".agents" / "merge-gate.json").write_text("{ not json", encoding="utf-8")

        result = self.run_hook(M + " 1 --squash")

        self.assertEqual(2, result.returncode)
        self.assertIn("could not be read", result.stderr)


class GrantTests(unittest.TestCase):
    """A merge that passed every check is approved only in the exact Claude envelope and only in
    a repository whose origin is a trusted owner."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)

    def set_origin(self, url):
        subprocess.run(["git", "-C", str(self.root), "remote", "add", "origin", url], check=True)

    def decision(self, data, target):
        import contextlib
        import io

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            try:
                gate.grant_if_trusted(data, target)
            except SystemExit as exit_:
                self.assertEqual(0, exit_.code)
        return out.getvalue()

    def test_a_trusted_canonical_claude_merge_is_granted(self):
        self.set_origin("https://github.com/tj-agents/core.git")

        output = json.loads(self.decision({}, str(self.root)))

        self.assertEqual("allow", output["hookSpecificOutput"]["permissionDecision"])

    def test_an_untrusted_owner_is_not_granted(self):
        self.set_origin("https://github.com/Infonetica/cris-diligence.git")

        self.assertEqual("", self.decision({}, str(self.root)))

    def test_a_non_canonical_or_codex_merge_is_not_granted(self):
        self.set_origin("https://github.com/tj-agents/core.git")

        self.assertEqual("", self.decision({}, None))
        self.assertEqual("", self.decision({"turn_id": "t1"}, str(self.root)))


class SecurityRangeTests(unittest.TestCase):
    """The security layer must judge the head being MERGED, and re-ask only when a sensitive
    path moved. Reading the session's HEAD made a sensitive PR merged from another checkout
    skip the layer outright; demanding marker == head left the marker with no legal exit."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.run_git("init", "-q", ".")
        self.run_git("symbolic-ref", "HEAD", "refs/heads/main")
        self.run_git("config", "user.email", "t@example.com")
        self.run_git("config", "user.name", "t")
        self.WORK_ORDER = "reviews/Fix-CredentialScoping.md"
        self.base = self.commit("readme.md", "hello")
        self.run_git("checkout", "-q", "-b", "feature")
        self.sensitive = self.commit("src/credentials.json", "{}")
        self.later = self.commit("docs/note.md", "note")
        self.run_git("checkout", "-q", "main")
        gate._GIT_CWD[0] = str(self.root)
        self.addCleanup(lambda: gate._GIT_CWD.__setitem__(0, "."))

    def run_git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=str(self.root), check=True, capture_output=True, text=True
        ).stdout.strip()

    def commit(self, relative, body):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        self.run_git("add", "-A")
        self.run_git("commit", "-q", "-m", "add " + relative)
        return self.run_git("rev-parse", "HEAD")

    def test_the_named_head_is_classified_not_the_checkouts_head(self):
        self.assertEqual(
            "src/credentials.json",
            gate.touches_security(gate.changed_against_main(self.later)),
        )

    def test_the_checkouts_own_head_is_not_what_answers(self):
        # The regression: on main this classified nothing, so a sensitive PR merged from any
        # other checkout was waved through without a security marker.
        self.assertIsNone(gate.touches_security(gate.changed_against_main(self.base)))

    def test_an_unresolvable_head_classifies_nothing(self):
        self.assertEqual([], gate.changed_against_main("0" * 40))

    def test_a_marker_is_still_current_when_only_ordinary_files_changed(self):
        self.assertFalse(
            gate.security_no_longer_covered(self.sensitive, self.later, gate._SECURITY_PATTERNS)
        )

    def test_a_marker_is_stale_once_a_sensitive_path_changes(self):
        self.assertTrue(
            gate.security_no_longer_covered(self.base, self.later, gate._SECURITY_PATTERNS)
        )

    def test_an_unresolvable_marker_fails_closed(self):
        self.assertTrue(
            gate.security_no_longer_covered("0" * 40, self.later, gate._SECURITY_PATTERNS)
        )

    def test_stamping_the_marker_does_not_restale_it_on_a_sensitively_named_branch(self):
        # The regression: the work order's path comes from the branch slug, so a branch named for
        # what it fixes puts `credential` into `reviews/<slug>.md` — where the generic vocabulary
        # matches it. Stamping the marker is a commit to that path, so stamping restaled the marker
        # and the branch could not be merged from any checkout. Fix/CredentialScoping hit exactly
        # this; Fix/AuthenticationRetry would too.
        self.run_git("checkout", "-q", "feature")
        stamped = self.commit(self.WORK_ORDER, "**Security-reviewed up to ...**")

        self.assertFalse(
            gate.security_no_longer_covered(
                self.later, stamped, gate._SECURITY_PATTERNS, self.WORK_ORDER
            )
        )

    def test_the_work_order_never_hides_a_real_sensitive_change_beside_it(self):
        # The exclusion is one path, not a range: a sensitive file in the same range still stales.
        self.run_git("checkout", "-q", "feature")
        self.commit(self.WORK_ORDER, "stamped")
        with_code = self.commit("src/credentials.json", '{"rotated": true}')

        self.assertTrue(
            gate.security_no_longer_covered(
                self.later, with_code, gate._SECURITY_PATTERNS, self.WORK_ORDER
            )
        )

    def test_a_sensitive_file_under_reviews_is_not_excused_by_living_there(self):
        # A `reviews/` prefix match would have put anything a writer placed in that directory
        # permanently beyond staleness detection once a first marker existed. Only this branch's
        # own artifact is evidence; a script sitting beside it is not.
        self.run_git("checkout", "-q", "feature")
        planted = self.commit("reviews/rotate-credentials.py", "print('rotate')")

        self.assertTrue(
            gate.security_no_longer_covered(
                self.later, planted, gate._SECURITY_PATTERNS, self.WORK_ORDER
            )
        )

    def test_another_branchs_work_order_is_not_this_branchs_evidence(self):
        # Arrives on a merge from main. It is not what this branch's security review looked at.
        self.run_git("checkout", "-q", "feature")
        other = self.commit("reviews/Fix-PasswordRotation.md", "someone else's review")

        self.assertTrue(
            gate.security_no_longer_covered(
                self.later, other, gate._SECURITY_PATTERNS, self.WORK_ORDER
            )
        )

if __name__ == "__main__":
    unittest.main()
