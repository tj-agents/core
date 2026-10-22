import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/base/policy/task-routing/scripts/session-context.py"
CONTRACT = ROOT / ".agents/base/policy/task-routing/SKILL.md"


class TaskRoutingContextTests(unittest.TestCase):
    def invoke(self, script=SCRIPT, extra=()):
        return subprocess.run(
            [sys.executable, "-B", str(script), *extra],
            input="{}",
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=20,
        )

    def test_context_is_session_start_and_digest_marked(self):
        result = self.invoke()
        self.assertEqual(0, result.returncode, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual("SessionStart", output["hookEventName"])
        self.assertTrue(output["additionalContext"].startswith("base:task-routing (source SHA-256 "))
        self.assertTrue(output["additionalContext"].endswith(CONTRACT.read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()))

    def test_instruction_fragment_tracks_the_contract(self):
        result = self.invoke(extra=("--instruction-fragment",))
        self.assertEqual(0, result.returncode, result.stderr)
        digest = hashlib.sha256(CONTRACT.read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()
        self.assertIn(f"<!-- BEGIN base:task-routing sha256:{digest} -->", result.stdout)

    def test_missing_contract_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "task-routing"
            shutil.copytree(SCRIPT.parent.parent, root)
            (root / "SKILL.md").unlink()
            result = self.invoke(root / "scripts/session-context.py")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("cannot read contract", result.stderr)

    def test_both_base_session_start_manifests_invoke_the_emitter_once(self):
        for host, path in (("codex", ".agents/plugins/manifests/codex/base-hooks.json"), ("claude", ".agents/plugins/manifests/claude/base-hooks.json")):
            with self.subTest(host=host):
                data = json.loads((ROOT / path).read_text(encoding="utf-8"))
                hook = data["hooks"]["SessionStart"][0]["hooks"][0]
                target = "task-routing/scripts/session-context.py"
                payloads = [hook.get("command", "") + " " + " ".join(hook.get("args", []))]
                if "commandWindows" in hook:
                    payloads.append(hook["commandWindows"])
                for payload in payloads:
                    self.assertEqual(1, payload.count(target))


if __name__ == "__main__":
    unittest.main()
