from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import math
import os
from pathlib import Path
import queue
import shutil
import sqlite3
import shlex
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("base", "machine", "workflow", "engineering")
IDENTITIES = tuple(f"{package}@tj-agents" for package in PACKAGES)


class AcceptanceError(RuntimeError):
    pass


def load_module(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise AcceptanceError(f"cannot load {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def native_command(executable, arguments=()):
    return [str(Path(executable).resolve(strict=True)), *arguments]


def observed_command(host, executable, project, receipt, arguments):
    return [sys.executable, '-B', str(ROOT / 'scripts/native_startup_observer.py'),
            '--host', host, '--target', str(executable), '--project', str(project),
            '--receipt', str(receipt), '--', *arguments]


def terminate_owned(process):
    if os.name == 'nt':
        subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                       capture_output=True, timeout=10, check=False)
    else:
        process.terminate()


def require_observer(path, state):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        raise AcceptanceError(f'native startup observer has no valid receipt: {path}') from error
    if value.get('state') != state:
        raise AcceptanceError(f'native startup observer expected {state}: {value}')
    return value


def require_failure_probe(host, evidence, operation):
    path = evidence / (host + '-startup-observer.json')
    path.unlink(missing_ok=True)
    try:
        operation()
    except AcceptanceError:
        pass
    else:
        raise AcceptanceError(f'{host} accepted a deliberately failed required startup hook')
    receipt = require_observer(path, 'failed')
    if 'workflow@tj-agents' not in receipt.get('error', '') \
            or 'native-required-hook-failure-probe' not in receipt.get('error', ''):
        raise AcceptanceError(f'{host} failed for a different reason: {receipt}')
    return receipt


def diagnostic(lines):
    return "\n".join(lines[-40:])[-4000:]


def run_native(arguments, cwd, environment, label, timeout):
    try:
        return subprocess.run(
            arguments, cwd=cwd, env=environment, check=True, capture_output=True,
            text=True, encoding="utf-8", timeout=timeout,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()[-4000:]
        message = f"{label} failed with exit code {error.returncode}"
        if detail:
            message = f"{message}: {detail}"
        raise AcceptanceError(message) from error
    except (OSError, subprocess.SubprocessError) as error:
        raise AcceptanceError(f"{label} failed: {error}") from error


def json_result(completed, label):
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise AcceptanceError(f"{label} did not return JSON") from error
    if not isinstance(value, dict):
        raise AcceptanceError(f"{label} did not return an object")
    return value


def claude_plugin_inventory(completed):
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise AcceptanceError("Claude plugin discovery did not return JSON") from error
    if not isinstance(value, list):
        raise AcceptanceError("Claude plugin discovery did not return a list")
    return {"installed": [
        {"pluginId": item.get("id"), "installed": isinstance(item.get("id"), str), "enabled": item.get("enabled") is True}
        for item in value if isinstance(item, dict)
    ]}


def installed_identities(inventory):
    installed = inventory.get("installed")
    if not isinstance(installed, list):
        raise AcceptanceError("native plugin inventory is malformed")
    return {
        item["pluginId"]
        for item in installed
        if isinstance(item, dict)
        and isinstance(item.get("pluginId"), str)
        and item.get("installed") is True
        and item.get("enabled") is True
    }


def require_plugins(inventory):
    missing = sorted(set(IDENTITIES) - installed_identities(inventory))
    if missing:
        raise AcceptanceError(f"native plugin discovery is missing enabled installed {', '.join(missing)}")


def write_fixture(project, environment=None):
    selection = project / ".agents" / "plugins.json"
    selection.parent.mkdir(parents=True, exist_ok=True)
    selection.write_text(json.dumps({
        "schema_version": 1,
        "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}},
        "plugins": list(IDENTITIES),
    }, indent=2) + "\n", encoding="utf-8")
    if environment is not None:
        try:
            subprocess.run(
                ["git", "init", "--quiet", str(project)], cwd=project, env=environment,
                check=True, capture_output=True, text=True, encoding="utf-8",
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise AcceptanceError(f"isolated fixture Git initialization failed: {error}") from error
    return project


def session_id_from(value):
    if not isinstance(value, dict):
        raise AcceptanceError("native startup response is malformed")
    for candidate in (value.get("thread"), value.get("session"), value):
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str) and candidate["id"]:
            return candidate["id"]
    raise AcceptanceError("native startup response did not include a session id")


def start_line_reader(stream, destination, parse_json=False, completion=None):
    def read():
        try:
            for line in stream:
                if parse_json:
                    try:
                        destination.put(json.loads(line))
                    except json.JSONDecodeError as error:
                        destination.put(error)
                else:
                    destination.append(line.rstrip())
        except OSError as error:
            if parse_json:
                destination.put(error)
        finally:
            if completion is not None:
                completion.put(None)
    threading.Thread(target=read, daemon=True).start()


class AppServer:
    def __init__(self, executable, cwd, environment, timeout, popen=subprocess.Popen, observer_receipt=None):
        self.timeout = timeout
        self.observed = observer_receipt is not None
        self.process = popen(
            (observed_command('codex', executable, cwd, observer_receipt, ['app-server']) if self.observed
             else [*native_command(executable), 'app-server']), cwd=cwd, env=environment,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.messages = queue.Queue()
        self.completed = queue.Queue()
        self.notifications = []
        self.stderr = []
        self.sequence = 0
        start_line_reader(self.process.stdout, self.messages, parse_json=True, completion=self.completed)
        start_line_reader(self.process.stderr, self.stderr)

    def send(self, value):
        self.process.stdin.write(json.dumps(value) + "\n")
        self.process.stdin.flush()

    def _next(self, deadline):
        try:
            value = self.messages.get(timeout=max(0.01, deadline - time.monotonic()))
        except queue.Empty as error:
            message = "Codex app-server timed out"
            if detail := diagnostic(self.stderr):
                message = f"{message}: {detail}"
            raise AcceptanceError(message) from error
        if isinstance(value, Exception):
            raise AcceptanceError(f"Codex app-server emitted invalid JSON: {value}")
        return value

    def request(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            value = self._next(deadline)
            if value.get("id") != request_id:
                self.notifications.append(value)
                continue
            if "error" in value:
                raise AcceptanceError(f"Codex {method} failed: {value['error']}")
            if "result" not in value:
                raise AcceptanceError(f"Codex {method} returned no result")
            return value["result"]

    def initialize(self):
        self.request("initialize", {
            "clientInfo": {"name": "tj-agents-native-acceptance", "version": "1.0.0"},
            "capabilities": {"experimentalApi": True},
        })
        self.send({"method": "initialized", "params": {}})

    def notifications_until(self, predicate):
        deadline = time.monotonic() + self.timeout
        while not predicate(self.notifications):
            self.notifications.append(self._next(deadline))
        return list(self.notifications)

    def close(self):
        if self.process.poll() is None:
            terminate_owned(self.process) if self.observed else self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            try:
                stream.close()
            except OSError:
                pass

    def __enter__(self):
        try:
            self.initialize()
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(self, *_):
        self.close()


def require_startup_hooks(value, trusted=False, trusted_hashes=None):
    if not isinstance(value, dict) or not isinstance(value.get("data"), list):
        raise AcceptanceError("Codex hooks/list is malformed")
    hooks = [
        hook
        for entry in value["data"] if isinstance(entry, dict)
        for hook in entry.get("hooks", []) if isinstance(hook, dict)
        if hook.get("source") == "plugin" and hook.get("enabled") is True
    ]
    values = {hook.get("pluginId") for hook in hooks}
    missing = {"base@tj-agents", "machine@tj-agents"} - values
    if missing:
        raise AcceptanceError(f"Codex hooks/list is missing required startup hooks for {', '.join(sorted(missing))}")
    if trusted:
        untrusted = [
            hook.get("key", "unknown") for hook in hooks
            if hook.get("pluginId") in {"base@tj-agents", "machine@tj-agents"}
            and (
                hook.get("trustStatus") != "trusted"
                or hook.get("currentHash") != (trusted_hashes or {}).get(hook.get("key"), {}).get("trusted_hash")
            )
        ]
        if untrusted:
            raise AcceptanceError(f"Codex hooks/list did not trust current startup hooks: {', '.join(untrusted)}")


def trust_current_hooks(server, trust, executable, project, environment, verified_roots, timeout):
    inventory = json_result(run_native(
        [*native_command(executable), "plugin", "list", "--json"],
        project, environment, "Codex plugin discovery", timeout,
    ), "Codex plugin discovery")
    hooks = server.request("hooks/list", {"cwds": [str(project)]})
    updates = trust.trust_updates(inventory, hooks["data"], project.resolve(), verified_roots)
    if not updates:
        raise AcceptanceError("Codex trust update found no current verified startup hooks")
    server.request("config/batchWrite", {
        "edits": [{"keyPath": "hooks.state", "value": updates, "mergeStrategy": "upsert"}],
        "reloadUserConfig": True,
    })
    return updates

def verify_installed_roots(value, trust, marketplace):
    roots = {}
    expected = {identity: marketplace / "plugins" / package for package, identity in zip(PACKAGES, IDENTITIES)}
    if not isinstance(value, dict) or not isinstance(value.get("data"), list):
        raise AcceptanceError("Codex hooks/list is malformed")
    for entry in value["data"]:
        if not isinstance(entry, dict):
            continue
        for hook in entry.get("hooks", []):
            if not isinstance(hook, dict) or hook.get("source") != "plugin":
                continue
            identity = hook.get("pluginId")
            if identity not in expected or identity in roots:
                continue
            installed = trust.installed_package(hook)
            if trust.package_files(installed) != trust.package_files(expected[identity]):
                raise AcceptanceError(f"installed {identity} plugin differs from the candidate package")
            roots[identity] = SimpleNamespace(identity=identity, root=installed)
    for identity in ("base@tj-agents", "machine@tj-agents"):
        if identity not in roots:
            raise AcceptanceError(f"Codex hooks/list has no installed package root for {identity}")
    return list(roots.values())


def require_base_evidence(evidence, package_root, label):
    contract = package_root / ".agents" / "base" / "policy" / "task-routing" / "SKILL.md"
    digest = hashlib.sha256(contract.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    if "base:task-routing" not in evidence or digest not in evidence:
        raise AcceptanceError(f"{label} did not include Base task-routing context")


def transcript_entries(path):
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return None
    except OSError as error:
        raise AcceptanceError("Codex did not write a session transcript") from error
    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def snapshot_transcript(path, artifacts):
    artifacts.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copyfile(path, artifacts / "codex-session.jsonl")
    except OSError:
        pass


def snapshot_diagnostic(artifacts, name, value):
    artifacts.mkdir(parents=True, exist_ok=True)
    (artifacts / name).write_text(value, encoding="utf-8")


def require_failed_turn(path, package_root, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        entries = transcript_entries(path)
        if entries is None:
            time.sleep(0.05)
            continue
        evidence = json.dumps(entries, sort_keys=True)
        try:
            require_base_evidence(evidence, package_root, "Codex session transcript")
        except AcceptanceError:
            pass
        else:
            for entry in entries:
                payload = entry.get("payload") if isinstance(entry, dict) else None
                if not isinstance(payload, dict) or payload.get("type") != "task_complete":
                    continue
                error = payload.get("error")
                if isinstance(error, dict) and "401" in str(error.get("message", "")):
                    return entries
                raise AcceptanceError("Codex startup turn did not complete with the expected unauthenticated 401")
        time.sleep(0.05)
    raise AcceptanceError("Codex startup turn did not record Base context and an unauthenticated 401 completion")


def strings_at_keys(value, keys):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and isinstance(item, str):
                yield item
            yield from strings_at_keys(item, keys)
    elif isinstance(value, list):
        for item in value:
            yield from strings_at_keys(item, keys)


def require_discovery(value, label):
    required = {"workflow": "run", "engineering": "commit"}
    records = []

    def collect(item):
        if isinstance(item, dict):
            records.append(item)
            for child in item.values():
                collect(child)
        elif isinstance(item, list):
            for child in item:
                collect(child)

    collect(value)
    for package, skill in required.items():
        qualified = f"{package}:{skill}"
        found = False
        for record in records:
            values = {
                item for key, item in record.items()
                if key in {"id", "name", "skill", "qualifiedName", "command"} and isinstance(item, str)
            }
            if qualified in values:
                found = True
                break
            if skill not in values:
                continue
            sources = {
                item.replace("\\", "/").casefold() for key, item in record.items()
                if key in {"pluginId", "plugin", "source", "path", "root", "location"} and isinstance(item, str)
            }
            if any(source in {package, f"{package}@tj-agents"} or f"/plugins/{package}/" in source for source in sources):
                found = True
                break
        if not found:
            raise AcceptanceError(f"{label} did not discover the required {package} skill")


def require_claude_discovery(response):
    if not isinstance(response, dict) or not isinstance(response.get("commands"), list):
        raise AcceptanceError("Claude initialize response has no command inventory")
    names = {
        command.get("name") for command in response["commands"]
        if isinstance(command, dict) and isinstance(command.get("name"), str)
    }
    for name in ("workflow:run", "engineering:commit"):
        if name not in names:
            raise AcceptanceError(f"Claude initialize response did not discover {name}")


def is_descendant(process, root_pid, lookup):
    seen = set()
    current = process
    while current is not None and current.pid not in seen:
        if current.pid == root_pid:
            return True
        seen.add(current.pid)
        current = lookup(getattr(current, "ppid", None))
    return False


def require_receipt(state, store, register, host, session_id, project, root_pid):
    path = state / "cli-sessions" / f"{session_id}.json"
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AcceptanceError(f"missing or malformed {host} receipt") from error
    required = ("host", "session_id", "cwd", "pid", "pid_started_at")
    if any(key not in receipt for key in required):
        raise AcceptanceError(f"{host} receipt is missing identity fields")
    if receipt["host"] != host or receipt["session_id"] != session_id:
        raise AcceptanceError(f"{host} receipt identity does not match startup")
    if Path(receipt["cwd"]).resolve() != project.resolve():
        raise AcceptanceError(f"{host} receipt cwd does not match fixture project")
    if not isinstance(receipt["pid"], int) or receipt["pid"] <= 0:
        raise AcceptanceError(f"{host} receipt pid is invalid")
    if not isinstance(receipt["pid_started_at"], (int, float)) or not math.isfinite(receipt["pid_started_at"]):
        raise AcceptanceError(f"{host} receipt start time is invalid")
    lookup = register.build_process_lookup()
    process = lookup(receipt["pid"])
    if process is None or process.pid != receipt["pid"] or Path(process.name).stem.casefold() != host:
        raise AcceptanceError(f"{host} receipt does not identify a live native process")
    if abs(process.started_at - receipt["pid_started_at"]) > 2:
        raise AcceptanceError(f"{host} receipt start time does not match its native process")
    if not is_descendant(process, root_pid, lookup):
        raise AcceptanceError(f"{host} receipt process is not descended from the accepted native host")
    try:
        connection = store.connect(state / "sessions.db")
        try:
            row = store.get_session(connection, f"{host}:{session_id}")
        finally:
            connection.close()
    except sqlite3.Error as error:
        raise AcceptanceError(f"{host} Agent Store is unavailable") from error
    if not isinstance(row, dict):
        raise AcceptanceError(f"{host} session is missing from Agent Store")
    for key in required:
        if row.get(key) != receipt[key]:
            raise AcceptanceError(f"{host} Agent Store row does not match its receipt")


def install_codex_plugins(executable, marketplace, project, environment, timeout):
    run_native(
        [*native_command(executable), "plugin", "marketplace", "add", str(marketplace), "--json"],
        project, environment, "Codex marketplace registration", timeout,
    )
    for identity in IDENTITIES:
        run_native(
            [*native_command(executable), "plugin", "add", identity, "--json"],
            project, environment, f"Codex plugin installation for {identity}", timeout,
        )
    inventory = json_result(run_native(
        [*native_command(executable), "plugin", "list", "--json"],
        project, environment, "Codex plugin discovery", timeout,
    ), "Codex plugin discovery")
    require_plugins(inventory)


def install_claude_plugins(executable, marketplace, project, environment, timeout):
    run_native(
        [*native_command(executable), "plugin", "marketplace", "add", str(marketplace), "--scope", "user"],
        project, environment, "Claude marketplace registration", timeout,
    )
    for identity in IDENTITIES:
        run_native(
            [*native_command(executable), "plugin", "install", identity, "--scope", "user"],
            project, environment, f"Claude plugin installation for {identity}", timeout,
        )
    inventory = claude_plugin_inventory(run_native(
        [*native_command(executable), "plugin", "list", "--json"],
        project, environment, "Claude plugin discovery", timeout,
    ))
    require_plugins(inventory)


def receipt_ids(state, host):
    directory = state / "cli-sessions"
    if not directory.is_dir():
        return set()
    values = set()
    for path in directory.glob("*.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if value.get("host") == host and isinstance(value.get("session_id"), str):
            values.add(value["session_id"])
    return values


def accept_claude_init(root, marketplace, executable, project, environment, artifacts, timeout):
    artifacts.mkdir(parents=True, exist_ok=True)
    debug = artifacts / "claude-debug.jsonl"
    state = Path(environment["AGENT_STATE_DIRECTORY"])
    before = receipt_ids(state, "claude")
    claude_environment = dict(environment)
    claude_environment["CLAUDE_CODE_ENTRYPOINT"] = "sdk-py"
    claude_environment.pop("CLAUDECODE", None)
    observer = artifacts / 'claude-startup-observer.json'
    process = subprocess.Popen(
        observed_command('claude', executable, project, observer, [
            "--output-format", "stream-json", "--verbose",
            "--input-format", "stream-json", "--debug-file", str(debug),
        ]),
        cwd=project, env=claude_environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", bufsize=1,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        messages = queue.Queue()
        completed = queue.Queue()
        errors = []
        start_line_reader(process.stdout, messages, parse_json=True, completion=completed)
        start_line_reader(process.stderr, errors)
        store = load_module("native_acceptance_claude_store", root / ".agents" / "dependencies" / "agent" / ".agents" / "agent-store" / "runtime" / "session_store.py")
        register = load_module("native_acceptance_claude_register", root / ".agents" / "dependencies" / "agent" / ".agents" / "agent" / "utility" / "peer" / "scripts" / "register_session.py")
        deadline = time.monotonic() + timeout
        request_id = "native-acceptance-1"
        process.stdin.write(json.dumps({
            "type": "control_request", "request_id": request_id,
            "request": {"subtype": "initialize", "hooks": None},
        }) + "\n")
        process.stdin.flush()
        initialized = None
        while time.monotonic() < deadline:
            try:
                message = messages.get(timeout=max(0.01, deadline - time.monotonic()))
            except queue.Empty:
                if process.poll() is not None:
                    break
                continue
            if isinstance(message, Exception):
                raise AcceptanceError(f"Claude startup emitted invalid JSON: {message}")
            if not isinstance(message, dict) or message.get("type") != "control_response":
                continue
            response = message.get("response")
            if not isinstance(response, dict) or response.get("request_id") != request_id:
                continue
            if response.get("subtype") != "success":
                raise AcceptanceError("Claude initialize request was not accepted")
            require_claude_discovery(response.get("response"))
            initialized = response
            break
        if initialized is None:
            detail = diagnostic(errors)
            message = "Claude startup did not return the initialize response"
            if detail:
                message = f"{message}: {detail}"
            raise AcceptanceError(message)
        session_id = None
        receipt_error = None
        while time.monotonic() < deadline:
            candidates = receipt_ids(state, "claude") - before
            if len(candidates) == 1:
                candidate = candidates.pop()
                try:
                    require_receipt(state, store, register, "claude", candidate, project, process.pid)
                except AcceptanceError as error:
                    receipt_error = error
                else:
                    session_id = candidate
                    break
            elif len(candidates) > 1:
                raise AcceptanceError("Claude startup created multiple session receipts")
            if process.poll() is not None:
                break
            time.sleep(0.05)
        if session_id is None:
            detail = diagnostic(errors) or str(receipt_error or "")
            message = "Claude startup did not create a live session receipt"
            if detail:
                message = f"{message}: {detail}"
            raise AcceptanceError(message)
        process.stdin.close()
        try:
            process.wait(timeout=max(0.01, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as error:
            raise AcceptanceError("Claude startup did not finish") from error
        if process.returncode:
            detail = diagnostic(errors)
            message = f"Claude startup failed with exit code {process.returncode}"
            if detail:
                message = f"{message}: {detail}"
            raise AcceptanceError(message)
        try:
            trace = debug.read_text(encoding="utf-8")
        except OSError as error:
            raise AcceptanceError("Claude did not create its debug artifact") from error
        if "SessionStart" not in trace:
            raise AcceptanceError("Claude debug artifact has no SessionStart marker")
        require_base_evidence(trace, marketplace / "plugins" / "base", "Claude debug artifact")
        require_observer(observer, 'confirmed')
        return session_id
    finally:
        if process.poll() is None:
            terminate_owned(process)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def accept_codex(root, marketplace, executable, project, environment, artifacts, timeout):
    install_codex_plugins(executable, marketplace, project, environment, timeout)
    trust = load_module("native_acceptance_trust", root / ".agents" / "dependencies" / "agent" / ".agents" / "agent" / "runtime" / "codex_hook_trust.py")
    store = load_module("native_acceptance_store", root / ".agents" / "dependencies" / "agent" / ".agents" / "agent-store" / "runtime" / "session_store.py")
    register = load_module("native_acceptance_register", root / ".agents" / "dependencies" / "agent" / ".agents" / "agent" / "utility" / "peer" / "scripts" / "register_session.py")
    with AppServer(executable, project, environment, timeout) as server:
        hooks = server.request("hooks/list", {"cwds": [str(project)]})
        require_startup_hooks(hooks)
        verified_roots = verify_installed_roots(hooks, trust, marketplace)
    with AppServer(executable, project, environment, timeout) as server:
        startup_hashes = trust_current_hooks(server, trust, executable, project, environment, verified_roots, timeout)
    observer = artifacts / 'codex-startup-observer.json'
    with AppServer(executable, project, environment, timeout, observer_receipt=observer) as server:
        hooks = server.request("hooks/list", {"cwds": [str(project)]})
        require_startup_hooks(hooks, trusted=True, trusted_hashes=startup_hashes)
        startup = server.request("thread/start", {
            "cwd": str(project), "approvalPolicy": "never", "sandbox": "read-only",
        })
        session_id = session_id_from(startup)
        thread = startup.get("thread") if isinstance(startup, dict) else None
        transcript = Path(thread.get("path")) if isinstance(thread, dict) and isinstance(thread.get("path"), str) else None
        if transcript is None:
            raise AcceptanceError("Codex startup response did not include its session transcript")
        server.request("turn/start", {
            "threadId": session_id,
            "input": [{"type": "text", "text": "native startup acceptance"}],
        })
        try:
            require_failed_turn(transcript, marketplace / "plugins" / "base", timeout)
        finally:
            snapshot_transcript(transcript, artifacts)
            snapshot_diagnostic(artifacts, "codex-app-server.stderr.log", diagnostic(server.stderr))
        require_receipt(
            Path(environment["AGENT_STATE_DIRECTORY"]), store, register, "codex", session_id,
            project, server.process.pid,
        )
        skills = server.request("skills/list", {"cwds": [str(project)], "forceReload": True})
        require_discovery(skills, "Codex skills/list")
        require_observer(observer, 'confirmed')
    return session_id


def accept_claude(root, marketplace, executable, project, environment, artifacts, timeout):
    install_claude_plugins(executable, marketplace, project, environment, timeout)
    return accept_claude_init(root, marketplace, executable, project, environment, artifacts, timeout)


@contextmanager
def authentication_failure_endpoint():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length', '0')))
            body = b'{"error":{"message":"native acceptance unauthenticated","type":"authentication_error"}}'
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = do_POST

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1'
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def isolated_environment(temporary_root, codex, claude, endpoint):
    codex_path = Path(codex).resolve(strict=True)
    claude_path = Path(claude).resolve(strict=True)
    home = temporary_root / "home"
    config = temporary_root / "config"
    data = temporary_root / "data"
    cache = temporary_root / "cache"
    codex_home = temporary_root / "codex-home"
    claude_home = temporary_root / "claude-home"
    state = temporary_root / "agent-state"
    for path in (home, config, data, cache, codex_home, claude_home, state):
        path.mkdir(parents=True, exist_ok=True)
    (codex_home / "config.toml").write_text(
        'cli_auth_credentials_store = "file"\n'
        'model_provider = "native_startup"\n\n'
        '[features]\n'
        'hooks = true\n\n'
        '[model_providers.native_startup]\n'
        'name = "OpenAI"\n'
        'base_url = ' + json.dumps(endpoint) + '\n'
        'wire_api = "responses"\n'
        'requires_openai_auth = false\n'
        'supports_websockets = false\n',
        encoding="utf-8",
    )
    environment = dict(os.environ)
    for key in list(environment):
        if (
            key.startswith(("ANTHROPIC_", "CLAUDE_CODE_", "CODEX_", "OPENAI_", "GIT_CONFIG_"))
            or key in {
                "AGENT_PROFILE", "CLAUDE_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_PROFILE",
                "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_PROFILE", "CODEX_PROFILE", "SESSION_ID",
                "TJ_AGENTS_PROFILE", "TOOL_CALL_ID",
            }
        ):
            environment.pop(key, None)
    directories = list(dict.fromkeys((str(codex_path.parent), str(claude_path.parent))))
    inherited = environment.get("PATH", "")
    environment.update(
        HOME=str(home),
        USERPROFILE=str(home),
        APPDATA=str(config),
        LOCALAPPDATA=str(data),
        XDG_CACHE_HOME=str(cache),
        XDG_CONFIG_HOME=str(config),
        XDG_DATA_HOME=str(data),
        CODEX_HOME=str(codex_home),
        CLAUDE_CONFIG_DIR=str(claude_home),
        AGENT_STATE_DIRECTORY=str(state),
        PATH=os.pathsep.join([*directories, inherited]) if inherited else os.pathsep.join(directories),
    )
    sys.path.insert(0, str(ROOT / '.agents/machine/scripts'))
    setup = load_module('native_acceptance_setup', ROOT / '.agents/machine/scripts/setup_machine.py')
    context = setup.Context(home=home, checkout=None, environ=environment, windows=os.name == 'nt')
    setup.apply_runtime(context)
    if setup.check_runtime(context):
        raise AcceptanceError('isolated setup runtime did not converge')
    environment['PATH'] = os.pathsep.join([*directories, str(state / 'bin'), inherited])
    return environment


def accept(root, marketplace, codex, claude, artifacts, timeout):
    root = root.resolve(strict=True)
    marketplace = marketplace.resolve(strict=True)
    if not (marketplace / "plugins").is_dir():
        raise AcceptanceError("candidate marketplace has no generated plugin packages")
    with tempfile.TemporaryDirectory(prefix="tj-agents-native-acceptance-") as temporary, \
            authentication_failure_endpoint() as endpoint:
        temporary_root = Path(temporary)
        environment = isolated_environment(temporary_root, codex, claude, endpoint)
        project = write_fixture(temporary_root / "fixture", environment)
        codex_session = accept_codex(root, marketplace, codex, project, environment, artifacts, timeout)
        claude_session = accept_claude(root, marketplace, claude, project, environment, artifacts, timeout)
        failed_marketplace = failure_marketplace(root, temporary_root / 'failure-marketplace')
        failures = {}
        for host, executable, operation in (('codex', codex, accept_codex), ('claude', claude, accept_claude)):
            case = temporary_root / ('failure-' + host)
            probe_environment = isolated_environment(case, codex, claude, endpoint)
            probe_project = write_fixture(case / 'fixture', probe_environment)
            evidence = artifacts / ('failure-' + host)
            failures[host] = require_failure_probe(host, evidence, lambda: operation(
                root, failed_marketplace, executable, probe_project, probe_environment, evidence, timeout))
    return {"claude_session": claude_session, "codex_session": codex_session,
            "plugins": list(IDENTITIES), 'required_hook_failure_probes': failures}


def failure_marketplace(root, directory):
    generator = load_module('native_failure_package_generator', root / 'scripts/sync_plugin_packages.py')
    _, output, _, _ = generator.build(root, validate_catalog_digests=False)
    output['plugins/workflow/.agents/workflow/policy/session/scripts/session-context.py'] = (
        b"raise RuntimeError('native-required-hook-failure-probe')\n"
    )
    output['plugins/workflow/hooks/codex.json'] = (
        root / '.agents/plugins/manifests/codex/workflow-hooks.json'
    ).read_bytes()
    generator.bind_codex_hook_snapshots(root, output, {'workflow'})
    for relative, content in output.items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return directory


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--marketplace", type=Path, required=True)
    parser.add_argument("--codex", required=True)
    parser.add_argument("--claude", required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=60)
    arguments = parser.parse_args(argv)
    if arguments.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    arguments.artifacts.mkdir(parents=True, exist_ok=True)
    (arguments.artifacts / 'native-host-acceptance.failure.log').unlink(missing_ok=True)
    try:
        result = accept(
            arguments.root, arguments.marketplace, arguments.codex, arguments.claude,
            arguments.artifacts, arguments.timeout,
        )
    except (AcceptanceError, OSError, ValueError, subprocess.SubprocessError) as error:
        snapshot_diagnostic(arguments.artifacts, "native-host-acceptance.failure.log", f"{error}\n")
        print(f"native-host-acceptance: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
