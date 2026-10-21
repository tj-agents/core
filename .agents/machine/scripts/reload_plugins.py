#!/usr/bin/env python3
"""Refresh selected tj-agents plugins through native hosts (Python 3.9+)."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agent_cli
from codex_hook_trust import AppServer, github_repository
import launch_check
import plugin_autoupdate

TIMEOUT = 300
ADOPTION = "Claude: /reload-plugins adopts updates in open sessions. Codex: resume the conversation in a new process."


class RefreshError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise RefreshError(f"Expected an object in {path}")
    return value


def configuration_root(host: str) -> Path:
    variable = "CLAUDE_CONFIG_DIR" if host == "claude" else "CODEX_HOME"
    return Path(os.environ.get(variable) or Path.home() / ("." + host))


def repository(source: object) -> str | None:
    match = github_repository(source)
    return "/".join(match) if match else None


def selection(host: str, executable: str, project: Path) -> tuple[dict, list[str]]:
    if host == "claude":
        marketplaces, plugins = {}, {}
        for path in (configuration_root(host) / "settings.json", project / ".claude/settings.json",
                     project / ".claude/settings.local.json"):
            settings = read_json(path)
            marketplaces.update(settings.get("extraKnownMarketplaces", {}))
            plugins.update(settings.get("enabledPlugins", {}))
        known = read_json(configuration_root(host) / "plugins/known_marketplaces.json")
        sources = {name: entry.get("source", {}) for name, entry in known.items()}
        sources.update({name: entry.get("source", {}) for name, entry in marketplaces.items()})
        sources = {name: repository(source.get("repo")) if source.get("source") == "github"
                   else repository(source.get("url")) for name, source in sources.items() if isinstance(source, dict)}
        enabled = [name for name, flag in plugins.items() if flag is True]
    else:
        with AppServer(executable, project) as server:
            response = server.request("config/read", {"cwd": str(project), "includeLayers": True})
        config = response["config"]
        sources = {name: repository(source.get("source")) for name, source in config.get("marketplaces", {}).items()
                   if source.get("source_type") == "git"}
        enabled = [name for name, flag in config.get("plugins", {}).items()
                   if isinstance(flag, dict) and flag.get("enabled") is True]
    sources = {name: repo for name, repo in sources.items() if repo and repo.split("/", 1)[0] == "tj-agents"}
    enabled = sorted(name for name in enabled if name.rsplit("@", 1)[-1] in sources)
    used = {name.rsplit("@", 1)[-1] for name in enabled}
    return {name: repo for name, repo in sorted(sources.items()) if name in used}, enabled


def run(command: list[str], project: Path) -> str:
    print("Refreshing: " + " ".join(command[1:]), file=sys.stderr, flush=True)
    result = subprocess.run(command, cwd=project, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=TIMEOUT)
    if result.returncode:
        raise RefreshError((result.stderr or result.stdout).strip() or f"Command exited {result.returncode}")
    return result.stdout


def refresh(host: str, executable: str, project: Path, marketplaces: dict, plugins: list[str]) -> None:
    known = read_json(configuration_root(host) / "plugins/known_marketplaces.json") if host == "claude" else {}
    for name in marketplaces:
        if host == "claude" and name not in known:
            run([executable, "plugin", "marketplace", "add", marketplaces[name]], project)
        run([executable, "plugin", "marketplace", "update" if host == "claude" else "upgrade", name], project)
    installations = (json.loads(run([executable, "plugin", "list", "--json"], project))
                     if host == "claude" and plugins else [])
    user_config = configuration_root(host) / "config.toml"
    user_enabled = plugin_autoupdate.enabled_identities(plugin_autoupdate.load_toml(user_config))
    for identity in plugins:
        if host == "claude":
            declared = {scope for scope, name in (("project", "settings.json"), ("local", "settings.local.json"))
                        if read_json(project / ".claude" / name).get("enabledPlugins", {}).get(identity) is True}
            scopes = set(declared) or {"user"}
            for entry in installations:
                owner = entry.get("projectPath")
                if (entry.get("id") == identity and entry.get("scope") == "local" and owner
                        and project.resolve().is_relative_to(Path(owner).resolve())):
                    scopes.add("local")
            for scope in sorted(declared):
                run([executable, "plugin", "install", identity, "--scope", scope], project)
            for scope in sorted(scopes):
                run([executable, "plugin", "update", identity, "--scope", scope], project)
        else:
            run([executable, "plugin", "add", identity], project)
    if host == "codex":
        plugin_autoupdate.remove_user_plugins(user_config, set(plugins) - user_enabled)


def publishers(name: str, plugins: list[str]) -> set[str]:
    location = read_json(configuration_root("claude") / "plugins/known_marketplaces.json").get(name, {}).get("installLocation")
    catalog = read_json(Path(location) / ".claude-plugin/marketplace.json") if location else {}
    wanted = {identity.rsplit("@", 1)[0] for identity in plugins if identity.rsplit("@", 1)[1] == name}
    return {repository(entry["source"].get("url")) for entry in catalog.get("plugins", [])
            if isinstance(entry, dict) and entry.get("name") in wanted and isinstance(entry.get("source"), dict)}


def refresh_repositories(project: Path, repositories: set[str]) -> bool:
    marketplaces, plugins = selection("claude", "", project)
    chosen = {name: repo for name, repo in marketplaces.items()
              if repo in repositories or publishers(name, plugins) & repositories}
    if chosen:
        refresh("claude", agent_cli.resolve_claude_executable(), project, chosen,
                [identity for identity in plugins if identity.rsplit("@", 1)[1] in chosen])
    return True


def package_tree(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise RefreshError(f"Missing plugin directory: {root}")
    result = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise RefreshError(f"Unexpected plugin symlink: {path}")
        if path.is_file() and ".git" not in path.relative_to(root).parts:
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def source_tree(source: object, location: Path, project: Path, temporary: Path,
                publishers: dict) -> dict[str, bytes]:
    if isinstance(source, dict) and source.get("source") == "git-subdir":
        publisher = repository(source.get("url"))
        if not publisher or publisher.split("/", 1)[0] != "tj-agents":
            raise RefreshError("Cannot verify package from an unknown publisher")
        ref = source.get("sha") or source.get("ref") or "main"
        if not isinstance(ref, str) or not ref or ref.startswith("-"):
            raise RefreshError("Invalid package source revision")
        key = (publisher, ref)
        if key not in publishers:
            checkout = temporary / str(len(publishers))
            run(["git", "init", str(checkout)], project)
            run(["git", "-C", str(checkout), "fetch", "--depth=1",
                 f"https://github.com/{publisher}.git", ref], project)
            run(["git", "-C", str(checkout), "checkout", "--detach", "FETCH_HEAD"], project)
            publishers[key] = checkout
        location = publishers[key]
        source = source.get("path")
    elif isinstance(source, dict) and source.get("source") == "local":
        source = source.get("path")
    if not isinstance(source, str) or not source or Path(source).is_absolute():
        raise RefreshError("Cannot verify catalog package source")
    root = (location / source).resolve()
    if not root.is_relative_to(location.resolve()):
        raise RefreshError("Catalog package escapes its publisher")
    return package_tree(root)


def verify(host: str, executable: str, project: Path, marketplaces: dict, plugins: list[str]) -> dict:
    with tempfile.TemporaryDirectory(prefix="tj-agents-verify-") as temporary:
        return verify_packages(host, executable, project, marketplaces, plugins, Path(temporary))


def verify_packages(host: str, executable: str, project: Path, marketplaces: dict,
                    plugins: list[str], temporary: Path) -> dict:
    print(f"Verifying {host} native installations and marketplace revisions...", file=sys.stderr, flush=True)
    inventory = json.loads(run([executable, "plugin", "list", "--json"], project))
    entries = inventory if host == "claude" else inventory.get("installed", [])
    if host == "claude":
        entries = [entry for entry in entries if entry.get("scope") in {"user", "managed"}
                   or entry.get("projectPath") and project.resolve().is_relative_to(Path(entry["projectPath"]).resolve())]
    installed = {entry.get("id", entry.get("pluginId")) for entry in entries if entry.get("enabled") is True}
    problems = [f"Missing enabled native installation: {identity}" for identity in plugins if identity not in installed]
    revisions = {}
    publishers = {}
    for name, repo in marketplaces.items():
        print(f"Verifying {name} against {repo} main...", file=sys.stderr, flush=True)
        remote = run(["git", "ls-remote", f"https://github.com/{repo}.git", "refs/heads/main"], project).split()
        if not remote or not re.fullmatch(r"[0-9a-f]{40}", remote[0]):
            raise RefreshError(f"Could not resolve main for {repo}")
        if host == "claude":
            known = read_json(configuration_root(host) / "plugins/known_marketplaces.json")
            location = known.get(name, {}).get("installLocation")
        else:
            with AppServer(executable, project) as server:
                listing = server.request("plugin/list", {"cwds": [str(project)]})
            location = next((str(Path(market["path"]).parents[2]) for market in listing.get("marketplaces", [])
                             if market.get("name") == name), None)
        if not location:
            problems.append(f"Missing native marketplace checkout: {name}")
            continue
        local = run(["git", "-C", location, "rev-parse", "HEAD"], project).strip()
        revisions[name] = {"installed": local, "main": remote[0]}
        if local != remote[0]:
            problems.append(f"{name} checkout is at {local}, main is {remote[0]}")
        catalog = read_json(Path(location) / (".claude-plugin/marketplace.json" if host == "claude"
                                             else ".agents/plugins/marketplace.json"))
        sources = {entry["name"]: entry.get("source") for entry in catalog.get("plugins", [])}
        for identity in plugins:
            plugin, marketplace = identity.rsplit("@", 1)
            if marketplace != name:
                continue
            try:
                expected = source_tree(sources.get(plugin), Path(location), project, temporary, publishers)
            except RefreshError as error:
                problems.append(f"{identity}: {error}")
                continue
            for entry in entries:
                if entry.get("id", entry.get("pluginId")) != identity:
                    continue
                owner = entry.get("projectPath")
                if host == "claude" and entry.get("scope") in {"project", "local"}:
                    if not owner or not project.resolve().is_relative_to(Path(owner).resolve()):
                        continue
                install = (Path(entry["installPath"]) if host == "claude" else configuration_root(host)
                           / "plugins/cache" / name / plugin / (entry.get("version") or "local"))
                if package_tree(install) != expected:
                    problems.append(f"Native installed bytes differ from marketplace: {identity} ({install})")
    return {"host": host, "plugins": plugins, "marketplaces": revisions, "problems": problems}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="both")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--all", action="store_true", help="Refresh every selected plugin, not only published changes")
    modes.add_argument("--verify", action="store_true", help="Refresh, then inspect native installations and remote main revisions")
    modes.add_argument("--verify-only", action="store_true", help="Inspect without changing plugins")
    arguments = parser.parse_args(argv)
    if not (arguments.all or arguments.verify or arguments.verify_only):
        result = launch_check.check(arguments.project.resolve())
        if result != "unconfigured":
            print(json.dumps({"check": result}))
            if result == "updated":
                print(ADOPTION, file=sys.stderr)
            return int(result in {"failed", "offline", "busy"})
    hosts = ("claude", "codex") if arguments.host == "both" else (arguments.host,)
    reports = []
    for host in hosts:
        try:
            executable = (agent_cli.resolve_claude_executable() if host == "claude"
                          else agent_cli.resolve_codex_executable()[0])
            marketplaces, plugins = selection(host, executable, arguments.project.resolve())
            if not arguments.verify_only:
                refresh(host, executable, arguments.project.resolve(), marketplaces, plugins)
            report = (verify(host, executable, arguments.project.resolve(), marketplaces, plugins)
                      if arguments.verify or arguments.verify_only else {"host": host, "plugins": plugins, "problems": []})
        except (RefreshError, agent_cli.LaunchError, OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
            report = {"host": host, "problems": [str(error)]}
        reports.append(report)
    print(json.dumps(reports, indent=2))
    print(ADOPTION, file=sys.stderr)
    return int(any(report["problems"] for report in reports))


if __name__ == "__main__":
    raise SystemExit(main())
