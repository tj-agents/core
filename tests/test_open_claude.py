"""open_claude.py: option validation and argument assembly, with launch_tab/sync/resolve stubbed."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.agents/machine/utility/open-claude/scripts/open_claude.py'
SPEC = importlib.util.spec_from_file_location('open_claude', SCRIPT)
OPEN_CLAUDE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = OPEN_CLAUDE
SPEC.loader.exec_module(OPEN_CLAUDE)


class StubLaunchError(Exception):
    pass


def stub_agent_cli(claude='/bin/claude'):
    stub = types.SimpleNamespace(LaunchError=StubLaunchError)
    stub.resolve_claude_executable = mock.Mock(return_value=claude)
    stub.sync_claude_standards = mock.Mock()
    stub.launch_tab = mock.Mock()
    return stub


class OpenClaudeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='open claude ')
        self.addCleanup(temp.cleanup)
        self.directory = temp.name
        self.stub = stub_agent_cli()
        patcher = mock.patch.object(OPEN_CLAUDE, '_load_agent_cli', return_value=self.stub)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = OPEN_CLAUDE.main(['--working-directory', self.directory, *args])
        return code, out.getvalue(), err.getvalue()

    # --- option validation ---

    def test_resume_and_continue_are_mutually_exclusive(self):
        code, _, err = self.run_main('--resume', 'abc', '--continue')
        self.assertEqual(code, 1)
        self.assertIn('not both', err)
        self.stub.launch_tab.assert_not_called()

    def test_prompt_and_prompt_path_are_mutually_exclusive(self):
        code, _, err = self.run_main('--prompt', 'hi', '--prompt-path', '/tmp/whatever')
        self.assertEqual(code, 1)
        self.assertIn('not both', err)
        self.stub.launch_tab.assert_not_called()

    def test_a_long_inline_prompt_is_rejected(self):
        code, _, err = self.run_main('--prompt', 'x' * 501)
        self.assertEqual(code, 1)
        self.assertIn('--prompt-path', err)
        self.stub.launch_tab.assert_not_called()

    def test_a_prompt_path_that_is_not_a_file_is_rejected(self):
        code, _, err = self.run_main('--prompt-path', self.directory)
        self.assertEqual(code, 1)
        self.assertIn('is not a file', err)
        self.stub.launch_tab.assert_not_called()

    def test_a_missing_working_directory_is_rejected(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = OPEN_CLAUDE.main(['--working-directory', str(Path(self.directory) / 'missing')])
        self.assertEqual(code, 1)
        self.assertIn('not a directory', err.getvalue())
        self.stub.launch_tab.assert_not_called()

    def test_a_symlinked_working_directory_reaches_the_tab_as_given(self):
        link = Path(self.directory).parent / (Path(self.directory).name + ' link')
        try:
            link.symlink_to(self.directory)
        except OSError:
            self.skipTest('this filesystem or account does not allow creating a symlink')
        self.addCleanup(link.unlink)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = OPEN_CLAUDE.main(['--working-directory', str(link)])
        self.assertEqual(code, 0, err.getvalue())
        self.assertEqual(self.stub.launch_tab.call_args.args[0], link)

    # --- argument assembly ---

    def test_resume_reaches_launch_tab_as_resume_flag_and_id(self):
        self.run_main('--resume', 'a2bcd5c4-bf6d-4087-95e3-d7ba7f711875')
        arguments = self.stub.launch_tab.call_args.kwargs['arguments']
        self.assertIn('--resume', arguments)
        self.assertIn('a2bcd5c4-bf6d-4087-95e3-d7ba7f711875', arguments)

    def test_continue_reaches_launch_tab(self):
        self.run_main('--continue')
        arguments = self.stub.launch_tab.call_args.kwargs['arguments']
        self.assertIn('--continue', arguments)

    def test_model_reaches_launch_tab(self):
        self.run_main('--model', 'claude-sonnet-5')
        arguments = self.stub.launch_tab.call_args.kwargs['arguments']
        self.assertEqual(arguments[arguments.index('--model') + 1], 'claude-sonnet-5')

    def test_dangerously_skip_permissions_reaches_launch_tab(self):
        self.run_main('--dangerously-skip-permissions')
        arguments = self.stub.launch_tab.call_args.kwargs['arguments']
        self.assertIn('--dangerously-skip-permissions', arguments)

    def test_an_inline_prompt_is_passed_through(self):
        self.run_main('--prompt', 'a short instruction')
        arguments = self.stub.launch_tab.call_args.kwargs['arguments']
        self.assertIn('a short instruction', arguments)

    def test_a_prompt_path_becomes_the_read_the_file_sentence(self):
        prompt_path = Path(self.directory) / 'draft.md'
        prompt_path.write_text('do the thing\n')
        self.run_main('--prompt-path', str(prompt_path))
        arguments = self.stub.launch_tab.call_args.kwargs['arguments']
        sentence = next(a for a in arguments if a.startswith('Read the file at'))
        self.assertIn(str(prompt_path.resolve()), sentence)
        self.assertIn('working from the current directory', sentence)

    def test_no_session_or_prompt_flags_means_no_extra_arguments(self):
        self.run_main()
        arguments = self.stub.launch_tab.call_args.kwargs['arguments']
        self.assertEqual(arguments, [])

    def test_force_environment_matches_the_native_claude_colour_contract(self):
        self.run_main()
        force = self.stub.launch_tab.call_args.kwargs['force']
        self.assertEqual(force, {'FORCE_COLOR': '1', 'TERM': 'xterm-256color'})

    def test_the_resolved_claude_executable_and_title_are_used(self):
        self.stub.resolve_claude_executable.return_value = '/opt/claude'
        self.run_main('--title', 'My Tab')
        args, kwargs = self.stub.launch_tab.call_args
        self.assertEqual(args[1], '/opt/claude')
        self.assertEqual(args[2], 'My Tab')

    def test_standards_are_synced_before_launch(self):
        self.run_main()
        self.stub.sync_claude_standards.assert_called_once()
        self.assertEqual(self.stub.sync_claude_standards.call_args.kwargs.get('claude'), '/bin/claude')

    def test_success_prints_the_launched_message(self):
        code, out, _ = self.run_main('--title', 'Tab Name')
        self.assertEqual(code, 0)
        self.assertIn("Launched claude tab 'Tab Name' in", out)
        self.assertIn(os.path.abspath(self.directory), out)

    def test_a_launch_error_from_resolving_claude_is_reported_and_exits_nonzero(self):
        self.stub.resolve_claude_executable.side_effect = StubLaunchError('no native claude found')
        code, out, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('no native claude found', err)
        self.assertEqual(out, '')
        self.stub.launch_tab.assert_not_called()

    def test_a_launch_error_from_launch_tab_is_reported_and_exits_nonzero(self):
        self.stub.launch_tab.side_effect = StubLaunchError('no terminal detected')
        code, out, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('no terminal detected', err)
        self.assertNotIn('Launched', out)


class InstalledLayoutTests(unittest.TestCase):
    """Every layout the package ships open_claude.py in must find the shared agent_cli.py beside it."""

    LAYOUTS = ('.agents/machine/utility', 'codex-skills', 'skills')

    def test_the_authored_and_every_packaged_copy_loads_agent_cli(self):
        copies = [SCRIPT] + [ROOT / 'plugins/machine' / layout / 'open-claude/scripts/open_claude.py'
                             for layout in self.LAYOUTS]
        for copy in copies:
            with self.subTest(copy=str(copy.relative_to(ROOT))):
                self.assertTrue(copy.is_file(), f'{copy} is missing; run pwsh .agents/sync-generated.ps1 first')
                spec = importlib.util.spec_from_file_location(f'open_claude_{abs(hash(copy))}', copy)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertTrue(callable(module._load_agent_cli().launch_tab))


if __name__ == '__main__':
    unittest.main()
