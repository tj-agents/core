import argparse
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/machine/bootstrap-capabilities/scripts/bootstrap_capabilities.py"
SPEC = importlib.util.spec_from_file_location("configuration_audit", SCRIPT)
BOOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOOT)


class ConfigurationAuditTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.profile = self.root / "profile"
        self.repository = self.root / "consumer"
        self.profile.mkdir()
        self.repository.mkdir()

    def write(self, path, contents):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    def audit(self, harness):
        return BOOT.audit_configuration(argparse.Namespace(
            profile=self.profile, harness=harness, repository=[self.repository]
        ))

    def snapshot(self):
        return {
            str(path.relative_to(self.root)): path.read_bytes() if path.is_file() else None
            for path in self.root.rglob("*")
        }

    def test_codex_reports_disabled_plugins_named_profiles_and_agent_copies_without_writes(self):
        self.write(self.profile / "config.toml", '[plugins."old@market"]\nenabled = false\n'
                   '[marketplaces.legacy]\nsource_type = "git"\nsource = "secret-source"\n'
                   '[profiles.work.plugins."other@market"]\nenabled = true\n')
        self.write(self.profile / "agents/reader.toml", 'name = "reader"\n')
        self.write(self.profile / "skills/private/SKILL.md", "secret skill contents")
        self.write(self.repository / ".codex/agents/copied.toml", "secret copied contents")
        before = self.snapshot()
        with mock.patch.object(BOOT.subprocess, "run", side_effect=AssertionError("audit invoked a process")):
            report = self.audit("codex")
        self.assertEqual(before, self.snapshot())
        self.assertEqual("drift", report["status"])
        self.assertEqual(6, len(report["findings"]))
        self.assertEqual([], report["applied"])
        self.assertNotIn("secret", json.dumps(report))
        self.assertIn("profiles.work.plugins", [item["setting"] for item in report["findings"]])

    def test_claude_reports_user_tables_even_when_empty_or_disabled(self):
        self.write(self.profile / "settings.json", json.dumps({
            "enabledPlugins": {"old@market": False}, "extraKnownMarketplaces": {},
            "env": {"PRIVATE_TOKEN": "secret"}
        }))
        self.write(self.profile / "agents/local.md", "secret")
        self.write(self.profile / "skills/local/SKILL.md", "secret")
        report = self.audit("claude")
        self.assertEqual(4, len(report["findings"]))
        self.assertNotIn("secret", json.dumps(report))

    def test_caches_credentials_and_codex_builtin_skills_are_allowed(self):
        self.write(self.profile / "auth.json", '{"token":"secret"}')
        self.write(self.profile / "plugins/cache/market/plugin/SKILL.md", "cached")
        self.write(self.profile / "skills/.system/tool/SKILL.md", "host supplied")
        self.write(self.profile / "config.toml", 'model = "host-model"\n')
        report = self.audit("codex")
        self.assertEqual("clean", report["status"])
        self.assertEqual([], report["findings"])

    def test_repository_github_sources_pass_and_local_sources_fail_for_both_hosts(self):
        self.write(self.repository / ".codex/config.toml",
                   '[marketplaces.domain]\nsource_type = "git"\nsource = "https://github.com/tj-agents/cpp.git"\n'
                   '[marketplaces.local]\nsource_type = "local"\nsource = "C:/private/source"\n')
        self.write(self.repository / ".claude/settings.json", json.dumps({
            "extraKnownMarketplaces": {
                "domain": {"source": {"source": "github", "repo": "tj-agents/cpp"}},
                "local": {"source": {"source": "directory", "path": "C:/private/source"}}
            }
        }))
        for harness in ("codex", "claude"):
            with self.subTest(harness=harness):
                report = self.audit(harness)
                self.assertEqual(1, len(report["findings"]))
                self.assertEqual("local-marketplace-override", report["findings"][0]["code"])
                self.assertNotIn("private/source", json.dumps(report))

    def test_local_git_url_is_reported(self):
        self.write(self.repository / ".codex/config.toml",
                   '[marketplaces.local]\nsource_type = "git"\nsource = "file:///C:/private/source"\n')
        self.assertEqual("local-marketplace-override", self.audit("codex")["findings"][0]["code"])

    def test_claude_local_settings_are_also_audited(self):
        path = self.repository / ".claude/settings.local.json"
        self.write(path, json.dumps({"extraKnownMarketplaces": {
            "local": {"source": {"source": "directory", "path": "C:/private/source"}}
        }}))
        report = self.audit("claude")
        self.assertEqual(1, len(report["findings"]))
        self.assertEqual(str(path.resolve()), report["findings"][0]["path"])

    def test_invalid_settings_fail_without_echoing_contents(self):
        for harness, filename, contents in (
            ("claude", "settings.json", '{"private":"secret"'),
            ("claude", "settings.json", "[]"),
            ("codex", "config.toml", 'private = "secret'),
        ):
            with self.subTest(harness=harness, contents=contents):
                self.write(self.profile / filename, contents)
                with self.assertRaises(BOOT.BootstrapError) as raised:
                    self.audit(harness)
                self.assertNotIn("secret", str(raised.exception))

    def test_unreadable_configuration_fails(self):
        with mock.patch.object(Path, "read_text", side_effect=PermissionError("private contents")):
            with self.assertRaisesRegex(BOOT.BootstrapError, "Cannot read configuration") as raised:
                self.audit("claude")
        self.assertNotIn("private contents", str(raised.exception))

    def test_missing_profile_is_not_reported_clean_or_created(self):
        self.profile.rmdir()
        with self.assertRaisesRegex(BOOT.BootstrapError, "Profile directory does not exist"):
            self.audit("codex")
        self.assertFalse(self.profile.exists())

    def test_cli_exits_nonzero_on_drift_and_zero_on_clean_profile_without_catalog(self):
        args = ["--mode", "audit", "--harness", "claude", "--profile", str(self.profile)]
        with mock.patch.object(BOOT, "find_catalog", side_effect=AssertionError("audit loaded catalog")):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, BOOT.main(args))
            self.write(self.profile / "settings.json", '{"enabledPlugins":{}}')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(1, BOOT.main(args))
            self.assertEqual("drift", json.loads(output.getvalue())["status"])

    def test_existing_modes_still_require_lock(self):
        for mode in ("preview", "apply", "verify"):
            with self.subTest(mode=mode), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    BOOT.parse_arguments(["--mode", mode, "--harness", "codex", "--profile", str(self.profile)])
                self.assertEqual(2, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
