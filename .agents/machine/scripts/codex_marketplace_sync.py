#!/usr/bin/env python3
"""Refresh enabled Codex plugins from their registered marketplaces before a session loads them, and
trust any of tj-agents' own hook definitions among them.

A faithful Python port of codex_marketplace_sync.ps1. Exposes sync_codex_standards() for launch_codex.py
to call before opening a handoff tab, and a CLI (`--codex <exe> --project <dir>`) for codex-profile.ps1 to
call from a typed `codex` in a terminal. Not runnable from a terminal in any other way.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent

# codex_hook_trust.py's own `.ps1`-shim handling and claude_standards_sync.py's own harness-permissions
# convergence are reused rather than duplicated here. Both live beside this file in every layout it ships
# in (authored and both packaged copies), the same hop codex_hook_trust.py and agent_cli.py already rely on.
sys.path.insert(0, str(HERE))
from codex_hook_trust import command as codex_command  # noqa: E402
from claude_standards_sync import (  # noqa: E402
    apply_harness_permissions,
    MARKETPLACE_TIMEOUT_SECONDS,
    PLUGIN_TIMEOUT_SECONDS,
)


class SyncError(Exception):
    """A Codex standards refresh step failed; the message is the whole report."""


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
    if Path(executable).suffix.casefold() in ('.ps1', '.cmd'):
        return True
    try:
        with open(executable, 'rb') as handle:
            return handle.read(2) == b'#!'
    except OSError:
        # Matches agent_cli._is_script's own fail-safe direction: an unreadable path cannot be confirmed
        # native, so it is re-resolved rather than trusted as-is.
        return True


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
        result = run([sys.executable, '-B', str(helper_script), '--codex', str(codex_executable),
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
    """Refresh every enabled git-sourced Codex plugin and trust tj-agents' own hooks among them.

    Returns the sorted, de-duplicated list of plugin identities refreshed. Mirrors
    codex_marketplace_sync.ps1's Sync-CodexStandards: upgrade the registered marketplaces, enumerate every
    enabled git-sourced plugin (installed or merely available), reinstall each one to pick up the upgrade,
    then trust any tj-agents hooks among them -- skipped only when there was nothing enabled to check at
    all. The hook trust helper is copied to a private temporary file before any of this runs, because the
    marketplace upgrade this triggers can replace the installed copy out from under a later read of it.
    Converges this machine's declared harness permissions last, always, even when an earlier step raised --
    the ps1 original ran it from a `finally`, after the same cleanup this function's own `with` block
    performs on the way out.
    """
    resolved = Path(working_directory).resolve()
    try:
        helper = HERE / 'codex_hook_trust.py'
        if not helper.is_file():
            raise SyncError(f'Codex hook trust helper missing: {helper}')

        with tempfile.TemporaryDirectory(prefix='codex-hook-trust-') as scratch:
            snapshot = Path(scratch) / 'codex_hook_trust.py'
            shutil.copyfile(helper, snapshot)

            upgrade = invoke_codex_sync_command(codex_executable, ['plugin', 'marketplace', 'upgrade', '--json'],
                                                 cwd=resolved, run=run, timeout=MARKETPLACE_TIMEOUT_SECONDS)
            errors = upgrade.get('errors') or []
            if errors:
                raise SyncError(f'Codex marketplace upgrade failed: {json.dumps(errors)}')

            inventory = invoke_codex_sync_command(codex_executable, ['plugin', 'list', '--available', '--json'],
                                                   cwd=resolved, run=run, timeout=PLUGIN_TIMEOUT_SECONDS)
            installed = inventory.get('installed') or []
            available = inventory.get('available') or []
            selected = sorted(enabled_git_plugins((*installed, *available)))
            for identity in selected:
                installed_result = invoke_codex_sync_command(codex_executable, ['plugin', 'add', identity, '--json'],
                                                               cwd=resolved, run=run, timeout=PLUGIN_TIMEOUT_SECONDS)
                if installed_result.get('pluginId') != identity:
                    raise SyncError(f"Codex installed {installed_result.get('pluginId')} while refreshing {identity}")

            if selected or any(isinstance(plugin, dict) and plugin.get('enabled') for plugin in installed):
                invoke_codex_hook_trust(codex_executable, resolved, snapshot, cwd=resolved, run=run, out=out)

            return selected
    finally:
        apply_harness_permissions(run=run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex')
    parser.add_argument('--project', type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    try:
        codex = arguments.codex
        if not codex or is_codex_shim(codex):
            agent_cli = _load_agent_cli()
            try:
                codex, _version = agent_cli.resolve_codex_executable()
            except agent_cli.LaunchError as error:
                raise SyncError(str(error)) from None
        sync_codex_standards(codex, arguments.project)
        return 0
    except SyncError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
