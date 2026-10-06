"""launch_claude.py: option validation, argument assembly and real lane resolution, with
resolve_claude_executable/sync_claude_standards/launch_tab stubbed but everything else (the directory
check, the prompt file check, resolve_lane_model and open_claude_tab's own orchestration) left real."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.agents/machine/utility/handoff-claude/scripts/launch_claude.py'
CLAUDE_LANES = json.loads((ROOT / '.agents/lanes/claude.json').read_text(encoding='utf-8'))

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))
import launcher_test_support  # noqa: E402  (after the sys.path fix-up above)

SPEC = importlib.util.spec_from_file_location('launch_claude', SCRIPT)
LAUNCH_CLAUDE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LAUNCH_CLAUDE
SPEC.loader.exec_module(LAUNCH_CLAUDE)


class LaunchClaudeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='launch claude ')
        self.addCleanup(temp.cleanup)
        self.directory = temp.name
        self.prompt_path = Path(self.directory) / 'draft prompt.md'
        self.prompt_path.write_text('Read this and continue.\n')
        self.agent_cli = launcher_test_support.real_agent_cli('agent_cli_for_launch_claude_tests')
        patcher = mock.patch.object(LAUNCH_CLAUDE, '_load_agent_cli', return_value=self.agent_cli)
        patcher.start()
        self.addCleanup(patcher.stop)

        # For the call-order assertion (H10): attached to the same three mocks real_agent_cli() installed.
        self.call_order = mock.Mock()
        self.call_order.attach_mock(self.agent_cli.resolve_claude_executable, 'resolve_claude_executable')
        self.call_order.attach_mock(self.agent_cli.sync_claude_standards, 'sync_claude_standards')
        self.call_order.attach_mock(self.agent_cli.launch_tab, 'launch_tab')

    def run_main(self, *args):
        argv = ['--working-directory', self.directory, '--prompt-path', str(self.prompt_path), *args]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = LAUNCH_CLAUDE.main(argv)
        return code, out.getvalue(), err.getvalue()

    # --- validation ---

    def test_a_missing_working_directory_is_rejected_through_the_real_directory_check(self):
        out, err = io.StringIO(), io.StringIO()
        missing = str(Path(self.directory) / 'missing')
        argv = ['--working-directory', missing, '--prompt-path', str(self.prompt_path)]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = LAUNCH_CLAUDE.main(argv)
        self.assertEqual(code, 1)
        self.assertIn('not a directory', err.getvalue())
        self.assertIn(os.path.abspath(missing), err.getvalue())
        self.agent_cli.launch_tab.assert_not_called()

    def test_a_missing_directory_is_reported_even_when_the_prompt_path_is_also_invalid(self):
        # H14: the directory is validated first, so its error is never shadowed by a later check.
        out, err = io.StringIO(), io.StringIO()
        argv = ['--working-directory', str(Path(self.directory) / 'missing'),
                '--prompt-path', str(Path(self.directory) / 'missing-prompt.md')]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = LAUNCH_CLAUDE.main(argv)
        self.assertEqual(code, 1)
        self.assertIn('Working directory is not a directory', err.getvalue())

    def test_a_prompt_path_that_is_not_a_file_is_rejected(self):
        out, err = io.StringIO(), io.StringIO()
        argv = ['--working-directory', self.directory, '--prompt-path', self.directory]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = LAUNCH_CLAUDE.main(argv)
        self.assertEqual(code, 1)
        self.assertIn('is not a file', err.getvalue())
        self.agent_cli.launch_tab.assert_not_called()

    def test_frontier_and_lane_are_mutually_exclusive(self):
        code, _, err = self.run_main('--frontier', '--lane', 'L1')
        self.assertEqual(code, 1)
        self.assertIn('--frontier rejects --lane', err)
        self.agent_cli.launch_tab.assert_not_called()

    def test_frontier_and_model_are_mutually_exclusive(self):
        code, _, err = self.run_main('--frontier', '--model', 'some-model')
        self.assertEqual(code, 1)
        self.assertIn('--frontier rejects --lane and --model', err)
        self.agent_cli.launch_tab.assert_not_called()

    def test_an_invalid_lane_is_rejected_by_argparse(self):
        with self.assertRaises(SystemExit) as raised:
            self.run_main('--lane', 'L9')
        self.assertEqual(raised.exception.code, 2)
        self.agent_cli.launch_tab.assert_not_called()

    def test_there_is_no_effort_flag(self):
        # H11: an explicit effort could reach a model it was never priced for (e.g. --lane L1 --effort max
        # reaching the frontier pair without --frontier) or a model that rejects it outright (L7's Haiku).
        # Effort is only ever the one the resolved lane or frontier entry prices for its own model.
        with self.assertRaises(SystemExit) as raised:
            self.run_main('--effort', 'high')
        self.assertEqual(raised.exception.code, 2)
        self.agent_cli.launch_tab.assert_not_called()

    # --- argument assembly and order ---

    def test_no_model_lane_or_permission_flags_means_only_the_prompt_sentence(self):
        self.run_main()
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertEqual(len(arguments), 1)
        self.assertTrue(arguments[0].startswith('Read the file at'))

    def test_dangerously_skip_permissions_then_model_then_the_prompt_sentence(self):
        self.run_main('--dangerously-skip-permissions', '--model', 'explicit-model')
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertEqual(arguments[0], '--dangerously-skip-permissions')
        self.assertEqual(arguments[1], '--model')
        self.assertEqual(arguments[2], 'explicit-model')
        self.assertTrue(arguments[3].startswith('Read the file at'))

    def test_the_prompt_sentence_names_the_resolved_prompt_path_and_current_directory(self):
        self.run_main()
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        sentence = arguments[-1]
        self.assertIn(str(self.prompt_path.resolve()), sentence)
        self.assertIn('working from the current directory', sentence)

    def test_no_model_means_no_model_flag_reaches_launch_tab(self):
        self.run_main()
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertNotIn('--model', arguments)

    # --- model precedence, against the real lane table ---

    def test_an_explicit_model_beats_a_lane(self):
        self.run_main('--lane', 'L3', '--model', 'explicit-model')
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertEqual(arguments[arguments.index('--model') + 1], 'explicit-model')
        self.assertNotIn(CLAUDE_LANES['lanes']['L3']['model'], arguments)

    def test_a_lane_resolves_through_the_real_claude_lane_table(self):
        self.run_main('--lane', 'L3')
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertEqual(arguments[arguments.index('--model') + 1], CLAUDE_LANES['lanes']['L3']['model'])

    def test_frontier_resolves_through_the_real_claude_frontier_tier(self):
        self.run_main('--frontier')
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertEqual(arguments[arguments.index('--model') + 1], CLAUDE_LANES['frontier']['model'])

    # --- effort, against the real lane table (H1) -- always the lane/frontier's own, never a caller's ---

    def test_a_lane_with_a_priced_effort_passes_both_model_and_effort_in_order(self):
        self.assertIn('effort', CLAUDE_LANES['lanes']['L3'])  # sanity: the table really prices one
        self.run_main('--lane', 'L3')
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertEqual(arguments[arguments.index('--model') + 1], CLAUDE_LANES['lanes']['L3']['model'])
        self.assertEqual(arguments[arguments.index('--effort') + 1], CLAUDE_LANES['lanes']['L3']['effort'])
        self.assertLess(arguments.index('--model'), arguments.index('--effort'))

    def test_a_lane_with_no_priced_effort_passes_no_effort_flag(self):
        self.assertNotIn('effort', CLAUDE_LANES['lanes']['L7'])  # sanity: the table prices none
        self.run_main('--lane', 'L7')
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertNotIn('--effort', arguments)

    def test_an_explicit_model_beating_the_lane_drops_the_lanes_effort_too(self):
        self.run_main('--lane', 'L3', '--model', 'explicit-model')
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertNotIn('--effort', arguments)

    def test_frontier_resolves_its_own_effort(self):
        self.run_main('--frontier')
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertEqual(arguments[arguments.index('--effort') + 1], CLAUDE_LANES['frontier']['effort'])

    def test_an_explicit_model_alone_passes_no_effort(self):
        self.run_main('--model', 'explicit-model')
        arguments = self.agent_cli.launch_tab.call_args.kwargs['arguments']
        self.assertNotIn('--effort', arguments)

    # --- forced environment, sync-before-launch ---

    def test_force_environment_matches_the_native_claude_colour_contract(self):
        self.run_main()
        force = self.agent_cli.launch_tab.call_args.kwargs['force']
        self.assertEqual(force, {'FORCE_COLOR': '1', 'TERM': 'xterm-256color'})

    def test_standards_are_synced_before_launch_in_order(self):
        self.run_main()
        self.assertEqual(
            [call[0] for call in self.call_order.mock_calls],
            ['resolve_claude_executable', 'sync_claude_standards', 'launch_tab'],
        )
        self.assertEqual(self.agent_cli.sync_claude_standards.call_args.kwargs.get('claude'), '/bin/claude')

    def test_stdio_is_hardened_against_encoding_errors(self):
        with mock.patch.object(self.agent_cli, 'make_stdio_encoding_lossy') as hardened:
            self.run_main()
        hardened.assert_called_once()

    # --- success message ---

    def test_success_message_with_no_selection_reports_the_cli_default_model(self):
        code, out, _ = self.run_main('--title', 'Tab Name')
        self.assertEqual(code, 0)
        self.assertIn("Launched claude handoff tab 'Tab Name' in", out)
        self.assertIn(os.path.abspath(self.directory), out)
        self.assertIn('on the CLI default model', out)
        self.assertIn(f'with prompt {self.prompt_path.resolve()}', out)

    def test_success_message_with_a_lane_reports_the_lane_model_and_effort(self):
        code, out, _ = self.run_main('--lane', 'L3')
        self.assertEqual(code, 0)
        self.assertIn(
            f"on lane L3 -> {CLAUDE_LANES['lanes']['L3']['model']} at {CLAUDE_LANES['lanes']['L3']['effort']}",
            out,
        )

    def test_success_message_with_a_lane_with_no_effort_omits_at(self):
        code, out, _ = self.run_main('--lane', 'L7')
        self.assertEqual(code, 0)
        self.assertIn(f"on lane L7 -> {CLAUDE_LANES['lanes']['L7']['model']} with prompt", out)

    def test_success_message_with_frontier_reports_the_frontier_tier_model_and_effort(self):
        code, out, _ = self.run_main('--frontier')
        self.assertEqual(code, 0)
        self.assertIn(
            f"on frontier -> {CLAUDE_LANES['frontier']['model']} at {CLAUDE_LANES['frontier']['effort']}",
            out,
        )

    def test_a_launch_error_from_launch_tab_is_reported_and_exits_nonzero(self):
        self.agent_cli.launch_tab.side_effect = self.agent_cli.LaunchError('no terminal detected')
        code, out, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('no terminal detected', err)
        self.assertNotIn('Launched', out)

    def test_a_launch_error_from_resolving_claude_is_reported_and_exits_nonzero(self):
        self.agent_cli.resolve_claude_executable.side_effect = self.agent_cli.LaunchError('no native claude found')
        code, out, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('no native claude found', err)
        self.assertEqual(out, '')
        self.agent_cli.launch_tab.assert_not_called()

    # --- H2: a LaunchTimeout is distinct from a definite failure ---

    def test_a_launch_timeout_exits_3_and_tells_the_caller_not_to_retry_blind(self):
        self.agent_cli.launch_tab.side_effect = self.agent_cli.LaunchTimeout(
            'Windows Terminal did not answer within 30 seconds; it may still have taken effect.'
        )
        code, out, err = self.run_main()
        self.assertEqual(code, 3)
        self.assertIn('did not answer within 30 seconds', err)
        self.assertIn('may already have opened', err)
        self.assertNotIn('Launched', out)

    # --- symlinked working directory ---

    def test_a_symlinked_working_directory_reaches_the_tab_as_given(self):
        link = Path(self.directory).parent / (Path(self.directory).name + ' link')
        try:
            link.symlink_to(self.directory)
        except OSError:
            self.skipTest('this filesystem or account does not allow creating a symlink')
        self.addCleanup(link.unlink)
        out, err = io.StringIO(), io.StringIO()
        argv = ['--working-directory', str(link), '--prompt-path', str(self.prompt_path)]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = LAUNCH_CLAUDE.main(argv)
        self.assertEqual(code, 0, err.getvalue())
        self.assertEqual(self.agent_cli.launch_tab.call_args.args[0], link)


class LaunchClaudeEndToEndTests(unittest.TestCase):
    """main() through the REAL agent_cli.launch_tab and open_claude_tab (H7) -- only
    resolve_claude_executable and sync_claude_standards are mocked. Exercises the real tmux handler, the
    real environment scrub and the real argument assembly, with only `subprocess.run` faked."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='launch claude e2e ')
        self.addCleanup(temp.cleanup)
        self.directory = temp.name
        self.prompt_path = Path(self.directory) / 'draft prompt.md'
        self.prompt_path.write_text('Read this and continue.\n')

        self.calls = []

        def fake_run(cmd, **kwargs):
            self.calls.append((cmd, kwargs))
            return subprocess.CompletedProcess(cmd, 0, stdout='', stderr='')

        self.agent_cli = launcher_test_support.real_agent_cli_for_e2e('agent_cli_for_launch_claude_e2e_tests', fake_run)

        windows_patcher = mock.patch.object(self.agent_cli, 'IS_WINDOWS', False)
        windows_patcher.start()
        self.addCleanup(windows_patcher.stop)

        load_patcher = mock.patch.object(LAUNCH_CLAUDE, '_load_agent_cli', return_value=self.agent_cli)
        load_patcher.start()
        self.addCleanup(load_patcher.stop)

        # Only TMUX is set, so the real detection order picks the tmux handler and nothing else (kitty,
        # Konsole and Windows Terminal are each gated on their own, otherwise-absent, environment variable).
        environ_patcher = mock.patch.dict(os.environ, {'TMUX': 'session'}, clear=True)
        environ_patcher.start()
        self.addCleanup(environ_patcher.stop)

    def test_main_reaches_the_real_tmux_handler_with_the_exact_expected_argv(self):
        argv = [
            '--working-directory', self.directory,
            '--prompt-path', str(self.prompt_path),
            '--title', 'e2e handoff',
            '--lane', 'L3',
        ]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = LAUNCH_CLAUDE.main(argv)
        self.assertEqual(code, 0, err.getvalue())
        self.assertEqual(len(self.calls), 1)
        cmd, kwargs = self.calls[0]

        self.assertEqual(cmd[:4], ['tmux', 'new-window', '-n', 'e2e handoff'])
        self.assertEqual(cmd[4], '--')
        inner = cmd[5:]
        directory = str(Path(os.path.abspath(self.directory)))
        self.assertEqual(inner[:5], ['sh', '-c', 'cd "$1" && shift && exec "$@"', 'sh', directory])
        self.assertEqual(inner[5], 'env')

        claude_index = inner.index('/bin/claude')
        expected_prompt_sentence = (
            f'Read the file at {self.prompt_path.resolve()} and follow its instructions, '
            'working from the current directory.'
        )
        self.assertEqual(
            inner[claude_index:],
            ['/bin/claude', '--model', CLAUDE_LANES['lanes']['L3']['model'],
             '--effort', CLAUDE_LANES['lanes']['L3']['effort'], expected_prompt_sentence],
        )

        env_args = inner[6:claude_index]
        self.assertIn('-u', env_args)
        self.assertIn('CLAUDECODE', env_args)
        self.assertIn('AGENT_CLI_TAB_TITLE=e2e handoff', env_args)
        self.assertIn('FORCE_COLOR=1', env_args)
        # TERM is never forced or cleared on POSIX: the terminal that starts the tab sets it itself.
        self.assertFalse(any(arg.startswith('TERM=') for arg in env_args))

        self.assertEqual(kwargs.get('stdin'), subprocess.DEVNULL)
        self.agent_cli.sync_claude_standards.assert_called_once()


class InstalledLayoutTests(unittest.TestCase):
    """Every layout the package ships launch_claude.py in must find the shared agent_cli.py beside it."""

    LAYOUTS = ('.agents/machine/utility', 'codex-skills', 'skills')

    def test_the_authored_and_every_packaged_copy_loads_agent_cli(self):
        copies = [SCRIPT] + [ROOT / 'plugins/machine' / layout / 'handoff-claude/scripts/launch_claude.py'
                             for layout in self.LAYOUTS]
        for copy in copies:
            with self.subTest(copy=str(copy.relative_to(ROOT))):
                self.assertTrue(copy.is_file(), f'{copy} is missing; run pwsh .agents/sync-generated.ps1 first')
                spec = importlib.util.spec_from_file_location(f'launch_claude_{abs(hash(copy))}', copy)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertTrue(callable(module._load_agent_cli().launch_tab))


if __name__ == '__main__':
    unittest.main()
