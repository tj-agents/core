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

    def test_session_start_carries_only_the_finish_section(self):
        output = self.output(self.run_hook())
        self.assertEqual('SessionStart', output['hookEventName'])
        context = output['additionalContext']
        self.assertIn('workflow:session-lifecycle (source SHA-256', context)
        self.assertIn(str(self.package / '.agents/workflow/policy/session-lifecycle/SKILL.md'), context)
        self.assertIn('Before returning a completed outcome, select `machine:close`', context)
        self.assertNotIn('## ', context)
        self.assertLess(len(context), 1000)
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

    def test_workflow_injects_the_lifecycle_on_both_hosts(self):
        claude = self.manifest('claude', 'workflow')
        self.assertEqual('${CLAUDE_PLUGIN_ROOT}/' + SCRIPT, claude['SessionStart'][0]['hooks'][0]['args'][-1])
        self.assertEqual(['${CLAUDE_PLUGIN_ROOT}/' + SCRIPT, '--prompt'],
                         claude['UserPromptSubmit'][0]['hooks'][0]['args'][-2:])
        codex = self.manifest('codex', 'workflow')
        for field in ('command', 'commandWindows'):
            self.assertTrue(codex['SessionStart'][0]['hooks'][0][field].endswith(f'/{SCRIPT}"'))
            self.assertTrue(codex['UserPromptSubmit'][0]['hooks'][0][field].endswith(f'/{SCRIPT}" --prompt'))

    def test_engineering_injects_no_session_text(self):
        for host in ('claude', 'codex'):
            hooks = self.manifest(host, 'engineering')
            self.assertNotIn('SessionStart', hooks)
            self.assertNotIn('UserPromptSubmit', hooks)


if __name__ == '__main__':
    unittest.main()
