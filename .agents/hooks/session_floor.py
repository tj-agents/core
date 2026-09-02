r"""SessionStart hook: inject the always-loaded behavioral floor.

The floor — take the scalable approach, questions before actions, act on reversible work — applies to
every task and is bound to no file path, so the write-time route table cannot deliver it and no skill
summons it. This hook reads ``standards/process/FLOOR.md`` from the installed plugin and prints it as
SessionStart context, so the floor is present from the first turn and, with the plugin's compact/resume
matchers, again after every compaction — without copying the rules into any repo's own AGENTS.md.

Scope: a repo opts in exactly as the skill router does, by carrying ``.agents/skill-routes.json``.
Outside a standards-managed repo the hook prints nothing, so it stays silent in unrelated projects on the
same machine. Anything unexpected exits 0 printing nothing: a broken floor hook must never wedge a
session.

Both harnesses run this one file from the plugin's ``hooks/`` directory and both add a SessionStart
hook's stdout to the session context, so plain stdout is the portable injection form; a Claude-only JSON
envelope is deliberately avoided so Codex receives the same floor.
"""

import json
import sys
from pathlib import Path

from hook_runtime import claim_invocation, own_payload_root

# The floor carries non-ASCII punctuation, and this text is what the agent reads. Windows defaults these
# streams to cp1252, which renders it as mojibake.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROUTES_FILE = ".agents/skill-routes.json"
FLOOR_DOC = ("standards", "process", "FLOOR.md")
HOOK_NAME = "session_floor"


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
        if (directory / ROUTES_FILE).is_file():
            return True
    return False


def main():
    data = _read_payload()
    if not _is_standards_repo(_project_dir(data)):
        return 0
    floor = own_payload_root(__file__).joinpath(*FLOOR_DOC)
    try:
        text = floor.read_text(encoding="utf-8").strip()
    except OSError:
        return 0
    if not text:
        return 0
    # A payload-less vendored copy must not suppress the installed plugin copy that can inject the
    # floor. Claim only after this copy has proved it has non-empty context to emit.
    if not claim_invocation(data, HOOK_NAME):
        return 0
    sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
