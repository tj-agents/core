#!/usr/bin/env python3
"""Refresh and transfer a checkpoint to one fresh Codex process (Python 3.9+)."""

import argparse
from contextlib import closing, redirect_stderr, redirect_stdout
import io
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys

import session_relaunch
import agent_cli


def transfer_script():
    here = Path(__file__).resolve().parent
    for path in (here / "handoff_transfer.py",
                 here.parents[1] / "workflow/workflow/handoff/scripts/transfer.py"):
        if path.is_file():
            return path.resolve()
    raise RuntimeError("The packaged handoff transfer helper is missing; repair the Machine installation.")


def session_id():
    values = {os.environ[key] for key in ("CODEX_THREAD_ID", "CODEX_SESSION_ID") if os.environ.get(key)}
    if len(values) != 1:
        raise ValueError("A single native Codex session identity is required; run from the owning Codex session.")
    return values.pop()


def receipt_path(project):
    profile = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").resolve()
    identity = json.dumps([str(profile), session_id(), str(Path(project).resolve())])
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return session_relaunch.state_directory() / "codex-continuation" / (key + ".json")


def check_owner(predecessor):
    database = session_relaunch.state_directory() / "sessions.db"
    if not database.exists():
        return
    try:
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)) as connection:
            row = connection.execute("SELECT work_item FROM sessions WHERE host = ? AND session_id = ?",
                                     ("codex", predecessor)).fetchone()
    except sqlite3.Error as error:
        raise ValueError(f"Cannot verify the existing execution owner: {error}") from error
    if row and row[0]:
        raise ValueError(f"Recorded execution {row[0]} requires its owner release/claim procedure. "
                         "Continue automatically through workflow:handoff using that existing owner; "
                         "this standalone checkpoint command cannot bypass its lease.")


def pointer(data, helper):
    command = "python" if os.name == "nt" else "python3"
    return (
        "Standards refresh continuation. The predecessor stopped deliverable writes before launch.\n"
        f"Work only in {data['worktree']}. Read the complete checkpoint at {data['goal']} and the "
        f"transfer receipt at {data['receipt']}. Preserve all user limits and reserved decisions.\n"
        "Before any deliverable write, verify the checkpoint and acknowledge this exact attempt using "
        "your own distinct native CODEX_THREAD_ID (never the predecessor's):\n"
        f'{command} -B "{helper}" acknowledge --receipt "{data["receipt"]}" '
        f'--attempt {data["attempt"]} --successor <your-native-session-id> --harness codex\n'
        "If acknowledgement fails, stop: another owner or changed checkpoint requires reconciliation.\n"
        "On success execute the checkpoint's ## Next Steps immediately through its authorized completion "
        "boundary. After the first action, save its actual nonempty evidence and record pickup progress:\n"
        f'{command} -B "{helper}" progress --receipt "{data["receipt"]}" '
        f'--attempt {data["attempt"]} --successor <your-native-session-id> --harness codex '
        '--evidence-file <absolute-first-action-evidence>\n'
        "Startup alone is not pickup or completion. Do not launch another continuation for this attempt.\n"
    )


def continue_session(project, goal, refresh):
    """The caller has checkpointed all context and stopped writing its owned paths."""
    helper = transfer_script()
    transfer = session_relaunch.load(helper, "refresh_handoff_transfer")
    predecessor = session_id()
    project = transfer.absolute(project, "project")
    goal = transfer.absolute(goal, "goal")
    receipt = receipt_path(project).resolve()
    if Path.cwd().resolve() != project:
        raise ValueError("Run continuation from the exact project directory.")
    check_owner(predecessor)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with transfer.lock(receipt):
        data = transfer.load(receipt) if receipt.exists() else None
        if data and (data.get("predecessor") != predecessor or data.get("worktree") != str(project)
                     or data.get("goal") != str(goal) or data.get("harness") != "codex"):
            raise ValueError("The continuation receipt belongs to another task or predecessor.")
    if data is None:
        data = transfer.prepare(argparse.Namespace(
            receipt=str(receipt), goal=str(goal), worktree=str(project), predecessor=predecessor,
            harness="codex", owner_reference=None, mode="transfer"))
    if data["state"] != "prepared":
        print(json.dumps({"continuation": data, "retry": "Inspect this receipt and its launcher evidence; "
                          "do not launch another successor or reclaim writes."}))
        return 0 if data["state"] in {"submitted", "acknowledged", "active"} else 3
    transfer.verify_pickup(data)
    if refresh():
        print(json.dumps({"continuation": "refresh_failed", "receipt": str(receipt),
                          "retry": "Fix the reported refresh failure, then repeat the same command and receipt."}))
        return 1
    launcher = session_relaunch.load(
        session_relaunch.utility_script("handoff-codex", "launch_codex.py"), "refresh_codex_launcher")
    prompt = receipt.with_suffix(receipt.suffix + ".prompt.md")
    prompt.write_text(pointer(data, helper), encoding="utf-8")
    transfer.mutate(argparse.Namespace(command="begin", receipt=str(receipt), attempt=data["attempt"],
                                       predecessor=predecessor))
    startup = agent_cli.handoff_status_path()
    with transfer.lock(receipt):
        current = transfer.load(receipt)
        current["launch_status"] = str(startup)
        transfer.save(receipt, current)
    output = io.StringIO()
    evidence = receipt.with_suffix(receipt.suffix + ".launch.txt")
    try:
        with redirect_stdout(output), redirect_stderr(output):
            result = launcher.main(["--working-directory", str(project), "--prompt-path", str(prompt),
                                    "--title", "Codex standards continuation", "--status-file", str(startup)])
    except BaseException:
        evidence.write_text(output.getvalue() or "Launcher interrupted\n", encoding="utf-8")
        transfer.mutate(argparse.Namespace(command="fail", receipt=str(receipt), attempt=data["attempt"],
                                          outcome="uncertain", reason=f"Launcher interrupted; inspect {startup} and {evidence}."))
        raise
    evidence.write_text(output.getvalue() or f"Launcher exited {result}\n", encoding="utf-8")
    print(output.getvalue(), end="")
    if result == 0:
        data = transfer.mutate(argparse.Namespace(command="submitted", receipt=str(receipt),
                                                attempt=data["attempt"], evidence_file=str(evidence)))
        print(json.dumps({"continuation": data, "pickup": "Observe acknowledge/progress in this same receipt; "
                          "the predecessor remains read-only."}))
        return 0
    if result == 1:
        with transfer.lock(receipt):
            data = transfer.load(receipt)
            if data["state"] == "launching":
                data.update(state="prepared", checkpoint_immutable=False,
                            failed_launch=transfer.evidence(str(evidence)))
                transfer.save(receipt, data)
                print(json.dumps({"continuation": "launch_failed", "receipt": str(receipt),
                                  "evidence": str(evidence), "retry": "Fix the observed launcher prerequisite, "
                                  "then repeat the same command. The launcher confirmed startup failed."}))
                return 1
    transfer.mutate(argparse.Namespace(command="fail", receipt=str(receipt), attempt=data["attempt"],
                                      outcome="uncertain", reason=f"Launcher exited {result}; evidence: {evidence}"))
    print(json.dumps({"continuation": "uncertain", "receipt": str(receipt), "evidence": str(evidence),
                      "retry": "Inspect the startup receipt named in launcher evidence and reconcile this attempt "
                      "through workflow:handoff; never repeat with a new receipt."}))
    return 3
