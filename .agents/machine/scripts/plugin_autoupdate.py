#!/usr/bin/env python3
"""Keep this machine's agent plugins current and its merged worktrees removed (Python 3.11+).

Codex marketplaces refresh only when their source revision changed. The worktree sweep runs from the
installed engineering package, so it always matches the current standards.
"""

from __future__ import annotations

import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor
import queue
import threading
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

GIT_TIMEOUT_SECONDS = 30
CLI_TIMEOUT_SECONDS = 300
SWEEP_TIMEOUT_SECONDS = 1800
LOCK_STALE_SECONDS = 3600
SCRIPT_NAME = "plugin_autoupdate.py"


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


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def codex_targets(config: dict) -> dict[str, dict]:
    marketplaces = config.get("marketplaces")
    plugins = config.get("plugins")
    if not isinstance(marketplaces, dict) or not isinstance(plugins, dict):
        return {}
    targets: dict[str, dict] = {}
    for identity, settings in sorted(plugins.items()):
        if not isinstance(settings, dict) or settings.get("enabled") is not True or "@" not in identity:
            continue
        marketplace = identity.rsplit("@", 1)[1]
        source = marketplaces.get(marketplace)
        if (not isinstance(source, dict) or source.get("source_type") != "git"
                or not isinstance(source.get("source"), str) or not source["source"]):
            continue
        target = targets.setdefault(marketplace, {"source": source["source"], "ref": source.get("ref"),
                                                  "plugins": []})
        target["plugins"].append(identity)
    return targets


def remote_revision(source: str, ref: object = None) -> str | None:
    reference = ref if isinstance(ref, str) and ref else "HEAD"
    if len(reference) == 40 and all(character in "0123456789abcdefABCDEF" for character in reference):
        return reference.lower()
    try:
        result = subprocess.run(["git", "ls-remote", source, reference], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=GIT_TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    for line in result.stdout.splitlines():
        revision = line.split("\t", 1)[0].strip()
        if len(revision) == 40:
            return revision
    return None


def run_cli(command: list[str], *, cwd: Path | None = None) -> bool:
    try:
        result = subprocess.run(command, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=CLI_TIMEOUT_SECONDS, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def target_key(name: str, target: dict) -> str:
    value = json.dumps({key: target.get(key) for key in ("source", "ref", "plugins", "publishers")},
                       sort_keys=True, separators=(",", ":"))
    return "codex:" + name + ":" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def project_directories(config: dict) -> list[Path]:
    projects = config.get("projects", {})
    if not isinstance(projects, dict):
        return []
    return sorted({Path(path).resolve() for path, settings in projects.items()
                   if isinstance(settings, dict) and settings.get("trust_level") == "trusted"
                   and (Path(path) / ".codex/config.toml").is_file()})


def effective_config(executable: str, project: Path) -> dict:
    process = subprocess.Popen([executable, "app-server"], cwd=project, stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, encoding="utf-8", bufsize=1,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    messages = queue.Queue()

    def receive():
        try:
            for line in process.stdout:
                messages.put(json.loads(line))
        except (OSError, ValueError) as error:
            messages.put(error)
        finally:
            messages.put(None)

    threading.Thread(target=receive, daemon=True).start()

    def request(identity, method, params):
        process.stdin.write(json.dumps({"id": identity, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        deadline = time.monotonic() + CLI_TIMEOUT_SECONDS
        while True:
            message = messages.get(timeout=max(0, deadline - time.monotonic()))
            if message is None or isinstance(message, Exception):
                raise ValueError(f"Codex stopped during {method}")
            if message.get("id") == identity:
                if "error" in message:
                    raise ValueError(f"Codex {method} failed: {message['error']}")
                return message["result"]

    try:
        request(1, "initialize", {"clientInfo": {"name": "tj_agents_autoupdate", "version": "1.0.0"},
                                   "capabilities": {"experimentalApi": True}})
        process.stdin.write(json.dumps({"method": "initialized"}) + "\n")
        process.stdin.flush()
        return request(2, "config/read", {"cwd": str(project), "includeLayers": False})["config"]
    except queue.Empty as error:
        raise ValueError("Codex configuration read timed out") from error
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stdin.close()
        process.stdout.close()


def project_targets(executable: str, project: Path) -> dict[str, dict]:
    targets = codex_targets(effective_config(executable, project))
    command = [executable, "plugin", "list", "--available", "--json"]
    options = {"cwd": project, "stdin": subprocess.DEVNULL, "capture_output": True, "text": True,
               "encoding": "utf-8", "errors": "replace", "timeout": CLI_TIMEOUT_SECONDS, "check": True}
    try:
        result = subprocess.run(command, **options)
    except subprocess.CalledProcessError:
        if not run_cli([executable, "plugin", "marketplace", "upgrade"], cwd=project):
            raise
        result = subprocess.run(command, **options)
    listing = json.loads(result.stdout)
    installed = {entry.get("pluginId") for entry in listing.get("installed", [])
                 if entry.get("installed") is True}
    for target in targets.values():
        target["missing"] = sorted(set(target["plugins"]) - installed)
        publishers = {}
        for entry in listing.get("installed", []) + listing.get("available", []):
            source = entry.get("source", {})
            if (entry.get("pluginId") in target["plugins"] and isinstance(source, dict)
                    and source.get("source") == "git-subdir" and isinstance(source.get("url"), str)):
                ref = source.get("sha") or source.get("ref") or "HEAD"
                if isinstance(ref, str):
                    publishers[(source["url"], ref)] = {"source": source["url"], "ref": ref}
        target["publishers"] = list(publishers.values())
    return targets


def refresh_codex(executable: str, targets: dict[str, dict], recorded: dict, revision=remote_revision,
                  run=run_cli, project: Path | None = None) -> dict[str, str]:
    outcomes: dict[str, str] = {}
    names = sorted(targets)
    references = sorted({(source["source"], source.get("ref") or "HEAD")
                         for target in targets.values() for source in [target, *target.get("publishers", [])]})
    with ThreadPoolExecutor(max_workers=max(1, min(8, len(references)))) as pool:
        heads = dict(zip(references, pool.map(lambda source: revision(*source), references)))
    for marketplace in names:
        target = targets[marketplace]
        key = target_key(marketplace, target)
        sources = [target, *target.get("publishers", [])]
        published = [heads[(source["source"], source.get("ref") or "HEAD")] for source in sources]
        head = (hashlib.sha256(json.dumps(published).encode("utf-8")).hexdigest()
                if len(published) > 1 else published[0])
        if published[0] is None:
            outcomes[marketplace] = "unreachable"
            continue
        if all(value is not None for value in published) and recorded.get(key) == head and not target.get("missing"):
            outcomes[marketplace] = "current"
            continue
        def invoke(command):
            return run(command, cwd=project) if project is not None else run(command)

        refreshed = invoke([executable, "plugin", "marketplace", "upgrade", marketplace]) and all(
            invoke([executable, "plugin", "add", plugin]) for plugin in target["plugins"])
        if refreshed:
            if all(value is not None for value in published):
                recorded[key] = head
            outcomes[marketplace] = "updated"
        else:
            outcomes[marketplace] = "failed"
    return outcomes



def refresh_projects(executable: str, config: dict, recorded: dict, run=run_cli) -> dict[str, dict]:
    revisions = {}

    def revision(source, ref):
        key = (source, ref)
        if key not in revisions:
            revisions[key] = remote_revision(source, ref)
        return revisions[key]

    outcomes = {"user": {}}
    if codex_targets(config):
        try:
            outcomes["user"] = refresh_codex(executable, project_targets(executable, Path.home()), recorded,
                                              revision=revision, run=run, project=Path.home())
        except (OSError, ValueError, TypeError, AttributeError, subprocess.SubprocessError) as error:
            outcomes["user"] = {"error": str(error)}
    for project in project_directories(config):
        try:
            targets = project_targets(executable, project)
            outcomes[str(project)] = refresh_codex(executable, targets, recorded, revision=revision, run=run,
                                                   project=project)
        except (OSError, ValueError, TypeError, AttributeError, subprocess.SubprocessError) as error:
            outcomes[str(project)] = {"error": str(error)}
    return outcomes


def load_codex_config() -> dict:
    import tomllib

    try:
        with (codex_home() / "config.toml").open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


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


def sweep_worktrees(codex_config: dict) -> str:
    relative = Path(".agents", "engineering", "workflow", "merge", "scripts", "worktree_sweep.py")
    script = newest_existing([root / relative for root in installed_plugin_roots("engineering", claude_home(),
                                                                                   codex_config)])
    if script is None:
        return "engineering package not installed"
    try:
        result = subprocess.run([sys.executable, "-B", str(script)], stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=SWEEP_TIMEOUT_SECONDS,
                                check=False)
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
        config = load_codex_config()
        executable = shutil.which("codex")
        outcomes = refresh_projects(executable, config, recorded) if executable else {}
        sweep = "skipped" if arguments.no_sweep else sweep_worktrees(config)
        write_json(state_file, {"revisions": recorded, "last_run": time.time(), "outcomes": outcomes,
                                "worktree_sweep": sweep})
        if not arguments.no_self_update:
            self_update(Path(__file__), load_codex_config())
    finally:
        lock.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
