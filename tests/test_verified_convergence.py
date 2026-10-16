import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/machine/scripts/verified_convergence.py"
ROLLING_SCRIPT = ROOT / ".agents/machine/scripts/rolling_plugins.py"
SPEC = importlib.util.spec_from_file_location("verified_convergence", SCRIPT)
CONVERGENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONVERGENCE)
ROLLING_SPEC = importlib.util.spec_from_file_location("rolling_plugins", ROLLING_SCRIPT)
ROLLING = importlib.util.module_from_spec(ROLLING_SPEC)
sys.modules[ROLLING_SPEC.name] = ROLLING
ROLLING_SPEC.loader.exec_module(ROLLING)


def digest(path):
    return CONVERGENCE._normalized_digest(path)


class VerifiedConvergenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / "engineering"
        (self.package / "codex-agents").mkdir(parents=True)
        (self.package / "workflows/hosts").mkdir(parents=True)
        self.agent = self.package / "codex-agents/lane-l1.toml"
        self.agent.write_text("model = 'old'\n", encoding="utf-8")
        self.delivery({})
        self.environ = {"CODEX_HOME": str(self.root / "codex")}

    def delivery(self, known):
        (self.package / "workflows/hosts/agent-delivery.json").write_text(json.dumps({"generated_agent_patterns": ["lane-*.toml"], "former_managed_agents": ["workflow-lane.toml"], "project_managed_agent_sha256": known}), encoding="utf-8")

    def converge(self):
        root = ROLLING.VerifiedRoot("engineering@base-agents", self.package, "a" * 40, "https://github.com/tj-agents/core.git")
        CONVERGENCE.converge(self.environ, self.root / "project", [root])

    def target(self):
        return Path(self.environ["CODEX_HOME"]) / "agents"

    def test_install_replace_and_retire_owned_agents(self):
        self.converge()
        installed = self.target() / "lane-l1.toml"
        self.assertEqual(self.agent.read_text(encoding="utf-8"), installed.read_text(encoding="utf-8"))
        self.agent.write_text("model = 'new'\n", encoding="utf-8")
        self.converge()
        self.assertEqual("model = 'new'\n", installed.read_text(encoding="utf-8"))
        replacement = self.package / "codex-agents/lane-l2.toml"
        replacement.write_text("model = 'replacement'\n", encoding="utf-8")
        self.agent.unlink()
        self.converge()
        self.assertFalse(installed.exists())
        self.assertTrue((self.target() / "lane-l2.toml").exists())

    def test_preserves_unrelated_and_rejects_modified_owned_agent(self):
        self.target().mkdir(parents=True)
        unrelated = self.target() / "personal.toml"
        unrelated.write_text("personal", encoding="utf-8")
        self.converge()
        installed = self.target() / "lane-l1.toml"
        installed.write_text("changed", encoding="utf-8")
        with self.assertRaises(CONVERGENCE.ConvergenceError):
            self.converge()
        self.assertEqual("personal", unrelated.read_text(encoding="utf-8"))
        self.assertEqual("changed", installed.read_text(encoding="utf-8"))

    def test_pending_journal_recovers_exact_copied_file(self):
        target = self.target()
        target.mkdir(parents=True)
        copied = target / "lane-l1.toml"
        copied.write_text(self.agent.read_text(encoding="utf-8"), encoding="utf-8")
        raw = CONVERGENCE._digest(self.agent)
        (target / CONVERGENCE.PENDING).write_text(json.dumps({"schema_version": 1, "owner": "base-agents", "files": [{"name": "lane-l1.toml", "sha256": raw}]}), encoding="utf-8")
        self.converge()
        self.assertFalse((target / CONVERGENCE.PENDING).exists())
        self.assertTrue((target / CONVERGENCE.MANIFEST).exists())

    def test_malformed_ownership_manifest_blocks_convergence(self):
        target = self.target()
        target.mkdir(parents=True)
        (target / CONVERGENCE.MANIFEST).write_text("{}", encoding="utf-8")
        with self.assertRaises(CONVERGENCE.ConvergenceError):
            self.converge()
        self.assertFalse((target / "lane-l1.toml").exists())

    def test_known_project_copy_is_removed_and_unknown_copy_survives(self):
        project_agents = self.root / "project/.codex/agents"
        project_agents.mkdir(parents=True)
        known = project_agents / "lane-l1.toml"
        known.write_text("legacy\r\n", encoding="utf-8")
        self.delivery({"lane-l1.toml": [digest(known)]})
        personal = project_agents / "workflow-lane.toml"
        personal.write_text("personal", encoding="utf-8")
        self.converge()
        self.assertFalse(known.exists())
        self.assertTrue(personal.exists())

    def test_reparse_source_is_refused(self):
        with mock.patch.object(CONVERGENCE, "_reparse", return_value=True):
            with self.assertRaises(CONVERGENCE.ConvergenceError):
                self.converge()

    def test_tj_agents_engineering_identity_is_accepted(self):
        root = ROLLING.VerifiedRoot("engineering@tj-agents", self.package, "a" * 40, "https://github.com/tj-agents/core.git")
        CONVERGENCE.converge(self.environ, self.root / "project", [root])
        self.assertTrue((self.target() / "lane-l1.toml").is_file())

    def test_same_generation_aliases_deduplicate_deterministically(self):
        roots = [
            ROLLING.VerifiedRoot("engineering@tj-agents", self.package, "a" * 40, "https://github.com/tj-agents/core.git"),
            ROLLING.VerifiedRoot("engineering@base-agents", self.package, "a" * 40, "https://github.com/tj-agents/core.git"),
        ]
        CONVERGENCE.converge(self.environ, self.root / "project", roots)
        self.assertTrue((self.target() / "lane-l1.toml").is_file())

    def test_different_generation_aliases_are_rejected(self):
        roots = [
            ROLLING.VerifiedRoot("engineering@tj-agents", self.package, "a" * 40, "https://github.com/tj-agents/core.git"),
            ROLLING.VerifiedRoot("engineering@base-agents", self.package, "b" * 40, "https://github.com/tj-agents/core.git"),
        ]
        with self.assertRaises(CONVERGENCE.ConvergenceError):
            CONVERGENCE.converge(self.environ, self.root / "project", roots)

if __name__ == "__main__":
    unittest.main()
