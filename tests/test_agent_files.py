"""Prove both hosts start one shared tier gate and never preload the instruction-pair rule."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/base"
CONTRACT = PLUGIN / ".agents/base/skills/agent-files/SKILL.md"


class AgentFileTests(unittest.TestCase):
    def test_both_host_manifests_dispatch_exactly_one_shared_session_start_gate(self):
        for host in ("claude", "codex"):
            manifest = json.loads((PLUGIN / f".{host}-plugin/plugin.json").read_text(encoding="utf-8"))
            hooks = json.loads((PLUGIN / manifest["hooks"]).read_text(encoding="utf-8"))
            registrations = hooks["hooks"]["SessionStart"]
            self.assertEqual(1, len(registrations))
            self.assertEqual(1, len(registrations[0]["hooks"]))

    def test_the_shared_gate_never_preloads_the_agent_files_rule(self):
        with tempfile.TemporaryDirectory(prefix="agent files policy ") as temp:
            root = Path(temp)
            profile = root / "profile"
            plugin = profile / "plugins/cache/tj-agents/base/local"
            shutil.copytree(PLUGIN, plugin)
            project = root / "project"
            project.mkdir()
            environment = dict(os.environ, CLAUDE_CONFIG_DIR=str(profile), CODEX_HOME=str(profile))
            result = subprocess.run(
                [sys.executable, "-B", str(plugin / "hooks/tier_gate.py"),
                 "--session-context", "--project", str(project)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=environment,
                check=True,
            )
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] if result.stdout else ""
        self.assertNotIn("base:agent-files", context)
        self.assertNotIn(CONTRACT.read_text(encoding="utf-8").split("\n---\n", 1)[1].strip(), context)


if __name__ == "__main__":
    unittest.main()
