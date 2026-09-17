r"""SessionStart hook: inject the always-loaded always-on instructions.

The instructions — take the scalable approach, questions before actions, act on reversible work — applies to
every task and is bound to no file path, so the write-time route table cannot deliver it and no skill
summons it. This hook reads ``standards/process/ALWAYS_ON_INSTRUCTIONS.md`` from the installed plugin and prints it as
SessionStart context, so the instructions are present from the first turn and, with the plugin's compact/resume
matchers, again after every compaction — without copying the rules into any repo's own AGENTS.md.

Beside the instructions it injects the conditional rules the repository has declared itself subject to, resolved
by ``dev_rules`` from its ``.agents/profile.json``. The instructions are identical everywhere; a rule arrives only
where its ``applies_when`` matches the declared profile.

Scope: a repo opts in as the skill router does, by carrying ``.agents/skill-routes.json``, or by
declaring a profile.
Outside a standards-managed repo the hook prints nothing, so it stays silent in unrelated projects on the
same machine. Anything unexpected exits 0 printing nothing: a broken instructions hook must never wedge a
session.

Both harnesses run this one file from the plugin's ``hooks/`` directory and both add a SessionStart
hook's stdout to the session context, so plain stdout is the portable injection form; a Claude-only JSON
envelope is deliberately avoided so Codex receives the same instructions.
"""

import json
import sys
from pathlib import Path

from dev_rules import PROFILE_FILE, resolve_rules
from hook_runtime import claim_invocation, own_payload_root

# The instructions carry non-ASCII punctuation, and this text is what the agent reads. Windows defaults these
# streams to cp1252, which renders it as mojibake.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROUTES_FILE = ".agents/skill-routes.json"
INSTRUCTIONS_DOC = ("standards", "process", "ALWAYS_ON_INSTRUCTIONS.md")
HOOK_NAME = "always_on_instructions"


def _read_payload():
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _project_dir(data):
    for key in ("cwd", "workspace", "workspaceRoot", "project_dir", "projectDir"):
        value = data.get(key)
        if value:
            try:
                return Path(value)
            except (TypeError, ValueError):
                continue
    return Path.cwd()


def _is_standards_repo(project_dir):
    # Walk up so a session started in a subdirectory still opts in.
    try:
        current = project_dir.resolve()
    except OSError:
        return False
    for directory in (current, *current.parents):
        if (directory / ROUTES_FILE).is_file() or (directory / PROFILE_FILE).is_file():
            return True
    return False


def main():
    data = _read_payload()
    project_dir = _project_dir(data)
    if not _is_standards_repo(project_dir):
        return 0
    payload_root = own_payload_root(__file__)
    sections = []
    try:
        instructions = payload_root.joinpath(*INSTRUCTIONS_DOC).read_text(encoding="utf-8").strip()
    except OSError:
        instructions = ""
    if instructions:
        sections.append(instructions)
    sections.extend(text for _, text in resolve_rules(project_dir, payload_root))
    if not sections:
        return 0
    # A payload-less vendored copy must not suppress the installed plugin copy that can inject the
    # instructions. Claim only after this copy has proved it has non-empty context to emit.
    if not claim_invocation(data, HOOK_NAME):
        return 0
    sys.stdout.write("\n\n".join(sections) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
