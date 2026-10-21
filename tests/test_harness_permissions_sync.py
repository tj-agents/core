from collections import namedtuple
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/machine/utility/plugin-selection/scripts/harness_permissions_sync.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("harness_permissions_sync", SCRIPT)
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)
VerifiedRoot = namedtuple("VerifiedRoot", "identity root revision repository")


def harness(root: Path, permissions: dict) -> None:
    root.mkdir(parents=True)
    value = {"schema_version": 1, "plugin": "tj-agents/test", "source_roots": [], "requires": {"marketplaces": [], "plugins": [], "hooks": [], "permissions": permissions}}
    (root / "harness.json").write_text(json.dumps(value), encoding="utf-8")


class HarnessPermissionsSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.environ = {"CLAUDE_CONFIG_DIR": str(self.root / "claude"), "CODEX_HOME": str(self.root / "codex"), "AGENT_STATE_DIRECTORY": str(self.root / "state")}

    def verified(self, identity: str, root: Path, repository="https://github.com/tj-agents/core.git"):
        return VerifiedRoot(identity, root, "a" * 40, repository)

    def test_removes_stale_owned_claude_grants_and_preserves_user_grants(self):
        root = self.root / "engineering"
        harness(root, {"claude_allow": ["Bash(shipped)"], "codex_prefix_rules": []})
        settings = Path(self.environ["CLAUDE_CONFIG_DIR"]) / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({"permissions": {"allow": ["Bash(personal)"]}}), encoding="utf-8")
        SYNC.apply_verified(self.environ, "claude", self.root, [self.verified("engineering@base-agents", root)])
        SYNC.apply_verified(self.environ, "claude", self.root, [])
        self.assertEqual(["Bash(personal)"], json.loads(settings.read_text(encoding="utf-8"))["permissions"]["allow"])

    def test_external_root_without_a_harness_is_ignored(self):
        root = self.root / "dotnet"
        root.mkdir()
        SYNC.apply_verified(self.environ, "claude", self.root, [self.verified("dotnet@tj-agents", root, "https://github.com/tj-agents/dotnet.git")])
        self.assertTrue((Path(self.environ["CLAUDE_CONFIG_DIR"]) / "settings.json").is_file())

    def test_authenticated_concertable_root_converges_its_declared_permissions(self):
        root = self.root / "project-policy"
        harness(root, {"claude_allow": ["Bash(project-task)"], "codex_prefix_rules": []})
        SYNC.apply_verified(self.environ, "claude", self.root, [
            self.verified("concertable@agents", root, "https://github.com/concertable/agents.git"),
        ])
        settings = Path(self.environ["CLAUDE_CONFIG_DIR"]) / "settings.json"
        self.assertEqual(["Bash(project-task)"], json.loads(settings.read_text(encoding="utf-8"))["permissions"]["allow"])

    def test_opt_out_and_legacy_scanner_fail_when_permissions_are_required(self):
        root = self.root / "engineering"
        harness(root, {"claude_allow": ["Bash(shipped)"], "codex_prefix_rules": []})
        with self.assertRaises(SYNC.PermissionSyncError):
            SYNC.apply_verified(dict(self.environ, BASE_AGENTS_HARNESS_PERMISSIONS="off"), "claude", self.root, [self.verified("engineering@base-agents", root)])
        with self.assertRaises(SYNC.PermissionSyncError):
            SYNC.synchronize(self.environ, "apply", self.root)
        self.assertEqual(2, SYNC.main(["--apply", "--project", str(self.root)]))

    def test_codex_rules_require_generated_or_sidecar_ownership(self):
        root = self.root / "engineering"
        rule = {"pattern": [["python"], "-B", "${PLUGIN_ROOT}/run.py"], "justification": "test", "match": [["python", "-B", "${PLUGIN_ROOT}/run.py"]], "not_match": [["python", "${PLUGIN_ROOT}/run.py"]]}
        harness(root, {"claude_allow": [], "codex_prefix_rules": [rule]})
        path = Path(self.environ["CODEX_HOME"]) / "rules" / "base-agents.rules"
        path.parent.mkdir(parents=True)
        path.write_text("personal", encoding="utf-8")
        with self.assertRaises(SYNC.PermissionSyncError):
            SYNC.apply_verified(self.environ, "codex", self.root, [self.verified("engineering@base-agents", root)])

    def test_claude_sidecar_failure_rolls_back(self):
        root = self.root / "engineering"
        harness(root, {"claude_allow": ["Bash(shipped)"], "codex_prefix_rules": []})
        settings = Path(self.environ["CLAUDE_CONFIG_DIR"]) / "settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({"permissions": {"allow": ["Bash(personal)"]}}), encoding="utf-8")
        original = settings.read_text(encoding="utf-8")
        actual = SYNC.write_text_atomic
        calls = []

        def fail_second(path, text):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("state write failed")
            return actual(path, text)

        with mock.patch.object(SYNC, "write_text_atomic", side_effect=fail_second):
            with self.assertRaises(SYNC.PermissionSyncError):
                SYNC.apply_verified(self.environ, "claude", self.root, [self.verified("engineering@base-agents", root)])
        self.assertEqual(original, settings.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
