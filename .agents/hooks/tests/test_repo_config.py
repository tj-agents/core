import importlib.util
import json
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[2] / "machine" / "utility" / "bootstrap-capabilities" / "scripts" / "repo_config.py"
sys.path.insert(0, str(SCRIPT.parent))
spec = importlib.util.spec_from_file_location("repo_config", SCRIPT)
repo_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repo_config)
CATALOG = Path(__file__).resolve().parents[2] / "catalog" / "catalog.json"


class RepoConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.lock = self.root / ".agents" / "capabilities.lock.json"
        self.lock.parent.mkdir()
        self.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        release = next(r for r in self.catalog["releases"] if r["marketplace"] == "base-agents")
        self.selections = [
            {
                "id": plugin["id"], "release": release["id"], "commit": "a" * 40,
                "required_skills": [], "path_scopes": [], "exceptions": [],
            }
            for plugin in release["plugins"]
        ]
        self.save_lock()

    def save_lock(self):
        self.lock.write_text(json.dumps({"schema_version": 1, "plugins": self.selections}), encoding="utf-8")

    def test_generates_both_hosts_preserving_unrelated_settings_and_checks_drift(self):
        claude = self.root / ".claude" / "settings.json"
        codex = self.root / ".codex" / "config.toml"
        claude.parent.mkdir()
        codex.parent.mkdir()
        claude.write_text(json.dumps({"env": {"MODE": "test"}, "enabledPlugins": {"old@other": True}}), encoding="utf-8")
        codex.write_text('model = "test"\n\n[plugins."old@other"]\nenabled = true\n', encoding="utf-8")
        self.assertEqual([".claude/settings.json", ".codex/config.toml"], repo_config.run(self.lock, CATALOG, "check"))
        repo_config.run(self.lock, CATALOG, "write")
        self.assertEqual([], repo_config.run(self.lock, CATALOG, "check"))
        c = json.loads(claude.read_text(encoding="utf-8"))
        self.assertEqual("test", c["env"]["MODE"])
        self.assertEqual("tj-agents/core", c["extraKnownMarketplaces"]["base-agents"]["source"]["repo"])
        self.assertEqual("v2.1.16", c["extraKnownMarketplaces"]["base-agents"]["source"]["ref"])
        self.assertEqual(3, len(c["enabledPlugins"]))
        self.assertNotIn("old@other", c["enabledPlugins"])
        self.assertEqual([], c["permissions"]["allow"])
        d = codex.read_text(encoding="utf-8")
        self.assertIn('model = "test"', d)
        self.assertIn('source = "https://github.com/tj-agents/core.git"', d)
        self.assertIn('ref = "v2.1.16"', d)
        self.assertIn('sparse_paths = [".agents/plugins", ".claude-plugin", "plugins"]', d)
        self.assertIn('sparse_paths = [".agents/plugins", ".claude-plugin", "plugins"]', d)
        self.assertEqual(3, d.count('[plugins."'))

    def test_rejects_foreign_source(self):
        self.catalog["releases"][0]["source"] = "https://github.com/foreign/core.git"
        catalog = self.root / "catalog.json"
        catalog.write_text(json.dumps(self.catalog), encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "source disagrees with catalog owner"):
            repo_config.run(self.lock, catalog, "write")
        self.assertFalse((self.root / ".claude").exists())

    def test_uses_consumer_catalog_without_core_source_roster(self):
        local = self.catalog["releases"][0]
        external = json.loads(json.dumps(local))
        external.update({
            "id": "sample-market@1.0.0",
            "marketplace": "sample-market",
            "owner_repository": "sample-org/sample-standards",
            "source": "https://github.com/sample-org/sample-standards.git",
            "version": "1.0.0",
            "revision": "v1.0.0",
            "plugins": [external["plugins"][0]],
        })
        external["plugins"][0].update({
            "id": "sample-market/sample",
            "name": "sample",
            "version": "1.0.0",
            "package_path": "plugins/sample",
            "skills": ["sample-skill"],
            "dependencies": {"required": [], "optional": []},
            "harness": {
                "marketplaces": [{"id": "sample-market", "repository": "sample-org/sample-standards"}],
                "plugins": ["sample-market/sample"],
                "hooks": [],
                "permissions": {"claude_allow": ["Bash(sample-command)"], "codex_prefix_rules": []},
            },
        })
        optional = json.loads(json.dumps(external["plugins"][0]))
        optional.update({"id": "sample-market/optional", "name": "optional", "package_path": "plugins/optional"})
        external["plugins"].append(optional)
        self.catalog["releases"].append(external)
        project_catalog = self.root / ".agents" / "catalog" / "catalog.json"
        project_catalog.parent.mkdir()
        project_catalog.write_text(json.dumps(self.catalog), encoding="utf-8")
        self.selections.append({
            "id": "sample-market/sample", "release": external["id"], "commit": "b" * 40,
            "required_skills": [], "path_scopes": [], "exceptions": [],
        })
        self.save_lock()
        self.assertEqual(project_catalog.resolve(), repo_config.bootstrap.catalog_for_lock(self.lock, SCRIPT))
        repo_config.run(self.lock, project_catalog, "write")
        claude = json.loads((self.root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(
            "sample-org/sample-standards",
            claude["extraKnownMarketplaces"]["sample-market"]["source"]["repo"],
        )
        self.assertIn("Bash(sample-command)", claude["permissions"]["allow"])
        self.assertIs(claude["enabledPlugins"]["sample@sample-market"], True)
        self.assertIs(claude["enabledPlugins"]["optional@sample-market"], False)
        codex = (self.root / ".codex" / "config.toml").read_text(encoding="utf-8")
        self.assertIn('[plugins."optional@sample-market"]\nenabled = false', codex)
        self.assertIn('ref = "v1.0.0"', codex)

    def test_overlay_composes_permissions_and_removes_stale_rules(self):
        overlay = self.root / ".agents" / "repository-harness.json"
        rule = {
            "pattern": ["sample", "safe"],
            "justification": "Required for a repository workflow.",
            "match": ["sample safe --check"],
            "not_match": ["sample unsafe"],
        }
        overlay.write_text(json.dumps({
            "schema_version": 1,
            "requires": {
                "marketplaces": [{"id": "base-agents", "repository": "tj-agents/core"}],
                "plugins": ["base-agents/base"],
                "hooks": [],
                "permissions": {
                    "claude_allow": ["Bash(sample safe)"],
                    "codex_prefix_rules": [rule],
                },
            },
        }), encoding="utf-8")
        self.assertIn(".codex/rules/agent-harness.rules", repo_config.run(self.lock, CATALOG, "check"))
        repo_config.run(self.lock, CATALOG, "write")
        self.assertEqual([], repo_config.run(self.lock, CATALOG, "check"))
        claude = json.loads((self.root / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(1, len(claude["permissions"]["allow"]))
        path = self.root / ".codex/rules/agent-harness.rules"
        self.assertIn('decision = "allow"', path.read_text(encoding="utf-8"))
        overlay.unlink()
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "unmanaged permissions.allow entries: Bash\\(sample safe\\)"):
            repo_config.run(self.lock, CATALOG, "check")
        claude["permissions"]["allow"].remove("Bash(sample safe)")
        (self.root / ".claude/settings.json").write_text(json.dumps(claude), encoding="utf-8")
        self.assertEqual([".claude/settings.json", ".codex/rules/agent-harness.rules"], repo_config.run(self.lock, CATALOG, "check"))
        repo_config.run(self.lock, CATALOG, "write")
        self.assertFalse(path.exists())

    def test_hand_written_allow_rule_blocks_check_and_write_without_mutation(self):
        settings = self.root / ".claude" / "settings.json"
        settings.parent.mkdir()
        original = json.dumps({"permissions": {"allow": ["Bash(hand-written-rule)"]}})
        settings.write_text(original, encoding="utf-8")
        for mode in ("check", "write"):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "Bash\\(hand-written-rule\\)"):
                    repo_config.run(self.lock, CATALOG, mode)
                self.assertEqual(original, settings.read_text(encoding="utf-8"))
                self.assertFalse((self.root / ".codex").exists())

    def test_overlay_required_plugin_must_be_selected(self):
        overlay = self.root / ".agents" / "repository-harness.json"
        overlay.write_text(json.dumps({
            "schema_version": 1,
            "requires": {
                "marketplaces": [{"id": "base-agents", "repository": "tj-agents/core"}],
                "plugins": ["sample-market/sample"],
                "hooks": [],
                "permissions": {"claude_allow": [], "codex_prefix_rules": []},
            },
        }), encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "harness-required plugins"):
            repo_config.run(self.lock, CATALOG, "write")

    def test_requires_core_selection(self):
        self.selections.pop()
        self.save_lock()
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "omits core plugins"):
            repo_config.run(self.lock, CATALOG, "write")

    def local(self, mode="write", root=None):
        return repo_config.run(self.lock, CATALOG, mode, root=root or self.root, scope="local")

    def git(self, *arguments, root=None):
        return subprocess.run(["git", "-c", "core.hooksPath=none", "-c", "commit.gpgsign=false", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "-C", str(root or self.root), *arguments], check=True, capture_output=True, encoding="utf-8").stdout.strip()

    def overlay(self, allow):
        path = self.lock.parent / "repository-harness.json"
        path.write_text(json.dumps({"schema_version": 1, "requires": {"marketplaces": [], "plugins": [], "hooks": [], "permissions": {"claude_allow": allow, "codex_prefix_rules": []}}}), encoding="utf-8")
        return path

    def test_local_preview_is_complete_and_non_git_root_is_explicit(self):
        destination = self.root / "aggregate"
        destination.mkdir()
        targets = repo_config.plan(self.lock, CATALOG, root=destination, scope="local")
        self.assertEqual({".claude/settings.local.json", ".codex/config.toml", ".codex/rules/agent-harness.rules", repo_config.LOCAL_STATE}, {path.relative_to(destination.resolve()).as_posix() for path in targets})
        before = self.lock.read_bytes()
        self.local("preview", destination)
        self.assertEqual([], list(destination.iterdir()))
        self.local(root=destination)
        self.assertEqual([], self.local("check", destination))
        self.assertEqual(before, self.lock.read_bytes())
        self.assertFalse((destination / ".git").exists())
        self.assertFalse((destination / ".claude/settings.json").exists())

    def test_local_preserves_foreign_selections_settings_and_approvals(self):
        claude = self.root / ".claude/settings.local.json"
        codex = self.root / ".codex/config.toml"
        claude.parent.mkdir()
        codex.parent.mkdir()
        claude.write_text(json.dumps({"env": {"MODE": "test"}, "enabledPlugins": {"browser@foreign": True}, "extraKnownMarketplaces": {"foreign": {"source": "local"}}, "permissions": {"allow": ["Bash(manual)", "Bash(shared)"], "deny": ["Bash(forbidden)"], "ask": ["Bash(prompt)"]}}), encoding="utf-8")
        prefix = 'model = "test"\n[plugins."browser@foreign"]\nenabled = true\n[marketplaces.foreign]\nsource = "local"\n'
        codex.write_text(prefix, encoding="utf-8")
        overlay = self.overlay(["Bash(shared)", "Bash(owned)"])
        self.local()
        first = {path: path.read_bytes() for path in repo_config.plan(self.lock, CATALOG, root=self.root, scope="local") if path.exists()}
        self.local()
        self.assertEqual(first, {path: path.read_bytes() for path in first})
        overlay.unlink()
        self.local()
        settings = json.loads(claude.read_text(encoding="utf-8"))
        self.assertIs(settings["enabledPlugins"]["browser@foreign"], True)
        self.assertIn("foreign", settings["extraKnownMarketplaces"])
        self.assertEqual({"MODE": "test"}, settings["env"])
        self.assertEqual({"allow": ["Bash(manual)", "Bash(shared)"], "deny": ["Bash(forbidden)"], "ask": ["Bash(prompt)"]}, settings["permissions"])
        self.assertTrue(codex.read_text(encoding="utf-8").startswith(prefix))

    def test_local_restores_prior_value_when_selection_becomes_stale(self):
        claude = self.root / ".claude/settings.local.json"
        claude.parent.mkdir()
        claude.write_text(json.dumps({"enabledPlugins": {"base@base-agents": False}}), encoding="utf-8")
        self.local()
        state = repo_config.local_state(self.root / repo_config.LOCAL_STATE)
        settings, owned = repo_config.local_claude(claude, {}, {}, [], state["claude"])
        self.assertEqual({"base@base-agents": False}, json.loads(settings)["enabledPlugins"])
        self.assertEqual({}, owned["enabledPlugins"])
        self.assertEqual({}, json.loads(settings)["extraKnownMarketplaces"])

    def test_local_collision_and_changed_owned_keys_fail_before_any_mutation(self):
        codex = self.root / ".codex/config.toml"
        codex.parent.mkdir()
        text = '[plugins."base@base-agents"]\nenabled = true\n'
        codex.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "collision"):
            self.local()
        self.assertFalse((self.root / ".claude").exists())
        self.assertEqual(text, codex.read_text(encoding="utf-8"))
        codex.unlink()
        self.local()
        claude = self.root / ".claude/settings.local.json"
        settings = json.loads(claude.read_text(encoding="utf-8"))
        settings["enabledPlugins"]["base@base-agents"] = False
        claude.write_text(json.dumps(settings), encoding="utf-8")
        unchanged = codex.read_bytes()
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "owned setting was changed"):
            self.local()
        self.assertEqual(unchanged, codex.read_bytes())

    def test_local_rejects_unowned_or_changed_codex_block_and_rules(self):
        self.local()
        codex = self.root / ".codex/config.toml"
        codex.write_text(codex.read_text(encoding="utf-8").replace('enabled = true', 'enabled = false', 1), encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "not owned or was changed"):
            self.local()
        codex.unlink()
        rules = self.root / ".codex/rules/agent-harness.rules"
        rules.parent.mkdir(exist_ok=True)
        rules.write_text("manual rule", encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "rules are not owned"):
            self.local()
        self.assertFalse(codex.exists())

    def test_local_tracked_target_is_rejected_with_no_changes(self):
        self.git("init", "--quiet")
        codex = self.root / ".codex/config.toml"
        codex.parent.mkdir()
        codex.write_text('model = "keep"\n', encoding="utf-8")
        self.git("add", ".codex/config.toml")
        before = codex.read_bytes()
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "tracked"):
            self.local()
        self.assertEqual(before, codex.read_bytes())
        self.assertFalse((self.root / ".claude").exists())

    def test_git_exclusions_preserve_unrelated_patterns_and_are_exact(self):
        self.git("init", "--quiet")
        exclude = self.root / ".git/info/exclude"
        exclude.write_text("unrelated.log\nliteral\\ \n", encoding="utf-8")
        preview = self.local("preview")
        self.assertIn(".git/info/exclude", preview)
        self.assertEqual("unrelated.log\nliteral\\ \n", exclude.read_text(encoding="utf-8"))
        self.local()
        content = exclude.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("unrelated.log\nliteral\\ \n"))
        for relative in (".claude/settings.local.json", ".codex/config.toml", ".codex/rules/agent-harness.rules", repo_config.LOCAL_STATE):
            self.assertIn("/" + relative + "\n", content)
            self.assertEqual(relative, self.git("check-ignore", relative))
        self.assertNotIn("/.claude/\n", content)
        self.assertEqual([], self.local("check"))

    def test_git_file_worktree_uses_common_info_exclude(self):
        self.git("init", "--quiet")
        self.git("commit", "--allow-empty", "--quiet", "-m", "Fixture")
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary).resolve() / "checkout"
            self.git("worktree", "add", "--quiet", "-b", "fixture-worktree", str(destination))
            self.assertTrue((destination / ".git").is_file())
            targets = repo_config.plan(self.lock, CATALOG, root=destination, scope="local")
            exclude = (self.root / ".git/info/exclude").resolve()
            self.assertIn(exclude, [path.resolve() for path in targets])
            self.local(root=destination)
            self.assertEqual([], self.local("check", destination))
            self.assertEqual(".codex/config.toml", self.git("check-ignore", ".codex/config.toml", root=destination))

    def test_prospective_paths_reject_escape_tracked_and_non_directory_parent(self):
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "escapes"):
            repo_config.preflight_paths(self.root, [Path("../escape.json")])
        (self.root / ".codex").write_text("file", encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "parent is not a directory"):
            self.local()
        self.assertFalse((self.root / ".claude").exists())
        (self.root / ".codex").unlink()
        self.git("init", "--quiet")
        prospective = self.root / "future.json"
        prospective.write_text("tracked", encoding="utf-8")
        self.git("add", "future.json")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "tracked"):
            repo_config.plan(self.lock, CATALOG, root=self.root, scope="local", prospective_paths=[prospective])
        self.assertFalse((self.root / ".claude").exists())

    def test_escaping_link_with_missing_leaf_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            outside = Path(temporary).resolve()
            link = self.root / ".codex"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except OSError:
                result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
                if result.returncode:
                    self.skipTest("Directory links unavailable")
            with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "escapes"):
                self.local()
            self.assertEqual([], list(outside.iterdir()))
            self.assertFalse((self.root / ".claude").exists())

    def test_malformed_ownership_and_exclusions_are_preflighted(self):
        state = self.root / repo_config.LOCAL_STATE
        state.write_text('{"schema_version":1,"claude":[]}', encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "ownership"):
            self.local()
        self.assertFalse((self.root / ".claude").exists())
        state.unlink()
        self.git("init", "--quiet")
        exclude = self.root / ".git/info/exclude"
        exclude.write_text(repo_config.EXCLUDE_START, encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "malformed managed exclusions"):
            self.local()
        self.assertFalse((self.root / ".claude").exists())

    def test_non_git_subdirectory_cannot_bypass_checkout_tracking(self):
        self.git("init", "--quiet")
        child = self.root / "subdirectory"
        child.mkdir()
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "exact Git checkout"):
            self.local(root=child)
        self.assertEqual([], list(child.iterdir()))

    def test_exclusion_parent_failure_is_detected_before_settings_write(self):
        self.git("init", "--quiet")
        info = self.root / ".git/info"
        (info / "exclude").unlink()
        info.rmdir()
        info.write_text("blocked", encoding="utf-8")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "parent is not a directory"):
            self.local()
        self.assertFalse((self.root / ".claude").exists())

    def test_prospective_exclusions_escape_pattern_metacharacters(self):
        self.git("init", "--quiet")
        target = self.root / "receipt[1].json"
        targets = repo_config.plan(self.lock, CATALOG, root=self.root, scope="local", prospective_paths=[target])
        exclude = self.root / ".git/info/exclude"
        exclude.write_text(targets[exclude.resolve()], encoding="utf-8")
        self.assertEqual("receipt[1].json", self.git("check-ignore", "receipt[1].json"))
        result = subprocess.run(["git", "-C", str(self.root), "check-ignore", "receipt1.json"], capture_output=True)
        self.assertEqual(1, result.returncode)

    def test_local_stale_owned_rules_are_removed(self):
        overlay = self.overlay([])
        value = json.loads(overlay.read_text(encoding="utf-8"))
        value["requires"]["permissions"]["codex_prefix_rules"] = [{"pattern": ["sample", "safe"], "justification": "Fixture approval", "match": ["sample safe"], "not_match": ["sample unsafe"]}]
        overlay.write_text(json.dumps(value), encoding="utf-8")
        self.local()
        rules = self.root / ".codex/rules/agent-harness.rules"
        self.assertIn('decision = "allow"', rules.read_text(encoding="utf-8"))
        overlay.unlink()
        self.assertIn(".codex/rules/agent-harness.rules", self.local("preview"))
        self.assertTrue(rules.is_file())
        self.local()
        self.assertFalse(rules.exists())
        self.assertEqual([], self.local("check"))

    def test_tracked_config_behind_in_root_directory_link_is_rejected(self):
        self.git("init", "--quiet")
        shared = self.root / "shared"
        shared.mkdir()
        (shared / "config.toml").write_text('model = "keep"', encoding="utf-8")
        self.git("add", "shared/config.toml")
        link = self.root / ".codex"
        try:
            link.symlink_to(shared, target_is_directory=True)
        except OSError:
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(shared)], capture_output=True)
            if result.returncode:
                self.skipTest("Directory links unavailable")
        with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "tracked"):
            self.local()
        self.assertFalse((self.root / ".claude").exists())
        self.assertEqual('model = "keep"', (shared / "config.toml").read_text(encoding="utf-8"))

    def test_two_host_targets_cannot_alias_the_same_missing_file(self):
        claude = self.root / ".claude/settings.local.json"
        claude.parent.mkdir()
        original = Path.resolve
        codex = self.root / ".codex/config.toml"

        def physical_path(path, *args, **kwargs):
            return original(codex if path == claude else path, *args, **kwargs)

        with mock.patch.object(Path, "resolve", autospec=True, side_effect=physical_path):
            with self.assertRaisesRegex(repo_config.bootstrap.BootstrapError, "alias the same file"):
                self.local()
        self.assertFalse((self.root / ".codex").exists())
        self.assertFalse((self.root / repo_config.LOCAL_STATE).exists())


if __name__ == "__main__":
    unittest.main()
