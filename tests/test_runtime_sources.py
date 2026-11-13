import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


SPEC = importlib.util.spec_from_file_location("runtime_sources", Path(__file__).resolve().parents[1] / "scripts/runtime_sources.py")
SOURCES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCES)


class RuntimeSourcesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="runtime sources ü ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "consumer"
        self.source = Path(temporary.name) / "publisher"
        self.package = self.source / "plugins/agent"
        (self.root / ".agents/plugins").mkdir(parents=True)
        (self.package / ".agents/agent/runtime").mkdir(parents=True)
        (self.package / ".agents/agent/runtime/helper.py").write_text("VALUE = 42\n", encoding="utf-8")
        self.declaration = {
            "schema_version": 1,
            "sources": {
                "agent": {
                    "repository": "tj-agents/agent",
                    "revision": "a" * 40,
                    "package": "plugins/agent",
                    "exports": [".agents/agent/runtime"],
                }
            },
        }
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
        original = self.package / ".agents/agent/runtime/helper.py"
        original.rename(original.with_name("replacement.py"))
        self.stage()
        target = self.root / ".agents/dependencies/agent/.agents/agent/runtime"
        self.assertFalse((target / "helper.py").exists())
        self.assertTrue((target / "replacement.py").exists())

    def test_restage_accepts_file_replaced_by_directory_and_back(self):
        module = self.package / ".agents/agent/runtime/module"
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
        link = self.package / ".agents/agent/runtime/link.py"
        try:
            link.symlink_to(link.with_name("helper.py"))
        except OSError:
            self.skipTest("Creating symbolic links requires platform privileges")
        with self.assertRaisesRegex(ValueError, "link"):
            self.stage()

    def test_rejects_missing_or_malformed_revision(self):
        for revision in (None, "", "g" * 40, "A" * 40, "deadbeef", 1234567890):
            with self.subTest(revision=revision):
                if revision is None:
                    del self.declaration["sources"]["agent"]["revision"]
                else:
                    self.declaration["sources"]["agent"]["revision"] = revision
                self.save()
                with self.assertRaises(ValueError):
                    self.stage()

    def fake_remote_git(self, revision):
        def fake_git(*arguments):
            if arguments[0] == "init":
                checkout = Path(arguments[-1])
                target = checkout / "plugins/agent/.agents/agent/runtime"
                target.mkdir(parents=True)
                (target / "helper.py").write_text("VALUE = 42\n", encoding="utf-8")
                return ""
            if arguments[0] == "-C" and arguments[2] == "rev-parse":
                return revision
            return ""

        return fake_git

    def test_staging_fetches_exactly_the_declared_revision(self):
        revision = "b" * 40
        self.declaration["sources"]["agent"]["revision"] = revision
        self.save()
        calls = []
        fake_git = self.fake_remote_git(revision)

        def recording_git(*arguments):
            calls.append(arguments)
            return fake_git(*arguments)

        with mock.patch.object(SOURCES, "git", side_effect=recording_git):
            result = SOURCES.stage(self.root, {})
        self.assertEqual("staged", result[0]["status"])
        self.assertEqual(revision, result[0]["revision"])
        fetch_call = next(
            call for call in calls if call[0] == "-C" and call[2] == "fetch"
        )
        self.assertIn("https://github.com/tj-agents/agent.git", fetch_call)
        self.assertIn(revision, fetch_call)

    def test_check_fails_when_declared_revision_is_bumped(self):
        revision = "c" * 40
        self.declaration["sources"]["agent"]["revision"] = revision
        self.save()
        fake_git = self.fake_remote_git(revision)
        with mock.patch.object(SOURCES, "git", side_effect=fake_git):
            SOURCES.stage(self.root, {})
        self.declaration["sources"]["agent"]["revision"] = "d" * 40
        self.save()
        with self.assertRaisesRegex(ValueError, "Stale or modified"):
            SOURCES.stage(self.root, {}, check=True)


if __name__ == "__main__":
    unittest.main()
