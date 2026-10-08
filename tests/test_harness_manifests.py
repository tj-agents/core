"""Package harness declarations stay consistent with the catalog and hook wiring."""

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

PERMISSIONS_SCRIPTS = ROOT / ".agents/machine/utility/bootstrap-capabilities/scripts"
sys.path.insert(0, str(PERMISSIONS_SCRIPTS))
import harness_permissions  # noqa: E402

INSTRUCTED_SCRIPTS = (("engineering", "cleanup_proof.py"), ("machine", "finish.ps1"), ("machine", "close.ps1"))
HOST_ENTRY_SKILLS = {"engineering": "merge", "machine": "peer-cli"}
CONTINUATION_RUNTIME_OPERATIONS = ("init", "claim", "heartbeat", "yield", "checkpoint", "status", "wake")
CONTINUATION_ADAPTER_OPERATIONS = ("claim", "register", "remove", "list", "wake")


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
    def test_core_manifests_are_current_and_catalog_is_core_only(self):
        manifests = HARNESS.synchronize(ROOT, check=True)
        self.assertEqual({"base", "engineering", "machine"}, set(manifests))
        catalog = HARNESS.load(ROOT / ".agents/catalog/catalog.json")
        self.assertEqual({"tj-agents/core"}, {release["owner_repository"] for release in catalog["releases"]})
        for release in catalog["releases"]:
            for plugin in release["plugins"]:
                self.assertEqual(manifests[plugin["name"]]["requires"], plugin["harness"])

    def test_additional_roots_require_canonical_owned_shipped_resources(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            shutil.copytree(ROOT / ".agents", root / ".agents")
            path = root / ".agents/plugins/harness/machine.json"
            original = json.loads(path.read_text(encoding="utf-8"))
            HARNESS.synchronize(root, check=True)
            for roots in (
                [".agents/catalog/catalog.schema.json"],
                [".agents/machine", ".agents/catalog/catalog.schema.json"],
                [".agents/machine", ".agents/machine"],
                [".agents/lanes", ".agents/machine", ".agents/workflows"],
                [".agents/catalog/missing.json", ".agents/machine"],
                [".agents/catalog/../catalog/catalog.schema.json", ".agents/machine"],
                ["../outside", ".agents/machine"],
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

    def test_wildcard_script_paths_in_claude_permissions_are_rejected(self):
        catalog = HARNESS.load(ROOT / ".agents/catalog/catalog.json")
        config = HARNESS.load(ROOT / ".agents/plugins/sources.json")
        original = json.loads((ROOT / ".agents/plugins/harness/machine.json").read_text(encoding="utf-8"))["requires"]
        for command in (
            r"PowerShell(& *\handoff-codex\scripts\launch-codex.ps1 *)",
            r"PowerShell(& *\.claude\plugins\cache\base-agents\machine\*\handoff-codex\scripts\launch-codex.ps1 *)",
        ):
            with self.subTest(command=command):
                requires = json.loads(json.dumps(original))
                requires["permissions"]["claude_allow"] = [command]
                with self.assertRaisesRegex(ValueError, "wildcard script path"):
                    HARNESS.validate_requires(ROOT, config, catalog, "machine", requires)

    def test_foreign_marketplace_owner_is_rejected(self):
        catalog = HARNESS.load(ROOT / ".agents/catalog/catalog.json")
        config = HARNESS.load(ROOT / ".agents/plugins/sources.json")
        requires = json.loads((ROOT / ".agents/plugins/harness/base.json").read_text(encoding="utf-8"))["requires"]
        requires["marketplaces"][0]["repository"] = "another-org/core"
        with self.assertRaisesRegex(ValueError, "disagrees with catalog"):
            HARNESS.validate_requires(ROOT, config, catalog, "base", requires)


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
    PLUGIN_ROOT = r"C:\scratch\base-agents-root"

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

    def test_close_permissions_are_exact_argument_free_commands(self):
        claude_allow, codex_rules = self.rendered("machine")
        entries = [entry for entry in claude_allow if "close.ps1" in entry]
        self.assertEqual(8, len(entries))
        for entry in entries:
            self.assertTrue(entry.replace("\\", "/").endswith("/close.ps1)"), entry)
            self.assertNotIn("*", entry)
        rules = [rule for rule in codex_rules if "close.ps1" in json.dumps(rule)]
        self.assertEqual(1, len(rules))
        self.assertEqual(6, len(rules[0]["pattern"]))
        root = self.PLUGIN_ROOT.replace("\\", "/")
        paths = {path.replace("\\", "/") for path in rules[0]["pattern"][-1]}
        self.assertEqual({
            f"{root}/.agents/machine/utility/peer-cli/scripts/close.ps1",
            f"{root}/skills/peer-cli/scripts/close.ps1",
            f"{root}/codex-skills/peer-cli/scripts/close.ps1",
        }, paths)

    def test_continuation_runtime_and_adapter_permissions_cover_each_host_operation(self):
        claude_allow, codex_rules = self.rendered("engineering")
        root = self.PLUGIN_ROOT.replace("\\", "/")
        runtime = f"{root}/workflows/continuation_runtime.py"
        adapter_source = f"{root}/.agents/engineering/workflow/persistent-workflow/scripts/delivery-continuation.ps1"
        adapter_skill = f"{root}/skills/persistent-workflow/scripts/delivery-continuation.ps1"
        adapter_codex = f"{root}/codex-skills/persistent-workflow/scripts/delivery-continuation.ps1"
        normalized_allow = [entry.replace("\\", "/") for entry in claude_allow]
        for operation in CONTINUATION_RUNTIME_OPERATIONS:
            with self.subTest(host="claude", script="runtime", operation=operation):
                self.assertIn(f"Bash(python -B {runtime} {operation})", normalized_allow)
                self.assertIn(f"PowerShell(python -B {runtime} {operation})", normalized_allow)
        for operation in CONTINUATION_ADAPTER_OPERATIONS:
            with self.subTest(host="claude", script="adapter", operation=operation):
                self.assertIn(
                    f"Bash(powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File {adapter_source} {operation})",
                    normalized_allow,
                )
                self.assertIn(
                    f"PowerShell(powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File {adapter_source} {operation})",
                    normalized_allow,
                )
                self.assertIn(
                    f"Bash(powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File {adapter_skill} {operation})",
                    normalized_allow,
                )
                self.assertIn(
                    f"PowerShell(powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File {adapter_skill} {operation})",
                    normalized_allow,
                )
        runtime_rules = [rule for rule in codex_rules if runtime in json.dumps(rule).replace("\\\\", "/")]
        self.assertEqual(1, len(runtime_rules))
        self.assertEqual(list(CONTINUATION_RUNTIME_OPERATIONS), runtime_rules[0]["pattern"][-1])
        runtime = runtime.replace("/", chr(92))
        self.assertEqual(
            [
                ["python", "-B", runtime.replace("/", "\\\\"), "_child"],
                ["python", "-B", runtime.replace("/", "\\\\"), "unknown"],
            ],
            runtime_rules[0]["not_match"],
        )
        adapter_rules = [rule for rule in codex_rules if adapter_codex in json.dumps(rule).replace("\\\\", "/")]
        self.assertEqual(1, len(adapter_rules))
        self.assertEqual(list(CONTINUATION_ADAPTER_OPERATIONS), adapter_rules[0]["pattern"][-1])
        self.assertEqual(
            {adapter_source, adapter_skill, adapter_codex},
            {path.replace(chr(92), "/") for path in adapter_rules[0]["pattern"][-2]},
        )
        adapter_codex = adapter_codex.replace("/", chr(92))
        self.assertEqual(
            [["powershell.exe", "-NoProfile", "-File", adapter_codex.replace("/", "\\\\"), "unexpected"]],
            adapter_rules[0]["not_match"],
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
            checks.extend((plugin, rule["match"][0]) for rule in codex_rules)
        with tempfile.TemporaryDirectory() as raw:
            rules_path = Path(raw) / "base-agents.rules"
            rules_path.write_text("\n".join(harness_permissions.codex_rule_lines(rules)), encoding="utf-8")
            for plugin, tokens in checks:
                with self.subTest(plugin=plugin):
                    result = subprocess.run(
                        [codex, "execpolicy", "check", "--rules", str(rules_path),
                         "--resolve-host-executables", "--", *tokens],
                        capture_output=True, text=True,
                    )
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertIn('"decision":"allow"', result.stdout.replace(" ", ""))


if __name__ == "__main__":
    unittest.main()
