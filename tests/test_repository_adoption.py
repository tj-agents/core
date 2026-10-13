import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/machine/utility/bootstrap-capabilities/scripts"
sys.path.insert(0, str(SCRIPTS))
import bootstrap_capabilities as bootstrap

spec = importlib.util.spec_from_file_location("adopt_repository", SCRIPTS / "adopt_repository.py")
adoption = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adoption)


class RepositoryAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "project"
        self.input = self.base / "sources.json"
        self.core, core_commit = self.source(
            "core", "base-agents", "tj-agents/core",
            {"base": ([], ["base-rule"]), "engineering": (["base-agents/base"], ["feature"]),
             "machine": (["base-agents/base"], ["bootstrap-capabilities"])},
        )
        self.dotnet, dotnet_commit = self.source(
            "dotnet", "dotagents", "tj-agents/dotnet",
            {"dotnet": ([], ["direction", "knowledge", "scaffold"]), "extras": ([], ["extras"])},
        )
        self.azure, azure_commit = self.source(
            "azure", "azure-agents", "tj-agents/azure",
            {"azure": (["dotagents/dotnet"], ["direction", "knowledge", "learning"])},
            {"dotagents": "tj-agents/dotnet"},
        )
        self.document = {
            "schema_version": 1,
            "sources": [
                self.request(self.core, "tj-agents/core", core_commit, ["base", "engineering", "machine"], "base"),
                self.request(self.dotnet, "tj-agents/dotnet", dotnet_commit, ["dotnet", "extras"], "dotnet"),
                self.request(self.azure, "tj-agents/azure", azure_commit, ["azure"], "azure"),
            ],
        }
        self.save_input()

    def git(self, path, *arguments):
        return subprocess.run(["git", "-C", str(path), *arguments], check=True, capture_output=True, text=True).stdout.strip()

    def source(self, name, marketplace, repository, packages, foreign_markets=None):
        root = self.base / name
        root.mkdir()
        self.git(root, "init", "-q")
        self.git(root, "config", "user.name", "Fixture")
        self.git(root, "config", "user.email", "fixture@example.test")
        self.git(root, "remote", "add", "origin", f"https://github.com/{repository}.git")
        names = sorted(packages)
        self.write_json(root / ".claude-plugin/marketplace.json", {"name": marketplace, "plugins": [
            {"name": package, "source": f"./plugins/{package}"} for package in names]})
        self.write_json(root / ".agents/plugins/marketplace.json", {"name": marketplace, "plugins": [
            {"name": package, "source": {"source": "local", "path": f"./plugins/{package}"}} for package in names]})
        markets = {marketplace: repository, **(foreign_markets or {})}
        for package, (dependencies, skills) in packages.items():
            package_root = root / "plugins" / package
            native = {"name": package, "version": "1.0.0", "description": package, "skills": "./skills/"}
            for host in ("codex", "claude"):
                self.write_json(package_root / f".{host}-plugin/plugin.json", native)
            self.write_json(package_root / "harness.json", {"schema_version": 1, "plugin": f"{marketplace}/{package}", "requires": {
                "marketplaces": [{"id": item, "repository": owner} for item, owner in sorted(markets.items())],
                "plugins": [f"{marketplace}/{package}", *dependencies], "hooks": [],
                "permissions": {"claude_allow": [], "codex_prefix_rules": []},
            }})
            self.write_json(package_root / "selection.json", {"plugin": package, "dependencies": dependencies})
            for skill in skills:
                self.write(package_root / "skills" / skill / "SKILL.md", b"---\nname: fixture\n---\nfixture\n")
        self.git(root, "add", ".")
        self.git(root, "commit", "-qm", "Fixture")
        return root, self.git(root, "rev-parse", "HEAD")

    def request(self, checkout, repository, commit, plugins, version_plugin):
        return {"repository": repository, "checkout": str(checkout), "commit": commit,
                "plugins": plugins, "version_plugin": version_plugin}

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)

    def write_json(self, path, value):
        self.write(path, json.dumps(value).encode("utf-8"))

    def save_input(self):
        self.input.write_text(json.dumps(self.document), encoding="utf-8")

    def commit_json_change(self, root, relative, mutate):
        path = root / relative
        value = json.loads(path.read_text(encoding="utf-8"))
        mutate(value)
        path.write_text(json.dumps(value), encoding="utf-8")
        self.git(root, "add", ".")
        self.git(root, "commit", "-qm", "Changed fixture")
        return self.git(root, "rev-parse", "HEAD")

    def files(self):
        if not self.project.exists():
            return {}
        return {path.relative_to(self.project).as_posix(): path.read_bytes() for path in self.project.rglob("*") if path.is_file()}

    def invoke(self, plugins, mode="write", root=None, input_path=None):
        return adoption.run(root or self.project, input_path or self.input, plugins, mode)

    def test_dotnet_and_azure_write_lock_catalog_and_host_settings(self):
        drift = self.invoke(["dotagents/dotnet", "azure-agents/azure"])
        self.assertEqual([
            ".agents/capabilities.lock.json", ".agents/catalog/catalog.json", ".claude/settings.json", ".codex/config.toml",
        ], drift)
        lock = json.loads((self.project / ".agents/capabilities.lock.json").read_text(encoding="utf-8"))
        selected = {entry["id"]: entry for entry in lock["plugins"]}
        self.assertEqual({"base-agents/base", "base-agents/engineering", "base-agents/machine", "dotagents/dotnet", "azure-agents/azure"}, set(selected))
        self.assertEqual(["direction", "knowledge", "learning"], selected["azure-agents/azure"]["required_skills"])
        self.assertEqual(["direction", "knowledge", "scaffold"], selected["dotagents/dotnet"]["required_skills"])
        self.assertIn('azure@azure-agents', (self.project / ".codex/config.toml").read_text(encoding="utf-8"))
        claude = json.loads((self.project / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertTrue(claude["enabledPlugins"]["azure@azure-agents"])
        self.assertEqual([], self.invoke(["dotagents/dotnet", "azure-agents/azure"], "check"))

    def test_addition_preserves_existing_metadata_and_snapshot(self):
        self.invoke(["dotagents/dotnet"])
        lock_path = self.project / ".agents/capabilities.lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["project_metadata"] = {"owner": "fixture"}
        dotnet = next(entry for entry in lock["plugins"] if entry["id"] == "dotagents/dotnet")
        dotnet["required_skills"] = ["direction"]
        dotnet["path_scopes"] = [{"path": "src", "skills": ["knowledge"]}]
        dotnet["exceptions"] = ["https://example.test/exception"]
        lock_path.write_text(json.dumps(lock), encoding="utf-8")
        self.invoke(["azure-agents/azure"])
        updated = json.loads(lock_path.read_text(encoding="utf-8"))
        dotnet = next(entry for entry in updated["plugins"] if entry["id"] == "dotagents/dotnet")
        self.assertEqual(["direction"], dotnet["required_skills"])
        self.assertEqual([{"path": "src", "skills": ["knowledge"]}], dotnet["path_scopes"])
        self.assertEqual(["https://example.test/exception"], dotnet["exceptions"])
        self.assertEqual({"owner": "fixture"}, updated["project_metadata"])
        self.assertIn("azure-agents/azure", {entry["id"] for entry in updated["plugins"]})

    def test_tagged_existing_release_adds_sibling_at_its_pinned_commit(self):
        self.invoke(["dotagents/dotnet"])
        lock_path = self.project / ".agents/capabilities.lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        dotnet = next(entry for entry in lock["plugins"] if entry["id"] == "dotagents/dotnet")
        dotnet["path_scopes"] = [{"path": "src", "skills": ["knowledge"]}]
        commit = dotnet["commit"]
        lock_path.write_text(json.dumps(lock), encoding="utf-8")
        catalog_path = self.project / ".agents/catalog/catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        release = next(value for value in catalog["releases"] if value["marketplace"] == "dotagents")
        release["revision"] = "v1.0.0"
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        self.input.write_text(json.dumps({"schema_version": 1, "sources": [self.document["sources"][0]]}), encoding="utf-8")
        self.invoke(["dotagents/extras"])
        updated = json.loads(lock_path.read_text(encoding="utf-8"))
        selected = {entry["id"]: entry for entry in updated["plugins"]}
        self.assertEqual(commit, selected["dotagents/extras"]["commit"])
        self.assertEqual([{"path": "src", "skills": ["knowledge"]}], selected["dotagents/dotnet"]["path_scopes"])

    def test_unpinned_existing_tagged_release_cannot_add_a_sibling(self):
        self.invoke(["dotagents/dotnet"])
        lock_path = self.project / ".agents/capabilities.lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["plugins"] = [entry for entry in lock["plugins"] if entry["id"] != "dotagents/dotnet"]
        lock_path.write_text(json.dumps(lock), encoding="utf-8")
        catalog_path = self.project / ".agents/catalog/catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        release = next(value for value in catalog["releases"] if value["marketplace"] == "dotagents")
        release["revision"] = "v1.0.0"
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        self.input.write_text(json.dumps({"schema_version": 1, "sources": [self.document["sources"][0]]}), encoding="utf-8")
        before = self.files()
        with self.assertRaisesRegex(bootstrap.BootstrapError, "commit must be a full lowercase Git commit"):
            self.invoke(["dotagents/extras"])
        self.assertEqual(before, self.files())

    def test_unpinned_existing_sha_release_can_add_a_sibling(self):
        self.invoke(["dotagents/dotnet"])
        lock_path = self.project / ".agents/capabilities.lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["plugins"] = [entry for entry in lock["plugins"] if entry["id"] != "dotagents/dotnet"]
        lock_path.write_text(json.dumps(lock), encoding="utf-8")
        self.input.write_text(json.dumps({"schema_version": 1, "sources": [self.document["sources"][0]]}), encoding="utf-8")
        self.invoke(["dotagents/extras"])
        updated = json.loads(lock_path.read_text(encoding="utf-8"))
        extras = next(entry for entry in updated["plugins"] if entry["id"] == "dotagents/extras")
        self.assertRegex(extras["commit"], r"^[0-9a-f]{40}$")

    def test_preview_missing_root_is_read_only_and_check_detects_drift(self):
        missing = self.base / "new-project"
        self.assertEqual([
            ".agents/capabilities.lock.json", ".agents/catalog/catalog.json", ".claude/settings.json", ".codex/config.toml",
        ], self.invoke(["dotagents/dotnet"], "preview", root=missing))
        self.assertFalse(missing.exists())
        self.invoke(["dotagents/dotnet"])
        codex = self.project / ".codex/config.toml"
        codex.write_text("model = \"changed\"\n", encoding="utf-8")
        self.assertEqual([".codex/config.toml"], self.invoke(["dotagents/dotnet"], "check"))

    def test_invalid_input_and_input_alias_leave_repository_unchanged(self):
        before = self.files()
        invalid = copy.deepcopy(self.document)
        invalid["sources"][0]["commit"] = "a" * 8
        self.input.write_text(json.dumps(invalid), encoding="utf-8")
        with self.assertRaises(bootstrap.BootstrapError):
            self.invoke(["dotagents/dotnet"])
        self.assertEqual(before, self.files())
        self.save_input()
        self.project.mkdir()
        alias = self.project / ".claude/settings.json"
        alias.parent.mkdir()
        alias.write_text(json.dumps(self.document), encoding="utf-8")
        before = self.files()
        with self.assertRaisesRegex(bootstrap.BootstrapError, "aliases a read input"):
            self.invoke(["dotagents/dotnet"], "preview", input_path=alias)
        self.assertEqual(before, self.files())

    def test_invalid_source_dependency_and_unknown_plugin_leave_no_outputs(self):
        invalid = copy.deepcopy(self.document)
        invalid["sources"] = [source for source in invalid["sources"] if source["repository"] != "tj-agents/dotnet"]
        self.input.write_text(json.dumps(invalid), encoding="utf-8")
        with self.assertRaisesRegex(bootstrap.BootstrapError, "unresolved or contradictory"):
            self.invoke(["azure-agents/azure"])
        self.assertEqual({}, self.files())
        self.save_input()
        with self.assertRaisesRegex(bootstrap.BootstrapError, "unknown plugin"):
            self.invoke(["missing/standard"])
        self.assertEqual({}, self.files())

    def test_contradictory_metadata_and_incomplete_pair_leave_no_outputs(self):
        changed = self.commit_json_change(self.azure, "plugins/azure/selection.json", lambda value: value.update(dependencies=[]))
        invalid = copy.deepcopy(self.document)
        invalid["sources"][2]["commit"] = changed
        self.input.write_text(json.dumps(invalid), encoding="utf-8")
        with self.assertRaisesRegex(bootstrap.BootstrapError, "Selection dependencies disagree"):
            self.invoke(["azure-agents/azure"])
        self.assertEqual({}, self.files())
        self.save_input()
        self.invoke(["dotagents/dotnet"])
        catalog = self.project / ".agents/catalog/catalog.json"
        catalog.unlink()
        before = self.files()
        with self.assertRaisesRegex(bootstrap.BootstrapError, "committed together"):
            self.invoke(["azure-agents/azure"])
        self.assertEqual(before, self.files())

    def test_incompatible_existing_package_record_is_rejected_without_writes(self):
        self.invoke(["dotagents/dotnet"])
        catalog_path = self.project / ".agents/catalog/catalog.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        dotnet = next(plugin for release in catalog["releases"] for plugin in release["plugins"] if plugin["id"] == "dotagents/dotnet")
        dotnet["digest"] = "sha256:" + "0" * 64
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        before = self.files()
        with self.assertRaisesRegex(bootstrap.BootstrapError, "package cannot change"):
            self.invoke(["azure-agents/azure"])
        self.assertEqual(before, self.files())

    def test_changed_snapshot_and_write_failure_do_not_leave_partial_outputs(self):
        self.invoke(["dotagents/dotnet"])
        revised = copy.deepcopy(self.document)
        revised["sources"][1]["commit"] = self.git(self.dotnet, "rev-parse", "HEAD")
        self.dotnet.joinpath("plugins/dotnet/skills/new/SKILL.md").parent.mkdir(parents=True)
        self.dotnet.joinpath("plugins/dotnet/skills/new/SKILL.md").write_text("---\nname: new\n---\n", encoding="utf-8")
        self.git(self.dotnet, "add", ".")
        self.git(self.dotnet, "commit", "-qm", "Changed")
        revised["sources"][1]["commit"] = self.git(self.dotnet, "rev-parse", "HEAD")
        self.input.write_text(json.dumps(revised), encoding="utf-8")
        before = self.files()
        with self.assertRaisesRegex(bootstrap.BootstrapError, "snapshot cannot change"):
            self.invoke(["azure-agents/azure"])
        self.assertEqual(before, self.files())
        empty = self.base / "empty"
        original = Path.write_text

        def blocked(path, value, *args, **kwargs):
            if path.name == "settings.json":
                raise PermissionError("blocked")
            return original(path, value, *args, **kwargs)

        self.save_input()
        with mock.patch.object(type(empty), "write_text", autospec=True, side_effect=blocked):
            with self.assertRaises(PermissionError):
                self.invoke(["dotagents/dotnet"], root=empty)
        self.assertFalse((empty / ".agents/capabilities.lock.json").exists())
        self.assertFalse((empty / ".agents/catalog/catalog.json").exists())
        self.assertFalse((empty / ".codex/config.toml").exists())


if __name__ == "__main__":
    unittest.main()
