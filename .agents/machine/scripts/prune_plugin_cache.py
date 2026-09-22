r"""Reconcile the Claude plugin cache against the installed-plugin registry.

The registry is the truth. A cached version directory survives only when a live `installPath` names
it. Install and update already converge; removal never did, so every plugin rename left its
predecessor on disk permanently and nothing reconciled the two.

Unlike `skill_router.manifest_install_roots`, an unreadable registry is fatal here rather than a
fallback to walking the cache: "no live paths" must never be read as "everything is prunable".

Codex is deliberately out of scope; see the sibling TECH_DEBT.md for the condition that changes that.
"""

import argparse
import json
import os
import shutil
import stat
import sys
import time
from pathlib import Path

CACHE_DEPTH = 3
NOTICE_INTERVAL_SECONDS = 60 * 60
STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"

LIVE = "live"
RETAINED = "retained"
STALE = "stale"
ORPHAN = "orphan"

EXIT_OK = 0
EXIT_REGISTRY = 2
EXIT_REMOVAL = 3


class RegistryUnusable(Exception):
    """The registry could not establish which install paths are live."""


def claude_config_root(environ=None, home=None):
    values = os.environ if environ is None else environ
    configured = values.get("CLAUDE_CONFIG_DIR")
    if configured:
        return Path(configured)
    return (Path.home() if home is None else home) / ".claude"


def registry_path(config_root):
    return config_root / "plugins" / "installed_plugins.json"


def cache_root(config_root):
    return config_root / "plugins" / "cache"


def normalize(path):
    """Comparison key for an install path.

    The registry spells Windows paths with escaped backslashes and inconsistent case, so the same
    directory arrives spelled differently from JSON than from a directory walk.
    """
    try:
        resolved = Path(path).resolve()
    except (OSError, ValueError):
        resolved = Path(path)
    return os.path.normcase(str(resolved).rstrip("\\/"))


def live_install_paths(config_root):
    """Every install path the registry names, as normalized keys.

    Raises RegistryUnusable rather than returning an empty set, which would classify the entire
    cache as prunable.
    """
    path = registry_path(config_root)
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        raise RegistryUnusable(f"cannot read {path}: {error}") from error
    try:
        data = json.loads(raw)
    except ValueError as error:
        raise RegistryUnusable(f"{path} is not valid JSON: {error}") from error
    plugins = data.get("plugins") if isinstance(data, dict) else None
    if not isinstance(plugins, dict):
        raise RegistryUnusable(f"{path} has no plugins object")
    paths = set()
    for installs in plugins.values():
        if not isinstance(installs, list):
            continue
        for install in installs:
            if not isinstance(install, dict):
                continue
            value = install.get("installPath")
            if isinstance(value, str) and value.strip():
                paths.add(normalize(value))
    if not paths:
        raise RegistryUnusable(f"{path} names no install paths")
    return paths


def is_reparse_point(path):
    """A junction or symlink. Never recursed into - a delete would follow it out of the cache."""
    if path.is_symlink():
        return True
    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def cached_versions(root):
    """Every `<marketplace>/<plugin>/<version>` directory, sorted."""
    if not root.is_dir():
        return []
    found = []
    try:
        marketplaces = sorted(entry for entry in root.iterdir() if entry.is_dir())
    except OSError:
        return []
    for marketplace in marketplaces:
        if is_reparse_point(marketplace):
            continue
        try:
            plugins = sorted(entry for entry in marketplace.iterdir() if entry.is_dir())
        except OSError:
            continue
        for plugin in plugins:
            if is_reparse_point(plugin):
                continue
            try:
                found.extend(sorted(entry for entry in plugin.iterdir() if entry.is_dir()))
            except OSError:
                continue
    return found


def modified_at(path):
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def classify(versions, live, keep_previous=0):
    """Label every cached version directory. Returns [(path, state)] in scan order.

    A plugin with no live version is orphaned outright - the rename case, where nothing is coming
    back. Retention applies only to plugins that are still installed.
    """
    by_plugin = {}
    for version in versions:
        by_plugin.setdefault(version.parent, []).append(version)

    states = {}
    for entries in by_plugin.values():
        alive = [entry for entry in entries if normalize(entry) in live]
        for entry in alive:
            states[entry] = LIVE
        dead = [entry for entry in entries if entry not in states]
        if not alive:
            states.update((entry, ORPHAN) for entry in dead)
            continue
        # Directory names are commit shas, so "previous" can only come from mtime.
        dead.sort(key=modified_at, reverse=True)
        for index, entry in enumerate(dead):
            states[entry] = RETAINED if index < keep_previous else STALE
    return [(version, states[version]) for version in versions]


def directory_size(path):
    total = 0
    for current, directories, files in os.walk(path):
        directories[:] = [
            name for name in directories if not is_reparse_point(Path(current) / name)
        ]
        for name in files:
            try:
                total += (Path(current) / name).lstat().st_size
            except OSError:
                continue
    return total


def human_bytes(count):
    value = float(count)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def _force_writable(function, path, _excinfo):
    """Windows refuses to unlink a read-only file, and a cached git checkout is full of them."""
    os.chmod(path, stat.S_IWRITE)
    function(path)


def remove_directory(path):
    if is_reparse_point(path):
        path.unlink()
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_force_writable)
    else:
        shutil.rmtree(path, onerror=_force_writable)


def assert_within(root, target):
    """A removal target must be exactly `<cache>/<marketplace>/<plugin>/<version>`."""
    try:
        relative = target.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{target} is outside {root}") from error
    if len(relative.parts) != CACHE_DEPTH:
        raise ValueError(f"{target} is not a cached version directory")


def missing_install_paths(live, versions):
    return sorted(live - {normalize(version) for version in versions})


def state_directory(environ=None, home=None):
    values = os.environ if environ is None else environ
    configured = values.get(STATE_DIRECTORY_ENV)
    if configured:
        return Path(configured)
    return (Path.home() if home is None else home) / ".agents-state"


def notice_is_due(path, now, interval=NOTICE_INTERVAL_SECONDS):
    try:
        last = float(json.loads(path.read_text(encoding="utf-8")).get("last_notice", 0))
    except (OSError, ValueError, TypeError, AttributeError):
        return True
    return not 0 <= now - last < interval


def record_notice(path, now):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps({"last_notice": now}) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def reconcile(config_root, keep_previous=0):
    live = live_install_paths(config_root)
    root = cache_root(config_root)
    versions = cached_versions(root)
    return {
        "cache_root": root,
        "live": live,
        "entries": classify(versions, live, keep_previous),
        "missing": missing_install_paths(live, versions),
    }


def prunable(entries):
    return [path for path, state in entries if state in (STALE, ORPHAN)]


def render_report(result, apply_mode, removed, failures, stream):
    entries = result["entries"]
    targets = prunable(entries)
    counts = {}
    for _, state in entries:
        counts[state] = counts.get(state, 0) + 1

    print(f"cache root: {result['cache_root']}", file=stream)
    print(
        f"registry: {len(result['live'])} live install paths, "
        f"{len(entries)} cached version directories",
        file=stream,
    )
    for state in (LIVE, RETAINED, STALE, ORPHAN):
        if counts.get(state):
            print(f"  {state:<9} {counts[state]}", file=stream)

    for path in result["missing"]:
        print(f"warning: registry names a missing install path: {path}", file=stream)

    if not targets:
        print("nothing to prune", file=stream)
        return

    total = 0
    for path, state in entries:
        if state not in (STALE, ORPHAN):
            continue
        if path in failures:
            print(f"  FAILED    {path}  {failures[path]}", file=stream)
            continue
        size = removed[path] if path in removed else directory_size(path)
        total += size
        print(f"  {state:<9} {path}  ({human_bytes(size)})", file=stream)
    verb = "removed" if apply_mode else "would remove"
    print(
        f"{verb} {len(targets) - len(failures)} directories, {human_bytes(total)}",
        file=stream,
    )
    if failures:
        print(f"{len(failures)} removals failed", file=stream)
    elif not apply_mode:
        print(f"re-run with --apply to remove them: {Path(__file__).resolve()}", file=stream)


def run_notice(config_root, keep_previous, now, environ=None, home=None, stream=sys.stdout):
    """One line when the cache has drifted, silence otherwise. Never removes anything."""
    marker = state_directory(environ, home) / "plugin-cache-notice.json"
    if not notice_is_due(marker, now):
        return EXIT_OK
    try:
        result = reconcile(config_root, keep_previous)
    except RegistryUnusable:
        return EXIT_OK
    targets = prunable(result["entries"])
    if targets:
        print(
            f"plugin cache: {len(targets)} version directories the registry no longer names. "
            f"Review with: python -B \"{Path(__file__).resolve()}\"",
            file=stream,
        )
    try:
        record_notice(marker, now)
    except OSError:
        pass
    return EXIT_OK


def run_reconcile(config_root, keep_previous, apply_mode, stream=sys.stdout):
    try:
        result = reconcile(config_root, keep_previous)
    except RegistryUnusable as error:
        print(f"error: {error}", file=sys.stderr)
        print("refusing to prune: the registry must establish what is live", file=sys.stderr)
        return EXIT_REGISTRY

    removed = {}
    failures = {}
    if apply_mode:
        for path in prunable(result["entries"]):
            try:
                assert_within(result["cache_root"], path)
                size = directory_size(path)
                remove_directory(path)
            except (OSError, ValueError) as error:
                failures[path] = error
                continue
            removed[path] = size

    render_report(result, apply_mode, removed, failures, stream)
    return EXIT_REMOVAL if failures else EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(
        prog="prune_plugin_cache",
        description="Reconcile the Claude plugin cache against the installed-plugin registry.",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=None,
        help="Claude configuration directory. Defaults to CLAUDE_CONFIG_DIR or ~/.claude.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Remove the reported directories. Without it the run only reports.",
    )
    parser.add_argument(
        "--keep-previous",
        type=int,
        default=0,
        metavar="N",
        help="Keep N non-live versions of a still-installed plugin, newest first by mtime.",
    )
    parser.add_argument(
        "--notice",
        action="store_true",
        help="Throttled one-line session notice. Reports drift only; never removes.",
    )
    return parser


def main(argv=None):
    arguments = build_parser().parse_args(argv)
    if arguments.keep_previous < 0:
        print("error: --keep-previous must not be negative", file=sys.stderr)
        return EXIT_REGISTRY
    config_root = arguments.config_dir or claude_config_root()
    if arguments.notice:
        return run_notice(config_root, arguments.keep_previous, time.time())
    return run_reconcile(config_root, arguments.keep_previous, arguments.apply)


if __name__ == "__main__":
    sys.exit(main())
