import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / ".codex/runtime/continuation/delivery_continuation.py"
SCHEDULER = ROOT / ".codex/runtime/continuation/continuation_scheduler.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


scheduler = load("continuation_scheduler_test", SCHEDULER)
adapter = load("delivery_continuation_test", ADAPTER)


class Result:
    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout, self.returncode, self.stderr = stdout, returncode, stderr


class LinuxTransport(scheduler.SchedulerTransport):
    def __init__(self, receipt=None):
        self.receipt = receipt
        self.files = {}
        self.calls = []
        self.fail_enable = False
        self.foreign_after_reload = None
        self.state = {"active": "active", "enabled": "enabled", "dropins": "", "reload": "no", "fragment": None}

    def run(self, args, **kwargs):
        self.calls.append(tuple(args))
        if "daemon-reload" in args:
            self.state["reload"] = "no"
            if self.foreign_after_reload:
                self.state.update(self.foreign_after_reload)
        if self.fail_enable and "enable" in args:
            return Result(returncode=1, stderr="injected registration failure")
        if "enable" in args:
            self.state.update(active="active", enabled="enabled")
        if "disable" in args:
            self.state.update(active="inactive", enabled="disabled")
        if "show" in args:
            unit = args[args.index("show") + 1]
            receipt = self.receipt
            if receipt is None:
                return Result(returncode=1, stderr="missing")
            path = receipt["service_path"] if unit == receipt["service_unit"] else receipt["timer_path"]
            # systemd emits named records, and may choose an order independently of --property.
            values = {"FragmentPath": self.state["fragment"] or path, "NeedDaemonReload": self.state["reload"], "LoadState": "loaded",
                      "DropInPaths": self.state["dropins"], "ActiveState": self.state["active"],
                      "UnitFileState": self.state["enabled"]}
            return Result("\n".join(key + "=" + values[key] for key in
                                      ("NeedDaemonReload", "FragmentPath", "UnitFileState", "DropInPaths", "LoadState", "ActiveState")) + "\n")
        return Result()

    def write(self, path, text):
        self.files[str(path)] = text

    def read(self, path):
        try:
            return self.files[str(path)]
        except KeyError as error:
            raise FileNotFoundError(path) from error

    def remove(self, path):
        self.files.pop(str(path), None)


class WindowsTransport(scheduler.SchedulerTransport):
    def __init__(self, task=None):
        self.task = task
        self.calls = []
        self.fail_register = False
        self.query_error = None
        self.query_invalid_json = False
        self.query_duration = None
        self.query_timeouts = []
        self.inventory_timeouts = []
        self.registrations = []

    def run(self, args, **kwargs):
        self.calls.append(tuple(args))
        payload = json.loads(kwargs.get("input_text") or "{}")
        operation = payload.get("operation")
        if "Get-ScheduledTask -TaskName 'AgentStandards-Continuation-*'" in args[-1]:
            self.inventory_timeouts.append(kwargs.get("timeout"))
            if self.query_duration is not None and self.query_duration > kwargs.get("timeout", 15):
                raise subprocess.TimeoutExpired(args, kwargs.get("timeout", 15))
            return Result(json.dumps(self.registrations))
        if operation == "query":
            self.query_timeouts.append(kwargs.get("timeout"))
            if self.query_duration is not None and self.query_duration > kwargs.get("timeout", 15):
                raise subprocess.TimeoutExpired(args, kwargs.get("timeout", 15))
            if self.query_error:
                return Result(returncode=1, stderr=self.query_error)
            if self.query_invalid_json:
                return Result("{")
            if self.task is None:
                return Result("null")
            return Result(json.dumps(self.task))
        if operation == "register":
            if self.fail_register:
                return Result(returncode=1, stderr="injected registration failure")
            self.task = {"TaskName": payload["task_name"], "TaskPath": "\\", "State": "Ready",
                         "Description": payload["description"], "Enabled": True,
                         "Actions": [{"Execute": payload["execute"], "Arguments": payload["arguments"],
                                      "WorkingDirectory": payload["worktree"]}],
                         "Triggers": [{"Enabled": True}]}
        if operation == "remove":
            self.task = None
        return Result()


class DeliveryContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="continuation unicode ")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name) / "work tree £"
        root.mkdir()
        self.root = root.resolve()
        self.owner_path = self.root / ".agents/continuation/owner.json"
        self.owner_path.parent.mkdir(parents=True)
        self.host = self.root / "native host"
        self.host.write_text("#!/bin/sh\n", encoding="utf-8")
        self.host.chmod(self.host.stat().st_mode | stat.S_IXUSR)
        self.owner = {"owner_id": "owner / $unicode £", "worktree": str(self.root), "harness": "codex", "state": "waiting"}
        self.owner_path.write_text(json.dumps(self.owner), encoding="utf-8")
        self.environment = {"XDG_CONFIG_HOME": str(Path(self.temp.name) / "config £"), "CODEX_HOME": "/safe profile £",
                            "GH_TOKEN": "must-not-copy", "CONTINUATION_NONCE": "must-not-child"}

    def receipt(self, interval=20):
        return scheduler.linux_receipt(self.owner, self.owner_path, ADAPTER, ROOT / ".codex/runtime/continuation/continuation_runtime.py",
                                       sys.executable, self.host, interval, self.environment)

    def windows_receipt(self):
        host = self.root / "native host.exe"
        host.write_text("native", encoding="utf-8")
        return scheduler.windows_receipt(self.owner, self.owner_path, ADAPTER, ROOT / ".codex/runtime/continuation/continuation_runtime.py",
                                         sys.executable, host, 20, self.environment)

    @unittest.skipIf(os.name == "nt" or not shutil.which("systemd-analyze"),
                     "Linux unit parser; Windows path transport has its inbox PowerShell counterpart")
    def test_real_systemd_parser_accepts_a_working_directory_with_special_characters(self):
        receipt = self.receipt()
        directory = self.root / 'cash$ percent% back\\slash "quotes"'
        directory.mkdir()
        receipt["worktree"] = str(directory)
        service, _ = scheduler.linux_units(receipt)
        unit = self.root / receipt["service_unit"]
        unit.write_text(service, encoding="utf-8")
        result = subprocess.run(["systemd-analyze", "--user", "verify", "--man=no", str(unit)],
                                capture_output=True, text=True, encoding="utf-8", timeout=15)
        if result.returncode and "SO_PASSRIGHTS" in result.stderr and "Operation not permitted" in result.stderr:
            self.skipTest("systemd user parser unavailable in this sandbox; Windows has the inbox PowerShell counterpart")
        self.assertEqual(0, result.returncode, result.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX systemd enable links; Windows re-registration uses task identity")
    def test_reregistration_keeps_the_enable_link_path_after_symlink_creation(self):
        receipt = self.receipt()
        target = Path(receipt["timer_path"])
        target.parent.mkdir(parents=True)
        target.write_text("timer", encoding="utf-8")
        link = Path(receipt["timer_enable_path"])
        link.parent.mkdir()
        link.symlink_to(target)
        self.assertTrue(scheduler._link_points_to(link, target))
        self.assertEqual(receipt["timer_enable_path"], self.receipt(10)["timer_enable_path"])

    def put_linux(self, receipt, transport):
        service, timer = scheduler.linux_units(receipt)
        transport.receipt = receipt
        transport.write(receipt["service_path"], service)
        transport.write(receipt["timer_path"], timer)

    def windows_task(self, receipt, *, enabled=True, trigger=True):
        return {"TaskName": receipt["task_name"], "TaskPath": "\\", "State": "Ready" if enabled else "Disabled",
                "Description": receipt["description"], "Enabled": enabled,
                "Actions": [{"Execute": receipt["execute"], "Arguments": receipt["arguments"], "WorkingDirectory": str(self.root)}],
                "Triggers": [{"Enabled": trigger}]}

    def args(self, *values):
        return adapter.parser().parse_args(values)

    def test_scheduler_and_runtime_commands_are_separate_and_exact(self):
        linux = self.receipt()
        windows = self.windows_receipt()
        for receipt in (linux, windows):
            self.assertEqual([receipt["python"], "-I", "-B", receipt["script"], "wake", "--owner", str(self.owner_path),
                              "--host-executable", receipt["host_executable"]], receipt["adapter_command"])
            self.assertEqual([receipt["python"], "-I", "-B", receipt["helper"], "wake", "--owner", str(self.owner_path),
                              "--host-command", receipt["host_executable"]], receipt["runtime_command"])
            self.assertNotEqual(receipt["adapter_command"], receipt["runtime_command"])
        service, _ = scheduler.linux_units(linux)
        self.assertIn("WorkingDirectory=", service)
        self.assertIn("WorkingDirectory=" + str(self.root), service)
        self.assertIn(scheduler.systemd_quote(str(ADAPTER.resolve())), service)
        self.assertNotIn(str(linux["helper"]), service)
        self.assertEqual(windows["execute"], windows["adapter_command"][0])
        self.assertIn(str(ADAPTER.resolve()), windows["arguments"])

    def test_linux_named_reordered_properties_are_owned_and_ready(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        self.assertTrue(scheduler.verify_linux_ownership(receipt, self.owner_path, self.owner, self.root, transport))
        self.assertTrue(scheduler.verify_linux(receipt, self.owner_path, self.owner, self.root, transport))
        self.assertTrue(any("--value" not in call for call in transport.calls if "show" in call))

    def test_linux_rejects_loaded_dropin_and_stale_path(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        transport.state["dropins"] = "/etc/systemd/user/foreign.conf"
        self.assertFalse(scheduler.verify_linux_ownership(receipt, self.owner_path, self.owner, self.root, transport))
        transport.state["dropins"] = ""
        transport.state["reload"] = "yes"
        self.assertFalse(scheduler.verify_linux_ownership(receipt, self.owner_path, self.owner, self.root, transport))

    @unittest.skipIf(os.name == "nt", "POSIX symlink identity; Windows has task-identity coverage")
    def test_linux_rejects_symlinked_unit_path(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        transport.state["reload"] = "no"
        Path(receipt["service_path"]).parent.mkdir(parents=True)
        Path(receipt["service_path"]).symlink_to(self.host)
        self.assertFalse(scheduler.verify_linux_ownership(receipt, self.owner_path, self.owner, self.root, transport))

    def test_ownership_allows_disabled_but_readiness_rejects_it_on_both_platforms(self):
        receipt = self.receipt()
        linux = LinuxTransport(receipt)
        self.put_linux(receipt, linux)
        linux.state.update(active="inactive", enabled="disabled")
        self.assertTrue(scheduler.verify_linux_ownership(receipt, self.owner_path, self.owner, self.root, linux))
        self.assertFalse(scheduler.verify_linux(receipt, self.owner_path, self.owner, self.root, linux))
        windows = self.windows_receipt()
        win = WindowsTransport(self.windows_task(windows, enabled=False))
        self.assertTrue(scheduler.verify_windows_ownership(windows, self.owner_path, self.owner, self.root, win))
        self.assertFalse(scheduler.verify_windows(windows, self.owner_path, self.owner, self.root, win))
        win.task["Enabled"] = True
        win.task["State"] = "Ready"
        win.task["Triggers"] = [{"Enabled": False}]
        self.assertFalse(scheduler.verify_windows(windows, self.owner_path, self.owner, self.root, win))

    def test_remove_disabled_linux_stops_timer_not_service_and_retains_evidence(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        transport.state.update(active="inactive", enabled="disabled")
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        result = adapter.remove(self.owner, self.root, self.owner_path, self.args("remove", "--owner", str(self.owner_path)), transport)
        self.assertTrue(result["removed"])
        self.assertFalse((self.owner_path.parent / "scheduler.json").exists())
        self.assertNotIn(receipt["service_path"], transport.files)
        self.assertNotIn(receipt["timer_path"], transport.files)
        self.assertTrue(any(call[:4] == ("systemctl", "--user", "disable", "--now") for call in transport.calls))
        self.assertFalse(any("stop" in call and receipt["service_unit"] in call for call in transport.calls))

    def test_disabled_owned_linux_registration_can_be_replaced(self):
        previous = self.receipt()
        proposed = self.receipt(10)
        transport = LinuxTransport(previous)
        self.put_linux(previous, transport)
        transport.state.update(active="inactive", enabled="disabled")
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", previous)
        arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", str(self.host),
                              "--interval-minutes", "10")
        with patch.object(adapter, "receipt_for", return_value=proposed):
            result = adapter.register(self.owner, self.root, self.owner_path, arguments, transport, windows=False)
        self.assertEqual(proposed["timer_unit"], result["registered"])
        self.assertEqual(proposed, json.loads((self.owner_path.parent / "scheduler.json").read_text(encoding="utf-8")))
        self.assertTrue(scheduler.verify_linux(proposed, self.owner_path, self.owner, self.root, transport))

    def test_missing_scheduler_allows_receipt_cleanup_without_foreign_mutation(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        result = adapter.remove(self.owner, self.root, self.owner_path, self.args("remove", "--owner", str(self.owner_path)), transport)
        self.assertTrue(result["removed"])
        self.assertFalse((self.owner_path.parent / "scheduler.json").exists())
        self.assertFalse(transport.calls)
        windows = self.windows_receipt()
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", windows)
        result = adapter.remove(self.owner, self.root, self.owner_path, self.args("remove", "--owner", str(self.owner_path)), WindowsTransport())
        self.assertTrue(result["removed"])

    def test_initial_partial_transaction_rolls_back_only_known_files(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        service, _ = scheduler.linux_units(receipt)
        transport.write(receipt["service_path"], service)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.pending.json", {"previous": None, "proposed": receipt})
        self.assertIsNone(scheduler.reconcile_pending(self.owner_path.parent / "scheduler.pending.json", self.owner_path.parent / "scheduler.json",
                                                       self.owner_path, self.owner, self.root, transport, windows=False))
        self.assertNotIn(receipt["service_path"], transport.files)
        self.assertTrue(any("disable" in call for call in transport.calls))

    def test_mixed_known_update_restores_previous_before_register(self):
        previous = self.receipt(20)
        proposed = scheduler.linux_receipt(self.owner, self.owner_path, self.root / "new adapter.py",
                                           ROOT / ".codex/runtime/continuation/continuation_runtime.py", sys.executable,
                                           self.host, 10, self.environment)
        transport = LinuxTransport(previous)
        old_service, old_timer = scheduler.linux_units(previous)
        _, new_timer = scheduler.linux_units(proposed)
        transport.write(previous["service_path"], old_service)
        transport.write(previous["timer_path"], new_timer)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", previous)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.pending.json", {"previous": previous, "proposed": proposed})
        result = scheduler.reconcile_pending(self.owner_path.parent / "scheduler.pending.json", self.owner_path.parent / "scheduler.json",
                                             self.owner_path, self.owner, self.root, transport, windows=False)
        self.assertEqual(previous, result)
        self.assertEqual(old_timer, transport.files[previous["timer_path"]])
        self.assertFalse((self.owner_path.parent / "scheduler.pending.json").exists())

    def test_unknown_transaction_evidence_is_preserved_and_dry_run_is_identical(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        transport.write(receipt["service_path"], "foreign")
        pending = self.owner_path.parent / "scheduler.pending.json"
        scheduler.atomic_json(pending, {"previous": None, "proposed": receipt})
        before = pending.read_bytes(), dict(transport.files)
        with self.assertRaisesRegex(scheduler.SchedulerError, "preserving"):
            scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json", self.owner_path, self.owner, self.root, transport, windows=False)
        self.assertEqual(before, (pending.read_bytes(), transport.files))
        with self.assertRaisesRegex(scheduler.SchedulerError, "preserving"):
            scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json", self.owner_path, self.owner, self.root, transport, windows=False, dry_run=True)
        self.assertEqual(before, (pending.read_bytes(), transport.files))

    def test_windows_task_identity_recovery_refuses_unknown_live_task_and_recovers_absent_previous(self):
        previous = self.windows_receipt()
        proposed = dict(previous)
        proposed["interval_minutes"] = 10
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", previous)
        pending = self.owner_path.parent / "scheduler.pending.json"
        scheduler.atomic_json(pending, {"previous": previous, "proposed": proposed})
        transport = WindowsTransport(self.windows_task(proposed))
        transport.task["Actions"][0]["Arguments"] = "foreign"
        with self.assertRaisesRegex(scheduler.SchedulerError, "preserving"):
            scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json", self.owner_path, self.owner, self.root, transport, windows=True)
        self.assertTrue(pending.exists())
        transport = WindowsTransport()
        resolved = scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json", self.owner_path, self.owner, self.root, transport, windows=True)
        self.assertEqual(previous, resolved)
        self.assertEqual(previous, json.loads((self.owner_path.parent / "scheduler.json").read_text(encoding="utf-8")))

    def test_windows_query_errors_preserve_transaction_evidence(self):
        receipt = self.windows_receipt()
        pending = self.owner_path.parent / "scheduler.pending.json"
        scheduler.atomic_json(pending, {"previous": None, "proposed": receipt})
        transport = WindowsTransport()
        transport.query_error = "access denied"
        before = pending.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "command failed"):
            scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json",
                                        self.owner_path, self.owner, self.root, transport, windows=True)
        self.assertEqual(before, pending.read_bytes())
        transport.query_error = None
        transport.query_invalid_json = True
        with self.assertRaisesRegex(RuntimeError, "invalid JSON"):
            scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json",
                                        self.owner_path, self.owner, self.root, transport, windows=True)
        self.assertEqual(before, pending.read_bytes())

    def test_windows_read_queries_allow_slow_valid_reads_and_reject_invalid_or_timed_out_tasks(self):
        receipt = self.windows_receipt()
        transport = WindowsTransport()
        transport.query_duration = 9
        arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", receipt["host_executable"])
        with patch.object(adapter, "receipt_for", return_value=receipt):
            result = adapter.register(self.owner, self.root, self.owner_path, arguments, transport, windows=True)
        self.assertEqual(receipt["task_name"], result["registered"])
        self.assertTrue(scheduler.verify_windows(receipt, self.owner_path, self.owner, self.root, transport))
        self.assertTrue(transport.query_timeouts)
        transport.registrations = [{"TaskName": receipt["task_name"]}]
        with patch.object(adapter.os, "name", "nt"):
            self.assertEqual([{"TaskName": receipt["task_name"]}], adapter.list_registrations(transport)["entries"])
        self.assertTrue(transport.inventory_timeouts)
        self.assertEqual({scheduler.WINDOWS_READ_QUERY_TIMEOUT},
                         set(transport.query_timeouts + transport.inventory_timeouts))

        transport.task["Actions"][0]["Arguments"] = "foreign"
        self.assertFalse(scheduler.verify_windows(receipt, self.owner_path, self.owner, self.root, transport))
        transport.task = self.windows_task(receipt, enabled=False)
        self.assertFalse(scheduler.verify_windows(receipt, self.owner_path, self.owner, self.root, transport))

        transport.query_duration = 16
        self.assertFalse(scheduler.verify_windows(receipt, self.owner_path, self.owner, self.root, transport))

    def test_a_receipt_without_a_recognized_platform_is_refused(self):
        arbitrary = {"version": 3, "owner_id": self.owner["owner_id"], "owner_path": str(self.owner_path),
                     "worktree": str(self.root), "task_name": "anything"}
        with self.assertRaisesRegex(scheduler.SchedulerError, "recognized platform"):
            scheduler.receipt_is_windows(arbitrary)

    def test_stale_receipt_survives_failed_reregistration_and_recovers_without_old_scheduler(self):
        stale = self.receipt()
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", stale)
        transport = LinuxTransport(stale)
        transport.fail_enable = True
        arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", str(self.host),
                              "--interval-minutes", "10")
        proposed = self.receipt(10)
        with patch.object(adapter, "receipt_for", return_value=proposed), \
             self.assertRaisesRegex(RuntimeError, "injected registration failure"):
            adapter.register(self.owner, self.root, self.owner_path, arguments, transport, windows=False)
        pending = json.loads((self.owner_path.parent / "scheduler.pending.json").read_text(encoding="utf-8"))
        self.assertEqual(stale, pending["previous"])
        self.assertTrue(pending["previous_missing"])
        transport.fail_enable = False
        with patch.object(adapter, "receipt_for", return_value=proposed):
            result = adapter.register(self.owner, self.root, self.owner_path, arguments, transport, windows=False)
        self.assertEqual("register", result["action"])
        self.assertFalse((self.owner_path.parent / "scheduler.pending.json").exists())

    def test_loaded_linux_recovery_evidence_is_prechecked_without_mutation(self):
        previous = self.receipt()
        proposed = self.receipt(10)
        transport = LinuxTransport(previous)
        self.put_linux(previous, transport)
        pending = self.owner_path.parent / "scheduler.pending.json"
        scheduler.atomic_json(pending, {"previous": previous, "proposed": proposed})
        before_files = dict(transport.files)
        transport.state["dropins"] = "/foreign/override.conf"
        with self.assertRaisesRegex(RuntimeError, "foreign loaded drop-ins"):
            scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json",
                                        self.owner_path, self.owner, self.root, transport, windows=False)
        self.assertTrue(pending.exists())
        self.assertEqual(before_files, transport.files)
        transport.state.update(dropins="", fragment="/foreign/fragment.service")
        with self.assertRaisesRegex(RuntimeError, "foreign loaded fragment"):
            scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json",
                                        self.owner_path, self.owner, self.root, transport, windows=False)
        self.assertTrue(pending.exists())
        transport.state.update(fragment=None)
        transport.state.update(reload="yes")
        result = scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json",
                                             self.owner_path, self.owner, self.root, transport, windows=False)
        self.assertEqual(previous, result)

    @unittest.skipIf(os.name == "nt", "POSIX enable-link identity; Windows has task-identity recovery coverage")
    def test_linux_recovery_rejects_foreign_enable_link(self):
        previous = self.receipt()
        proposed = self.receipt(10)
        transport = LinuxTransport(previous)
        self.put_linux(previous, transport)
        pending = self.owner_path.parent / "scheduler.pending.json"
        scheduler.atomic_json(pending, {"previous": previous, "proposed": proposed})
        link = Path(previous["timer_enable_path"])
        link.parent.mkdir(parents=True)
        link.symlink_to(self.root / "foreign.timer")
        with self.assertRaisesRegex(RuntimeError, "enable link"):
            scheduler.reconcile_pending(pending, self.owner_path.parent / "scheduler.json",
                                        self.owner_path, self.owner, self.root, transport, windows=False)
        self.assertTrue(pending.exists())

    @unittest.skipIf(os.name == "nt", "POSIX symlink filesystem identity; Windows has task-identity coverage")
    def test_linux_refuses_enable_link_that_only_lexically_targets_the_timer(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        target = Path(receipt["timer_path"])
        target.parent.mkdir(parents=True)
        target.write_text("timer", encoding="utf-8")
        link = Path(receipt["timer_enable_path"])
        foreign = Path(self.temp.name) / "foreign"
        (foreign / "subdir").mkdir(parents=True)
        foreign_target = foreign / target.name
        foreign_target.write_text("foreign timer", encoding="utf-8")
        alias = link.parent.parent / "alias"
        alias.symlink_to(foreign / "subdir", target_is_directory=True)
        link.parent.mkdir()
        link.symlink_to("../alias/../" + target.name)

        apparent = link.parent / os.readlink(link)
        self.assertEqual(os.path.normpath(str(target)), os.path.normpath(str(apparent)))
        self.assertEqual(foreign_target.resolve(), apparent.resolve())
        self.assertFalse(scheduler._link_points_to(link, target))
        self.assertFalse(scheduler.verify_linux_ownership(receipt, self.owner_path, self.owner, self.root, transport))

        receipt_path = self.owner_path.parent / "scheduler.json"
        pending_path = self.owner_path.parent / "scheduler.pending.json"
        scheduler.atomic_json(receipt_path, receipt)
        before_files = dict(transport.files)
        arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", str(self.host))
        with patch.object(adapter, "receipt_for", return_value=receipt), \
             self.assertRaisesRegex(RuntimeError, "exact ownership receipt"):
            adapter.register(self.owner, self.root, self.owner_path, arguments, transport, windows=False)
        self.assertEqual(before_files, transport.files)
        self.assertFalse(pending_path.exists())

        scheduler.atomic_json(pending_path, {"previous": receipt, "proposed": receipt})
        before_pending = pending_path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "enable link"):
            scheduler.reconcile_pending(pending_path, receipt_path, self.owner_path, self.owner, self.root,
                                        transport, windows=False)
        self.assertEqual(before_pending, pending_path.read_bytes())
        self.assertEqual(before_files, transport.files)
        with self.assertRaisesRegex(RuntimeError, "enable link"):
            adapter.remove(self.owner, self.root, self.owner_path,
                           self.args("remove", "--owner", str(self.owner_path)), transport)
        self.assertEqual(before_pending, pending_path.read_bytes())
        self.assertEqual(before_files, transport.files)

        pending_path.unlink()
        before_receipt = receipt_path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "exact ownership receipt"):
            adapter.remove(self.owner, self.root, self.owner_path,
                           self.args("remove", "--owner", str(self.owner_path)), transport)
        self.assertEqual(before_receipt, receipt_path.read_bytes())
        self.assertEqual(before_files, transport.files)
        self.assertFalse(any(any(operation in call for operation in ("disable", "enable", "daemon-reload"))
                             for call in transport.calls))

    def test_linux_registration_refuses_foreign_loaded_evidence_before_mutation(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        transport.state["dropins"] = "/foreign/override.conf"
        arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", str(self.host))
        with patch.object(adapter, "receipt_for", return_value=receipt), \
             self.assertRaisesRegex(RuntimeError, "foreign loaded drop-ins"):
            adapter.register(self.owner, self.root, self.owner_path, arguments, transport, windows=False)
        self.assertFalse(transport.files)
        self.assertFalse((self.owner_path.parent / "scheduler.pending.json").exists())

    def test_linux_registration_rechecks_ownership_after_reload_before_enabling(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        transport.foreign_after_reload = {"dropins": "/foreign/override.conf"}
        arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", str(self.host))
        with patch.object(adapter, "receipt_for", return_value=receipt), \
             self.assertRaisesRegex(RuntimeError, "after reload"):
            adapter.register(self.owner, self.root, self.owner_path, arguments, transport, windows=False)
        self.assertFalse(any("enable" in call for call in transport.calls))
        self.assertTrue((self.owner_path.parent / "scheduler.pending.json").exists())

    def test_linux_recovery_rechecks_restored_ownership_after_reload_before_enabling(self):
        previous = self.receipt()
        proposed = scheduler.linux_receipt(self.owner, self.owner_path, self.root / "new adapter.py",
                                           ROOT / ".codex/runtime/continuation/continuation_runtime.py", sys.executable,
                                           self.host, 10, self.environment)
        transport = LinuxTransport(previous)
        old_service, _ = scheduler.linux_units(previous)
        _, new_timer = scheduler.linux_units(proposed)
        transport.write(previous["service_path"], old_service)
        transport.write(previous["timer_path"], new_timer)
        transport.foreign_after_reload = {"dropins": "/foreign/override.conf"}
        receipt_path = self.owner_path.parent / "scheduler.json"
        pending = self.owner_path.parent / "scheduler.pending.json"
        scheduler.atomic_json(receipt_path, previous)
        scheduler.atomic_json(pending, {"previous": previous, "proposed": proposed})
        before_receipt = receipt_path.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "restored scheduler differs"):
            scheduler.reconcile_pending(pending, receipt_path, self.owner_path, self.owner, self.root,
                                        transport, windows=False)
        self.assertFalse(any("enable" in call for call in transport.calls))
        self.assertEqual(before_receipt, receipt_path.read_bytes())
        self.assertTrue(pending.exists())

    @unittest.skipIf(os.name == "nt", "POSIX symlink filesystem identity; Windows has task-identity coverage")
    def test_linux_paths_keep_final_components_lexical_and_reject_symlinks_before_writes(self):
        real_config = Path(self.temp.name) / "real config"
        linked_config = Path(self.temp.name) / "linked config"
        real_config.mkdir()
        linked_config.symlink_to(real_config, target_is_directory=True)
        receipt = scheduler.linux_receipt(self.owner, self.owner_path, ADAPTER,
                                          ROOT / ".codex/runtime/continuation/continuation_runtime.py", sys.executable,
                                          self.host, 20, {"XDG_CONFIG_HOME": str(linked_config)})
        self.assertEqual(real_config.resolve() / "systemd/user", Path(receipt["unit_directory"]))
        self.assertEqual(Path(receipt["unit_directory"]) / receipt["timer_unit"], Path(receipt["timer_path"]))
        target = Path(receipt["timer_path"])
        target.parent.mkdir(parents=True)
        target.write_text("timer", encoding="utf-8")
        link = Path(receipt["timer_enable_path"])
        link.parent.mkdir()
        link.symlink_to(target)
        self.assertTrue(scheduler._link_points_to(link, target))
        link.unlink()
        external = self.root / "outside"
        Path(receipt["service_path"]).parent.mkdir(parents=True, exist_ok=True)
        Path(receipt["service_path"]).symlink_to(external)
        self.assertEqual(Path(receipt["unit_directory"]) / receipt["service_unit"], Path(receipt["service_path"]))
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            adapter.write_linux(receipt, self.owner_path, self.owner, self.root, LinuxTransport(receipt))

    def test_unpinned_registration_binds_host_to_linux_and_windows_actions(self):
        arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", str(self.host))
        linux_receipt = self.receipt()
        linux = LinuxTransport(linux_receipt)
        with patch.object(adapter, "receipt_for", return_value=linux_receipt):
            linux_result = adapter.register(self.owner, self.root, self.owner_path, arguments, linux, windows=False)
        self.assertEqual("register", linux_result["action"])
        stored = json.loads((self.owner_path.parent / "scheduler.json").read_text(encoding="utf-8"))
        self.assertEqual(["--host-executable", str(self.host.resolve())], stored["adapter_command"][-2:])
        adapter.remove(self.owner, self.root, self.owner_path, self.args("remove", "--owner", str(self.owner_path)), linux)
        windows_host = self.root / "explicit.exe"
        windows_host.write_text("native", encoding="utf-8")
        windows = WindowsTransport()
        windows_arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", str(windows_host))
        windows_receipt = scheduler.windows_receipt(self.owner, self.owner_path, ADAPTER,
                                                    ROOT / ".codex/runtime/continuation/continuation_runtime.py", sys.executable,
                                                    windows_host, 20, self.environment)
        with patch.object(adapter, "receipt_for", return_value=windows_receipt):
            windows_result = adapter.register(self.owner, self.root, self.owner_path, windows_arguments, windows, windows=True)
        self.assertEqual("register", windows_result["action"])
        self.assertIn("--host-executable", windows.task["Actions"][0]["Arguments"])
        replacement = dict(windows_receipt)
        replacement["interval_minutes"] = 10
        replacement_arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", str(windows_host),
                                          "--interval-minutes", "10")
        with patch.object(adapter, "receipt_for", return_value=replacement):
            replacement_result = adapter.register(self.owner, self.root, self.owner_path,
                                                  replacement_arguments, windows, windows=True)
        self.assertEqual("register", replacement_result["action"])
        self.assertEqual(10, json.loads((self.owner_path.parent / "scheduler.json").read_text(encoding="utf-8"))["interval_minutes"])

    def test_receipt_only_host_substitution_is_rejected_on_both_platforms(self):
        alternate = self.root / "alternate host"
        alternate.write_text("#!/bin/sh\n", encoding="utf-8")
        alternate.chmod(alternate.stat().st_mode | stat.S_IXUSR)
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        receipt["host_executable"] = str(alternate.resolve())
        receipt["adapter_command"] = scheduler.adapter_command(receipt)
        receipt["runtime_command"] = scheduler.runtime_command(receipt)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        with self.assertRaisesRegex(RuntimeError, "host executable"):
            adapter.wake(self.owner, self.root, self.owner_path,
                         self.args("wake", "--owner", str(self.owner_path), "--host-executable", str(self.host)), transport)
        windows = self.windows_receipt()
        windows_transport = WindowsTransport(self.windows_task(windows))
        alternate_windows = self.root / "alternate.exe"
        alternate_windows.write_text("native", encoding="utf-8")
        windows["host_executable"] = str(alternate_windows.resolve())
        windows["adapter_command"] = scheduler.adapter_command(windows)
        windows["runtime_command"] = scheduler.runtime_command(windows)
        self.owner["host_executable"] = str((self.root / "native host.exe").resolve())
        self.owner_path.write_text(json.dumps(self.owner), encoding="utf-8")
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", windows)
        with self.assertRaisesRegex(RuntimeError, "host executable"):
            adapter.wake(self.owner, self.root, self.owner_path,
                         self.args("wake", "--owner", str(self.owner_path), "--host-executable", self.owner["host_executable"]),
                         windows_transport)

    def test_windows_v3_rejects_changed_host_command_with_stale_registered_action_before_launch(self):
        receipt = self.windows_receipt()
        transport = WindowsTransport(self.windows_task(receipt))
        alternate = self.root / "alternate.exe"
        alternate.write_text("native", encoding="utf-8")
        receipt["host_executable"] = str(alternate.resolve())
        receipt["adapter_command"] = scheduler.adapter_command(receipt)
        receipt["runtime_command"] = scheduler.runtime_command(receipt)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        with patch.object(adapter.subprocess, "run") as runtime:
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                adapter.wake(self.owner, self.root, self.owner_path,
                             self.args("wake", "--owner", str(self.owner_path), "--host-executable", str(alternate)),
                             transport)
        runtime.assert_not_called()

    def test_outer_scheduler_timeout_keeps_adapter_and_child_budgets(self):
        receipt = self.receipt()
        service, _ = scheduler.linux_units(receipt)
        self.assertIn("TimeoutStartSec=7200", service)
        self.assertIn("ExecutionTimeLimit (New-TimeSpan -Seconds 7200)", scheduler.WINDOWS_SCRIPT)
        self.assertIn("timeout=930", ADAPTER.read_text(encoding="utf-8"))

    def test_python_version_guard_runs_before_scheduler_import(self):
        with patch.object(sys, "version_info", (3, 8, 0)):
            with self.assertRaisesRegex(RuntimeError, "Python 3.9"):
                load("delivery_continuation_python38", ADAPTER)

    def test_windows_registration_and_cleanup_are_exact_without_runtime_recursion(self):
        receipt = self.windows_receipt()
        transport = WindowsTransport()
        adapter.write_windows(receipt, transport)
        self.assertTrue(scheduler.verify_windows(receipt, self.owner_path, self.owner, self.root, transport))
        self.assertEqual(receipt["adapter_command"][0], transport.task["Actions"][0]["Execute"])
        self.assertIn(str(ADAPTER.resolve()), transport.task["Actions"][0]["Arguments"])
        self.assertNotIn(str(receipt["helper"]), transport.task["Actions"][0]["Arguments"])
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        result = adapter.remove(self.owner, self.root, self.owner_path, self.args("remove", "--owner", str(self.owner_path)), transport)
        self.assertTrue(result["removed"])
        self.assertIsNone(transport.task)

    def test_post_registration_receipt_failure_retains_pending_and_concurrent_lock_is_rejected(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        arguments = self.args("register", "--owner", str(self.owner_path), "--host-executable", str(self.host))
        original = adapter.scheduler.atomic_json

        def fail_receipt(path, value):
            if Path(path).name == "scheduler.json":
                raise OSError("injected receipt write failure")
            return original(path, value)

        with patch.object(adapter, "receipt_for", return_value=receipt), patch.object(adapter.scheduler, "atomic_json", side_effect=fail_receipt):
            with self.assertRaisesRegex(OSError, "receipt"):
                adapter.register(self.owner, self.root, self.owner_path, arguments, transport, windows=False)
        self.assertTrue((self.owner_path.parent / "scheduler.pending.json").exists())
        with scheduler.lifecycle_lock(self.owner_path.parent) as first:
            self.assertTrue(first)
            with scheduler.lifecycle_lock(self.owner_path.parent) as second:
                self.assertFalse(second)

    def test_adapter_wake_runs_runtime_once_and_terminal_cleanup_never_stops_service(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        self.owner["state"] = "complete"
        self.owner_path.write_text(json.dumps(self.owner), encoding="utf-8")
        calls = []
        with patch.object(adapter.subprocess, "run", side_effect=lambda *args, **kwargs: calls.append((args, kwargs)) or Result()), \
             patch.object(adapter, "read_json", side_effect=[receipt, self.owner, FileNotFoundError]):
            result = adapter.wake(self.owner, self.root, self.owner_path,
                                  self.args("wake", "--owner", str(self.owner_path), "--host-executable", str(self.host)), transport)
        self.assertEqual("complete", result["state"])
        self.assertEqual(receipt["runtime_command"], calls[0][0][0])
        self.assertEqual("/safe profile £", calls[0][1]["env"]["CODEX_HOME"])
        self.assertNotIn("CONTINUATION_NONCE", calls[0][1]["env"])
        self.assertFalse((self.owner_path.parent / "scheduler.json").exists())
        self.assertFalse(any("stop" in call and receipt["service_unit"] in call for call in transport.calls))

    def test_terminal_cleanup_retains_foreign_pending_evidence(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        scheduler.atomic_json(self.owner_path.parent / "scheduler.pending.json",
                              {"previous": None, "proposed": {"owner_id": "foreign"}})
        self.owner["state"] = "complete"
        self.owner_path.write_text(json.dumps(self.owner), encoding="utf-8")
        with patch.object(adapter.subprocess, "run", return_value=Result()):
            with self.assertRaisesRegex(RuntimeError, "foreign pending"):
                adapter.wake(self.owner, self.root, self.owner_path,
                             self.args("wake", "--owner", str(self.owner_path), "--host-executable", str(self.host)), transport)
        self.assertTrue((self.owner_path.parent / "scheduler.json").exists())
        self.assertTrue((self.owner_path.parent / "scheduler.pending.json").exists())

    def test_wake_rejects_stale_adapter_path_and_disabled_scheduler(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        receipt["script"] = str(self.root / "stale adapter.py")
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        with self.assertRaisesRegex(RuntimeError, "pinned script"):
            adapter.wake(self.owner, self.root, self.owner_path,
                         self.args("wake", "--owner", str(self.owner_path), "--host-executable", str(self.host)), transport)
        receipt = self.receipt()
        self.put_linux(receipt, transport)
        transport.state.update(active="inactive", enabled="disabled")
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        with self.assertRaisesRegex(RuntimeError, "unavailable"):
            adapter.wake(self.owner, self.root, self.owner_path,
                         self.args("wake", "--owner", str(self.owner_path), "--host-executable", str(self.host)), transport)

    def test_posix_and_windows_native_pin_refusals(self):
        bad = self.root / "not executable"
        bad.write_text("x", encoding="utf-8")
        with patch.object(adapter.os, "access", return_value=False), self.assertRaisesRegex(RuntimeError, "execute"):
            adapter.existing_host(self.owner, str(bad), windows=False)
        command = self.root / "host.cmd"
        command.write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "native .exe"):
            adapter.existing_host(self.owner, str(command), windows=True)
        with self.assertRaisesRegex(RuntimeError, "missing"):
            adapter.load_owner(self.owner_path.parent)

    def test_windows_profile_changes_require_the_registered_description_to_match(self):
        receipt = self.windows_receipt()
        transport = WindowsTransport(self.windows_task(receipt))
        self.assertTrue(scheduler.verify_windows(receipt, self.owner_path, self.owner, self.root, transport))
        receipt["profile_environment"]["CODEX_HOME"] = "/unregistered profile"
        self.assertFalse(scheduler.verify_windows(receipt, self.owner_path, self.owner, self.root, transport))
        receipt["description"] = scheduler.windows_description(receipt)
        self.assertFalse(scheduler.verify_windows(receipt, self.owner_path, self.owner, self.root, transport))
        transport.task["Description"] = receipt["description"]
        self.assertTrue(scheduler.verify_windows(receipt, self.owner_path, self.owner, self.root, transport))

    def test_registered_agent_cli_resolves_without_the_interactive_environment(self):
        directory = self.root / "agent bin"
        directory.mkdir()
        shim = directory / ("gh.exe" if os.name == "nt" else "gh")
        shim.write_text("fixture", encoding="utf-8")
        shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
        isolated = str(self.root / "isolated github config")
        self.environment.update(PATH=str(directory), TJ_AGENT="1", GH_CONFIG_DIR=isolated)
        for receipt in (self.receipt(), self.windows_receipt()):
            with self.subTest(platform=receipt["platform"]):
                self.assertNotIn("GH_TOKEN", receipt["profile_environment"])
                with patch.dict(os.environ, {"PATH": str(self.root / "ambient bin"), "TJ_AGENT": "0",
                                             "GH_CONFIG_DIR": str(self.root / "ambient config")}):
                    environment = adapter.wake_environment(receipt)
                result = subprocess.run([sys.executable, "-I", "-c",
                    "import json,os,shutil;print(json.dumps([shutil.which('gh'),os.environ['TJ_AGENT'],os.environ['GH_CONFIG_DIR']]))"],
                    env=environment, capture_output=True, text=True, timeout=10)
                self.assertEqual(0, result.returncode, result.stderr)
                resolved, flag, configuration = json.loads(result.stdout)
                self.assertIsNotNone(resolved)
                self.assertEqual(shim, Path(resolved))
                self.assertEqual(["1", isolated], [flag, configuration])

    def test_installed_package_resources_and_custom_profile_are_portable(self):
        package = (Path(self.temp.name) / "installed package £").resolve()
        scripts = package / ".codex/runtime/continuation"
        resources = package / ".codex/runtime/continuation"
        scripts.mkdir(parents=True)
        resources.mkdir(parents=True, exist_ok=True)
        (package / ".codex-plugin").mkdir()
        (package / ".codex-plugin/plugin.json").write_text("{}")
        (package / ".agents/engineering").mkdir(parents=True)
        shutil.copy2(ADAPTER, scripts / ADAPTER.name)
        shutil.copy2(SCHEDULER, resources / SCHEDULER.name)
        shutil.copy2(ROOT / ".codex/runtime/continuation/continuation_runtime.py", resources / "continuation_runtime.py")
        installed = load("installed_delivery_continuation", scripts / ADAPTER.name)
        self.assertEqual(resources / "continuation_scheduler.py", installed.resource("continuation_scheduler.py"))
        self.assertEqual(resources / "continuation_runtime.py", installed.resource("continuation_runtime.py"))
        receipt = self.receipt()
        self.assertEqual("/safe profile £", receipt["profile_environment"]["CODEX_HOME"])
        self.assertNotIn("GH_TOKEN", receipt["profile_environment"])

    def test_generated_continuation_transport_is_codex_only(self):
        package = ROOT / "plugins/engineering"
        self.assertTrue((package / ".codex/runtime/continuation/delivery_continuation.py").is_file())
        self.assertTrue((package / ".codex/runtime/continuation/continuation_runtime.py").is_file())
        self.assertTrue((package / ".codex/runtime/continuation/continuation_scheduler.py").is_file())
        self.assertFalse((package / "skills/continue/scripts").exists())
        self.assertFalse((package / ".agents/workflow/workflow/continue/scripts").exists())
        self.assertFalse((package / "workflows/continuation_runtime.py").exists())
        installed = load("generated_delivery_continuation",
                         package / ".codex/runtime/continuation/delivery_continuation.py")
        for module in (adapter, installed):
            runtime, python = module.prerequisites(self.owner, str(self.host))
            self.assertEqual(module.package_root() / ".codex/runtime/continuation/continuation_runtime.py", runtime)
            self.assertEqual(Path(sys.executable).resolve(), python)

    def test_runtime_does_not_use_outer_package_marker_or_shared_resources(self):
        outer = self.root / "outer-runtime"
        resources = outer / ".codex/runtime/continuation"
        resources.mkdir(parents=True, exist_ok=True)
        (outer / ".codex-plugin").mkdir()
        (outer / ".codex-plugin/plugin.json").write_text("{}")
        (outer / ".agents/engineering").mkdir(parents=True)
        shutil.copytree(ROOT / ".agents/workflows", outer / "workflows")
        nested = outer / "nested"
        runtime = nested / ".codex/runtime/continuation/continuation_runtime.py"
        runtime.parent.mkdir(parents=True)
        (nested / ".agents/engineering").mkdir(parents=True)
        shutil.copy2(ROOT / ".codex/runtime/continuation/continuation_runtime.py", runtime)
        result = subprocess.run([sys.executable, "-B", str(runtime), "--help"],
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("package root unavailable", result.stderr)
        (nested / ".codex-plugin").mkdir()
        (nested / ".codex-plugin/plugin.json").write_text("{}")
        result = subprocess.run([sys.executable, "-B", str(runtime), "--help"],
                                capture_output=True, text=True, timeout=10)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("shared runtime unavailable", result.stderr)

    def test_adapter_rejects_claude_layout(self):
        scripts = self.root / "skills/continue/scripts"
        scripts.mkdir(parents=True)
        shutil.copy2(ADAPTER, scripts / ADAPTER.name)
        with self.assertRaisesRegex(RuntimeError, "adapter layout unavailable"):
            load("claude_delivery_continuation", scripts / ADAPTER.name)

    def test_adapter_does_not_use_outer_package_resources_or_marker(self):
        outer = self.root / "outer"
        for package in (outer, outer / "nested"):
            scripts = package / ".codex/runtime/continuation"
            scripts.mkdir(parents=True)
            (package / ".agents/engineering").mkdir(parents=True)
            (package / ".codex-plugin").mkdir()
            (package / ".codex-plugin/plugin.json").write_text("{}")
            shutil.copy2(ADAPTER, scripts / ADAPTER.name)
        resources = outer / ".codex/runtime/continuation"
        resources.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SCHEDULER, resources / SCHEDULER.name)
        nested = outer / "nested"
        script = nested / ".codex/runtime/continuation" / ADAPTER.name
        with self.assertRaisesRegex(RuntimeError, "resource unavailable"):
            load("nested_delivery_continuation", script)
        (nested / ".codex-plugin/plugin.json").unlink()
        with self.assertRaisesRegex(RuntimeError, "package root unavailable"):
            load("unmarked_delivery_continuation", script)

    def test_adapter_rejects_existing_claude_owner(self):
        owner = json.loads(self.owner_path.read_text())
        owner["harness"] = "claude"
        self.owner_path.write_text(json.dumps(owner))
        with self.assertRaisesRegex(adapter.scheduler.SchedulerError, "invalid continuation runtime owner"):
            adapter.load_owner(self.owner_path)

    @unittest.skipUnless(os.name == "nt", "requires inbox Windows PowerShell")
    def test_inbox_powershell_json_transport_is_utf8_without_registration(self):
        payload = json.dumps({"path": "C:\\space £\\owner.json"}, ensure_ascii=False)
        command = "[Console]::InputEncoding=[Text.UTF8Encoding]::new($false);[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);$x=[Console]::In.ReadToEnd()|ConvertFrom-Json;$x|ConvertTo-Json -Compress"
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command], input=payload,
                                text=True, encoding="utf-8", capture_output=True, check=False)
        self.assertEqual(0, result.returncode)
        self.assertEqual(json.loads(payload), json.loads(result.stdout))

    @unittest.skipUnless(os.name == "nt" or shutil.which("pwsh"),
                         "requires inbox Windows PowerShell on Windows or the repository pwsh prerequisite on Linux")
    def test_powershell_query_returns_case_variant_and_absence_without_registration(self):
        receipt = self.windows_receipt()
        command = (
            "function Get-ScheduledTask { param([string]$TaskPath) "
            "if($PSBoundParameters.ContainsKey('TaskPath')){throw 'enumerate tasks before filtering'};"
            "[pscustomobject]@{TaskName='" + receipt["task_name"].lower() + "';TaskPath=$payload.fixture_task_path;State='Ready';"
            "Description='foreign';Actions=@([pscustomobject]@{Execute='x';Arguments='y';WorkingDirectory='z'});"
            "Triggers=@([pscustomobject]@{Enabled=$true});Settings=[pscustomobject]@{Enabled=$true}} };"
            + scheduler.WINDOWS_SCRIPT
        )
        executable = "powershell.exe" if os.name == "nt" else "pwsh"
        for task_path in ("\\", "\\foreign\\"):
            result = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-Command", command],
                                    input=json.dumps({"operation": "query", "task_name": receipt["task_name"],
                                                      "fixture_task_path": task_path}),
                                    text=True, encoding="utf-8", capture_output=True, check=False)
            self.assertEqual(0, result.returncode, result.stderr)
            if task_path == "\\":
                self.assertEqual(receipt["task_name"].lower(), json.loads(result.stdout)["TaskName"])
            else:
                self.assertIsNone(json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
