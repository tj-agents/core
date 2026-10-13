#!/usr/bin/env python3
"""Refresh enabled Codex plugins from their registered marketplaces before a session loads them, and
trust any of tj-agents' own hook definitions among them.

A faithful Python port of codex_marketplace_sync.ps1. Exposes sync_codex_standards() for launch_codex.py
to call before opening a handoff tab, and for codex_terminal_launcher.py to call from a typed `codex` in a
terminal. Not runnable from a terminal in any other way.

Legacy preference migration requires Python 3.11 or newer for TOML parsing. Ordinary refreshes do not.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None

HERE = Path(__file__).resolve().parent

# codex_hook_trust.py's own `.ps1`-shim handling and claude_standards_sync.py's own harness-permissions
# convergence are reused rather than duplicated here. Both live beside this file in every layout it ships
# in (authored and both packaged copies), the same hop codex_hook_trust.py and agent_cli.py already rely on.
sys.path.insert(0, str(HERE))
from codex_hook_trust import command as codex_command, github_repository  # noqa: E402
from claude_standards_sync import (  # noqa: E402
    apply_harness_permissions,
    MARKETPLACE_TIMEOUT_SECONDS,
    PLUGIN_TIMEOUT_SECONDS,
)

CANONICAL_MARKETPLACE = 'tj-agents'
CANONICAL_MARKETPLACE_SOURCE = 'tj-agents/marketplace'
CANONICAL_MARKETPLACE_REPOSITORY = ('tj-agents', 'marketplace')
PLUGIN_ID = re.compile(r'(?P<name>[a-z][a-z0-9-]*)@(?P<marketplace>[a-z][a-z0-9-]*)\Z')
GITHUB_REMOTE = re.compile(
    r'(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)'
    r'[A-Za-z0-9-]+/[A-Za-z0-9_.-]+?(?:\.git)?/?\Z',
    re.IGNORECASE,
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


def plugin_identity(entry):
    identity = entry.get('pluginId') if isinstance(entry, dict) else None
    match = PLUGIN_ID.fullmatch(identity) if isinstance(identity, str) else None
    return (match['name'], match['marketplace']) if match else None


def inventory_records(inventory, key):
    records = inventory.get(key)
    if records is None:
        return []
    if not isinstance(records, list):
        raise SyncError(f'Codex plugin inventory has invalid {key} records')
    return [record for record in records if isinstance(record, dict)]


def marketplace_root(listing):
    marketplaces = listing.get('marketplaces')
    if not isinstance(marketplaces, list):
        raise SyncError('Codex marketplace listing has no marketplace records')
    matches = [record for record in marketplaces if isinstance(record, dict)
               and record.get('name') == CANONICAL_MARKETPLACE]
    if len(matches) != 1 or not isinstance(matches[0].get('root'), str) or not matches[0]['root']:
        raise SyncError('Codex did not register one usable tj-agents marketplace root')
    return Path(matches[0]['root'])


def invoke_git(arguments, cwd, run=subprocess.run):
    environment = os.environ.copy()
    environment['GIT_NO_REPLACE_OBJECTS'] = '1'
    try:
        result = run(['git', '--no-replace-objects', *arguments], cwd=cwd, capture_output=True, text=True,
                     encoding='utf-8', errors='replace', timeout=PLUGIN_TIMEOUT_SECONDS, env=environment)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SyncError(f'Cannot verify tj-agents marketplace provenance: {error}') from None
    if result.returncode != 0:
        detail = ((result.stdout or '') + (result.stderr or '')).strip()
        raise SyncError(f'Cannot verify tj-agents marketplace provenance: {detail}')
    return (result.stdout or '').strip()


def authenticated_catalog(root, git_run=subprocess.run):
    try:
        origin = invoke_git(['-C', str(root), 'remote', 'get-url', 'origin'], root, git_run)
        if not GITHUB_REMOTE.fullmatch(origin):
            raise SyncError(f'{root}: tj-agents marketplace origin must use an authenticated GitHub remote transport')
        if github_repository(origin) != CANONICAL_MARKETPLACE_REPOSITORY:
            raise SyncError(f'{root}: tj-agents marketplace origin is not {CANONICAL_MARKETPLACE_SOURCE}')
        if invoke_git(['-C', str(root), 'status', '--porcelain'], root, git_run):
            raise SyncError(f'{root}: tj-agents marketplace checkout has local changes')
        head = invoke_git(['-C', str(root), 'rev-parse', 'HEAD'], root, git_run)
        published = invoke_git(
            ['-C', str(root), 'ls-remote', 'origin', 'HEAD', 'refs/heads/*', 'refs/tags/*'], root, git_run,
        )
        if head not in {line.split()[0] for line in published.splitlines() if line.split()}:
            raise SyncError(f'{root}: tj-agents marketplace revision is not published by its origin')
        catalog = json.loads(invoke_git(['-C', str(root), 'show', f'{head}:catalog.json'], root, git_run))
    except (OSError, UnicodeError, ValueError) as error:
        raise SyncError(f'{root}: cannot read the tj-agents marketplace catalog: {error}') from None
    if catalog.get('name') != CANONICAL_MARKETPLACE or not isinstance(catalog.get('plugins'), list):
        raise SyncError(f'{root}: invalid tj-agents marketplace catalog')
    result = {}
    for record in catalog['plugins']:
        if not isinstance(record, dict):
            raise SyncError(f'{root}: invalid tj-agents marketplace catalog entry')
        name, repository = record.get('name'), record.get('repository')
        if not isinstance(name, str) or not isinstance(repository, str) or not PLUGIN_ID.fullmatch(f'{name}@x'):
            raise SyncError(f'{root}: invalid tj-agents marketplace catalog entry')
        if name in result:
            raise SyncError(f'{root}: duplicate tj-agents marketplace plugin {name}')
        result[name] = ('tj-agents', repository)
    return result


def canonical_catalog(codex_executable, resolved, run, git_run):
    listing = invoke_codex_sync_command(codex_executable, ['plugin', 'marketplace', 'list', '--json'],
                                        cwd=resolved, run=run, timeout=PLUGIN_TIMEOUT_SECONDS)
    try:
        root = marketplace_root(listing)
    except SyncError:
        added = invoke_codex_sync_command(
            codex_executable, ['plugin', 'marketplace', 'add', CANONICAL_MARKETPLACE_SOURCE, '--json'],
            cwd=resolved, run=run, timeout=MARKETPLACE_TIMEOUT_SECONDS,
        )
        if added.get('marketplaceName') != CANONICAL_MARKETPLACE:
            raise SyncError(f"Codex registered {added.get('marketplaceName')} while adding tj-agents marketplace")
        listing = invoke_codex_sync_command(codex_executable, ['plugin', 'marketplace', 'list', '--json'],
                                            cwd=resolved, run=run, timeout=PLUGIN_TIMEOUT_SECONDS)
        root = marketplace_root(listing)
    return authenticated_catalog(root, git_run)


def source_repository(entry):
    marketplace = entry.get('marketplaceSource') if isinstance(entry, dict) else None
    if not isinstance(marketplace, dict) or marketplace.get('sourceType') != 'git':
        return None
    return github_repository(marketplace.get('source'))


def canonical_records(inventory, catalog):
    records = {}
    for entry in (*inventory_records(inventory, 'installed'), *inventory_records(inventory, 'available')):
        parsed = plugin_identity(entry)
        if not parsed or parsed[1] != CANONICAL_MARKETPLACE or parsed[0] not in catalog:
            continue
        if source_repository(entry) != CANONICAL_MARKETPLACE_REPOSITORY:
            raise SyncError(f"Canonical plugin has unauthenticated marketplace source: {entry['pluginId']}")
        if entry.get('installed') is True or parsed[0] not in records:
            records[parsed[0]] = entry
    return records


def profile_root(config_root):
    if config_root:
        return Path(config_root).expanduser()
    configured = os.environ.get('CODEX_HOME')
    return Path(configured).expanduser() if configured else Path.home() / '.codex'


def toml_library():
    if tomllib is None:
        raise SyncError('Codex plugin migration requires Python 3.11 or newer for TOML preferences')
    return tomllib


def read_preference_config(path):
    if not path.is_file():
        return b'', {}
    try:
        raw = path.read_bytes()
        parsed = toml_library().loads(raw.decode('utf-8-sig'))
    except (OSError, UnicodeError, toml_library().TOMLDecodeError) as error:
        raise SyncError(f'Cannot parse Codex preference {path}: {error}') from None
    if not isinstance(parsed, dict):
        raise SyncError(f'Codex preference {path} must contain a TOML table')
    return raw, parsed


def preference_value(parsed, identity, path):
    plugins = parsed.get('plugins')
    if plugins is None:
        return None
    if not isinstance(plugins, dict):
        raise SyncError(f'Codex preference plugins must be a TOML table in {path}')
    plugin = plugins.get(identity)
    if plugin is None:
        return None
    if not isinstance(plugin, dict):
        raise SyncError(f'Codex preference for {identity} must be a TOML table in {path}')
    enabled = plugin.get('enabled')
    if enabled is None:
        return None
    if type(enabled) is not bool:
        raise SyncError(f'Codex preference enabled must be true or false for {identity} in {path}')
    return enabled


def plugin_preference(path, identity):
    _raw, parsed = read_preference_config(path)
    return preference_value(parsed, identity, path)


def project_preference_paths(working_directory, global_path):
    paths = []
    current = Path(working_directory).resolve()
    root = current
    ancestor = current
    while True:
        if (ancestor / '.git').exists():
            root = ancestor
            break
        parent = ancestor.parent
        if parent == ancestor:
            break
        ancestor = parent
    while True:
        candidate = current / '.codex' / 'config.toml'
        if candidate != global_path and candidate.is_file():
            paths.append(candidate)
        if current == root:
            return paths
        current = current.parent


class PreferenceLock:
    def __init__(self, path):
        self.path = path
        self.handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + PLUGIN_TIMEOUT_SECONDS
        while True:
            handle = None
            try:
                handle = open(self.path, 'a+b')
                handle.seek(0)
                if not handle.read(1):
                    handle.seek(0)
                    handle.write(b'0')
                    handle.flush()
                handle.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.handle = handle
                return self
            except OSError:
                if handle is not None:
                    handle.close()
                if time.monotonic() >= deadline:
                    raise SyncError(f'Codex migration timed out waiting for preference lock: {self.path}') from None
                time.sleep(0.05)

    def __exit__(self, exception_type, exception, traceback):
        if self.handle is None:
            return
        self.handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        self.handle.close()


def preference_lock(config_root):
    return PreferenceLock(profile_root(config_root) / '.codex-marketplace-sync.lock')


def native_preference_text(text, identity, enabled):
    lines = text.splitlines(keepends=True)
    header = f'[plugins."{identity}"]'
    table = next((index for index, line in enumerate(lines)
                  if line.rstrip('\r\n').partition('#')[0].strip() == header), None)
    if table is None:
        raise SyncError(f'Codex did not create the canonical preference table for {identity}')
    for index in range(table + 1, len(lines)):
        line = lines[index]
        body = line.rstrip('\r\n')
        if body.lstrip().startswith('['):
            break
        code, marker, comment = body.partition('#')
        if code.strip() != 'enabled = true':
            continue
        ending = line[len(body):]
        leading = code[:len(code) - len(code.lstrip())]
        trailing = code[len(code.rstrip()):]
        lines[index] = f'{leading}enabled = {str(enabled).lower()}{trailing}{marker}{comment}{ending}'
        return ''.join(lines)
    raise SyncError(f'Codex did not create an enabled preference for {identity}')


def update_native_preference(path, identity, enabled):
    before, parsed = read_preference_config(path)
    current = preference_value(parsed, identity, path)
    if current == enabled:
        return
    if current is None:
        raise SyncError(f'Codex did not create a canonical preference for {identity} in {path}')
    try:
        text = before.decode('utf-8-sig')
        updated = native_preference_text(text, identity, enabled).encode('utf-8')
        after = toml_library().loads(updated.decode('utf-8-sig'))
    except (UnicodeError, toml_library().TOMLDecodeError) as error:
        raise SyncError(f'Cannot preserve Codex preference {path}: {error}') from None
    expected = copy.deepcopy(parsed)
    expected['plugins'][identity]['enabled'] = enabled
    if after != expected:
        raise SyncError(f'Codex preference edit would change unrelated content in {path}')
    try:
        if (path.read_bytes() if path.is_file() else b'') != before:
            raise SyncError(f'Codex preference changed while preparing migration: {path}')
        descriptor, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=str(path.parent))
        try:
            with os.fdopen(descriptor, 'wb') as handle:
                handle.write(updated)
                handle.flush()
                os.fsync(handle.fileno())
            if (path.read_bytes() if path.is_file() else b'') != before:
                raise SyncError(f'Codex preference changed while applying migration: {path}')
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    except OSError as error:
        raise SyncError(f'Cannot update Codex preference {path}: {error}') from None


def config_snapshot(path):
    try:
        return path.is_file(), path.read_bytes() if path.is_file() else b''
    except OSError as error:
        raise SyncError(f'Cannot read Codex preference {path}: {error}') from None


def restore_preference_config(path, original, expected):
    current = config_snapshot(path)
    if current == original:
        return
    if current != expected:
        raise SyncError(f'Codex preference changed while recovering failed migration: {path}')
    existed, contents = original
    try:
        if existed:
            descriptor, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=str(path.parent))
            try:
                with os.fdopen(descriptor, 'wb') as handle:
                    handle.write(contents)
                    handle.flush()
                    os.fsync(handle.fileno())
                if config_snapshot(path) != expected:
                    raise SyncError(f'Codex preference changed while recovering failed migration: {path}')
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
        else:
            if config_snapshot(path) != expected:
                raise SyncError(f'Codex preference changed while recovering failed migration: {path}')
            path.unlink()
    except OSError as error:
        raise SyncError(f'Cannot restore Codex preference {path}: {error}') from None


def migration_preference(legacy, canonical, working_directory, config_root):
    toml_library()
    global_path = profile_root(config_root) / 'config.toml'
    for project_path in project_preference_paths(working_directory, global_path):
        if plugin_preference(project_path, legacy) is not None:
            raise SyncError(
                f'Codex migration cannot rewrite scoped project preference {project_path} for {legacy}; '
                f'update it to {canonical} before retrying'
            )
    canonical_choice = plugin_preference(global_path, canonical)
    legacy_choice = plugin_preference(global_path, legacy)
    return global_path, canonical_choice if canonical_choice is not None else legacy_choice


def migration_candidates(inventory, catalog, out):
    result = []
    for entry in inventory_records(inventory, 'installed'):
        parsed = plugin_identity(entry)
        repository = source_repository(entry)
        if (
            not parsed or parsed[1] == CANONICAL_MARKETPLACE or repository is None
            or repository[0] != 'tj-agents'
        ):
            continue
        if parsed[0] not in catalog:
            out(
                f'Codex migration left {entry["pluginId"]} unresolved: shared catalog has no matching '
                'plugin with shipped skill-coverage evidence'
            )
            continue
        if repository != catalog[parsed[0]]:
            continue
        if entry.get('installed') is not True:
            continue
        if entry.get('scope') not in (None, 'user', 'global') or entry.get('projectPath') or entry.get('project'):
            raise SyncError(f"Codex migration cannot remove scoped legacy plugin {entry['pluginId']}")
        result.append(entry)
    return result


def migrate_plugin(codex_executable, legacy, canonical, inventory, working_directory, config_root, run):
    preference = migration_preference(legacy, canonical, working_directory, config_root)
    path, enabled = preference
    original = config_snapshot(path)
    expected = None
    try:
        installed = invoke_codex_sync_command(codex_executable, ['plugin', 'add', canonical, '--json'],
                                               cwd=working_directory, run=run, timeout=PLUGIN_TIMEOUT_SECONDS)
        expected = config_snapshot(path)
        if installed.get('pluginId') != canonical:
            raise SyncError(f"Codex installed {installed.get('pluginId')} while migrating {legacy} to {canonical}")
        verified = invoke_codex_sync_command(codex_executable, ['plugin', 'list', '--available', '--json'],
                                             cwd=working_directory, run=run, timeout=PLUGIN_TIMEOUT_SECONDS)
        replacement = next((entry for entry in inventory_records(verified, 'installed')
                            if entry.get('pluginId') == canonical and entry.get('installed') is True), None)
        if replacement is None or source_repository(replacement) != CANONICAL_MARKETPLACE_REPOSITORY:
            raise SyncError(f'Codex did not verify replacement payload for {legacy} as {canonical}')
        update_native_preference(path, canonical, bool(inventory.get('enabled')) if enabled is None else enabled)
        expected = config_snapshot(path)
        removed = invoke_codex_sync_command(codex_executable, ['plugin', 'remove', legacy, '--json'],
                                            cwd=working_directory, run=run, timeout=PLUGIN_TIMEOUT_SECONDS)
        if removed.get('pluginId') not in (None, legacy):
            raise SyncError(f"Codex removed {removed.get('pluginId')} while migrating {legacy}")
        final = invoke_codex_sync_command(codex_executable, ['plugin', 'list', '--available', '--json'],
                                          cwd=working_directory, run=run, timeout=PLUGIN_TIMEOUT_SECONDS)
        if any(entry.get('pluginId') == legacy and entry.get('installed') is True
               for entry in inventory_records(final, 'installed')):
            raise SyncError(f'Codex retained legacy plugin cache for {legacy}')
        return final
    except SyncError:
        if expected is not None:
            restore_preference_config(path, original, expected)
        raise


def sync_codex_standards(codex_executable, working_directory, out=print, run=subprocess.run,
                          git_run=subprocess.run, config_root=None):
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

            canonical_catalog(codex_executable, resolved, run, git_run)

            upgrade = invoke_codex_sync_command(codex_executable, ['plugin', 'marketplace', 'upgrade', '--json'],
                                                 cwd=resolved, run=run, timeout=MARKETPLACE_TIMEOUT_SECONDS)
            errors = upgrade.get('errors') or []
            if errors:
                raise SyncError(f'Codex marketplace upgrade failed: {json.dumps(errors)}')

            catalog = canonical_catalog(codex_executable, resolved, run, git_run)

            with preference_lock(config_root):
                inventory = invoke_codex_sync_command(codex_executable, ['plugin', 'list', '--available', '--json'],
                                                       cwd=resolved, run=run, timeout=PLUGIN_TIMEOUT_SECONDS)
                canonical_records(inventory, catalog)
                for legacy in migration_candidates(inventory, catalog, out):
                    name, _marketplace = plugin_identity(legacy)
                    inventory = migrate_plugin(
                        codex_executable, legacy['pluginId'], f'{name}@{CANONICAL_MARKETPLACE}', legacy,
                        resolved, config_root, run,
                    )
                canonical_records(inventory, catalog)
                installed = inventory_records(inventory, 'installed')
                available = inventory_records(inventory, 'available')
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
        apply_harness_permissions(resolved, run=run)


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
