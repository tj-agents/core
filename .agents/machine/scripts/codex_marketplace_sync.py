#!/usr/bin/env python3
"""Refresh enabled Codex plugins from their registered marketplaces before a session loads them, and
trust any of tj-agents' own hook definitions among them.

A faithful Python port of codex_marketplace_sync.ps1. Exposes sync_codex_standards() for launch_codex.py
to call before opening a handoff tab, and a CLI (`--codex <exe> --project <dir>`) for codex-profile.ps1 to
call from a typed `codex` in a terminal. Not runnable from a terminal in any other way.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


class SyncError(Exception):
    """A Codex standards refresh step failed; the message is the whole report."""


def codex_command(executable):
    """The argv that actually runs <executable>, same rule codex_hook_trust.py already applies: a `.ps1`
    shim needs PowerShell to run it directly, since Windows cannot execute a PowerShell script as if it
    were a program in its own right.
    """
    if Path(executable).suffix.casefold() == '.ps1':
        shell = shutil.which('pwsh') or shutil.which('powershell.exe')
        if not shell:
            raise SyncError('PowerShell is required to run the Codex shim')
        return [shell, '-NoProfile', '-File', str(executable)]
    return [str(executable)]


def invoke_codex_sync_command(codex_executable, arguments, cwd=None, run=subprocess.run):
    """Run one `codex <arguments>` call and parse its combined stdout+stderr as JSON.

    Both streams are combined before parsing, matching the PowerShell original's `2>&1`: Codex's own
    `--json` commands write their report to stdout on success, but a failure before that point can land
    on either stream, and the combined text is what a caller's error message quotes.
    """
    result = run([*codex_command(codex_executable), *arguments], cwd=cwd, capture_output=True,
                 text=True, encoding='utf-8', errors='replace')
    combined = (result.stdout or '') + (result.stderr or '')
    if result.returncode != 0:
        raise SyncError(f"Codex plugin sync failed: {' '.join(arguments)}: {combined.strip()}")
    try:
        return json.loads(combined)
    except ValueError:
        raise SyncError(f"Codex plugin sync returned invalid JSON: {' '.join(arguments)}") from None


def invoke_codex_hook_trust(codex_executable, working_directory, helper_script, cwd=None, run=subprocess.run, out=print):
    """Run the hook-trust helper with the current interpreter, against a snapshot of itself."""
    result = run([sys.executable, '-B', str(helper_script), '--codex', str(codex_executable),
                 '--project', str(working_directory)], cwd=cwd, capture_output=True,
                text=True, encoding='utf-8', errors='replace')
    for line in (result.stdout or '').splitlines():
        out(line)
    if result.returncode != 0:
        raise SyncError('Codex could not trust tj-agents hooks')


def sync_codex_standards(codex_executable, working_directory, out=print, run=subprocess.run):
    """Refresh every enabled git-sourced Codex plugin and trust tj-agents' own hooks among them.

    Returns the sorted, de-duplicated list of plugin identities refreshed. Mirrors
    codex_marketplace_sync.ps1's Sync-CodexStandards: upgrade the registered marketplaces, enumerate every
    enabled git-sourced plugin (installed or merely available), reinstall each one to pick up the upgrade,
    then trust any tj-agents hooks among them -- skipped only when there was nothing enabled to check at
    all. The hook trust helper is copied to a private temporary file before any of this runs, because the
    marketplace upgrade this triggers can replace the installed copy out from under a later read of it.
    """
    resolved = Path(working_directory).resolve()
    helper = HERE / 'codex_hook_trust.py'
    if not helper.is_file():
        raise SyncError(f'Codex hook trust helper missing: {helper}')

    with tempfile.TemporaryDirectory(prefix='codex-hook-trust-') as scratch:
        snapshot = Path(scratch) / 'codex_hook_trust.py'
        shutil.copyfile(helper, snapshot)

        upgrade = invoke_codex_sync_command(codex_executable, ['plugin', 'marketplace', 'upgrade', '--json'],
                                             cwd=resolved, run=run)
        errors = upgrade.get('errors') or []
        if errors:
            raise SyncError(f'Codex marketplace upgrade failed: {json.dumps(errors)}')

        inventory = invoke_codex_sync_command(codex_executable, ['plugin', 'list', '--available', '--json'],
                                               cwd=resolved, run=run)
        installed = inventory.get('installed') or []
        available = inventory.get('available') or []
        selected = sorted({
            plugin['pluginId'] for plugin in (*installed, *available)
            if plugin and plugin.get('enabled') and (plugin.get('marketplaceSource') or {}).get('sourceType') == 'git'
        })
        for identity in selected:
            installed_result = invoke_codex_sync_command(codex_executable, ['plugin', 'add', identity, '--json'],
                                                           cwd=resolved, run=run)
            if installed_result.get('pluginId') != identity:
                raise SyncError(f"Codex installed {installed_result.get('pluginId')} while refreshing {identity}")

        if selected or any(plugin.get('enabled') for plugin in installed):
            invoke_codex_hook_trust(codex_executable, resolved, snapshot, cwd=resolved, run=run, out=out)

        return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex', required=True)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    try:
        sync_codex_standards(arguments.codex, arguments.project)
        return 0
    except SyncError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
