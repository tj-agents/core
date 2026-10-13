import json
import os
import re
import shlex
import sys
from pathlib import Path

from git_auth_scope_gate import extract_command
from hook_runtime import CommandTimeout, claim_invocation, run_command


HOOK_NAME = "worktree-placement-gate"
CONTINUATION = re.compile(r"[`\\][ \t]*\r?\n[ \t]*")
SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SHELL_EXPANSION = re.compile(r"[$%]|`|[*!?\[]")
BOOLEAN_OPTIONS = {
    "--checkout",
    "--detach",
    "--force",
    "--guess-remote",
    "--lock",
    "--no-checkout",
    "--no-track",
    "--quiet",
    "--track",
    "-f",
}
VALUE_OPTIONS = {"--orphan", "--reason"}
ENVIRONMENT_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*\Z")


def block(reason):
    sys.stderr.write(
        "WORKTREE PLACEMENT GATE: " + reason + "\n"
        "Use a standalone native Git command with an absolute checkout and destination, for example:\n"
        "  git -C \"<repository checkout>\" worktree add -b \"<branch>\" -- "
        "\"<repository root>/.worktrees/<flat-branch>\" \"<start-point>\"\n"
    )


def normalize(command):
    return CONTINUATION.sub(" ", command).strip()


def executable_shell_kind(value):
    executable = str(value).replace("\\", "/").rsplit("/", 1)[-1].casefold()
    if executable.endswith(".exe"):
        executable = executable[:-4]
    if executable in {"bash", "sh", "zsh", "dash"}:
        return "bash"
    if executable in {"powershell", "pwsh"}:
        return "powershell"
    return None


def normalized_extraction_input(tool_input):
    if not isinstance(tool_input, dict):
        return tool_input
    normalized = tool_input.copy()
    for container, key in ((normalized, "command"), (normalized, "cmd"), (normalized, "script"), (normalized, "input")):
        value = container.get(key)
        if isinstance(value, list) and value:
            kind = executable_shell_kind(value[0])
            if kind:
                container[key] = [kind, *value[1:]]
    action = tool_input.get("action")
    if isinstance(action, dict):
        normalized_action = action.copy()
        for key in ("command", "cmd"):
            value = normalized_action.get(key)
            if isinstance(value, list) and value:
                kind = executable_shell_kind(value[0])
                if kind:
                    normalized_action[key] = [kind, *value[1:]]
        normalized["action"] = normalized_action
    return normalized


def shell_kind(tool_name, tool_input):
    name = str(tool_name).casefold()
    if name == "powershell":
        return "powershell"
    if name == "bash":
        return "bash"
    shell = tool_input.get("shell") if isinstance(tool_input, dict) else None
    if isinstance(shell, str):
        kind = executable_shell_kind(shell)
        if kind:
            return kind
    for value in (tool_input or {}).values() if isinstance(tool_input, dict) else ():
        if isinstance(value, list) and value:
            kind = executable_shell_kind(value[0])
            if kind:
                return kind
    action = tool_input.get("action") if isinstance(tool_input, dict) else None
    if isinstance(action, dict):
        for key in ("command", "cmd"):
            value = action.get(key)
            if isinstance(value, list) and value:
                kind = executable_shell_kind(value[0])
                if kind:
                    return kind
    return "powershell" if os.name == "nt" else "bash"


def shell_segments(command, kind):
    text = normalize(command)
    if text.startswith("&"):
        text = text[1:].lstrip()
    segments = []
    start = 0
    quote = None
    escaped = False
    for index, character in enumerate(text):
        if escaped:
            escaped = False
            continue
        if quote == "'":
            if character == quote and kind == "powershell" and index + 1 < len(text) and text[index + 1] == quote:
                escaped = True
            elif character == quote:
                quote = None
            continue
        if (kind == "bash" and character == "\\") or (kind == "powershell" and character == "`"):
            escaped = True
            continue
        if quote:
            if character == quote:
                quote = None
            continue
        if character in ("'", '"'):
            quote = character
        elif character in ";|&\n":
            if text[start:index].strip():
                segments.append(text[start:index].strip())
            start = index + 1
    if quote or escaped:
        return None
    if text[start:].strip():
        segments.append(text[start:].strip())
    return segments


def substitution_end(text, index, kind):
    depth = 1
    quote = None
    escaped = False
    while index < len(text):
        character = text[index]
        if escaped:
            escaped = False
        elif quote == "'":
            if character == quote and kind == "powershell" and index + 1 < len(text) and text[index + 1] == quote:
                index += 1
            elif character == quote:
                quote = None
        elif (kind == "bash" and character == "\\") or (kind == "powershell" and character == "`"):
            escaped = True
        elif quote:
            if character == quote:
                quote = None
        elif character in ("'", '"'):
            quote = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def substitution_creations(command, kind):
    text = normalize(command)
    creations = []
    index = 0
    quote = None
    escaped = False
    while index < len(text):
        character = text[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if quote == "'":
            if character == quote and kind == "powershell" and index + 1 < len(text) and text[index + 1] == quote:
                index += 2
                continue
            if character == quote:
                quote = None
            index += 1
            continue
        if (kind == "bash" and character == "\\") or (kind == "powershell" and character == "`"):
            escaped = True
            index += 1
            continue
        if quote:
            if character == quote:
                quote = None
            elif character == "$" and index + 1 < len(text) and text[index + 1] == "(":
                end = substitution_end(text, index + 2, kind)
                if end is not None:
                    content = text[index + 2:end]
                    creations.extend(creation_segments(content, kind))
                    creations.extend(substitution_creations(content, kind))
                    index = end + 1
                    continue
            elif kind == "bash" and character == "`":
                end = text.find("`", index + 1)
                if end != -1:
                    content = text[index + 1:end]
                    creations.extend(creation_segments(content, kind))
                    creations.extend(substitution_creations(content, kind))
                    index = end + 1
                    continue
            index += 1
            continue
        if character in ("'", '"'):
            quote = character
        elif character == "$" and index + 1 < len(text) and text[index + 1] == "(":
            end = substitution_end(text, index + 2, kind)
            if end is not None:
                content = text[index + 2:end]
                creations.extend(creation_segments(content, kind))
                creations.extend(substitution_creations(content, kind))
                index = end
        elif kind == "bash" and character == "`":
            end = text.find("`", index + 1)
            if end != -1:
                content = text[index + 1:end]
                creations.extend(creation_segments(content, kind))
                creations.extend(substitution_creations(content, kind))
                index = end
        index += 1
    return creations


def unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def tokens_of(segment):
    try:
        return [unquote(token) for token in shlex.split(segment, posix=False)]
    except ValueError:
        return None


def git_executable(value):
    name = value.replace("\\", "/").rsplit("/", 1)[-1].casefold()
    return name in {"git", "git.exe"}


def path_is_literal_absolute(value):
    return bool(value) and not SHELL_EXPANSION.search(value) and Path(value).is_absolute()


def git_start(tokens):
    index = 0
    while index < len(tokens) and ENVIRONMENT_ASSIGNMENT.fullmatch(tokens[index]):
        index += 1
    if index < len(tokens) and git_executable(tokens[index]):
        return index
    return None


def worktree_add_index(tokens, start):
    if start is None:
        return None
    index = start + 1
    while index < len(tokens):
        value = tokens[index]
        if value == "worktree":
            return index if index + 1 < len(tokens) and tokens[index + 1] == "add" else None
        if value == "-C":
            index += 2
        elif value.startswith("-C") and len(value) > 2:
            index += 1
        elif value.startswith("-c") and len(value) > 2:
            index += 1
        elif value == "-c":
            index += 2
        else:
            index += 1
    return None


def branch_name(value):
    if value.startswith("refs/heads/"):
        value = value[len("refs/heads/"):]
    if (
        not value
        or any(character in value for character in "~^:\\?*[")
        or value in {".", "..", "HEAD"}
        or re.fullmatch(r"[0-9A-Fa-f]{7,64}", value)
    ):
        return None
    return value


def parse_creation(segment):
    tokens = tokens_of(segment)
    if tokens is None:
        return "invalid", None
    start = git_start(tokens)
    add_index = worktree_add_index(tokens, start)
    if add_index is None:
        return None, None
    if start != 0 or any(SHELL_EXPANSION.search(value) for value in tokens):
        return "invalid", None
    checkout = None
    index = start + 1
    while index < add_index:
        value = tokens[index]
        if value == "-C":
            if index + 1 >= add_index or checkout is not None:
                return "invalid", None
            checkout = tokens[index + 1]
            index += 2
        elif value.startswith("-C") and len(value) > 2:
            if checkout is not None:
                return "invalid", None
            checkout = value[2:]
            index += 1
        elif value == "-c":
            if index + 1 >= add_index:
                return "invalid", None
            index += 2
        elif value.startswith("-c") and len(value) > 2:
            index += 1
        else:
            return "invalid", None
    if index != add_index or not path_is_literal_absolute(checkout):
        return "invalid", None

    index = add_index + 2
    declared_branch = None
    detached = False
    while index < len(tokens) and tokens[index] != "--":
        value = tokens[index]
        if value in {"-b", "-B"}:
            if index + 1 >= len(tokens):
                return "invalid", None
            declared_branch = tokens[index + 1]
            index += 2
        elif value.startswith("-b") and len(value) > 2:
            declared_branch = value[2:]
            index += 1
        elif value.startswith("-B") and len(value) > 2:
            declared_branch = value[2:]
            index += 1
        elif value in VALUE_OPTIONS:
            if index + 1 >= len(tokens):
                return "invalid", None
            index += 2
        elif value.startswith("--lock=") or any(value.startswith(option + "=") for option in VALUE_OPTIONS):
            index += 1
        elif value in BOOLEAN_OPTIONS:
            detached = detached or value == "--detach"
            index += 1
        else:
            return "invalid", None
    if index >= len(tokens) or tokens[index] != "--":
        return "invalid", None
    remaining = tokens[index + 1:]
    if len(remaining) not in {1, 2}:
        return "invalid", None
    destination = remaining[0]
    positional_branch = branch_name(remaining[1]) if len(remaining) == 2 and not detached else None
    requested_branch = branch_name(declared_branch) if declared_branch else positional_branch
    if declared_branch and requested_branch is None:
        return "invalid", None
    return "creation", (checkout, destination, requested_branch)


def creation_segments(command, kind):
    segments = shell_segments(command, kind)
    if segments is None:
        return [("invalid", None)] if re.search(r"\bgit(?:\.exe)?\b.*\bworktree\s+add\b", command, re.I | re.S) else []
    creations = []
    for segment in segments:
        parsed = parse_creation(segment)
        if parsed[0] is not None:
            creations.append(parsed)
    return creations


def git_environment():
    return {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}


def inherited_git_routing():
    return next(
        (
            key
            for key in ("GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE")
            if os.environ.get(key)
        ),
        None,
    )


def common_root(checkout):
    try:
        completed = run_command(
            ["git", "-C", checkout, "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=git_environment(),
        )
    except (CommandTimeout, OSError):
        return None
    if completed.returncode:
        return None
    lines = completed.stdout.strip().splitlines()
    if len(lines) != 1 or not lines[0]:
        return None
    try:
        common_dir = Path(lines[0]).resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if common_dir.name != ".git":
        return None
    return common_dir.parent


def placement_reason(checkout, destination, requested_branch):
    if not path_is_literal_absolute(destination):
        return "the destination must be a literal absolute path."
    try:
        target = Path(destination)
        if any(part in {".", ".."} for part in target.parts):
            return "the destination must be a flat child path."
        if not SAFE_NAME.fullmatch(target.name):
            return "the destination basename must be a flat safe name."
        if os.path.lexists(str(target)) or target.is_symlink():
            return "the destination already exists or is a symlink."
        root = common_root(checkout)
        if root is None:
            return "Git could not prove the checkout's common repository root."
        expected = root / ".worktrees"
        if expected.exists() and not expected.is_dir():
            return "the repository's .worktrees root must be a real directory."
        resolved_expected = expected.resolve()
        resolved_root = root.resolve()
        if expected.exists() and (
            expected.is_symlink()
            or resolved_expected != expected
            or not resolved_expected.is_relative_to(resolved_root)
        ):
            return "the repository's .worktrees root must be a real directory inside its common repository root."
        resolved_target = target.resolve()
        if resolved_target.parent != resolved_expected:
            return "the destination must be a direct child of the common repository's .worktrees directory."
        if requested_branch is not None and target.name != requested_branch.replace("/", "-"):
            return "the destination basename must equal the supplied branch with `/` flattened to `-`."
    except (OSError, RuntimeError, ValueError):
        return "the checkout and destination could not be resolved safely."
    return None


def main():
    try:
        data = json.load(sys.stdin)
        tool_input = data.get("tool_input") or {}
        command = extract_command(data.get("tool_name", ""), normalized_extraction_input(tool_input))
        if not command:
            return 0
        kind = shell_kind(data.get("tool_name", ""), tool_input)
        segments = shell_segments(command, kind)
        substitutions = substitution_creations(command, kind)
        if segments is None:
            if substitutions:
                creations = substitutions
            else:
                return 0
        else:
            creations = creation_segments(command, kind) + substitutions
        if not creations:
            return 0
    except Exception:
        return 0
    try:
        routing_variable = inherited_git_routing()
        if routing_variable:
            reason = f"{routing_variable} is active, so Git repository routing cannot be proven safely."
        elif substitutions:
            reason = "worktree creation must not be hidden in a shell command substitution."
        elif len(segments) != 1 or len(creations) != 1:
            reason = "worktree creation must not be hidden in a compound shell command."
        elif creations[0][0] != "creation":
            reason = "the native Git worktree-add command is ambiguous or unsupported."
        else:
            reason = placement_reason(*creations[0][1])
        if reason is None:
            return 0
        if not claim_invocation(data, HOOK_NAME):
            reason = "the gate could not safely claim this creation attempt."
        block(reason)
        return 2
    except Exception:
        block("the creation attempt could not be validated safely.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
