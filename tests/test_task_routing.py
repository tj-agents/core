import hashlib
import json
import os
import shlex
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def snapshot(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


class PolicyContextTests(unittest.TestCase):
    policies = ("task-routing", "idea-initialization")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="policy context ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plugin = self.root / "installed cache with spaces" / "tj-agents" / "base" / "local"
        shutil.copytree(ROOT / "plugins/base", self.plugin)
        self.cwd = self.root / "unrelated directory with spaces"
        self.cwd.mkdir()
        self.environment = dict(os.environ, PLUGIN_DATA=str(self.root / "data"), AGENT_STATE_DIRECTORY=str(self.root / "state"))
        self.environment.pop("TJ_AGENTS_STARTUP_SNAPSHOT_DIRECTORY", None)

    def manifest(self, host):
        manifest_path = self.plugin / f".{host}-plugin/plugin.json"
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def handler(self, host):
        hooks = json.loads((self.plugin / self.manifest(host)["hooks"]).read_text(encoding="utf-8"))
        startup = hooks["hooks"]["SessionStart"]
        self.assertEqual(1, len(startup))
        self.assertEqual(1, len(startup[0]["hooks"]))
        return startup[0]["hooks"][0]

    def invoke(self, policy, extra=()):
        script = self.plugin / f".agents/base/policy/{policy}/scripts/session-context.py"
        return subprocess.run(
            [sys.executable, "-B", str(script), *extra],
            input="{}",
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=self.cwd,
        )

    def dispatch_arguments(self, host, handler):
        variable = "CLAUDE_PLUGIN_ROOT" if host == "claude" else "PLUGIN_ROOT"
        if host == "claude":
            self.assertEqual("python", handler["command"])
            arguments = handler["args"]
        else:
            command = shlex.split(handler["command"])
            self.assertEqual("python3", command[0])
            arguments = command[1:]
        return [argument.replace(f"${{{variable}}}", self.plugin.as_posix()) for argument in arguments]

    def test_packaged_hooks_append_the_context_helper_for_both_hosts(self):
        for host, variable in (("codex", "PLUGIN_ROOT"), ("claude", "CLAUDE_PLUGIN_ROOT")):
            with self.subTest(host=host):
                handler = self.handler(host)
                for policy in self.policies:
                    helper = f".agents/base/policy/{policy}/scripts/session-context.py"
                    target = f"${{{variable}}}/{helper}"
                    if host == "claude":
                        self.assertIn(f"${{{variable}}}/hooks/hook_dispatch.py", handler["args"])
                        self.assertEqual(1, handler["args"].count(target))
                    else:
                        for variant in ("command", "commandWindows"):
                            self.assertIn(f'"${{{variable}}}/hooks/hook_dispatch.py"', handler[variant])
                            self.assertEqual(1, handler[variant].count(f'--hook "{target}"'))
                    self.assertTrue((self.plugin / helper).is_file())

    def test_context_has_its_own_identity_and_is_read_only_in_an_installed_path(self):
        for policy in self.policies:
            with self.subTest(policy=policy):
                before = snapshot(self.root)
                source = (self.plugin / f".agents/base/policy/{policy}/SKILL.md").read_text(encoding="utf-8")
                result = self.invoke(policy)
                self.assertEqual(0, result.returncode, result.stderr)
                output = json.loads(result.stdout)["hookSpecificOutput"]
                self.assertEqual("SessionStart", output["hookEventName"])
                self.assertTrue(output["additionalContext"].startswith(f"base:{policy} (source SHA-256 "))
                self.assertTrue(output["additionalContext"].endswith(source.split("\n---\n", 1)[1].strip()))
                self.assertEqual("", result.stderr)
                self.assertEqual(before, snapshot(self.root))

    def test_instruction_fallback_tracks_the_packaged_contract_digest(self):
        for policy in self.policies:
            with self.subTest(policy=policy):
                contract = self.plugin / f".agents/base/policy/{policy}/SKILL.md"
                digest = hashlib.sha256(contract.read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()
                result = self.invoke(policy, ("--instruction-fragment",))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn(f"<!-- BEGIN base:{policy} sha256:{digest} -->", result.stdout)
                self.assertIn(contract.read_text(encoding="utf-8-sig").split("\n---\n", 1)[1].strip(), result.stdout)

    def test_missing_or_malformed_contract_fails_without_changing_the_package(self):
        for policy in self.policies:
            with self.subTest(policy=policy):
                contract = self.plugin / f".agents/base/policy/{policy}/SKILL.md"
                original = contract.read_bytes()
                for content in (b"invalid contract", b"\xff"):
                    contract.write_bytes(content)
                    before = snapshot(self.root)
                    result = self.invoke(policy)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("cannot read contract", result.stderr)
                    self.assertEqual("", result.stdout)
                    self.assertEqual(before, snapshot(self.root))
                contract.unlink()
                result = self.invoke(policy)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(str(contract.resolve()), result.stderr)
                contract.write_bytes(original)

    def test_packaged_session_start_dispatches_both_policy_bodies(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                handler = self.handler(host)
                arguments = self.dispatch_arguments(host, handler)
                result = subprocess.run(
                    [sys.executable, *arguments],
                    input="{}",
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    cwd=self.cwd,
                    env=self.environment,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertEqual(1, context.count("base:task-routing (source SHA-256 "))
                for policy in self.policies:
                    body = (self.plugin / f".agents/base/policy/{policy}/SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()
                    self.assertIn(body, context)


if __name__ == "__main__":
    unittest.main()
