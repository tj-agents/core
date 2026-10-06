import json
import re
import sys
from pathlib import Path
from git_auth_scope_gate import extract_command
from merge_review_gate import canonical_merge_target_dir, is_codex_invocation, merge_target_dir

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflows"))
from pr_body import validate_pr_body

from hook_runtime import (
    CommandTimeout,
    NETWORK_COMMAND_TIMEOUT_SECONDS,
    claim_invocation,
    own_payload_root,
    run_command,
)

# The message is what the agent acts on, and Windows defaults these streams to cp1252.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

CONFIG_FILE = ".agents/delivery-authorization.json"
BINDING_FILE = ".agents/persistent-workflow-binding.json"
HOOK_NAME = "delivery-binding-gate"
RESULT_KEYS = ("tool_response", "tool_result", "tool_output")

_PR_URL = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/pull/(\d+)")
_TOKEN = re.compile(r"'[^']*'|\"[^\"]*\"|[;&|]+|[^\s'\";&|]+(?:'[^']*'|\"[^\"]*\")?")
_VALUE_FLAGS = {
    "--title", "-t", "--head", "-H", "--base", "-B", "--assignee", "-a",
    "--reviewer", "-r", "--label", "-l", "--milestone", "-m", "--project", "-p",
    "--match-head-commit", "--add-assignee", "--remove-assignee", "--add-reviewer",
    "--remove-reviewer", "--add-label", "--remove-label", "--add-project", "--remove-project",
    "--body", "-b", "--body-file", "-F", "--repo", "-R",
}


def pr_command(command):
    tokens = []
    end = 0
    for match in _TOKEN.finditer(command):
        if command[end:match.start()].strip():
            return None
        if "\n" in command[end:match.start()]:
            tokens.append((";", ";"))
        raw = match.group()
        quoted = raw[0] in "\"'"
        value = raw[1:-1] if quoted else raw
        tokens.append((value, raw))
        end = match.end()
    if command[end:].strip():
        return None
    for index in range(len(tokens) - 2):
        if [raw for _, raw in tokens[index:index + 2]] != ["gh", "pr"]:
            continue
        if index and tokens[index - 1][1] not in {"&&", ";", "&", "||", "|"}:
            continue
        operation = tokens[index + 2][0]
        if operation in {"create", "new", "edit", "merge"}:
            return operation, tokens[index + 3:], index
    return None


def literal(raw):
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    value = raw[1:-1] if raw.startswith('"') and raw.endswith('"') else raw
    if any(char in value for char in "$`%!"):
        raise ValueError("unresolved shell expression")
    return value


def command_options(tokens):
    values = {}
    targets = []
    body_flags = {"--body", "-b", "--body-file", "-F", "--repo", "-R"}
    index = 0
    while index < len(tokens):
        value, raw = tokens[index]
        if any(char in raw for char in ";&|<>") and not raw.startswith(("'", '"')):
            raise ValueError("ambiguous command composition")
        key, equal, _ = value.partition("=")
        if key in _VALUE_FLAGS:
            if equal:
                argument = raw.split("=", 1)[1]
            else:
                index += 1
                if index >= len(tokens):
                    raise ValueError(f"missing {key} value")
                argument = tokens[index][1]
            if key in values:
                raise ValueError(f"duplicate {key}")
            values[key] = literal(argument) if key in body_flags else argument
        elif value.startswith("-"):
            values[key] = True
        elif not value.startswith("-"):
            targets.append(literal(raw))
        index += 1
    return values, targets


def authoritative_body(root, pr, repo=None):
    arguments = [sys.executable, "-B", str(workflow_ops(root)), "--root", str(root),
                 "--workflow-run-id", "pr-body-check", "pr-body-check", "--pr", str(pr)]
    if repo:
        arguments += ["--repo", repo]
    completed = run_command(arguments, capture_output=True, text=True, cwd=str(root),
                            timeout=NETWORK_COMMAND_TIMEOUT_SECONDS)
    try:
        result = json.loads(completed.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise ValueError("authoritative PR body check returned no readable result")
    if completed.returncode or not result.get("validation", {}).get("valid"):
        errors = result.get("validation", {}).get("errors") or [result.get("error") or completed.stderr]
        raise ValueError("; ".join(errors))
    return result


def validate_before(data, command, parsed):
    operation, tokens, prefix = parsed
    try:
        options, targets = command_options(tokens)
        if "--help" in options or "-h" in options:
            return 0
        if operation in {"create", "new", "edit"} and {
                "--fill", "--fill-first", "--fill-verbose", "--editor", "--web", "-w"
        }.intersection(options):
            raise ValueError("interactive or generated body cannot be inspected; supply a body file")
        body_options = {"--body", "-b", "--body-file", "-F"}
        if operation == "edit" and not body_options.intersection(options):
            if not options or {"--editor", "--web", "-w"}.intersection(options):
                raise ValueError("interactive body edit cannot be inspected; supply a body file")
            return 0
        if operation == "merge" and "--disable-auto" in options:
            if not {"--auto", "--merge", "--squash", "--rebase", "--admin"}.intersection(options):
                return 0
        root = Path(working_directory(data)).resolve()
        if operation == "merge":
            canonical = canonical_merge_target_dir(command)
            if (is_codex_invocation(data) or prefix) and canonical is None:
                raise ValueError('use exactly pushd "<absolute-checkout>" && gh pr merge <number> [merge options]')
            root = Path(canonical or merge_target_dir(command, data)).resolve()
            if not targets or not re.fullmatch(r"[1-9]\d*|https://github\.com/[^/]+/[^/]+/pull/[1-9]\d*", targets[0]):
                raise ValueError("name the PR explicitly by number or URL")
            authoritative_body(root, targets[0], options.get("--repo") or options.get("-R"))
            return 0
        if prefix:
            raise ValueError("ambiguous command composition")
        bodies = [options[key] for key in ("--body", "-b") if key in options]
        files = [options[key] for key in ("--body-file", "-F") if key in options]
        if len(bodies) + len(files) != 1:
            raise ValueError("supply one explicit literal --body/-b or readable --body-file/-F")
        if files:
            if files[0] == "-":
                raise ValueError("stdin body cannot be inspected")
            body = (root / files[0]).read_text(encoding="utf-8-sig")
        else:
            body = bodies[0]
        validation = validate_pr_body(body)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))
    except (OSError, ValueError, CommandTimeout) as error:
        announce(f"PR BODY GATE: {error}. Split into a simple gh command with a readable body file; supply nonempty What and Why sections.")
    return 0


def announce(message):
    sys.stderr.write(message)
    sys.exit(2)


def tool_output(data):
    for key in RESULT_KEYS:
        value = data.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for inner in ("stdout", "output", "content", "result"):
                candidate = value.get(inner)
                if isinstance(candidate, str):
                    return candidate
            return json.dumps(value)
    return ""


def created_pr(data):
    match = _PR_URL.search(tool_output(data))
    return match.group(1) if match else None


def working_directory(data):
    for key in ("cwd", "working_directory", "workdir"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    tool_input = data.get("tool_input") or {}
    for key in ("cwd", "working_directory", "workdir"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return "."


def find_config(cwd):
    """The opted-in repo root at or above `cwd`, or None. Walking up rather than asking git keeps a
    worktree, a submodule and a plain checkout on the same answer, as the merge gates do."""
    try:
        base = Path(cwd).resolve()
    except OSError:
        return None
    for candidate in (base, *base.parents):
        if (candidate / CONFIG_FILE).is_file():
            return candidate
    return None


def existing_owner(root):
    """The PR number this worktree's binding already owns, or None when it holds no readable one.

    An unreadable binding counts as none: `delivery-bind` overwrites it, which is the recovery.
    """
    try:
        parsed = json.loads((root / BINDING_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    owner = str(parsed.get("pr", "")).strip() if isinstance(parsed, dict) else ""
    return owner or None


def workflow_ops(root):
    """The operations module beside this hook when it runs from a plugin payload, and the repo's own
    otherwise. A vendored copy and an installed plugin must reach the same code."""
    beside = own_payload_root(__file__) / "workflows" / "workflow_ops.py"
    if beside.is_file():
        return beside
    return root / ".agents" / "workflows" / "workflow_ops.py"


def bind(root, pr):
    try:
        completed = run_command(
            [
                sys.executable,
                "-B",
                str(workflow_ops(root)),
                "--root",
                str(root),
                "--workflow-run-id",
                f"delivery-bind-pr-{pr}",
                "delivery-bind",
                "--pr",
                str(pr),
            ],
            capture_output=True,
            text=True,
            cwd=str(root),
            timeout=NETWORK_COMMAND_TIMEOUT_SECONDS,
        )
    except CommandTimeout as error:
        return None, str(error)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[:800]
        return None, detail or f"delivery-bind exited {completed.returncode}"
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1]), None
    except (ValueError, IndexError):
        return None, "delivery-bind produced no readable result"


def authorization_line(resolution):
    stopped = resolution.get("stopped_by")
    if stopped is None:
        return (
            "Merge authorization: AUTO, from this repository's recorded standing instruction. Once "
            "the exact head is green and independently reviewed, the continuation may enqueue it "
            "without asking."
        )
    if stopped.get("class") == "hold-label":
        return (
            "Merge authorization: ABSENT - this PR carries the `"
            + str(stopped.get("label"))
            + "` hold label, so it stops at its merge gate whatever it touches."
        )
    if stopped.get("class") == "no-recorded-authorization":
        return (
            "Merge authorization: ABSENT - this repository records no standing instruction, so the "
            "delivery stops at its merge gate and asks."
        )
    where = (
        "this repository's own always-stop list"
        if stopped.get("class") == "repository-declared"
        else "the `" + str(stopped.get("class")) + "` class"
    )
    return (
        "Merge authorization: ABSENT - `"
        + str(stopped.get("path"))
        + "` matches "
        + where
        + ", which the standing instruction always stops. Drive it to green and reviewed, then ask "
        "for this one."
    )


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if not isinstance(data, dict):
        return 0
    command = extract_command(data.get("tool_name", ""), data.get("tool_input") or {})
    parsed = pr_command(command) if command else None
    if parsed is None:
        if "--validate-body" in sys.argv and command and re.match(r"^\s*gh\s+pr\s+(?:create|new|edit|merge)\b", command):
            announce("PR BODY GATE: command cannot be inspected. Split into a simple gh command with a readable body file.")
        return 0
    if "--validate-body" in sys.argv:
        return validate_before(data, command, parsed)
    operation, tokens, _ = parsed
    if operation not in {"create", "new", "edit"}:
        return 0
    if operation == "edit" and not any(value.split("=")[0] in {"--body", "-b", "--body-file", "-F"}
                                        for value, _ in tokens):
        return 0
    pr = created_pr(data)
    if operation in {"create", "new"} and pr is None:
        return 0
    try:
        options, targets = command_options(tokens)
        if "--help" in options or "-h" in options:
            return 0
        url_match = _PR_URL.search(tool_output(data))
        target = url_match.group(0) if operation in {"create", "new"} and url_match else (targets[0] if targets else None)
        if target is None:
            announce("PR BODY GATE: body edit requires an explicit PR target for authoritative validation.")
        authoritative_body(Path(working_directory(data)).resolve(), target,
                           options.get("--repo") or options.get("-R"))
    except (OSError, ValueError, CommandTimeout) as error:
        announce(f"PR BODY GATE: authoritative body validation failed: {error}. Repair the PR body and rerun pr-body-check.")
    if operation == "edit":
        return 0

    root = find_config(working_directory(data))
    if root is None:
        return 0  # repo records no standing instruction — not this hook's business
    if not claim_invocation(data, HOOK_NAME):
        return 0

    held = existing_owner(root)
    if held is not None:
        if held == pr:
            return 0  # this same delivery already has its owner; delivery-bind is the only rebinder
        announce(
            "DELIVERY BINDING GATE: PR #"
            + pr
            + " was opened but this worktree still owns PR #"
            + held
            + " through " + BINDING_FILE + ", so the new PR has nothing watching it. That binding "
            "should have been removed at its terminal. Resolve PR #" + held + " or run `python "
            ".agents/workflows/workflow_ops.py --workflow-run-id delivery-release delivery-release "
            "--reason <terminal>`, then bind PR #" + pr + "."
        )

    result, failure = bind(root, pr)
    if failure is not None:
        announce(
            "DELIVERY BINDING GATE: PR #"
            + pr
            + " was opened but its delivery owner could not be bound ("
            + failure
            + "). Run `python .agents/workflows/workflow_ops.py --workflow-run-id "
            "delivery-bind-pr-" + pr + " delivery-bind --pr " + pr + "` and read the error, or "
            "enter the persistent-workflow skill and bind it by hand. Do not leave this PR with no "
            "continuation owning its wait."
        )

    binding = result.get("binding", {})
    resolution = result.get("authorization_resolution", {})
    announce(
        "DELIVERY BINDING GATE: PR #"
        + pr
        + " now has a delivery owner. "
        + BINDING_FILE
        + " binds head "
        + str(binding.get("head", ""))[:12]
        + " in "
        + str(binding.get("worktree", ""))
        + ".\n"
        + authorization_line(resolution)
        + "\nEnter the persistent-workflow skill now and give this binding a continuation that "
        "owns the wait — do not end the turn with the PR unowned. The continuation drives exact-head "
        "CI, dispatches one fresh debugging context per failure, obtains independent current-head "
        "review, and stops at whichever terminal the binding records. Release it with "
        "`workflow_ops.py delivery-release --reason <terminal>` when the delivery ends."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as error:
        sys.stderr.write(f"PR BODY GATE: cannot validate PR body: {error}")
        sys.exit(2)
