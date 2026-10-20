"""React to GitHub hints over one blocking ntfy stream (Python 3.11+)."""

from __future__ import annotations

import argparse
import hashlib
from collections import OrderedDict
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import select
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request

import plugin_autoupdate as plugins

OWNERS = ("tj-agents", "Concertable", "tomjseery")
TOPIC_VARIABLE = "MACHINE_EVENTS_TOPIC"
SERVICE_NAME = "tj-agents machine events"
MAX_LINE = 16384
LOG = logging.getLogger("machine-events")
FIELDS = """nameWithOwner isArchived isFork
defaultBranchRef { name target { oid } }
policy: object(expression: "HEAD:.github/merge-policy.json") { oid }
marketplace: object(expression: "HEAD:.claude-plugin/marketplace.json") { oid }
catalog: object(expression: "HEAD:.agents/plugins/marketplace.json") { oid }"""


def tommy_environment():
    return {key: value for key, value in os.environ.items()
            if key not in {"TJ_AGENT", "GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN"}
            and not key.startswith("GIT_CONFIG_")}


def gh(arguments, payload=None, run=subprocess.run):
    environment = tommy_environment()
    shim = os.path.normcase(str(Path.home() / ".agents-state/bin/bot-identity"))
    path = os.pathsep.join(entry for entry in environment.get("PATH", "").split(os.pathsep)
                           if entry and os.path.normcase(os.path.abspath(entry)) != shim)
    executable = plugins.shutil.which("gh", path=path)
    if not executable:
        raise RuntimeError("GitHub CLI must be installed and signed in as tomjseery")
    result = run([executable, "api", *arguments], input=None if payload is None else json.dumps(payload),
                 env=environment, capture_output=True, text=True, encoding="utf-8", errors="replace",
                 timeout=60, check=False, creationflags=plugins.NO_WINDOW)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "GitHub API failed")
    return json.loads(result.stdout) if result.stdout.strip() else None


def require_tommy(api=gh):
    if api(["user"])["login"].lower() != "tomjseery":
        raise RuntimeError("Machine events must run with Tommy's saved gh login (tomjseery)")


def valid_repository(value):
    return isinstance(value, str) and bool(re.fullmatch(
        r"(?:tj-agents|Concertable|tomjseery)/[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}", value, re.I))


def parse_hint(envelope):
    if not isinstance(envelope, dict) or envelope.get("event") != "message":
        return None
    try:
        message = json.loads(envelope.get("message", ""))
    except (ValueError, TypeError):
        return None
    if not isinstance(message, dict) or type(message.get("v")) is not int or message["v"] != 1:
        return None
    return message["repo"] if valid_repository(message.get("repo")) else None


def repository_state(repository, api=gh):
    owner, name = repository.split("/")
    query = "query($owner:String!,$name:String!){repository(owner:$owner,name:$name){" + FIELDS + "}}"
    response = api(["graphql", "-f", "query=" + query, "-f", "owner=" + owner, "-f", "name=" + name])
    if response.get("errors"):
        raise RuntimeError("GitHub repository query failed")
    return response["data"]["repository"]


def catch_up_states(api=gh):
    for owner in OWNERS:
        cursor = None
        while True:
            query = ("query($owner:String!,$after:String){repositoryOwner(login:$owner){repositories("
                     "first:100,after:$after,ownerAffiliations:OWNER){nodes{" + FIELDS
                     + "}pageInfo{hasNextPage endCursor}}}}")
            arguments = ["graphql", "-f", "query=" + query, "-f", "owner=" + owner]
            if cursor:
                arguments += ["-f", "after=" + cursor]
            response = api(arguments)
            if response.get("errors"):
                raise RuntimeError("GitHub catch-up query failed")
            repositories = response["data"]["repositoryOwner"]["repositories"]
            yield from repositories["nodes"]
            page = repositories["pageInfo"]
            if not page["hasNextPage"]:
                break
            cursor = page["endCursor"]


def policy_script():
    config = plugins.load_codex_config()
    roots = [root for _, declaration in plugins.declarations(config)
             for root in plugins.installed_plugin_roots("github-actions", plugins.claude_home(), declaration)]
    relative = Path(".agents/github-actions/utility/merge-policy/scripts/merge_policy.py")
    candidates = [root / relative for root in roots]
    candidates += [root / "skills/merge-policy/scripts/merge_policy.py" for root in roots]
    script = plugins.newest_existing(candidates)
    if script is None:
        raise RuntimeError("Install the github-actions plugin containing merge-policy reconcile before setup")
    return script


def reconcile_policy(repository, run=subprocess.run):
    result = run([plugins.console_python(), "-B", str(policy_script()), "reconcile", "--repo", repository],
                 env=tommy_environment(), capture_output=True, text=True, encoding="utf-8", errors="replace",
                 timeout=180, check=False, creationflags=plugins.NO_WINDOW)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "merge-policy reconciliation failed")


def refresh_plugins():
    arguments = ["--no-sweep", "--retry-failures"]
    if Path(plugins.__file__).resolve().parent != (plugins.state_directory() / "bin").resolve():
        arguments.append("--no-self-update")
    return plugins.main(arguments)


class Reconciler:
    def __init__(self, state=None, refresh=None, policy=reconcile_policy, sweep=None):
        self.state = state if state is not None else {}
        self.refresh = refresh or refresh_plugins
        self.policy = policy
        self.sweep = sweep or (lambda: plugins.sweep_worktrees(plugins.load_codex_config()))

    def repository(self, current, refresh_plugins=True):
        if not current or current.get("isArchived") or current.get("isFork"):
            return
        repository = current.get("nameWithOwner")
        if not valid_repository(repository) or not current.get("defaultBranchRef"):
            return
        revision = current["defaultBranchRef"]["target"]["oid"]
        old = self.state.get(repository, {})
        policy = (current.get("policy") or {}).get("oid")
        marketplace = bool(current.get("marketplace") or current.get("catalog"))
        if old.get("revision") == revision:
            return
        if policy and policy != old.get("policy"):
            self.policy(repository)
        if marketplace and refresh_plugins:
            if self.refresh() != 0:
                raise RuntimeError("plugin refresh failed")
        self.state[repository] = {"revision": revision, "policy": policy}
        return True

    def catch_up(self, states):
        if self.refresh() != 0:
            raise RuntimeError("plugin catch-up failed")
        failures = []
        for current in states:
            try:
                self.repository(current, refresh_plugins=False)
            except Exception:
                LOG.exception("Catch-up failed for %s", current.get("nameWithOwner"))
                failures.append(current["nameWithOwner"])
        self.sweep()
        return failures


class Pending:
    def __init__(self):
        self.items = OrderedDict()
        self.condition = threading.Condition()

    def put(self, repository):
        with self.condition:
            if repository in self.items or len(self.items) < 256:
                self.items[repository] = None
            self.condition.notify()

    def get(self):
        with self.condition:
            self.condition.wait_for(lambda: bool(self.items))
            return self.items.popitem(last=False)[0]


def process_pending(pending, reconciler, state_file):
    def runtime_digest():
        return hashlib.sha256(Path(__file__).read_bytes() + Path(plugins.__file__).read_bytes()).digest()

    running_bytes = runtime_digest()
    waiter = None
    while True:
        repository = pending.get()
        for attempt in range(3):
            try:
                if repository is None:
                    for failed in reconciler.catch_up(catch_up_states()):
                        pending.put(failed)
                else:
                    if reconciler.repository(repository_state(repository)):
                        reconciler.sweep()
                plugins.write_json(state_file, reconciler.state)
                if runtime_digest() != running_bytes:
                    os._exit(75)
                outcomes = plugins.read_json(plugins.state_directory() / "plugin-autoupdate.json").get("outcomes", {})
                deferred = any(str(value).startswith("deferred")
                               for value in outcomes.get("marketplaces", {}).values())
                if deferred and (waiter is None or not waiter.is_alive()):
                    waiter = threading.Thread(target=wait_for_sessions, args=(pending,), daemon=True)
                    waiter.start()
                break
            except Exception:
                LOG.exception("Reconciliation failed for %s (attempt %s)", repository or "catch-up", attempt + 1)
                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))


def session_pids():
    database = plugins.state_directory() / "sessions.db"
    if not database.is_file():
        return []
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True, timeout=5)
    try:
        rows = connection.execute("SELECT profile, pid FROM sessions WHERE ended_at IS NULL").fetchall()
    finally:
        connection.close()
    home = os.path.normcase(str(plugins.codex_home().resolve()))
    return sorted({pid for profile, pid in rows if isinstance(pid, int) and pid > 0
                   and isinstance(profile, str) and os.path.normcase(str(Path(profile).resolve())) == home})


def wait_for_exit(pid):
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x00100000, False, pid)
        if not handle:
            if ctypes.get_last_error() == 87:
                return
            raise OSError(ctypes.get_last_error(), "Cannot wait for registered Codex process")
        try:
            if kernel.WaitForSingleObject(handle, 0xFFFFFFFF) != 0:
                raise OSError("Codex process wait failed")
        finally:
            kernel.CloseHandle(handle)
    else:
        try:
            descriptor = os.pidfd_open(pid)
        except ProcessLookupError:
            return
        try:
            select.select([descriptor], [], [])
        finally:
            os.close(descriptor)


def wait_for_sessions(pending):
    try:
        for pid in session_pids():
            wait_for_exit(pid)
        pending.put(None)
    except Exception:
        LOG.exception("Cannot subscribe to the deferred Codex process exit")


def topic_value(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", value):
        raise ValueError("Machine event topic must contain 32-128 letters, digits, underscores or hyphens")
    return value


def subscribe(topic, pending, cursor_file, opener=urllib.request.urlopen):
    cursor = plugins.read_json(cursor_file).get("since", "all")
    delay = 1
    opened = False
    started_at = time.monotonic()
    pending.put(None)
    while True:
        connected_at = time.monotonic()
        try:
            url = "https://ntfy.sh/" + topic + "/json?" + urllib.parse.urlencode({"since": cursor})
            with opener(url, timeout=90) as response:
                if opened or time.monotonic() - started_at > 60:
                    pending.put(None)
                opened = True
                while True:
                    line = response.readline(MAX_LINE + 1)
                    if not line:
                        raise ConnectionError("Event stream disconnected")
                    if len(line) > MAX_LINE:
                        raise ValueError("Event exceeds the maximum line length")
                    try:
                        envelope = json.loads(line)
                    except (ValueError, UnicodeError):
                        continue
                    repository = parse_hint(envelope)
                    if repository:
                        pending.put(repository)
                    if isinstance(envelope, dict) and envelope.get("event") == "message":
                        message_id = envelope.get("id")
                        if isinstance(message_id, str) and re.fullmatch(r"[A-Za-z0-9]{1,64}", message_id):
                            cursor = message_id
                            plugins.write_json(cursor_file, {"since": cursor})
        except Exception as error:
            LOG.warning("Event stream interrupted: %s", type(error).__name__)
            if time.monotonic() - connected_at > 60:
                delay = 1
            time.sleep(delay)
            delay = min(delay * 2, 60)


def acquire_listener_lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    try:
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            if not stream.read(1):
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        stream.close()
        return None
    return stream


def main(argv=None):
    if sys.version_info < (3, 11):
        raise RuntimeError("machine_events requires Python 3.11 or newer")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--repo")
    parser.add_argument("--state-directory", type=Path)
    arguments = parser.parse_args(argv)
    if arguments.state_directory:
        os.environ["AGENT_STATE_DIRECTORY"] = str(arguments.state_directory.resolve())
    directory = plugins.state_directory()
    directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(directory / "machine-events.log", maxBytes=262144, backupCount=2,
                                  encoding="utf-8")
    LOG.addHandler(handler)
    LOG.setLevel(logging.INFO)
    lock = acquire_listener_lock(directory / "machine-events.lock")
    if lock is None:
        return 0
    try:
        require_tommy()
        state_file = directory / "machine-events-state.json"
        reconciler = Reconciler(plugins.read_json(state_file))
        if arguments.once:
            failures = []
            if arguments.repo:
                if not valid_repository(arguments.repo):
                    raise ValueError("Unsupported repository")
                reconciler.repository(repository_state(arguments.repo))
            else:
                failures = reconciler.catch_up(catch_up_states())
            plugins.write_json(state_file, reconciler.state)
            return int(bool(failures))
        topic = topic_value(plugins.read_json(directory / "machine-events.json").get("topic"))
        pending = Pending()
        threading.Thread(target=process_pending, args=(pending, reconciler, state_file), daemon=True).start()
        subscribe(topic, pending, directory / "machine-events-cursor.json")
    finally:
        lock.close()


if __name__ == "__main__":
    raise SystemExit(main())
