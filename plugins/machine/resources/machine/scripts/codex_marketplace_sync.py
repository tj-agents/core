#!/usr/bin/env python3
"""Prepare enabled Codex plugins from current authenticated publisher main branches."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent

sys.path.insert(0, str(HERE))
from codex_hook_trust import AppServer, apply_trust, command as codex_command  # noqa: E402
import rolling_plugins  # noqa: E402
from claude_standards_sync import MARKETPLACE_TIMEOUT_SECONDS, PLUGIN_TIMEOUT_SECONDS  # noqa: E402

TJ_AGENTS_MARKETPLACES = {"base-agents", "tj-agents", "dotagents", "cpp-agents", "react-agents"}


class SyncError(Exception):
    """A Codex standards refresh step failed; the message is the whole report."""


def maintenance_arguments(arguments):
    values = list(arguments or ())
    result = []
    index = 0
    while index < len(values):
        value = values[index]
        if value == "--":
            break
        if value in {"-c", "--config", "--enable", "--disable"}:
            if index + 1 >= len(values):
                raise SyncError(f"Codex option {value} requires a value")
            result.extend((value, values[index + 1]))
            index += 2
            continue
        if value.startswith("--config=") or value.startswith("--enable=") or value.startswith("--disable="):
            result.append(value)
            index += 1
            continue
        if value in {"-C", "--cd"}:
            if index + 1 >= len(values):
                raise SyncError(f"Codex option {value} requires a directory")
            index += 2
            continue
        if value.startswith("--cd="):
            index += 1
            continue
        if value in {"--profile", "-p"} or value.startswith("--profile=") or value.startswith("-p"):
            raise SyncError("Codex named profiles are unsupported by rolling plugin preflight")
        if value.startswith("-"):
            index += 1
            continue
        index += 1
    return result


def effective_codex_directory(working_directory, arguments=()):
    current = Path(working_directory).resolve()
    values = list(arguments or ())
    index = 0
    while index < len(values):
        value = values[index]
        if value == "--":
            break
        if value in {"-C", "--cd"}:
            if index + 1 >= len(values):
                raise SyncError(f"Codex option {value} requires a directory")
            current = (current / values[index + 1]).resolve()
            index += 2
            continue
        if value.startswith("--cd="):
            current = (current / value.split("=", 1)[1]).resolve()
        if value in {"-c", "--config", "--enable", "--disable"}:
            index += 2
            continue
        if value in {"--profile", "-p"} or value.startswith("--profile=") or value.startswith("-p"):
            raise SyncError("Codex named profiles are unsupported by rolling plugin preflight")
        index += 1
    return current


def _effective_config(response):
    if not isinstance(response, dict):
        raise SyncError("Codex config/read returned an invalid response")
    config = response.get("config", response.get("effectiveConfig", response))
    if not isinstance(config, dict):
        raise SyncError("Codex config/read returned no effective config")
    return config


def _plugin_enabled(value):
    if value is True:
        return True
    if value is False:
        return False
    if isinstance(value, dict) and isinstance(value.get("enabled"), bool):
        return value["enabled"]
    return None


def _marketplace_source(value):
    if not isinstance(value, dict):
        return None
    kind = value.get("source_type", value.get("sourceType"))
    source = value.get("source")
    if kind != "git" or not isinstance(source, str):
        return None
    return source


def codex_config_selection(codex_executable, working_directory, launch_args=(), timeout=None):
    arguments = maintenance_arguments(launch_args)
    directory = effective_codex_directory(working_directory, launch_args)
    try:
        with AppServer(codex_executable, directory, arguments, timeout=timeout or 90) as server:
            response = server.request("config/read", {"cwd": str(directory), "includeLayers": True})
    except (OSError, RuntimeError, ValueError) as error:
        raise SyncError(f"Codex effective configuration could not be read: {error}") from None
    config = _effective_config(response)
    plugins = config.get("plugins")
    marketplaces = config.get("marketplaces")
    if plugins is None:
        plugins = {}
    if marketplaces is None:
        marketplaces = {}
    if not isinstance(plugins, dict) or not isinstance(marketplaces, dict):
        raise SyncError("Codex effective configuration has invalid plugins or marketplaces")
    selected, disabled = [], []
    for identity, value in plugins.items():
        enabled = _plugin_enabled(value)
        if enabled is None or not isinstance(identity, str) or identity.count("@") != 1:
            continue
        name, marketplace = identity.rsplit("@", 1)
        if enabled is False:
            disabled.append(identity)
            continue
        source = _marketplace_source(marketplaces.get(marketplace))
        if source is None:
            if marketplace.casefold() in TJ_AGENTS_MARKETPLACES:
                raise SyncError(f"Codex effective configuration has no authenticated Git source for selected plugin {identity}")
            continue
        selected.append({"identity": identity, "marketplace": marketplace, "source_url": source})
    hooks = config.get("hooks")
    hook_state = hooks.get("state") if isinstance(hooks, dict) else {}
    if hook_state is None:
        hook_state = {}
    if not isinstance(hook_state, dict):
        raise SyncError("Codex effective configuration has invalid hooks.state")
    return {
        "selections": selected,
        "final_selections": selected,
        "disabled": disabled,
        "project": directory,
        "effective_plugin_configuration": dict(plugins),
        "effective_marketplace_configuration": dict(marketplaces),
        "hook_state": dict(hook_state),
    }


def _load_agent_cli():
    path = HERE / 'agent_cli.py'
    if not path.is_file():
        raise SyncError(f'The shared agent_cli.py library was not found beside {__file__}.')
    spec = importlib.util.spec_from_file_location('codex_marketplace_sync_agent_cli', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_codex_shim(executable):
    """Whether <executable> is a launch-time shim rather than the native binary itself: a `.ps1`/`.cmd`
    wrapper, or a POSIX `#!` script. Used to tell a caller-supplied `--codex` that already names the npm
    entry point from one that names the real executable, so only the former is re-resolved."""
    if Path(executable).suffix.casefold() in ('.ps1', '.cmd', '.bat'):
        return True
    try:
        with open(executable, 'rb') as handle:
            return handle.read(2) == b'#!'
    except OSError:
        # Matches agent_cli._is_script's own fail-safe direction: an unreadable path cannot be confirmed
        # native, so it is re-resolved rather than trusted as-is.
        return True



def resolve_codex_for_sync(codex: str | None) -> str:
    """Return a native Codex binary for maintenance, retaining the typed shim for final launch."""
    if codex and not is_codex_shim(codex):
        return codex
    agent_cli = _load_agent_cli()
    try:
        resolved, _version = agent_cli.resolve_codex_executable()
    except agent_cli.LaunchError as error:
        raise SyncError(str(error)) from None
    return resolved

def invoke_codex_sync_command(codex_executable, arguments, cwd=None, run=subprocess.run, timeout=None):
    """Run one `codex <arguments>` call and parse its stdout as JSON.

    Only stdout is parsed: Codex's own `--json` commands write their report there on success. Both
    streams are combined only for an error message, matching the PowerShell original's `2>&1` -- a
    failure before the JSON was ever written can land on either stream, and the combined text is what the
    message quotes.
    """
    try:
        result = run([*codex_command(codex_executable), *arguments], cwd=cwd, capture_output=True,
                     text=True, encoding='utf-8', errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SyncError(f"Codex plugin sync timed out after {timeout}s: {' '.join(arguments)}") from None
    except (RuntimeError, OSError) as error:
        raise SyncError(f"Codex plugin sync could not start: {' '.join(arguments)}: {error}") from None
    if result.returncode != 0:
        combined = (result.stdout or '') + (result.stderr or '')
        raise SyncError(f"Codex plugin sync failed: {' '.join(arguments)}: {combined.strip()}")
    try:
        parsed = json.loads(result.stdout)
    except ValueError:
        raise SyncError(
            f"Codex plugin sync returned invalid JSON: {' '.join(arguments)}: {result.stdout.strip()!r}"
        ) from None
    if not isinstance(parsed, dict):
        raise SyncError(
            f"Codex plugin sync returned a non-object JSON value: {' '.join(arguments)}: {result.stdout.strip()!r}"
        )
    return parsed


def invoke_codex_hook_trust(codex_executable, working_directory, helper_script, cwd=None, run=subprocess.run, out=print):
    """Run the hook-trust helper with the current interpreter, against a snapshot of itself."""
    try:
        result = run([sys.executable, '-I', '-B', str(helper_script), '--codex', str(codex_executable),
                     '--project', str(working_directory)], cwd=cwd, capture_output=True,
                    text=True, encoding='utf-8', errors='replace', timeout=PLUGIN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        raise SyncError(f'Codex hook trust timed out after {PLUGIN_TIMEOUT_SECONDS}s') from None
    except OSError as error:
        raise SyncError(f'Codex hook trust could not start: {error}') from None
    for line in (result.stdout or '').splitlines():
        out(line)
    if result.stderr:
        for line in result.stderr.splitlines():
            out(line)
    if result.returncode != 0:
        raise SyncError('Codex could not trust tj-agents hooks')


def enabled_git_plugins(entries):
    """The enabled, git-sourced pluginIds among <entries> -- skipping a null, non-dict, or pluginId-less
    entry rather than raising, same as the PowerShell original's Where-Object silently passed over one."""
    found = set()
    for plugin in entries:
        if not isinstance(plugin, dict):
            continue
        identity = plugin.get('pluginId')
        if not identity or not plugin.get('enabled'):
            continue
        if (plugin.get('marketplaceSource') or {}).get('sourceType') != 'git':
            continue
        found.add(identity)
    return found


def sync_codex_standards(codex_executable, working_directory, out=print, run=subprocess.run):
    """Materialize current selected Codex plugins and trust their verified hooks."""
    resolved = Path(working_directory).resolve()
    home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex').resolve()
    try:
        selection = codex_config_selection(codex_executable, resolved)
        selection['selection_reader'] = lambda: codex_config_selection(codex_executable, resolved)
        with rolling_plugins.preflight('codex', home, resolved, selection) as active:
            prepared = active.materialize_native(codex_executable)
            if prepared.selected_roots:
                apply_trust(codex_executable, resolved, verified_roots=prepared.selected_roots,
                            launch_args=rolling_plugins.hook_trust_arguments(prepared), environment=prepared.environment)
            active.acknowledge_binding()
        return [root.identity for root in prepared.selected_roots]
    except (rolling_plugins.RollingPluginError, SyncError) as error:
        raise SyncError(str(error)) from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex')
    parser.add_argument('--project', type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    try:
        codex = resolve_codex_for_sync(arguments.codex)
        sync_codex_standards(codex, arguments.project)
        return 0
    except SyncError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
