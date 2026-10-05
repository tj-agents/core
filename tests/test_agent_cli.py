"""agent_cli.py: synthetic homes, PATHs and plugin registries only; the real profile is never read."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('agent_cli', ROOT / '.agents/machine/scripts/agent_cli.py')
CLI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CLI
SPEC.loader.exec_module(CLI)


# A model of what Windows Terminal does to `wt --window 0 new-tab ... --suppressApplicationTitle <exe>
# <args>` before the tab process sees it, ported from the C# stub in handoff-launchers.tests.ps1, where each
# stage was checked against a real wt.exe. First it splits its own argv on `;` into subcommands, unescaping
# `\;` to a literal `;` by dropping one backslash. Then it re-joins the tab command into one string, quoting
# a token only when it contains a space and escaping nothing inside it, and the tab process parses that
# string by CommandLineToArgvW rules.
def split_subcommands(args):
    commands, current = [], []
    for arg in args:
        token = ''
        for character in arg:
            if character != ';':
                token += character
            elif token.endswith('\\'):
                token = token[:-1] + ';'
            else:
                if token:
                    current.append(token)
                    token = ''
                commands.append(current)
                current = []
        if token:
            current.append(token)
    commands.append(current)
    return commands


def command_line_to_argv(line):
    """CommandLineToArgvW for every argument after argv[0], which this model never reads."""
    args, current, in_quotes, have_token, i = [], '', False, False, 0
    while i < len(line):
        character = line[i]
        if character == '\\':
            run = 0
            while i < len(line) and line[i] == '\\':
                run += 1
                i += 1
            if i < len(line) and line[i] == '"':
                current += '\\' * (run // 2)
                if run % 2:
                    current += '"'
                    i += 1
            else:
                current += '\\' * run
            have_token = True
            continue
        if character == '"':
            in_quotes = not in_quotes
            have_token = True
        elif character in ' \t' and not in_quotes:
            if have_token:
                args.append(current)
            current, have_token = '', False
        else:
            current += character
            have_token = True
        i += 1
    if have_token:
        args.append(current)
    return args[1:]


def deliver(command):
    start = command.index('--suppressApplicationTitle')
    joined = 'stub.exe' + ''.join(' ' + (f'"{token}"' if ' ' in token else token) for token in command[start + 1:])
    return command_line_to_argv(joined)


def through_windows_terminal(executable, *arguments):
    """(subcommand count, argv the tab process receives) for one escaped new-tab invocation."""
    argv = ['--window', '0', 'new-tab', '--startingDirectory', r'C:\work dir', '--title', 'a title',
            '--suppressApplicationTitle', executable, *arguments]
    commands = split_subcommands([CLI.terminal_argument(value) for value in argv])
    return len(commands), deliver(commands[0])


class TerminalArgumentTests(unittest.TestCase):
    CLAUDE = r'C:\Users\Test User\.local\bin\claude.exe'

    def assert_delivered(self, *arguments):
        count, delivered = through_windows_terminal(self.CLAUDE, *arguments)
        self.assertEqual(count, 1, 'a semicolon split the terminal command line into several subcommands')
        self.assertEqual(delivered, [self.CLAUDE, *arguments])

    def test_the_handoff_prompt_that_was_truncated_reaches_the_tab_whole(self):
        self.assert_delivered('Phase one: migrate Auth; then Search.\nPhase two: verify "end to end"; report back.')

    def test_a_spaced_executable_path_reaches_the_tab_whole(self):
        self.assert_delivered('--resume', 'a2bcd5c4-bf6d-4087-95e3-d7ba7f711875')

    def test_a_trailing_backslash_in_a_spaced_value_does_not_swallow_the_next_argument(self):
        self.assert_delivered('C:\\dir with space\\', 'next', 'C:\\two\\\\ trailing\\\\')

    def test_backslashes_before_a_quote_survive(self):
        self.assert_delivered('a\\"b c', 'a\\\\"b', '"', 'say "hi"')

    def test_backslashes_before_a_semicolon_survive(self):
        self.assert_delivered('x\\;y', 'a b\\;', 'a;b', ';', 'a\\\\;b c')

    def test_plain_values_pass_through_unchanged(self):
        for value in ('--resume', 'abc', r'C:\plain\path', 'model_reasoning_effort=high'):
            self.assertEqual(CLI.terminal_argument(value), value)

    def test_a_line_break_or_tab_without_a_space_is_refused_rather_than_dropped(self):
        for value in ('a\nb', 'a\r\nb', 'a\tb'):
            with self.assertRaises(CLI.LaunchError):
                CLI.terminal_argument(value)

    def test_an_empty_value_is_refused_rather_than_dropped(self):
        with self.assertRaises(CLI.LaunchError):
            CLI.terminal_argument('')

    def test_a_line_break_or_tab_beside_a_space_is_carried(self):
        self.assert_delivered('a b\nc', 'tab\there too')


class LaunchEnvironmentTests(unittest.TestCase):
    def test_session_state_is_cleared_and_forced_values_win_over_a_clear(self):
        cleared, forced = CLI.launch_environment(clear=('TERM', 'CLAUDECODE'), force={'NO_COLOR': '0', 'X': '1'})
        self.assertIn('CLAUDECODE', cleared)
        self.assertIn('CLAUDE_CODE_MESSAGING_SOCKET', cleared)
        self.assertIn('TERM', cleared)
        self.assertNotIn('NO_COLOR', cleared)
        self.assertEqual(len(cleared), len(set(cleared)))
        self.assertEqual(forced, {'NO_COLOR': '0', 'X': '1'})

    def test_machine_configuration_is_not_session_state(self):
        self.assertNotIn('CLAUDE_CODE_GIT_BASH_PATH', CLI.SESSION_ENVIRONMENT)


def executable(path, body='#!/bin/sh\nexit 0\n'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class ClaudeExecutableTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='agent cli ')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.name = 'claude.exe' if CLI.IS_WINDOWS else 'claude'

    def test_the_native_install_under_home_wins(self):
        native = executable(self.base / 'home' / '.local' / 'bin' / self.name, '\x7fELF')
        self.assertEqual(CLI.resolve_claude_executable(home=self.base / 'home', which=lambda _: None), str(native))

    @unittest.skipIf(CLI.IS_WINDOWS, 'the #! shim check is POSIX-only')
    def test_an_npm_shim_on_path_is_refused(self):
        shim = executable(self.base / 'npm' / 'claude', '#!/usr/bin/env node\n')
        with self.assertRaises(CLI.LaunchError):
            CLI.resolve_claude_executable(home=self.base / 'empty', which=lambda _: str(shim))

    @unittest.skipIf(CLI.IS_WINDOWS, 'the #! shim check is POSIX-only')
    def test_an_npm_shim_at_the_native_install_path_is_refused(self):
        executable(self.base / 'npm' / 'cli.js', '#!/usr/bin/env node\n')
        local = self.base / 'home' / '.local' / 'bin' / 'claude'
        local.parent.mkdir(parents=True)
        local.symlink_to(self.base / 'npm' / 'cli.js')
        native = executable(self.base / 'path' / 'claude', '\x7fELF')
        self.assertEqual(CLI.resolve_claude_executable(home=self.base / 'home', which=lambda _: str(native)), str(native))
        with self.assertRaises(CLI.LaunchError):
            CLI.resolve_claude_executable(home=self.base / 'home', which=lambda _: None)

    def test_a_native_binary_on_path_is_accepted(self):
        native = executable(self.base / 'path' / self.name, '\x7fELF')
        self.assertEqual(CLI.resolve_claude_executable(home=self.base / 'empty', which=lambda _: str(native)), str(native))


class CodexVersionTests(unittest.TestCase):
    def order(self, left, right):
        return CLI.compare_codex_version(CLI.parse_codex_version(left), CLI.parse_codex_version(right))

    def test_parses_the_cli_banner(self):
        version = CLI.parse_codex_version('codex-cli 0.160.0\n')
        self.assertEqual(version['core'], (0, 160, 0))
        self.assertEqual(version['text'], '0.160.0')
        self.assertIsNone(CLI.parse_codex_version('no version here'))

    def test_a_prerelease_ranks_below_its_release(self):
        self.assertEqual(self.order('0.151.0-alpha.7.1', '0.151.0'), -1)
        self.assertEqual(self.order('0.151.0', '0.150.9'), 1)
        self.assertEqual(self.order('0.151.0-alpha.10', '0.151.0-alpha.9'), 1)
        self.assertEqual(self.order('0.151.0-alpha', '0.151.0-alpha.1'), -1)
        self.assertEqual(self.order('0.151.0-beta', '0.151.0-alpha.9'), 1)
        self.assertEqual(self.order('1.2.3', '1.2.3'), 0)


@unittest.skipIf(CLI.IS_WINDOWS, 'stub executables here are POSIX shell scripts')
class CodexExecutableTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='agent cli ')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)

    def vendored(self, prefix, version):
        package = prefix / 'lib' / 'node_modules' / '@openai' / 'codex'
        executable(package / 'bin' / 'codex.js', '#!/usr/bin/env node\n')
        binary = executable(package / 'node_modules' / '@openai' / 'codex-linux-x64' / 'vendor' / 'x86_64-unknown-linux-musl' / 'bin' / 'codex',
                            f'#!/bin/sh\necho "codex-cli {version}"\n')
        shim = prefix / 'bin' / 'codex'
        shim.parent.mkdir(parents=True)
        shim.symlink_to(Path('..') / 'lib' / 'node_modules' / '@openai' / 'codex' / 'bin' / 'codex.js')
        return shim, binary

    def test_finds_the_vendored_binary_behind_a_posix_npm_symlink(self):
        shim, binary = self.vendored(self.base / 'npm global', '0.160.0')
        self.assertEqual(CLI.codex_candidate_paths(which=lambda _: str(shim)), [str(binary)])

    def test_skips_the_windows_desktop_cache_elsewhere(self):
        executable(self.base / 'appdata' / 'OpenAI' / 'Codex' / 'bin' / 'h' / 'codex.exe')
        self.assertEqual(CLI.codex_candidate_paths(which=lambda _: None, local_app_data=str(self.base / 'appdata')), [])

    def test_picks_the_newest_answering_candidate(self):
        old = executable(self.base / 'old', '#!/bin/sh\necho "codex-cli 0.155.0"\n')
        alpha = executable(self.base / 'alpha', '#!/bin/sh\necho "codex-cli 0.160.0-alpha.3"\n')
        new = executable(self.base / 'new', '#!/bin/sh\necho "codex-cli 0.160.0"\n')
        silent = executable(self.base / 'silent', '#!/bin/sh\nexit 1\n')
        path, version = CLI.resolve_codex_executable(candidates=[str(old), str(silent), str(new), str(alpha)])
        self.assertEqual((path, version['text']), (str(new), '0.160.0'))

    def test_refuses_a_build_below_the_minimum_and_lists_what_was_found(self):
        old = executable(self.base / 'old', '#!/bin/sh\necho "codex-cli 0.150.0"\n')
        with self.assertRaisesRegex(CLI.LaunchError, r'0\.150\.0.*below the required 0\.154\.0(?s:.*)old'):
            CLI.resolve_codex_executable(candidates=[str(old)])

    def test_refuses_when_nothing_answers(self):
        with self.assertRaises(CLI.LaunchError):
            CLI.resolve_codex_executable(candidates=[str(self.base / 'missing')])


class StandardsSyncTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='agent cli ')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.config = self.base / 'profile' / '.claude'
        (self.config / 'plugins').mkdir(parents=True)
        environment = {'CLAUDE_CONFIG_DIR': str(self.config)}
        patcher = mock.patch.dict(os.environ, environment)
        patcher.start()
        self.addCleanup(patcher.stop)
        for name in ('CLAUDE_CODE_PLUGIN_CACHE_DIR', 'USERPROFILE'):
            os.environ.pop(name, None)

    def register(self, install_path, scope='user'):
        registry = {'plugins': {'machine@base-agents': [{'scope': scope, 'installPath': str(install_path)}]}}
        (self.config / 'plugins' / 'installed_plugins.json').write_text(json.dumps(registry))

    def test_the_installed_user_plugin_copy_wins_and_receives_the_project_and_claude(self):
        install = self.base / 'install'
        script = install / 'resources' / 'machine' / 'scripts' / 'claude_standards_sync.py'
        script.parent.mkdir(parents=True)
        script.write_text('import sys\nprint("installed", *sys.argv[1:])\n')
        self.register(install)
        lines = []
        CLI.sync_claude_standards(self.base / 'project dir', claude='/bin/claude', out=lines.append)
        self.assertEqual(lines, [f'installed --project {self.base / "project dir"} --claude /bin/claude'])

    def test_falls_back_to_the_shipped_copy_without_a_user_install_or_userprofile(self):
        self.register(self.base / 'elsewhere', scope='project')
        self.assertEqual(CLI.standards_sync_script(), CLI.HERE / 'claude_standards_sync.py')

    def test_a_corrupt_registry_is_not_fatal(self):
        (self.config / 'plugins' / 'installed_plugins.json').write_text('{not json')
        self.assertEqual(CLI.standards_sync_script(), CLI.HERE / 'claude_standards_sync.py')


class LaneModelTests(unittest.TestCase):
    def table(self, harness):
        return json.loads((ROOT / '.agents/lanes' / f'{harness}.json').read_text(encoding='utf-8-sig'))

    def test_a_lane_resolves_to_its_tables_model_and_effort(self):
        for harness in ('claude', 'codex'):
            table = self.table(harness)
            effort_key = table.get('effort_key', 'effort')
            for lane, rung in table['lanes'].items():
                self.assertEqual(CLI.resolve_lane_model(harness, lane=lane), (rung['model'], rung.get(effort_key)))

    def test_the_frontier_tier_resolves_from_its_own_entry(self):
        for harness in ('claude', 'codex'):
            table = self.table(harness)
            if 'frontier' in table:
                self.assertEqual(CLI.resolve_lane_model(harness, frontier=True)[0], table['frontier']['model'])

    def test_lane_and_frontier_are_exclusive_and_one_is_required(self):
        for kwargs in ({}, {'lane': 'L1', 'frontier': True}):
            with self.assertRaises(CLI.LaunchError):
                CLI.resolve_lane_model('claude', **kwargs)

    def test_an_unknown_lane_is_an_error_not_a_fallback(self):
        with self.assertRaisesRegex(CLI.LaunchError, 'unknown lane'):
            CLI.resolve_lane_model('codex', lane='L9')


if __name__ == '__main__':
    unittest.main()
