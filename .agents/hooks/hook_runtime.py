"""Shared runtime helpers for plugin-delivered and vendored hook copies."""

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path


PLUGIN_ROOT_VARIABLES = ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "CODEX_PLUGIN_ROOT")
CLAIM_PREFIX = "agent-standards-hook-"
CLAIM_RETENTION_SECONDS = 7 * 24 * 60 * 60
CLAIM_PRUNE_INTERVAL_SECONDS = 60 * 60
PRUNE_LOCK_NAME = f"{CLAIM_PREFIX}prune.lock"
PRUNE_MARKER_NAME = f"{CLAIM_PREFIX}last-pruned"


def declared_plugin_root(hook_file):
    """Return the injected plugin root only for its exact ``hooks/<running-hook>`` copy."""
    hook = Path(hook_file).resolve()
    for name in PLUGIN_ROOT_VARIABLES:
        value = os.environ.get(name)
        if not value:
            continue
        try:
            root = Path(value).resolve()
        except OSError:
            continue
        if (root / "hooks" / hook.name).resolve() == hook:
            return root
    return None


def own_payload_root(hook_file):
    """Resolve the payload beside a hook without depending on a harness variable name."""
    root = declared_plugin_root(hook_file)
    if root is not None:
        return root
    return Path(hook_file).resolve().parent.parent


def _invocation_identity(data, hook_name):
    session = data.get("session_id") or data.get("sessionId")
    if not session:
        return None

    tool_use = data.get("tool_use_id") or data.get("toolUseId")
    if tool_use:
        return f"{hook_name}\0{session}\0tool\0{tool_use}"

    event = data.get("hook_event_name") or data.get("hookEventName")
    if not event:
        return None
    turn = data.get("turn_id") or data.get("turnId")
    if not turn:
        transcript = data.get("transcript_path") or data.get("transcriptPath")
        if not transcript:
            return None
        try:
            stat = Path(transcript).stat()
        except OSError:
            return None
        turn = f"transcript:{Path(transcript).resolve()}:{stat.st_size}:{stat.st_mtime_ns}"
    retry = bool(data.get("stop_hook_active") or data.get("stopHookActive"))
    message = data.get("last_assistant_message") or data.get("lastAssistantMessage") or ""
    digest = hashlib.sha256(str(message).encode("utf-8", errors="replace")).hexdigest()
    return f"{hook_name}\0{session}\0{turn}\0{event}\0{retry}\0{digest}"


def _try_acquire_prune_lock(directory):
    """Take the shared pruning lock without delaying hook enforcement."""
    path = directory / PRUNE_LOCK_NAME
    descriptor = None
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR)
        if os.name == "nt":
            import msvcrt

            if os.fstat(descriptor).st_size == 0:
                os.write(descriptor, b"\0")
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        return None
    return descriptor


def _release_prune_lock(descriptor):
    try:
        try:
            if os.name == "nt":
                import msvcrt

                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_UN)
        except OSError:
            pass
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass


def _pruning_is_due(marker, now):
    try:
        last_pruned = marker.stat().st_mtime
    except OSError:
        return True
    return last_pruned > now or now - last_pruned >= CLAIM_PRUNE_INTERVAL_SECONDS


def _remove_expired_claims(directory, current_path, cutoff):
    for path in directory.glob(f"{CLAIM_PREFIX}*.claim"):
        if path == current_path:
            continue
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            continue


def _prune_stale_claims(directory, current_path):
    """Periodically remove expired claims without racing another pruner or the current claim."""
    marker = directory / PRUNE_MARKER_NAME
    if not _pruning_is_due(marker, time.time()):
        return

    descriptor = _try_acquire_prune_lock(directory)
    if descriptor is None:
        return
    try:
        now = time.time()
        if not _pruning_is_due(marker, now):
            return
        _remove_expired_claims(directory, current_path, now - CLAIM_RETENTION_SECONDS)
        try:
            marker.touch(exist_ok=True)
            os.utime(marker, (now, now))
        except OSError:
            pass
    finally:
        _release_prune_lock(descriptor)


def claim_invocation(data, hook_name):
    """Atomically select one of duplicate plugin/project registrations for this event.

    A consuming repo keeps vendored hooks so enforcement exists on an unprovisioned machine. An
    installed plugin registers the same mechanisms. Both receive the same hook invocation id; the
    first copy claims it and the other exits neutrally. If a harness supplies no stable id, do not
    deduplicate: preserving enforcement is more important than avoiding an extra process.
    """
    identity = _invocation_identity(data, hook_name)
    if identity is None:
        return True
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    directory = Path(tempfile.gettempdir())
    path = directory / f"{CLAIM_PREFIX}{key}.claim"
    _prune_stale_claims(directory, path)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    except OSError:
        return True
    try:
        os.write(descriptor, json.dumps({"hook": hook_name}).encode("utf-8"))
    finally:
        os.close(descriptor)
    return True
