import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / ".agents/machine/utility/peer-cli/scripts/close_tab.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("close_tab", PATH)
close_tab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(close_tab)

class CloseTabTests(unittest.TestCase):
    def test_missing_or_unverified_native_identity_refuses(self):
        with self.assertRaises(close_tab.TerminalRefusal):
            close_tab.close_entry({"pid": 0, "pid_started_at": 0, "terminal": {"kind": "kitty"}})

    def test_windows_adapter_lists_tabs_and_supports_id_or_unique_title_without_keystrokes(self):
        source = PATH.with_name("windows_terminal_uia.ps1").read_text(encoding="utf-8")
        self.assertIn("AutomationId", source)
        self.assertIn("$Title", source)
        self.assertIn("$Json", source)
        self.assertIn("WindowsTerminal", source)
        self.assertNotIn("SendKeys", source)

    def test_kitty_inventory_selects_exact_window_not_prefix_or_tab_id(self):
        inventory = [{"tabs": [
            {"id": 11, "windows": [{"id": 110, "pid": 10}]},
            {"id": 99, "windows": [{"id": 11, "pid": 20}]},
        ]}]
        completed = mock.Mock(returncode=0, stdout=json.dumps(inventory), stderr="")
        with mock.patch.object(close_tab, "run", return_value=completed):
            _tab, window = close_tab.kitty_target({"listen_on": "unix:/kitty", "window_id": "11"})
        self.assertEqual(window["id"], 11)
        self.assertNotEqual(window["id"], 110)

    def test_tmux_uses_recorded_socket_and_exact_pane(self):
        completed = mock.Mock(returncode=0, stdout="%1\t101\n%10\t202\n", stderr="")
        root = mock.Mock(pid=101)
        with mock.patch.object(close_tab, "run", return_value=completed) as runner:
            with mock.patch.object(close_tab, "exact_process", return_value=root):
                pane, found = close_tab.tmux_target({"socket": "/tmp/tmux-1/default", "pane_id": "%1"})
        self.assertEqual(pane, "%1")
        self.assertEqual(found.pid, 101)
        self.assertEqual(runner.call_args.args[0][:3], ["tmux", "-S", "/tmp/tmux-1/default"])

    def test_host_must_descend_from_terminal_root(self):
        entry = {"pid": 30, "pid_started_at": 3.0}
        host = mock.Mock(pid=30, ppid=20)
        root = mock.Mock(pid=20, ppid=1)
        with mock.patch.object(close_tab.session_close, "verified_live", return_value=True):
            with mock.patch.object(close_tab.session_close, "process_info", side_effect=[host, root]):
                self.assertTrue(close_tab.host_belongs_to(entry, [20]))
        with mock.patch.object(close_tab.session_close, "verified_live", return_value=True):
            with mock.patch.object(close_tab.session_close, "process_info", side_effect=[host, root, None]):
                self.assertFalse(close_tab.host_belongs_to(entry, [99]))
