"""Keep agent writes out of host memory, host settings and machine state."""

from __future__ import annotations

import os
import re
import shlex
from collections.abc import Iterable, Mapping
from enum import Enum
from itertools import islice
from pathlib import Path

PATH_TOKENS = 256
PATH_LIKE = re.compile(r"[/\\.~]")
TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\'[^\']*\'|[^\s;|&<>()]+')
LEADING_CD = re.compile(
    r'^\s*cd\s+(?:/d\s+)?("[^"]+"|\'[^\']+\'|[^\s;&|]+)\s*(?:&&|;|\|\|)'
)
HOME_VARIABLE = re.compile(
    r"^(?:\$HOME|\$\{HOME\}|\$env:(?:HOME|USERPROFILE)|%USERPROFILE%)(?=[/\\]|$)",
    re.IGNORECASE,
)
FILE_WRITERS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"})
COMMANDS = frozenset({"Bash", "PowerShell", "shell", "exec_command"})
READERS = frozenset(
    {
        "cat",
        "gc",
        "get-content",
        "get-childitem",
        "get-item",
        "grep",
        "head",
        "ls",
        "pwd",
        "rg",
        "select-object",
        "select-string",
        "tail",
        "test-path",
    }
)
RG_READ_OPTIONS = frozenset(
    {
        "-n",
        "--line-number",
        "-i",
        "--ignore-case",
        "-s",
        "--case-sensitive",
        "-S",
        "--smart-case",
        "-F",
        "--fixed-strings",
        "-e",
        "--regexp",
        "-g",
        "--glob",
        "--hidden",
        "--no-ignore",
        "--files",
        "-l",
        "--files-with-matches",
        "-v",
        "--invert-match",
        "-m",
        "--max-count",
        "-A",
        "--after-context",
        "-B",
        "--before-context",
        "-C",
        "--context",
        "--no-config",
        "--no-heading",
        "--heading",
        "--color",
        "--",
    }
)
MEMORY_LESSON = (
    "Host memory lives on one machine, so a lesson kept there repeats everywhere else. "
    "Fix the cause in its source instead: a defect in the installed agent tooling "
    "goes through template:self-repair, or `tj item create` in that tooling's own "
    "repository when fixing it now would derail the current task. A fact about a "
    "project belongs in that project's documentation."
)
SETTINGS_LESSON = (
    "These are written only by their owning scripted commands (tj install, setup, "
    "onboard), never by an agent edit; record the choice in the repository instead "
    "(base:machine-agnostic)."
)


class Host(Enum):
    CLAUDE = (("projects", "*", "memory"), ("settings.json", "settings.local.json"))
    CODEX = (("memories",), ("config.toml", "rules"))

    def __init__(self, memory: tuple[str, ...], settings: tuple[str, ...]) -> None:
        self.memory = memory
        self.settings = settings

    def holds_memory(self, home: Path, target: Path) -> bool:
        try:
            relative = target.relative_to(home)
        except ValueError:
            return False
        names = relative.parts
        return len(names) > len(self.memory) and all(
            expected in ("*", name)
            for expected, name in zip(self.memory, names, strict=False)
        )

    def holds_settings(self, home: Path, target: Path) -> bool:
        return any(target.is_relative_to(home / name) for name in self.settings)


def memory_target(targets: Iterable[Path], homes: Mapping[Host, Path]) -> Path | None:
    for target in targets:
        if any(host.holds_memory(home, target) for host, home in homes.items()):
            return target
    return None


def settings_target(
    targets: Iterable[Path], homes: Mapping[Host, Path], state: Path
) -> Path | None:
    for target in targets:
        if target.is_relative_to(state) or any(
            host.holds_settings(home, target) for host, home in homes.items()
        ):
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
    if _read_only(command):
        return ()
    leading = LEADING_CD.match(command)
    directory = _resolved(leading.group(1).strip("\"'"), cwd) if leading else cwd
    targets = [directory]
    tokens = TOKEN.findall(command)
    for raw in islice(tokens, PATH_TOKENS):
        token = raw.strip("\"'")
        if token != raw and ("$(" in token or "`" in token):
            tokens.extend(TOKEN.findall(token))
        if not PATH_LIKE.search(token):
            continue
        for candidate in (token, *token.split("=", 1)[1:], token.removeprefix("@")):
            path = HOME_VARIABLE.sub("~", candidate)
            if _names_path(path, directory):
                targets.append(_resolved(path, directory))
    return tuple(targets)


def _read_only(command: str) -> bool:
    # This recognizes only literal inspection pipelines, not arbitrary shell code.
    # Uncertain syntax retains the existing conservative target scan.
    if any(value in command for value in ("`", '\\"', "\\'")):
        return False
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.escape = ""
    lexer.commenters = ""
    reader = ""
    seen = False
    try:
        for token in lexer:
            if token and all(character in ";&|\n" for character in token):
                if token not in {"&&", "||", "|"} and not all(
                    character in ";\n" for character in token
                ):
                    return False
                reader = ""
                continue
            literal = HOME_VARIABLE.sub("~", token)
            if any(character in literal for character in "$`{}()<>@&"):
                return False
            if not reader:
                reader = token.lower().removesuffix(".exe")
                if reader not in READERS:
                    return False
                seen = True
            elif (
                reader == "rg"
                and token.startswith("-")
                and token.partition("=")[0] not in RG_READ_OPTIONS
            ):
                return False
    except ValueError:
        return False
    return seen


def _names_path(candidate: str, directory: Path) -> bool:
    if not candidate or candidate.startswith("-") or len(candidate) > 1024:
        return False
    try:
        path = _resolved(candidate, directory)
        return path.exists() or path.parent.exists()
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


def settings_reason(target: Path) -> str:
    return (
        f"Blocked: {target} is user-level host settings or machine state. "
        f"{SETTINGS_LESSON}"
    )
