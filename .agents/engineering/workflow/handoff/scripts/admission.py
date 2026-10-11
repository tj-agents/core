from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any


FENCE = re.compile(r"```agent-handoff-disposition\s*\n(?P<body>.*?)\n```", re.DOTALL | re.IGNORECASE)
AUTHORIZATION = re.compile(r"standards[- ](?:defect|repair)|source[- ]owner repair", re.I)
BLOCKERS = {"capability", "dependency", "conflict", "capacity"}
STATES = {"blocked", "deferred", "in-progress"}
DISPOSITIONS = {"deferred", "existing-owner"}
EVIDENCE_KINDS = {
    "read-failure",
    "executable-failure",
    "dependency-artifact",
    "native-observer",
    "owner-recovery",
}


def rank_eligible(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priorities = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    eligible = [item for item in items if item.get("eligible") is True]
    return sorted(
        eligible,
        key=lambda item: (
            priorities.get(item.get("priority"), 4),
            -int(item.get("unblocks", 0)),
            item.get("observed_at", ""),
            item.get("record_id", ""),
        ),
    )


def dependency_transition(previous: str | None, current: str, attempted: str | None) -> bool:
    return bool(current and current != previous and current != attempted)


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def absolute_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else None


def nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def selected_disposition(record: Path, record_id: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        body = record.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, "record is unreadable"
    matches = []
    for match in FENCE.finditer(body):
        try:
            value = json.loads(match.group("body"))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("record_id") == record_id:
            matches.append((value, match.group(0)))
    if len(matches) != 1:
        return None, "record id must select exactly one disposition"
    value, entry = matches[0]
    value = dict(value)
    value["_entry_sha256"] = digest_bytes(entry.encode("utf-8"))
    return value, None


def registry_root() -> Path:
    return Path(os.environ.get("AGENT_STATE_DIRECTORY") or Path.home() / ".agents-state") / "cli-sessions"


def process_started_at(pid: int) -> float | None:
    if pid <= 0:
        return None
    if sys.platform.startswith("linux"):
        try:
            stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
            fields = stat.rsplit(")", 1)[1].split()
            if fields[0] == "Z":
                return None
            start_ticks = int(fields[19])
            boot = next(
                int(line.split()[1])
                for line in Path("/proc/stat").read_text(encoding="utf-8").splitlines()
                if line.startswith("btime ")
            )
            return boot + start_ticks / os.sysconf("SC_CLK_TCK")
        except (OSError, StopIteration, ValueError, IndexError):
            return None
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.GetProcessTimes.argtypes = (
                wintypes.HANDLE,
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
                ctypes.POINTER(wintypes.FILETIME),
            )
            kernel32.GetProcessTimes.restype = wintypes.BOOL
            kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
            kernel32.GetExitCodeProcess.restype = wintypes.BOOL
            kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
            kernel32.CloseHandle.restype = wintypes.BOOL
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            handle = kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return None
            try:
                exit_code = wintypes.DWORD()
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)) or exit_code.value != 259:
                    return None
                if not kernel32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time),
                                                 ctypes.byref(kernel), ctypes.byref(user)):
                    return None
            finally:
                kernel32.CloseHandle(handle)
            ticks = (creation.dwHighDateTime << 32) + creation.dwLowDateTime
            return ticks / 10_000_000 - 11_644_473_600
        except (AttributeError, OSError):
            return None
    return None


def registry_owner(owner: dict[str, Any]) -> tuple[dict[str, Any] | None, Path | None]:
    matches = []
    for path in registry_root().glob("*.json"):
        try:
            observed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(observed, dict) or observed.get("session_id") != owner.get("session_id"):
            continue
        if observed.get("host") != owner.get("harness") or observed.get("cwd") != owner.get("worktree"):
            continue
        if not isinstance(observed.get("pid"), int) or not isinstance(observed.get("pid_started_at"), (int, float)):
            continue
        started = process_started_at(observed["pid"])
        if started is None or abs(started - observed["pid_started_at"]) > 1:
            continue
        matches.append((observed, path))
    return matches[0] if len(matches) == 1 else (None, None)


def declared_assets(goal_text: str) -> set[str]:
    values = set()
    for label in ("Owned paths", "Shared resources"):
        match = re.search(rf"(?im)^{label}:\s*(.+)$", goal_text)
        if match:
            values.update(item.strip() for item in match.group(1).split(",") if item.strip())
    return values


def evidence_is_observed(evidence: Any, disposition: dict[str, Any]) -> str | None:
    if not isinstance(evidence, dict):
        return "evidence is required"
    kind = evidence.get("kind")
    path = absolute_path(evidence.get("path"))
    expected = evidence.get("sha256")
    if kind not in EVIDENCE_KINDS or path is None or not nonempty(expected):
        return "evidence requires kind, absolute path, and sha256"
    try:
        actual = digest_bytes(path.read_bytes())
    except OSError:
        return "evidence path is unreadable"
    if actual != expected:
        return "evidence changed"
    blocker = disposition.get("blocked_by")
    if blocker == "capability" and kind not in {"read-failure", "executable-failure"}:
        return "capability evidence has the wrong kind"
    if blocker == "dependency" and kind != "dependency-artifact":
        return "dependency evidence has the wrong kind"
    if blocker in {"conflict", "capacity"} and kind not in {"native-observer", "owner-recovery"}:
        return "owner evidence is required for conflict or capacity"
    if kind == "read-failure":
        target = absolute_path(evidence.get("target"))
        if target is None or not nonempty(evidence.get("operation")) or not nonempty(evidence.get("error")):
            return "read failure evidence is incomplete"
        try:
            target.read_bytes()
        except OSError:
            return None
        return "read target is now available"
    elif kind == "executable-failure":
        executable = evidence.get("executable")
        if not nonempty(executable):
            return "executable failure evidence is incomplete"
        if shutil.which(executable) is not None:
            return "executable is now available"
    elif kind == "dependency-artifact":
        required = evidence.get("required_sha256")
        if not nonempty(evidence.get("artifact_id")) or not nonempty(required):
            return "dependency artifact evidence is incomplete"
        if actual == required:
            return "dependency artifact now satisfies the required fingerprint"
    else:
        owner = disposition.get("owner")
        if not isinstance(owner, dict):
            return "owner evidence is incomplete"
        observed, registry = registry_owner(owner)
        if observed is None or registry is None or path.resolve() != registry.resolve():
            return "current native owner registry evidence is unavailable"
        if evidence.get("registry_session_id") != owner.get("session_id"):
            return "owner evidence does not name the current session"
    return None


def validate(
    record_value: str,
    record_id: str,
    session_id: str,
    prompt_sha256: str,
    callout_id: str,
) -> dict[str, Any]:
    record = absolute_path(record_value)
    if record is None:
        return {"valid": False, "reason": "record must be an absolute path"}
    disposition, error = selected_disposition(record, record_id)
    if error:
        return {"valid": False, "reason": error}
    assert disposition is not None
    required = ("schema_version", "record_id", "kind", "state", "callout", "source_owner", "repair_goal",
                "disposition", "reason", "resolver", "resume_condition", "next_action", "evidence")
    if any(field not in disposition for field in required):
        return {"valid": False, "reason": "disposition is missing required fields"}
    if disposition["schema_version"] != 1 or disposition["record_id"] != record_id:
        return {"valid": False, "reason": "unsupported disposition identity"}
    if disposition.get("kind") not in {"bug", "mistake", "debt"} or disposition.get("state") not in STATES:
        return {"valid": False, "reason": "unsupported problem state"}
    callout = disposition.get("callout")
    if not isinstance(callout, dict) or any(
        callout.get(field) != expected for field, expected in (
            ("session_id", session_id), ("prompt_sha256", prompt_sha256), ("callout_id", callout_id)
        )
    ):
        return {"valid": False, "reason": "callout binding is stale or unrelated"}
    if not all(nonempty(disposition.get(field)) for field in ("source_owner", "reason", "resolver", "resume_condition", "next_action")):
        return {"valid": False, "reason": "disposition fields are incomplete"}
    goal = absolute_path(disposition.get("repair_goal"))
    if goal is None:
        return {"valid": False, "reason": "repair goal must be an absolute path"}
    try:
        goal_text = goal.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {"valid": False, "reason": "repair goal is unreadable"}
    backlink = f"Problem record: {record}#{record_id}"
    if backlink not in goal_text or AUTHORIZATION.search(goal_text) is None:
        return {"valid": False, "reason": "repair goal lacks the required problem-record backlink or authority"}
    choice = disposition.get("disposition")
    if choice not in DISPOSITIONS:
        return {"valid": False, "reason": "unsupported disposition"}
    if choice == "deferred":
        if disposition.get("state") not in {"blocked", "deferred"} or disposition.get("blocked_by") not in BLOCKERS:
            return {"valid": False, "reason": "deferred disposition lacks a supported blocker"}
        if disposition.get("blocked_by") in {"conflict", "capacity"}:
            owner = disposition.get("owner")
            if not isinstance(owner, dict) or not all(
                nonempty(owner.get(field)) for field in ("session_id", "harness", "worktree", "goal")
            ):
                return {"valid": False, "reason": "conflict or capacity disposition lacks an occupied owner"}
            if not absolute_path(owner.get("worktree")) or not absolute_path(owner.get("goal")):
                return {"valid": False, "reason": "occupied owner paths must be absolute"}
            try:
                owner_goal = Path(owner["goal"]).read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                return {"valid": False, "reason": "occupied owner goal is unreadable"}
            if backlink not in owner_goal or f"Native owner: {owner['session_id']}" not in owner_goal:
                return {"valid": False, "reason": "occupied owner goal lacks its exact acknowledgement"}
            if disposition.get("blocked_by") == "conflict" and not (
                declared_assets(goal_text) & declared_assets(owner_goal)
            ):
                return {"valid": False, "reason": "conflict goals lack a declared shared path or resource"}
            if disposition.get("blocked_by") == "capacity":
                owners = disposition.get("occupied_owners")
                budget_match = re.search(r"(?im)^Writer budget:\s*(\d+)\s*$", goal_text)
                if not isinstance(owners, list) or not budget_match or int(budget_match.group(1)) < 1:
                    return {"valid": False, "reason": "capacity lacks an explicit exhausted goal budget"}
                owner_ids = [item.get("session_id") for item in owners if isinstance(item, dict)]
                if len(owners) < int(budget_match.group(1)) or len(owner_ids) != len(set(owner_ids)):
                    return {"valid": False, "reason": "capacity owners do not exhaust the declared budget"}
                if any(not isinstance(item, dict) or registry_owner(item)[0] is None for item in owners):
                    return {"valid": False, "reason": "capacity owners are not currently registered"}
    else:
        owner = disposition.get("owner")
        if not isinstance(owner, dict) or not all(nonempty(owner.get(field)) for field in ("session_id", "harness", "worktree", "goal")):
            return {"valid": False, "reason": "existing owner is incomplete"}
        if not absolute_path(owner.get("worktree")) or not absolute_path(owner.get("goal")):
            return {"valid": False, "reason": "existing owner paths must be absolute"}
        if owner.get("session_id") == session_id or Path(owner["goal"]) != goal:
            return {"valid": False, "reason": "existing owner must be the distinct linked repair owner"}
        try:
            owner_goal = Path(owner["goal"]).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return {"valid": False, "reason": "existing owner goal is unreadable"}
        if backlink not in owner_goal or f"Native owner: {owner['session_id']}" not in owner_goal:
            return {"valid": False, "reason": "existing owner goal lacks the problem-record backlink"}
        if not isinstance(disposition["evidence"], dict) or disposition["evidence"].get("kind") not in {"native-observer", "owner-recovery"}:
            return {"valid": False, "reason": "existing owner requires native registry evidence"}
    evidence_error = evidence_is_observed(disposition["evidence"], disposition)
    if evidence_error:
        return {"valid": False, "reason": evidence_error}
    return {
        "valid": True,
        "event": "agent-handoff-disposition",
        "record": str(record),
        "record_id": record_id,
        "disposition": choice,
        "entry_sha256": disposition["_entry_sha256"],
        "callout_id": callout_id,
        "session_id": session_id,
        "prompt_sha256": prompt_sha256,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="command", required=True)
    check = subcommands.add_parser("check")
    check.add_argument("--record", required=True)
    check.add_argument("--id", required=True)
    check.add_argument("--session", required=True)
    check.add_argument("--prompt-sha256", required=True)
    check.add_argument("--callout-id", required=True)
    args = parser.parse_args()
    result = validate(args.record, args.id, args.session, args.prompt_sha256, args.callout_id)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    sys.exit(main())
