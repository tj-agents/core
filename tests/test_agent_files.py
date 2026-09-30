"""Prove the universal instruction-pair rule ships to both hosts."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/base"
SCRIPT = PLUGIN / ".agents/base/contract/agent-files/scripts/session-context.py"
CONTRACT = PLUGIN / ".agents/base/contract/agent-files/SKILL.md"


class AgentFileTests(unittest.TestCase):
    def test_both_host_hooks_load_the_packaged_base_rule(self):
        for host in ("claude", "codex"):
            manifest = json.loads((PLUGIN / f".{host}-plugin/plugin.json").read_text(encoding="utf-8"))
            hooks = json.loads((PLUGIN / manifest["hooks"]).read_text(encoding="utf-8"))
            commands = [item["hooks"][0]["command"] for item in hooks["hooks"]["SessionStart"]]
            self.assertEqual(1, sum("agent-files/scripts/session-context.py" in command for command in commands))
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            capture_output=True,
            text=True,
            check=True,
        )
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("base:agent-files", context)
        self.assertIn(CONTRACT.read_text(encoding="utf-8").split("\n---\n", 1)[1].strip(), context)
        self.assertIn("@AGENTS.md", context)


if __name__ == "__main__":
    unittest.main()
