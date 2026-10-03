import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / '.agents/machine/scripts'
sys.path.insert(0, str(SCRIPTS))
import bounded_process

SPEC = importlib.util.spec_from_file_location('claude_sync_bounded', SCRIPTS / 'claude_standards_sync.py')
SYNC = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SYNC
SPEC.loader.exec_module(SYNC)


class BoundedProcessTests(unittest.TestCase):
    def test_success_keeps_arguments_output_and_exit_code(self):
        code, output, error = bounded_process.run([
            sys.executable, '-c', 'import sys; print(sys.argv[1]); print("detail", file=sys.stderr); sys.exit(7)',
            'spaces "quotes" & punctuation',
        ], timeout=5)
        self.assertEqual(code, 7)
        self.assertEqual(output.strip(), 'spaces "quotes" & punctuation')
        self.assertEqual(error.strip(), 'detail')

    def test_expired_budget_never_starts_a_command(self):
        self.assertEqual(bounded_process.run(['missing-executable'], timeout=0),
                         (None, '', 'refresh time budget exhausted'))

    def test_timeout_stops_grandchild_holding_output_open(self):
        with tempfile.TemporaryDirectory() as directory:
            heartbeat = Path(directory) / 'heartbeat'
            child = (
                'import pathlib,time; p=pathlib.Path(' + repr(str(heartbeat)) + '); '
                '[(p.write_text(str(i)), time.sleep(0.1)) for i in range(200)]'
            )
            parent = 'import subprocess,sys; subprocess.Popen([sys.executable,"-c",' + repr(child) + ']).wait()'
            started = time.monotonic()
            code, output, error = SYNC.run([sys.executable, '-c', parent], timeout=2)
            self.assertLess(time.monotonic() - started, 9)
            self.assertIsNone(code)
            self.assertIn('timed out', error)
            self.assertTrue(heartbeat.exists(), 'Grandchild did not start')
            previous = heartbeat.read_text()
            time.sleep(0.4)
            self.assertEqual(heartbeat.read_text(), previous, 'Grandchild survived timeout')

    def test_cli_forwards_utf8_under_a_legacy_pipe_encoding(self):
        environment = dict(os.environ, PYTHONIOENCODING='cp1252')
        completed = subprocess.run([
            sys.executable, '-B', str(SCRIPTS / 'bounded_process.py'), '--timeout', '5', '--',
            sys.executable, '-c', 'import sys; sys.stdout.buffer.write(bytes.fromhex("e4bda0e5a5bd")); '
            'sys.stderr.buffer.write(bytes.fromhex("e4bda0e5a5bd"))',
        ], env=environment, capture_output=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, bytes.fromhex('e4bda0e5a5bd'))
        self.assertEqual(completed.stderr, bytes.fromhex('e4bda0e5a5bd'))

    def test_claude_respects_remaining_budget(self):
        token = SYNC.SYNC_DEADLINE.set(time.monotonic() - 1)
        try:
            self.assertEqual(SYNC.run(['missing-executable']),
                             (None, '', 'refresh time budget exhausted'))
        finally:
            SYNC.SYNC_DEADLINE.reset(token)


if __name__ == '__main__':
    unittest.main()
