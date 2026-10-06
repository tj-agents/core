"""launch_claude.py: option validation, argument assembly and real lane resolution, with
launch_tab/sync/resolve_claude_executable stubbed but resolve_lane_model left real."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.agents/machine/utility/handoff-claude/scripts/launch_claude.py'
AGENT_CLI = ROOT / '.agents/machine/scripts/agent_cli.py'
CLAUDE_LANES = json.loads((ROOT / '.agents/lanes/claude.json').read_text(encoding='utf-8'))

SPEC = importlib.util.spec_from_file_location('launch_claude', SCRIPT)
LAUNCH_CLAUDE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LAUNCH_CLAUDE
SPEC.loader.exec_module(LAUNCH_CLAUDE)


def real_agent_cli(claude='/bin/claude'):
    """The real shared library, so resolve_lane_model resolves through the real lane tables; only the
    three functions that would otherwise touch a real executable or terminal are replaced."""
    spec = importlib.util.spec_from_file_location('agent_cli_for_launch_claude_tests', AGENT_CLI)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.resolve_claude_executable = mock.Mock(return_value=claude)
    module.sync_claude_standards = mock.Mock()
    module.launch_tab = mock.Mock()
    return module


class LaunchClaudeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='launch claude ')
        self.addCleanup(temp.cleanup)
        self.directory = temp.name
        self.prompt_path = Path(self.directory) / 'draft prompt.md'
        self.prompt_path.write_text('Read this and continue.\n')
        self.agent_cli = real_agent_cli()
        patcher = mock.patch.object(LAUNCH_CLAUDE, '_load_agent_cli', return_value=self.agent_cli)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_main(self, *args):
        argv = ['--working-directory', self.directory, '--prompt-path', str(self.prompt_path), *args]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = LAUNCH_CLAUDE.main(argv)
        return code, out.getvalue(), err.getvalue()

    # --- validation ---

    def test_a_missing_working_directory_is_rejected(self):
        out, err = io.StringIO(), io.StringIO()
        argv = ['--working-directory', str(Path(self.directory) / 'missing'),
                '--prompt-path', str(self.prompt_path)]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = LAUNCH_CLAUDE.main(argv)
        self.assertEqual(code, 1)
        self.assertIn('not a directory', err.getvalue())
        self.agent_cli.launch_tab.assert_not_called()

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

    # --- forced environment, sync-before-launch ---

    def test_force_environment_matches_the_native_claude_colour_contract(self):
        self.run_main()
        force = self.agent_cli.launch_tab.call_args.kwargs['force']
        self.assertEqual(force, {'FORCE_COLOR': '1', 'TERM': 'xterm-256color'})

    def test_standards_are_synced_before_launch(self):
        self.run_main()
        self.agent_cli.sync_claude_standards.assert_called_once()
        self.assertEqual(self.agent_cli.sync_claude_standards.call_args.kwargs.get('claude'), '/bin/claude')
        self.agent_cli.launch_tab.assert_called_once()

    # --- success message ---

    def test_success_message_with_no_selection_reports_the_cli_default_model(self):
        code, out, _ = self.run_main('--title', 'Tab Name')
        self.assertEqual(code, 0)
        self.assertIn("Launched claude handoff tab 'Tab Name' in", out)
        self.assertIn(os.path.abspath(self.directory), out)
        self.assertIn('on the CLI default model', out)
        self.assertIn(f'with prompt {self.prompt_path.resolve()}', out)

    def test_success_message_with_a_lane_reports_the_lane_and_resolved_model(self):
        code, out, _ = self.run_main('--lane', 'L3')
        self.assertEqual(code, 0)
        self.assertIn(f"on lane L3 -> {CLAUDE_LANES['lanes']['L3']['model']}", out)

    def test_success_message_with_frontier_reports_the_frontier_tier_and_model(self):
        code, out, _ = self.run_main('--frontier')
        self.assertEqual(code, 0)
        self.assertIn(f"on frontier -> {CLAUDE_LANES['frontier']['model']}", out)

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
