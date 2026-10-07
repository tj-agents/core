import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests" / "close-tab.tests.ps1"


def run_with(shell):
    return subprocess.run(
        [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


@unittest.skipUnless(os.name == "nt", "Windows is required")
class CloseTabTests(unittest.TestCase):
    def test_windows_powershell_5(self):
        if not shutil.which("powershell.exe"):
            self.skipTest("Windows PowerShell 5.1 is required")
        result = run_with("powershell.exe")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS close-tab.tests.ps1", result.stdout)

    def test_powershell_7(self):
        if not shutil.which("pwsh"):
            self.skipTest("PowerShell 7 is required")
        result = run_with("pwsh")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS close-tab.tests.ps1", result.stdout)


if __name__ == "__main__":
    unittest.main()
