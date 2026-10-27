"""Package harness declarations stay consistent with the plugin roster and hook wiring."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("harness_sync", ROOT / "scripts/sync_harness_manifests.py")
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)

PERMISSIONS_SCRIPTS = ROOT / ".agents/dependencies/agent/.agents/agent/utility/plugins/scripts"
RUNTIME_SCRIPTS = ROOT / ".agents/dependencies/agent/.agents/agent/runtime"
sys.path.insert(0, str(PERMISSIONS_SCRIPTS))
sys.path.insert(0, str(RUNTIME_SCRIPTS))
import harness_permissions  # noqa: E402
import plugin_autoupdate  # noqa: E402

INSTRUCTED_SCRIPTS = (("engineering", "cleanup_proof.py"), ("workflow", "status.py"))
HOST_ENTRY_SKILLS = {"engineering": "merge", "workflow": "status"}


def validate_harness_schema(documents):
    schema = str(ROOT / ".agents/plugins/harness.schema.json").replace("'", "''")
    script = f"""
$documents = [Console]::In.ReadToEnd() | ConvertFrom-Json -AsHashtable -Depth 100
foreach ($document in $documents) {{
    $valid = $document | ConvertTo-Json -Depth 100 -Compress |
        Test-Json -SchemaFile '{schema}' -ErrorAction SilentlyContinue
    [Console]::Out.WriteLine($valid.ToString().ToLowerInvariant())
}}
"""
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", script],
        input=json.dumps(documents),
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return [line == "true" for line in result.stdout.splitlines()]


class HarnessManifestTests(unittest.TestCase):
    def test_core_manifests_are_current_and_roster_is_core_only(self):
        manifests = HARNESS.synchronize(ROOT, check=True)
        self.assertEqual({"base", "engineering", "workflow"}, set(manifests))
        roster = HARNESS.load(ROOT / ".agents/plugins/plugins.json")
        self.assertEqual({"tj-agents/core"}, {package["owner_repository"] for package in roster["packages"]})
        for package in roster["packages"]:
            self.assertEqual(manifests[package["name"]]["requires"], package["harness"])

    def test_additional_roots_require_canonical_owned_shipped_resources(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            shutil.copytree(ROOT / ".agents", root / ".agents")
            path = root / ".agents/plugins/harness/workflow.json"
            original = json.loads(path.read_text(encoding="utf-8"))
            HARNESS.synchronize(root, check=True)
            for roots in (
                [".agents/plugins/plugins.schema.json"],
                [".agents/workflow", ".agents/plugins/plugins.schema.json"],
                [".agents/workflow", ".agents/workflow"],
                [".agents/lanes", ".agents/workflow", ".agents/workflows"],
                [".agents/plugins/missing.json", ".agents/workflow"],
                [".agents/plugins/../plugins/plugins.schema.json", ".agents/workflow"],
                ["../outside", ".agents/workflow"],
            ):
                with self.subTest(roots=roots):
                    manifest = {**original, "source_roots": roots}
                    path.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        HARNESS.synchronize(root, check=True)

    def test_manifest_shape_carries_no_digest_fields(self):
        manifest = json.loads(
            (ROOT / ".agents/plugins/harness/base.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {"schema_version", "plugin", "source_roots", "requires"}, set(manifest)
        )

    def test_engineering_workflow_payload_ships_the_guarded_auto_merge_wrapper(self):
        sources = HARNESS.load(ROOT / ".agents/plugins/sources.json")["resources"]
        self.assertIn(
            {"plugin": "engineering", "source": ".agents/workflows", "destination": "workflows"},
            sources,
        )
        self.assertTrue((ROOT / "plugins/engineering/workflows/auto_merge.py").is_file())

    def test_declared_hook_hosts_must_match_host_wiring(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / ".agents/plugins/manifests/claude/base-hooks.json"
            source.parent.mkdir(parents=True)
            source.write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [{
                "command": 'python "${CLAUDE_PLUGIN_ROOT}/hooks/start.py"',
            }]}]}}), encoding="utf-8")
            config = {"host_hook_sources": {"base": {"claude": ".agents/plugins/manifests/claude/base-hooks.json"}}}
            self.assertEqual(
                [{"path": "hooks/start.py", "hosts": ["claude"]}],
                HARNESS.expected_hooks(root, config, "base"),
            )

    def test_foreign_marketplace_owner_is_rejected(self):
        roster = HARNESS.load(ROOT / ".agents/plugins/plugins.json")
        config = HARNESS.load(ROOT / ".agents/plugins/sources.json")
        requires = json.loads((ROOT / ".agents/plugins/harness/base.json").read_text(encoding="utf-8"))["requires"]
        requires["marketplaces"][0]["repository"] = "another-org/core"
        with self.assertRaisesRegex(ValueError, "disagrees with plugin roster"):
            HARNESS.validate_requires(ROOT, config, roster, "base", requires)
        requires["marketplaces"][0]["repository"] = "tj-agents/core"
        with self.assertRaisesRegex(ValueError, "disagrees with plugin roster"):
            HARNESS.validate_requires(ROOT, config, roster, "base", requires)

    def test_core_marketplace_identity_matches_plugin_selection(self):
        config = HARNESS.load(ROOT / ".agents/plugins/sources.json")
        self.assertEqual(plugin_autoupdate.MARKETPLACE_NAME, HARNESS.PACKAGES.core_marketplace(ROOT, config))
        self.assertEqual(plugin_autoupdate.MARKETPLACE_REPOSITORY, HARNESS.DISTRIBUTION_REPOSITORY)
        for path in (ROOT / ".agents/plugins/harness").glob("*.json"):
            with self.subTest(path=path.name):
                manifest = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(f"{plugin_autoupdate.MARKETPLACE_NAME}/{path.stem}", manifest["plugin"])
                self.assertEqual([{"id": plugin_autoupdate.MARKETPLACE_NAME, "repository": plugin_autoupdate.MARKETPLACE_REPOSITORY}],
                                 manifest["requires"]["marketplaces"])


class HarnessPermissionValidationTests(unittest.TestCase):
    def requires(self, command):
        return {
            "marketplaces": [],
            "plugins": [],
            "hooks": [],
            "permissions": {"claude_allow": [command], "codex_prefix_rules": []},
        }

    def test_terminal_matchers_allow_only_literal_command_prefixes(self):
        for command in (
            "Bash(python -B ${PLUGIN_ROOT}/script.py:*)",
            "Bash(python -B ${PLUGIN_ROOT}/script.py --clear:*)",
            "Bash(python -B ${PLUGIN_ROOT}/script.py --clear *)",
        ):
            with self.subTest(command=command):
                harness_permissions.validate_requires(self.requires(command), "test")

    def test_optional_setup_declaration_is_strictly_validated(self):
        requires = self.requires("Bash(python -B ${PLUGIN_ROOT}/script.py:*)")
        requires["setup"] = {"script": ".agents/personal/utility/bot-identity/scripts/bot_identity.py"}
        harness_permissions.validate_requires(requires, "test")
        for setup in ({}, {"script": "../setup.py"}, {"script": "setup.ps1"}, {"script": "setup.py", "extra": True}):
            with self.subTest(setup=setup):
                invalid = self.requires("Bash(python -B ${PLUGIN_ROOT}/script.py:*)")
                invalid["setup"] = setup
                with self.assertRaises(harness_permissions.lock_io.LockError):
                    harness_permissions.validate_requires(invalid, "test")

    def test_exact_script_rules_preserve_fixed_arguments(self):
        for command in (
            "Bash(python -B ${PLUGIN_ROOT}/script.py --clear)",
            'Bash(python -B "${PLUGIN_ROOT}/policy runner.py" --name café)',
        ):
            with self.subTest(command=command):
                harness_permissions.validate_requires(self.requires(command), "test")

    def test_wildcard_arguments_require_a_terminal_matcher_after_a_literal_prefix(self):
        for command in (
            "Bash(python -B ${PLUGIN_ROOT}/script.py --clear*)",
            "Bash(python -B ${PLUGIN_ROOT}/script.py --clear:* more)",
            "Bash(python* -B ${PLUGIN_ROOT}/script.py --clear:*)",
            "Bash(python -B ${PLUGIN_ROOT}/hooks/*.py --clear:*)",
            "Bash(python -B ${PLUGIN_ROOT}/script.py * --clear:*)",
        ):
            with self.subTest(command=command), self.assertRaisesRegex(harness_permissions.lock_io.LockError, "script arguments require :\\*"):
                harness_permissions.validate_requires(self.requires(command), "test")


@unittest.skipUnless(shutil.which("pwsh"), "PowerShell 7 is required for Test-Json")
class HarnessManifestSchemaTests(unittest.TestCase):
    def rule(self):
        manifest = json.loads(
            (ROOT / ".agents/plugins/harness/engineering.json").read_text(encoding="utf-8")
        )
        return manifest, manifest["requires"]["permissions"]["codex_prefix_rules"][0]

    def test_shipped_manifests_validate_against_schema(self):
        manifests = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((ROOT / ".agents/plugins/harness").glob("*.json"))
        ]
        self.assertEqual([True] * len(manifests), validate_harness_schema(manifests))

    def test_codex_prefix_rule_accepts_legacy_string_tokens(self):
        manifest, rule = self.rule()
        rule["pattern"] = ["python", "-B", "script.py"]
        rule["match"] = ["python"]
        rule["not_match"] = ["pwsh"]
        self.assertEqual([True], validate_harness_schema([manifest]))

    def test_codex_prefix_rule_rejects_invalid_tokens_and_unknown_fields(self):
        manifest, rule = self.rule()
        invalid_rules = []
        for field, value in (
            ("pattern", []),
            ("pattern", [""]),
            ("pattern", [123]),
            ("pattern", [[]]),
            ("pattern", [["python", ["-B"]]]),
            ("match", [[]]),
            ("match", [[["python"]]]),
            ("not_match", [123]),
            ("not_match", [["python", ""]]),
        ):
            invalid = deepcopy(manifest)
            invalid["requires"]["permissions"]["codex_prefix_rules"][0][field] = value
            invalid_rules.append(invalid)
        invalid = deepcopy(manifest)
        invalid["requires"]["permissions"]["codex_prefix_rules"][0]["unexpected"] = True
        invalid_rules.append(invalid)
        self.assertEqual([False] * len(invalid_rules), validate_harness_schema(invalid_rules))


class HarnessPermissionCoverageTests(unittest.TestCase):
    PLUGIN_ROOT = r"C:\scratch\tj-agents-root"

    def rendered(self, plugin):
        manifest = json.loads((ROOT / f".agents/plugins/harness/{plugin}.json").read_text(encoding="utf-8"))
        return harness_permissions.render_permissions(manifest["requires"]["permissions"], self.PLUGIN_ROOT)

    def test_every_instructed_command_is_declared_for_both_hosts(self):
        for plugin, script in INSTRUCTED_SCRIPTS:
            with self.subTest(plugin=plugin, script=script):
                claude_allow, codex_rules = self.rendered(plugin)
                matching = [entry for entry in claude_allow if script in entry]
                self.assertTrue(
                    any(entry.startswith("Bash(") for entry in matching),
                    f"{plugin}: missing a Bash( entry for {script}",
                )
                self.assertTrue(
                    any(entry.startswith("PowerShell(") for entry in matching),
                    f"{plugin}: missing a PowerShell( entry for {script}",
                )
                matching_rules = [rule for rule in codex_rules if script in json.dumps(rule)]
                self.assertEqual(1, len(matching_rules), f"{plugin}: expected exactly one Codex rule for {script}")

    def test_host_entry_and_vendored_script_paths_are_both_declared(self):
        for plugin, script in INSTRUCTED_SCRIPTS:
            skill = HOST_ENTRY_SKILLS[plugin]
            with self.subTest(plugin=plugin, script=script):
                claude_allow, codex_rules = self.rendered(plugin)
                matching = [entry.replace("\\", "/") for entry in claude_allow if script in entry]
                self.assertTrue(
                    any("/.agents/" in entry for entry in matching),
                    f"{plugin}: missing the vendored .agents/ path for {script}",
                )
                self.assertTrue(
                    any(f"/skills/{skill}/scripts/{script}" in entry for entry in matching),
                    f"{plugin}: missing the host-entry skills/ path for {script}",
                )
                rules_text = json.dumps(
                    [rule for rule in codex_rules if script in json.dumps(rule)]
                ).replace("\\\\", "/")
                self.assertIn(".agents/", rules_text, f"{plugin}: missing the vendored .agents/ Codex path")
                self.assertIn(
                    f"codex-skills/{skill}/scripts/{script}", rules_text,
                    f"{plugin}: missing the host-entry codex-skills/ Codex path",
                )

    def test_rendered_codex_rules_load_under_execpolicy_when_available(self):
        codex = shutil.which("codex")
        if not codex:
            self.skipTest("codex CLI not on PATH")
        rules = []
        checks = []
        for plugin in dict.fromkeys(plugin for plugin, _ in INSTRUCTED_SCRIPTS):
            _, codex_rules = self.rendered(plugin)
            rules += codex_rules
            checks.extend((plugin, tokens, True) for rule in codex_rules for tokens in rule["match"])
            checks.extend((plugin, tokens, False) for rule in codex_rules for tokens in rule["not_match"])
        with tempfile.TemporaryDirectory() as raw:
            rules_path = Path(raw) / "tj-agents.rules"
            rules_path.write_text("\n".join(harness_permissions.codex_rule_lines(rules)), encoding="utf-8")
            for plugin, tokens, allowed in checks:
                with self.subTest(plugin=plugin):
                    result = subprocess.run(
                        [codex, "execpolicy", "check", "--rules", str(rules_path),
                         "--resolve-host-executables", "--", *tokens],
                        capture_output=True, text=True,
                    )
                    self.assertEqual(0, result.returncode, result.stderr)
                    decision = result.stdout.replace(" ", "")
                    if allowed:
                        self.assertIn('"decision":"allow"', decision)
                    else:
                        self.assertNotIn('"decision":"allow"', decision)


if __name__ == "__main__":
    unittest.main()
