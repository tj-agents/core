#!/usr/bin/env python3
"""Run a verified tj-agents preflight through native SessionStart binding."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from codex_marketplace_sync import codex_config_selection
import launch_status
from rolling_plugins import OPERATION_TIMEOUT_SECONDS, RollingPluginError, preflight, terminate_process_tree
from terminal_command import command_for_target, native_target_for_shim


HERE = Path(__file__).resolve().parent
ACK_DIRECTORY_ENV = "TJ_AGENTS_STARTUP_ACK_DIRECTORY"
ACK_TOKEN_ENV = "TJ_AGENTS_STARTUP_ACK_TOKEN"
SNAPSHOT_DIRECTORY_ENV = "TJ_AGENTS_STARTUP_SNAPSHOT_DIRECTORY"
STARTUP_TIMEOUT_SECONDS = 20


class StartupBindingError(RuntimeError):
    pass


def _snapshot_module():
    paths = (HERE.parents[1] / "hooks" / "codex_hook_snapshot.py",
             HERE.parents[2] / "hooks" / "codex_hook_snapshot.py")
    path = next((candidate for candidate in paths if candidate.is_file()), None)
    if path is None:
        raise StartupBindingError("Codex hook snapshot helper is unavailable")
    spec = importlib.util.spec_from_file_location("tj_agents_codex_hook_snapshot", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _module(name: str, paths: Sequence[Path]):
    path = next((candidate for candidate in paths if candidate.is_file()), None)
    if path is None:
        raise StartupBindingError(f"{name} is unavailable")
    spec = importlib.util.spec_from_file_location(f"tj_agents_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def _remaining(prepared, limit: float) -> float:
    deadline = getattr(prepared, "deadline", None)
    if deadline is None:
        return limit
    return deadline.remaining(limit)


def _startup_remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise StartupBindingError("startup preparation exceeded its deadline")
    return remaining


def _converge(prepared, executable: str, project: Path, trust_runtime: bool = True) -> None:
    if not prepared.selected_roots:
        return
    _remaining(prepared, OPERATION_TIMEOUT_SECONDS)
    permissions = _module(
        "harness_permissions_sync",
        (
            HERE.parent / "utility" / "plugin-selection" / "scripts" / "harness_permissions_sync.py",
            HERE.parents[2] / ".agents" / "machine" / "utility" / "plugin-selection" / "scripts" / "harness_permissions_sync.py",
        ),
    )
    permissions.apply_verified(os.environ, prepared.host, project, prepared.selected_roots)
    _remaining(prepared, OPERATION_TIMEOUT_SECONDS)
    if prepared.host == "codex":
        convergence = _module("verified_convergence", (HERE / "verified_convergence.py",))
        convergence.converge(os.environ, project, prepared.selected_roots)
        if trust_runtime:
            trust = _module("codex_hook_trust", (HERE / "codex_hook_trust.py",))
            trust.apply_trust(
                executable, project, verified_roots=prepared.selected_roots,
                launch_args=prepared.launch_args, environment=prepared.environment,
                timeout=prepared.deadline.remaining(),
            )
        _remaining(prepared, OPERATION_TIMEOUT_SECONDS)


def _configuration_root(host: str) -> Path:
    if host == "claude":
        return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    if host == "codex":
        return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    raise StartupBindingError(f"unsupported host: {host}")


def _preflight_arguments(host: str, executable: str, project: Path, arguments: Sequence[str],
                         remaining: Callable[[], float]) -> Mapping[str, object]:
    if host == "claude":
        config = _configuration_root(host)
        return {"plugins_root": str(Path(os.environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR", config / "plugins"))),
                "argv": tuple(arguments), "deadline_seconds": remaining()}
    selection = codex_config_selection(executable, project, launch_args=arguments, timeout=remaining())
    selection["deadline_seconds"] = remaining()
    selection["selection_reader"] = lambda: codex_config_selection(
        executable, project, launch_args=arguments, timeout=remaining(),
    )
    return selection


def _session_start_dispatcher(roots, host: str) -> bool:
    for verified in roots:
        definition = verified.root / "hooks" / f"{host}.json"
        try:
            payload = json.loads(definition.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        hooks = payload.get("hooks") if isinstance(payload, dict) else None
        session_start = hooks.get("SessionStart") if isinstance(hooks, dict) else None
        if "hook_dispatch.py" in json.dumps(session_start, ensure_ascii=True):
            return True
    return False


def _binding_environment(directory: Path, token: str, snapshot_directory: Path,
                         prepared_environment: Mapping[str, str], extra_environment: Mapping[str, str] | None):
    environment = _without_binding_state(os.environ)
    environment.update(prepared_environment)
    if extra_environment:
        environment.update(extra_environment)
    environment[ACK_DIRECTORY_ENV] = str(directory)
    environment[ACK_TOKEN_ENV] = token
    environment[SNAPSHOT_DIRECTORY_ENV] = str(snapshot_directory)
    return environment


def _without_binding_state(environment: Mapping[str, str]) -> dict[str, str]:
    values = dict(environment)
    values.pop(ACK_DIRECTORY_ENV, None)
    values.pop(ACK_TOKEN_ENV, None)
    values.pop(SNAPSHOT_DIRECTORY_ENV, None)
    values.pop("TJ_AGENTS_CODEX_RUNTIME_RECEIPT", None)
    values.pop("TJ_AGENTS_CODEX_RUNTIME_RECEIPT_SHA256", None)
    return values


def _cleanup_runtime(runtime, binding, configuration: Path) -> None:
    try:
        runtime.cleanup_runtime(binding, configuration)
    except Exception:
        pass


def _acknowledged(directory: Path, token: str) -> bool:
    path = directory / token
    try:
        return path.is_file() and path.read_text(encoding="utf-8") == token
    except OSError:
        return False


def _launch_arguments(arguments: Sequence[str], overrides: Sequence[str]) -> list[str]:
    values = list(arguments)
    prepared = list(overrides)
    try:
        delimiter = values.index("--")
    except ValueError:
        delimiter = len(values)
    return [*values[:delimiter], *prepared, *values[delimiter:]]


def _preseed_snapshots(roots, snapshot_directory: Path) -> None:
    helper = _snapshot_module()
    for verified in roots:
        plugin = verified.identity.rsplit("@", 1)[0]
        expected = helper.digest_tree(verified.root, plugin)
        helper.snapshot_root(verified.root, expected, plugin, snapshot_directory)


def run_session(host: str, target: str, project: Path, arguments: Sequence[str], *,
                extra_environment: Mapping[str, str] | None = None,
                timeout: float = STARTUP_TIMEOUT_SECONDS,
                on_running: Callable[[], None] | None = None) -> int:
    running = on_running or (lambda: None)
    project = Path(project).resolve()
    configuration = _configuration_root(host).resolve()
    startup_deadline = time.monotonic() + OPERATION_TIMEOUT_SECONDS
    try:
        executable = native_target_for_shim(target)
        preflight_arguments = _preflight_arguments(
            host, executable, project, arguments,
            lambda: _startup_remaining(startup_deadline),
        )
        effective_project = project
        if host == "codex":
            selected_project = preflight_arguments.get("project")
            if not isinstance(selected_project, Path):
                raise StartupBindingError("Codex effective configuration did not report a project directory")
            effective_project = selected_project
        with preflight(host, configuration, effective_project, preflight_arguments) as active:
            if host == "codex":
                logical = getattr(active, "prepared", None)
                if logical is None:
                    raise StartupBindingError("Codex rolling preflight did not prepare a package set")
                if logical.selected_roots:
                    runtime = _module("codex_runtime_binding", (HERE / "codex_runtime_binding.py",))
                    binding = runtime.prepare_runtime(
                        executable, effective_project, configuration, logical, preflight_arguments, arguments,
                    )
                    process = None
                    cleaned = False
                    try:
                        from rolling_plugins import verify_final
                        verify_final(logical, "codex", configuration, effective_project, preflight_arguments)
                        _converge(logical, executable, effective_project, trust_runtime=False)
                        snapshot_directory = binding.directory / "hook-snapshots"
                        snapshot_directory.mkdir()
                        if os.name != "nt":
                            snapshot_directory.chmod(0o700)
                        _preseed_snapshots(binding.prepared.selected_roots, snapshot_directory)
                        active.acknowledge_binding()
                        environment = _without_binding_state(os.environ)
                        environment.update(binding.prepared.environment)
                        environment.update(binding.environment)
                        environment[SNAPSHOT_DIRECTORY_ENV] = str(snapshot_directory)
                        if extra_environment:
                            environment.update(extra_environment)
                        try:
                            process = subprocess.Popen(
                                command_for_target(target, _launch_arguments(arguments, binding.prepared.launch_args)),
                                cwd=project, env=environment, start_new_session=os.name != "nt",
                            )
                            running()
                            return process.wait()
                        except OSError as error:
                            raise StartupBindingError(f"native {host} could not start: {error}") from error
                        finally:
                            if process is None or process.poll() is not None:
                                _cleanup_runtime(runtime, binding, configuration)
                                cleaned = True
                    except BaseException:
                        if not cleaned and (process is None or process.poll() is not None):
                            _cleanup_runtime(runtime, binding, configuration)
                        raise
                active.acknowledge_binding()
                environment = _without_binding_state(os.environ)
                environment.update(logical.environment)
                if extra_environment:
                    environment.update(extra_environment)
                try:
                    running()
                    return subprocess.run(command_for_target(target, arguments), cwd=project, env=environment).returncode
                except OSError as error:
                    raise StartupBindingError(f"native {host} could not start: {error}") from error
            prepared = active.materialize_native(executable)
            _converge(prepared, executable, effective_project)
            launch_arguments = _launch_arguments(arguments, prepared.launch_args)
            if not prepared.selected_roots:
                active.acknowledge_binding()
                environment = _without_binding_state(os.environ)
                environment.update(prepared.environment)
                if extra_environment:
                    environment.update(extra_environment)
                try:
                    running()
                    return subprocess.run(command_for_target(target, launch_arguments), cwd=project,
                                          env=environment).returncode
                except OSError as error:
                    raise StartupBindingError(f"native {host} could not start: {error}") from error
            if not _session_start_dispatcher(prepared.selected_roots, host):
                raise StartupBindingError("verified selected tj-agents packages do not provide a hook_dispatch SessionStart hook")
            directory = Path(tempfile.mkdtemp(prefix="tj-agents-startup-"))
            snapshot_directory = directory / "hook-snapshots"
            snapshot_directory.mkdir()
            if os.name != "nt":
                directory.chmod(0o700)
                snapshot_directory.chmod(0o700)
            token = secrets.token_urlsafe(32)
            try:
                if host == "codex":
                    _preseed_snapshots(prepared.selected_roots, snapshot_directory)
                environment = _binding_environment(directory, token, snapshot_directory,
                                                    prepared.environment, extra_environment)
                process = None
                try:
                    process = subprocess.Popen(
                        command_for_target(target, launch_arguments), cwd=project, env=environment,
                        start_new_session=os.name != "nt",
                    )
                except OSError as error:
                    raise StartupBindingError(f"native {host} could not start: {error}") from error
                try:
                    deadline = time.monotonic() + _remaining(prepared, timeout)
                    while process.poll() is None and time.monotonic() < deadline:
                        if _acknowledged(directory, token):
                            active.acknowledge_binding()
                            running()
                            return process.wait()
                        time.sleep(0.05)
                    if process.poll() is not None:
                        return process.returncode
                    raise StartupBindingError(f"native {host} did not acknowledge SessionStart before the startup deadline")
                except BaseException as error:
                    if process.poll() is None:
                        try:
                            terminate_process_tree(process)
                        except Exception as cleanup_error:
                            raise StartupBindingError(
                                f"{error}; native {host} cleanup also failed: {cleanup_error}"
                            ) from error
                    raise
            finally:
                shutil.rmtree(directory, ignore_errors=True)
    except RollingPluginError as error:
        raise StartupBindingError(str(error)) from None
    except StartupBindingError:
        raise
    except Exception as error:
        raise StartupBindingError(f"{host} startup preflight could not complete: {error}") from error


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex"), required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(argv)
    arguments = parsed.arguments[1:] if parsed.arguments[:1] == ["--"] else parsed.arguments
    status: dict[str, object] = {"pid": os.getpid()}

    def report(state: str, **details: object) -> None:
        status.update(details, state=state, at=time.time())
        if parsed.status_file is not None:
            launch_status.replace(parsed.status_file, status)

    if parsed.status_file is not None and not launch_status.create(
            parsed.status_file, {**status, "state": "preparing", "at": time.time()}):
        print(f"standards: {parsed.host} launch was abandoned or already claimed before startup", file=sys.stderr)
        return 1
    try:
        returncode = run_session(parsed.host, parsed.target, parsed.project, arguments,
                                 on_running=lambda: report("running", running_at=time.time()))
    except StartupBindingError as error:
        message = f"standards: {parsed.host} refresh failed: {error}"
        print(message, file=sys.stderr)
        report("failed", error=message)
        return 1
    report("exited", returncode=returncode)
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
