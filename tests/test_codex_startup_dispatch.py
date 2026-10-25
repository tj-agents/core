import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'base': (10, 7, [
        ('hooks/tier_gate.py', ['--session-context']),
        ('.agents/base/policy/agent-files/scripts/session-context.py', []),
        ('.agents/base/policy/idea-initialization/scripts/session-context.py', []),
        ('.agents/base/policy/task-routing/scripts/session-context.py', []),
    ]),
    'machine': (10, 7, [
        ('.agents/dependencies/agent/.agents/agent/utility/peer/scripts/register_session.py', []),
        ('resources/machine/scripts/reap_orphans.py', ['--notice']),
    ]),
}


class CodexStartupDispatchTests(unittest.TestCase):
    def manifest(self, package):
        return json.loads((ROOT / '.agents/plugins/manifests/codex' /
                           f'{package}-hooks.json').read_text(encoding='utf-8'))

    def test_one_launch_per_package_keeps_original_scripts_arguments_and_host_timeout(self):
        resources = json.loads((ROOT / '.agents/plugins/sources.json').read_text())['resources']
        for package, (timeout, deadline, scripts) in EXPECTED.items():
            with self.subTest(package=package):
                registrations = self.manifest(package)['hooks']['SessionStart']
                self.assertEqual(1, len(registrations))
                self.assertEqual(1, len(registrations[0]['hooks']))
                hook = registrations[0]['hooks'][0]
                self.assertEqual(timeout, hook['timeout'])
                for command, python in [('command', 'python3'), ('commandWindows', 'python')]:
                    expected = [python, '-B', '${PLUGIN_ROOT}/hooks/hook_dispatch.py',
                                '--deadline', str(deadline)]
                    for script, arguments in scripts:
                        expected.extend(['--hook', '${PLUGIN_ROOT}/' + script, *arguments])
                    self.assertEqual(expected, shlex.split(hook[command]))
                self.assertIn({'plugin': package, 'source': '.agents/hooks/hook_dispatch.py',
                               'destination': 'hooks/hook_dispatch.py'}, resources)
                self.assertTrue((ROOT / 'plugins' / package / 'hooks/hook_dispatch.py').is_file())

    def test_packaged_base_dispatch_aggregates_every_original_context(self):
        with tempfile.TemporaryDirectory(prefix='startup context ') as temp:
            cwd = Path(temp)
            plugin = ROOT / 'plugins/base'
            data = json.dumps({'hook_event_name': 'SessionStart', 'cwd': temp})
            contexts = []
            for script, arguments in EXPECTED['base'][2]:
                result = subprocess.run([sys.executable, '-B', str(plugin / script), *arguments],
                                        input=data, capture_output=True, text=True,
                                        encoding='utf-8', cwd=cwd, timeout=20)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual('', result.stderr)
                if result.stdout.strip():
                    contexts.append(json.loads(result.stdout)['hookSpecificOutput']['additionalContext'])
            command = self.manifest('base')['hooks']['SessionStart'][0]['hooks'][0]['command']
            arguments = [arg.replace('${PLUGIN_ROOT}', plugin.as_posix())
                         for arg in shlex.split(command)[1:]]
            result = subprocess.run([sys.executable, *arguments], input=data, capture_output=True,
                                    text=True, encoding='utf-8', cwd=cwd, timeout=10)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual('', result.stderr)
            output = json.loads(result.stdout)['hookSpecificOutput']
            self.assertEqual('SessionStart', output['hookEventName'])
            self.assertEqual('\n\n'.join(contexts), output['additionalContext'])
            self.assertGreaterEqual(len(contexts), 2)


if __name__ == '__main__':
    unittest.main()
