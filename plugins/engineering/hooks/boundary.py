"""Keep agent lessons out of host memory."""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from enum import Enum
from pathlib import Path

PATH_TOKENS = 256
PATH_LIKE = re.compile(r"[/\\.~]")
TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\'[^\']*\'|[^\s;|&<>()]+')
LEADING_CD = re.compile(
    r'^\s*cd\s+(?:/d\s+)?("[^"]+"|\'[^\']+\'|[^\s;&|]+)\s*(?:&&|;|\|\|)'
)
FILE_WRITERS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"})
COMMANDS = frozenset({"Bash", "PowerShell", "shell", "exec_command"})
MEMORY_LESSON = (
    "Host memory lives on one machine, so a lesson kept there repeats everywhere else. "
    "Fix the cause in its source instead: a defect in the installed agent tooling "
    "goes through template:self-repair, or `tj item create` in that tooling's own "
    "repository when fixing it now would derail the current task. A fact about a "
    "project belongs in that project's documentation."
)


class HostMemory(Enum):
    CLAUDE = ("projects", "*", "memory")
    CODEX = ("memories",)

    def __init__(self, *parts: str) -> None:
        self.parts = parts

    def holds(self, home: Path, target: Path) -> bool:
        try:
            relative = target.relative_to(home)
        except ValueError:
            return False
        names = relative.parts
        return len(names) > len(self.parts) and all(
            expected in ("*", name)
            for expected, name in zip(self.parts, names, strict=False)
        )


def memory_target(
    targets: Iterable[Path], homes: Mapping[HostMemory, Path]
) -> Path | None:
    for target in targets:
        if any(host.holds(home, target) for host, home in homes.items()):
            return target
    return None


def outgoing_targets(
    tool: str, tool_input: Mapping[str, object], cwd: Path
) -> tuple[Path, ...]:
    if tool in FILE_WRITERS:
        return tuple(_resolved(path, cwd) for path in _written(tool, tool_input))
    if tool in COMMANDS:
        command = tool_input.get("command")
        if isinstance(command, list):
            command = " ".join(part for part in command if isinstance(part, str))
        if isinstance(command, str):
            return _command_targets(command, cwd)
    return ()


def _written(tool: str, tool_input: Mapping[str, object]) -> dict[str, str]:
    if tool == "apply_patch":
        command = tool_input.get("command")
        return _patch_additions(command) if isinstance(command, str) else {}
    key = "notebook_path" if tool == "NotebookEdit" else "file_path"
    path = tool_input.get(key)
    if not isinstance(path, str) or not path:
        return {}
    if tool == "MultiEdit":
        edits = tool_input.get("edits")
        texts = (
            [edit.get("new_string") for edit in edits if isinstance(edit, dict)]
            if isinstance(edits, list)
            else []
        )
        return {path: "\n".join(text for text in texts if isinstance(text, str))}
    field = {"Write": "content", "Edit": "new_string", "NotebookEdit": "new_source"}[
        tool
    ]
    value = tool_input.get(field)
    return {path: value if isinstance(value, str) else ""}


def _patch_additions(patch: str) -> dict[str, str]:
    added: dict[str, list[str]] = {}
    current = None
    for line in patch.splitlines():
        header = re.fullmatch(
            r"\*\*\* (?:Update|Add|Delete) File: (.+)|\*\*\* Move to: (.+)", line
        )
        if header is not None:
            current = header.group(1) or header.group(2)
            added.setdefault(current, [])
        elif current is not None and line.startswith("+"):
            added[current].append(line[1:])
    return {path: "\n".join(lines) for path, lines in added.items()}


def _command_targets(command: str, cwd: Path) -> tuple[Path, ...]:
    leading = LEADING_CD.match(command)
    directory = _resolved(leading.group(1).strip("\"'"), cwd) if leading else cwd
    targets = [directory]
    for raw in TOKEN.findall(command)[:PATH_TOKENS]:
        token = raw.strip("\"'")
        candidates = [token, *token.split("=", 1)[1:], token.removeprefix("@")]
        if PATH_LIKE.search(token):
            targets.extend(
                _resolved(candidate, directory)
                for candidate in candidates
                if _exists(candidate, directory)
            )
    return tuple(targets)


def _exists(candidate: str, directory: Path) -> bool:
    if not candidate or candidate.startswith("-") or len(candidate) > 1024:
        return False
    try:
        return _resolved(candidate, directory).exists()
    except (OSError, ValueError):
        return False


def _resolved(path: str, cwd: Path) -> Path:
    # PowerShell accepts `\` as a separator on every platform; on POSIX it would
    # otherwise be read as part of a file name.
    raw = Path(path if os.sep == "\\" else path.replace("\\", "/")).expanduser()
    return (raw if raw.is_absolute() else cwd / raw).resolve(strict=False)


def memory_reason(target: Path) -> str:
    return (
        f"Blocked: {target} is host memory, which agents do not write. {MEMORY_LESSON}"
    )
