"""Prove both hosts start one shared tier gate that leaves base policies to load from their descriptions."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class PolicyContextTests(unittest.TestCase):
    policies = ("agent-files", "project-setup", "solution-assessment", "task-routing")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="policy context ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / "profile with spaces"
        self.plugin = self.profile / "plugins" / "cache" / "tj-agents" / "base" / "local"
        shutil.copytree(ROOT / "plugins/base", self.plugin)
        self.cwd = self.root / "unrelated directory with spaces"
        self.cwd.mkdir()
        self.environment = dict(os.environ, CLAUDE_CONFIG_DIR=str(self.profile), CODEX_HOME=str(self.profile))

    def manifest(self, host):
        manifest_path = self.plugin / f".{host}-plugin/plugin.json"
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def handler(self, host):
        hooks = json.loads((self.plugin / self.manifest(host)["hooks"]).read_text(encoding="utf-8"))
        startup = hooks["hooks"]["SessionStart"]
        self.assertEqual(1, len(startup))
        self.assertEqual(1, len(startup[0]["hooks"]))
        return startup[0]["hooks"][0]

    def run_gate(self, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(self.plugin / "hooks/tier_gate.py"), *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=self.cwd,
            env=self.environment,
            timeout=20,
        )

    def test_both_host_manifests_dispatch_the_one_shared_gate_at_session_start(self):
        for host, variable in (("codex", "PLUGIN_ROOT"), ("claude", "CLAUDE_PLUGIN_ROOT")):
            with self.subTest(host=host):
                handler = self.handler(host)
                self.assertTrue((self.plugin / "hooks/tier_gate.py").is_file())
                if host == "claude":
                    self.assertEqual("tj_hook", handler["command"])
                    self.assertEqual(
                        ["--", "python", "-B", f"${{{variable}}}/hooks/tier_gate.py", "--session-context"],
                        handler["args"],
                    )
                else:
                    for variant in ("command", "commandWindows"):
                        self.assertIn(f'"${{{variable}}}/hooks/tier_gate.py"', handler[variant])
                        self.assertIn("--session-context", handler[variant])

    def test_no_base_policy_is_preloaded_and_the_call_is_read_only(self):
        before = snapshot(self.root)
        result = self.run_gate("--session-context", "--project", str(self.cwd))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] if result.stdout else ""
        for policy in self.policies:
            with self.subTest(policy=policy):
                self.assertNotIn(f"base:{policy}", context)
        self.assertEqual(before, snapshot(self.root))

    def test_every_base_policy_is_selectable_from_its_description(self):
        for policy in self.policies:
            with self.subTest(policy=policy):
                source = (self.plugin / f".agents/base/policy/{policy}/SKILL.md").read_text(encoding="utf-8")
                header = source.split("\n---\n", 1)[0]
                self.assertRegex(header, r"(?m)^description: .*\bUse (when|before)\b")


if __name__ == "__main__":
    unittest.main()
