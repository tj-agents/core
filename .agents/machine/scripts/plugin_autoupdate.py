#!/usr/bin/env python3
"""Keep this machine's agent plugins current and its merged worktrees removed (Python 3.11+).

Codex marketplaces refresh only when their source revision changed. The worktree sweep runs from the
installed engineering package, so it always matches the current standards.
"""

from __future__ import annotations

import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

GIT_TIMEOUT_SECONDS = 30
SWEEP_TIMEOUT_SECONDS = 1800
LOCK_STALE_SECONDS = 3600
SCRIPT_NAME = "plugin_autoupdate.py"
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
CLI_TIMEOUT_SECONDS = 60
STILL_ACTIVE = 259
FAILURE_BACKOFF_SECONDS = 24 * 60 * 60
RETIRED = "retired"


def state_directory() -> Path:
    return Path(os.environ.get("AGENT_STATE_DIRECTORY") or Path.home() / ".agents-state")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path: Path, value: dict) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def is_pinned(ref: object) -> bool:
    return isinstance(ref, str) and len(ref) == 40 and all(character in "0123456789abcdefABCDEF"
                                                            for character in ref)


def load_toml(path: Path) -> dict:
    import tomllib

    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def git_marketplace(source: object) -> dict | None:
    if (not isinstance(source, dict) or source.get("source_type") != "git"
            or not isinstance(source.get("source"), str) or not source["source"]):
        return None
    ref = source.get("ref")
    return {"source": source["source"], "ref": ref if isinstance(ref, str) and ref else None}


def project_directories(config: dict, temporary: Path | None = None) -> list[Path]:
    projects = config.get("projects", {})
    if not isinstance(projects, dict):
        return []
    temporary = (temporary or Path(tempfile.gettempdir())).resolve()
    return sorted({Path(path).resolve() for path, settings in projects.items()
                   if isinstance(settings, dict) and settings.get("trust_level") == "trusted"
                   and (Path(path) / ".codex/config.toml").is_file()
                   and not Path(path).resolve().is_relative_to(temporary)})


def declarations(config: dict) -> list[tuple[Path, dict]]:
    found = [(Path.home(), config)]
    user_file = (codex_home() / "config.toml").resolve()
    for project in project_directories(config):
        path = project / ".codex" / "config.toml"
        if path.resolve() != user_file:
            found.append((project, load_toml(path)))
    return found


def section(config: dict, name: str) -> dict:
    value = config.get(name)
    return value if isinstance(value, dict) else {}


def declared_targets(config: dict) -> tuple[dict[str, dict], list[str]]:
    user = section(config, "marketplaces")
    candidates: dict[str, dict[tuple, dict]] = {}
    for rank, (directory, declared) in enumerate(declarations(config)):
        marketplaces = section(declared, "marketplaces")
        for identity, settings in sorted(section(declared, "plugins").items()):
            if not isinstance(settings, dict) or settings.get("enabled") is not True or "@" not in identity:
                continue
            name = identity.rsplit("@", 1)[1]
            source = git_marketplace(marketplaces[name] if name in marketplaces else user.get(name))
            if source is None:
                continue
            option = candidates.setdefault(name, {}).setdefault(
                (source["source"], source["ref"]), {**source, "project": directory, "rank": rank, "plugins": set()})
            option["plugins"].add(identity)
    targets, ignored = {}, []
    for name, options in sorted(candidates.items()):
        chosen = min(options.values(), key=lambda option: (option["rank"] > 0, is_pinned(option["ref"]),
                                                            option["rank"]))
        targets[name] = {"source": chosen["source"], "ref": chosen["ref"], "project": chosen["project"],
                         "plugins": sorted(chosen["plugins"])}
        ignored.extend(f"{name} at {option['ref'] or 'HEAD'} declared by {option['project']}"
                       for option in options.values() if option is not chosen)
    return targets, ignored


def marketplace_manifest(name: str) -> dict:
    root = codex_home() / ".tmp" / "marketplaces" / name
    for relative in (Path(".agents", "plugins", "marketplace.json"), Path(".claude-plugin", "marketplace.json")):
        manifest = read_json(root / relative)
        if manifest:
            return manifest
    return {}


def inspect_installation(name: str, target: dict) -> None:
    cache = codex_home() / "plugins" / "cache" / name
    selected = {identity.rsplit("@", 1)[0] for identity in target["plugins"]}
    target["missing"] = [identity for identity in target["plugins"]
                         if not (cache / identity.rsplit("@", 1)[0]).is_dir()]
    publishers = {}
    entries = marketplace_manifest(name).get("plugins")
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict) or entry.get("name") not in selected:
            continue
        source = entry.get("source")
        if isinstance(source, dict) and source.get("source") == "git-subdir" and isinstance(source.get("url"), str):
            ref = source.get("sha") or source.get("ref") or "HEAD"
            if isinstance(ref, str):
                publishers[(source["url"], ref)] = {"source": source["url"], "ref": ref}
    target["publishers"] = [publishers[key] for key in sorted(publishers)]


def process_alive(pid: object) -> bool:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def codex_session_running(alive=process_alive) -> bool:
    database = state_directory() / "sessions.db"
    if not database.exists():
        return False
    try:
        connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True, timeout=5)
        try:
            rows = connection.execute("SELECT profile, pid FROM sessions WHERE ended_at IS NULL").fetchall()
        finally:
            connection.close()
    except sqlite3.Error:
        return True
    home = os.path.normcase(str(codex_home().resolve()))
    return any(isinstance(profile, str) and os.path.normcase(str(Path(profile).resolve())) == home and alive(pid)
               for profile, pid in rows)


def remote_revision(source: str, ref: object = None) -> str | None:
    reference = ref if isinstance(ref, str) and ref else "HEAD"
    if is_pinned(reference):
        return reference.lower()
    try:
        result = subprocess.run(["git", "ls-remote", source, reference], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=GIT_TIMEOUT_SECONDS, check=False,
                                creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    for line in result.stdout.splitlines():
        revision = line.split("\t", 1)[0].strip()
        if len(revision) == 40:
            return revision
    return None


def run_cli(command: list[str], *, cwd: Path) -> bool | str:
    try:
        result = subprocess.run(command, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=CLI_TIMEOUT_SECONDS, check=False,
                                creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode and "was not found in marketplace" in (result.stderr + result.stdout):
        return RETIRED
    return result.returncode == 0


def refresh_codex(executable: str, targets: dict[str, dict], recorded: dict, revision=remote_revision,
                  run=run_cli, now: float | None = None, busy=codex_session_running) -> dict[str, str]:
    now = time.time() if now is None else now
    outcomes: dict[str, str] = {}
    references = sorted({(source["source"], source.get("ref") or "HEAD")
                         for target in targets.values() for source in [target, *target.get("publishers", [])]})
    with ThreadPoolExecutor(max_workers=max(1, min(8, len(references)))) as pool:
        heads = dict(zip(references, pool.map(lambda source: revision(*source), references)))
    running = None
    for marketplace in sorted(targets):
        target = targets[marketplace]
        key = "codex:" + marketplace
        published = [heads[(source["source"], source.get("ref") or "HEAD")]
                     for source in [target, *target.get("publishers", [])]]
        if published[0] is None:
            outcomes[marketplace] = "unreachable"
            continue
        head = (hashlib.sha256(json.dumps(published).encode("utf-8")).hexdigest()
                if len(published) > 1 else published[0])
        missing = set(target.get("missing", [])) - set(recorded.get("retired:" + key, []))
        if None not in published and recorded.get(key) == head and not missing:
            outcomes[marketplace] = "current"
            continue
        failed_at = recorded.get("failed:" + key)
        if isinstance(failed_at, (int, float)) and now - failed_at < FAILURE_BACKOFF_SECONDS:
            outcomes[marketplace] = "failed recently; retried after 24 hours"
            continue
        running = busy() if running is None else running
        if running:
            outcomes[marketplace] = "deferred while a Codex session is running"
            continue
        refreshed = run([executable, "plugin", "marketplace", "upgrade", marketplace],
                        cwd=target["project"]) is True
        retired = []
        for plugin in target["plugins"] if refreshed else []:
            added = run([executable, "plugin", "add", plugin], cwd=target["project"])
            if added == RETIRED:
                retired.append(plugin)
            elif added is not True:
                refreshed = False
                break
        if retired:
            recorded["retired:" + key] = sorted(retired)
        retired = f" (no longer published, not installed: {', '.join(retired)})" if retired else ""
        if refreshed:
            if None not in published:
                recorded[key] = head
            recorded.pop("failed:" + key, None)
            outcomes[marketplace] = "updated" + retired
        else:
            recorded["failed:" + key] = now
            outcomes[marketplace] = "failed" + retired
    return outcomes


def enabled_identities(config: dict) -> set[str]:
    return {identity for identity, settings in section(config, "plugins").items()
            if isinstance(settings, dict) and settings.get("enabled") is True}


def remove_user_plugins(path: Path, identities: set[str]) -> None:
    if not path.is_file():
        return
    original = path.read_text(encoding="utf-8")
    headers = {f"[plugins.{json.dumps(identity)}]" for identity in identities}
    kept, skipping = [], False
    for line in original.splitlines(keepends=True):
        if line.lstrip().startswith("["):
            skipping = line.strip() in headers
        if not skipping:
            kept.append(line)
    text = re.sub(r"\n{3,}", "\n\n", "".join(kept))
    if text != original:
        write_text(path, text)


def refresh_declared(executable: str, config: dict, recorded: dict, previous: list[str] = (), **options) -> dict:
    targets, ignored = declared_targets(config)
    for name, target in targets.items():
        inspect_installation(name, target)
    declared = set().union(*(enabled_identities(layer) for _, layer in declarations(config)[1:]))
    project_only = declared - (enabled_identities(config) - set(previous))
    outcomes = refresh_codex(executable, targets, recorded, **options)
    remove_user_plugins(codex_home() / "config.toml", project_only)
    kept = {prefix + "codex:" + name for name in targets for prefix in ("", "retired:", "failed:")}
    for key in [key for key in recorded if key not in kept]:
        del recorded[key]
    return {"marketplaces": outcomes, "ignored": ignored, "project_only": sorted(project_only)}


def load_codex_config() -> dict:
    return load_toml(codex_home() / "config.toml")


def installed_plugin_roots(plugin: str, claude_config: Path, codex_config: dict) -> list[Path]:
    roots = []
    prefix = plugin + "@"
    settings = read_json(claude_config / "settings.json").get("enabledPlugins")
    installed = read_json(claude_config / "plugins" / "installed_plugins.json").get("plugins")
    if isinstance(settings, dict) and isinstance(installed, dict):
        for identity, on in settings.items():
            entries = installed.get(identity)
            if on is True and identity.startswith(prefix) and isinstance(entries, list):
                roots.extend(Path(entry["installPath"]) for entry in entries
                             if isinstance(entry, dict) and isinstance(entry.get("installPath"), str))
    plugins = codex_config.get("plugins")
    if isinstance(plugins, dict):
        for identity, settings in plugins.items():
            if identity.startswith(prefix) and isinstance(settings, dict) and settings.get("enabled") is True:
                roots.append(codex_home() / "plugins" / "cache" / identity.split("@", 1)[1] / plugin / "local")
    return roots


def newest_existing(paths: list[Path]) -> Path | None:
    existing = [path for path in paths if path.is_file()]
    return max(existing, key=lambda path: path.stat().st_mtime) if existing else None


def console_python() -> str:
    executable = Path(sys.executable)
    console = executable.with_name("python.exe")
    return str(console) if executable.name.lower() == "pythonw.exe" and console.is_file() else sys.executable


def sweep_script(codex_config: dict) -> Path | None:
    relative = Path(".agents", "engineering", "workflow", "merge", "scripts", "worktree_sweep.py")
    return newest_existing([root / relative for root in installed_plugin_roots("engineering", claude_home(),
                                                                                codex_config)])


def sweep_worktrees(codex_config: dict) -> str:
    script = sweep_script(codex_config)
    if script is None:
        return "engineering package not installed"
    try:
        result = subprocess.run([console_python(), "-B", str(script)], stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=SWEEP_TIMEOUT_SECONDS, check=False, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"failed: {error}"
    return "ran" if result.returncode == 0 else f"failed with exit code {result.returncode}"


def packaged_copies(codex_config: dict) -> list[Path]:
    relative = Path("resources", "machine", "scripts", SCRIPT_NAME)
    return [root / relative for root in installed_plugin_roots("machine", claude_home(), codex_config)
            if (root / relative).is_file()]


def self_update(current: Path, codex_config: dict) -> bool:
    candidates = [path for path in packaged_copies(codex_config) if path.resolve() != current.resolve()]
    if not candidates:
        return False
    newest = max(candidates, key=lambda path: path.stat().st_mtime)
    try:
        if newest.read_bytes() == current.read_bytes():
            return False
        shutil.copyfile(newest, current.with_name(current.name + ".next"))
        os.replace(current.with_name(current.name + ".next"), current)
    except OSError:
        return False
    return True


def acquire_lock(path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        if time.time() - path.stat().st_mtime > LOCK_STALE_SECONDS:
            path.unlink(missing_ok=True)
    except OSError:
        pass
    try:
        os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
    except FileExistsError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print("plugin_autoupdate requires Python 3.11 or newer", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-self-update", action="store_true")
    parser.add_argument("--no-sweep", action="store_true")
    arguments = parser.parse_args(argv)
    directory = state_directory()
    lock = directory / "plugin-autoupdate.lock"
    if not acquire_lock(lock):
        return 0
    try:
        state_file = directory / "plugin-autoupdate.json"
        state = read_json(state_file)
        recorded = state.get("revisions") if isinstance(state.get("revisions"), dict) else {}
        previous = state.get("project_only") if isinstance(state.get("project_only"), list) else []
        config = load_codex_config()
        executable = shutil.which("codex")
        outcomes = refresh_declared(executable, config, recorded, previous) if executable else {}
        sweep = "skipped" if arguments.no_sweep else sweep_worktrees(config)
        write_json(state_file, {"revisions": recorded, "project_only": outcomes.get("project_only", previous),
                                "last_run": time.time(), "outcomes": outcomes, "worktree_sweep": sweep})
        if not arguments.no_self_update:
            self_update(Path(__file__), load_codex_config())
    finally:
        lock.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
