import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'base': (10, 7, [
        ('.agents/base/policy/plan-artifacts/scripts/session-context.py', []),
        ('hooks/tier_gate.py', ['--session-context']),
        ('.agents/base/policy/agent-files/scripts/session-context.py', []),
        ('.agents/base/policy/goal-continuation/scripts/session-context.py', []),
    ]),
    'engineering': (15, 12, [
        ('.agents/engineering/policy/session-guidance/scripts/session-context.py', []),
        ('hooks/worktree_cleanup_gate.py', []),
        ('hooks/merge_cleanup_gate.py', []),
    ]),
    'machine': (10, 7, [
        ('.agents/machine/utility/peer-cli/scripts/register_session.py', []),
        ('resources/machine/scripts/reap_orphans.py', ['--notice']),
        ('resources/machine/scripts/codex_terminal_profile.py', []),
        ('.agents/machine/utility/bootstrap-capabilities/scripts/harness_permissions_sync.py', ['--apply']),
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
            self.assertGreaterEqual(len(contexts), 3)

    def test_packaged_engineering_cleanup_block_survives_with_session_guidance(self):
        with tempfile.TemporaryDirectory(prefix='startup cleanup ') as temp:
            cwd = Path(temp)
            (cwd / '.agents').mkdir()
            (cwd / '.agents/worktree-cleanup-gate.json').write_text(json.dumps({
                'audit_command': [sys.executable, '-c', 'print("ORPHAN_FOLDER example")'],
            }), encoding='utf-8')
            plugin = ROOT / 'plugins/engineering'
            command = self.manifest('engineering')['hooks']['SessionStart'][0]['hooks'][0]['command']
            arguments = [arg.replace('${PLUGIN_ROOT}', plugin.as_posix())
                         for arg in shlex.split(command)[1:]]
            result = subprocess.run([sys.executable, *arguments], input=json.dumps({
                'hook_event_name': 'SessionStart', 'cwd': temp, 'session_id': str(uuid.uuid4()),
            }), capture_output=True, text=True, encoding='utf-8', cwd=cwd,
                env=dict(os.environ, TEMP=temp, TMP=temp, TMPDIR=temp), timeout=15)
            self.assertEqual(0, result.returncode, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual('block', output['decision'])
            self.assertIn('ORPHAN_FOLDER example', output['reason'])
            self.assertIn('engineering:plan-execution', output['hookSpecificOutput']['additionalContext'])


if __name__ == '__main__':
    unittest.main()
