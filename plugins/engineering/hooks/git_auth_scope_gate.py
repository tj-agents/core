r"""PreToolUse hook: an agent never widens the account's credential.

The mistake this exists to make impossible: a `gh api` call is refused for lack of
permission, and the agent reaches for `gh auth refresh -h github.com -s admin:org`
to clear it. Classic OAuth scopes are **account-wide**. That command does not grant
"admin on the organization being worked on" — it grants organization administration
across every organization the account belongs to, employers' included, to read one
setting in one of them. It is the widest possible answer to the narrowest possible
question, and it is irreversible from the agent's side: only the human can revoke it.

So the whole command family is refused, not just the scope flags. There is no
legitimate reason for an agent to authenticate on the human's behalf, and matching on
`-s` / `--scopes` would miss scopes that arrive through a variable or a heredoc.
Authentication is the human's action; the agent's job is to ask for the narrow
credential and say exactly what it needs. The `git-auth` skill is the procedure.

What is allowed, so ordinary work is never in the way: every other `gh auth`
subcommand — `status`, `token`, `setup-git`, `switch` — reads or selects a credential
that already exists and widens nothing. `gh auth login --help`, which executes nothing.
Every non-`gh` command. Every `gh api` call, including the one that was refused: a 403
is a finding to report, not a thing to escalate around.

Two failure directions, deliberately different:

* **Recognising** the command fails OPEN. An unparseable payload, an unknown shape, a
  tool this gate does not understand — allow, because a credential gate that wedges
  unrelated shell calls gets switched off, and then it protects nothing.
* **Refusing** a command already identified fails CLOSED. Once the pattern matches, no
  later exception may turn a confirmed `gh auth refresh -s admin:org` into a silent
  allow. This gate's failure mode is the only irreversible one here, so the two stages
  do not share an exception handler.

Residual risk this cannot see, stated rather than implied. A shell can hide the token
pair from any regex: `gh auth $(echo refresh)`, or `powershell -EncodedCommand <base64>`,
which arrives already opaque. And the credential can be installed without `gh auth` at
all, by writing `~/.config/gh/hosts.yml` (`%APPDATA%\GitHub CLI\hosts.yml`) directly —
this gate wires only to shell tools, never to `Write`/`Edit`, so that path is outside its
jurisdiction entirely. None of these is what a careless agent reaches for, which is what
this gate is for; a determined one was never going to be stopped by a matcher.

Wired for BOTH harnesses. Claude's matcher is ``Bash|PowerShell``; Codex's is
``exec_command|unified_exec|local_shell|shell``. A ``command`` arriving as an argv
list (``["bash","-lc",...]``), or under ``cmd`` / ``script`` / ``input`` /
``action.command``, is unwrapped.

No opt-in file. Every other gate here is per-repo policy a repo may reasonably decline;
this one is a property of the human's account, identical in every repo, and a repo that
had forgotten to opt in is exactly where the mistake would land.

Contract: exit 0 = allow; exit 2 = block (stderr is fed back to the agent).
"""

import json
import re
import sys
from pathlib import Path

from hook_runtime import claim_invocation

# This message is what the agent acts on, and Windows defaults these streams to cp1252.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

HOOK_NAME = "git-auth-scope-gate"

# Lowercased. A shell tool not named here cannot be wired to this gate, because a matcher the
# hook ignores is enforcement that is inert while looking wired.
SHELL_TOOLS = {"bash", "powershell", "shell", "exec_command", "unified_exec", "local_shell"}

# A line continuation is whitespace to the shell and is not whitespace to `\s`: PowerShell's
# backtick and sh's backslash both bridge `gh auth` on one line to `refresh` on the next, and
# without collapsing them first the pattern below simply does not match a command that runs.
CONTINUATION = re.compile(r"[`\\][ \t]*\r?\n[ \t]*")

# Only the two subcommands that mint or widen a credential. `gh auth status|token|setup-git|switch`
# read or select what already exists, so they are deliberately absent.
#
# `gh` arrives as a bare name, an absolute path, or `gh.exe` — and on Windows, where this runs, the
# `.exe` form is exactly what a quoted Program Files path produces. Demanding whitespace straight
# after `gh` let every one of those through, so the optional extension and a closing quote are part
# of the pattern, case-insensitively for `GH.EXE`.
BLOCKED = re.compile(r"""\bgh(?:\.exe)?["']?\s+auth\s+(refresh|login)\b""", re.IGNORECASE)

# Where one command ends and the next begins, so `--help` is only read from the invocation it
# belongs to and never borrowed from a later one.
SEPARATOR = re.compile(r"[;&|\r\n]")

MESSAGE = """GIT-AUTH GATE: `gh auth {subcommand}` is refused — an agent does not authenticate on the human's behalf.

Classic OAuth scopes are account-wide. A scope requested here is granted across EVERY organization this account belongs to, including employers', not just the one being worked on. Only the human can revoke it afterwards.

Do this instead:
  1. Ask for a FINE-GRAINED personal access token whose resource owner is the single organization that owns this repository, carrying only the permission the refused call needs.
  2. Use it for that one call: GH_TOKEN=<token> gh api <endpoint>
  3. Name three things when asking: the organization, the exact permission, and the single call it is for.

If that credential is not available, record the check as unavailable, say what it would have told you, and continue with what can be established without it. A broader credential is never the fallback, and a refused check is never a reason to guess and present the guess as a finding.

The `git-auth` skill is the full procedure."""

# Used when the refusal path itself throws. It must need nothing but a literal, because whatever
# broke may be the formatting, the claim store, or anything else the normal path depends on.
FALLBACK_MESSAGE = (
    "GIT-AUTH GATE: refused. This command authenticates on the human's behalf and would widen "
    "the credential across every organization the account belongs to. The gate could not build "
    "its full message, so it is refusing on the match alone. See the `git-auth` skill."
)


def _shell_script_from_list(parts):
    """A shell tool invoked as ``["bash", "-lc", "<script>"]`` carries its script in the last arg."""
    cleaned = [str(p) for p in parts if isinstance(p, (str, int, float))]
    if not cleaned:
        return None
    if len(cleaned) >= 2 and re.fullmatch(r"-[a-z]*c", cleaned[1]) and Path(cleaned[0]).name in (
        "bash",
        "sh",
        "zsh",
        "dash",
        "pwsh",
        "powershell",
    ):
        return cleaned[-1]
    return " ".join(cleaned)


def extract_command(tool_name, tool_input):
    """The shell text a Claude Bash/PowerShell or Codex exec/unified-exec call would run, or None."""
    if not isinstance(tool_input, dict):
        return None
    if str(tool_name).lower() not in SHELL_TOOLS:
        return None
    for key in ("command", "cmd", "script", "input"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list):
            joined = _shell_script_from_list(value)
            if joined and joined.strip():
                return joined
    action = tool_input.get("action")
    if isinstance(action, dict):
        value = action.get("command") or action.get("cmd")
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list):
            joined = _shell_script_from_list(value)
            if joined and joined.strip():
                return joined
    return None


def find_violation(command):
    """The blocked subcommand name, or None when this command mints no credential."""
    joined = CONTINUATION.sub(" ", command or "")
    match = BLOCKED.search(joined)
    if match is None:
        return None
    # `--help` prints flags and executes nothing, and an agent may legitimately need to read them
    # to build the request the skill asks for. Read it only from this invocation, not a later one.
    rest = SEPARATOR.split(joined[match.end():], 1)[0]
    if "--help" in rest:
        return None
    return match.group(1)


def main():
    try:
        data = json.load(sys.stdin)
        command = extract_command(data.get("tool_name", ""), data.get("tool_input") or {})
        subcommand = find_violation(command) if command else None
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - recognition fails open; see the module docstring
        sys.exit(0)

    if subcommand is None:
        sys.exit(0)

    # Past here the command is known to authenticate on the human's behalf. Nothing below may
    # downgrade that to an allow, so its failures are absorbed into the refusal rather than
    # escaping to the recognition stage's handler.
    try:
        if not claim_invocation(data, HOOK_NAME):
            sys.exit(0)
        sys.stderr.write(MESSAGE.format(subcommand=subcommand))
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - a confirmed match is never allowed through by a later fault
        sys.stderr.write(FALLBACK_MESSAGE)
    sys.exit(2)


if __name__ == "__main__":
    main()
