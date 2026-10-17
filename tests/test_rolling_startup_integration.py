from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "machine" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ROLLING = load("rolling_plugins", SCRIPTS / "rolling_plugins.py")
BINDING = load("rolling_startup_binding", SCRIPTS / "startup_binding.py")
CONVERGENCE = load("rolling_verified_convergence", SCRIPTS / "verified_convergence.py")


def git(path: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "-C", str(path), *arguments],
        capture_output=True, text=True, encoding="utf-8",
    )
    if completed.returncode:
        raise RuntimeError(f"Git fixture command failed: {arguments}: {completed.stderr}")
    return completed.stdout.strip()


class RollingStartupIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="rolling startup integration ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.core_remote, self.core = self._repository("core")
        self.publisher_remote, self.publisher = self._repository("publisher")
        self._publish_publisher()
        self._publish_core("v1")
        self.original_fetch = ROLLING._fetch_main
        routes = {
            "https://github.com/tj-agents/core.git": self.core_remote,
            "https://github.com/tj-agents/marketplace.git": self.publisher_remote,
        }

        def fetch(url: str, root: Path, deadline=None):
            authenticated = ROLLING.canonical_source(url)
            source = routes.get(authenticated)
            if source is None:
                raise AssertionError(f"unexpected publisher fetch: {url}")
            clone = root / "git" / ROLLING._cache_name(authenticated)
            clone.parent.mkdir(parents=True, exist_ok=True)
            if not (clone / ".git").is_dir():
                subprocess.run(["git", "clone", "--no-checkout", "--depth", "1", str(source), str(clone)],
                               check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", str(clone), "fetch", "--force", "--depth", "1", "origin",
                 "refs/heads/main:refs/remotes/origin/main"],
                check=True, capture_output=True,
            )
            return clone, git(clone, "rev-parse", "refs/remotes/origin/main")

        ROLLING._fetch_main = fetch
        self.addCleanup(setattr, ROLLING, "_fetch_main", self.original_fetch)
        self.project = self.root / "project"
        self.project.mkdir()
        self.codex_home = self.root / "codex"
        original_module = BINDING._module
        trust = mock.Mock()
        loader = mock.patch.object(BINDING, "_module", side_effect=lambda name, paths:
                                   trust if name == "codex_hook_trust" else original_module(name, paths))
        loader.start()
        self.addCleanup(loader.stop)
        self.environ = {
            "CODEX_HOME": str(self.codex_home),
            "CLAUDE_CONFIG_DIR": str(self.root / "claude"),
            "AGENT_STATE_DIRECTORY": str(self.root / "state"),
        }

    def _repository(self, name: str) -> tuple[Path, Path]:
        remote = self.root / f"{name}.git"
        author = self.root / f"{name}-author"
        subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(remote)], check=True,
                       capture_output=True)
        subprocess.run(["git", "clone", str(remote), str(author)], check=True, capture_output=True)
        return remote, author

    @staticmethod
    def _write(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def _commit(self, author: Path, message: str) -> str:
        git(author, "add", "-A")
        git(author, "commit", "-m", message)
        git(author, "push", "origin", "HEAD:main")
        return git(author, "rev-parse", "HEAD")

    def _publish_publisher(self) -> str:
        self._write(self.publisher / ".claude-plugin" / "marketplace.json", {
            "name": "publisher",
            "plugins": [{"name": "other", "source": "./relocated/other"}],
        })
        self._write(self.publisher / "relocated" / "other" / ".claude-plugin" / "plugin.json", {"name": "other"})
        (self.publisher / "relocated" / "other" / "payload.txt").write_text("publisher main", encoding="utf-8")
        return self._commit(self.publisher, "publisher current catalog")

    def _publish_core(self, version: str) -> str:
        generator = self.core / "scripts" / "sync_plugin_packages.py"
        generator.parent.mkdir(parents=True, exist_ok=True)
        generator.write_text(
            "from pathlib import Path\n"
            "def build(root, validate_catalog_digests=False):\n"
            "    return {}, Path(root) / 'plugins', set(), {}\n"
            "def publication_fingerprint(root, output):\n"
            "    return 'fixture-publication'\n",
            encoding="utf-8",
        )
        self._write(self.core / "plugins" / "publication.json", {"source_fingerprint": "fixture-publication"})
        self._write(self.core / ".claude-plugin" / "marketplace.json", {
            "name": "base-agents",
            "plugins": [
                {"name": "base", "source": "./plugins/base"},
                {"name": "engineering", "source": "./plugins/engineering"},
                {
                    "name": "other",
                    "source": {
                        "source": "git-subdir",
                        "url": "https://github.com/tj-agents/marketplace.git",
                        "path": "./stale-path-that-must-not-be-used",
                    },
                },
                {"name": "unselected", "source": "./plugins/unselected"},
            ],
        })
        self._write(self.core / "plugins" / "base" / ".claude-plugin" / "plugin.json", {"name": "base"})
        self._write(self.core / "plugins" / "base" / "harness.json", {
            "schema_version": 1,
            "plugin": "base-agents/base",
            "source_roots": [],
            "requires": {"marketplaces": [], "plugins": [], "hooks": [],
                         "permissions": {"claude_allow": [], "codex_prefix_rules": []}},
        })
        engineering = self.core / "plugins" / "engineering"
        self._write(engineering / ".claude-plugin" / "plugin.json", {"name": "engineering"})
        self._write(engineering / "harness.json", {
            "schema_version": 1,
            "plugin": "base-agents/engineering",
            "source_roots": [],
            "requires": {
                "marketplaces": [{"id": "base-agents", "repository": "tj-agents/core"}],
                "plugins": ["base-agents/base"],
                "hooks": [],
                "permissions": {
                    "claude_allow": [],
                    "codex_prefix_rules": [{
                        "pattern": [["python"], "-B", "${PLUGIN_ROOT}/workflow.py"],
                        "justification": "fixture workflow",
                        "match": [["python", "-B", "${PLUGIN_ROOT}/workflow.py"]],
                        "not_match": [["python", "${PLUGIN_ROOT}/workflow.py"]],
                    }],
                },
            },
        })
        self._write(engineering / "workflows" / "hosts" / "agent-delivery.json", {
            "generated_agent_patterns": ["lane-*.toml"],
            "former_managed_agents": ["lane-old.toml"],
            "project_managed_agent_sha256": {},
        })
        agents = engineering / "codex-agents"
        agents.mkdir(parents=True, exist_ok=True)
        if version == "v1":
            (agents / "lane-old.toml").write_text("name = 'old'\n", encoding="utf-8")
            (engineering / "obsolete.txt").write_text("obsolete", encoding="utf-8")
        else:
            for stale in (agents / "lane-old.toml", engineering / "obsolete.txt"):
                stale.unlink(missing_ok=True)
            (agents / "lane-new.toml").write_text("name = 'new'\n", encoding="utf-8")
        self._write(self.core / "plugins" / "unselected" / ".claude-plugin" / "plugin.json", {"name": "unselected"})
        return self._commit(self.core, f"core {version}")

    def _resolve(self, include_current_alias: bool = False):
        selections = [
            ROLLING.Selection("engineering@base-agents", "https://github.com/tj-agents/core.git", "base-agents"),
            ROLLING.Selection("other@base-agents", "https://github.com/tj-agents/core.git", "base-agents"),
        ]
        if include_current_alias:
            selections.append(
                ROLLING.Selection("engineering@tj-agents", "https://github.com/tj-agents/core.git", "tj-agents"),
            )
        revisions: dict[str, str] = {}
        packages = ROLLING.resolve(selections, self.root / "cache", source_revisions=revisions)
        return packages, revisions

    def _prepared(self, packages, revisions):
        catalog, _roots = ROLLING._projection("codex", packages, self.root / "cache")
        verified = tuple(ROLLING.VerifiedRoot(package.identity, package.root, package.revision, package.repository)
                         for package in packages)
        return ROLLING.Prepared(
            "codex",
            tuple(item for package in packages for item in ("-c", f"plugins.{package.identity}.enabled=true")),
            verified,
            catalog,
            {},
            (),
            tuple(sorted(revisions.items())),
            self.codex_home / "plugins",
            ROLLING.Deadline(),
        )

    def test_current_catalog_resolves_selected_closure_then_converges_permissions_and_owned_agents(self):
        packages, revisions = self._resolve()
        self.assertEqual(["base@base-agents", "engineering@base-agents", "other@base-agents"],
                         [package.identity for package in packages])
        self.assertEqual(2, len(revisions))
        other = next(package for package in packages if package.identity == "other@base-agents")
        self.assertEqual("publisher main", (other.root / "payload.txt").read_text(encoding="utf-8"))
        self.assertFalse((other.root / "stale-path-that-must-not-be-used").exists())
        self.assertFalse(any(package.identity == "unselected@base-agents" for package in packages))

        prepared = self._prepared(packages, revisions)
        user_agent = self.codex_home / "agents" / "personal.toml"
        user_agent.parent.mkdir(parents=True)
        user_agent.write_text("name = 'personal'\n", encoding="utf-8")
        with mock.patch.dict(os.environ, self.environ, clear=False):
            BINDING._converge(prepared, "fixture-codex", self.project)
        self.assertEqual("name = 'personal'\n", user_agent.read_text(encoding="utf-8"))
        self.assertTrue((self.codex_home / "agents" / "lane-old.toml").is_file())
        self.assertIn("workflow.py", (self.codex_home / "rules" / "base-agents.rules").read_text(encoding="utf-8"))
        arguments = BINDING._launch_arguments(["exec", "--", "prompt"], prepared.launch_args)
        self.assertLess(arguments.index(prepared.launch_args[0]), arguments.index("--"))

        self._publish_core("v2")
        packages, revisions = self._resolve()
        engineering = next(package for package in packages if package.identity == "engineering@base-agents")
        self.assertFalse((engineering.root / "obsolete.txt").exists())
        with mock.patch.dict(os.environ, self.environ, clear=False):
            BINDING._converge(self._prepared(packages, revisions), "fixture-codex", self.project)
        self.assertFalse((self.codex_home / "agents" / "lane-old.toml").exists())
        self.assertEqual("name = 'new'\n", (self.codex_home / "agents" / "lane-new.toml").read_text(encoding="utf-8"))
        self.assertEqual("name = 'personal'\n", user_agent.read_text(encoding="utf-8"))

    def test_missing_selection_and_explicitly_disabled_required_dependency_fail(self):
        with self.assertRaisesRegex(ROLLING.RollingPluginError, "explicitly disabled"):
            ROLLING.resolve(
                [ROLLING.Selection("engineering@base-agents", "https://github.com/tj-agents/core.git", "base-agents")],
                self.root / "cache", {"base@base-agents"},
            )
        with self.assertRaisesRegex(ROLLING.RollingPluginError, "missing from the current publisher catalog"):
            ROLLING.resolve(
                [ROLLING.Selection("missing@base-agents", "https://github.com/tj-agents/core.git", "base-agents")],
                self.root / "cache",
            )

    def test_current_engineering_aliases_share_one_verified_delivery_but_different_generations_fail(self):
        packages, revisions = self._resolve(include_current_alias=True)
        prepared = self._prepared(packages, revisions)
        engineering = [root for root in prepared.selected_roots if root.identity.startswith("engineering@")]
        self.assertEqual(2, len(engineering))
        self.assertEqual({root.revision for root in engineering}, {git(self.core, "rev-parse", "HEAD")})
        with mock.patch.dict(os.environ, self.environ, clear=False):
            BINDING._converge(prepared, "fixture-codex", self.project)
        self.assertTrue((self.codex_home / "agents" / "lane-old.toml").is_file())

        self._publish_core("v2")
        later, _revisions = self._resolve()
        different = next(root for root in self._prepared(later, {}).selected_roots
                         if root.identity == "engineering@base-agents")
        with self.assertRaises(CONVERGENCE.ConvergenceError):
            CONVERGENCE._engineering((engineering[0], different))

    def test_convergence_failure_prevents_the_native_session_from_starting(self):
        packages, revisions = self._resolve()
        prepared = self._prepared(packages, revisions)
        conflict = self.codex_home / "agents" / "lane-old.toml"
        conflict.parent.mkdir(parents=True)
        conflict.write_text("name = 'user owned'\n", encoding="utf-8")

        class Active:
            def __enter__(self):
                return self

            def __exit__(self, *details):
                return None

        Active.prepared = prepared
        runtime = mock.Mock()
        original_module = BINDING._module

        with mock.patch.dict(os.environ, self.environ, clear=False), \
                mock.patch.object(BINDING, "preflight", return_value=Active()), \
                mock.patch.object(BINDING, "native_target_for_shim", return_value="native"), \
                mock.patch.object(BINDING, "_preflight_arguments", return_value={"project": self.project}), \
                mock.patch.object(BINDING, "_module", side_effect=lambda name, paths:
                                  runtime if name == "codex_runtime_binding" else original_module(name, paths)), \
                mock.patch.object(ROLLING, "verify_final"), \
                mock.patch.object(BINDING.subprocess, "Popen") as native:
            with self.assertRaisesRegex(BINDING.StartupBindingError, "unowned or modified"):
                BINDING.run_session("codex", "typed", self.project, ["exec", "prompt"])
        native.assert_not_called()
        self.assertEqual("name = 'user owned'\n", conflict.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
