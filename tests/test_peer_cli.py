import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == "nt" and shutil.which("pwsh"), "PowerShell 7 on Windows is required")
class PeerCliTests(unittest.TestCase):
    def test_scope_regressions(self):
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "tests" / "peer-cli.tests.ps1")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS peer-cli.tests.ps1", result.stdout)


if __name__ == "__main__":
    unittest.main()
