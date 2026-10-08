#!/usr/bin/env python3
import argparse
import hashlib
import importlib.util
import json
import time
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import math
from contextlib import contextmanager

HERE = Path(__file__).resolve().parent
SESSION_ID = re.compile(r"(?!-)[A-Za-z0-9_-]+\Z")
LOCKS = {}
LOCKS_GUARD = threading.Lock()
MODULES = {}


def _load(name):
    peer = HERE.parent / "utility/peer-cli/scripts" / f"{name}.py"
    packaged = tuple(HERE.parents[2] / layout / "peer-cli/scripts" / f"{name}.py"
                     for layout in ("skills", "codex-skills")) if len(HERE.parents) > 2 else ()
    for path in (HERE / f"{name}.py", HERE / "resources/machine/scripts" / f"{name}.py", peer, *packaged):
        if path.is_file():
            identity = str(path.resolve())
            if identity in MODULES:
                return MODULES[identity]
            spec = importlib.util.spec_from_file_location(f"agent_recovery_{name}_{len(MODULES)}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            MODULES[identity] = module
            return module
    raise RuntimeError(f"The shared {name}.py helper was not found relative to {HERE}.")


def _registry_root():
    return Path(os.environ.get("AGENT_STATE_DIRECTORY", Path.home() / ".agents-state")) / "cli-sessions"


def _registry(session_id):
    path = _registry_root() / f"{session_id}.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def liveness(item, process_lookup=None):
    session_id = item.get("session") or item.get("id")
    current_id = os.environ.get("CODEX_THREAD_ID") if item["host"] == "codex" else os.environ.get("CLAUDE_CODE_SESSION_ID")
    if current_id and current_id == session_id:
        return "live"
    record = _registry(session_id)
    if not record:
        return "unknown"
    if record.get("host") and record["host"] != item["host"]:
        return "unknown"
    pid, started = record.get("pid"), record.get("pid_started_at")
    if not isinstance(pid, int) or isinstance(started, bool) or not isinstance(started, (int, float)) or not math.isfinite(started):
        return "unknown"
    if process_lookup is None:
        try:
            process_lookup = _load("register_session").build_process_lookup()
        except Exception:
            return "unknown"
    try:
        current = process_lookup(pid)
    except Exception:
        return "unknown"
    if current is None:
        return "closed"
    if getattr(current, "name", "").casefold().removesuffix(".exe") != item["host"]:
        return "closed"
    if isinstance(current.started_at, bool) or not isinstance(current.started_at, (int, float)) or not math.isfinite(current.started_at):
        return "unknown"
    return "live" if current.started_at == started else "closed"


def _profile(host, root):
    return os.path.normcase(str(Path(root).parent.resolve()))


def _normalise(item, root):
    preview = item.get("preview") or next((re.sub(r"\s+", " ", text)[:160] for _, role, text in item.get("messages", ())
                                             if role == "user" and not text.lstrip().startswith("<")), "(no user preview)")
    return {
        "id": item["session"], "host": item["host"], "cwd": item.get("cwd"),
        "branch": item.get("branch"), "activity": item.get("last_activity"),
        "preview": preview, "profile": _profile(item["host"], root),
        "status": liveness(item), "matched_by": item.get("matched_by"),
    }


def _recoverable(item):
    return item["host"] != "codex" or item.get("source") == "cli"


def _roots(host, root):
    if host == "codex":
        return (root, root.parent / "archived_sessions")
    return (root,)


def _title_index(root):
    titles = {}
    for path in (root.parent / "session_index.jsonl", _registry_root() / "session_index.jsonl"):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not isinstance(entry, dict):
                continue
            session_id = entry.get("id") or entry.get("session_id") or entry.get("sessionId")
            title = entry.get("thread_name") or entry.get("title")
            if isinstance(session_id, str) and isinstance(title, str):
                titles[session_id] = title
    try:
        registry = _registry_root().glob("*.json")
    except OSError:
        registry = ()
    for path in registry:
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(entry, dict) and isinstance(entry.get("session_id"), str) and isinstance(entry.get("title"), str):
            titles[entry["session_id"]] = " | ".join(dict.fromkeys(filter(None, (titles.get(entry["session_id"]), entry["title"]))))
    return titles


def _matches(item, topic, checkout, history, title):
    if checkout:
        variants = history._worktree_variants(checkout)
        if not history._cwd_under(item.get("cwd"), variants) and not any(history._contains_path_token(text, variants) for text in item.get("tool_strings", ())):
            return False
    if topic:
        query = topic.casefold()
        values = [item["session"], title or ""] + [text for _, _, text in item.get("messages", ())]
        if not any(query in value.casefold() for value in values):
            return False
    return True


def _record_items(host, root, history):
    files = []
    for directory in _roots(host, root):
        if not directory.is_dir():
            continue
        files.extend(directory.rglob("*.jsonl") if host == "codex" else directory.glob("*/*.jsonl"))
    for path in files:
        item = history.session(path, host)
        if item and _recoverable(item) and SESSION_ID.fullmatch(item["session"]):
            yield item


def search(hosts=("codex", "claude"), topic=None, checkout=None, count=10, roots=None):
    if count < 1:
        raise ValueError("--count must be positive")
    history = _load("history")
    results = []
    for host in hosts:
        root = (roots or {}).get(host) if roots else None
        root = Path(root) if root else history.history_root(host)
        if not root.is_dir():
            raise ValueError(f"No {host} history directory at {root}; select the correct profile or history root.")
        titles = _title_index(root)
        for item in _record_items(host, root, history):
            title = titles.get(item["session"])
            if _matches(item, topic, checkout, history, title):
                normal = _normalise(item, root)
                normal["title"] = title
                results.append(normal)
    results.sort(key=lambda item: item.get("activity") or "", reverse=True)
    return results[:count]


def find(host, session_id, roots=None):
    if host not in ("codex", "claude") or not SESSION_ID.fullmatch(session_id):
        raise ValueError("A host and native session id are required.")
    history = _load("history")
    root = Path((roots or {}).get(host) or history.history_root(host))
    if not root.is_dir():
        raise ValueError(f"No {host} history directory at {root}; select the correct profile or history root.")
    for item in _record_items(host, root, history):
        if item["session"] == session_id:
            item = _normalise(item, root)
            if not item["cwd"] or not Path(item["cwd"]).is_dir():
                raise ValueError("The recorded session directory is missing; refusing to resume it elsewhere.")
            return item
    raise ValueError("The requested native session was not found in the selected profile history.")


def _verify_codex_resume(executable):
    try:
        result = subprocess.run([executable, "resume", "--help"], text=True, capture_output=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"Could not verify native Codex resume support: {exc}") from None
    if result.returncode or "SESSION_ID" not in result.stdout + result.stderr:
        raise ValueError("The native Codex executable does not support exact `resume SESSION_ID [PROMPT]`.")


def _session_lock(host, session_id):
    key = (host, session_id)
    with LOCKS_GUARD:
        return LOCKS.setdefault(key, threading.Lock())


def _receipt(host, session_id, profile):
    namespace = hashlib.sha256(profile.encode("utf-8")).hexdigest()[:16]
    path = _registry_root().parent / "recovery-launches" / f"{host}-{namespace}-{session_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def _claim_lock(path):
    lock_path = path.with_suffix(".lock")
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0)
            handle.write(b"0")
            handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _claim(host, session_id, profile):
    path = _receipt(host, session_id, profile)
    with _claim_lock(path):
        if path.exists():
            try:
                previous = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                previous = {}
            before = previous.get("registry_fingerprint")
            current = _registry(session_id)
            current_fingerprint = _fingerprint(current)
            registered = current_fingerprint and current_fingerprint != before and current.get("started_at", 0) >= previous.get("created_at", float("inf"))
            if registered and liveness({"host": host, "session": session_id}) == "closed":
                path.unlink()
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ValueError("A prior launch for that exact host session is pending or ambiguous; check its terminal before retrying.") from None
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump({"host": host, "session": session_id, "profile": profile, "state": "pending",
                       "created_at": time.time(), "registry_fingerprint": _fingerprint(_registry(session_id))}, handle)
    return path


def _fingerprint(entry):
    if not isinstance(entry, dict):
        return None
    return json.dumps(entry, sort_keys=True, separators=(",", ":"))


def _receipt_state(path, host, session_id, profile, state):
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        previous = {}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"host": host, "session": session_id, "profile": profile, "state": state,
                                     "created_at": previous.get("created_at", time.time()),
                                     "registry_fingerprint": previous.get("registry_fingerprint")}) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def open_session(host, session_id, prompt="Continue the requested work.", title=None, roots=None, confirm_closed=False,
                 prompt_path=None, model=None, dangerously_skip_permissions=False, cli=None):
    item = find(host, session_id, roots)
    if item["status"] == "live":
        raise ValueError("That exact session is verified live; refusing to create a duplicate writer.")
    if item["status"] == "unknown" and not confirm_closed:
        raise ValueError("That session has conflicting or incomplete live identity; reconcile it before resuming.")
    if prompt_path and prompt:
        raise ValueError("Pass either a short prompt or a prompt file, not both.")
    if not prompt_path and (not prompt or len(prompt) > 500):
        raise ValueError("The continue instruction must be a non-empty short prompt (500 characters or fewer).")
    cli = cli or _load("agent_cli")
    lock = _session_lock(host, session_id)
    if not lock.acquire(blocking=False):
        raise ValueError("A launch request for that exact session is already in progress.")
    receipt = None
    launched = False
    try:
        receipt = _claim(host, session_id, item["profile"])
        directory = cli.resolve_tab_directory(item["cwd"])
        label = title or f"{host.title()} {session_id[:8]}"
        instruction = cli.prompt_file_argument(prompt_path)[0] if prompt_path else prompt
        if host == "claude":
            old_profile = os.environ.get("CLAUDE_CONFIG_DIR")
            os.environ["CLAUDE_CONFIG_DIR"] = item["profile"]
            try:
                arguments = ["--resume", session_id]
                if dangerously_skip_permissions:
                    arguments.append("--dangerously-skip-permissions")
                if model:
                    arguments += ["--model", model]
                arguments.append(instruction)
                cli.open_claude_tab(directory, label, arguments)
            finally:
                if old_profile is None:
                    os.environ.pop("CLAUDE_CONFIG_DIR", None)
                else:
                    os.environ["CLAUDE_CONFIG_DIR"] = old_profile
        else:
            executable, _ = cli.resolve_codex_executable()
            _verify_codex_resume(executable)
            old_profile = os.environ.get("CODEX_HOME")
            os.environ["CODEX_HOME"] = item["profile"]
            try:
                _sync_codex(executable, directory)
            finally:
                if old_profile is None:
                    os.environ.pop("CODEX_HOME", None)
                else:
                    os.environ["CODEX_HOME"] = old_profile
            arguments = ["resume", session_id]
            if model:
                arguments += ["-m", model]
            arguments.append(instruction)
            cli.launch_tab(directory, executable, label, arguments, clear=("TERM",), force={"CODEX_HOME": item["profile"]})
        launched = True
        try:
            _receipt_state(receipt, host, session_id, item["profile"], "launched")
        except OSError:
            pass
        return item
    except Exception as exc:
        if receipt is not None:
            timeout_type = getattr(cli, "LaunchTimeout", None)
            if isinstance(timeout_type, type) and isinstance(exc, timeout_type):
                try:
                    _receipt_state(receipt, host, session_id, item["profile"], "ambiguous")
                except OSError:
                    pass
            elif not launched:
                try:
                    receipt.unlink()
                except OSError:
                    pass
        raise
    finally:
        lock.release()


def _sync_codex(executable, directory):
    if os.name != "nt":
        return
    source = HERE / "codex_marketplace_sync.ps1"
    if not source.is_file():
        source = HERE / "resources/machine/scripts/codex_marketplace_sync.ps1"
    if not source.is_file():
        return
    command = ". '{}' ; Sync-CodexStandards -CodexExecutable '{}' -WorkingDirectory '{}' | Out-Null".format(
        str(source).replace("'", "''"), str(executable).replace("'", "''"), str(directory).replace("'", "''"))
    subprocess.run(["pwsh", "-NoProfile", "-Command", command], check=False, timeout=90)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Search and safely reopen exact native Codex or Claude sessions.")
    parser.add_argument("operation", choices=("search", "open", "recover"))
    parser.add_argument("--host", choices=("codex", "claude", "both"), default="both")
    parser.add_argument("--id")
    parser.add_argument("--topic")
    parser.add_argument("--checkout")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-path")
    parser.add_argument("--model")
    parser.add_argument("--title")
    parser.add_argument("--select", action="append", default=[])
    parser.add_argument("--confirm-closed", action="store_true")
    parser.add_argument("--codex-history-root")
    parser.add_argument("--claude-history-root")
    args = parser.parse_args(argv)
    try:
        hosts = ("codex", "claude") if args.host == "both" else (args.host,)
        roots = {host: value for host, value in (("codex", args.codex_history_root), ("claude", args.claude_history_root)) if value}
        if args.operation == "search":
            print(json.dumps(search(hosts, args.topic, args.checkout, args.count, roots), indent=2))
            return 0
        if args.operation == "recover":
            candidates = []
            unavailable = []
            for host in hosts:
                try:
                    candidates.extend(search((host,), args.topic, args.checkout, args.count, roots))
                except ValueError as exc:
                    unavailable.append({"host": host, "unavailable": str(exc)})
            if not args.select:
                print(json.dumps({"sessions": candidates, "unavailable": unavailable}, indent=2))
                return 0
            selected = []
            available = {(item["host"], item["id"]) for item in candidates}
            seen = set()
            for value in args.select:
                host, separator, session_id = value.partition(":")
                if not separator or (host, session_id) not in available:
                    raise ValueError("Each --select must be an exact host:id returned by this recovery inventory.")
                if (host, session_id) in seen:
                    raise ValueError("Each --select host:id may appear only once.")
                seen.add((host, session_id))
                selected.append((host, session_id))
            opened = []
            for host, session_id in selected:
                try:
                    opened.append(open_session(host, session_id, args.prompt if args.prompt_path else args.prompt or "Continue the requested work.",
                                               roots=roots, confirm_closed=args.confirm_closed,
                                               prompt_path=args.prompt_path, model=args.model))
                except Exception:
                    if opened:
                        print(f"Already opened: {', '.join(item['host'] + ':' + item['id'] for item in opened)}", file=sys.stderr)
                    raise
            print(json.dumps(opened, indent=2))
            return 0
        if len(hosts) != 1 or not args.id:
            raise ValueError("open requires one --host and an exact --id.")
        item = open_session(hosts[0], args.id, args.prompt if args.prompt_path else args.prompt or "Continue the requested work.", args.title, roots, args.confirm_closed,
                            args.prompt_path, args.model)
        print(json.dumps(item, indent=2))
        return 0
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        try:
            cli = _load("agent_cli")
        except RuntimeError:
            raise
        if isinstance(exc, cli.LaunchTimeout):
            print(str(exc), file=sys.stderr)
            return 3
        if isinstance(exc, cli.LaunchError):
            return cli.report_launch_failure(exc)
        raise


if __name__ == "__main__":
    sys.exit(main())
