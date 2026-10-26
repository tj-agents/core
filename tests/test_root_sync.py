import os
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RootSyncTests(unittest.TestCase):
    def test_root_sync_scripts_run_the_shared_refresh_with_arguments_passed_through(self):
        for script, shell in (("sync.ps1", "pwsh"), ("sync.sh", "bash")):
            executable = shutil.which(shell)
            if not executable or (shell == "bash" and os.name == "nt"):
                continue
            with self.subTest(script=script):
                command = [executable, "-NoProfile", "-File", str(ROOT / script)] if shell == "pwsh" else \
                    [executable, str(ROOT / script)]
                result = subprocess.run([*command, "--help"], capture_output=True, text=True, encoding="utf-8",
                                        timeout=60, cwd=ROOT)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("--all", result.stdout)
                self.assertIn("--no-relaunch", result.stdout)


if __name__ == "__main__":
    unittest.main()
