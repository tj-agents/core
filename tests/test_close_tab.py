import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/machine/utility/peer-cli/scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name):
    path = SCRIPTS / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


close_tab = load_module("close_tab")
configurator = load_module("configure_terminal_tab_close")


def completed(stdout="", returncode=0, stderr=""):
    return mock.Mock(stdout=stdout, returncode=returncode, stderr=stderr)


class CloseTabTests(unittest.TestCase):
    def test_stale_windows_fallback_requires_unique_title_and_honors_recorded_id(self):
        identity = {"kind": "windows-terminal", "wt_session": "native-session"}
        entry = {"title": "same", "terminal": identity}
        target = {"title": "same", "identity": {"kind": "windows-terminal",
                  "automation_id": "tab-2"}}
        with mock.patch.object(close_tab, "windows_inventory", return_value=[target]), \
                mock.patch.object(close_tab.session_close, "entries", return_value=[(Path("stale"), entry)]), \
                mock.patch.object(close_tab, "close_actual") as closer:
            close_tab.close_stale_entry(entry)
            closer.assert_called_once_with(target, force=True)
        for recorded, targets in ((identity, [target, target]),
                                  ({**identity, "automation_id": "tab-1"}, [target])):
            with self.subTest(recorded=recorded, targets=targets), \
                    mock.patch.object(close_tab, "windows_inventory", return_value=targets), \
                    mock.patch.object(close_tab.session_close, "entries", return_value=[(Path("stale"), entry)]), \
                    mock.patch.object(close_tab, "close_actual") as closer:
                with self.assertRaisesRegex(close_tab.TerminalRefusal, "absent or ambiguous"):
                    close_tab.close_stale_entry({"title": "same", "terminal": recorded})
                closer.assert_not_called()

    def test_stale_windows_title_fallback_refuses_any_other_registered_peer(self):
        stale = {"session_id": "stale", "title": "same",
                 "terminal": {"kind": "windows-terminal", "wt_session": "old"}}
        live = {"session_id": "live", "title": "same",
                "terminal": {"kind": "windows-terminal", "wt_session": "current"}}
        target = {"title": "same", "identity": {"kind": "windows-terminal",
                  "automation_id": "live-tab"}}
        for state in (True, None, False):
            with self.subTest(other_peer_liveness=state), \
                    mock.patch.object(close_tab, "windows_inventory", return_value=[target]), \
                    mock.patch.object(close_tab.session_close, "entries",
                                      return_value=[(Path("stale"), stale), (Path("live"), live)]), \
                    mock.patch.object(close_tab.session_close, "liveness", return_value=state), \
                    mock.patch.object(close_tab, "close_actual") as closer:
                with self.assertRaisesRegex(close_tab.TerminalRefusal, "absent or ambiguous"):
                    close_tab.close_stale_entry(stale)
                closer.assert_not_called()

    def test_stale_linux_target_requires_recorded_identity_despite_matching_title(self):
        cases = (
            ("kitty", "kitty_inventory", {"window_id": "1", "listen_on": "unix:/kitty"},
             {"window_id": "2", "listen_on": "unix:/kitty"}),
            ("tmux", "tmux_inventory", {"pane_id": "%1", "socket": "/tmp/tmux"},
             {"pane_id": "%2", "socket": "/tmp/tmux"}),
        )
        for kind, inventory, recorded, replacement in cases:
            with self.subTest(kind=kind):
                identity = {"kind": kind, **recorded}
                entry = {"title": "same", "terminal": identity}
                other = {"title": "same", "identity": {"kind": kind, **replacement}}
                exact = {"title": "same", "identity": identity}
                with mock.patch.object(close_tab, inventory, return_value=[other]), \
                        mock.patch.object(close_tab, "close_actual") as closer:
                    with self.assertRaisesRegex(close_tab.TerminalRefusal, "absent or ambiguous"):
                        close_tab.close_stale_entry(entry)
                    closer.assert_not_called()
                with mock.patch.object(close_tab, inventory, return_value=[other, exact]), \
                        mock.patch.object(close_tab, "close_actual") as closer:
                    close_tab.close_stale_entry(entry)
                    closer.assert_called_once_with(exact, force=True)

    def test_missing_or_unverified_native_identity_refuses(self):
        entry = {"pid": 0, "pid_started_at": 0, "terminal": {"kind": "kitty"}}
        with self.assertRaisesRegex(close_tab.TerminalRefusal, "unknown"):
            close_tab.close_entry(entry)

    def test_windows_adapter_selects_pscustomobject_element_and_emits_arrays(self):
        source = (SCRIPTS / "windows_terminal_uia.ps1").read_text(encoding="utf-8")
        self.assertIn("$matches[0].Element.FindFirst", source)
        self.assertNotIn("$matches[0].FindFirst", source)
        self.assertIn("Write-Output ('[' + ($items -join ',') + ']')", source)
        self.assertNotIn("SendKeys", source)

    def test_windows_inventory_accepts_zero_one_and_many_tabs(self):
        payloads = ("[]", '[{"title":"one","automationId":"a"}]',
                    '[{"title":"one","automationId":"a"},{"title":"two","automationId":"b"}]')
        for payload, count in zip(payloads, (0, 1, 2)):
            with self.subTest(payload=payload):
                with mock.patch.object(close_tab, "is_windows", return_value=True), \
                        mock.patch.object(Path, "is_file", return_value=True), \
                        mock.patch.object(close_tab, "run", return_value=completed(payload)):
                    self.assertEqual(len(close_tab.windows_inventory()), count)

    def test_windows_inventory_refuses_single_object_payload(self):
        with mock.patch.object(close_tab, "is_windows", return_value=True), \
                mock.patch.object(Path, "is_file", return_value=True), \
                mock.patch.object(close_tab, "run", return_value=completed('{"title":"one"}')):
            with self.assertRaisesRegex(close_tab.TerminalUnavailable, "non-array"):
                close_tab.windows_inventory()

    def test_kitty_inventory_selects_exact_window_not_prefix_or_tab_id(self):
        inventory = [{"tabs": [
            {"id": 11, "windows": [{"id": 110, "pid": 10, "title": "other"}]},
            {"id": 99, "windows": [{"id": 11, "pid": 20, "title": "target"}]},
        ]}]
        with mock.patch.object(close_tab, "run", return_value=completed(json.dumps(inventory))):
            _tab, window = close_tab.kitty_target({"listen_on": "unix:/kitty", "window_id": "11"})
        self.assertEqual(window["id"], 11)
        self.assertNotEqual(window["id"], 110)

    def test_tmux_uses_recorded_socket_and_exact_pane_without_killing_siblings(self):
        result = completed("%1\t101\tone\n%10\t202\ttwo\n")
        root = mock.Mock(pid=101)
        with mock.patch.object(close_tab, "run", return_value=result) as runner, \
                mock.patch.object(close_tab, "exact_process", return_value=root):
            pane, found = close_tab.tmux_target(
                {"socket": "/tmp/tmux-1/default", "pane_id": "%1"})
        self.assertEqual(pane, "%1")
        self.assertEqual(found.pid, 101)
        self.assertEqual(runner.call_args.args[0][:3], ["tmux", "-S", "/tmp/tmux-1/default"])
        target = {"title": "one", "identity": {"kind": "tmux", "pane_id": "%1",
                  "socket": "/tmp/tmux-1/default"}, "actual": True}
        with mock.patch.object(close_tab, "target_liveness", return_value=False), \
                mock.patch.object(close_tab, "run", return_value=completed()) as closer:
            close_tab.close_actual(target)
        self.assertEqual(closer.call_args.args[0][-2:], ["-t", "%1"])

    def test_host_must_descend_from_terminal_root(self):
        entry = {"pid": 30, "pid_started_at": 3.0}
        host = mock.Mock(pid=30, ppid=20, started_at=3.0)
        root = mock.Mock(pid=20, ppid=1, started_at=1.0)
        with mock.patch.object(close_tab.session_close, "verified_live", return_value=True), \
                mock.patch.object(close_tab.session_close, "process_info", side_effect=[host, root]):
            self.assertTrue(close_tab.host_belongs_to(entry, [20]))
        with mock.patch.object(close_tab.session_close, "verified_live", return_value=True), \
                mock.patch.object(close_tab.session_close, "process_info", side_effect=[host, root, None]):
            self.assertFalse(close_tab.host_belongs_to(entry, [99]))

    def test_reused_parent_pid_cannot_prove_terminal_ownership(self):
        entry = {"pid": 30, "pid_started_at": 3.0}
        host = mock.Mock(pid=30, ppid=20, started_at=3.0)
        reused_root = mock.Mock(pid=20, ppid=1, started_at=10.0)
        with mock.patch.object(close_tab.session_close, "verified_live", return_value=True), \
                mock.patch.object(close_tab.session_close, "process_info",
                                  side_effect=[host, reused_root]):
            self.assertFalse(close_tab.host_belongs_to(entry, [20]))

    def test_exact_title_requires_one_actual_target(self):
        targets = [
            {"title": "same", "identity": {"kind": "tmux", "pane_id": "%1"}, "actual": True},
            {"title": "same", "identity": {"kind": "tmux", "pane_id": "%2"}, "actual": True},
        ]
        with mock.patch.object(close_tab, "merged_inventory", return_value=targets):
            with self.assertRaisesRegex(close_tab.TerminalRefusal, "ambiguous"):
                close_tab.main(["--title", "same"])

    def test_wildcard_one_target_still_refuses_without_all(self):
        targets = [{"title": "only", "identity": {"kind": "tmux", "pane_id": "%1"},
                    "actual": True}]
        with mock.patch.object(close_tab, "merged_inventory", return_value=targets):
            with self.assertRaisesRegex(close_tab.TerminalRefusal, "wildcard"):
                close_tab.main(["--title", "on*"])

    def test_live_unknown_and_force_policy_never_signals_a_process(self):
        target = {"title": "stale", "identity": {"kind": "tmux", "pane_id": "%1"},
                  "actual": True}
        for live in (True, None):
            with self.subTest(live=live), \
                    mock.patch.object(close_tab, "target_liveness", return_value=live), \
                    mock.patch.object(close_tab, "run") as runner, \
                    mock.patch.object(close_tab.os, "kill") as killer:
                with self.assertRaisesRegex(close_tab.TerminalRefusal, "live or unknown"):
                    close_tab.close_actual(target)
                runner.assert_not_called()
                killer.assert_not_called()
        with mock.patch.object(close_tab, "target_liveness", return_value=None), \
                mock.patch.object(close_tab, "run", return_value=completed()) as runner, \
                mock.patch.object(close_tab.os, "kill") as killer:
            close_tab.close_actual(target, force=True)
        self.assertEqual(runner.call_args.args[0][-2:], ["-t", "%1"])
        killer.assert_not_called()

    def test_windows_unique_title_must_resolve_to_one_live_uia_tab(self):
        entry = {"title": "peer", "pid": 7, "pid_started_at": 2.0,
                 "terminal": {"kind": "windows-terminal"}}
        tabs = [{"title": "peer", "identity": {"kind": "windows-terminal",
                 "automation_id": "a"}, "actual": True}]
        with mock.patch.object(close_tab, "is_windows", return_value=True), \
                mock.patch.object(close_tab.session_close, "liveness", return_value=True), \
                mock.patch.object(close_tab.session_close, "entries", return_value=[(Path("x"), entry)]), \
                mock.patch.object(close_tab, "windows_inventory", return_value=tabs), \
                mock.patch.object(close_tab, "close_actual") as closer:
            close_tab.close_entry(entry)
        closer.assert_called_once_with(tabs[0], force=True)
        with mock.patch.object(close_tab, "is_windows", return_value=True), \
                mock.patch.object(close_tab.session_close, "liveness", return_value=True), \
                mock.patch.object(close_tab.session_close, "entries", return_value=[(Path("x"), entry)]), \
                mock.patch.object(close_tab, "windows_inventory", return_value=tabs * 2):
            with self.assertRaisesRegex(close_tab.TerminalRefusal, "ambiguous"):
                close_tab.close_entry(entry)

    def test_windows_automation_id_requires_one_uia_tab_across_all_windows(self):
        entry = {"title": "peer", "pid": 7, "pid_started_at": 2.0,
                 "terminal": {"kind": "windows-terminal", "automation_id": "tab-7"}}
        tabs = [{"title": "peer", "identity": {"kind": "windows-terminal",
                 "automation_id": "tab-7"}, "actual": True}]
        with mock.patch.object(close_tab, "is_windows", return_value=True), \
                mock.patch.object(close_tab.session_close, "liveness", return_value=True), \
                mock.patch.object(close_tab, "windows_inventory", return_value=tabs), \
                mock.patch.object(close_tab, "close_actual") as closer:
            close_tab.close_entry(entry)
        closer.assert_called_once_with(tabs[0], force=True)
        with mock.patch.object(close_tab, "is_windows", return_value=True), \
                mock.patch.object(close_tab.session_close, "liveness", return_value=True), \
                mock.patch.object(close_tab, "windows_inventory", return_value=tabs * 2):
            with self.assertRaisesRegex(close_tab.TerminalRefusal, "ambiguous"):
                close_tab.close_entry(entry)

    def test_list_combines_actual_stale_tabs_and_registered_live_targets(self):
        actual = {"title": "stale", "identity": {"kind": "tmux", "pane_id": "%1"},
                  "actual": True}
        live_entry = {"title": "live", "terminal": {"kind": "tmux", "pane_id": "%2"}}
        stale_entry = {"title": "stale", "terminal": {"kind": "tmux", "pane_id": "%1"}}
        with mock.patch.object(close_tab, "current_terminal_targets", return_value=[actual]), \
                mock.patch.object(close_tab.session_close, "entries",
                                  return_value=[(Path("stale"), stale_entry),
                                                (Path("live"), live_entry)]), \
                mock.patch.object(close_tab.session_close, "liveness",
                                  side_effect=lambda entry: False if entry is stale_entry else True):
            inventory = close_tab.merged_inventory()
        self.assertEqual(inventory[0]["title"], "stale")
        self.assertFalse(inventory[0]["live"])
        self.assertEqual(inventory[1]["title"], "live")
        self.assertTrue(inventory[1]["live"])

    def test_konsole_uses_qdbus6_full_service_path_and_refuses_foreign_ancestry(self):
        identity = {"kind": "konsole", "service": "org.kde.konsole-3", "session": "/Sessions/7"}
        first = completed("20\n")
        second = completed("21\n")
        with mock.patch.object(close_tab.shutil, "which", return_value="/usr/bin/qdbus6"), \
                mock.patch.object(close_tab, "run", side_effect=[first, second]) as runner, \
                mock.patch.object(close_tab, "exact_process", side_effect=[mock.Mock(pid=20), mock.Mock(pid=21)]):
            self.assertEqual(close_tab.konsole_roots(identity), [20, 21])
        self.assertEqual(runner.call_args_list[0].args[0][:3],
                         ["/usr/bin/qdbus6", "org.kde.konsole-3", "/Sessions/7"])
        entry = {"pid": 30, "pid_started_at": 3.0, "terminal": identity}
        with mock.patch.object(close_tab.session_close, "liveness", return_value=True), \
                mock.patch.object(close_tab, "konsole_roots", return_value=[20]), \
                mock.patch.object(close_tab, "host_belongs_to", return_value=False), \
                mock.patch.object(close_tab.os, "kill") as killer:
            with self.assertRaisesRegex(close_tab.TerminalRefusal, "not owned"):
                close_tab.close_entry(entry)
        killer.assert_not_called()


class ConfigureTerminalTabCloseTests(unittest.TestCase):
    def test_write_preserves_windows_line_endings_and_backup_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            original = b'{\r\n  "profiles": {"defaults": {}}\r\n}\r\n'
            path.write_bytes(original)
            _message, backup = configurator.configure(path, "always")
            self.assertEqual(backup.read_bytes(), original)
            updated = path.read_bytes()
            self.assertIn(b'"closeOnExit": "always"', updated)
            self.assertNotIn(b"\n", updated.replace(b"\r\n", b""))

    def test_preview_preserves_jsonc_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            original = '{\n  // keep this comment\n  "profiles": { "defaults": { } }\n}\n'
            path.write_text(original, encoding="utf-8")
            message, backup = configurator.configure(path, "always", preview=True)
            self.assertIn("Would set", message)
            self.assertIsNone(backup)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_write_makes_timestamped_backup_and_preserves_jsonc(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            original = '{\n  // keep\n  "profiles": {\n    "defaults": {\n      "fontFace": "Cascadia"\n    }\n  }\n}\n'
            path.write_text(original, encoding="utf-8")
            moment = configurator.datetime.datetime(2026, 10, 10, 12, 0, 1)
            _message, backup = configurator.configure(path, "always", now=moment)
            self.assertEqual(backup.name, "settings.json.bak-20261010120001")
            self.assertEqual(backup.read_text(encoding="utf-8"), original)
            updated = path.read_text(encoding="utf-8")
            self.assertIn("// keep", updated)
            self.assertIn('"closeOnExit": "always",', updated)

    def test_empty_defaults_does_not_receive_invalid_comma(self):
        updated, changed = configurator.update_close_on_exit('{"profiles":{"defaults":{}}}', "always")
        self.assertTrue(changed)
        self.assertIn('"closeOnExit": "always"}', updated)
        self.assertNotIn('"always",}', updated)

    def test_existing_value_is_unchanged_without_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text('{"profiles":{"defaults":{"closeOnExit":"always"}}}', encoding="utf-8")
            message, backup = configurator.configure(path, "always")
            self.assertEqual(message, "closeOnExit is already 'always'.")
            self.assertIsNone(backup)
            self.assertEqual(list(Path(directory).glob("*.bak-*")), [])

    def test_linux_noop_and_explicit_disposable_settings_path(self):
        output = io.StringIO()
        with mock.patch.object(configurator, "is_windows", return_value=False), \
                contextlib.redirect_stdout(output):
            self.assertEqual(configurator.main([]), 0)
        self.assertIn("Linux is a no-op", output.getvalue())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text('{"profiles":{"defaults":{}}}', encoding="utf-8")
            with mock.patch.object(configurator, "is_windows", return_value=False):
                self.assertEqual(configurator.main(["--settings-path", str(path), "--preview"]), 0)

    def test_default_windows_settings_path_uses_local_app_data(self):
        path = configurator.default_settings_path({"LOCALAPPDATA": "C:/Users/agent/AppData/Local"})
        self.assertEqual(
            str(path).replace("\\", "/"),
            "C:/Users/agent/AppData/Local/Packages/"
            "Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json",
        )
