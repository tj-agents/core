from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "machine" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("startup_binding_test", SCRIPTS / "startup_binding.py")
BINDING = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BINDING)


class StartupBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="startup binding ")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.root = self.project / "machine"
        (self.root / "hooks").mkdir(parents=True)
        (self.root / "hooks" / "claude.json").write_text(
            '{"hooks":{"SessionStart":"hook_dispatch.py"}}', encoding="utf-8",
        )
        self.verified = type("Verified", (), {"root": self.root, "identity": "machine@tj-agents"})()
        self.prepared = type("Prepared", (), {
            "selected_roots": (self.verified,), "launch_args": (), "environment": {},
        })()

    def test_isolated_script_loads_shipped_dependencies_outside_the_callers_import_path(self):
        package = self.project / "packaged machine \u00e9" / "resources" / "machine" / "scripts"
        shutil.copytree(SCRIPTS, package)
        caller = self.project / "caller"
        caller.mkdir()
        (caller / "codex_marketplace_sync.py").write_text(
            'raise RuntimeError("untrusted caller import")\n', encoding="utf-8",
        )
        environment = dict(os.environ, PYTHONPATH=str(caller))

        for scripts in (SCRIPTS, package):
            with self.subTest(scripts=scripts):
                completed = subprocess.run(
                    [sys.executable, "-I", "-B", str(scripts / "startup_binding.py"), "--help"],
                    cwd=caller, env=environment, capture_output=True, timeout=30,
                )
                diagnostics = (completed.stdout + completed.stderr).decode("utf-8", errors="replace")
                self.assertEqual(0, completed.returncode, diagnostics)
                self.assertIn(b"--host", completed.stdout)
                self.assertNotIn(b"untrusted caller import", completed.stderr)

    def test_session_start_acknowledgement_releases_the_preflight_after_native_start(self):
        events = []
        prepared = self.prepared

        class Active:
            def __enter__(self):
                return self

            def __exit__(self, *details):
                events.append("exit")

            def materialize_native(self, executable):
                events.append("materialize")
                return prepared

            def acknowledge_binding(self):
                events.append("ack")

        class Process:
            def __init__(self, _command, **kwargs):
                events.append("start")
                directory = Path(kwargs["env"][BINDING.ACK_DIRECTORY_ENV])
                token = kwargs["env"][BINDING.ACK_TOKEN_ENV]
                (directory / token).write_text(token, encoding="utf-8")

            def poll(self):
                return None

            def wait(self, timeout=None):
                return 0

        with mock.patch.object(BINDING, "preflight", return_value=Active()), \
                mock.patch.object(BINDING, "native_target_for_shim", return_value="native"), \
                mock.patch.object(BINDING, "_preflight_arguments", return_value={}), \
                mock.patch.object(BINDING, "_converge"), \
                mock.patch.object(BINDING, "command_for_target", return_value=["native"]), \
                mock.patch.object(BINDING.subprocess, "Popen", Process), \
                mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.project / "config")}, clear=False):
            self.assertEqual(0, BINDING.run_session("claude", "typed", self.project, ["session"]))

        self.assertEqual(["materialize", "start", "ack", "exit"], events)

    def test_selected_packages_without_session_start_dispatcher_fail_before_native_start(self):
        (self.root / "hooks" / "claude.json").write_text('{"hooks":{"SessionStart":[]}}', encoding="utf-8")
        prepared = self.prepared

        class Active:
            def __enter__(self):
                return self

            def __exit__(self, *details):
                return None

            def materialize_native(self, executable):
                return prepared

        with mock.patch.object(BINDING, "preflight", return_value=Active()), \
                mock.patch.object(BINDING, "native_target_for_shim", return_value="native"), \
                mock.patch.object(BINDING, "_preflight_arguments", return_value={}), \
                mock.patch.object(BINDING, "_converge"), \
                mock.patch.object(BINDING.subprocess, "Popen") as launch, \
                mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.project / "config")}, clear=False):
            with self.assertRaisesRegex(BINDING.StartupBindingError, "hook_dispatch SessionStart"):
                BINDING.run_session("claude", "typed", self.project, ["session"])

        launch.assert_not_called()

    def test_native_catalog_overrides_follow_user_options_before_a_prompt_delimiter(self):
        self.assertEqual(
            ["-c", "marketplaces.old.source=old", "exec", "-c", "marketplaces.old.source=new", "--", "prompt"],
            BINDING._launch_arguments(
                ["-c", "marketplaces.old.source=old", "exec", "--", "prompt"],
                ["-c", "marketplaces.old.source=new"],
            ),
        )

    def test_empty_selection_does_not_export_startup_acknowledgement_state(self):
        prepared = type("Prepared", (), {
            "selected_roots": (), "launch_args": (), "environment": {"PREPARED": "yes"},
        })()

        class Active:
            def __enter__(self):
                return self

            def __exit__(self, *details):
                return None

            def materialize_native(self, executable):
                return prepared

            def acknowledge_binding(self):
                return None

        captured = {}

        def run(_command, **kwargs):
            captured.update(kwargs)
            return type("Result", (), {"returncode": 7})()

        with mock.patch.object(BINDING, "preflight", return_value=Active()), \
                mock.patch.object(BINDING, "native_target_for_shim", return_value="native"), \
                mock.patch.object(BINDING, "_preflight_arguments", return_value={}), \
                mock.patch.object(BINDING, "command_for_target", return_value=["native"]), \
                mock.patch.object(BINDING.subprocess, "run", side_effect=run), \
                mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.project / "config")}, clear=False):
            self.assertEqual(7, BINDING.run_session("claude", "typed", self.project, ["session"]))

        self.assertEqual("yes", captured["env"]["PREPARED"])
        self.assertNotIn(BINDING.ACK_DIRECTORY_ENV, captured["env"])
        self.assertNotIn(BINDING.ACK_TOKEN_ENV, captured["env"])
        self.assertNotIn(BINDING.SNAPSHOT_DIRECTORY_ENV, captured["env"])

    def test_preparation_uses_the_operation_budget_not_the_acknowledgement_timeout(self):
        prepared = type("Prepared", (), {
            "selected_roots": (), "launch_args": (), "environment": {},
        })()
        observed = []

        class Active:
            def __enter__(self):
                return self

            def __exit__(self, *details):
                return None

            def materialize_native(self, executable):
                return prepared

            def acknowledge_binding(self):
                return None

        def arguments(host, executable, project, values, remaining):
            observed.append(remaining())
            return {}

        with mock.patch.object(BINDING, "preflight", return_value=Active()), \
                mock.patch.object(BINDING, "native_target_for_shim", return_value="native"), \
                mock.patch.object(BINDING, "_preflight_arguments", side_effect=arguments), \
                mock.patch.object(BINDING, "command_for_target", return_value=["native"]), \
                mock.patch.object(BINDING.subprocess, "run", return_value=type("Result", (), {"returncode": 0})()), \
                mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.project / "config")}, clear=False):
            self.assertEqual(0, BINDING.run_session("claude", "typed", self.project, ["session"], timeout=0.01))

        self.assertGreater(observed[0], BINDING.STARTUP_TIMEOUT_SECONDS)

    def test_packaged_coordinator_loads_permissions_and_snapshot_helpers(self):
        package = self.project / "packaged machine"
        scripts = package / "resources" / "machine" / "scripts"
        scripts.mkdir(parents=True)
        permission_scripts = package / ".agents" / "machine" / "utility" / "plugin-selection" / "scripts"
        shutil.copytree(ROOT / ".agents/machine/utility/plugin-selection/scripts", permission_scripts)
        hooks = package / "hooks"
        hooks.mkdir()
        shutil.copyfile(ROOT / ".agents/hooks/codex_hook_snapshot.py", hooks / "codex_hook_snapshot.py")
        original_module = BINDING._module
        loaded = {}

        def modules(name, paths):
            module = original_module(name, paths)
            loaded[name] = module
            module.apply_verified = mock.Mock()
            return module

        prepared = type("Prepared", (), {"host": "claude", "selected_roots": (self.verified,)})()
        with mock.patch.object(BINDING, "HERE", scripts), mock.patch.object(BINDING, "_module", side_effect=modules):
            BINDING._converge(prepared, "fixture-claude", self.project)
            snapshot = BINDING._snapshot_module()
        permissions = loaded["harness_permissions_sync"]
        self.assertEqual(permission_scripts / "harness_permissions_sync.py", Path(permissions.__file__))
        permissions.apply_verified.assert_called_once_with(os.environ, "claude", self.project, prepared.selected_roots)
        self.assertEqual(hooks / "codex_hook_snapshot.py", Path(snapshot.__file__))

    def test_codex_convergence_applies_permissions_agents_then_trust(self):
        events = []

        class Deadline:
            def remaining(self, limit=BINDING.OPERATION_TIMEOUT_SECONDS):
                events.append(("remaining", limit))
                return limit

        prepared = type("Prepared", (), {
            "host": "codex",
            "selected_roots": (self.verified,),
            "launch_args": ("-c", "marketplaces.base-agents.source=current"),
            "environment": {"CODEX_HOME": str(self.project / "home")},
            "deadline": Deadline(),
        })()
        permissions = mock.Mock()
        convergence = mock.Mock()
        trust = mock.Mock()

        def modules(name, _paths):
            return {
                "harness_permissions_sync": permissions,
                "verified_convergence": convergence,
                "codex_hook_trust": trust,
            }[name]

        with mock.patch.object(BINDING, "_module", side_effect=modules):
            BINDING._converge(prepared, "native-codex", self.project)

        permissions.apply_verified.assert_called_once_with(
            os.environ, "codex", self.project, prepared.selected_roots,
        )
        convergence.converge.assert_called_once_with(os.environ, self.project, prepared.selected_roots)
        trust.apply_trust.assert_called_once_with(
            "native-codex", self.project, verified_roots=prepared.selected_roots,
            launch_args=prepared.launch_args, environment=prepared.environment,
            timeout=BINDING.OPERATION_TIMEOUT_SECONDS,
        )
        self.assertEqual([("remaining", BINDING.OPERATION_TIMEOUT_SECONDS)] * 4, events)

    def test_convergence_failure_blocks_native_start(self):
        prepared = self.prepared

        class Active:
            def __enter__(self):
                return self

            def __exit__(self, *details):
                return None

            def materialize_native(self, executable):
                return prepared

        with mock.patch.object(BINDING, "preflight", return_value=Active()), \
                mock.patch.object(BINDING, "native_target_for_shim", return_value="native"), \
                mock.patch.object(BINDING, "_preflight_arguments", return_value={}), \
                mock.patch.object(BINDING, "_converge", side_effect=RuntimeError("trust failed")), \
                mock.patch.object(BINDING.subprocess, "Popen") as launch, \
                mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.project / "config")}, clear=False):
            with self.assertRaisesRegex(BINDING.StartupBindingError, "trust failed"):
                BINDING.run_session("claude", "typed", self.project, ["session"])

        launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
