"""Exercise the workflow session-lifecycle hook from a relocated, self-contained package."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ".agents/workflow/policy/session-lifecycle/scripts/session-context.py"
REMINDER = "Nothing owned left to do before this reply? Select `machine:close`."


class PackagedSessionLifecycleHook(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='workflow package with spaces ')
        self.addCleanup(temporary.cleanup)
        self.package = Path(temporary.name).resolve() / 'cache' / 'tj-agents' / 'workflow' / '1.0.0'
        shutil.copytree(ROOT / 'plugins/workflow', self.package)
        self.cwd = Path(temporary.name) / 'caller'
        self.cwd.mkdir()

    def run_hook(self, *arguments):
        return subprocess.run([sys.executable, '-B', str(self.package / SCRIPT), *arguments],
                              input=json.dumps({'cwd': str(self.cwd)}), capture_output=True, text=True,
                              encoding='utf-8', cwd=self.cwd, env=dict(os.environ, PYTHONIOENCODING='utf-8'),
                              timeout=20)

    def output(self, result):
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)['hookSpecificOutput']

    def test_session_start_carries_the_callout_lifecycle_and_finish_sections(self):
        output = self.output(self.run_hook())
        self.assertEqual('SessionStart', output['hookEventName'])
        context = output['additionalContext']
        self.assertIn('workflow:session-lifecycle (source SHA-256', context)
        self.assertIn(str(self.package / '.agents/workflow/policy/session-lifecycle/SKILL.md'), context)
        self.assertEqual(['## When the user calls out a mistake',
                          '## A task has an owning lifecycle — load it before the first edit',
                          '## Finish the session'],
                         [line for line in context.splitlines() if line.startswith('## ')])
        self.assertIn('Before returning a completed outcome, select `machine:close`', context)
        self.assertLess(len(context), 2500)
        self.assertEqual([], list(self.cwd.iterdir()))

    def test_each_prompt_carries_only_the_one_line_reminder(self):
        output = self.output(self.run_hook('--prompt'))
        self.assertEqual({'hookEventName': 'UserPromptSubmit', 'additionalContext': REMINDER}, output)

    def test_missing_contract_is_an_actionable_error(self):
        (self.package / '.agents/workflow/policy/session-lifecycle/SKILL.md').unlink()
        result = self.run_hook()
        self.assertNotEqual(0, result.returncode)
        self.assertIn('cannot read contract', result.stderr)
        self.assertEqual('', result.stdout)


class SessionInjectionManifests(unittest.TestCase):
    def manifest(self, host, plugin):
        path = ROOT / '.agents/plugins/manifests' / host / f'{plugin}-hooks.json'
        return json.loads(path.read_text(encoding='utf-8'))['hooks']

    def session_start_dispatch(self, host, plugin):
        hook = self.manifest(host, plugin)['SessionStart'][0]['hooks'][0]
        if host == 'claude':
            return [' '.join(hook['args'][-1:])]
        return [hook['command'], hook['commandWindows']]

    def test_each_plugin_injects_its_session_rules_once_at_session_start_on_both_hosts(self):
        for plugin, script in (('workflow', SCRIPT),
                               ('engineering', '.agents/engineering/policy/session/scripts/session-context.py')):
            for host in ('claude', 'codex'):
                with self.subTest(plugin=plugin, host=host):
                    for command in self.session_start_dispatch(host, plugin):
                        self.assertTrue(command.rstrip('"').endswith(script), command)

    def test_only_the_one_line_reminder_is_injected_per_prompt(self):
        claude = self.manifest('claude', 'workflow')['UserPromptSubmit'][0]['hooks'][0]
        self.assertEqual(['${CLAUDE_PLUGIN_ROOT}/' + SCRIPT, '--prompt'], claude['args'][-2:])
        codex = self.manifest('codex', 'workflow')['UserPromptSubmit'][0]['hooks'][0]
        for field in ('command', 'commandWindows'):
            self.assertTrue(codex[field].endswith(f'/{SCRIPT}" --prompt'))
        for host in ('claude', 'codex'):
            self.assertNotIn('UserPromptSubmit', self.manifest(host, 'engineering'))

if __name__ == '__main__':
    unittest.main()
