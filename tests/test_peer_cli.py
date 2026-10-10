import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock

PATH = Path(__file__).resolve().parents[1] / ".agents/machine/utility/peer-cli/scripts/peer_cli.py"
sys.path.insert(0, str(PATH.parent))
spec = importlib.util.spec_from_file_location("peer_cli", PATH); peer_cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(peer_cli)

class PeerCliTests(unittest.TestCase):
    def test_ambiguous_prefix_refuses(self):
        entries = [
            {"title": "one", "session_id": "a"},
            {"title": "once", "session_id": "b"},
        ]
        with self.assertRaises(peer_cli.session_close.Refusal):
            peer_cli.select(entries, "on")

    def test_exact_session_id_wins(self):
        entries = [
            {"title": "one", "session_id": "a"},
            {"title": "once", "session_id": "b"},
        ]
        self.assertEqual("b", peer_cli.select(entries, "b")["session_id"])

    def test_unrecorded_uses_cross_platform_process_table(self):
        process = peer_cli.register_session.ProcessInfo(88, 1, "codex.exe", 2.0)
        with mock.patch.object(peer_cli.register_session, "process_table", return_value={88: process}):
            found = peer_cli.unrecorded([])
        self.assertEqual(found[0]["pid"], 88)
        self.assertFalse(found[0]["recorded"])

    def test_force_closes_a_recorded_stale_terminal_without_killing_a_pid(self):
        stale = {
            "title": "old tab",
            "session_id": "stale",
            "alive": False,
            "terminal": {"kind": "windows-terminal"},
        }
        with mock.patch.object(peer_cli, "records", return_value=[stale]):
            with mock.patch.object(peer_cli.close_tab, "close_stale_entry") as close_terminal, \
                    mock.patch.object(peer_cli.os, "kill") as killer:
                self.assertEqual(peer_cli.main(["close", "stale", "--force"]), 0)
        close_terminal.assert_called_once_with(stale)
        killer.assert_not_called()

    def test_windows_uia_unavailable_uses_verified_host_only_fallback(self):
        target = {
            "title": "peer", "session_id": "peer", "pid": 31, "pid_started_at": 4.0,
            "terminal": {"kind": "windows-terminal"},
        }
        with mock.patch.object(peer_cli.close_tab, "close_entry",
                               side_effect=peer_cli.close_tab.TerminalUnavailable("no UIA")), \
                mock.patch.object(peer_cli.session_close, "verified_live", return_value=True), \
                mock.patch.object(peer_cli.os, "kill") as killer:
            self.assertTrue(peer_cli.close_terminal_or_host(target, force=False))
        killer.assert_called_once_with(31, peer_cli.signal.SIGTERM)

    def test_windows_ambiguous_tab_never_uses_host_only_fallback(self):
        target = {
            "title": "peer", "session_id": "peer", "pid": 31, "pid_started_at": 4.0,
            "terminal": {"kind": "windows-terminal"},
        }
        with mock.patch.object(peer_cli.close_tab, "close_entry",
                               side_effect=peer_cli.close_tab.TerminalRefusal("ambiguous")), \
                mock.patch.object(peer_cli.os, "kill") as killer:
            with self.assertRaisesRegex(peer_cli.close_tab.TerminalRefusal, "ambiguous"):
                peer_cli.close_terminal_or_host(target, force=False)
        killer.assert_not_called()

    def test_unknown_identity_never_signals_a_process_even_with_force(self):
        target = {
            "title": "unknown", "session_id": "unknown", "pid": 31,
            "pid_started_at": 4.0, "alive": None,
            "terminal": {"kind": "windows-terminal"},
        }
        with mock.patch.object(peer_cli, "records", return_value=[target]), \
                mock.patch.object(peer_cli.os, "kill") as killer:
            with self.assertRaisesRegex(peer_cli.session_close.Refusal, "unknown"):
                peer_cli.main(["close", "unknown", "--force"])
        killer.assert_not_called()
