import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[2] / "machine" / "utility" / "plugin-lock" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bump_plugin_lock = load("bump_plugin_lock")
repo_config = bump_plugin_lock.repo_config


class BumpPluginLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.roots = []
        for name in ("one", "two"):
            root = Path(self.temp.name).resolve() / name
            (root / ".agents").mkdir(parents=True)
            self.roots.append(root)
            self.save(root, "v1.0.0")
            repo_config.run(root / ".agents" / "plugins.lock.json", "write", root=root)

    def save(self, root, revision, plugins=("base", "engineering", "machine", "react")):
        document = {"schema_version": 3, "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace", "revision": revision}}, "plugins": [f"{name}@tj-agents" for name in plugins]}
        (root / ".agents" / "plugins.lock.json").write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def revision(self, root):
        lock = json.loads((root / ".agents" / "plugins.lock.json").read_text(encoding="utf-8"))
        claude = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
        return lock["marketplaces"]["tj-agents"]["revision"], claude["extraKnownMarketplaces"]["tj-agents"]["source"]["ref"]

    def run_main(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            status = bump_plugin_lock.main(list(arguments))
        return status, output.getvalue(), errors.getvalue()

    def test_preview_changes_nothing_and_names_the_files(self):
        status, output, _ = self.run_main("--revision", "v1.1.0", "--root", str(self.roots[0]))
        self.assertEqual(0, status)
        self.assertIn("would move tj-agents v1.0.0 -> v1.1.0", output)
        self.assertIn(".claude/settings.json", output)
        self.assertEqual(("v1.0.0", "v1.0.0"), self.revision(self.roots[0]))

    def test_write_moves_every_root_lock_and_both_hosts(self):
        arguments = ["--revision", "v1.1.0", "--mode", "write"]
        for root in self.roots:
            arguments += ["--root", str(root)]
        status, _, _ = self.run_main(*arguments)
        self.assertEqual(0, status)
        for root in self.roots:
            self.assertEqual(("v1.1.0", "v1.1.0"), self.revision(root))
            self.assertIn('ref = "v1.1.0"', (root / ".codex" / "config.toml").read_text(encoding="utf-8"))
            self.assertEqual([], repo_config.run(root / ".agents" / "plugins.lock.json", "check", root=root))

    def test_invalid_revision_fails_without_touching_the_root(self):
        status, _, errors = self.run_main("--revision", "main", "--mode", "write", "--root", str(self.roots[0]))
        self.assertEqual(1, status)
        self.assertIn("marketplaces.tj-agents.revision", errors)
        self.assertEqual(("v1.0.0", "v1.0.0"), self.revision(self.roots[0]))

    def test_one_failing_root_does_not_stop_the_others(self):
        (self.roots[0] / ".agents" / "plugins.lock.json").write_text("{}", encoding="utf-8")
        status, output, errors = self.run_main("--revision", "v1.1.0", "--mode", "write", "--root", str(self.roots[0]), "--root", str(self.roots[1]))
        self.assertEqual(1, status)
        self.assertIn("moved tj-agents v1.0.0 -> v1.1.0", output)
        self.assertEqual(("v1.1.0", "v1.1.0"), self.revision(self.roots[1]))
        self.assertIn(str(self.roots[0]), errors)


    def test_preview_names_the_lock_file_it_would_rewrite(self):
        status, output, _ = self.run_main("--revision", "v1.1.0", "--root", str(self.roots[0]))
        self.assertEqual(0, status)
        self.assertIn(".agents/plugins.lock.json", output)

    def test_malformed_lock_is_reported_and_other_roots_still_move(self):
        (self.roots[0] / ".agents" / "plugins.lock.json").write_text('{"schema_version": 3}', encoding="utf-8")
        status, output, errors = self.run_main("--revision", "v1.1.0", "--mode", "write", "--root", str(self.roots[0]), "--root", str(self.roots[1]))
        self.assertEqual(1, status)
        self.assertIn(str(self.roots[0]), errors)
        self.assertEqual(("v1.1.0", "v1.1.0"), self.revision(self.roots[1]))


    def test_a_local_scope_clone_is_refused_untouched(self):
        (self.roots[0] / ".agents" / "repo-capabilities.local.json").write_text("{}", encoding="utf-8")
        status, _, errors = self.run_main("--revision", "v1.1.0", "--mode", "write", "--root", str(self.roots[0]))
        self.assertEqual(1, status)
        self.assertIn("adopted with --scope local", errors)
        self.assertEqual(("v1.0.0", "v1.0.0"), self.revision(self.roots[0]))

    def test_bumping_to_the_pinned_revision_changes_nothing(self):
        before = (self.roots[0] / ".agents" / "plugins.lock.json").read_bytes()
        status, output, _ = self.run_main("--revision", "v1.0.0", "--mode", "write", "--root", str(self.roots[0]))
        self.assertEqual(0, status)
        self.assertIn("no host settings change", output)
        self.assertEqual(before, (self.roots[0] / ".agents" / "plugins.lock.json").read_bytes())


    def test_moves_a_second_marketplace_without_touching_tj_agents(self):
        lock = self.roots[0] / ".agents" / "plugins.lock.json"
        document = json.loads(lock.read_text(encoding="utf-8"))
        document["marketplaces"]["agents"] = {"repository": "Concertable/agents", "revision": "cccccccccccccccccccccccccccccccccccccccc"}
        document["plugins"].append("concertable@agents")
        lock.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        status, _, errors = self.run_main("--marketplace", "agents", "--revision", "dddddddddddddddddddddddddddddddddddddddd", "--mode", "write", "--root", str(self.roots[0]))
        self.assertEqual(0, status, errors)
        document = json.loads(lock.read_text(encoding="utf-8"))
        self.assertEqual("dddddddddddddddddddddddddddddddddddddddd", document["marketplaces"]["agents"]["revision"])
        self.assertEqual("v1.0.0", document["marketplaces"]["tj-agents"]["revision"])
        status, _, errors = self.run_main("--marketplace", "missing", "--revision", "v1.0.0", "--root", str(self.roots[1]))
        self.assertEqual(1, status)
        self.assertIn("does not use the missing marketplace", errors)


if __name__ == "__main__":
    unittest.main()
