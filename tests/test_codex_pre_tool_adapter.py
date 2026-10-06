import ctypes
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / ".codex" / "adapters" / "pre_tool_use.py"


class CodexPreToolAdapter(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="adapter test ", dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def script(self, source):
        script = self.root / "hook with spaces.py"
        script.write_text(source, encoding="utf-8")
        return script

    def launch(self, source, timeout=1.5):
        script = self.script(source)
        process = subprocess.Popen(
            [sys.executable, "-B", str(ADAPTER), "--timeout", str(timeout), str(script)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.addCleanup(self.close_process, process)
        return process

    @staticmethod
    def close_process(process):
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream:
                stream.close()

    def decision(self, stdout):
        decision = json.loads(stdout)["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        return decision["permissionDecisionReason"]

    def test_complete_input_executes_without_eof_and_preserves_unicode(self):
        process = self.launch(
            "import json, sys\n"
            "value = json.load(sys.stdin)\n"
            "sys.stdout.buffer.write(json.dumps(value, ensure_ascii=False).encode('utf-8'))\n"
            "sys.stderr.buffer.write('évidence'.encode('utf-8'))\n"
        )
        payload = {"text": 'café 雪 } { \\"', "nested": [{"x": 1}]}
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        for chunk in (encoded[:14], encoded[14:15], encoded[15:]):
            process.stdin.write(chunk)
            process.stdin.flush()
        process.wait(timeout=4)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(json.loads(process.stdout.read()), payload)
        self.assertEqual(process.stderr.read().decode("utf-8"), "évidence")

    def test_incomplete_held_open_input_denies_within_deadline(self):
        marker = self.root / "executed"
        process = self.launch(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        started = time.monotonic()
        process.stdin.write(b'{"tool_name":')
        process.stdin.flush()
        process.wait(timeout=4)
        self.assertLess(time.monotonic() - started, 3)
        reason = self.decision(process.stdout.read())
        self.assertIn("input", reason)
        self.assertIn("hook with spaces.py", reason)
        self.assertFalse(marker.exists())

    def test_invalid_input_denies_without_launching_hook(self):
        for payload in (b"[]", b'{"x":broken}', b'{"x":"\xff"}', b'{} trailing'):
            with self.subTest(payload=payload):
                process = self.launch("raise AssertionError('must not execute')\n")
                stdout, stderr = process.communicate(payload, timeout=4)
                self.assertEqual(process.returncode, 0, stderr)
                self.assertIn("input", self.decision(stdout))

    def test_hung_child_denies_within_deadline(self):
        process = self.launch("import time\ntime.sleep(60)\n")
        started = time.monotonic()
        stdout, stderr = process.communicate(b"{}", timeout=4)
        self.assertEqual(process.returncode, 0, stderr)
        self.assertLess(time.monotonic() - started, 3)
        self.assertIn("child execution/output collection", self.decision(stdout))

    def test_grandchild_holding_output_is_terminated(self):
        pid_file = self.root / "grandchild.pid"
        heartbeat = self.root / "heartbeat"
        child_code = (
            "import os,time\nfrom pathlib import Path\n"
            f"Path({str(pid_file)!r}).write_text(str(os.getpid()))\n"
            "while True:\n"
            f" Path({str(heartbeat)!r}).write_text(str(time.time_ns()))\n"
            " time.sleep(.02)\n"
        )
        process = self.launch(
            "import subprocess,sys\n"
            f"subprocess.Popen([sys.executable, '-c', {child_code!r}])\n",
            timeout=2,
        )
        stdout, stderr = process.communicate(b"{}", timeout=5)
        self.assertEqual(process.returncode, 0, stderr)
        self.assertIn("output collection", self.decision(stdout))
        self.assertTrue(pid_file.exists())
        previous = heartbeat.read_text()
        time.sleep(.15)
        self.assertEqual(heartbeat.read_text(), previous)
        pid = int(pid_file.read_text())
        if os.name == "nt":
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_uint]
            kernel.OpenProcess.restype = ctypes.c_void_p
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            handle = kernel.OpenProcess(0x1000, False, pid)
            if handle:
                exit_code = ctypes.c_uint()
                kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
                self.assertTrue(kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)))
                kernel.CloseHandle(handle)
                self.assertNotEqual(exit_code.value, 259)
        elif Path(f"/proc/{pid}/stat").exists():
            self.assertEqual(Path(f"/proc/{pid}/stat").read_text().split()[2], "Z")

    def test_exit_two_and_crashes_remain_denials(self):
        for source, reason in (
            ("import sys\nsys.stderr.buffer.write('déni 雪'.encode('utf-8'))\nsys.exit(2)\n", "déni 雪"),
            ("raise RuntimeError('probe failure')\n", "failed with exit code 1"),
        ):
            with self.subTest(reason=reason):
                process = self.launch(source)
                stdout, stderr = process.communicate(b"{}", timeout=4)
                self.assertEqual(process.returncode, 0, stderr)
                self.assertIn(reason, self.decision(stdout))

    def test_windows_launch_is_hidden_suspended_and_contained_before_resume(self):
        spec = importlib.util.spec_from_file_location("pretool", ADAPTER)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        kernel = mock.Mock()
        kernel.AssignProcessToJobObject.return_value = True
        process = mock.Mock()
        process._handle = 123
        process.returncode = 0
        process.communicate.return_value = (b"", b"")
        ntdll = mock.Mock()
        ntdll.NtResumeProcess.return_value = 0
        calls = mock.Mock()
        calls.attach_mock(kernel.AssignProcessToJobObject, "assign")
        calls.attach_mock(ntdll.NtResumeProcess, "resume")
        with mock.patch.object(adapter.os, "name", "nt"), \
             mock.patch.object(adapter, "windows_job", return_value=(kernel, 456)), \
             mock.patch.object(adapter.ctypes, "WinDLL", return_value=ntdll, create=True), \
             mock.patch.object(adapter.subprocess, "CREATE_NO_WINDOW", 0x08000000, create=True), \
             mock.patch.object(adapter.subprocess, "Popen", return_value=process) as popen, \
             mock.patch.object(adapter, "read_object", return_value=b"{}"), \
             mock.patch.object(adapter.sys, "argv", ["adapter", "--timeout", "2", "probe.py"]):
            self.assertEqual(adapter.main(), 0)
        self.assertEqual(popen.call_args.kwargs["creationflags"], 0x08000004)
        self.assertFalse(popen.call_args.kwargs["start_new_session"])
        self.assertEqual(calls.mock_calls, [mock.call.assign(456, 123), mock.call.resume(123)])
        kernel.CloseHandle.assert_called_once_with(456)

    def test_windows_delayed_launch_is_cancelled_without_resume(self):
        spec = importlib.util.spec_from_file_location("pretool_cancelled", ADAPTER)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        kernel = mock.Mock()
        process = mock.Mock()
        process._handle = 123
        ntdll = mock.Mock()
        launched = adapter.threading.Event()

        def delayed_launch(*args, **kwargs):
            time.sleep(.3)
            launched.set()
            return process

        with mock.patch.object(adapter.os, "name", "nt"), \
             mock.patch.object(adapter, "windows_job", return_value=(kernel, 456)), \
             mock.patch.object(adapter.ctypes, "WinDLL", return_value=ntdll, create=True), \
             mock.patch.object(adapter.subprocess, "CREATE_NO_WINDOW", 0x08000000, create=True), \
             mock.patch.object(adapter.subprocess, "Popen", side_effect=delayed_launch), \
             mock.patch.object(adapter, "read_object", return_value=b"{}"), \
             mock.patch.object(adapter, "deny", return_value=0) as deny, \
             mock.patch.object(adapter.sys, "argv", ["adapter", "--timeout", ".1", "probe.py"]):
            self.assertEqual(adapter.main(), 0)
            self.assertTrue(launched.wait(1))
            until = time.monotonic() + 1
            while not process.kill.called and time.monotonic() < until:
                time.sleep(.005)
        deny.assert_called_once()
        process.kill.assert_called_once()
        ntdll.NtResumeProcess.assert_not_called()
        kernel.AssignProcessToJobObject.assert_not_called()
        kernel.CloseHandle.assert_called_once_with(456)


if __name__ == "__main__":
    unittest.main()
