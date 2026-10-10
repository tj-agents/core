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
ADAPTER = ROOT / ".agents/engineering/workflow/persistent-workflow/scripts/delivery_continuation.py"
SCHEDULER = ROOT / ".agents/workflows/continuation_scheduler.py"


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
        self.state = {"active": "active", "enabled": "enabled", "dropins": "", "reload": "no"}

    def run(self, args, **kwargs):
        self.calls.append(tuple(args))
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
            values = {"FragmentPath": path, "NeedDaemonReload": self.state["reload"], "LoadState": "loaded",
                      "DropInPaths": self.state["dropins"], "ActiveState": self.state["active"],
                      "UnitFileState": self.state["enabled"]}
            return Result("\n".join(key + "=" + values[key] for key in
                                      ("NeedDaemonReload", "FragmentPath", "UnitFileState", "DropInPaths", "LoadState", "ActiveState")) + "\n")
        return Result()

    def write(self, path, text):
        self.files[str(path)] = text

    def read(self, path):
        return self.files[str(path)]

    def remove(self, path):
        self.files.pop(str(path), None)


class WindowsTransport(scheduler.SchedulerTransport):
    def __init__(self, task=None):
        self.task = task
        self.calls = []
        self.fail_register = False

    def run(self, args, **kwargs):
        self.calls.append(tuple(args))
        payload = json.loads(kwargs.get("input_text") or "{}")
        operation = payload.get("operation")
        if operation == "query":
            if self.task is None:
                return Result(returncode=1, stderr="not found")
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
        self.root = Path(self.temp.name) / "work tree £"
        self.root.mkdir()
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
        return scheduler.linux_receipt(self.owner, self.owner_path, ADAPTER, ROOT / ".agents/workflows/continuation_runtime.py",
                                       sys.executable, self.host, interval, self.environment)

    def windows_receipt(self):
        host = self.root / "native host.exe"
        host.write_text("native", encoding="utf-8")
        return scheduler.windows_receipt(self.owner, self.owner_path, ADAPTER, ROOT / ".agents/workflows/continuation_runtime.py",
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
            self.assertEqual([receipt["python"], "-I", "-B", receipt["script"], "wake", "--owner", str(self.owner_path)], receipt["adapter_command"])
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

    def test_linux_rejects_loaded_dropin_stale_path_and_symlink(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        transport.state["dropins"] = "/etc/systemd/user/foreign.conf"
        self.assertFalse(scheduler.verify_linux_ownership(receipt, self.owner_path, self.owner, self.root, transport))
        transport.state["dropins"] = ""
        transport.state["reload"] = "yes"
        self.assertFalse(scheduler.verify_linux_ownership(receipt, self.owner_path, self.owner, self.root, transport))
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
            result = adapter.register(self.owner, self.root, self.owner_path, arguments, transport)
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
                                           ROOT / ".agents/workflows/continuation_runtime.py", sys.executable,
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

    def test_windows_transaction_refuses_unknown_live_task_and_recovers_absent_previous(self):
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
                adapter.register(self.owner, self.root, self.owner_path, arguments, transport)
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
            result = adapter.wake(self.owner, self.root, self.owner_path, self.args("wake", "--owner", str(self.owner_path)), transport)
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
                adapter.wake(self.owner, self.root, self.owner_path, self.args("wake", "--owner", str(self.owner_path)), transport)
        self.assertTrue((self.owner_path.parent / "scheduler.json").exists())
        self.assertTrue((self.owner_path.parent / "scheduler.pending.json").exists())

    def test_wake_rejects_stale_adapter_path_and_disabled_scheduler(self):
        receipt = self.receipt()
        transport = LinuxTransport(receipt)
        self.put_linux(receipt, transport)
        receipt["script"] = str(self.root / "stale adapter.py")
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        with self.assertRaisesRegex(RuntimeError, "pinned script"):
            adapter.wake(self.owner, self.root, self.owner_path, self.args("wake", "--owner", str(self.owner_path)), transport)
        receipt = self.receipt()
        self.put_linux(receipt, transport)
        transport.state.update(active="inactive", enabled="disabled")
        scheduler.atomic_json(self.owner_path.parent / "scheduler.json", receipt)
        with self.assertRaisesRegex(RuntimeError, "unavailable"):
            adapter.wake(self.owner, self.root, self.owner_path, self.args("wake", "--owner", str(self.owner_path)), transport)

    def test_posix_and_windows_native_pin_refusals(self):
        bad = self.root / "not executable"
        bad.write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "execute"):
            adapter.existing_host(self.owner, str(bad))
        command = self.root / "host.cmd"
        command.write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "native .exe"):
            adapter.existing_host(self.owner, str(command), windows=True)
        with self.assertRaisesRegex(RuntimeError, "missing"):
            adapter.load_owner(self.owner_path.parent)

    def test_installed_package_resources_and_custom_profile_are_portable(self):
        package = Path(self.temp.name) / "installed package £"
        scripts, workflows = package / "skills/persistent-workflow/scripts", package / "workflows"
        scripts.mkdir(parents=True)
        workflows.mkdir()
        shutil.copy2(ADAPTER, scripts / ADAPTER.name)
        shutil.copy2(SCHEDULER, workflows / SCHEDULER.name)
        shutil.copy2(ROOT / ".agents/workflows/continuation_runtime.py", workflows / "continuation_runtime.py")
        installed = load("installed_delivery_continuation", scripts / ADAPTER.name)
        self.assertEqual(workflows / "continuation_scheduler.py", installed.resource("continuation_scheduler.py"))
        self.assertEqual(workflows / "continuation_runtime.py", installed.resource("continuation_runtime.py"))
        receipt = self.receipt()
        self.assertEqual("/safe profile £", receipt["profile_environment"]["CODEX_HOME"])
        self.assertNotIn("GH_TOKEN", receipt["profile_environment"])

    @unittest.skipUnless(os.name == "nt", "requires inbox Windows PowerShell")
    def test_inbox_powershell_json_transport_is_utf8_without_registration(self):
        payload = json.dumps({"path": "C:\\space £\\owner.json"}, ensure_ascii=False)
        command = "[Console]::InputEncoding=[Text.UTF8Encoding]::new($false);[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);$x=[Console]::In.ReadToEnd()|ConvertFrom-Json;$x|ConvertTo-Json -Compress"
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command], input=payload,
                                text=True, encoding="utf-8", capture_output=True, check=False)
        self.assertEqual(0, result.returncode)
        self.assertEqual(json.loads(payload), json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
