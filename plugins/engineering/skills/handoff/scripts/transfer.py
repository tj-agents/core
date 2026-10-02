import argparse
import errno
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


def absolute(value, label):
    path = Path(value)
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    return path.resolve()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def readiness(goal, receipt):
    lines = goal.read_text(encoding="utf-8").splitlines()
    start = [index for index, line in enumerate(lines) if line.strip() == "## Execution readiness"]
    if len(start) != 1:
        raise ValueError("goal must contain one ## Execution readiness section")
    body = []
    for line in lines[start[0] + 1:]:
        if line.startswith("#"):
            break
        if line.strip():
            body.append(line.strip())
    required = {
        "Verdict": "Verdict: ready",
        "Execution authorization": "Execution authorization: implementation",
        "Transfer": "Transfer: required",
    }
    for key, value in required.items():
        matches = [line for line in body if line.startswith(key + ":")]
        if matches != [value]:
            raise ValueError(f"readiness field missing or ambiguous: {key}")
    receipts = [line for line in body if line.startswith("Receipt:")]
    if len(receipts) != 1:
        raise ValueError("readiness field missing or ambiguous: Receipt")
    if absolute(receipts[0].split(":", 1)[1].strip(), "Receipt") != receipt:
        raise ValueError("readiness field missing or ambiguous: Receipt")
    headings = [index for index, line in enumerate(lines) if line.strip() == "## Next Steps"]
    if len(headings) != 1:
        raise ValueError("goal must contain one ## Next Steps section")
    for line in lines[headings[0] + 1:]:
        if line.startswith("#"):
            break
        if line.strip():
            return
    raise ValueError("## Next Steps must be nonempty")


def git_identity(worktree):
    def run(*args):
        return subprocess.run(
            ["git", "-C", str(worktree), *args],
            capture_output=True,
            text=True,
            timeout=5,
        )

    try:
        root = run("rev-parse", "--show-toplevel")
    except FileNotFoundError:
        if any((parent / ".git").exists() for parent in (worktree, *worktree.parents)):
            raise ValueError("Git executable is required for repository worktrees")
        return None
    if root.returncode:
        message = root.stderr.strip()
        if "not a git repository" in message.lower():
            return None
        raise ValueError(f"cannot inspect Git worktree: {message or 'git rev-parse failed'}")
    branch = run("symbolic-ref", "--short", "HEAD")
    head = run("rev-parse", "HEAD")
    if branch.returncode or head.returncode:
        raise ValueError("Git worktree must have a branch and HEAD")
    return {"root": str(Path(root.stdout.strip()).resolve()), "branch": branch.stdout.strip(), "head": head.stdout.strip()}


@contextmanager
def lock(path):
    lock_path = Path(str(path) + ".lock")
    with open(lock_path, "a+b") as handle:
        handle.seek(0)
        handle.write(b"0")
        handle.flush()
        deadline = time.monotonic() + 10
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as error:
                    if error.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                        raise
                    if time.monotonic() >= deadline:
                        raise ValueError("receipt lock is busy")
                    time.sleep(0.05)
        else:
            import fcntl

            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as error:
                    if error.errno not in {errno.EACCES, errno.EAGAIN}:
                        raise
                    if time.monotonic() >= deadline:
                        raise ValueError("receipt lock is busy")
                    time.sleep(0.05)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def save(path, data):
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid receipt: {error}")


def attempt(data, value):
    if data.get("attempt") != value:
        raise ValueError("attempt does not match receipt")


def evidence(path):
    path = absolute(path, "evidence file")
    if not path.is_file() or not path.stat().st_size:
        raise ValueError("evidence file must exist and be nonempty")
    text = path.read_text(encoding="utf-8")
    return {"path": str(path), "sha256": digest(path), "text": text[:4096]}


def evidence_valid(record):
    if not record:
        return None
    path = Path(record["path"])
    return path.is_file() and path.stat().st_size > 0 and digest(path) == record["sha256"]


def verify_pickup(data):
    if Path.cwd().resolve() != Path(data["worktree"]):
        raise ValueError("current directory does not match receipt worktree")
    goal = Path(data["goal"])
    readiness(goal, Path(data["receipt"]))
    if digest(goal) != data["goal_sha256"]:
        raise ValueError("goal changed since prepare")
    if git_identity(Path(data["worktree"])) != data["git"]:
        raise ValueError("Git identity changed since prepare")


def prepare(args):
    receipt = absolute(args.receipt, "receipt")
    goal = absolute(args.goal, "goal")
    worktree = absolute(args.worktree, "worktree")
    if args.mode != "transfer":
        raise ValueError("receipt preparation is unavailable for this mode")
    if not goal.is_file() or not worktree.is_dir():
        raise ValueError("goal and worktree must exist")
    if Path.cwd().resolve() != worktree:
        raise ValueError("current directory does not match worktree")
    if not args.predecessor.strip():
        raise ValueError("predecessor must be nonempty")
    readiness(goal, receipt)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with lock(receipt):
        if receipt.exists():
            raise ValueError("receipt already exists")
        data = {
            "version": 1,
            "receipt": str(receipt),
            "goal": str(goal),
            "goal_sha256": digest(goal),
            "worktree": str(worktree),
            "git": git_identity(worktree),
            "predecessor": args.predecessor,
            "harness": args.harness,
            "owner_reference": args.owner_reference or None,
            "attempt": str(uuid.uuid4()),
            "state": "prepared",
            "checkpoint_immutable": False,
        }
        save(receipt, data)
    return data


def mutate(args):
    receipt = absolute(args.receipt, "receipt")
    with lock(receipt):
        data = load(receipt)
        attempt(data, args.attempt)
        state = data["state"]
        if args.command == "begin":
            if args.predecessor != data["predecessor"]:
                raise ValueError("begin requires the recorded predecessor")
            if state != "prepared":
                raise ValueError("begin requires prepared state")
            verify_pickup(data)
            data["state"] = "launching"
            data["checkpoint_immutable"] = True
        elif args.command == "submitted":
            record = evidence(args.evidence_file)
            if state not in {"launching", "submitted", "acknowledged", "active"}:
                raise ValueError("submitted requires launching, submitted, acknowledged, or active state")
            existing = data.get("submission")
            if existing and existing["sha256"] != record["sha256"]:
                raise ValueError("submission evidence already differs")
            data["submission"] = record
            if state == "launching":
                data["state"] = "submitted"
        elif args.command == "acknowledge":
            if args.harness != data["harness"]:
                raise ValueError("harness does not match receipt")
            successor = args.successor.strip()
            if not successor or successor == data["predecessor"]:
                raise ValueError("successor must be nonempty and distinct from predecessor")
            verify_pickup(data)
            if state in {"acknowledged", "active"}:
                if data.get("successor") != successor:
                    raise ValueError("receipt already has another successor")
            elif state in {"launching", "submitted", "uncertain"}:
                verify_pickup(data)
                data["successor"] = successor
                data["state"] = "acknowledged"
            else:
                raise ValueError("acknowledge requires launching, submitted, or uncertain state")
        elif args.command == "progress":
            if args.harness != data["harness"]:
                raise ValueError("harness does not match receipt")
            successor = args.successor.strip()
            if state not in {"acknowledged", "active"} or successor != data.get("successor"):
                raise ValueError("progress requires the acknowledged successor")
            data["progress"] = evidence(args.evidence_file)
            data["state"] = "active"
        elif args.command == "fail":
            if args.outcome == "failed" and state == "prepared":
                data["state"] = "failed"
            elif args.outcome == "uncertain" and state in {"launching", "submitted"}:
                data["state"] = "uncertain"
            else:
                raise ValueError("failure outcome is not valid for receipt state")
            data["failure"] = {"reason": args.reason, "outcome": args.outcome}
        save(receipt, data)
    return data


def status(args):
    receipt = absolute(args.receipt, "receipt")
    with lock(receipt):
        data = load(receipt)
    result = dict(data)
    result["evidence_validity"] = {
        "submission": evidence_valid(data.get("submission")),
        "progress": evidence_valid(data.get("progress")),
    }
    return result


def parser():
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--receipt", required=True)
    prepare_parser.add_argument("--goal", required=True)
    prepare_parser.add_argument("--worktree", required=True)
    prepare_parser.add_argument("--predecessor", required=True)
    prepare_parser.add_argument("--harness", required=True, choices=("codex", "claude"))
    prepare_parser.add_argument("--owner-reference")
    prepare_parser.add_argument("--mode", default="transfer", choices=("transfer", "planning-only", "prompt-only", "inline"))
    for name in ("begin", "submitted", "acknowledge", "progress", "fail"):
        item = commands.add_parser(name)
        item.add_argument("--receipt", required=True)
        item.add_argument("--attempt", required=True)
        if name == "begin":
            item.add_argument("--predecessor", required=True)
        if name in {"submitted", "progress"}:
            item.add_argument("--evidence-file", required=True)
        if name in {"acknowledge", "progress"}:
            item.add_argument("--successor", required=True)
            item.add_argument("--harness", required=True, choices=("codex", "claude"))
        if name == "fail":
            item.add_argument("--reason", required=True)
            item.add_argument("--outcome", required=True, choices=("failed", "uncertain"))
    status_parser = commands.add_parser("status")
    status_parser.add_argument("--receipt", required=True)
    return root


def main():
    try:
        args = parser().parse_args()
        result = prepare(args) if args.command == "prepare" else status(args) if args.command == "status" else mutate(args)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as error:
        print(f"transfer: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
