import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


SOURCES = Path(__file__).resolve().parents[1] / ".agents" / "workflows" / "skill_sources.py"


def load_sources():
    spec = importlib.util.spec_from_file_location("skill_sources", SOURCES)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sources = load_sources()


class SkillSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "consumer café"
        self.root.mkdir()

    def package(self, host, marketplace="example", name="engineering", version="1.0"):
        if host == "codex":
            package = Path(os.environ["CODEX_HOME"]) / "plugins" / "cache" / marketplace / name / version
        else:
            package = self.root.parent / f"{host}-{marketplace}-{name}"
        package.mkdir(parents=True)
        manifest = package / f".{host}-plugin"
        manifest.mkdir()
        tree = "codex-skills" if host == "codex" else "skills"
        (manifest / "plugin.json").write_text(
            json.dumps({"name": name, "version": version, "skills": f"./{tree}/"}), encoding="utf-8"
        )
        entry = package / tree / "review" / "SKILL.md"
        body = package / ".agents" / "engineering" / "workflow" / "review" / "SKILL.md"
        entry.parent.mkdir(parents=True)
        body.parent.mkdir(parents=True)
        body.write_bytes(b"---\nname: review\n---\nraw\r\nbytes\n")
        entry.write_text(
            "Read [canonical shared definition](../../.agents/engineering/workflow/review/SKILL.md) in full.\n",
            encoding="utf-8",
        )
        return package

    def test_declared_host_entry_resolves_to_contained_canonical_raw_bytes(self):
        old = os.environ.get("CODEX_HOME")
        home = self.root.parent / "codex home"
        os.environ["CODEX_HOME"] = str(home)
        self.addCleanup(lambda: os.environ.__setitem__("CODEX_HOME", old) if old else os.environ.pop("CODEX_HOME", None))
        package = self.package("codex")
        record = sources.resolve_installed_skill(
            "engineering", "review", "codex", self.root,
            [{"enabled": True, "name": "engineering", "marketplaceName": "example", "version": "1.0"}],
        )
        self.assertEqual(".agents/engineering/workflow/review/SKILL.md", record["body_path"])
        self.assertEqual("codex-skills/review/SKILL.md", record["entry_path"])
        self.assertNotEqual(record["entry_sha256"], record["body_sha256"])
        self.assertEqual(str(package.resolve()), record["package_root"])

    def test_relocation_does_not_change_installed_identity(self):
        first = {"kind": "technical", "name": "engineering:review", "resolved_name": "engineering:review", "source_type": "installed_plugin", "host": "claude", "plugin_id": "engineering@example", "marketplace": "example", "native_version": "1", "native_scope": "user", "project_path": str(self.root), "advertised_source": None, "declaration_method": "manifest", "manifest_path": ".claude-plugin/plugin.json", "manifest_sha256": "a", "entry_path": "skills/review/SKILL.md", "entry_sha256": "b", "body_path": ".agents/engineering/workflow/review/SKILL.md", "body_sha256": "c", "resolved_path": "C:/old", "package_root": "C:/old"}
        moved = dict(first, resolved_path="D:/new", package_root="D:/new")
        self.assertEqual(sources.identity_key(first), sources.identity_key(moved))

    def test_claude_install_path_uses_its_declared_skills_root(self):
        package = self.package("claude")
        record = sources.resolve_skill(
            "engineering:review", self.root, self.root, "claude",
            [{"enabled": True, "id": "engineering@example", "installPath": str(package), "scope": "project", "projectPath": str(self.root)}],
        )
        self.assertEqual("engineering@example", record["plugin_id"])
        self.assertEqual("skills/review/SKILL.md", record["entry_path"])
        self.assertEqual(".agents/engineering/workflow/review/SKILL.md", record["body_path"])
        self.assertEqual("1.0", record["manifest_version"])

    def test_missing_manifest_uses_contained_default_skills_directory(self):
        package = self.package("claude")
        shutil.rmtree(package / ".claude-plugin")
        record = sources.resolve_installed_skill(
            "engineering", "review", "claude", self.root,
            [{"enabled": True, "id": "engineering@example", "installPath": str(package)}],
        )
        self.assertEqual("native-default", record["declaration_method"])
        self.assertEqual("skills/review/SKILL.md", record["entry_path"])

    def test_bare_name_uses_one_enabled_declared_installed_skill(self):
        package = self.package("claude")
        record = sources.resolve_skill(
            "review", self.root, self.root, "claude",
            [{"enabled": True, "id": "engineering@example", "installPath": str(package), "revision": "advertised"}],
        )
        self.assertEqual("review", record["name"])
        self.assertEqual("engineering:review", record["resolved_name"])
        self.assertEqual("advertised", record["native_revision"])

    def test_explicit_local_escape_is_rejected(self):
        with self.assertRaisesRegex(sources.SkillSourceError, "repository-local path"):
            sources.resolve_skill("review=../outside/SKILL.md", self.root, self.root)

    def test_disabled_and_ambiguous_native_records_do_not_resolve(self):
        with self.assertRaisesRegex(sources.SkillSourceError, "disabled"):
            sources.resolve_installed_skill("engineering", "review", "claude", self.root, [{"enabled": False, "id": "engineering@example"}])
        package = self.package("claude")
        inventory = [
            {"enabled": True, "id": "engineering@example", "installPath": str(package), "scope": "user"},
            {"enabled": True, "id": "engineering@other", "installPath": str(package), "scope": "user"},
        ]
        with self.assertRaisesRegex(sources.SkillSourceError, "ambiguous"):
            sources.resolve_installed_skill("engineering", "review", "claude", self.root, inventory)

    def test_codex_installed_false_is_not_an_enabled_installation(self):
        old = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(self.root.parent / "home")
        self.addCleanup(lambda: os.environ.__setitem__("CODEX_HOME", old) if old else os.environ.pop("CODEX_HOME", None))
        self.package("codex")
        with self.assertRaisesRegex(sources.SkillSourceError, "disabled"):
            sources.resolve_installed_skill(
                "engineering", "review", "codex", self.root,
                [{"enabled": True, "installed": False, "name": "engineering", "marketplaceName": "example", "version": "1.0"}],
            )

    def test_project_scope_does_not_hide_another_marketplace_owner(self):
        first = self.package("claude", "first")
        second = self.package("claude", "second")
        inventory = [
            {"enabled": True, "id": "engineering@first", "installPath": str(first), "scope": "project", "projectPath": str(self.root)},
            {"enabled": True, "id": "engineering@second", "installPath": str(second), "scope": "user"},
        ]
        with self.assertRaisesRegex(sources.SkillSourceError, "across marketplaces"):
            sources.resolve_installed_skill("engineering", "review", "claude", self.root, inventory)

    def test_disabled_marketplace_does_not_shadow_an_enabled_owner(self):
        package = self.package("claude", "enabled")
        record = sources.resolve_installed_skill(
            "engineering", "review", "claude", self.root,
            [
                {"enabled": True, "id": "engineering@enabled", "installPath": str(package)},
                {"enabled": False, "id": "engineering@disabled", "installPath": str(package)},
            ],
        )
        self.assertEqual("engineering@enabled", record["plugin_id"])

    def test_disabled_marketplace_does_not_shadow_an_enabled_owner(self):
        package = self.package("claude", "enabled")
        record = sources.resolve_installed_skill(
            "engineering", "review", "claude", self.root,
            [
                {"enabled": True, "id": "engineering@enabled", "installPath": str(package)},
                {"enabled": False, "id": "engineering@disabled", "installPath": str(package)},
            ],
        )
        self.assertEqual("engineering@enabled", record["plugin_id"])

    def test_canonical_target_symlink_inside_the_package_is_rejected(self):
        package = self.package("claude")
        body = package / ".agents" / "engineering" / "workflow" / "review" / "SKILL.md"
        target = body.with_name("target.md")
        target.write_text("body\n", encoding="utf-8")
        body.unlink()
        try:
            body.symlink_to(target)
        except OSError:
            self.skipTest("symlink creation is unavailable")
        with self.assertRaisesRegex(sources.SkillSourceError, "redirected"):
            sources.resolve_installed_skill(
                "engineering", "review", "claude", self.root,
                [{"enabled": True, "id": "engineering@example", "installPath": str(package)}],
            )

    def test_declared_local_scope_root_finds_a_unique_canonical_body(self):
        path = self.root / ".agents" / "engineering" / "workflow" / "review" / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text("---\nname: review\n---\n", encoding="utf-8")
        declaration = self.root / ".agents" / "plugins"
        declaration.mkdir()
        (declaration / "sources.json").write_text(
            json.dumps({"scopes": [{"root": ".agents/engineering"}]}), encoding="utf-8"
        )
        record = sources.resolve_skill("review", self.root, self.root)
        self.assertEqual(".agents/engineering/workflow/review/SKILL.md", record["path"])


if __name__ == "__main__":
    unittest.main()
