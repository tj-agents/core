"""Exercise selected engineering hooks from a relocated, self-contained package."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]


class PackagedEngineeringHooks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='engineering package with spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.package = self.root / 'cache' / 'tj-agents' / 'engineering' / '2.1.16'
        shutil.copytree(ROOT / 'plugins/engineering', self.package)
        self.cwd = self.root / 'unrelated caller'
        self.cwd.mkdir()
        review_cache = self.root / 'review cache'
        review_cache.mkdir()
        plugin_data = self.root / 'plugin data'
        self.environment = dict(os.environ, PLUGIN_ROOT=str(self.package),
                                CLAUDE_PLUGIN_ROOT=str(self.package), PYTHONIOENCODING='utf-8',
                                TMP=str(review_cache), TEMP=str(review_cache),
                                PLUGIN_DATA=str(plugin_data))

    def run_hook(self, path, data=None, arguments=()):
        payload = dict(cwd=str(self.cwd), session_id=str(uuid.uuid4()),
                       hook_event_name='PreToolUse', tool_use_id=str(uuid.uuid4()))
        payload.update(data or {})
        return subprocess.run([sys.executable, '-B', str(self.package / path), *arguments],
                              input=json.dumps(payload), capture_output=True, text=True,
                              encoding='utf-8', cwd=self.cwd, env=self.environment, timeout=20)

    def test_session_start_carries_the_callout_and_lifecycle_sections(self):
        contract = self.package / ".agents/engineering/policy/session/SKILL.md"
        result = self.run_hook(".agents/engineering/policy/session/scripts/session-context.py",
                               {"hook_event_name": "SessionStart"})
        self.assertEqual(0, result.returncode, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("SessionStart", output["hookEventName"])
        context = output["additionalContext"]
        self.assertIn("engineering:session (source SHA-256", context)
        self.assertIn(str(contract), context)
        self.assertIn("## When the user calls out a mistake", context)
        self.assertIn("before any host product feedback", " ".join(context.split()))
        self.assertIn("A bounded behavior change selects `engineering:feature`", context)
        self.assertNotIn("## Repository routine-decision delegation", context)
        self.assertLess(len(context), 2000)
        self.assertEqual([], list(self.cwd.iterdir()))

    def test_missing_session_contract_is_an_actionable_error(self):
        (self.package / ".agents/engineering/policy/session/SKILL.md").unlink()
        result = self.run_hook(".agents/engineering/policy/session/scripts/session-context.py")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("cannot read contract", result.stderr)
        self.assertEqual("", result.stdout)


if __name__ == '__main__':
    unittest.main()
