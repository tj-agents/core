r"""SessionStart hook (Codex only): keep installed standards plugins current."""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from dev_rules import PROFILE_FILE
from hook_runtime import claim_invocation


HOOK_NAME = "marketplace_refresh"
ROUTES_FILE = ".agents/skill-routes.json"
STATE_DIRECTORY_ENV = "AGENT_STANDARDS_STATE_DIRECTORY"
SUCCESS_INTERVAL_SECONDS = 60 * 60
FAILURE_RETRY_SECONDS = 5 * 60
LOCK_STALE_SECONDS = 10 * 60
COMMAND_TIMEOUT_SECONDS = 60


def _state_directory():
    override = os.environ.get(STATE_DIRECTORY_ENV)
    return Path(override) if override else Path.home() / ".agent-standards"


def _state_path():
    return _state_directory() / "codex-marketplace-refresh.json"


def _lock_path():
    return _state_directory() / "codex-marketplace-refresh.lock"


def _read_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return fallback


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
    try:
        current = project_dir.resolve()
    except OSError:
        return False
    for directory in (current, *current.parents):
        if (directory / ROUTES_FILE).is_file() or (directory / PROFILE_FILE).is_file():
            return True
    return False


def _timestamp(state, name):
    try:
        return float(state.get(name, 0))
    except (TypeError, ValueError):
        return 0


def _due(now=None):
    current = time.time() if now is None else now
    state = _read_json(_state_path(), {})
    last_success = _timestamp(state, "last_success")
    if last_success > 0 and 0 <= current - last_success < SUCCESS_INTERVAL_SECONDS:
        return False
    last_failure = _timestamp(state, "last_failure")
    return not (
        last_failure > 0 and 0 <= current - last_failure < FAILURE_RETRY_SECONDS
    )


def _write_state(success):
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    state = _read_json(path, {})
    key = "last_success" if success else "last_failure"
    state[key] = time.time()
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _acquire_lock():
    path = _lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        try:
            if time.time() - path.stat().st_mtime < LOCK_STALE_SECONDS:
                return False
            path.unlink()
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError:
            return False
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    return True


def _release_lock():
    try:
        _lock_path().unlink()
    except OSError:
        pass


def _codex_home():
    configured = os.environ.get("CODEX_HOME")
    return Path(configured) if configured else Path.home() / ".codex"


def _codex_executable():
    executable = shutil.which("codex")
    if executable:
        return executable
    bundled = _codex_home() / "plugins" / ".plugin-appserver" / "codex.exe"
    return str(bundled) if bundled.is_file() else None


def _codex_environment():
    environment = os.environ.copy()
    environment["CODEX_HOME"] = str(_codex_home())
    return environment


def _run(executable, arguments, capture_output=False):
    # This worker is itself spawned with no console (see start_refresh_if_due). Without
    # CREATE_NO_WINDOW, Windows allocates a brand-new visible console for `executable` when it
    # is a .cmd shim - the stray window popping up on every refresh.
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    return subprocess.run(
        [executable, *arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
        env=_codex_environment(),
        **options,
    )


def _installed_plugins(executable):
    completed = _run(executable, ["plugin", "list", "--json"], capture_output=True)
    if completed.returncode != 0:
        return None
    try:
        result = json.loads(completed.stdout)
    except (ValueError, TypeError):
        return None
    return result.get("installed") if isinstance(result, dict) else None


def refresh_plugins():
    executable = _codex_executable()
    if not executable:
        return False
    listed = _installed_plugins(executable)
    if not isinstance(listed, list):
        return False
    installed = [
        entry
        for entry in listed
        if isinstance(entry, dict)
        and entry.get("installed")
        and entry.get("enabled")
        and entry.get("installPolicy") == "INSTALLED_BY_DEFAULT"
        and entry.get("marketplaceSource", {}).get("sourceType") == "git"
        and entry.get("pluginId")
        and entry.get("marketplaceName")
    ]
    if not installed:
        return False
    success = True
    for marketplace in sorted({entry["marketplaceName"] for entry in installed}):
        completed = _run(executable, ["plugin", "marketplace", "upgrade", marketplace])
        success = completed.returncode == 0 and success
    for entry in installed:
        completed = _run(executable, ["plugin", "add", entry["pluginId"]])
        success = completed.returncode == 0 and success
    return success


def start_refresh_if_due():
    if not _due() or not _acquire_lock():
        return False
    arguments = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker"]
    options = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
        "env": _codex_environment(),
    }
    if os.name == "nt":
        options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NO_WINDOW
        )
    else:
        options["start_new_session"] = True
    try:
        subprocess.Popen(arguments, **options)
    except Exception:
        _release_lock()
        return False
    return True


def run_session_start():
    data = _read_payload()
    if not _is_standards_repo(_project_dir(data)):
        return 0
    if not claim_invocation(data, HOOK_NAME):
        return 0
    start_refresh_if_due()
    return 0


def run_worker():
    try:
        success = refresh_plugins()
        _write_state(success)
        return 0 if success else 1
    finally:
        _release_lock()


def main():
    if len(sys.argv) == 1:
        return run_session_start()
    if sys.argv[1:] == ["--worker"]:
        return run_worker()
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
