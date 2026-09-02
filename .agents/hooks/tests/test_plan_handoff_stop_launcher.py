import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plan_handoff_stop_launcher
from plan_handoff_stop_launcher import (
    TRUSTED_FILES,
    blob_oid,
    implementation_is_current,
    main,
    plugin_delivered,
)


class PluginDeliveryTests(unittest.TestCase):
    """An installed plugin has no repo above it, so the currency check could only ever fail -
    it would block every turn. Under plugin delivery the plugin is the author, so the launcher
    runs the implementation beside it instead of verifying a checkout that does not exist."""

    def setUp(self):
        self.hooks = Path(plan_handoff_stop_launcher.__file__).resolve().parent

    @patch.dict(os.environ, {}, clear=False)
    def test_a_vendored_copy_is_not_plugin_delivered(self):
        os.environ.pop("CLAUDE_PLUGIN_ROOT", None)

        self.assertFalse(plugin_delivered())

    @patch.dict(os.environ, {}, clear=False)
    def test_an_unrelated_plugin_root_is_not_this_copys_home(self):
        os.environ["CLAUDE_PLUGIN_ROOT"] = tempfile.mkdtemp()

        self.assertFalse(plugin_delivered())

    @patch.dict(os.environ, {}, clear=False)
    def test_a_workspace_ancestor_is_not_this_copys_plugin_root(self):
        os.environ["CLAUDE_PLUGIN_ROOT"] = str(self.hooks.parents[1])

        self.assertFalse(plugin_delivered())

    @patch.dict(os.environ, {}, clear=False)
    def test_the_hook_file_is_not_its_own_plugin_root(self):
        os.environ["CLAUDE_PLUGIN_ROOT"] = str(
            Path(plan_handoff_stop_launcher.__file__).resolve()
        )

        self.assertFalse(plugin_delivered())

    @patch.dict(os.environ, {}, clear=False)
    def test_a_plugin_root_containing_this_file_is_plugin_delivered(self):
        os.environ["CLAUDE_PLUGIN_ROOT"] = str(self.hooks.parent)

        self.assertTrue(plugin_delivered())

    @patch("plan_handoff_stop_launcher.runpy.run_path")
    @patch("plan_handoff_stop_launcher.implementation_is_current", return_value=False)
    @patch.dict(os.environ, {}, clear=False)
    def test_plugin_delivery_runs_the_sibling_implementation_without_a_currency_check(
        self, current, run_path
    ):
        os.environ["CLAUDE_PLUGIN_ROOT"] = str(self.hooks.parent)

        main()

        run_path.assert_called_once_with(
            str(self.hooks / "plan_handoff_stop.py"), run_name="__main__"
        )
        current.assert_not_called()

    @patch("plan_handoff_stop_launcher.runpy.run_path")
    @patch("plan_handoff_stop_launcher.implementation_is_current", return_value=False)
    @patch.dict(os.environ, {}, clear=False)
    def test_workspace_ancestor_does_not_bypass_the_currency_check(self, current, run_path):
        os.environ["CLAUDE_PLUGIN_ROOT"] = str(self.hooks.parents[1])
        output = io.StringIO()
        hook_input = io.TextIOWrapper(
            io.BytesIO(json.dumps({"stop_hook_active": False}).encode("utf-8")),
            encoding="utf-8",
        )

        with patch("sys.stdin", hook_input), redirect_stdout(output):
            main()

        current.assert_called_once()
        run_path.assert_not_called()
        self.assertIn('"decision": "block"', output.getvalue())


class PlanHandoffStopLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    @patch("plan_handoff_stop_launcher.subprocess.run")
    def test_reads_checked_out_blob_oid(self, run):
        run.return_value = Mock(returncode=0, stdout="abc123\n")

        self.assertEqual("abc123", blob_oid(self.root))
        run.assert_called_once_with(
            [
                "git",
                "-C",
                str(self.root),
                "hash-object",
                str(self.root / ".agents/hooks/plan_handoff_stop.py"),
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

    @patch("plan_handoff_stop_launcher.subprocess.run")
    def test_reads_origin_main_blob_oid_without_executing_it(self, run):
        run.return_value = Mock(returncode=0, stdout="def456\n")

        self.assertEqual("def456", blob_oid(self.root, revision="origin/main"))
        run.assert_called_once_with(
            [
                "git",
                "-C",
                str(self.root),
                "rev-parse",
                "origin/main:.agents/hooks/plan_handoff_stop.py",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

    @patch("plan_handoff_stop_launcher.blob_oid", side_effect=["same", "same"] * len(TRUSTED_FILES))
    def test_accepts_matching_implementation(self, _):
        self.assertTrue(implementation_is_current(self.root))

    @patch("plan_handoff_stop_launcher.blob_oid", side_effect=["old", "new"])
    def test_rejects_stale_implementation(self, _):
        self.assertFalse(implementation_is_current(self.root))

    @patch("plan_handoff_stop_launcher.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 5))
    def test_rejects_unverifiable_implementation(self, _):
        self.assertIsNone(blob_oid(self.root))

    @patch("plan_handoff_stop_launcher.runpy.run_path")
    @patch("plan_handoff_stop_launcher.implementation_is_current", return_value=False)
    def test_stale_launcher_blocks_once_without_running_old_implementation(self, _, run_path):
        output = io.StringIO()
        hook_input = io.TextIOWrapper(
            io.BytesIO(json.dumps({"stop_hook_active": False}).encode("utf-8")),
            encoding="utf-8",
        )
        with patch("sys.stdin", hook_input), redirect_stdout(output):
            main()

        self.assertIn('"decision": "block"', output.getvalue())
        self.assertIn("differs from origin/main", output.getvalue())
        run_path.assert_not_called()

    @patch("plan_handoff_stop_launcher.runpy.run_path")
    @patch("plan_handoff_stop_launcher.implementation_is_current", return_value=False)
    def test_stale_launcher_retry_guard_does_not_reblock(self, _, run_path):
        output = io.StringIO()
        hook_input = io.TextIOWrapper(
            io.BytesIO(json.dumps({"stop_hook_active": True}).encode("utf-8")),
            encoding="utf-8",
        )
        with patch("sys.stdin", hook_input), redirect_stdout(output):
            main()

        self.assertNotIn('"decision": "block"', output.getvalue())
        self.assertIn("prevent a recursive Stop-hook loop", output.getvalue())
        run_path.assert_not_called()

    @patch("plan_handoff_stop_launcher.runpy.run_path")
    @patch("plan_handoff_stop_launcher.implementation_is_current", return_value=True)
    def test_current_launcher_executes_only_checked_out_implementation(self, _, run_path):
        main()

        root = Path(__file__).resolve().parents[3]
        run_path.assert_called_once_with(
            str(root / ".agents/hooks/plan_handoff_stop.py"),
            run_name="__main__",
        )


if __name__ == "__main__":
    unittest.main()
