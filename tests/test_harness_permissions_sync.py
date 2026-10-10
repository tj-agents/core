"""Converge every installed base-agents package's declared harness permissions on this machine."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/machine/utility/bootstrap-capabilities/scripts/harness_permissions_sync.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("harness_permissions_sync", SCRIPT)
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)
import harness_permissions


CLEANUP = "Bash(python -B ${PLUGIN_ROOT}/cleanup_proof.py)"


def cleanup_entries(root):
    """CLEANUP rendered for one plugin root in both separator spellings, built without the renderer."""
    forward, backslash = str(root).replace("\\", "/"), str(root).replace("/", "\\")
    return sorted([f"Bash(python -B {forward}/cleanup_proof.py)", f"Bash(python -B {backslash}\\cleanup_proof.py)"])


SAMPLE_RULE = {
    "pattern": [["python", "python3", "py"], "-B", "${PLUGIN_ROOT}/sample/finish.py"],
    "justification": "test rule",
    "match": [["python", "-B", "${PLUGIN_ROOT}/sample/finish.py"]],
    "not_match": [["python", "${PLUGIN_ROOT}/sample/finish.py"]],
}


def write_harness(root, name, claude_allow, codex_rules=None):
    root.mkdir(parents=True, exist_ok=True)
    harness = {
        "schema_version": 1,
        "plugin": f"base-agents/{name}",
        "source_roots": [],
        "requires": {
            "marketplaces": [],
            "plugins": [],
            "hooks": [],
            "permissions": {"claude_allow": claude_allow, "codex_prefix_rules": codex_rules or []},
        },
    }
    (root / "harness.json").write_text(json.dumps(harness), encoding="utf-8")


def install_claude_plugin(
    claude_config, name, version, claude_allow, codex_rules=None, scope="user", project_path=None,
    marketplace="base-agents", repository="tj-agents/core",
):
    root = claude_config / "plugins" / "cache" / marketplace / name / version
    write_harness(root, name, claude_allow, codex_rules)
    installed_path = claude_config / "plugins" / "installed_plugins.json"
    installed_path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(installed_path.read_text(encoding="utf-8")) if installed_path.is_file() else {"version": 2, "plugins": {}}
    known_path = claude_config / "plugins" / "known_marketplaces.json"
    known = json.loads(known_path.read_text(encoding="utf-8")) if known_path.is_file() else {}
    known[marketplace] = {"source": {"source": "github", "repo": repository}}
    known_path.write_text(json.dumps(known), encoding="utf-8")
    identity = f"{name}@{marketplace}"
    entry = {"scope": scope, "installPath": str(root), "version": version}
    if project_path is not None:
        entry["projectPath"] = str(project_path)
    data["plugins"].setdefault(identity, []).append(entry)
    installed_path.write_text(json.dumps(data), encoding="utf-8")
    return root


def clear_claude_plugin(claude_config, name, marketplace="base-agents"):
    installed_path = claude_config / "plugins" / "installed_plugins.json"
    data = json.loads(installed_path.read_text(encoding="utf-8"))
    data["plugins"][f"{name}@{marketplace}"] = []
    installed_path.write_text(json.dumps(data), encoding="utf-8")


def install_codex_plugin(
    codex_home, name, version, claude_allow=None, codex_rules=None, marketplace="base-agents",
    repository="tj-agents/core",
):
    root = codex_home / "plugins" / "cache" / marketplace / name / version
    write_harness(root, name, claude_allow or [], codex_rules)
    config_path = codex_home / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("a", encoding="utf-8") as config:
        config.write(
            f'\n[marketplaces.{marketplace}]\nsource_type = "git"\n'
            f'source = "https://github.com/{repository}.git"\n'
        )
    return root


class HarnessPermissionsSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.claude_config = self.root / "claude"
        self.codex_home = self.root / "codex"
        self.state = self.root / "state"
        self.environ = {
            "CLAUDE_CONFIG_DIR": str(self.claude_config),
            "CODEX_HOME": str(self.codex_home),
            "AGENT_STATE_DIRECTORY": str(self.state),
        }

    def settings_path(self):
        return self.claude_config / "settings.json"

    def rules_path(self):
        return self.codex_home / "rules" / "base-agents.rules"

    def write_settings(self, content):
        self.settings_path().parent.mkdir(parents=True, exist_ok=True)
        self.settings_path().write_text(json.dumps(content), encoding="utf-8")

    def test_user_entries_survive(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        self.write_settings({"permissions": {"allow": ["Bash(user-thing)"]}})

        drifted, warnings = SYNC.synchronize(self.environ, "apply")

        self.assertEqual([], warnings)
        allow = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertIn("Bash(user-thing)", allow)
        self.assertIn(str(self.settings_path()), drifted)

    def test_stale_owned_entries_are_removed(self):
        v1 = install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        SYNC.synchronize(self.environ, "apply")
        before = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertEqual(cleanup_entries(v1), sorted(before))

        clear_claude_plugin(self.claude_config, "engineering")
        SYNC.synchronize(self.environ, "apply")

        after = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertEqual([], after)

    def test_tj_agents_non_base_marketplace_permissions_apply_on_both_hosts(self):
        claude_root = install_claude_plugin(
            self.claude_config, "work", "v1", ["Bash(work-review)"], marketplace="work-agents",
            repository="tj-agents/work",
        )
        codex_root = install_codex_plugin(
            self.codex_home, "work", "v1", codex_rules=[SAMPLE_RULE], marketplace="work-agents",
            repository="tj-agents/work",
        )

        SYNC.synchronize(self.environ, "apply")

        allow = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertIn("Bash(work-review)", allow)
        forward, _ = harness_permissions.path_spellings(codex_root)
        self.assertIn(forward, self.rules_path().read_text(encoding="utf-8"))
        self.assertTrue(claude_root.is_dir())

    def test_foreign_marketplace_permissions_are_ignored_on_both_hosts(self):
        install_claude_plugin(
            self.claude_config, "foreign", "v1", ["Bash(foreign-review)"], marketplace="foreign-agents",
            repository="foreign-org/standards",
        )
        install_codex_plugin(
            self.codex_home, "foreign", "v1", codex_rules=[SAMPLE_RULE], marketplace="foreign-agents",
            repository="foreign-org/standards",
        )

        SYNC.synchronize(self.environ, "apply")

        self.assertFalse(self.settings_path().is_file())
        self.assertFalse(self.rules_path().is_file())

    def test_removed_non_base_marketplace_permissions_are_withdrawn_on_both_hosts(self):
        install_claude_plugin(
            self.claude_config, "work", "v1", ["Bash(work-review)"], marketplace="work-agents",
            repository="tj-agents/work",
        )
        install_codex_plugin(
            self.codex_home, "work", "v1", codex_rules=[SAMPLE_RULE], marketplace="work-agents",
            repository="tj-agents/work",
        )
        SYNC.synchronize(self.environ, "apply")

        clear_claude_plugin(self.claude_config, "work", marketplace="work-agents")
        config_path = self.codex_home / "config.toml"
        config_path.write_text("", encoding="utf-8")
        SYNC.synchronize(self.environ, "apply")

        allow = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertEqual([], allow)
        self.assertFalse(self.rules_path().is_file())

    def test_a_version_path_change_rerenders(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        SYNC.synchronize(self.environ, "apply")

        clear_claude_plugin(self.claude_config, "engineering")
        v2 = install_claude_plugin(self.claude_config, "engineering", "v2", [CLEANUP])
        SYNC.synchronize(self.environ, "apply")

        # Exact equality also proves every v1 entry is gone; a "v1" substring check matched random
        # temporary directory names.
        allow = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertEqual(cleanup_entries(v2), sorted(allow))

    def test_idempotent_second_apply_is_byte_identical(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        install_codex_plugin(self.codex_home, "machine", "2.0.0", codex_rules=[SAMPLE_RULE])

        SYNC.synchronize(self.environ, "apply")
        settings_first = self.settings_path().read_bytes()
        rules_first = self.rules_path().read_bytes()

        drifted, warnings = SYNC.synchronize(self.environ, "apply")

        self.assertEqual([], warnings)
        self.assertEqual(settings_first, self.settings_path().read_bytes())
        self.assertEqual(rules_first, self.rules_path().read_bytes())

    def test_settings_with_foreign_formatting_are_untouched_when_allow_already_matches(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        SYNC.synchronize(self.environ, "apply")
        data = json.loads(self.settings_path().read_text(encoding="utf-8"))
        data["theme"] = "dark"
        foreign = json.dumps(data, indent=4).replace("\n", "\r\n") + "\r\n"
        self.settings_path().write_bytes(foreign.encode("utf-8"))

        drifted, _ = SYNC.synchronize(self.environ, "apply")

        self.assertEqual([], [path for path in drifted if path.endswith("settings.json")])
        self.assertEqual(foreign.encode("utf-8"), self.settings_path().read_bytes())

    def test_malformed_settings_warn_and_do_not_write(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        self.settings_path().parent.mkdir(parents=True, exist_ok=True)
        self.settings_path().write_text("{not json", encoding="utf-8")

        drifted, warnings = SYNC.synchronize(self.environ, "apply")

        self.assertNotIn(str(self.settings_path()), drifted)
        self.assertTrue(any("cannot parse settings" in warning for warning in warnings))
        self.assertEqual("{not json", self.settings_path().read_text(encoding="utf-8"))

    def test_unreadable_installed_plugins_json_warns_and_leaves_claude_target_untouched(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        SYNC.synchronize(self.environ, "apply")
        before = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertTrue(before)

        installed_path = self.claude_config / "plugins" / "installed_plugins.json"
        installed_path.write_text("{not json", encoding="utf-8")

        drifted, warnings = SYNC.synchronize(self.environ, "apply")

        self.assertNotIn(str(self.settings_path()), drifted)
        self.assertTrue(any("installed_plugins.json" in warning for warning in warnings), warnings)
        after = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertEqual(before, after)

    def test_malformed_shape_installed_plugins_json_warns_and_leaves_claude_target_untouched(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        SYNC.synchronize(self.environ, "apply")
        before = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertTrue(before)

        installed_path = self.claude_config / "plugins" / "installed_plugins.json"
        installed_path.write_text(json.dumps({"version": 2, "plugins": "not-a-dict"}), encoding="utf-8")

        drifted, warnings = SYNC.synchronize(self.environ, "apply")

        self.assertNotIn(str(self.settings_path()), drifted)
        self.assertTrue(any("installed_plugins.json" in warning for warning in warnings), warnings)
        after = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertEqual(before, after)

    def test_genuinely_absent_installed_plugins_json_means_zero_roots_without_warning(self):
        drifted, warnings = SYNC.synchronize(self.environ, "apply")

        self.assertEqual([], warnings)
        self.assertFalse(self.settings_path().is_file())

    def test_unlistable_codex_cache_directory_warns_and_leaves_codex_rules_untouched(self):
        install_codex_plugin(self.codex_home, "machine", "2.0.0", codex_rules=[SAMPLE_RULE])
        SYNC.synchronize(self.environ, "apply")
        before = self.rules_path().read_bytes()

        cache_base = self.codex_home / "plugins" / "cache"
        original_iterdir = Path.iterdir

        def fake_iterdir(self_path):
            if self_path == cache_base:
                raise OSError("permission denied")
            return original_iterdir(self_path)

        with mock.patch.object(Path, "iterdir", fake_iterdir):
            drifted, warnings = SYNC.synchronize(self.environ, "apply")

        self.assertNotIn(str(self.rules_path()), drifted)
        self.assertTrue(any("Codex plugin cache" in warning for warning in warnings), warnings)
        self.assertEqual(before, self.rules_path().read_bytes())

    def test_check_exit_codes(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])

        drifted, warnings = SYNC.synchronize(self.environ, "check")
        self.assertTrue(drifted)
        self.assertEqual([], warnings)

        SYNC.synchronize(self.environ, "apply")
        drifted, warnings = SYNC.synchronize(self.environ, "check")
        self.assertEqual([], drifted)

    def test_opt_out_disables_both_modes(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        self.environ["BASE_AGENTS_HARNESS_PERMISSIONS"] = "off"

        drifted, warnings = SYNC.synchronize(self.environ, "apply")

        self.assertEqual([], drifted)
        self.assertEqual([], warnings)
        self.assertFalse(self.settings_path().is_file())

    def test_both_separator_spellings_are_rendered(self):
        root = install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])
        SYNC.synchronize(self.environ, "apply")

        allow = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        forward, backslash = harness_permissions.path_spellings(root)
        self.assertIn(f"Bash(python -B {forward}/cleanup_proof.py)", allow)
        self.assertIn(f"Bash(python -B {backslash}\\cleanup_proof.py)", allow)

    def test_multiple_scopes_all_survive(self):
        install_claude_plugin(self.claude_config, "engineering", "user-root", [CLEANUP], scope="user")
        install_claude_plugin(
            self.claude_config, "engineering", "local-root", [CLEANUP],
            scope="local", project_path=self.root / "some-project",
        )

        SYNC.synchronize(self.environ, "apply")

        allow = json.loads(self.settings_path().read_text(encoding="utf-8"))["permissions"]["allow"]
        self.assertTrue(any("user-root" in entry for entry in allow))
        self.assertTrue(any("local-root" in entry for entry in allow))

    def test_print_mode_resolves_an_exact_invocation(self):
        install_claude_plugin(self.claude_config, "engineering", "v1", [CLEANUP])

        lines, warnings = SYNC.print_invocations(self.environ, "cleanup_proof.py")

        self.assertEqual([], warnings)
        self.assertEqual(1, len(lines))
        self.assertIn("cleanup_proof.py", lines[0])
        self.assertNotIn("${PLUGIN_ROOT}", lines[0])

    def test_codex_rules_file_loads_under_execpolicy_when_available(self):
        codex = shutil.which("codex")
        if not codex:
            self.skipTest("codex CLI not on PATH")
        root = install_codex_plugin(self.codex_home, "engineering", "2.1.16", codex_rules=[SAMPLE_RULE])

        SYNC.synchronize(self.environ, "apply")

        rules_path = self.rules_path()
        self.assertTrue(rules_path.is_file())
        _, backslash = harness_permissions.path_spellings(root)
        result = subprocess.run(
            [codex, "execpolicy", "check", "--rules", str(rules_path), "--resolve-host-executables",
             "--", "python", "-B", f"{backslash}\\sample\\finish.py"],
            capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('"decision":"allow"', result.stdout.replace(" ", ""))


if __name__ == "__main__":
    unittest.main()
