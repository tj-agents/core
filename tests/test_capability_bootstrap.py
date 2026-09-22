"""Behavioral tests for catalog validation and exact-profile bootstrap."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/machine/bootstrap-capabilities/scripts/bootstrap_capabilities.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_capabilities", SCRIPT)
BOOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOOT)


class CatalogTests(unittest.TestCase):
    def catalog(self):
        return json.loads((ROOT / ".agents/catalog/catalog.json").read_text(encoding="utf-8"))

    def test_catalog_has_unique_closed_acyclic_plugins(self):
        releases, plugins = BOOT.catalog_index(self.catalog())
        self.assertEqual(4, len(releases))
        self.assertEqual(14, len(plugins))
        self.assertEqual(
            ["base-agents/base"],
            plugins["base-agents/engineering"]["dependencies"]["required"],
        )
        self.assertEqual("deprecated", plugins["cpp-agents/windows"]["status"])
        self.assertEqual("2027-03-31", plugins["cpp-agents/windows"]["remove_after"])

    def test_lock_requires_dependency_closure_and_known_skills(self):
        releases, plugins = BOOT.catalog_index(self.catalog())
        incomplete = {
            "schema_version": 1,
            "plugins": [
                {
                    "id": "base-agents/engineering",
                    "release": "base-agents@2.1.4",
                    "commit": "a" * 40,
                    "required_skills": ["review"],
                    "path_scopes": [],
                    "exceptions": [],
                }
            ],
        }
        with self.assertRaisesRegex(BOOT.BootstrapError, "missing required plugin"):
            BOOT.validate_lock(incomplete, releases, plugins)
        incomplete["plugins"][0]["required_skills"] = ["not-a-real-skill"]
        with self.assertRaisesRegex(BOOT.BootstrapError, "unknown skills"):
            BOOT.validate_lock(incomplete, releases, plugins)

    def test_missing_required_executable_fails_preview_clearly(self):
        catalog = self.catalog()
        catalog["releases"][0]["plugins"][0]["external_prerequisites"]["required"] = [
            "exe:definitely-not-a-real-agent-tool"
        ]
        releases, plugins = BOOT.catalog_index(catalog)
        lock = {
            "schema_version": 1,
            "plugins": [
                {
                    "id": "base-agents/base",
                    "release": "base-agents@2.1.4",
                    "commit": "a" * 40,
                    "required_skills": [],
                    "path_scopes": [],
                    "exceptions": [],
                }
            ],
        }
        selections = BOOT.validate_lock(lock, releases, plugins)
        with self.assertRaisesRegex(BOOT.BootstrapError, "requires executable"):
            BOOT.check_required_prerequisites(selections, plugins)

    def test_malformed_catalog_fails_with_a_bootstrap_error(self):
        catalog = self.catalog()
        del catalog["releases"][0]["plugins"][0]["external_prerequisites"]
        with self.assertRaisesRegex(BOOT.BootstrapError, "external_prerequisites"):
            BOOT.catalog_index(catalog)

    def test_cycle_is_rejected(self):
        catalog = self.catalog()
        catalog["releases"][0]["plugins"][0]["dependencies"]["required"] = [
            "base-agents/engineering"
        ]
        with self.assertRaisesRegex(BOOT.BootstrapError, "cycle"):
            BOOT.catalog_index(catalog)

    def test_tree_digest_is_stable_and_honors_narrow_exclusion(self):
        with tempfile.TemporaryDirectory(prefix="capability digest ") as raw:
            root = Path(raw)
            (root / "nested").mkdir()
            (root / "z.txt").write_bytes(b"z")
            (root / "nested/a.txt").write_bytes(b"a")
            first = BOOT.tree_digest(root, [])
            (root / "catalog.json").write_bytes(b"first")
            excluded = BOOT.tree_digest(root, ["catalog.json"])
            included = BOOT.tree_digest(root, [])
            (root / "catalog.json").write_bytes(b"second")
            self.assertEqual(first, excluded)
            self.assertEqual(excluded, BOOT.tree_digest(root, ["catalog.json"]))
            self.assertNotEqual(included, BOOT.tree_digest(root, []))


class BootstrapIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="capability bootstrap path with spaces ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source marketplace"
        self.profile = self.root / "isolated profile"
        self.project = self.root / "project"
        self.project.mkdir()
        package = self.source / "plugins/example"
        package.mkdir(parents=True)
        (package / "payload.txt").write_text("payload\n", encoding="utf-8")
        (self.source / ".agents/plugins").mkdir(parents=True)
        (self.source / ".agents/plugins/marketplace.json").write_text("{}\n", encoding="utf-8")
        self.git("init", "-b", "main", cwd=self.source)
        self.git("config", "user.name", "Capability Test", cwd=self.source)
        self.git("config", "user.email", "capability@example.invalid", cwd=self.source)
        self.git("config", "core.autocrlf", "false", cwd=self.source)
        self.git("add", ".", cwd=self.source)
        self.git("commit", "-m", "fixture", cwd=self.source)
        self.parent_commit = self.git("rev-parse", "HEAD", cwd=self.source).strip()
        (self.source / "release.txt").write_text("release\n", encoding="utf-8")
        self.git("add", "release.txt", cwd=self.source)
        self.git("commit", "-m", "release", cwd=self.source)
        self.git("tag", "v1.0.0", cwd=self.source)
        self.commit = self.git("rev-parse", "HEAD", cwd=self.source).strip()
        digest = BOOT.tree_digest(package, [])
        self.catalog_path = self.root / "catalog.json"
        self.catalog_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "digest_format": "sha256-tree-v1",
                    "releases": [
                        {
                            "id": "fixture@1.0.0",
                            "owner_repository": "fixture/fixture",
                            "source": str(self.source),
                            "marketplace": "fixture",
                            "revision": "v1.0.0",
                            "version": "1.0.0",
                            "plugins": [
                                {
                                    "id": "fixture/example",
                                    "name": "example",
                                    "package_path": "plugins/example",
                                    "version": "1.0.0",
                                    "description": "Fixture plugin.",
                                    "status": "current",
                                    "platforms": ["windows", "linux", "macos"],
                                    "skills": ["example-skill"],
                                    "dependencies": {"required": [], "optional": []},
                                    "external_prerequisites": {"required": [], "optional": []},
                                    "digest": digest,
                                }
                            ],
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.lock_path = self.project / ".agents/capabilities.lock.json"
        self.lock_path.parent.mkdir()
        self.lock_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "plugins": [
                        {
                            "id": "fixture/example",
                            "release": "fixture@1.0.0",
                            "commit": self.commit,
                            "required_skills": ["example-skill"],
                            "path_scopes": [{"path": "src/**", "skills": ["example-skill"]}],
                            "exceptions": ["https://example.invalid/decision/1"],
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.marketplaces = set()
        self.plugins = {}
        self.host_mutations = 0
        self.fail_install_once = False
        self.fail_plugin_list_once = False
        self.plugin_refreshes = 0
        self.marketplace_root_override = {}

    def git(self, *arguments, cwd=None):
        completed = subprocess.run(
            ["git", *arguments], cwd=cwd, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, check=False
        )
        if completed.returncode:
            self.fail(completed.stderr)
        return completed.stdout

    def arguments(self, mode, harness="codex"):
        return argparse.Namespace(
            lock=self.lock_path,
            harness=harness,
            profile=self.profile,
            mode=mode,
            catalog=self.catalog_path,
            report=None,
        )

    def cache_plugin(self, identity, claude):
        name, marketplace = identity.split("@", 1)
        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        release = next(item for item in catalog["releases"] if item["marketplace"] == marketplace)
        plugin = next(item for item in release["plugins"] if item["name"] == name)
        lock = json.loads(self.lock_path.read_text(encoding="utf-8"))
        selection = next(item for item in lock["plugins"] if item["id"] == plugin["id"])
        version = selection["commit"][:12] if claude else plugin["version"]
        source = self.profile / BOOT.STATE_DIRECTORY / "checkouts" / marketplace / plugin["package_path"]
        target = self.profile / "fake host cache" / ("claude" if claude else "codex") / marketplace / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        self.plugins[identity] = {"enabled": True, "version": version, "path": str(target)}

    def fake_run(self, command, **kwargs):
        if command[0] not in {"codex-fixture", "claude-fixture"}:
            return subprocess.run(command, **kwargs)
        claude = command[0] == "claude-fixture"
        arguments = command[1:]
        stdout = ""
        if arguments == ["plugin", "marketplace", "list", "--json"] and not claude:
            stdout = json.dumps({"marketplaces": [
                {
                    "name": value,
                    "root": self.marketplace_root_override.get(
                        value, str(self.profile / BOOT.STATE_DIRECTORY / "checkouts" / value)
                    ),
                }
                for value in sorted(self.marketplaces)
            ]})
        elif arguments == ["plugin", "marketplace", "list"] and claude:
            stdout = "".join(
                f"  ❯ {value}\n    Source: Directory ({self.profile / BOOT.STATE_DIRECTORY / 'checkouts' / value})\n"
                for value in sorted(self.marketplaces)
            )
        elif arguments == ["plugin", "list", "--json"]:
            if self.fail_plugin_list_once:
                self.fail_plugin_list_once = False
                return subprocess.CompletedProcess(command, 1, "", "injected plugin-list failure")
            records = [
                {
                    "id": identity,
                    "scope": "user",
                    "enabled": record["enabled"],
                    "version": record["version"],
                    "installPath": record["path"],
                }
                if claude else {
                    "pluginId": identity,
                    "installed": True,
                    "enabled": record["enabled"],
                    "version": record["version"],
                    "source": {"path": record["path"]},
                }
                for identity, record in sorted(self.plugins.items())
            ]
            stdout = json.dumps(records if claude else {"installed": records})
        elif arguments[:3] == ["plugin", "marketplace", "add"]:
            self.marketplaces.add(Path(arguments[3]).name)
            self.host_mutations += 1
        elif (not claude and arguments[:2] == ["plugin", "add"]) or (
            claude and arguments[:2] == ["plugin", "install"]
        ) or (
            claude and arguments[:2] == ["plugin", "update"]
        ):
            if self.fail_install_once:
                self.fail_install_once = False
                return subprocess.CompletedProcess(command, 1, "", "injected install failure")
            if arguments[:2] == ["plugin", "update"] or arguments[2] in self.plugins:
                self.plugin_refreshes += 1
            self.cache_plugin(arguments[2], claude)
            self.host_mutations += 1
        elif claude and arguments[:2] == ["plugin", "enable"]:
            self.plugins[arguments[2]]["enabled"] = True
            self.host_mutations += 1
        else:
            return subprocess.CompletedProcess(command, 1, "", "unexpected host arguments")
        return subprocess.CompletedProcess(command, 0, stdout, "")

    def test_native_processes_request_utf8_decoding(self):
        calls = []

        def run(command, **kwargs):
            calls.append((command, kwargs))
            stdout = '{"marketplaces": []}' if "codex-fixture" in command[0] else ""
            return subprocess.CompletedProcess(command, 0, stdout, "")

        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else "git-fixture",
        ):
            BOOT.NativeHost("codex", self.profile, run).marketplaces()
            BOOT.git(run, ["status"], self.root)

        self.assertEqual(2, len(calls))
        for _, kwargs in calls:
            self.assertTrue(kwargs["text"])
            self.assertEqual("utf-8", kwargs["encoding"])

    def test_preview_is_read_only_then_apply_and_offline_verify_are_idempotent(self):
        unrelated = self.profile / "unrelated.json"
        self.profile.mkdir()
        unrelated.write_bytes(b'{"preserve":true}\n')
        with mock.patch.object(BOOT, "executable", side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git")):
            preview = BOOT.execute(self.arguments("preview"), run=self.fake_run)
            self.assertEqual("planned", preview["status"])
            self.assertEqual(0, self.host_mutations)
            self.assertFalse((self.profile / BOOT.STATE_DIRECTORY).exists())

            applied = BOOT.execute(self.arguments("apply"), run=self.fake_run)
            self.assertEqual("applied", applied["status"])
            self.assertEqual(2, self.host_mutations)
            self.assertEqual(b'{"preserve":true}\n', unrelated.read_bytes())

            before = self.host_mutations
            verified = BOOT.execute(self.arguments("verify"), run=self.fake_run)
            self.assertEqual("verified", verified["status"])
            self.assertEqual(before, self.host_mutations)

            repeated = BOOT.execute(self.arguments("apply"), run=self.fake_run)
            self.assertEqual("applied", repeated["status"])
            self.assertEqual(before, self.host_mutations)

    def prepare_moved_release(self):
        moved_source = self.root / "moved source marketplace"
        self.git("clone", "--no-hardlinks", str(self.source), str(moved_source), cwd=self.root)
        self.git("config", "user.name", "Capability Test", cwd=moved_source)
        self.git("config", "user.email", "capability@example.invalid", cwd=moved_source)
        (moved_source / "second-release.txt").write_text("second release\n", encoding="utf-8")
        (moved_source / "plugins/example/payload.txt").write_text("updated payload\n", encoding="utf-8")
        self.git("add", "second-release.txt", "plugins/example/payload.txt", cwd=moved_source)
        self.git("commit", "-m", "second release", cwd=moved_source)
        self.git("tag", "v1.0.1", cwd=moved_source)
        moved_commit = self.git("rev-parse", "HEAD", cwd=moved_source).strip()

        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        release = catalog["releases"][0]
        release.update(
            {
                "id": "fixture@1.0.1",
                "source": str(moved_source),
                "revision": "v1.0.1",
                "version": "1.0.1",
            }
        )
        release["plugins"][0]["version"] = "1.0.1"
        release["plugins"][0]["digest"] = BOOT.tree_digest(moved_source / "plugins/example", [])
        self.catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

        lock = json.loads(self.lock_path.read_text(encoding="utf-8"))
        lock["plugins"][0].update({"release": "fixture@1.0.1", "commit": moved_commit})
        self.lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        return moved_source, moved_commit

    def test_apply_migrates_owned_marketplace_to_new_source_and_release(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            moved_source, moved_commit = self.prepare_moved_release()
            migrated = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
        self.assertEqual(str(moved_source), self.git("remote", "get-url", "origin", cwd=checkout).strip())
        self.assertEqual(moved_commit, self.git("rev-parse", "HEAD", cwd=checkout).strip())
        state = json.loads((self.profile / BOOT.STATE_DIRECTORY / "managed.json").read_text())
        self.assertEqual("fixture@1.0.1", state["marketplaces"]["fixture"]["release"])
        self.assertEqual(moved_commit, state["marketplaces"]["fixture"]["commit"])
        self.assertEqual({}, state["transitions"])
        self.assertEqual("1.0.1", self.plugins["example@fixture"]["version"])
        self.assertEqual(1, self.plugin_refreshes)
        self.assertIn(f"managed-state:fixture@{moved_commit}", migrated["applied"])

    def test_interrupted_release_transition_resumes_from_durable_pending_state(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            _, moved_commit = self.prepare_moved_release()
            self.fail_plugin_list_once = True
            with self.assertRaisesRegex(BOOT.BootstrapError, "injected plugin-list failure"):
                BOOT.execute(self.arguments("apply"), run=self.fake_run)

            state = json.loads((self.profile / BOOT.STATE_DIRECTORY / "managed.json").read_text())
            self.assertEqual("fixture@1.0.0", state["marketplaces"]["fixture"]["release"])
            self.assertEqual(moved_commit, state["transitions"]["fixture"]["to"]["commit"])
            resumed = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        self.assertEqual("applied", resumed["status"])
        state = json.loads((self.profile / BOOT.STATE_DIRECTORY / "managed.json").read_text())
        self.assertEqual("fixture@1.0.1", state["marketplaces"]["fixture"]["release"])
        self.assertEqual({}, state["transitions"])

    def test_stale_state_cannot_rewrite_an_unrelated_checkout_origin(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
            def remove_readonly(function, path, _error):
                os.chmod(path, 0o700)
                function(path)

            shutil.rmtree(checkout, onexc=remove_readonly)
            checkout.mkdir()
            (checkout / "unrelated.txt").write_text("unrelated\n", encoding="utf-8")
            self.git("init", "-b", "main", cwd=checkout)
            self.git("config", "user.name", "Capability Test", cwd=checkout)
            self.git("config", "user.email", "capability@example.invalid", cwd=checkout)
            self.git("add", ".", cwd=checkout)
            self.git("commit", "-m", "unrelated", cwd=checkout)
            self.git("remote", "add", "origin", "https://example.invalid/unrelated.git", cwd=checkout)

            with self.assertRaisesRegex(BOOT.BootstrapError, "recorded state requires"):
                BOOT.execute(self.arguments("apply"), run=self.fake_run)

        self.assertEqual(
            "https://example.invalid/unrelated.git",
            self.git("remote", "get-url", "origin", cwd=checkout).strip(),
        )


    def test_claude_apply_and_offline_verify_use_the_same_lock(self):
        with mock.patch.object(BOOT, "executable", side_effect=lambda name: f"{name}-fixture" if name in {"codex", "claude"} else shutil.which("git")):
            applied = BOOT.execute(self.arguments("apply", "claude"), run=self.fake_run)
            self.assertEqual("applied", applied["status"])
            before = self.host_mutations
            verified = BOOT.execute(self.arguments("verify", "claude"), run=self.fake_run)
            self.assertEqual("verified", verified["status"])
            self.assertEqual(before, self.host_mutations)

    def test_partial_apply_is_recoverable(self):
        self.fail_install_once = True
        with mock.patch.object(BOOT, "executable", side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git")):
            with self.assertRaisesRegex(BOOT.BootstrapError, "injected install failure") as caught:
                BOOT.execute(self.arguments("apply"), run=self.fake_run)
            self.assertEqual("partial", caught.exception.report["status"])
            self.assertIn("marketplace:fixture", caught.exception.report["applied"])
            state = json.loads((self.profile / BOOT.STATE_DIRECTORY / "managed.json").read_text())
            self.assertIn("fixture", state["marketplaces"])
            resumed = BOOT.execute(self.arguments("apply"), run=self.fake_run)
            self.assertEqual("applied", resumed["status"])
            self.assertTrue(self.plugins["example@fixture"])

    def test_registered_marketplace_source_drift_is_rejected(self):
        with mock.patch.object(BOOT, "executable", side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git")):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            self.marketplace_root_override["fixture"] = str(self.root / "somewhere else")
            with self.assertRaisesRegex(BOOT.BootstrapError, "source disagrees"):
                BOOT.execute(self.arguments("verify"), run=self.fake_run)

    def test_offline_verify_rejects_local_tag_drift(self):
        with mock.patch.object(BOOT, "executable", side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git")):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
            self.git("tag", "-f", "v1.0.0", self.parent_commit, cwd=checkout)
            with self.assertRaisesRegex(BOOT.BootstrapError, "local tag"):
                BOOT.execute(self.arguments("verify"), run=self.fake_run)

    def test_lock_path_scope_cannot_escape_the_project(self):
        catalog = json.loads(self.catalog_path.read_text())
        releases, plugins = BOOT.catalog_index(catalog)
        lock = json.loads(self.lock_path.read_text())
        lock["plugins"][0]["path_scopes"][0]["path"] = "../outside/**"
        with self.assertRaisesRegex(BOOT.BootstrapError, "stay inside"):
            BOOT.validate_lock(lock, releases, plugins)

    def test_existing_unmanaged_marketplace_is_preserved_and_rejected(self):
        self.marketplaces.add("fixture")
        with mock.patch.object(BOOT, "executable", side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git")):
            with self.assertRaisesRegex(BOOT.BootstrapError, "outside this bootstrap"):
                BOOT.execute(self.arguments("apply"), run=self.fake_run)
        self.assertEqual({}, self.plugins)
        self.assertFalse((self.profile / BOOT.STATE_DIRECTORY / "managed.json").exists())


if __name__ == "__main__":
    unittest.main()
