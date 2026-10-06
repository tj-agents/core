import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "nt", "Windows is required")
class FinishTests(unittest.TestCase):
    def test_finish_scenarios(self):
        shell = "pwsh" if shutil.which("pwsh") else "powershell.exe"
        result = subprocess.run(
            [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "tests" / "finish.tests.ps1")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=480,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS finish.tests.ps1", result.stdout)


if __name__ == "__main__":
    unittest.main()
