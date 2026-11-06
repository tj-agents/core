from __future__ import annotations

import argparse
import importlib.util
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("base", "workflow", "engineering")
IDENTITIES = tuple(f"{package}@tj-agents" for package in PACKAGES)
STARTUP_HOOKS = ("base@tj-agents",)
CONTEXT_PROBE = "native-tier-gate-context-probe"
FAILURE_PROBE = "native-tier-gate-failure-probe"


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


def terminate_owned(process):
    if os.name == "nt":
        subprocess.run(
            ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            timeout=10,
            check=False,
        )
    else:
        process.terminate()


def diagnostic(lines):
    return "\n".join(lines[-40:])[-4000:]


def run_native(arguments, cwd, environment, label, timeout):
    try:
        return subprocess.run(
            arguments,
            cwd=cwd,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
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
    return {
        "installed": [
            {
                "pluginId": item.get("id"),
                "installed": isinstance(item.get("id"), str),
                "enabled": item.get("enabled") is True,
            }
            for item in value
            if isinstance(item, dict)
        ]
    }


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
        raise AcceptanceError(
            f"native plugin discovery is missing enabled installed {', '.join(missing)}"
        )


def write_fixture(project, environment=None):
    selection = project / ".agents" / "plugins.json"
    selection.parent.mkdir(parents=True, exist_ok=True)
    selection.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "marketplaces": {"tj-agents": {"repository": "tj-agents/marketplace"}},
                "plugins": list(IDENTITIES),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if environment is not None:
        try:
            subprocess.run(
                ["git", "init", "--quiet", str(project)],
                cwd=project,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise AcceptanceError(
                f"isolated fixture Git initialization failed: {error}"
            ) from error
    return project


def session_id_from(value):
    if not isinstance(value, dict):
        raise AcceptanceError("native startup response is malformed")
    for candidate in (value.get("thread"), value.get("session"), value):
        if (
            isinstance(candidate, dict)
            and isinstance(candidate.get("id"), str)
            and candidate["id"]
        ):
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
    def __init__(self, executable, cwd, environment, timeout, popen=subprocess.Popen):
        self.timeout = timeout
        self.process = popen(
            [*native_command(executable), "app-server"],
            cwd=cwd,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.messages = queue.Queue()
        self.completed = queue.Queue()
        self.notifications = []
        self.stderr = []
        self.sequence = 0
        start_line_reader(
            self.process.stdout,
            self.messages,
            parse_json=True,
            completion=self.completed,
        )
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
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "tj-agents-native-acceptance",
                    "version": "1.0.0",
                },
                "capabilities": {"experimentalApi": True},
            },
        )
        self.send({"method": "initialized", "params": {}})

    def notifications_until(self, predicate):
        deadline = time.monotonic() + self.timeout
        while not predicate(self.notifications):
            self.notifications.append(self._next(deadline))
        return list(self.notifications)

    def drain_notifications(self) -> None:
        while True:
            try:
                value = self.messages.get_nowait()
            except queue.Empty:
                return
            if isinstance(value, Exception):
                self.notifications.append({"diagnosticError": str(value)})
            else:
                self.notifications.append(value)

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
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
        for entry in value["data"]
        if isinstance(entry, dict)
        for hook in entry.get("hooks", [])
        if isinstance(hook, dict)
        if hook.get("source") == "plugin" and hook.get("enabled") is True
    ]
    values = {hook.get("pluginId") for hook in hooks}
    missing = set(STARTUP_HOOKS) - values
    if missing:
        raise AcceptanceError(
            f"Codex hooks/list is missing required startup hooks for {', '.join(sorted(missing))}"
        )
    if trusted:
        untrusted = [
            hook.get("key", "unknown")
            for hook in hooks
            if hook.get("pluginId") in STARTUP_HOOKS
            and (
                hook.get("trustStatus") != "trusted"
                or hook.get("currentHash")
                != (trusted_hashes or {}).get(hook.get("key"), {}).get("trusted_hash")
            )
        ]
        if untrusted:
            raise AcceptanceError(
                f"Codex hooks/list did not trust current startup hooks: {', '.join(untrusted)}"
            )


def trust_current_hooks(
    server, trust, executable, project, environment, verified_roots, timeout
):
    inventory = json_result(
        run_native(
            [*native_command(executable), "plugin", "list", "--json"],
            project,
            environment,
            "Codex plugin discovery",
            timeout,
        ),
        "Codex plugin discovery",
    )
    hooks = server.request("hooks/list", {"cwds": [str(project)]})
    updates = trust.trust_updates(
        inventory, hooks["data"], project.resolve(), verified_roots
    )
    if not updates:
        raise AcceptanceError(
            "Codex trust update found no current verified startup hooks"
        )
    server.request(
        "config/batchWrite",
        {
            "edits": [
                {"keyPath": "hooks.state", "value": updates, "mergeStrategy": "upsert"}
            ],
            "reloadUserConfig": True,
        },
    )
    return updates


def verify_installed_roots(value, trust, marketplace):
    roots = {}
    expected = {
        identity: marketplace / "plugins" / package
        for package, identity in zip(PACKAGES, IDENTITIES)
    }
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
            if trust.package_files(installed) != trust.package_files(
                expected[identity]
            ):
                raise AcceptanceError(
                    f"installed {identity} plugin differs from the candidate package"
                )
            roots[identity] = SimpleNamespace(identity=identity, root=installed)
    for identity in STARTUP_HOOKS:
        if identity not in roots:
            raise AcceptanceError(
                f"Codex hooks/list has no installed package root for {identity}"
            )
    return list(roots.values())


def require_hook_completion(notifications: list[dict]) -> None:
    for notification in notifications:
        if notification.get("method") != "hook/completed":
            continue
        run = notification.get("params", {}).get("run", {})
        if run.get("eventName") != "sessionStart" or run.get("source") != "plugin":
            continue
        if "base" not in Path(run.get("sourcePath", "")).parts:
            continue
        if run.get("status") != "completed":
            raise AcceptanceError(f"Base SessionStart did not complete: {run}")
        return
    raise AcceptanceError("Codex did not complete the Base SessionStart hook")


def require_failure_evidence(path: Path) -> None:
    try:
        diagnostic = path.read_text(encoding="utf-8")
    except OSError as error:
        raise AcceptanceError(
            "tier-gate fail-open probe has no diagnostic evidence"
        ) from error
    if diagnostic != FAILURE_PROBE:
        raise AcceptanceError("tier-gate fail-open probe recorded an unrelated error")


def require_context(evidence: str, expected: str | None, label: str) -> None:
    if expected is not None and expected not in evidence:
        raise AcceptanceError(f"{label} did not include {expected}")


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


def require_failed_turn(path, expected_context, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        entries = transcript_entries(path)
        if entries is None:
            time.sleep(0.05)
            continue
        evidence = json.dumps(entries, sort_keys=True)
        try:
            require_context(evidence, expected_context, "Codex session transcript")
        except AcceptanceError:
            pass
        else:
            for entry in entries:
                payload = entry.get("payload") if isinstance(entry, dict) else None
                if (
                    not isinstance(payload, dict)
                    or payload.get("type") != "task_complete"
                ):
                    continue
                error = payload.get("error")
                if isinstance(error, dict) and "401" in str(error.get("message", "")):
                    return entries
                raise AcceptanceError(
                    "Codex startup turn did not complete with the expected unauthenticated 401"
                )
        time.sleep(0.05)
    raise AcceptanceError(
        "Codex startup turn did not record expected tier context and an unauthenticated 401 completion"
    )


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
                item
                for key, item in record.items()
                if key in {"id", "name", "skill", "qualifiedName", "command"}
                and isinstance(item, str)
            }
            if qualified in values:
                found = True
                break
            if skill not in values:
                continue
            sources = {
                item.replace("\\", "/").casefold()
                for key, item in record.items()
                if key in {"pluginId", "plugin", "source", "path", "root", "location"}
                and isinstance(item, str)
            }
            if any(
                source in {package, f"{package}@tj-agents"}
                or f"/plugins/{package}/" in source
                for source in sources
            ):
                found = True
                break
        if not found:
            raise AcceptanceError(
                f"{label} did not discover the required {package} skill"
            )


def require_claude_discovery(response):
    if not isinstance(response, dict) or not isinstance(response.get("commands"), list):
        raise AcceptanceError("Claude initialize response has no command inventory")
    names = {
        command.get("name")
        for command in response["commands"]
        if isinstance(command, dict) and isinstance(command.get("name"), str)
    }
    for name in ("workflow:run", "engineering:commit"):
        if name not in names:
            raise AcceptanceError(f"Claude initialize response did not discover {name}")


def install_codex_plugins(executable, marketplace, project, environment, timeout):
    run_native(
        [
            *native_command(executable),
            "plugin",
            "marketplace",
            "add",
            str(marketplace),
            "--json",
        ],
        project,
        environment,
        "Codex marketplace registration",
        timeout,
    )
    for identity in IDENTITIES:
        run_native(
            [*native_command(executable), "plugin", "add", identity, "--json"],
            project,
            environment,
            f"Codex plugin installation for {identity}",
            timeout,
        )
    inventory = json_result(
        run_native(
            [*native_command(executable), "plugin", "list", "--json"],
            project,
            environment,
            "Codex plugin discovery",
            timeout,
        ),
        "Codex plugin discovery",
    )
    require_plugins(inventory)


def install_claude_plugins(executable, marketplace, project, environment, timeout):
    run_native(
        [
            *native_command(executable),
            "plugin",
            "marketplace",
            "add",
            str(marketplace),
            "--scope",
            "user",
        ],
        project,
        environment,
        "Claude marketplace registration",
        timeout,
    )
    for identity in IDENTITIES:
        run_native(
            [
                *native_command(executable),
                "plugin",
                "install",
                identity,
                "--scope",
                "user",
            ],
            project,
            environment,
            f"Claude plugin installation for {identity}",
            timeout,
        )
    inventory = claude_plugin_inventory(
        run_native(
            [*native_command(executable), "plugin", "list", "--json"],
            project,
            environment,
            "Claude plugin discovery",
            timeout,
        )
    )
    require_plugins(inventory)


def accept_claude_init(
    root,
    marketplace,
    executable,
    project,
    environment,
    artifacts,
    timeout,
    expected_context=CONTEXT_PROBE,
):
    artifacts.mkdir(parents=True, exist_ok=True)
    debug = artifacts / "claude-debug.jsonl"
    debug.unlink(missing_ok=True)
    claude_environment = dict(environment)
    claude_environment["CLAUDE_CODE_ENTRYPOINT"] = "sdk-py"
    claude_environment.pop("CLAUDECODE", None)
    process = subprocess.Popen(
        [
            *native_command(executable),
            "--output-format",
            "stream-json",
            "--verbose",
            "--input-format",
            "stream-json",
            "--debug-file",
            str(debug),
        ],
        cwd=project,
        env=claude_environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        messages = queue.Queue()
        completed = queue.Queue()
        errors = []
        start_line_reader(
            process.stdout, messages, parse_json=True, completion=completed
        )
        start_line_reader(process.stderr, errors)
        deadline = time.monotonic() + timeout
        request_id = "native-acceptance-1"
        process.stdin.write(
            json.dumps(
                {
                    "type": "control_request",
                    "request_id": request_id,
                    "request": {"subtype": "initialize", "hooks": None},
                }
            )
            + "\n"
        )
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
            if (
                not isinstance(message, dict)
                or message.get("type") != "control_response"
            ):
                continue
            response = message.get("response")
            if (
                not isinstance(response, dict)
                or response.get("request_id") != request_id
            ):
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
        require_context(trace, expected_context, "Claude debug artifact")
    finally:
        if process.poll() is None:
            terminate_owned(process)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def accept_codex(
    root,
    marketplace,
    executable,
    project,
    environment,
    artifacts,
    timeout,
    expected_context=CONTEXT_PROBE,
):
    install_codex_plugins(executable, marketplace, project, environment, timeout)
    trust = load_module(
        "native_acceptance_trust",
        root
        / ".agents"
        / "dependencies"
        / "agent"
        / ".agents"
        / "agent"
        / "runtime"
        / "codex"
        / "hook_trust.py",
    )
    with AppServer(executable, project, environment, timeout) as server:
        hooks = server.request("hooks/list", {"cwds": [str(project)]})
        require_startup_hooks(hooks)
        verified_roots = verify_installed_roots(hooks, trust, marketplace)
    with AppServer(executable, project, environment, timeout) as server:
        startup_hashes = trust_current_hooks(
            server, trust, executable, project, environment, verified_roots, timeout
        )
    with AppServer(executable, project, environment, timeout) as server:
        hooks = server.request("hooks/list", {"cwds": [str(project)]})
        require_startup_hooks(hooks, trusted=True, trusted_hashes=startup_hashes)
        startup = server.request(
            "thread/start",
            {
                "cwd": str(project),
                "approvalPolicy": "never",
                "sandbox": "read-only",
            },
        )
        session_id = session_id_from(startup)
        thread = startup.get("thread") if isinstance(startup, dict) else None
        transcript = (
            Path(thread.get("path"))
            if isinstance(thread, dict) and isinstance(thread.get("path"), str)
            else None
        )
        if transcript is None:
            raise AcceptanceError(
                "Codex startup response did not include its session transcript"
            )
        server.request(
            "turn/start",
            {
                "threadId": session_id,
                "input": [{"type": "text", "text": "native startup acceptance"}],
            },
        )
        try:
            require_failed_turn(transcript, expected_context, timeout)
            skills = server.request(
                "skills/list", {"cwds": [str(project)], "forceReload": True}
            )
            require_discovery(skills, "Codex skills/list")
            require_hook_completion(server.notifications)
        finally:
            server.drain_notifications()
            snapshot_diagnostic(
                artifacts, "codex-hooks.json", json.dumps(hooks, indent=2)
            )
            snapshot_transcript(transcript, artifacts)
            snapshot_diagnostic(
                artifacts, "codex-app-server.stderr.log", diagnostic(server.stderr)
            )
            snapshot_diagnostic(
                artifacts,
                "codex-notifications.json",
                json.dumps(server.notifications, indent=2),
            )


def accept_claude(
    root,
    marketplace,
    executable,
    project,
    environment,
    artifacts,
    timeout,
    expected_context=CONTEXT_PROBE,
):
    install_claude_plugins(executable, marketplace, project, environment, timeout)
    accept_claude_init(
        root,
        marketplace,
        executable,
        project,
        environment,
        artifacts,
        timeout,
        expected_context=expected_context,
    )


@contextmanager
def authentication_failure_endpoint():
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            body = b'{"error":{"message":"native acceptance unauthenticated","type":"authentication_error"}}'
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = do_POST

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
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
        "[features]\n"
        "hooks = true\n\n"
        "[model_providers.native_startup]\n"
        'name = "OpenAI"\n'
        "base_url = " + json.dumps(endpoint) + "\n"
        'wire_api = "responses"\n'
        "requires_openai_auth = false\n"
        "supports_websockets = false\n",
        encoding="utf-8",
    )
    environment = dict(os.environ)
    for key in list(environment):
        if key.startswith(
            ("ANTHROPIC_", "CLAUDE_CODE_", "CODEX_", "OPENAI_", "GIT_CONFIG_")
        ) or key in {
            "AGENT_PROFILE",
            "CLAUDE_API_KEY",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "CLAUDE_CODE_PROFILE",
            "CLAUDE_CODE_USE_BEDROCK",
            "CLAUDE_PROFILE",
            "CODEX_PROFILE",
            "SESSION_ID",
            "TJ_AGENTS_PROFILE",
            "TOOL_CALL_ID",
        }:
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
        PATH=os.pathsep.join([*directories, inherited])
        if inherited
        else os.pathsep.join(directories),
    )
    return environment


def accept(root, marketplace, codex, claude, artifacts, timeout):
    root = root.resolve(strict=True)
    marketplace = marketplace.resolve(strict=True)
    if not (marketplace / "plugins").is_dir():
        raise AcceptanceError("candidate marketplace has no generated plugin packages")
    with (
        tempfile.TemporaryDirectory(prefix="tj-agents-native-acceptance-") as temporary,
        authentication_failure_endpoint() as endpoint,
    ):
        temporary_root = Path(temporary)
        environment = isolated_environment(temporary_root, codex, claude, endpoint)
        project = write_fixture(temporary_root / "fixture", environment)
        contextual = context_marketplace(
            root, marketplace, temporary_root / "context-marketplace"
        )
        accept_codex(root, contextual, codex, project, environment, artifacts, timeout)
        accept_claude(
            root, contextual, claude, project, environment, artifacts, timeout
        )
        failed_marketplace = failure_marketplace(
            root, contextual, temporary_root / "failure-marketplace"
        )
        for host, executable, operation in (
            ("codex", codex, accept_codex),
            ("claude", claude, accept_claude),
        ):
            case = temporary_root / ("failure-" + host)
            probe_environment = isolated_environment(case, codex, claude, endpoint)
            probe_project = write_fixture(case / "fixture", probe_environment)
            evidence = artifacts / ("failure-" + host)
            evidence.mkdir(parents=True, exist_ok=True)
            failure_evidence = evidence / "tier-gate-failure.txt"
            failure_evidence.unlink(missing_ok=True)
            probe_environment["TJ_NATIVE_GATE_FAILURE_EVIDENCE"] = str(failure_evidence)
            operation(
                root,
                failed_marketplace,
                executable,
                probe_project,
                probe_environment,
                evidence,
                timeout,
                expected_context=None,
            )
            require_failure_evidence(failure_evidence)
    return {
        "plugins": list(IDENTITIES),
        "tier_context_probe": CONTEXT_PROBE,
        "fail_open_probes": ["codex", "claude"],
    }


def fixture_marketplace(
    root: Path, marketplace: Path, directory: Path, changes: dict[str, bytes]
) -> Path:
    shutil.copytree(marketplace / "plugins", directory / "plugins")
    for relative in (
        ".claude-plugin/marketplace.json",
        ".agents/plugins/marketplace.json",
    ):
        source = marketplace / relative
        target = directory / source.relative_to(marketplace)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    generator = load_module(
        "native_fixture_package_generator", root / "scripts/sync_plugin_packages.py"
    )
    output = {
        path.relative_to(directory).as_posix(): generator.canonical_output_bytes(
            path.read_bytes()
        )
        for path in (directory / "plugins/base").rglob("*")
        if path.is_file()
    }
    output.update(
        {path: generator.canonical_output_bytes(body) for path, body in changes.items()}
    )
    output["plugins/base/hooks/codex.json"] = (
        root / ".agents/plugins/manifests/codex/base-hooks.json"
    ).read_bytes()
    generator.bind_codex_hook_snapshots(root, output, {"base"})
    for relative, content in output.items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return directory


def context_marketplace(root: Path, marketplace: Path, directory: Path) -> Path:
    declaration = json.loads(
        (marketplace / "plugins/base/tier.json").read_text(encoding="utf-8")
    )
    declaration.update(schema_version=3, session_context=CONTEXT_PROBE)
    return fixture_marketplace(
        root,
        marketplace,
        directory,
        {
            "plugins/base/tier.json": (json.dumps(declaration) + "\n").encode("utf-8"),
        },
    )


def failure_marketplace(root: Path, marketplace: Path, directory: Path) -> Path:
    source = (marketplace / "plugins/base/hooks/tier_gate.py").read_text(
        encoding="utf-8"
    )
    statement = "context = statement(project_root(payload))"
    if source.count(statement) != 1:
        raise AcceptanceError(
            "tier-gate failure probe could not locate its protected statement"
        )
    source = source.replace(statement, f"raise RuntimeError({FAILURE_PROBE!r})")
    handler = 'print(f"tier gate failed: {error}", file=sys.stderr)'
    if source.count(handler) != 1:
        raise AcceptanceError(
            "tier-gate failure probe could not locate its diagnostic handler"
        )
    source = source.replace(
        handler,
        handler
        + '\n        Path(os.environ["TJ_NATIVE_GATE_FAILURE_EVIDENCE"]).write_text('
        + 'str(error), encoding="utf-8")',
    )
    return fixture_marketplace(
        root,
        marketplace,
        directory,
        {
            "plugins/base/hooks/tier_gate.py": source.encode("utf-8"),
        },
    )


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
    (arguments.artifacts / "native-host-acceptance.failure.log").unlink(missing_ok=True)
    try:
        result = accept(
            arguments.root,
            arguments.marketplace,
            arguments.codex,
            arguments.claude,
            arguments.artifacts,
            arguments.timeout,
        )
    except (AcceptanceError, OSError, ValueError, subprocess.SubprocessError) as error:
        snapshot_diagnostic(
            arguments.artifacts, "native-host-acceptance.failure.log", f"{error}\n"
        )
        print(f"native-host-acceptance: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
