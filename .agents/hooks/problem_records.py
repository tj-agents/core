import json
from pathlib import Path
import re
import subprocess
import sys


if sys.version_info < (3, 9):
    raise SystemExit("Problem-record providers require Python 3.9 or later")


CONFIG = ".problem-records.json"
PROVIDER = re.compile(r"[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*")
REFERENCE = re.compile(r"[a-z][a-z0-9+.-]*://[^\s]+")


class RecordError(ValueError):
    pass


def primary_checkout(directory):
    try:
        root = subprocess.run(
            ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, encoding="utf-8", timeout=5, check=False,
        )
        if root.returncode:
            raise RecordError("source repository root could not be resolved")
        worktree = Path(root.stdout.strip()).resolve()
        listed = subprocess.run(
            ["git", "-C", str(worktree), "worktree", "list", "--porcelain", "-z"],
            capture_output=True, text=True, encoding="utf-8", timeout=5, check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RecordError("source primary checkout could not be resolved") from error
    entries = []
    for block in listed.stdout.split("\0\0"):
        fields = block.strip("\0").split("\0")
        if fields[0].startswith("worktree ") and fields[0][9:] and "bare" not in fields[1:]:
            entries.append(Path(fields[0][9:]).resolve())
    if listed.returncode or not entries or worktree not in entries or not entries[0].is_dir():
        raise RecordError("source primary checkout could not be resolved")
    return entries[0]


def declaration(root):
    path = Path(root) / CONFIG
    if path.is_symlink():
        raise RecordError("problem-record selection must be a regular repository file")
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise RecordError("problem-record selection is unreadable or invalid") from error
    if not isinstance(value, dict) or set(value) != {"schema_version", "provider"}:
        raise RecordError("problem-record selection has an invalid shape")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or not isinstance(value["provider"], str) or not PROVIDER.fullmatch(value["provider"]):
        raise RecordError("problem-record selection requires schema 1 and a qualified provider skill")
    return value


def read_record(root, reference, harness):
    root = Path(root).resolve()
    selected = declaration(root)
    if selected is None:
        raise RecordError("source repository has no selected problem-record provider")
    if harness not in {"codex", "claude"} or not isinstance(reference, str) or not REFERENCE.fullmatch(reference):
        raise RecordError("provider reads require the actual host and a canonical record URI")
    from skill_router import NativePluginDiscoveryError, resolved_skill
    try:
        found = resolved_skill(selected["provider"], harness)
    except (OSError, ValueError, RuntimeError, NativePluginDiscoveryError) as error:
        raise RecordError("selected problem-record provider could not be resolved") from error
    if found is None:
        raise RecordError("selected problem-record provider is not installed")
    skill_root = found[0].parent.resolve()
    reader = skill_root / "scripts/read_problem_record.py"
    if not reader.is_file() or not reader.resolve().is_relative_to(skill_root):
        raise RecordError("selected provider does not ship its record reader")
    try:
        result = subprocess.run([sys.executable, "-B", str(reader), "--root", str(root), "--record", reference],
                                capture_output=True, text=True, encoding="utf-8", timeout=15, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        raise RecordError("selected provider record read failed") from error
    if result.returncode:
        raise RecordError("selected provider could not read the canonical record")
    try:
        value = json.loads(result.stdout)
    except ValueError as error:
        raise RecordError("selected provider returned invalid JSON") from error
    if not isinstance(value, dict) or set(value) != {"record", "kind", "state", "body"}:
        raise RecordError("selected provider returned an invalid record shape")
    if value["record"] != reference or not isinstance(value["kind"], str) or value["kind"] not in {"bug", "mistake", "debt"} or value["state"] != "open" or not isinstance(value["body"], str) or not value["body"].strip():
        raise RecordError("selected provider returned an unrelated, closed or invalid problem record")
    return value
