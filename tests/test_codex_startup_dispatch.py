import json
from pathlib import Path
import shlex
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CodexStartupDispatchTests(unittest.TestCase):
    def manifest(self, package):
        return json.loads((ROOT / '.agents/plugins/manifests/codex' /
                           f'{package}-hooks.json').read_text(encoding='utf-8'))

    def test_the_one_shared_gate_is_the_only_registered_codex_startup_hook(self):
        registrations = self.manifest('base')['hooks']['SessionStart']
        self.assertEqual(1, len(registrations))
        self.assertEqual(1, len(registrations[0]['hooks']))
        hook = registrations[0]['hooks'][0]
        self.assertEqual(30, hook['timeout'])
        for field, python in (('command', 'python3'), ('commandWindows', 'python')):
            expected = [python, '-B', '${PLUGIN_ROOT}/hooks/tier_gate.py', '--session-context']
            self.assertEqual(expected, shlex.split(hook[field]))

    def test_no_other_package_declares_a_codex_hooks_manifest_source(self):
        resources = json.loads((ROOT / '.agents/plugins/sources.json').read_text(encoding='utf-8'))
        self.assertEqual({'base'}, set(resources['host_hook_sources']))
        for package in ('engineering', 'workflow'):
            self.assertFalse((ROOT / '.agents/plugins/manifests/codex' / f'{package}-hooks.json').exists())
            self.assertFalse((ROOT / '.agents/plugins/manifests/claude' / f'{package}-hooks.json').exists())


if __name__ == '__main__':
    unittest.main()
