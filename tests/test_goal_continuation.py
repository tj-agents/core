"""Package-level checks for the base goal-continuation context hook."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}


class GoalContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="goal continuation ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plugin = self.root / "installed cache with spaces" / "base package with spaces"
        shutil.copytree(ROOT / "plugins/base", self.plugin)
        self.cwd = self.root / "unrelated directory with spaces"
        self.cwd.mkdir()

    def manifest(self, host):
        manifest_path = self.plugin / f".{host}-plugin/plugin.json"
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def invoke(self, extra=()):
        script = self.plugin / ".agents/base/policy/goal-continuation/scripts/session-context.py"
        return subprocess.run([sys.executable, "-B", str(script), *extra], input="{}", text=True,
                              encoding="utf-8", capture_output=True, cwd=self.cwd)

    def test_packaged_hooks_append_the_context_helper_for_both_hosts(self):
        for host, variable in (("codex", "PLUGIN_ROOT"), ("claude", "CLAUDE_PLUGIN_ROOT")):
            hooks = json.loads((self.plugin / self.manifest(host)["hooks"]).read_text(encoding="utf-8"))
            startup = hooks["hooks"]["SessionStart"]
            helper = ".agents/base/policy/goal-continuation/scripts/session-context.py"
            self.assertEqual(len(startup), 4)
            handler = startup[3]["hooks"][0]
            if host == "claude":
                self.assertEqual(handler["command"], f'python -B "${{{variable}}}/{helper}"')
            else:
                self.assertIn(f'"${{{variable}}}/{helper}"', handler["command"])
                self.assertIn(f'"${{{variable}}}/{helper}"', handler["commandWindows"])
            self.assertTrue((self.plugin / helper).is_file())

    def test_context_has_its_own_identity_and_is_read_only_in_an_installed_path(self):
        before = snapshot(self.root)
        source = (self.plugin / ".agents/base/policy/goal-continuation/SKILL.md").read_text(encoding="utf-8")
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertTrue(output["additionalContext"].startswith("base:goal-continuation (source SHA-256 "))
        self.assertTrue(output["additionalContext"].endswith(source.split("\n---\n", 1)[1].strip()))
        self.assertEqual(result.stderr, "")
        self.assertEqual(before, snapshot(self.root))

    def test_instruction_fallback_tracks_the_packaged_contract_digest(self):
        contract = self.plugin / ".agents/base/policy/goal-continuation/SKILL.md"
        digest = hashlib.sha256(contract.read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()
        result = self.invoke(("--instruction-fragment",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"<!-- BEGIN base:goal-continuation sha256:{digest} -->", result.stdout)
        self.assertIn(contract.read_text(encoding="utf-8-sig").split("\n---\n", 1)[1].strip(), result.stdout)

    def test_missing_or_malformed_contract_fails_without_changing_the_package(self):
        contract = self.plugin / ".agents/base/policy/goal-continuation/SKILL.md"
        original = contract.read_bytes()
        for content in (b"invalid contract", b"\xff"):
            contract.write_bytes(content)
            before = snapshot(self.root)
            result = self.invoke()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot read contract", result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(before, snapshot(self.root))
        contract.unlink()
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(str(contract.resolve()), result.stderr)
        contract.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
