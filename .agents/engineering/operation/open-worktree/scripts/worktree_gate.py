import json
import re
import shlex
import sys
import time
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import cast

import create_worktree


class Mutation(Enum):
    ADD = ("add", 0, frozenset({"-b", "-B", "--reason"}))
    MOVE = ("move", 1, frozenset[str]())

    def __init__(self, command: str, destination: int, options: frozenset[str]) -> None:
        self.command = command
        self.destination = destination
        self.options = options


def literal(value: str) -> str:
    if not value or re.search(r"[$`%\n\r]", value):
        raise create_worktree.CreateWorktreeError("use literal worktree arguments")
    return value


def executable(value: str) -> str:
    return value.replace("\\", "/").rsplit("/", 1)[-1].removesuffix(".exe").lower()


def segments(command: str) -> list[list[str]]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.escape = ""
    groups: list[list[str]] = [[]]
    for token in lexer:
        if token and all(character in ";&|()\n" for character in token):
            if "(" in token or ")" in token or "||" in token:
                raise ValueError("unsupported shell control flow")
            if groups[-1]:
                groups.append([])
        else:
            groups[-1].append(token)
    return [group for group in groups if group]


def destination(arguments: Sequence[str], mutation: Mutation) -> str:
    operands = []
    index = 0
    options = True
    while index < len(arguments):
        value = literal(arguments[index])
        index += 1
        if options and value == "--":
            options = False
        elif options and value in mutation.options:
            if index == len(arguments):
                raise create_worktree.CreateWorktreeError(
                    f"missing argument for {value}"
                )
            literal(arguments[index])
            index += 1
        elif options and value.startswith("--reason="):
            continue
        elif options and value.startswith("-"):
            if value not in {
                "-f",
                "-ff",
                "--force",
                "--detach",
                "-d",
                "--checkout",
                "--no-checkout",
                "--lock",
                "--quiet",
                "-q",
                "--track",
                "--no-track",
                "--guess-remote",
                "--no-guess-remote",
                "--orphan",
            } and not value.startswith("--track="):
                raise create_worktree.CreateWorktreeError(
                    f"unsupported worktree option: {value}"
                )
        else:
            operands.append(value)
    if len(operands) <= mutation.destination:
        raise create_worktree.CreateWorktreeError("worktree destination is missing")
    return operands[mutation.destination]


def check_git(arguments: Sequence[str], cwd: Path, deadline: float) -> None:
    index = 0
    while index < len(arguments):
        value = literal(arguments[index])
        if value == "-C" and index + 1 < len(arguments):
            cwd = (cwd / literal(arguments[index + 1])).resolve()
            index += 2
        elif value in {"--no-pager", "--literal-pathspecs", "--no-optional-locks"}:
            index += 1
        else:
            break
    if index == len(arguments):
        return
    if arguments[index] != "worktree":
        if "worktree" in arguments:
            raise create_worktree.CreateWorktreeError("unsupported Git routing options")
        return
    if index + 1 == len(arguments):
        return
    action = literal(arguments[index + 1])
    if action in {"list", "prune", "remove", "repair", "lock", "unlock", "-h"}:
        return
    mutation = next((item for item in Mutation if item.command == action), None)
    if mutation is None:
        raise create_worktree.CreateWorktreeError("unsupported worktree operation")
    target = destination(arguments[index + 2 :], mutation)
    repo = create_worktree.repository_root(cwd, deadline=deadline)
    create_worktree.validate_destination(repo, cwd / target)


def mentions_worktree(words: Sequence[str]) -> bool:
    return "worktree" in words or any(
        word.startswith("--worktree") or word == "-w" for word in words
    )


def mutates_worktree(words: Sequence[str]) -> bool:
    if "worktree" not in words:
        return False
    action = words[words.index("worktree") + 1 :]
    return bool(action) and literal(action[0]) in {"add", "move"}


def check_command(command: str, cwd: Path, deadline: float) -> None:
    if not re.search(r"\b(?:git(?:\.exe)?|worktree)\b", command, re.IGNORECASE):
        return
    if "worktree" in command.lower() and ("`" in command or "$(" in command):
        raise create_worktree.CreateWorktreeError(
            "worktree shell substitutions cannot be verified; use literal arguments"
        )
    try:
        commands = segments(command)
    except ValueError as error:
        if "worktree" in command.lower():
            raise create_worktree.CreateWorktreeError(
                "cannot verify this worktree shell expression"
            ) from error
        return
    if not any(mentions_worktree(words) for words in commands):
        return
    for words in commands:
        program = executable(words[0])
        if program in {
            "rg",
            "grep",
            "findstr",
            "select-string",
            "echo",
            "printf",
            "write-output",
            "write-host",
        }:
            continue
        if program in {"cd", "chdir", "set-location", "push-location", "pushd"}:
            arguments = [
                word for word in words[1:] if word not in {"-LiteralPath", "-Path"}
            ]
            if len(arguments) != 1:
                raise create_worktree.CreateWorktreeError(
                    "cannot resolve shell directory"
                )
            cwd = (cwd / literal(arguments[0])).resolve()
        elif program in {"command", "env"} and len(words) > 1:
            if executable(words[1]) == "git":
                check_git(words[2:], cwd, deadline)
            elif "worktree" in words:
                raise create_worktree.CreateWorktreeError("unsupported Git environment")
        elif program == "git":
            check_git(words[1:], cwd, deadline)
        elif program in {"bash", "sh", "zsh", "pwsh", "powershell", "cmd"}:
            for index, word in enumerate(words[1:], start=1):
                if word.lower() in {"-c", "-lc", "-command", "/c"}:
                    check_command(" ".join(words[index + 1 :]), cwd, deadline)
                    break
        elif program in {"claude", "codex"} and any(
            word.split("=", 1)[0] in {"--worktree", "-w"} for word in words[1:]
        ):
            raise create_worktree.CreateWorktreeError(
                "native worktree placement is not supported"
            )
        elif (
            program in {"popd", "pop-location"}
            or "=" in words[0]
            or any(executable(word) == "git" for word in words[1:])
            or mutates_worktree(words)
        ):
            raise create_worktree.CreateWorktreeError(
                "cannot verify this worktree shell expression"
            )


def check_tool(payload: Mapping[str, object]) -> None:
    name = str(payload.get("tool_name", ""))
    raw_input = payload.get("tool_input", {})
    if isinstance(raw_input, str):
        raw_input = json.loads(raw_input)
    if not isinstance(raw_input, dict):
        raise create_worktree.CreateWorktreeError("invalid worktree hook tool input")
    arguments = cast(dict[str, object], raw_input)
    if (
        payload.get("hook_event_name") == "WorktreeCreate"
        or name == "EnterWorktree"
        or name.endswith("create_worktree")
        or arguments.get("isolation") == "worktree"
    ):
        raise create_worktree.CreateWorktreeError(
            "native worktree placement is not supported"
        )
    command = arguments.get("command", arguments.get("cmd", ""))
    cwd = arguments.get("workdir", arguments.get("cwd", payload.get("cwd")))
    if not isinstance(command, str) or not command:
        return
    if not isinstance(cwd, str) or not cwd:
        raise create_worktree.CreateWorktreeError(
            "worktree hook working directory is missing"
        )
    check_command(command, Path(cwd), time.monotonic() + 10)


def main() -> int:
    if sys.version_info < create_worktree.MINIMUM_PYTHON:
        print("worktree_gate.py requires Python 3.12 or newer", file=sys.stderr)
        return 2
    payload: dict[str, object] = {}
    try:
        value = json.load(sys.stdin)
        if not isinstance(value, dict):
            raise create_worktree.CreateWorktreeError("invalid worktree hook payload")
        payload = value
        check_tool(payload)
    except (create_worktree.CreateWorktreeError, ValueError) as error:
        interpreter = "python" if sys.platform == "win32" else "python3"
        script = Path(__file__).with_name("create_worktree.py")
        reason = (
            f"{error}. Use Core's engineering:open-worktree command: "
            f'{interpreter} -B "{script}" --repo <repository> <Type/Name>.'
        )
        if payload.get("hook_event_name") == "WorktreeCreate":
            print(reason, file=sys.stderr)
            return 2
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
