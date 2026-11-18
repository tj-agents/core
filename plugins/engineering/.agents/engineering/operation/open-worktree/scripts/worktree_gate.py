import json
import re
import shlex
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Self, cast

import create_worktree

PASSIVE_PROGRAMS = frozenset(
    {
        "rg",
        "grep",
        "findstr",
        "select-string",
        "echo",
        "printf",
        "write-output",
        "write-host",
    }
)


class Mutation(Enum):
    MOVE = ("move", 1, frozenset[str]())

    def __init__(self, command: str, destination: int, options: frozenset[str]) -> None:
        self.command = command
        self.destination = destination
        self.options = options


class ShellSyntax(Enum):
    POSIX = ("\\", True, True, False, ("bash", "sh", "zsh"))
    POWERSHELL = ("`", True, False, True, ("pwsh", "powershell"))
    CMD = ("^", False, False, False, ("cmd",))

    def __init__(
        self,
        escape: str,
        expansions: bool,
        heredocs: bool,
        here_strings: bool,
        programs: tuple[str, ...],
    ) -> None:
        self.escape = escape
        self.expansions = expansions
        self.heredocs = heredocs
        self.here_strings = here_strings
        self.programs = programs

    @classmethod
    def for_program(cls, value: str) -> Self | None:
        program = executable(value.strip("\"'"))
        return next((syntax for syntax in cls if program in syntax.programs), None)


@dataclass(frozen=True, slots=True)
class ShellReader:
    syntax: ShellSyntax | None
    in_process: bool = False

    def check_context(self, command: str) -> None:
        if self.syntax is None and re.search(
            r"\b(?:worktree|git-wt|wt)\b|\balias\.", command, re.IGNORECASE
        ):
            raise create_worktree.CreateWorktreeError(
                "cannot verify worktree commands passed to this shell reader"
            )


def literal(value: str) -> str:
    if not value or re.search(r"[$`%\n\r]", value):
        raise create_worktree.CreateWorktreeError("use literal worktree arguments")
    return value


def executable(value: str) -> str:
    return value.replace("\\", "/").rsplit("/", 1)[-1].lower().removesuffix(".exe")


def shell_words(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.escape = ""
    return list(lexer)


def shell_reader(header: str, syntax: ShellSyntax) -> ShellReader | None:
    if syntax.here_strings and re.fullmatch(
        r"\s*\$[\w:]+\s*(?:[-+*/%]|\?\?)?=\s*", header
    ):
        return None
    try:
        words = shell_words(re.sub(r"\d*[<>]&\d+", "", header))
    except ValueError:
        return ShellReader(None, in_process=True)
    program = True
    operand = False
    wrapper = ""
    uncertain = False
    for word in words:
        if word and all(character in ";&|()\n" for character in word):
            program, wrapper, uncertain = True, "", False
        elif operand:
            operand = False
        elif program:
            if re.match(r"\d*[<>]", word):
                operand = re.fullmatch(r"\d*(?:<<-?|>>?|<)", word) is not None
            elif (
                re.match(r"\w+=", word)
                or word == "--"
                or (
                    (wrapper == "env" and word in {"-i", "--ignore-environment"})
                    or (wrapper == "command" and word == "-p")
                    or (wrapper == "exec" and word in {"-c", "-l"})
                )
            ):
                continue
            elif (wrapper == "env" and word in {"-u", "--unset"}) or (
                wrapper == "exec" and word == "-a"
            ):
                operand = True
            elif word.startswith("-") or re.search(r"[$`%]", word):
                return ShellReader(None, in_process=True)
            elif executable(word) in {"env", "command", "exec", "sudo", "doas", "nice"}:
                wrapper = executable(word)
            elif executable(word) in {"source", ".", "iex", "invoke-expression"}:
                return ShellReader(syntax, in_process=True)
            elif (reader_syntax := ShellSyntax.for_program(word)) is not None:
                return ShellReader(reader_syntax)
            else:
                program = False
                uncertain = executable(word) not in PASSIVE_PROGRAMS | {
                    "cat",
                    "tee",
                    "set-content",
                    "add-content",
                    "out-file",
                }
        elif uncertain and (
            ShellSyntax.for_program(word) is not None
            or word.lower() in {"-c", "-lc", "-command", "/c"}
        ):
            return ShellReader(None, in_process=True)
    return None


def without_literal_documents(command: str, syntax: ShellSyntax) -> str:
    pieces: list[str] = []
    start = index = 0
    quote = ""
    while index < len(command):
        character = command[index]
        if quote:
            if quote == '"' and character == syntax.escape:
                index += 2
                continue
            if character == quote:
                quote = ""
        elif character == "#" and (index == 0 or command[index - 1].isspace()):
            newline = command.find("\n", index)
            index = len(command) if newline == -1 else newline + 1
            continue
        elif syntax.here_strings and re.match(r"@(['\"])\r?\n", command[index:]):
            delimiter = command[index + 1]
            closing = re.search(rf"(?m)^{delimiter}@(?=\s|;|$)", command[index + 2 :])
            if closing is not None:
                end = index + 2 + closing.end()
                body = command[index + 2 : index + 2 + closing.start()]
                if delimiter == '"' and has_placement_expansion(
                    body, syntax, literal=True
                ):
                    raise create_worktree.CreateWorktreeError(
                        "worktree command substitution"
                    )
                header = command[command.rfind("\n", 0, index) + 1 : index]
                reader = shell_reader(header, syntax)
                if reader is not None:
                    reader.check_context(command)
                    if reader.syntax is None or reader.in_process:
                        index = end
                        continue
                    script = without_literal_documents(body, reader.syntax)
                    if needs_placement_check(script, reader.syntax):
                        raise create_worktree.CreateWorktreeError(
                            "worktree commands in shell input require "
                            "the shared creator"
                        )
                blank = re.sub(r"[^\r\n]", " ", command[index + 1 : end - 1])
                pieces.extend((command[start:index], "'" + blank + "'"))
                start = index = end
                continue
        elif (
            syntax.heredocs
            and character == "<"
            and (index == 0 or command[index - 1] != "<")
        ):
            opening = re.match(
                r"<<(-?)[\t ]*(?:(['\"])(.*?)\2|(\w+))(?=[\s;|&<>]|$)",
                command[index:],
            )
            newline = command.find("\n", index)
            while newline != -1 and command[:newline].rstrip("\r").endswith("\\"):
                newline = command.find("\n", newline + 1)
            if opening is not None and newline != -1:
                line = command.rfind("\n", 0, index) + 1
                while line and command[:line].rstrip("\r\n").endswith("\\"):
                    line = command.rfind("\n", 0, line - 1) + 1
                header = command[line:newline].replace("\\\r\n", "").replace("\\\n", "")
                indent = r"\t*" if opening[1] else ""
                closing = re.search(
                    rf"(?m)^{indent}{re.escape(opening[3] or opening[4])}\r?$",
                    command[newline + 1 :],
                )
                if closing is not None:
                    body = command[newline + 1 : newline + 1 + closing.start()]
                    if not opening[2] and has_placement_expansion(
                        body, syntax, literal=True
                    ):
                        raise create_worktree.CreateWorktreeError(
                            "worktree command substitution"
                        )
                    reader = shell_reader(header, syntax)
                    if reader is not None:
                        reader.check_context(command)
                        if reader.syntax is None or reader.in_process:
                            index = newline + 1 + closing.end()
                            continue
                        script = without_literal_documents(body, reader.syntax)
                        if needs_placement_check(script, reader.syntax):
                            raise create_worktree.CreateWorktreeError(
                                "worktree commands in shell input require "
                                "the shared creator"
                            )
                    end = newline + 1 + closing.end()
                    blank = re.sub(r"[^\r\n]", " ", command[newline + 1 : end])
                    pieces.extend((command[start : newline + 1], blank))
                    start = index = end
                    continue
        elif character in "\"'":
            quote = character
        elif character == syntax.escape:
            index += 2
            continue
        index += 1
    pieces.append(command[start:])
    return "".join(pieces)


def substitution_end(command: str, start: int, syntax: ShellSyntax) -> int:
    command = command[:start] + without_literal_documents(command[start:], syntax)
    quotes = [""]
    index = start
    while index < len(command):
        character = command[index]
        quote = quotes[-1]
        if (
            not quote
            and character == "#"
            and (index == 0 or command[index - 1].isspace())
        ):
            newline = command.find("\n", index)
            index = len(command) if newline == -1 else newline + 1
            continue
        if character == syntax.escape and quote != "'":
            index += 2
            continue
        if character in "\"'" and (not quote or character == quote):
            quotes[-1] = "" if quote else character
        elif quote != "'" and command.startswith("$(", index):
            quotes.append("")
            index += 2
            continue
        elif not quote and character == "(":
            quotes.append("")
        elif not quote and character == ")":
            quotes.pop()
            if not quotes:
                return index
        index += 1
    raise ValueError("unclosed command substitution")


def has_placement_expansion(
    command: str,
    syntax: ShellSyntax,
    *,
    literal: bool = False,
) -> bool:
    if not syntax.expansions:
        return False
    quote = ""
    index = 0
    while index < len(command):
        character = command[index]
        if (
            not literal
            and not quote
            and character == "#"
            and (index == 0 or command[index - 1].isspace())
        ):
            newline = command.find("\n", index)
            index = len(command) if newline == -1 else newline + 1
            continue
        if character == syntax.escape and quote != "'":
            index += 2
            continue
        if not literal and character in "\"'" and (not quote or character == quote):
            quote = "" if quote else character
        elif quote != "'" and (
            command.startswith("$(", index) or (syntax.heredocs and character == "`")
        ):
            start = index + (2 if character == "$" else 1)
            end = (
                substitution_end(command, start, syntax)
                if character == "$"
                else command.find("`", start)
            )
            if end == -1:
                raise ValueError("unclosed command substitution")
            nested = without_literal_documents(command[start:end], syntax)
            if needs_placement_check(nested, syntax):
                return True
            index = end
        index += 1
    return False


def nonplacement_operation(action: str) -> bool:
    return action in {"list", "prune", "remove", "repair", "lock", "unlock", "-h"}


def is_worktrunk_executable(value: str) -> bool:
    return executable(value) in {"git-wt", "wt"}


def placement_alias(value: str) -> bool:
    if value.startswith("--config-env="):
        return value.partition("=")[2].partition("=")[0].casefold().startswith("alias.")
    value = value.removeprefix("-c")
    return value.partition("=")[0].casefold().startswith("alias.") and bool(
        re.search(r"\b(?:worktree|git-wt|wt)\b", value.partition("=")[2])
    )


def needs_placement_check(command: str, syntax: ShellSyntax) -> bool:
    if has_placement_expansion(command, syntax):
        return True
    words = shell_words(command)
    start = 0
    for index, word in enumerate(words):
        nested_syntax = ShellSyntax.for_program(words[start])
        if (
            index > start
            and nested_syntax is not None
            and words[index - 1].lower() in {"-c", "-lc", "-command", "/c"}
            and needs_placement_check(
                without_literal_documents(word, nested_syntax), nested_syntax
            )
        ):
            return True
        if placement_alias(word) and (
            word.startswith(("-c", "--config-env="))
            or (index > start and words[index - 1] == "-c")
        ):
            return True
        if word in {"do", "then", "else"} or (
            word and all(character in ";&|()\n" for character in word)
        ):
            start = index + 1
            continue
        if is_worktrunk_executable(word) and (
            index == start
            or executable(words[start]) in {"env", "command", "git"}
            or "=" in words[start]
        ):
            try:
                check_worktrunk(words[index + 1 :])
            except create_worktree.CreateWorktreeError:
                return True
        if (word.startswith("--worktree") or word == "-w") and executable(
            words[start].strip("\"'")
        ) in {"claude", "codex"}:
            return True
        if (
            word == "worktree"
            and executable(words[start]) not in PASSIVE_PROGRAMS
            and index + 1 < len(words)
            and not nonplacement_operation(words[index + 1])
        ):
            return True
    return False


def segments(command: str) -> list[list[str]]:
    groups: list[list[str]] = [[]]
    for token in shell_words(command):
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


def check_worktrunk(arguments: Sequence[str]) -> None:
    if not arguments:
        raise create_worktree.CreateWorktreeError("unsupported Worktrunk operation")
    action = literal(arguments[0])
    if action in {"--help", "-h", "--version", "version", "help", "list"}:
        return
    if action == "step" and len(arguments) > 1 and literal(arguments[1]) == "diff":
        return
    if len(arguments) > 1 and literal(arguments[1]) in {"--help", "-h"}:
        return
    raise create_worktree.CreateWorktreeError(
        "Worktrunk worktree mutations are not supported"
    )


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
    if arguments[index] == "wt":
        check_worktrunk(arguments[index + 1 :])
        return
    if arguments[index] != "worktree":
        if arguments[index].startswith("-") and (
            "worktree" in arguments
            or any(placement_alias(word) for word in arguments)
            or any(is_worktrunk_executable(word) for word in arguments)
        ):
            raise create_worktree.CreateWorktreeError("unsupported Git routing options")
        return
    if index + 1 == len(arguments):
        return
    action = literal(arguments[index + 1])
    if nonplacement_operation(action):
        return
    if action == "add":
        raise create_worktree.CreateWorktreeError(
            "direct git worktree add is not supported"
        )
    mutation = next((item for item in Mutation if item.command == action), None)
    if mutation is None:
        raise create_worktree.CreateWorktreeError("unsupported worktree operation")
    target = destination(arguments[index + 2 :], mutation)
    repo = create_worktree.repository_root(cwd, deadline=deadline)
    create_worktree.validate_destination(repo, cwd / target)


def mutates_worktree(words: Sequence[str]) -> bool:
    if "worktree" not in words:
        return False
    action = words[words.index("worktree") + 1 :]
    return bool(action) and literal(action[0]) in {"add", "move"}


def check_command(
    command: str, cwd: Path, deadline: float, syntax: ShellSyntax
) -> None:
    command = without_literal_documents(command, syntax)
    if not re.search(
        r"\b(?:git(?:-wt)?(?:\.exe)?|wt(?:\.exe)?|worktree)\b|\balias\.",
        command,
        re.IGNORECASE,
    ):
        return
    try:
        if not needs_placement_check(command, syntax):
            return
        if has_placement_expansion(command, syntax):
            raise create_worktree.CreateWorktreeError(
                "worktree shell substitutions cannot be verified; use literal arguments"
            )
        commands = segments(command)
    except ValueError as error:
        if "worktree" in command.lower():
            raise create_worktree.CreateWorktreeError(
                "cannot verify this worktree shell expression"
            ) from error
        return
    for words in commands:
        program = executable(words[0])
        if program in PASSIVE_PROGRAMS:
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
            elif is_worktrunk_executable(words[1]):
                check_worktrunk(words[2:])
            elif "worktree" in words or any(
                is_worktrunk_executable(word) for word in words
            ):
                raise create_worktree.CreateWorktreeError("unsupported Git environment")
        elif program == "git":
            check_git(words[1:], cwd, deadline)
        elif is_worktrunk_executable(words[0]):
            check_worktrunk(words[1:])
        elif (nested_syntax := ShellSyntax.for_program(program)) is not None:
            for index, word in enumerate(words[1:], start=1):
                if word.lower() in {"-c", "-lc", "-command", "/c"}:
                    check_command(
                        " ".join(words[index + 1 :]), cwd, deadline, nested_syntax
                    )
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
            or any(is_worktrunk_executable(word) for word in words[1:])
            or any(placement_alias(word) for word in words[1:])
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
    syntax = ShellSyntax.for_program(name) or ShellSyntax.for_program(
        str(arguments.get("shell", ""))
    )
    if syntax is None:
        syntax = (
            ShellSyntax.POWERSHELL if sys.platform == "win32" else ShellSyntax.POSIX
        )
    check_command(command, Path(cwd), time.monotonic() + 10, syntax)


def deny(payload: Mapping[str, object], reason: str) -> int:
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


def main(extra_check: Callable[[Mapping[str, object]], str] | None = None) -> int:
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
        if extra_check is not None and (reason := extra_check(payload)):
            return deny(payload, reason)
    except (create_worktree.CreateWorktreeError, ValueError) as error:
        interpreter = "python" if sys.platform == "win32" else "python3"
        script = Path(__file__).with_name("create_worktree.py")
        reason = (
            f"{error}. Use Core's engineering:open-worktree command: "
            f'{interpreter} -B "{script}" --repo <repository> <Type/Name>.'
        )
        return deny(payload, reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
