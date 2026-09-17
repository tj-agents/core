import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


HOOKS_DIR = Path(__file__).resolve().parents[1]
HOOK_SRC = HOOKS_DIR / "always_on_instructions.py"
RUNTIME_SRC = HOOKS_DIR / "hook_runtime.py"
RULES_SRC = HOOKS_DIR / "dev_rules.py"
INSTRUCTIONS_TEXT = "# Always-on instructions\n\nTake the scalable approach. Questions before actions.\n"


class AlwaysOnInstructionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name).resolve()

        # A plugin layout: hooks/ beside standards/, so own_payload_root resolves the doc.
        self.plugin = base / "plugin"
        (self.plugin / "hooks").mkdir(parents=True)
        shutil.copy(HOOK_SRC, self.plugin / "hooks" / "always_on_instructions.py")
        shutil.copy(RUNTIME_SRC, self.plugin / "hooks" / "hook_runtime.py")
        shutil.copy(RULES_SRC, self.plugin / "hooks" / "dev_rules.py")
        self.instructions_doc = self.plugin / "standards" / "process" / "ALWAYS_ON_INSTRUCTIONS.md"
        self.instructions_doc.parent.mkdir(parents=True)
        self.instructions_doc.write_text(INSTRUCTIONS_TEXT, encoding="utf-8")
        self.hook = self.plugin / "hooks" / "always_on_instructions.py"

        # A standards-managed repo: opts in by carrying the route table.
        self.repo = base / "repo"
        (self.repo / ".agents").mkdir(parents=True)
        (self.repo / ".agents" / "skill-routes.json").write_text('{"routes": []}', encoding="utf-8")

        # A consuming repo vendors the executable hook but deliberately not the plugin's instructions payload.
        vendored_hooks = self.repo / ".agents" / "hooks"
        vendored_hooks.mkdir()
        shutil.copy(HOOK_SRC, vendored_hooks / "always_on_instructions.py")
        shutil.copy(RUNTIME_SRC, vendored_hooks / "hook_runtime.py")
        shutil.copy(RULES_SRC, vendored_hooks / "dev_rules.py")
        self.vendored_hook = vendored_hooks / "always_on_instructions.py"

    def tearDown(self):
        self.temp.cleanup()

    def run_hook(self, cwd=None, payload=None, env_root=True, hook=None):
        data = {"hook_event_name": "SessionStart", "session_id": str(uuid.uuid4())}
        if cwd is not None:
            data["cwd"] = str(cwd)
        if payload is not None:
            data = payload
        env = dict(os.environ)
        if env_root:
            env["CLAUDE_PLUGIN_ROOT"] = str(self.plugin)
        else:
            for name in ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "CODEX_PLUGIN_ROOT"):
                env.pop(name, None)
        return subprocess.run(
            [sys.executable, str(hook or self.hook)],
            input=json.dumps(data),
            capture_output=True,
            text=True,
            env=env,
        )

    def test_injects_instructions_in_standards_repo(self):
        result = self.run_hook(cwd=self.repo)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Always-on instructions", result.stdout)

    def test_injects_from_subdirectory(self):
        sub = self.repo / "api" / "Service"
        sub.mkdir(parents=True)
        result = self.run_hook(cwd=sub)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Always-on instructions", result.stdout)

    def test_silent_outside_standards_repo(self):
        plain = Path(self.temp.name) / "plain"
        plain.mkdir()
        result = self.run_hook(cwd=plain)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    def test_silent_when_instructions_doc_missing(self):
        self.instructions_doc.unlink()
        result = self.run_hook(cwd=self.repo)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    def test_payloadless_vendored_copy_does_not_suppress_plugin_copy(self):
        payload = {
            "hook_event_name": "SessionStart",
            "session_id": str(uuid.uuid4()),
            "turn_id": "session-start",
            "cwd": str(self.repo),
        }

        vendored = self.run_hook(payload=payload, hook=self.vendored_hook)
        plugin = self.run_hook(payload=payload)

        self.assertEqual(vendored.returncode, 0)
        self.assertEqual(vendored.stdout.strip(), "")
        self.assertEqual(plugin.returncode, 0)
        self.assertIn("Always-on instructions", plugin.stdout)

    def test_survives_empty_stdin(self):
        result = subprocess.run(
            [sys.executable, str(self.hook)],
            input="",
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(self.plugin)},
        )
        self.assertEqual(result.returncode, 0)

    def test_survives_malformed_stdin(self):
        result = subprocess.run(
            [sys.executable, str(self.hook)],
            input="{not json",
            capture_output=True,
            text=True,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(self.plugin)},
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
