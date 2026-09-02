r"""SessionStart hook (Codex only): keep the installed standards marketplaces current.

Codex has no background auto-update for a plugin marketplace - only the manual
``codex plugin marketplace upgrade``. Claude Code has a native one instead (``autoUpdate`` on the
marketplace declaration in settings.json), so this hook exists only for Codex; it is wired in
codex-hooks.json and deliberately absent from hooks.json.

Rate-limited via a local marker file rather than Codex's own config.toml, so this keeps working even if
Codex's config schema changes. A failed or skipped attempt still marks the marker, so a machine with no
network does not retry-and-stall every session - it just waits for the next window.

Scope: gated the same way session_floor is, by ``.agents/skill-routes.json`` - a repo that never opted
into these standards should not pay for a marketplace refresh on every Codex session.
"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from hook_runtime import claim_invocation

HOOK_NAME = "marketplace_refresh"
ROUTES_FILE = ".agents/skill-routes.json"
REFRESH_INTERVAL_SECONDS = 60 * 60
MARKER = Path.home() / ".agent-standards" / "codex-marketplace-refresh.marker"
UPGRADE_TIMEOUT_SECONDS = 20


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


def _due():
    try:
        age = time.time() - MARKER.stat().st_mtime
    except OSError:
        return True
    return age >= REFRESH_INTERVAL_SECONDS


def _mark_attempted():
    try:
        MARKER.parent.mkdir(parents=True, exist_ok=True)
        MARKER.touch(exist_ok=True)
    except OSError:
        pass


def main():
    data = _read_payload()
    if not _is_standards_repo(_project_dir(data)):
        return 0
    if not claim_invocation(data, HOOK_NAME):
        return 0
    if not _due():
        return 0
    codex = shutil.which("codex")
    if codex:
        try:
            subprocess.run(
                [codex, "plugin", "marketplace", "upgrade"],
                timeout=UPGRADE_TIMEOUT_SECONDS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    _mark_attempted()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
