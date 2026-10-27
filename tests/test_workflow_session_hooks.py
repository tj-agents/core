"""Prove Workflow and Engineering register no hooks and Base alone starts the tier gate."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class NeitherWorkflowNorEngineeringRegistersItsOwnHook(unittest.TestCase):
    def manifest(self, host, plugin):
        path = ROOT / '.agents/plugins/manifests' / host / f'{plugin}.json'
        return json.loads(path.read_text(encoding='utf-8'))

    def test_workflow_and_engineering_ship_no_hooks_manifest_on_either_host(self):
        for plugin in ('workflow', 'engineering'):
            for host in ('claude', 'codex'):
                with self.subTest(plugin=plugin, host=host):
                    self.assertNotIn('hooks', self.manifest(host, plugin))
                    manifest_root = ROOT / '.agents/plugins/manifests' / host
                    self.assertFalse((manifest_root / f'{plugin}-hooks.json').exists())

    def test_only_base_registers_a_session_start_hook_on_either_host(self):
        for host in ('claude', 'codex'):
            manifest_root = ROOT / '.agents/plugins/manifests' / host
            self.assertTrue((manifest_root / 'base-hooks.json').is_file())
            hooks = json.loads((manifest_root / 'base-hooks.json').read_text(encoding='utf-8'))['hooks']
            self.assertEqual({'SessionStart'}, set(hooks))


if __name__ == '__main__':
    unittest.main()
