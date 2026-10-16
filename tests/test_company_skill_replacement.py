import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROUTERS = (ROOT / "plugins/base/hooks/skill_router.py",
           ROOT / "plugins/engineering/hooks/skill_router.py")
GATES = (ROOT / "plugins/base/hooks/tier_gate.py",
         ROOT / "plugins/engineering/hooks/tier_gate.py")


class CompanySkillReplacement(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        (self.repo / ".agents").mkdir(parents=True)
        (self.repo / "src").mkdir()
        (self.repo / "src/item.x").write_text("value\n", encoding="utf-8")
        (self.repo / ".agents/skill-routes.json").write_text(json.dumps({
            "routes": [{"path": "^src/", "skills": ["stackx:style", "stackx:logging"]}]
        }), encoding="utf-8")
        subprocess.run(["git", "init", "--quiet", str(self.repo)], check=True)
        self.remote("acme/project")
        self.profile = self.root / "profile"
        self.cache = self.profile / "plugins/cache"
        self.install("stackx", {"schema_version": 3, "tier": "stackx", "applies": "stack-present",
                                "detect": {"file": "src/item.x"}}, ("style", "logging"))
        self.install("acme", {"schema_version": 3, "tier": "acme", "applies": "stack-present",
                              "detect": {"all": [{"remote_host": "example.test"},
                                                 {"remote": "^acme/"}]},
                              "employer": {"context_skill": "context"}}, ("context",))
        self.company = self.install("acme-stackx", None, ("style",))

    def remote(self, identity):
        subprocess.run(["git", "-C", str(self.repo), "config", "remote.origin.url",
                        "git@example.test:" + identity + ".git"], check=True)

    def install(self, plugin, tier, skills):
        payload = self.cache / "market" / plugin / "1"
        for name in skills:
            path = payload / "skills" / name / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text("---\nname: " + name + "\ndescription: " + name
                            + " rule.\nkind: convention\n---\n", encoding="utf-8")
        if tier is not None:
            (payload / "tier.json").write_text(json.dumps(tier), encoding="utf-8")
        registry = self.cache.parent / "installed_plugins.json"
        data = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {"plugins": {}}
        data["plugins"][plugin + "@market"] = [{"installPath": str(payload)}]
        registry.write_text(json.dumps(data), encoding="utf-8")
        return payload

    def environment(self):
        return dict(os.environ, CLAUDE_CONFIG_DIR=str(self.profile),
                    CODEX_HOME=str(self.profile), HOME=str(self.root), USERPROFILE=str(self.root))

    def run_hook(self, path, *arguments, payload=None):
        return subprocess.run([sys.executable, "-B", str(path), *arguments], cwd=self.repo,
                              env=self.environment(), input=json.dumps(payload) if payload else None,
                              capture_output=True, text=True, encoding="utf-8", timeout=20)

    def query(self, router):
        result = self.run_hook(router, "--skills-for", "--json", "src/item.x")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["skills"]

    def test_both_packaged_routers_replace_only_installed_same_name_skills(self):
        for router in ROUTERS:
            with self.subTest(router=router):
                self.assertEqual(set(self.query(router)), {"acme-stackx:style", "stackx:logging"})
        self.remote("other/project")
        for router in ROUTERS:
            self.assertEqual(set(self.query(router)), {"stackx:style", "stackx:logging"})
        self.remote("acme/project")
        (self.company / "skills/style/SKILL.md").unlink()
        for router in ROUTERS:
            self.assertEqual(set(self.query(router)), {"stackx:style", "stackx:logging"})

    def test_uninstalled_company_plugin_falls_through(self):
        registry = self.cache.parent / "installed_plugins.json"
        data = json.loads(registry.read_text(encoding="utf-8"))
        del data["plugins"]["acme-stackx@market"]
        registry.write_text(json.dumps(data), encoding="utf-8")
        for router in ROUTERS:
            self.assertEqual(set(self.query(router)), {"stackx:style", "stackx:logging"})

    def test_both_packaged_gates_redirect_native_calls_and_read_paths(self):
        for gate in GATES:
            with self.subTest(gate=gate):
                payload = {"cwd": str(self.repo), "tool_name": "Skill",
                           "tool_input": {"skill": "stackx:style"}}
                result = self.run_hook(gate, payload=payload)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("acme-stackx:style", result.stderr)
                payload["tool_input"]["skill"] = "stackx:logging"
                self.assertEqual(self.run_hook(gate, payload=payload).returncode, 0)
                payload = {"cwd": str(self.repo), "tool_name": "PowerShell",
                           "tool_input": {"command": "Get-Content '" + str(
                               self.cache / "market/stackx/1/skills/style/SKILL.md") + "'"}}
                result = self.run_hook(gate, payload=payload)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("acme-stackx:style", result.stderr)
                context = self.run_hook(gate, "--session-context", "--project", str(self.repo))
                self.assertIn("acme-<stack>:<name>", context.stdout)


if __name__ == "__main__":
    unittest.main()
