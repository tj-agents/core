import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BRANCH = "release"


def git(root, *arguments):
    return subprocess.run(["git", *arguments], cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120, check=False)


def advance(root, sha, remote="origin"):
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError(f"invalid release commit: {sha}")
    fetched = git(root, "fetch", "--quiet", remote, f"refs/heads/{BRANCH}")
    if not fetched.returncode:
        current = git(root, "rev-parse", "FETCH_HEAD").stdout.strip()
        if current == sha:
            return "current"
        if git(root, "merge-base", "--is-ancestor", current, sha).returncode:
            return "superseded"
    pushed = git(root, "push", remote, f"{sha}:refs/heads/{BRANCH}")
    if pushed.returncode:
        raise RuntimeError(f"release push failed: {(pushed.stderr or pushed.stdout).strip()}")
    return "advanced"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fast-forward the release branch to a verified main commit")
    parser.add_argument("--sha", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    arguments = parser.parse_args(argv)
    try:
        outcome = advance(arguments.root, arguments.sha)
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"release: {error}", file=sys.stderr)
        return 1
    print(f"release: {outcome} at {arguments.sha}")
    if os.environ.get("GITHUB_OUTPUT"):
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(f"outcome={outcome}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
