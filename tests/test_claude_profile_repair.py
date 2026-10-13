from dataclasses import replace
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest import mock

from test_claude_standards_sync import SYNC, StandardsSyncHarness, git


class PackageCompletenessTests(StandardsSyncHarness):
    def installed(self):
        return SYNC.installs(self.plugins, self.project, {"base@core"})[0]

    def test_missing_declared_skills_hooks_and_harness_hooks_are_incomplete(self):
        package = self.install()
        cases = {
            "declared skills": (
                {"name": "base", "skills": "./missing"},
                None,
            ),
            "declared hook": (
                {"name": "base", "hooks": "./hooks/claude.json"},
                {"hooks": {"SessionStart": [{"command": "${CLAUDE_PLUGIN_ROOT}/missing.py"}]}},
            ),
            "harness hook": (
                {"name": "base"},
                None,
            ),
        }
        for name, (manifest, hooks) in cases.items():
            with self.subTest(name=name):
                (package / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
                if hooks is not None:
                    (package / "hooks" / "claude.json").write_text(json.dumps(hooks), encoding="utf-8")
                if name == "harness hook":
                    self.write(package / "harness.json", {
                        "requires": {"hooks": [{"hosts": ["claude"], "path": "hooks/missing.py"}]},
                    })
                self.assertFalse(SYNC.package_complete(self.installed()))
                self.install()

    def test_optional_manifest_sections_and_harness_are_healthy(self):
        package = self.install()
        (package / ".claude-plugin" / "plugin.json").write_text(json.dumps({"name": "base"}), encoding="utf-8")
        (package / "harness.json").unlink()
        self.assertTrue(SYNC.package_complete(self.installed()))

    def test_manifestless_package_is_accepted_only_for_a_non_strict_catalog_entry(self):
        package = self.install()
        (package / ".claude-plugin" / "plugin.json").unlink()
        self.write(self.checkout / ".claude-plugin" / "marketplace.json", {
            "plugins": [{"name": "base", "strict": False}],
        })
        relaxed = SYNC.marketplaces(self.plugins, [self.installed()])[0].installs[0]
        self.assertTrue(SYNC.package_complete(relaxed))
        self.assertFalse(SYNC.package_complete(replace(relaxed, strict=True)))

    def test_actual_sha_overrides_cached_state_and_versions_fall_back_to_suffixes(self):
        self.install()
        installed = self.installed()
        remote = git(self.checkout, "rev-parse", "HEAD")
        stale_sha = "f" * 40 if remote != "f" * 40 else "e" * 40
        self.assertFalse(SYNC.current(replace(installed, git_commit_sha=stale_sha), remote, {installed.key: remote}))
        self.assertTrue(SYNC.current(replace(installed, git_commit_sha=remote), remote, {}))
        legacy = replace(installed, git_commit_sha=None, version=f"release-{remote[:12]}")
        self.assertTrue(SYNC.installed_at(legacy, remote))

    def test_same_version_repair_does_not_record_state_when_reinstall_fails(self):
        package = self.install()
        shutil.rmtree(package / "skills")
        with mock.patch.dict("os.environ", {"FAKE_CLAUDE_FAIL": "base@core"}):
            code, output = self.sync()
        self.assertEqual(code, 1)
        self.assertIn("base@core (user) was not updated", output)
        self.assertEqual(
            [entry["argv"] for entry in self.invocations()],
            [
                ["plugin", "uninstall", "base@core", "--scope", "user", "--keep-data"],
                ["plugin", "install", "base@core", "--scope", "user"],
            ],
        )
        self.assertNotIn(self.installed().key, SYNC.load_state(self.state))

    def test_same_version_repair_uninstalls_with_keep_data_then_reinstalls(self):
        package = self.install()
        shutil.rmtree(package / "skills")
        code, output = self.sync()
        self.assertEqual(code, 0, output)
        self.assertEqual(
            [entry["argv"] for entry in self.invocations()],
            [
                ["plugin", "uninstall", "base@core", "--scope", "user", "--keep-data"],
                ["plugin", "install", "base@core", "--scope", "user"],
            ],
        )
        self.assertIn(self.installed().key, SYNC.load_state(self.state))


class ProfileMigrationTests(StandardsSyncHarness):
    def configure_dotnet_sources(self):
        self.write(self.plugins / "known_marketplaces.json", {
            "core": {"source": {"source": "git", "url": str(self.remote)}, "installLocation": str(self.checkout)},
            "tj-agents": {
                "source": {"source": "github", "repo": "tj-agents/marketplace"},
                "installLocation": str(self.checkout),
            },
            "base-agents": {"source": {"source": "github", "repo": "tj-agents/core"}, "installLocation": str(self.checkout)},
            "dotagents": {"source": {"source": "github", "repo": "tj-agents/dotnet"}, "installLocation": str(self.checkout)},
        })
        self.write(self.checkout / ".claude-plugin" / "marketplace.json", {
            "plugins": [
                {"name": "base", "source": {"source": "github", "repo": "tj-agents/core"}},
                {"name": "dotnet", "source": {"source": "github", "repo": "tj-agents/dotnet"}},
            ],
        })

    def migrate(self, check=False, executable=None):
        out = io.StringIO()
        code = SYNC.migrate_profile(
            self.config, self.plugins, self.project, self.executable if executable is None else executable, check, out,
        )
        return code, out.getvalue()

    def profile(self):
        return json.loads((self.config / "settings.json").read_text(encoding="utf-8"))

    def test_stale_alias_uses_authenticated_sibling_and_migrates_without_deleting_registry_sources(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        self.install("dotnet@tj-agents")
        self.enable({"dotnet@dotnet": True, "unrelated@foreign": True})
        known_before = (self.plugins / "known_marketplaces.json").read_text(encoding="utf-8")
        code, output = self.migrate()
        self.assertEqual((code, output), (0, ""))
        self.assertEqual(self.profile()["enabledPlugins"], {"dotnet@tj-agents": True, "unrelated@foreign": True})
        self.assertTrue(self.records("dotnet@dotagents"))
        self.assertEqual((self.plugins / "known_marketplaces.json").read_text(encoding="utf-8"), known_before)

    def test_disabled_alias_and_existing_canonical_false_remain_disabled(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        self.install("dotnet@tj-agents")
        for enabled in (
            {"dotnet@dotagents": False},
            {"dotnet@dotagents": True, "dotnet@tj-agents": False},
        ):
            with self.subTest(enabled=enabled):
                self.enable(enabled)
                code, output = self.migrate()
                self.assertEqual((code, output), (0, ""))
                self.assertEqual(self.profile()["enabledPlugins"], {"dotnet@tj-agents": False})

    def test_canonical_enablement_defers_for_any_scoped_legacy_false_choice(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        self.install("dotnet@tj-agents")
        other = Path(self.temp.name) / "other project"
        other.mkdir()
        self.install("dotnet@dotagents", scope="project", project=other)
        self.write(other / ".claude" / "settings.json", {"enabledPlugins": {"dotnet@dotagents": False}})
        self.enable({"dotnet@dotagents": True})
        before = self.profile()
        code, output = self.migrate()
        self.assertEqual(code, 1)
        self.assertIn("deferred for dotnet@tj-agents", output)
        self.assertEqual(self.profile(), before)

    def test_active_project_legacy_false_defers_without_a_scoped_install(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        self.install("dotnet@tj-agents")
        self.write(self.project / ".claude" / "settings.json", {"enabledPlugins": {"dotnet@dotagents": False}})
        self.enable({"dotnet@dotagents": True})
        before = self.profile()
        code, output = self.migrate()
        self.assertEqual(code, 1)
        self.assertIn("deferred for dotnet@tj-agents", output)
        self.assertEqual(self.profile(), before)

    def test_mixed_migration_and_scoped_deferral_reports_a_problem(self):
        self.configure_dotnet_sources()
        self.install("base@base-agents")
        self.install("base@tj-agents")
        self.install("dotnet@dotagents")
        self.install("dotnet@tj-agents")
        other = Path(self.temp.name) / "scoped dotnet"
        other.mkdir()
        self.install("dotnet@dotagents", scope="project", project=other)
        self.write(other / ".claude" / "settings.json", {"enabledPlugins": {"dotnet@dotagents": False}})
        self.enable({"base@base-agents": True, "dotnet@dotagents": True})
        code, output = self.migrate()
        self.assertEqual(code, 1)
        self.assertIn("deferred for dotnet@tj-agents", output)
        self.assertEqual(self.profile()["enabledPlugins"], {
            "base@tj-agents": True,
            "dotnet@dotagents": True,
        })

    def test_install_or_verification_failure_preserves_aliases_and_unrelated_settings(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        incomplete = self.install("dotnet@tj-agents")
        shutil.rmtree(incomplete / "skills")
        original = {"dotnet@dotagents": True, "unrelated@foreign": False}
        for result in ((False, "install denied"), (True, "claimed success")):
            with self.subTest(result=result), mock.patch.object(SYNC, "claude", return_value=result):
                self.enable(original)
                code, output = self.migrate()
                self.assertEqual(code, 1)
                self.assertIn("aliases were preserved", output)
                self.assertEqual(self.profile()["enabledPlugins"], original)

    def test_changed_alias_preference_defers_only_its_selection(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        self.install("dotnet@tj-agents")
        self.enable({"dotnet@dotagents": True, "unrelated@foreign": True})
        original = SYNC.read_json_object
        reads = 0

        def reread(path):
            nonlocal reads
            if path == self.config / "settings.json":
                reads += 1
                if reads == 2:
                    self.enable({"dotnet@dotagents": False, "unrelated@foreign": True})
            return original(path)

        with mock.patch.object(SYNC, "read_json_object", side_effect=reread):
            code, output = self.migrate()
        self.assertEqual(code, 1)
        self.assertIn("affected preferences changed", output)
        self.assertEqual(self.profile()["enabledPlugins"], {"dotnet@dotagents": False, "unrelated@foreign": True})

    def test_registered_stale_alias_requires_its_own_authenticated_marketplace(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        self.install("dotnet@dotnet")
        self.install("dotnet@tj-agents")
        known = SYNC.read_json_object(self.plugins / "known_marketplaces.json")
        known["dotnet"] = {"source": {"source": "github", "repo": "foreign/dotnet"}, "installLocation": str(self.checkout)}
        self.write(self.plugins / "known_marketplaces.json", known)
        self.enable({"dotnet@dotnet": True})
        before = self.profile()
        code, _ = self.migrate()
        self.assertEqual(code, 1)
        self.assertEqual(self.profile(), before)

    def test_missing_executable_defers_enabled_selection_but_allows_false_selection(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        self.install("dotnet@tj-agents")
        self.enable({"dotnet@dotagents": True})
        before = self.profile()
        out = io.StringIO()
        code = SYNC.migrate_profile(self.config, self.plugins, self.project, None, False, out)
        self.assertEqual(code, 1)
        self.assertIn("claude executable was not found", out.getvalue())
        self.assertEqual(self.profile(), before)
        self.enable({"dotnet@dotagents": False})
        code = SYNC.migrate_profile(self.config, self.plugins, self.project, None, False, io.StringIO())
        self.assertEqual(code, 0)
        self.assertEqual(self.profile()["enabledPlugins"], {"dotnet@tj-agents": False})

    def test_cli_preview_reaches_migration_without_writing_the_profile(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        self.install("dotnet@tj-agents")
        self.install("base@core")
        self.enable({"dotnet@dotnet": True, "base@core": True})
        settings_path = self.config / "settings.json"
        before = settings_path.read_bytes()
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(Path(__file__).resolve().parents[1] / ".agents/machine/scripts/claude_standards_sync.py"),
                "--project",
                str(self.project),
                "--claude",
                self.executable,
                "--migrate-profile",
                "--check",
            ],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=30,
        )
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("profile migration would select dotnet@tj-agents", completed.stdout)
        self.assertEqual(settings_path.read_bytes(), before)
        self.assertEqual(self.invocations(), [])

    def test_malformed_user_or_scoped_profiles_refuse_all_mutation(self):
        self.configure_dotnet_sources()
        self.install("dotnet@dotagents")
        self.install("dotnet@tj-agents")
        settings = self.config / "settings.json"
        for kind in ("user", "scoped"):
            with self.subTest(kind=kind):
                self.enable({"dotnet@dotagents": True})
                if kind == "user":
                    settings.write_text("[]", encoding="utf-8")
                else:
                    other = Path(self.temp.name) / "malformed scoped"
                    other.mkdir(exist_ok=True)
                    self.install("dotnet@dotagents", scope="project", project=other)
                    path = other / ".claude" / "settings.json"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("[]", encoding="utf-8")
                before = settings.read_text(encoding="utf-8")
                code, output = self.migrate()
                self.assertEqual(code, 1)
                self.assertIn("profile registry is malformed" if kind == "user" else "scoped profile is malformed", output)
                self.assertEqual(settings.read_text(encoding="utf-8"), before)

    def test_repository_authentication_requires_the_exact_github_owner_and_repository(self):
        self.assertFalse(SYNC.source_matches_repository(
            {"source": "git", "url": "https://github.com.evil/tj-agents/marketplace.git"}, "tj-agents/marketplace",
        ))
        self.assertFalse(SYNC.source_matches_repository(
            {"source": "github", "repo": "tj-agents-lookalike/marketplace"}, "tj-agents/marketplace",
        ))
        self.assertFalse(SYNC.source_matches_repository(
            {"source": "git", "url": "file://github.com/tj-agents/marketplace.git"}, "tj-agents/marketplace",
        ))
        self.assertFalse(SYNC.source_matches_repository(
            {"source": "git", "url": "github.com/tj-agents/marketplace.git"}, "tj-agents/marketplace",
        ))
if __name__ == "__main__":
    unittest.main()
