import argparse
import hashlib
import importlib
import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cleanup_proof
import worktree_sweep

SCHEMA_VERSION = 1
Json = dict[str, Any]
Identity = dict[str, int | float]


class CleanupError(RuntimeError):
    pass


def load_session_close(path: str | Path | None = None) -> Any:
    candidate = Path(path) if path else Path(__file__).with_name("session_close.py")
    if not candidate.is_file():
        raise CleanupError("declared Agent cleanup launcher is unavailable")
    if str(candidate.parent) not in sys.path:
        sys.path.insert(0, str(candidate.parent))
    spec = importlib.util.spec_from_file_location("targeted_cleanup_session_close", candidate)
    if spec is None or spec.loader is None:
        raise CleanupError("declared Agent cleanup launcher is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity(module: Any, pid: int) -> Identity:
    info = process_info(pid)
    if info is None or not module.valid_identity(info.pid, info.started_at):
        raise CleanupError("process identity is unavailable")
    return {"pid": info.pid, "started_at": info.started_at}


def process_info(pid: int) -> Any:
    processes: Any = importlib.import_module("tj_cli.processes")
    return processes.process_info(pid)


def under(module: Any, child: str | Path, parent: str | Path) -> bool:
    return bool(module.under_or_equal(child, parent))


def state_directory() -> Path:
    configured = os.environ.get("AGENT_STATE_DIRECTORY")
    return Path(configured) if configured else Path.home() / ".agents-state"


def atomic_json(path: Path, value: Json) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def obligation_path(worktree: str | Path) -> Path:
    return state_directory() / "merge-cleanup" / "targeted-obligations" / f"{digest(str(Path(worktree).resolve()))}.json"


def receipt_path(obligation: Json) -> Path:
    return state_directory() / "merge-cleanup" / "targeted-receipts" / f"{obligation['obligation_id']}.json"


def lock_path(obligation_path: str | Path) -> Path:
    return Path(obligation_path).with_suffix(".lock")


@contextmanager
def obligation_lock(path: str | Path) -> Iterator[None]:
    lock = lock_path(path)
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("a+b") as stream:
        deadline = time.monotonic() + 2
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            stream.write(b"\0")
            stream.flush()
            while True:
                try:
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as error:
                    if time.monotonic() >= deadline:
                        raise CleanupError("targeted cleanup lock acquisition timed out") from error
                    time.sleep(0.01)
        else:
            fcntl: Any = importlib.import_module("fcntl")
            while True:
                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError as error:
                    if time.monotonic() >= deadline:
                        raise CleanupError("targeted cleanup lock acquisition timed out") from error
                    time.sleep(0.01)
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl_unlock: Any = importlib.import_module("fcntl")
                fcntl_unlock.flock(stream.fileno(), fcntl_unlock.LOCK_UN)


def safe_runtime(module: Any, target: Path) -> None:
    for path in (Path(__file__), Path(cleanup_proof.__file__), Path(worktree_sweep.__file__), Path(module.__file__)):
        if under(module, path, target):
            raise CleanupError("targeted cleanup runtime is inside the removal target")


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_identity(value: object) -> bool:
    return (isinstance(value, dict) and set(value) == {"pid", "started_at"}
            and type(value["pid"]) is int and value["pid"] > 0
            and isinstance(value["started_at"], (int, float)) and value["started_at"] > 0)


def identity_value(value: object) -> Identity | None:
    if not valid_identity(value) or not isinstance(value, dict):
        return None
    return {"pid": value["pid"], "started_at": value["started_at"]}


def owner(host: object, session_id: object) -> dict[str, str]:
    if not nonempty(host) or not nonempty(session_id):
        raise CleanupError("targeted cleanup requires owner host and session id")
    if not isinstance(host, str) or not isinstance(session_id, str):
        raise CleanupError("targeted cleanup requires owner host and session id")
    return {"host": host.strip(), "session_id": session_id.strip()}


def load(path: str | Path) -> Json:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CleanupError(f"targeted cleanup obligation is unreadable: {error}") from error
    required = {
        "schema_version", "kind", "obligation_id", "state", "owner", "primary", "worktree", "branch",
        "head", "pr", "repository", "holders", "created_at", "updated_at", "reason",
        "worker", "launch", "launch_token", "identity_sha256",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise CleanupError("targeted cleanup obligation has an invalid shape")
    if value["schema_version"] != SCHEMA_VERSION or value["kind"] != "targeted-cleanup":
        raise CleanupError("targeted cleanup obligation has an unsupported schema")
    if value["state"] not in {"pending", "running", "verified", "retained", "refused", "timed_out"}:
        raise CleanupError("targeted cleanup obligation has an invalid state")
    owner(value["owner"].get("host") if isinstance(value["owner"], dict) else None,
          value["owner"].get("session_id") if isinstance(value["owner"], dict) else None)
    if not all(nonempty(value[key]) for key in ("primary", "worktree", "branch", "head", "obligation_id")):
        raise CleanupError("targeted cleanup obligation has invalid identity")
    if type(value["pr"]) is not int or value["pr"] < 1 or not isinstance(value["holders"], list):
        raise CleanupError("targeted cleanup obligation has invalid cleanup context")
    if not all(valid_identity(holder) for holder in value["holders"]):
        raise CleanupError("targeted cleanup obligation has invalid holder identities")
    if not isinstance(value["launch_token"], str) or len(value["launch_token"]) < 16:
        raise CleanupError("targeted cleanup obligation has invalid launch token")
    if not isinstance(value["identity_sha256"], str) or len(value["identity_sha256"]) != 64:
        raise CleanupError("targeted cleanup obligation has invalid identity digest")
    if value["identity_sha256"] != immutable_digest(value):
        raise CleanupError("targeted cleanup obligation identity changed")
    if value["launch"] is not None and (not isinstance(value["launch"], dict)
                                         or set(value["launch"]) != {"token", "launcher"}
                                         or value["launch"].get("token") != value["launch_token"]
                                         or not valid_identity(value["launch"].get("launcher"))):
        raise CleanupError("targeted cleanup obligation has invalid launch acknowledgement")
    worker = value["worker"]
    if worker is not None and not valid_identity(worker):
        raise CleanupError("targeted cleanup obligation has invalid worker acknowledgement")
    return value


def immutable_value(obligation: Json) -> Json:
    return {key: obligation[key] for key in (
        "owner", "primary", "worktree", "branch", "head", "pr", "repository", "holders",
    )}


def immutable_digest(obligation: Json) -> str:
    return hashlib.sha256(json.dumps(immutable_value(obligation), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def require_pinned(obligation: Json, identity_sha256: str, token: str, require_launch: bool = False) -> None:
    if obligation["identity_sha256"] != identity_sha256:
        raise CleanupError("targeted cleanup obligation identity changed")
    if obligation["launch_token"] != token:
        raise CleanupError("targeted cleanup launch token changed")
    if require_launch:
        launch = obligation["launch"]
        if not isinstance(launch, dict) or launch.get("token") != token:
            raise CleanupError("targeted cleanup requires a recorded launch")


def save(path: str | Path, obligation: Json, state: str | None = None, reason: str | None = None) -> Json:
    path = Path(path)
    if state is not None:
        obligation["state"] = state
    obligation["reason"] = reason
    obligation["updated_at"] = time.time()
    atomic_json(path, obligation)
    atomic_json(receipt_path(obligation), obligation)
    return obligation


def prepare(primary: str | Path, worktree: str | Path, branch: str, head: str, pr: int, repository: str,
            owner_value: dict[str, str], holders: Iterable[Identity] = (), retained: bool = False) -> tuple[Path, Json]:
    primary = Path(primary).resolve()
    worktree = Path(worktree).resolve()
    holders = list(holders)
    if not all(valid_identity(holder) for holder in holders):
        raise CleanupError("targeted cleanup holders require exact pid and start identities")
    if len({(holder["pid"], holder["started_at"]) for holder in holders}) != len(holders):
        raise CleanupError("targeted cleanup holders must be unique")
    launch_token = uuid.uuid4().hex
    obligation = {
        "schema_version": SCHEMA_VERSION,
        "kind": "targeted-cleanup",
        "obligation_id": uuid.uuid4().hex,
        "state": "retained" if retained else "pending",
        "owner": owner_value,
        "primary": str(primary),
        "worktree": str(worktree),
        "branch": branch,
        "head": head,
        "pr": pr,
        "repository": repository,
        "holders": list(holders),
        "created_at": time.time(),
        "updated_at": time.time(),
        "reason": "explicitly retained" if retained else None,
        "worker": None,
        "launch": None,
        "launch_token": launch_token,
        "identity_sha256": "",
    }
    obligation["identity_sha256"] = immutable_digest(obligation)
    path = obligation_path(worktree)
    with obligation_lock(path):
        if path.is_file():
            existing = load(path)
            if existing["identity_sha256"] != obligation["identity_sha256"]:
                raise CleanupError("targeted cleanup obligation conflicts with existing worktree identity")
            return path, existing
        atomic_json(path, obligation)
        atomic_json(receipt_path(obligation), obligation)
        return path, obligation


def registered(primary: Path, worktree: Path) -> bool | None:
    listing = worktree_sweep.git(primary, "worktree", "list", "--porcelain")
    if listing.returncode:
        return None
    return any(Path(entry.get("path", "")).resolve() == worktree for entry in worktree_sweep.parse_worktrees(listing.stdout))


def holder_state(module: Any, holders: list[Identity]) -> str:
    states = [module.identity_status(holder["pid"], holder["started_at"]) for holder in holders]
    if any(state in {"unknown", "reused"} for state in states):
        return "unknown"
    return "active" if "live" in states else "released"


def store_holder_state(module: Any, worktree: Path) -> str:
    rows = worktree_sweep.session_rows(state_directory() / "sessions.db")
    states = []
    for row in rows:
        if row["ended_at"] is not None or not isinstance(row["cwd"], str) or not worktree_sweep.inside(row["cwd"], worktree):
            continue
        state, _info = module.process_state(row["pid"])
        states.append(state)
    if any(state == "present" for state in states):
        return "active"
    return "unknown" if any(state == "unknown" for state in states) else "released"


def ready_for_removal(module: Any, obligation: Json, target: Path) -> tuple[bool, str | None]:
    holder = holder_state(module, obligation["holders"])
    if holder != "released":
        return False, "cleanup holder identity is " + holder
    try:
        stored = store_holder_state(module, target)
    except worktree_sweep.UnreadableSessions as error:
        return False, f"session registry is unreadable: {error}"
    if stored != "released":
        return False, "session registry ownership is " + stored
    if worktree_sweep.recently_edited(target):
        return False, "changed files were edited in the last 30 minutes"
    return True, None


def exact_target(primary: Path, target: Path, obligation: Json) -> bool:
    if not target.is_dir() or not registered(primary, target):
        return False
    branch = worktree_sweep.git(target, "rev-parse", "--abbrev-ref", "HEAD")
    head = worktree_sweep.git(target, "rev-parse", "HEAD")
    return branch.returncode == 0 and head.returncode == 0 and branch.stdout.strip() == obligation["branch"] \
        and head.stdout.strip() == obligation["head"]


def verify_removal(primary: Path, worktree: Path) -> bool:
    registered_now = registered(primary, worktree)
    return registered_now is False and not worktree.exists()


def wait_for_worker(path: str | Path, module: Any, token: str, identity_sha256: str, timeout: float) -> Json:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        obligation = load(path)
        require_pinned(obligation, identity_sha256, token, require_launch=True)
        launch = obligation.get("launch")
        worker = obligation.get("worker")
        worker_identity = identity_value(worker)
        if (isinstance(launch, dict) and launch.get("token") == token and worker_identity is not None
                and module.verified_live(worker_identity["pid"], worker_identity["started_at"])):
            return obligation
        time.sleep(0.05)
    raise CleanupError("targeted cleanup worker did not acknowledge launch")


def launch(path: str | Path, session_close_path: str | Path, wait_seconds: float = 600,
           acknowledgement_timeout: float = 15, retry: bool = False) -> Json:
    module = load_session_close(session_close_path)
    with obligation_lock(path):
        obligation = load(path)
        target = Path(obligation["worktree"])
        primary = Path(obligation["primary"])
        if obligation["state"] in {"verified", "retained"}:
            return obligation
        if target == primary or under(module, primary, target):
            raise CleanupError("targeted cleanup refuses a primary checkout or its ancestor")
        safe_runtime(module, target)
        existing = obligation.get("launch")
        if existing is not None:
            worker = identity_value(obligation.get("worker"))
            if worker is None:
                raise CleanupError("targeted cleanup launch has no worker acknowledgement")
            worker_state = module.identity_status(worker["pid"], worker["started_at"])
            if worker_state == "live":
                raise CleanupError("targeted cleanup worker is already live")
            if worker_state != "exited":
                raise CleanupError("targeted cleanup worker identity is not safely reconciled")
            if not retry:
                raise CleanupError("targeted cleanup launch requires native worker reconciliation")
        if obligation["state"] in {"refused", "timed_out"} and not retry:
            return obligation
        if retry:
            obligation["state"] = "pending"
            obligation["reason"] = None
            obligation["worker"] = None
        token = obligation["launch_token"]
        identity_sha256 = obligation["identity_sha256"]
        obligation["launch"] = {"token": token, "launcher": identity(module, os.getpid())}
        obligation = save(path, obligation)
    module.start_detached(
        Path(__file__),
        ["run", "--obligation", str(Path(path).resolve()), "--launch-token", token,
         "--wait-seconds", str(wait_seconds)],
        extra=(Path(cleanup_proof.__file__), Path(worktree_sweep.__file__)),
    )
    return wait_for_worker(path, module, token, identity_sha256, acknowledgement_timeout)


def run(path: str | Path, wait_seconds: float = 0, retry: bool = False,
        launch_token: str | None = None) -> Json:
    module = load_session_close()
    initial = load(path)
    token = initial["launch_token"]
    identity_sha256 = initial["identity_sha256"]
    require_pinned(initial, identity_sha256, token, require_launch=True)
    target = Path(initial["worktree"])
    primary = Path(initial["primary"])
    if target == primary or under(module, primary, target):
        raise CleanupError("targeted cleanup refuses a primary checkout or its ancestor")
    safe_runtime(module, target)
    if launch_token != token:
        raise CleanupError("targeted cleanup launch token does not match")
    mine = identity(module, os.getpid())
    with obligation_lock(path):
        obligation = load(path)
        require_pinned(obligation, identity_sha256, token, require_launch=True)
        if obligation["state"] in {"verified", "retained"}:
            return obligation
        previous_worker = identity_value(obligation.get("worker"))
        if previous_worker is not None and previous_worker != mine:
            state = module.identity_status(previous_worker["pid"], previous_worker["started_at"])
            if state == "live":
                raise CleanupError("targeted cleanup worker is already live")
            if state != "exited":
                raise CleanupError("targeted cleanup worker identity is not safely reconciled")
            if not retry:
                raise CleanupError("targeted cleanup worker requires reconciliation before retry")
        if obligation["state"] in {"refused", "timed_out"} and not retry:
            return obligation
        obligation["worker"] = mine
        obligation = save(path, obligation, "running", None)
    if not primary.is_dir():
        return save_pinned(path, identity_sha256, token, mine, "refused", "primary checkout is unavailable")
    if not target.is_dir():
        if verify_removal(primary, target):
            return save_pinned(path, identity_sha256, token, mine, "verified", None)
        return save_pinned(path, identity_sha256, token, mine, "pending", "worktree absence is not yet verified")
    deadline = time.monotonic() + max(0, wait_seconds)
    while True:
        obligation = load(path)
        require_pinned(obligation, identity_sha256, token, require_launch=True)
        if identity_value(obligation["worker"]) != mine:
            raise CleanupError("targeted cleanup worker ownership changed")
        ready, reason = ready_for_removal(module, obligation, target)
        if ready:
            break
        if reason is not None and reason.endswith(("unknown", "reused")):
            return save_pinned(path, identity_sha256, token, mine, "refused", reason)
        if time.monotonic() >= deadline:
            return save_pinned(path, identity_sha256, token, mine, "timed_out", reason)
        time.sleep(max(0, min(0.25, deadline - time.monotonic())))
    with obligation_lock(path):
        obligation = load(path)
        require_pinned(obligation, identity_sha256, token, require_launch=True)
        if identity_value(obligation["worker"]) != mine:
            raise CleanupError("targeted cleanup worker ownership changed")
        if not exact_target(primary, target, obligation):
            return save(path, obligation, "refused", "worktree identity changed before cleanup proof")
        arguments = argparse.Namespace(
            worktree=str(target), branch=obligation["branch"], head=obligation["head"], pr=obligation["pr"],
            default=None, repo=obligation["repository"],
        )
    previous = Path.cwd()
    try:
        os.chdir(primary)
        proof_runner: Any = cleanup_proof.run
        proof = proof_runner(arguments)
    except (cleanup_proof.Preserve, OSError) as error:
        return save_pinned(path, identity_sha256, token, mine, "refused", getattr(error, "reason", str(error)))
    finally:
        os.chdir(previous)
    if proof != 0:
        return save_pinned(path, identity_sha256, token, mine, "refused", "cleanup proof did not permit removal")
    with obligation_lock(path):
        obligation = load(path)
        require_pinned(obligation, identity_sha256, token, require_launch=True)
        if identity_value(obligation["worker"]) != mine:
            raise CleanupError("targeted cleanup worker ownership changed")
        if not exact_target(primary, target, obligation):
            return save(path, obligation, "refused", "worktree identity changed before removal")
        ready, reason = ready_for_removal(module, obligation, target)
        if not ready:
            return save(path, obligation, "refused", reason)
        removed, reason = worktree_sweep.remove(primary, {
            "path": str(target), "branch": obligation["branch"], "head": obligation["head"],
        })
        if not removed or not verify_removal(primary, target):
            return save(path, obligation, "pending", reason)
        return save(path, obligation, "verified", reason)


def save_pinned(path: str | Path, identity_sha256: str, token: str, worker: Identity,
                state: str, reason: str | None) -> Json:
    with obligation_lock(path):
        obligation = load(path)
        require_pinned(obligation, identity_sha256, token, require_launch=True)
        if identity_value(obligation["worker"]) != worker:
            raise CleanupError("targeted cleanup worker ownership changed")
        return save(path, obligation, state, reason)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--primary", required=True)
    prepare_parser.add_argument("--worktree", required=True)
    prepare_parser.add_argument("--branch", required=True)
    prepare_parser.add_argument("--head", required=True)
    prepare_parser.add_argument("--pr", type=int, required=True)
    prepare_parser.add_argument("--repository", required=True)
    prepare_parser.add_argument("--owner-host", required=True)
    prepare_parser.add_argument("--owner-session-id", required=True)
    prepare_parser.add_argument("--holder", action="append", default=[])
    prepare_parser.add_argument("--retained", action="store_true")
    launch_parser = commands.add_parser("launch")
    launch_parser.add_argument("--obligation", required=True)
    launch_parser.add_argument("--session-close", required=True)
    launch_parser.add_argument("--wait-seconds", type=float, default=600)
    launch_parser.add_argument("--acknowledgement-timeout", type=float, default=15)
    launch_parser.add_argument("--retry", action="store_true")
    run_parser = commands.add_parser("run")
    run_parser.add_argument("--obligation", required=True)
    run_parser.add_argument("--wait-seconds", type=float, default=0)
    run_parser.add_argument("--retry", action="store_true")
    run_parser.add_argument("--launch-token", required=True)
    return result


def parse_holder(value: str) -> Identity:
    try:
        pid_text, started_text = value.split(":", 1)
        holder = {"pid": int(pid_text), "started_at": float(started_text)}
    except (AttributeError, TypeError, ValueError) as error:
        raise CleanupError("targeted cleanup holder requires PID:START") from error
    if not valid_identity(holder):
        raise CleanupError("targeted cleanup holder requires PID:START")
    return holder


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.command == "prepare":
        path, obligation = prepare(
            arguments.primary, arguments.worktree, arguments.branch, arguments.head, arguments.pr,
            arguments.repository, owner(arguments.owner_host, arguments.owner_session_id),
            [parse_holder(value) for value in arguments.holder],
            arguments.retained,
        )
    elif arguments.command == "launch":
        path = Path(arguments.obligation)
        obligation = launch(
            path, arguments.session_close, arguments.wait_seconds, arguments.acknowledgement_timeout, arguments.retry,
        )
    else:
        path = Path(arguments.obligation)
        obligation = run(path, arguments.wait_seconds, arguments.retry, arguments.launch_token)
    print(json.dumps({"obligation_path": str(path.resolve()), "receipt_path": str(receipt_path(obligation).resolve()),
                      "receipt": obligation}, sort_keys=True))
    return 0 if obligation["state"] in {"pending", "running", "verified", "retained"} else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CleanupError as error:
        print(json.dumps({"error": str(error)}))
        raise SystemExit(2) from error
