import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("advance_release", ROOT / "scripts/advance_release.py")
RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE)


class AdvanceReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="advance release ")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.origin, self.clone = root / "origin.git", root / "clone"
        self.git(root, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.git(root, "clone", "-q", str(self.origin), str(self.clone))

    def git(self, cwd, *arguments):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *arguments], cwd=cwd,
                              check=True, capture_output=True, text=True).stdout.strip()

    def commit(self):
        self.git(self.clone, "commit", "-q", "--allow-empty", "-m", "change")
        return self.git(self.clone, "rev-parse", "HEAD")

    def released(self):
        return self.git(self.origin, "rev-parse", "refs/heads/release")

    def test_release_is_created_then_only_fast_forwards(self):
        first = self.commit()
        self.assertEqual("advanced", RELEASE.advance(self.clone, first))
        self.assertEqual(first, self.released())
        self.assertEqual("current", RELEASE.advance(self.clone, first))
        second = self.commit()
        self.assertEqual("advanced", RELEASE.advance(self.clone, second))
        self.assertEqual("superseded", RELEASE.advance(self.clone, first))
        self.assertEqual(second, self.released())

    def test_an_invalid_commit_is_rejected_before_any_push(self):
        with self.assertRaises(ValueError):
            RELEASE.advance(self.clone, "main")


if __name__ == "__main__":
    unittest.main()
