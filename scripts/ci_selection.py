import argparse
import ast
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOTS = ("tests", ".agents/hooks/tests")
FULL_LABEL = "ci:full"
MAX_FILES = 40
MAX_LINES = 1000
FAMILIES = {
    "problem-records": {
        "sources": {
            ".agents/hooks/problem_records.py",
        },
        "tests": {
            ".agents/hooks/tests/test_problem_records.py",
        },
    },
    "plugin-adoption": {
        "sources": {
            ".agents/machine/utility/plugin-selection/scripts/adopt_plugins.py",
            ".agents/machine/utility/plugin-selection/scripts/plugin_roster.json",
        },
        "tests": {".agents/hooks/tests/test_adopt_plugins.py"},
    },
    "machine-verification": {
        "sources": {".agents/machine/utility/plugin-selection/scripts/verify_machine.py"},
        "tests": {".agents/hooks/tests/test_verify_machine.py"},
    },
    "handoff-transfer": {
        "sources": {".agents/engineering/workflow/handoff/scripts/transfer.py"},
        "tests": {".agents/hooks/tests/test_handoff_transfer.py"},
    },
}


def plan(mode, reason, tests=()):
    return {"mode": mode, "reason": reason, "tests": sorted(set(tests))}


def inert_document(path):
    value = PurePosixPath(path)
    return (
        value.suffix == ".md"
        and value.name not in {"AGENTS.md", "CLAUDE.md", "SKILL.md"}
        and (path in {"README.md", "BUGS.md", "MISTAKES.md", "TECH_DEBT.md", "CHANGELOG.md"}
             or value.parts[0] in {"docs", "plans", "reviews"})
    )


def test_file(path):
    value = PurePosixPath(path)
    return (
        str(value.parent) in TEST_ROOTS
        and value.name.startswith("test_")
        and value.suffix == ".py"
    )


def test_closure(root, selected):
    dependencies = {}
    for parent in TEST_ROOTS:
        for path in (root / parent).glob("test_*.py"):
            names = set()
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
                if isinstance(node, ast.ImportFrom) and node.module:
                    names.add(node.module.split(".")[-1])
                elif isinstance(node, ast.Import):
                    names.update(alias.name.split(".")[-1] for alias in node.names)
            dependencies[path.relative_to(root).as_posix()] = names
    while True:
        names = {PurePosixPath(path).stem for path in selected}
        expanded = selected | {path for path, imports in dependencies.items() if names & imports}
        if expanded == selected:
            return selected
        selected = expanded


def classify(paths, *, event="pull_request", labels=(), lines=0, binary=False, root=ROOT):
    paths = set(paths)
    if event != "pull_request":
        return plan("full", "non-PR event")
    if FULL_LABEL in labels:
        return plan("full", "explicit full-coverage label")
    if not paths or binary or len(paths) > MAX_FILES or lines > MAX_LINES:
        return plan("full", "empty, binary or broad change")
    selected = set()
    for path in sorted(paths):
        if inert_document(path):
            continue
        families = [family for family in FAMILIES.values() if path in family["sources"]]
        if families:
            for family in families:
                selected.update(family["tests"])
        elif test_file(path) and path != "tests/test_ci_selection.py":
            if not (root / path).is_file():
                return plan("full", "deleted test")
            selected.add(path)
        else:
            return plan("full", f"unmapped surface: {path}")
    if selected:
        try:
            selected = test_closure(root, selected)
        except (OSError, UnicodeError, SyntaxError):
            return plan("full", "regression dependencies cannot be read")
        if not all((root / path).is_file() for path in selected):
            return plan("full", "selected regression is unavailable")
    if selected:
        return plan("focused", "mapped behavioral regressions", selected)
    return plan("docs", "inert documentation")


def git_output(root, *arguments):
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, timeout=30
    ).stdout


def select(root, event, payload):
    if event != "pull_request":
        return plan("full", "non-PR event")
    try:
        base = payload["pull_request"]["base"]["sha"]
        if not isinstance(base, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", base):
            raise ValueError("invalid base SHA")
        raw_paths = git_output(root, "diff", "--name-only", "--no-renames", "-z", base, "HEAD")
        paths = raw_paths.decode("utf-8").rstrip("\0").split("\0") if raw_paths else []
        stats = git_output(root, "diff", "--numstat", "--no-renames", "-z", base, "HEAD")
        lines = 0
        binary = False
        for entry in stats.split(b"\0"):
            if not entry:
                continue
            added, deleted, _ = entry.split(b"\t", 2)
            if b"-" in (added, deleted):
                binary = True
            else:
                lines += int(added) + int(deleted)
        labels = [label["name"] for label in payload["pull_request"].get("labels", [])]
        return classify(paths, event=event, labels=labels, lines=lines, binary=binary, root=root)
    except (KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError):
        return plan("full", "change range or event cannot be resolved")


def validate_plan(value):
    if not isinstance(value, dict) or set(value) != {"mode", "reason", "tests"}:
        raise ValueError("invalid CI selection")
    if (value["mode"] not in {"full", "focused", "docs"}
            or not isinstance(value["reason"], str) or not value["reason"]):
        raise ValueError("invalid CI selection mode/reason")
    tests = value["tests"]
    if not isinstance(tests, list) or any(not isinstance(path, str) or not test_file(path) for path in tests):
        raise ValueError("invalid selected tests")
    if len(tests) != len(set(tests)) or bool(tests) != (value["mode"] == "focused"):
        raise ValueError("selected tests do not match CI mode")
    return value


def required_results(value, needs, event):
    validate_plan(value)
    if not isinstance(needs, dict):
        raise ValueError("invalid CI job results")
    if event != "pull_request" and value["mode"] != "full":
        raise ValueError("non-PR validation requires full coverage")
    expected = {"select": "success", "guard": "success" if event == "pull_request" else "skipped"}
    expected.update({name: "skipped" if value["mode"] == "docs" else "success"
                     for name in ("verify-windows", "verify-linux")})
    for name, result in expected.items():
        if not isinstance(needs.get(name), dict) or needs[name].get("result") != result:
            raise ValueError(f"{name} must finish as {result}")


def run_tests(root, value, group):
    validate_plan(value)
    if value["mode"] != "focused":
        raise ValueError("focused test execution needs a focused selection")
    parent = TEST_ROOTS[0] if group == "source" else TEST_ROOTS[1]
    selected = [path for path in value["tests"] if str(PurePosixPath(path).parent) == parent]
    if not selected:
        print(f"No {group} regression modules selected")
        return 0
    suite = unittest.TestSuite()
    for path in selected:
        target = root / path
        if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"selected test is unavailable: {path}")
        loader = unittest.TestLoader()
        discovered = loader.discover(str(target.parent), pattern=target.name)
        if not discovered.countTestCases():
            raise ValueError(f"selected regression module discovered no tests: {path}")
        suite.addTests(discovered)
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


def main(argv=None):
    if sys.version_info < (3, 9):
        print("CI selection requires Python 3.9 or newer", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description="Select and require CI coverage (Python 3.9+)")
    parser.add_argument("operation", choices=("select", "run", "required"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--group", choices=("source", "runtime"))
    args = parser.parse_args(argv)
    try:
        if args.operation == "select":
            event = os.environ.get("GITHUB_EVENT_NAME", "")
            try:
                payload = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
            except (KeyError, OSError, ValueError):
                payload = {}
            value = select(args.root, event, payload)
            serialized = json.dumps(value, separators=(",", ":"))
            if os.environ.get("GITHUB_OUTPUT"):
                with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write(f"plan={serialized}\n")
            print(serialized)
            if value["mode"] == "docs":
                subprocess.run([sys.executable, "-B", str(args.root / ".agents/hooks/docs_reachability.py"),
                                "--root", str(args.root)], check=True, timeout=120)
            return 0
        value = json.loads(os.environ["CI_SELECTION"])
        if args.operation == "required":
            required_results(
                value, json.loads(os.environ["CI_NEEDS"]), os.environ.get("GITHUB_EVENT_NAME", "")
            )
            print("Every selected CI job succeeded")
            return 0
        if args.group is None:
            raise ValueError("run requires --group")
        return run_tests(args.root, value, args.group)
    except (KeyError, TypeError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"CI selection: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
