import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("runtime_sources", Path(__file__).resolve().parents[1] / "scripts/runtime_sources.py")
SOURCES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCES)


class RuntimeSourcesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="runtime sources ü ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "consumer"
        self.source = Path(temporary.name) / "publisher"
        (self.root / ".agents/plugins").mkdir(parents=True)
        (self.source / ".agents/agent/runtime").mkdir(parents=True)
        (self.source / ".agents/agent/runtime/helper.py").write_text("VALUE = 42\n", encoding="utf-8")
        self.declaration = {"schema_version": 1, "sources": {"agent": {
            "repository": "tj-agents/agent", "exports": [".agents/agent/runtime"]}}}
        self.save()

    def save(self):
        (self.root / ".agents/plugins/runtime-sources.json").write_text(json.dumps(self.declaration), encoding="utf-8")

    def stage(self):
        return SOURCES.stage(self.root, {"agent": self.source})

    def test_local_export_is_self_contained_and_verified_without_publisher(self):
        self.stage()
        self.source.rename(self.source.with_name("publisher removed"))
        self.assertEqual("verified", SOURCES.stage(self.root, {}, check=True)[0]["status"])
        target = self.root / ".agents/dependencies/agent/.agents/agent/runtime/helper.py"
        self.assertEqual("VALUE = 42\n", target.read_text(encoding="utf-8"))

    def test_changed_or_missing_staged_file_fails_verification(self):
        self.stage()
        target = self.root / ".agents/dependencies/agent/.agents/agent/runtime/helper.py"
        target.write_text("wrong", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "modified"):
            SOURCES.stage(self.root, {}, check=True)
        target.unlink()
        with self.assertRaises(ValueError):
            SOURCES.stage(self.root, {}, check=True)

    def test_existing_input_is_reused_and_checked_without_network(self):
        self.stage()
        self.assertEqual("verified", SOURCES.ensure(self.root)[0]["status"])

    def test_repository_without_external_sources_needs_no_setup(self):
        (self.root / ".agents/plugins/runtime-sources.json").unlink()
        self.assertEqual([], SOURCES.ensure(self.root))

    def test_restage_removes_obsolete_exported_files(self):
        self.stage()
        original = self.source / ".agents/agent/runtime/helper.py"
        original.rename(original.with_name("replacement.py"))
        self.stage()
        target = self.root / ".agents/dependencies/agent/.agents/agent/runtime"
        self.assertFalse((target / "helper.py").exists())
        self.assertTrue((target / "replacement.py").exists())

    def test_restage_accepts_file_replaced_by_directory_and_back(self):
        module = self.source / ".agents/agent/runtime/module"
        module.write_text("old file", encoding="utf-8")
        self.stage()
        module.unlink()
        module.mkdir()
        nested = module / "helper.py"
        nested.write_text("nested file", encoding="utf-8")
        self.stage()
        staged = self.root / ".agents/dependencies/agent/.agents/agent/runtime/module"
        self.assertEqual("nested file", (staged / "helper.py").read_text(encoding="utf-8"))
        nested.unlink()
        module.rmdir()
        module.write_text("new file", encoding="utf-8")
        self.stage()
        self.assertEqual("new file", staged.read_text(encoding="utf-8"))
        self.assertEqual("verified", SOURCES.stage(self.root, {}, check=True)[0]["status"])

    def test_rejects_undeclared_local_override(self):
        with self.assertRaisesRegex(ValueError, "Undeclared"):
            SOURCES.stage(self.root, {"other": self.source})

    def test_rejects_escaped_and_missing_export(self):
        for export in ("../outside", ".agents/../outside", ".agents/missing"):
            with self.subTest(export=export):
                self.declaration["sources"]["agent"]["exports"] = [export]
                self.save()
                with self.assertRaises(ValueError):
                    self.stage()

    def test_rejects_unapproved_remote(self):
        self.declaration["sources"]["agent"]["repository"] = "unknown/publisher"
        self.save()
        with self.assertRaisesRegex(ValueError, "Unapproved"):
            self.stage()

    def test_rejects_source_links(self):
        link = self.source / ".agents/agent/runtime/link.py"
        try:
            link.symlink_to(link.with_name("helper.py"))
        except OSError:
            self.skipTest("Creating symbolic links requires platform privileges")
        with self.assertRaisesRegex(ValueError, "link"):
            self.stage()


if __name__ == "__main__":
    unittest.main()
