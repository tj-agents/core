import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
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
        self.install("acme-stackx", None, ("style",))

    def remote(self, identity):
        subprocess.run(["git", "-C", str(self.repo), "config", "remote.origin.url",
                        "git@example.test:" + identity + ".git"], check=True)

    def install(self, plugin, tier, skills):
        payload = self.cache / "market" / plugin / "1"
        for name in skills:
            path = payload / "skills" / name / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text("---\nname: " + name + "\ndescription: " + name
                            + " rule.\nkind: standard\n---\n", encoding="utf-8")
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

    def test_both_packaged_gates_name_the_company_replacement_at_session_start(self):
        for gate in GATES:
            with self.subTest(gate=gate):
                context = self.run_hook(gate, "--session-context", "--project", str(self.repo))
                self.assertIn("acme-<stack>:<name>", context.stdout)


if __name__ == "__main__":
    unittest.main()
