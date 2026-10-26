import hashlib
import importlib.util
import json
import os
import sys
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/engineering/utility/review/scripts/review_rules.py"
SPEC = importlib.util.spec_from_file_location("review_rules", SCRIPT)
RULES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RULES)


class ReviewRulesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="review standards \u00e9 ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "application"
        (self.project / ".agents").mkdir(parents=True)
        self.gate = RULES.tier_gate()

    def selection(self, *identities):
        (self.project / ".agents/plugins.json").write_text(json.dumps({
            "schema_version": 1,
            "marketplaces": {identity.partition("@")[2]: {"repository": "example/marketplace"}
                             for identity in identities},
            "plugins": list(identities),
        }), encoding="utf-8")

    def plugin(self, name, *, marketplace="selected", data=None, kind="convention", canonical=False):
        payload = self.root / "cache" / marketplace / name / "version"
        skill = payload / "skills/style/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text(f"---\nname: style\nkind: {kind}\n---\n{name} rules\n", encoding="utf-8")
        if canonical:
            source = payload / ".agents" / name / "convention/style/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("---\nname: style\nkind: convention\n---\nCanonical rule body\n", encoding="utf-8")
        declaration = data or {"schema_version": 1, "tier": name, "applies": "always"}
        return self.gate.Declaration(name, marketplace, declaration, payload)

    def test_no_route_table_still_loads_only_selected_applicable_conventions(self):
        self.selection("backend@selected", "frontend@selected", "tools@selected")
        declarations = [
            self.plugin("backend", canonical=True),
            self.plugin("frontend", data={"schema_version": 1, "tier": "frontend",
                                         "applies": "stack-present", "detect": {"files": ["package.json"]}}),
            self.plugin("tools", kind="utility"),
            self.plugin("unrelated"),
            self.plugin("backend", marketplace="other"),
        ]

        result = RULES.resolve(self.project, self.gate, declarations)

        self.assertFalse((self.project / ".agents/skill-routes.json").exists())
        self.assertEqual(["backend:style"], [rule["name"] for rule in result["rules"]])
        source = Path(result["rules"][0]["path"])
        self.assertIn(".agents", source.parts)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), result["rules"][0]["sha256"])
        self.assertEqual(["backend@selected", "frontend@selected", "tools@selected"],
                         result["selection"]["plugins"])

    def test_selected_company_replaces_the_whole_generic_skill(self):
        self.selection("stack@selected", "company@selected", "company-stack@selected")
        (self.project / "company.marker").write_text("company\n", encoding="utf-8")
        employer = self.plugin("company", data={
            "schema_version": 3, "tier": "company", "applies": "stack-present",
            "detect": {"file": "company.marker"}, "employer": {"context_skill": "context"},
        }, kind="knowledge")
        context = employer.payload_dir / "skills/context/SKILL.md"
        context.parent.mkdir()
        context.write_text("---\nname: context\nkind: knowledge\n---\nCompany context\n", encoding="utf-8")
        result = RULES.resolve(self.project, self.gate, [self.plugin("stack"), employer,
                                                       self.plugin("company-stack")])
        self.assertEqual(["company-stack:style"], [rule["name"] for rule in result["rules"]])

    def test_unselected_company_cannot_replace_a_selected_standard(self):
        self.selection("stack@selected")
        result = RULES.resolve(self.project, self.gate, [self.plugin("stack"), self.plugin("company-stack")])
        self.assertEqual(["stack:style"], [rule["name"] for rule in result["rules"]])

    def test_contract_kind_remains_a_review_convention_during_migration(self):
        self.selection("legacy@selected")
        result = RULES.resolve(self.project, self.gate, [self.plugin("legacy", kind="contract")])
        self.assertEqual(["legacy:style"], [rule["name"] for rule in result["rules"]])

    def test_selected_marketplaces_cannot_shadow_each_other(self):
        self.selection("stack@selected", "stack@other")
        with self.assertRaisesRegex(ValueError, "conflicting plugin namespaces"):
            RULES.resolve(self.project, self.gate, [self.plugin("stack"),
                                                   self.plugin("stack", marketplace="other")])

    def test_host_inventory_uses_only_the_enabled_native_version(self):
        self.selection("stack@selected")
        active = self.plugin("stack")
        (active.payload_dir / "tier.json").write_text(json.dumps(active.data), encoding="utf-8")
        profile = self.root / "profile"
        cache = profile / "plugins/cache"
        cache.parent.mkdir(parents=True)
        self.root.joinpath("cache").rename(cache)
        unrelated = cache / "selected/unrelated/version/tier.json"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("invalid unrelated declaration", encoding="utf-8")
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(profile)}), mock.patch.object(
                self.gate, "native_plugins", return_value=[
                    {"marketplaceName": "selected", "name": "stack", "version": "version"},
                    {"marketplaceName": "selected", "name": "unrelated", "version": "version"},
                ]) as inventory:
            result = RULES.resolve(self.project, self.gate, host="codex")
        inventory.assert_called_once_with("codex", str(self.project.resolve()))
        self.assertEqual(["stack:style"], [rule["name"] for rule in result["rules"]])
        self.assertTrue(Path(result["rules"][0]["path"]).is_relative_to(cache.resolve()))

    def test_claude_inventory_uses_only_the_installation_that_applies_to_the_reviewed_repository(self):
        self.selection("stack@selected")
        profile = self.root / "profile"
        cache = profile / "plugins/cache"
        installs = {}
        for version in ("user", "elsewhere", "here"):
            payload = cache / "selected/stack" / version
            (payload / "skills/style").mkdir(parents=True)
            (payload / "skills/style/SKILL.md").write_text(
                f"---\nname: style\nkind: convention\n---\n{version}\n", encoding="utf-8")
            (payload / "tier.json").write_text(json.dumps({"schema_version": 1, "tier": "stack", "applies": "always"}),
                                               encoding="utf-8")
            installs[version] = str(payload)
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(profile)}), mock.patch.object(
                self.gate, "native_plugins", return_value=[
                    {"id": "stack@selected", "scope": "user", "installPath": installs["user"]},
                    {"id": "stack@selected", "scope": "project", "projectPath": str(self.root / "other"),
                     "installPath": installs["elsewhere"]},
                    {"id": "stack@selected", "scope": "project", "projectPath": str(self.project),
                     "installPath": installs["here"]},
                ]):
            result = RULES.resolve(self.project, self.gate, host="claude")
        self.assertEqual([Path(installs["here"]).resolve()],
                         [Path(rule["path"]).parents[2] for rule in result["rules"]])

    def test_native_inventory_executes_in_the_reviewed_repository(self):
        script = self.project / "plugin"
        script.write_text(
            'import json, os\nprint(json.dumps({"installed": [{"enabled": True, "name": os.getcwd()}]}))\n',
            encoding="utf-8",
        )
        self.gate.native_plugins.cache_clear()
        self.addCleanup(self.gate.native_plugins.cache_clear)
        with mock.patch.object(self.gate.shutil, "which", return_value=sys.executable):
            entries = self.gate.native_plugins("codex", str(self.project))
        self.assertEqual(self.project.resolve(), Path(entries[0]["name"]).resolve())

    def test_relative_host_executable_is_frozen_before_the_directory_change(self):
        binary = str(Path("relative-bin") / "codex")
        self.gate.native_plugins.cache_clear()
        self.addCleanup(self.gate.native_plugins.cache_clear)
        completed = subprocess.CompletedProcess([], 0, '{"installed": [{"enabled": true}]}', '')
        with mock.patch.object(self.gate.shutil, "which", return_value=binary), mock.patch.object(
                self.gate.subprocess, "run", return_value=completed) as launch:
            self.gate.native_plugins("codex", str(self.project))
        self.assertEqual(str((Path.cwd() / binary).resolve()), launch.call_args.args[0][0])
        self.assertEqual(str(self.project), launch.call_args.kwargs["cwd"])

    def test_missing_native_inventory_never_falls_back_to_another_host(self):
        self.selection("stack@selected")
        with mock.patch.object(self.gate, "native_plugins", return_value=()), mock.patch.object(
                self.gate, "declarations", side_effect=AssertionError("unexpected cross-host discovery")):
            with self.assertRaisesRegex(ValueError, "inventory is unavailable"):
                RULES.resolve(self.project, self.gate, host="codex")

    def test_missing_selected_package_is_visible(self):
        self.selection("missing@selected")
        with self.assertRaisesRegex(ValueError, "missing@selected"):
            RULES.resolve(self.project, self.gate, [self.plugin("unrelated")])

    def test_no_selection_does_not_scan_installed_caches(self):
        with mock.patch.object(self.gate, "declarations", side_effect=AssertionError("unexpected cache scan")):
            result = RULES.resolve(self.project, self.gate)
        self.assertIsNone(result["selection"])
        self.assertEqual([], result["rules"])
        self.assertTrue(result["diagnostics"])

    def test_malformed_selection_is_rejected(self):
        path = self.project / ".agents/plugins.json"
        for document in ([], {}, {"schema_version": 1, "plugins": ["invalid"], "marketplaces": {}}):
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.subTest(document=document), self.assertRaisesRegex(ValueError, "Invalid repository"):
                RULES.resolve(self.project, self.gate, [])


if __name__ == "__main__":
    unittest.main()
