"""Behavioral tests for catalog validation and exact-profile bootstrap."""

import argparse
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/machine/utility/bootstrap-capabilities/scripts/bootstrap_capabilities.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_capabilities", SCRIPT)
BOOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BOOT)


class CatalogTests(unittest.TestCase):
    def catalog(self):
        return json.loads((ROOT / ".agents/catalog/catalog.json").read_text(encoding="utf-8"))

    def test_catalog_has_unique_closed_acyclic_plugins(self):
        releases, plugins = BOOT.catalog_index(self.catalog())
        self.assertEqual(1, len(releases))
        self.assertEqual(3, len(plugins))
        self.assertEqual(
            ["base-agents/base"],
            plugins["base-agents/engineering"]["dependencies"]["required"],
        )
        self.assertEqual({"base-agents/base", "base-agents/engineering", "base-agents/machine"}, set(plugins))

    def test_lock_requires_dependency_closure_and_known_skills(self):
        catalog = self.catalog()
        releases, plugins = BOOT.catalog_index(catalog)
        base_release = catalog["releases"][0]["id"]
        incomplete = {
            "schema_version": 1,
            "plugins": [
                {
                    "id": "base-agents/engineering",
                    "release": base_release,
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
        base_release = catalog["releases"][0]["id"]
        lock = {
            "schema_version": 1,
            "plugins": [
                {
                    "id": "base-agents/base",
                    "release": base_release,
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


class RevisionValidationTests(unittest.TestCase):
    def test_catalog_revision_formats_and_lock_commit_equality(self):
        original = json.loads((ROOT / ".agents/catalog/catalog.json").read_text(encoding="utf-8"))
        for revision in ("v9.8.7", "a" * 40):
            with self.subTest(revision=revision):
                catalog = json.loads(json.dumps(original))
                catalog["releases"][0]["revision"] = revision
                releases, plugins = BOOT.catalog_index(catalog)
                lock = {"schema_version": 1, "plugins": [{"id": name, "release": plugin["_release"]["id"], "commit": "a" * 40, "required_skills": [], "path_scopes": [], "exceptions": []} for name, plugin in plugins.items()]}
                self.assertEqual(3, len(BOOT.validate_lock(lock, releases, plugins)))
                if revision == "a" * 40:
                    for selection in lock["plugins"]:
                        selection["commit"] = "b" * 40
                    with self.assertRaisesRegex(BOOT.BootstrapError, "disagrees with lock/state commit"):
                        BOOT.validate_lock(lock, releases, plugins)
        for revision in ("main", "a" * 39, "A" * 40, "a" * 40 + "^{commit}", "refs/tags/v1.0.0", "v1.2", "v1.2.3-beta"):
            with self.subTest(revision=revision):
                catalog = json.loads(json.dumps(original))
                catalog["releases"][0]["revision"] = revision
                with self.assertRaisesRegex(BOOT.BootstrapError, "immutable semantic tag or full lowercase"):
                    BOOT.catalog_index(catalog)

    def test_sha_mismatch_blocks_state_checkout_and_verification_before_git(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "checkout"
            release = {"id": "fixture@1.0.0", "marketplace": "fixture", "source": "fixture", "revision": "a" * 40}
            record = {"checkout": str(destination), "release": release["id"], "source": "fixture", "revision": "a" * 40, "commit": "b" * 40}
            run = mock.Mock(side_effect=AssertionError("Git must not run"))
            operations = [lambda: BOOT.release_state(release, "b" * 40, destination), lambda: BOOT.validate_state_record(record, destination, "fixture"), lambda: BOOT.checkout_release(run, release, "b" * 40, destination), lambda: BOOT.verify_checkout(run, Path(temporary), release, "b" * 40, [], {})]
            for operation in operations:
                with self.subTest(operation=operations.index(operation)), self.assertRaisesRegex(BOOT.BootstrapError, "disagrees with lock/state commit"):
                    operation()
            self.assertFalse(destination.exists())
            run.assert_not_called()

    def test_pending_complete_identity_and_flat_revision_cannot_conflict_with_commit(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            prior = {"checkout": str(destination), "release": "fixture@1.0.0", "source": "fixture", "revision": "b" * 40, "commit": "b" * 40}
            target = {**prior, "release": "fixture@1.0.1", "revision": "a" * 40, "commit": "a" * 40}
            pending = {"from": prior, "to": target, "source": "fixture", "revision": "b" * 40}
            with self.assertRaisesRegex(BOOT.BootstrapError, "disagrees with lock/state commit"):
                BOOT.validate_pending_transition(pending, prior, target, {"marketplace": "fixture"})
            pending["revision"] = target["revision"]
            pending["to"] = {**target, "revision": "c" * 40}
            run = mock.Mock(side_effect=AssertionError("Git must not run"))
            with self.assertRaisesRegex(BOOT.BootstrapError, "disagrees with lock/state commit"):
                BOOT.upgrade_pending_transition(run, pending, prior, target, destination, "fixture")
            with self.assertRaisesRegex(BOOT.BootstrapError, "disagrees with lock/state commit"):
                BOOT.validate_transition_checkout(run, pending, destination)
            run.assert_not_called()

    def test_matching_legacy_sha_identity_needs_no_tag_and_ambiguity_stays_closed(self):
        record = {"release": "fixture@1.0.0", "commit": "a" * 40}
        expected = {**record, "revision": "a" * 40}
        with mock.patch.object(BOOT, "git", side_effect=AssertionError("Tag discovery must not run")):
            self.assertEqual("a" * 40, BOOT.resolve_legacy_revision(None, record, Path("fixture"), expected))
        expected["release"] = "fixture@1.0.1"
        with mock.patch.object(BOOT, "git", return_value="v1.0.0\nv2.0.0"):
            with self.assertRaisesRegex(BOOT.BootstrapError, "cannot determine an exact revision"):
                BOOT.resolve_legacy_revision(None, record, Path("fixture"), expected)

    def test_installed_sha_identity_is_checked_for_both_hosts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plugin = {"version": "1.0.0", "digest": BOOT.tree_digest(root, []), "_release": {"revision": "a" * 40}}
            for harness, version in (("codex", "1.0.0"), ("claude", "b" * 12)):
                installed = {"example@fixture": {"enabled": True, "version": version, "path": str(root)}}
                with self.subTest(harness=harness), self.assertRaisesRegex(BOOT.BootstrapError, "disagrees with lock/state commit"):
                    BOOT.verify_installed_plugin(harness, "example@fixture", installed, plugin, "b" * 40)
                self.assertFalse(BOOT.installed_plugin_is_exact(harness, "example@fixture", installed, plugin, "b" * 40))

    def test_loaded_state_rejects_malformed_sha_pairs_in_every_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            valid = {"commit": "a" * 40, "revision": "a" * 40}
            malformed = {"commit": "b" * 40, "revision": "a" * 40}
            states = [{"schema_version": 1, "marketplaces": {"fixture": malformed}, "transitions": {}}, {"schema_version": 1, "marketplaces": {"fixture": valid}, "transitions": {"fixture": {"from": malformed, "to": valid, "revision": "a" * 40}}}, {"schema_version": 1, "marketplaces": {"fixture": valid}, "transitions": {"fixture": {"from": valid, "to": valid, "revision": "b" * 40}}}]
            for state in states:
                with self.subTest(state=state):
                    BOOT.write_json(BOOT.state_path(profile), state)
                    before = BOOT.state_path(profile).read_bytes()
                    with self.assertRaisesRegex(BOOT.BootstrapError, "disagrees with lock/state commit"):
                        BOOT.load_state(profile)
                    self.assertEqual(before, BOOT.state_path(profile).read_bytes())

    def test_catalog_schema_requires_the_complete_immutable_revision(self):
        schema = json.loads((ROOT / ".agents/catalog/catalog.schema.json").read_text(encoding="utf-8"))
        pattern = schema["$defs"]["release"]["properties"]["revision"]["pattern"]
        for revision, accepted in (("v1.2.3", True), ("a" * 40, True), ("main", False), ("A" * 40, False), ("a" * 40 + "\n", False), ("v1.2.3\n", False)):
            with self.subTest(revision=revision):
                self.assertEqual(accepted, re.search(pattern, revision) is not None)


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
        self.host_commands = []
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
        self.host_commands.append(list(arguments))
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

    def prepare_source_only_move(self):
        moved_source = self.root / "source-only moved marketplace"
        self.git("clone", "--no-hardlinks", str(self.source), str(moved_source), cwd=self.root)
        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        catalog["releases"][0]["source"] = str(moved_source)
        self.catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
        return moved_source

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

    def test_source_only_transition_is_journaled_and_resumes_after_remote_rewrite(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            moved_source = self.prepare_source_only_move()
            self.fail_plugin_list_once = True
            with self.assertRaisesRegex(BOOT.BootstrapError, "injected plugin-list failure"):
                BOOT.execute(self.arguments("apply"), run=self.fake_run)

            state = json.loads((self.profile / BOOT.STATE_DIRECTORY / "managed.json").read_text())
            transition = state["transitions"]["fixture"]
            self.assertEqual(BOOT.normalize_source(str(moved_source)), transition["to"]["source"])
            checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
            self.assertEqual(str(moved_source), self.git("remote", "get-url", "origin", cwd=checkout).strip())
            resumed = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        self.assertEqual("applied", resumed["status"])
        state = json.loads((self.profile / BOOT.STATE_DIRECTORY / "managed.json").read_text())
        self.assertEqual(BOOT.normalize_source(str(moved_source)), state["marketplaces"]["fixture"]["source"])
        self.assertEqual({}, state["transitions"])

    def test_apply_repairs_installed_package_drift_then_becomes_idempotent(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            installed_payload = Path(self.plugins["example@fixture"]["path"]) / "payload.txt"
            installed_payload.write_text("corrupt\n", encoding="utf-8")
            before_repair = self.host_mutations
            repaired = BOOT.execute(self.arguments("apply"), run=self.fake_run)
            after_repair = self.host_mutations
            repeated = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        self.assertEqual("applied", repaired["status"])
        self.assertEqual("payload\n", installed_payload.read_text(encoding="utf-8"))
        self.assertEqual(before_repair + 1, after_repair)
        self.assertEqual(after_repair, self.host_mutations)
        self.assertEqual("applied", repeated["status"])

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

    def prepare_legacy_pending_transition(self, rewrite_origin):
        moved_source, moved_commit = self.prepare_moved_release()
        state_file = self.profile / BOOT.STATE_DIRECTORY / "managed.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        prior = state["marketplaces"]["fixture"]
        legacy_prior = {
            key: prior[key] for key in ("checkout", "release", "commit")
        }
        expected = {
            "checkout": prior["checkout"],
            "release": "fixture@1.0.1",
            "commit": moved_commit,
        }
        state["marketplaces"]["fixture"] = legacy_prior
        state["transitions"]["fixture"] = {
            "from": legacy_prior,
            "to": expected,
            "source": str(moved_source),
            "revision": "v1.0.1",
        }
        state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        if rewrite_origin:
            checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
            self.git("remote", "set-url", "origin", str(moved_source), cwd=checkout)
        return moved_source, moved_commit, state_file

    def assert_legacy_pending_transition_resumes(self, rewrite_origin):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            moved_source, moved_commit, state_file = self.prepare_legacy_pending_transition(
                rewrite_origin
            )
            resumed = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        self.assertEqual("applied", resumed["status"])
        state = json.loads(state_file.read_text(encoding="utf-8"))
        managed = state["marketplaces"]["fixture"]
        self.assertEqual(moved_commit, managed["commit"])
        self.assertEqual(BOOT.normalize_source(str(moved_source)), managed["source"])
        self.assertEqual("v1.0.1", managed["revision"])
        self.assertEqual({}, state["transitions"])

    def test_legacy_pending_transition_resumes_before_remote_rewrite(self):
        self.assert_legacy_pending_transition_resumes(False)

    def test_legacy_pending_transition_resumes_after_remote_rewrite(self):
        self.assert_legacy_pending_transition_resumes(True)

    def test_legacy_managed_state_is_upgraded_without_refreshing_plugins(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            state_file = self.profile / BOOT.STATE_DIRECTORY / "managed.json"
            state = json.loads(state_file.read_text())
            state["marketplaces"]["fixture"].pop("source")
            state["marketplaces"]["fixture"].pop("revision")
            state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            mutations_before = self.host_mutations
            upgraded = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        self.assertEqual("applied", upgraded["status"])
        self.assertEqual(mutations_before, self.host_mutations)
        state = json.loads(state_file.read_text())
        self.assertEqual(BOOT.normalize_source(str(self.source)), state["marketplaces"]["fixture"]["source"])
        self.assertEqual("v1.0.0", state["marketplaces"]["fixture"]["revision"])

    def test_legacy_state_uses_catalog_revision_when_it_differs_from_version(self):
        self.git("tag", "-d", "v1.0.0", cwd=self.source)
        self.git("tag", "v2.0.0", cwd=self.source)
        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        catalog["releases"][0]["revision"] = "v2.0.0"
        self.catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            state_file = self.profile / BOOT.STATE_DIRECTORY / "managed.json"
            state = json.loads(state_file.read_text(encoding="utf-8"))
            state["marketplaces"]["fixture"].pop("source")
            state["marketplaces"]["fixture"].pop("revision")
            state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            upgraded = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        managed = json.loads(state_file.read_text(encoding="utf-8"))["marketplaces"]["fixture"]
        self.assertEqual("applied", upgraded["status"])
        self.assertEqual("v2.0.0", managed["revision"])
        self.assertEqual(BOOT.normalize_source(str(self.source)), managed["source"])

    def test_legacy_revision_only_change_fetches_target_before_upgrading_state(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            state_file = self.profile / BOOT.STATE_DIRECTORY / "managed.json"
            state = json.loads(state_file.read_text(encoding="utf-8"))
            state["marketplaces"]["fixture"].pop("source")
            state["marketplaces"]["fixture"].pop("revision")
            state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            self.git("tag", "v2.0.0", cwd=self.source)
            catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
            catalog["releases"][0]["revision"] = "v2.0.0"
            self.catalog_path.write_text(
                json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
            )
            migrated = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        managed = json.loads(state_file.read_text(encoding="utf-8"))["marketplaces"]["fixture"]
        checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
        self.assertEqual("applied", migrated["status"])
        self.assertEqual("v2.0.0", managed["revision"])
        self.assertEqual(
            self.commit,
            self.git("rev-parse", "refs/tags/v2.0.0^{commit}", cwd=checkout).strip(),
        )

    def test_ambiguous_legacy_revision_fails_closed(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
            self.git("tag", "v2.0.0", self.commit, cwd=checkout)
            state_file = self.profile / BOOT.STATE_DIRECTORY / "managed.json"
            state = json.loads(state_file.read_text(encoding="utf-8"))
            state["marketplaces"]["fixture"].pop("source")
            state["marketplaces"]["fixture"].pop("revision")
            state_file.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            self.prepare_moved_release()
            with self.assertRaisesRegex(
                BOOT.BootstrapError, "cannot determine an exact revision"
            ):
                BOOT.execute(self.arguments("apply"), run=self.fake_run)

    def test_same_revision_fetch_interruption_resumes_with_target_tag(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            moved_source, moved_commit = self.prepare_moved_release()
            self.git("tag", "-f", "v1.0.0", moved_commit, cwd=moved_source)
            catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
            catalog["releases"][0]["revision"] = "v1.0.0"
            self.catalog_path.write_text(
                json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
            )
            original_git = BOOT.git
            interrupted = False

            def fail_after_fetch(run, arguments, cwd=None):
                nonlocal interrupted
                result = original_git(run, arguments, cwd)
                if arguments[0] == "fetch" and not interrupted:
                    interrupted = True
                    raise BOOT.BootstrapError("injected post-fetch failure")
                return result

            with mock.patch.object(BOOT, "git", side_effect=fail_after_fetch):
                with self.assertRaisesRegex(BOOT.BootstrapError, "post-fetch"):
                    BOOT.execute(self.arguments("apply"), run=self.fake_run)
            resumed = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        state = json.loads(
            (self.profile / BOOT.STATE_DIRECTORY / "managed.json").read_text(encoding="utf-8")
        )
        self.assertEqual("applied", resumed["status"])
        self.assertEqual(moved_commit, state["marketplaces"]["fixture"]["commit"])
        self.assertEqual("v1.0.0", state["marketplaces"]["fixture"]["revision"])
        self.assertEqual({}, state["transitions"])

    def assert_legacy_same_revision_transition_resumes(self, checkout_target):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            moved_source, moved_commit = self.prepare_moved_release()
            self.git("tag", "-f", "v1.0.0", moved_commit, cwd=moved_source)
            catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
            catalog["releases"][0]["revision"] = "v1.0.0"
            self.catalog_path.write_text(
                json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
            )

            state_file = self.profile / BOOT.STATE_DIRECTORY / "managed.json"
            state = json.loads(state_file.read_text(encoding="utf-8"))
            prior = state["marketplaces"]["fixture"]
            legacy_prior = {
                key: prior[key] for key in ("checkout", "release", "commit")
            }
            legacy_target = {
                "checkout": prior["checkout"],
                "release": "fixture@1.0.1",
                "commit": moved_commit,
            }
            state["marketplaces"]["fixture"] = legacy_prior
            state["transitions"]["fixture"] = {
                "from": legacy_prior,
                "to": legacy_target,
                "source": str(moved_source),
                "revision": "v1.0.0",
            }
            state_file.write_text(
                json.dumps(state, indent=2) + "\n", encoding="utf-8"
            )

            checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
            self.git("remote", "set-url", "origin", str(moved_source), cwd=checkout)
            self.git(
                "fetch",
                "origin",
                "+refs/tags/v1.0.0:refs/tags/v1.0.0",
                cwd=checkout,
            )
            expected_head = prior["commit"]
            if checkout_target:
                self.git("checkout", "--detach", moved_commit, cwd=checkout)
                expected_head = moved_commit
            self.assertEqual(expected_head, self.git("rev-parse", "HEAD", cwd=checkout).strip())
            resumed = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        managed = json.loads(state_file.read_text(encoding="utf-8"))["marketplaces"]["fixture"]
        self.assertEqual("applied", resumed["status"])
        self.assertEqual(moved_commit, managed["commit"])
        self.assertEqual("v1.0.0", managed["revision"])
        self.assertEqual({}, json.loads(state_file.read_text(encoding="utf-8"))["transitions"])

    def test_legacy_same_revision_transition_resumes_after_target_tag_fetch(self):
        self.assert_legacy_same_revision_transition_resumes(False)

    def test_legacy_same_revision_transition_resumes_after_target_checkout(self):
        self.assert_legacy_same_revision_transition_resumes(True)

    def test_catalog_revision_is_preserved_when_it_differs_from_version(self):
        self.git("tag", "-d", "v1.0.0", cwd=self.source)
        self.git("tag", "v2.0.0", cwd=self.source)
        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        catalog["releases"][0]["revision"] = "v2.0.0"
        self.catalog_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")

        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            _, moved_commit = self.prepare_moved_release()
            migrated = BOOT.execute(self.arguments("apply"), run=self.fake_run)

        self.assertEqual("applied", migrated["status"])
        state = json.loads((self.profile / BOOT.STATE_DIRECTORY / "managed.json").read_text())
        self.assertEqual(moved_commit, state["marketplaces"]["fixture"]["commit"])
        self.assertEqual("v1.0.1", state["marketplaces"]["fixture"]["revision"])

    def test_offline_verify_rejects_checkout_origin_drift(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: "codex-fixture" if name == "codex" else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
            self.git("remote", "set-url", "origin", "https://example.invalid/drift.git", cwd=checkout)
            with self.assertRaisesRegex(BOOT.BootstrapError, "origin"):
                BOOT.execute(self.arguments("verify"), run=self.fake_run)

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

    def test_claude_release_transition_refreshes_commit_versioned_cache(self):
        with mock.patch.object(
            BOOT,
            "executable",
            side_effect=lambda name: f"{name}-fixture" if name in {"codex", "claude"} else shutil.which("git"),
        ):
            BOOT.execute(self.arguments("apply", "claude"), run=self.fake_run)
            moved_source, moved_commit = self.prepare_moved_release()
            migrated = BOOT.execute(self.arguments("apply", "claude"), run=self.fake_run)
            unavailable_source = self.root / "moved source unavailable during verify"
            moved_source.rename(unavailable_source)
            mutations_before_verify = self.host_mutations

            def offline_run(command, **kwargs):
                if command[0] not in {"codex-fixture", "claude-fixture"} and any(
                    argument in {"clone", "fetch"} for argument in command[1:]
                ):
                    self.fail(f"offline verify attempted network/source Git operation: {command}")
                return self.fake_run(command, **kwargs)

            verified = BOOT.execute(self.arguments("verify", "claude"), run=offline_run)

        self.assertEqual("applied", migrated["status"])
        self.assertEqual("verified", verified["status"])
        self.assertEqual(moved_commit[:12], self.plugins["example@fixture"]["version"])
        self.assertEqual(1, self.plugin_refreshes)
        self.assertIn(
            ["plugin", "update", "example@fixture", "--scope", "user", "--yes"],
            self.host_commands,
        )
        self.assertEqual(mutations_before_verify, self.host_mutations)


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

    def set_revision(self, revision):
        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        catalog["releases"][0]["revision"] = revision
        self.catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    def native_fixture(self):
        return mock.patch.object(BOOT, "executable", side_effect=lambda name: f"{name}-fixture" if name in {"codex", "claude"} else shutil.which("git"))

    def test_untagged_sha_apply_and_offline_verify_work_for_both_hosts(self):
        self.git("tag", "-d", "v1.0.0", cwd=self.source)
        self.set_revision(self.commit)
        fetches = []
        original_git = BOOT.git

        def capture_git(run, arguments, cwd=None):
            if arguments[0] == "fetch":
                fetches.append(arguments)
            return original_git(run, arguments, cwd)

        with self.native_fixture(), mock.patch.object(BOOT, "git", side_effect=capture_git):
            for harness in ("codex", "claude"):
                with self.subTest(harness=harness):
                    self.profile = self.root / f"{harness} isolated profile"
                    self.marketplaces = set()
                    self.plugins = {}
                    self.assertEqual("planned", BOOT.execute(self.arguments("preview", harness), run=self.fake_run)["status"])
                    self.assertFalse(self.profile.exists())
                    self.assertEqual("applied", BOOT.execute(self.arguments("apply", harness), run=self.fake_run)["status"])
                    before = self.host_mutations
                    self.assertEqual("applied", BOOT.execute(self.arguments("apply", harness), run=self.fake_run)["status"])
                    self.assertEqual(before, self.host_mutations)
                    checkout = self.profile / BOOT.STATE_DIRECTORY / "checkouts/fixture"
                    self.assertEqual("", self.git("tag", cwd=checkout))
                    count = len(fetches)
                    self.assertEqual("verified", BOOT.execute(self.arguments("verify", harness), run=self.fake_run)["status"])
                    self.assertEqual(count, len(fetches))
                    state = BOOT.load_state(self.profile)
                    self.assertEqual(self.commit, state["marketplaces"]["fixture"]["revision"])
        self.assertTrue(fetches)
        self.assertTrue(all(arguments[-1] == self.commit and "refs/tags/" not in " ".join(arguments) for arguments in fetches))

    def test_sha_lock_mismatch_fails_preview_before_profile_or_host_mutation(self):
        self.set_revision(self.parent_commit)
        for mode in ("preview", "apply", "verify"):
            with self.subTest(mode=mode), self.assertRaisesRegex(BOOT.BootstrapError, "disagrees with lock/state commit"):
                BOOT.execute(self.arguments(mode), run=self.fake_run)
            self.assertFalse(self.profile.exists())
            self.assertEqual(0, self.host_mutations)

    def test_sha_resolver_rejects_tree_and_annotated_tag_object_ids(self):
        self.git("tag", "-a", "object-tag", "-m", "Fixture annotated tag", cwd=self.source)
        object_ids = [self.git("rev-parse", "HEAD^{tree}", cwd=self.source).strip(), self.git("rev-parse", "refs/tags/object-tag", cwd=self.source).strip()]
        for object_id in object_ids:
            with self.subTest(object_id=object_id), self.assertRaises(BOOT.BootstrapError):
                BOOT.resolve_revision(subprocess.run, object_id, self.source, object_id)
        self.assertEqual(self.commit, BOOT.resolve_revision(subprocess.run, self.commit, self.source, self.commit))
        self.assertEqual(self.commit, BOOT.resolve_revision(subprocess.run, "v1.0.0", self.source, self.commit))

    def test_untagged_sha_legacy_state_upgrade_is_exact_and_idempotent(self):
        self.git("tag", "-d", "v1.0.0", cwd=self.source)
        self.set_revision(self.commit)
        with self.native_fixture():
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            state_path = BOOT.state_path(self.profile)
            state = BOOT.load_state(self.profile)
            state["marketplaces"]["fixture"].pop("source")
            state["marketplaces"]["fixture"].pop("revision")
            BOOT.write_json(state_path, state)
            mutations = self.host_mutations
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            self.assertEqual(mutations, self.host_mutations)
            self.assertEqual(self.commit, BOOT.load_state(self.profile)["marketplaces"]["fixture"]["revision"])
            self.assertEqual("verified", BOOT.execute(self.arguments("verify"), run=self.fake_run)["status"])

    def assert_revision_transition_recovers(self, prior_sha, target_sha, failure_command):
        if prior_sha:
            self.set_revision(self.commit)
        with self.native_fixture():
            BOOT.execute(self.arguments("apply"), run=self.fake_run)
            _, moved_commit = self.prepare_moved_release()
            if target_sha:
                self.set_revision(moved_commit)
            original_git = BOOT.git
            interrupted = False

            def fail_after_operation(run, arguments, cwd=None):
                nonlocal interrupted
                result = original_git(run, arguments, cwd)
                if arguments[0] == failure_command and not interrupted:
                    interrupted = True
                    raise BOOT.BootstrapError("injected revision transition interruption")
                return result

            with mock.patch.object(BOOT, "git", side_effect=fail_after_operation):
                with self.assertRaisesRegex(BOOT.BootstrapError, "revision transition interruption"):
                    BOOT.execute(self.arguments("apply"), run=self.fake_run)
            pending = BOOT.load_state(self.profile)["transitions"]["fixture"]
            self.assertEqual(self.commit, pending["from"]["commit"])
            self.assertEqual(moved_commit, pending["to"]["commit"])
            self.assertEqual("applied", BOOT.execute(self.arguments("apply"), run=self.fake_run)["status"])
            state = BOOT.load_state(self.profile)
            self.assertEqual({}, state["transitions"])
            self.assertEqual(moved_commit if target_sha else "v1.0.1", state["marketplaces"]["fixture"]["revision"])
            self.assertEqual("verified", BOOT.execute(self.arguments("verify"), run=self.fake_run)["status"])

    def test_tag_to_sha_transition_resumes_after_fetch(self):
        self.assert_revision_transition_recovers(False, True, "fetch")

    def test_sha_to_tag_transition_resumes_after_checkout(self):
        self.assert_revision_transition_recovers(True, False, "checkout")

    def test_sha_to_sha_transition_resumes_after_fetch(self):
        self.assert_revision_transition_recovers(True, True, "fetch")

    def test_sha_to_sha_transition_resumes_after_checkout(self):
        self.assert_revision_transition_recovers(True, True, "checkout")

    def test_malformed_managed_sha_blocks_preview_and_apply_without_host_operations(self):
        state = {"schema_version": 1, "marketplaces": {"fixture": {"commit": self.commit, "revision": self.parent_commit}}, "transitions": {}}
        BOOT.write_json(BOOT.state_path(self.profile), state)
        before = BOOT.state_path(self.profile).read_bytes()
        for mode in ("preview", "apply", "verify"):
            with self.subTest(mode=mode), self.assertRaisesRegex(BOOT.BootstrapError, "disagrees with lock/state commit"):
                BOOT.execute(self.arguments(mode), run=self.fake_run)
            self.assertEqual(before, BOOT.state_path(self.profile).read_bytes())
            self.assertEqual([], self.host_commands)


if __name__ == "__main__":
    unittest.main()
