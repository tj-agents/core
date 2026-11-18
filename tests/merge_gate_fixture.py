import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


class MergeFixture:
    def __init__(self, root, environment):
        self.root = root / "checkout with spaces"
        self.root.mkdir()
        self.environment = dict(environment)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Merge Gate Fixture")
        self.git("config", "user.email", "fixture@example.test")
        (self.root / "item.txt").write_text("candidate\n", encoding="utf-8")
        self.git("add", "item.txt")
        self.git("commit", "-qm", "candidate")
        self.head = self.git("rev-parse", "HEAD")
        self.git("update-ref", "refs/remotes/origin/main", self.head)
        self.git("switch", "-qc", "Feature/Fixture")
        self.branch = "Feature/Fixture"
        self.marker = self.root / "merge-executed"
        binary = root / "fixture-bin"
        binary.mkdir()
        body = (
            "import json, os, pathlib, sys\n"
            "if sys.argv[1:2] == ['view']:\n"
            "    print(os.environ['MERGE_FIXTURE_STATE'])\n"
            "elif sys.argv[1:2] == ['merge']:\n"
            "    pathlib.Path('merge-executed').write_text('fixture only', encoding='utf-8')\n"
            "else:\n"
            "    sys.exit(3)\n"
        )
        if os.name == "nt":
            shutil.copy2(sys.executable, binary / "gh.exe")
            for library in Path(sys.base_prefix).glob("python*.dll"):
                shutil.copy2(library, binary / library.name)
            (self.root / "pr").write_text(body, encoding="utf-8")
            self.environment["PYTHONHOME"] = sys.base_prefix
        else:
            executable = binary / "gh"
            executable.write_text("#!/usr/bin/env python3\n" + body.replace(
                "sys.argv[1:2]", "sys.argv[2:3]"
            ), encoding="utf-8")
            executable.chmod(0o755)
        self.environment.update(
            PATH=str(binary) + os.pathsep + os.environ.get("PATH", ""),
            MERGE_FIXTURE_STATE=json.dumps({"headRefName": self.branch, "headRefOid": self.head,
                                            "baseRefOid": self.head}),
        )

    def git(self, *arguments):
        return subprocess.run(
            ["git", *arguments], cwd=self.root, check=True, capture_output=True,
            text=True, encoding="utf-8", timeout=15,
        ).stdout.strip()

    def command(self, head=None):
        return (f'pushd "{self.root.as_posix()}" && gh pr merge 42 --merge '
                f'--match-head-commit {head or self.head}')

    def review(self, module, status="complete", judgment="approved", findings="", head=None):
        head = head or self.head
        body = (f"# Fixture review\n\n**Review status:** `{status}`\n"
                f"**Reviewed up to commit:** `{head}`\n**Judgment:** `{judgment}`\n\n{findings}\n")
        path = module.prepare_path(self.root, self.branch)
        path.write_text(body, encoding="utf-8")
        module.record(self.root, self.branch, head, "a" * 64, path, body.encode("utf-8"))
        return path
