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
IN_USE = ".in_use"
ADOPTION = "Codex adopts updates when the conversation resumes in a new process."


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


def applies(entry: dict, project: Path) -> bool:
    if entry.get("scope") in {"user", "managed"}:
        return True
    owner = entry.get("projectPath")
    return bool(owner) and project.resolve().is_relative_to(Path(owner).resolve())


def path_key(path: object) -> str:
    return os.path.normcase(str(Path(path).resolve()))


def declared_scopes(identity: str, project: Path) -> list[str]:
    return [scope for scope, name in (("project", "settings.json"), ("local", "settings.local.json"))
            if read_json(project / ".claude" / name).get("enabledPlugins", {}).get(identity) is True]


def update_targets(identity: str, project: Path, installations: list) -> list[tuple[str, Path]]:
    declared = declared_scopes(identity, project)
    targets = {(scope, path_key(project)): (scope, project) for scope in declared or ["user"]}
    for entry in installations:
        scope = entry.get("scope")
        if entry.get("id") != identity or scope not in {"user", "project", "local"} or not applies(entry, project):
            continue
        owner = project if scope == "user" else Path(entry["projectPath"])
        targets.setdefault((scope, path_key(owner)), (scope, owner))
    return [targets[key] for key in sorted(targets)]


def update_result(output: str, identity: str, scope: str) -> dict:
    for line in reversed(output.splitlines()):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            break
    else:
        raise RefreshError(f"{identity} ({scope}): claude plugin update printed no result")
    outcome = value.get("updateOutcome")
    if outcome not in {"updated", "up_to_date"} or value.get("refreshFailed") or not value.get("newVersion"):
        raise RefreshError(f"{identity} ({scope}) was not updated: {value.get('message') or outcome}")
    return value


def plugin_errors(installations: list, project: Path) -> list[str]:
    return [f"{entry.get('id')} ({entry.get('scope')}): {error}" for entry in installations
            if entry.get("enabled") is True and applies(entry, project) for error in entry.get("errors") or []]


def persistence_problems(expected: list[tuple[str, str, Path, str]], installations: list) -> list[str]:
    problems = []
    for identity, scope, owner, version in expected:
        entry = next((entry for entry in installations if entry.get("id") == identity and entry.get("scope") == scope
                      and (scope == "user" or entry.get("projectPath") and path_key(entry["projectPath"]) == path_key(owner))),
                     None)
        if entry is None or entry.get("version") != version:
            found = entry.get("version") if entry else "nothing"
            problems.append(f"{identity} ({scope}) update did not persist: installed_plugins.json has {found}, "
                            f"the update reported {version}")
    return problems


def plugin_revision(identity: str) -> str | None:
    plugin, name = identity.rsplit("@", 1)
    known = read_json(configuration_root("claude") / "plugins/known_marketplaces.json")
    location = known.get(name, {}).get("installLocation")
    if not location:
        return None
    catalog = read_json(Path(location) / ".claude-plugin/marketplace.json")
    source = next((entry.get("source") for entry in catalog.get("plugins", [])
                   if isinstance(entry, dict) and entry.get("name") == plugin), None)
    path = (source.get("path") if isinstance(source, dict) and source.get("source") == "local"
           else source if isinstance(source, str) else None)
    return plugin_autoupdate.subtree_revision(Path(location), path.lstrip("./")) if isinstance(path, str) else None


def refresh_claude(executable: str, project: Path, plugins: list[str], recorded: dict | None = None) -> list[str]:
    installations = json.loads(run([executable, "plugin", "list", "--json"], project))
    expected, updated = [], []
    for identity in plugins:
        for scope in declared_scopes(identity, project):
            run([executable, "plugin", "install", identity, "--scope", scope], project)
        revision = plugin_revision(identity) if recorded is not None else None
        if revision is not None and recorded.get(identity) == revision:
            continue
        for scope, owner in update_targets(identity, project, installations):
            result = update_result(run([executable, "plugin", "update", identity, "--scope", scope, "--json"], owner),
                                   identity, scope)
            expected.append((identity, scope, owner, result["newVersion"]))
            if result["updateOutcome"] == "updated" and identity not in updated:
                updated.append(identity)
        if revision is not None:
            recorded[identity] = revision
    after = json.loads(run([executable, "plugin", "list", "--json"], project))
    problems = persistence_problems(expected, after) + plugin_errors(after, project)
    if problems:
        raise RefreshError("; ".join(problems))
    return updated


def refresh(host: str, executable: str, project: Path, marketplaces: dict, plugins: list[str],
           recorded: dict | None = None) -> list[str]:
    known = read_json(configuration_root(host) / "plugins/known_marketplaces.json") if host == "claude" else {}
    for name in marketplaces:
        if host == "claude" and name not in known:
            run([executable, "plugin", "marketplace", "add", marketplaces[name]], project)
        run([executable, "plugin", "marketplace", "update" if host == "claude" else "upgrade", name], project)
    if host == "claude":
        return refresh_claude(executable, project, plugins, recorded) if plugins else []
    user_config = configuration_root(host) / "config.toml"
    user_enabled = plugin_autoupdate.enabled_identities(plugin_autoupdate.load_toml(user_config))
    for identity in plugins:
        run([executable, "plugin", "add", identity], project)
    plugin_autoupdate.remove_user_plugins(user_config, set(plugins) - user_enabled)
    return []


def publishers(name: str, plugins: list[str]) -> set[str]:
    location = read_json(configuration_root("claude") / "plugins/known_marketplaces.json").get(name, {}).get("installLocation")
    catalog = read_json(Path(location) / ".claude-plugin/marketplace.json") if location else {}
    wanted = {identity.rsplit("@", 1)[0] for identity in plugins if identity.rsplit("@", 1)[1] == name}
    return {repository(entry["source"].get("url")) for entry in catalog.get("plugins", [])
            if isinstance(entry, dict) and entry.get("name") in wanted and isinstance(entry.get("source"), dict)}


def refresh_repositories(project: Path, repositories: set[str] | None, updated: set[str] | None = None) -> bool:
    marketplaces, plugins = selection("claude", "", project)
    chosen = {name: repo for name, repo in marketplaces.items()
              if repositories is None or repo in repositories or publishers(name, plugins) & repositories}
    if chosen:
        versions_path = configuration_root("claude") / "plugins" / "tj-agents-plugin-versions.json"
        recorded = read_json(versions_path)
        changed = refresh("claude", agent_cli.resolve_claude_executable(), project, chosen,
                          [identity for identity in plugins if identity.rsplit("@", 1)[1] in chosen], recorded)
        plugin_autoupdate.write_json(versions_path, recorded)
        if updated is not None:
            updated.update(changed)
    return True


def package_tree(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise RefreshError(f"Missing plugin directory: {root}")
    result = {}
    for path in root.rglob("*"):
        parts = path.relative_to(root).parts
        if parts[0] == IN_USE:
            continue
        if path.is_symlink():
            raise RefreshError(f"Unexpected plugin symlink: {path}")
        if path.is_file() and ".git" not in parts:
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
        entries = [entry for entry in entries if applies(entry, project)]
    installed = {entry.get("id", entry.get("pluginId")) for entry in entries if entry.get("enabled") is True}
    problems = [f"Missing enabled native installation: {identity}" for identity in plugins if identity not in installed]
    if host == "claude":
        problems += plugin_errors(entries, project)
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


def executable_for(host: str) -> str:
    return agent_cli.resolve_claude_executable() if host == "claude" else agent_cli.resolve_codex_executable()[0]


def review_legacy(hosts: tuple[str, ...], project: Path) -> tuple[list[str], dict[str, list[str]]]:
    import legacy_marketplaces

    removed, problems = [], {}
    for host in hosts:
        try:
            gone, found = legacy_marketplaces.review(host, project, lambda host=host: executable_for(host), run)
        except (RefreshError, agent_cli.LaunchError, OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            gone, found = [], [f"legacy marketplace review failed: {error}"]
        removed += gone
        if found:
            problems[host] = found
    return removed, problems


def relaunch_session(project: Path, updated: set[str]) -> dict | None:
    import session_relaunch

    identity = session_relaunch.session_identity()
    if identity is None:
        return None
    installed = read_json(configuration_root("claude") / "plugins/installed_plugins.json").get("plugins") or {}
    _, plugins = selection("claude", "", project)
    stale = session_relaunch.stale_plugins(identity[1], project, plugins, installed, updated)
    if not stale:
        return None
    if os.environ.get("CLAUDE_CODE_CHILD_SESSION"):
        return {"relaunch": "skipped", "stale": stale, "reason": "a child session cannot relaunch its parent; "
                                                              "run sync-plugins from the parent session"}
    try:
        result = session_relaunch.relaunch(project, installed)
    except Exception as error:
        return {"relaunch": "failed", "stale": stale, "error": str(error)}
    print("plugins: this Claude session closes when the turn ends and resumes in a fresh process with "
          + ", ".join(stale), file=sys.stderr)
    return {**result, "stale": stale}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="both")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--no-relaunch", action="store_true", help="Never relaunch the calling Claude session")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--all", action="store_true", help="Refresh every selected plugin, not only published changes")
    modes.add_argument("--verify", action="store_true", help="Refresh, then inspect native installations and remote main revisions")
    modes.add_argument("--verify-only", action="store_true", help="Inspect without changing plugins")
    arguments = parser.parse_args(argv)
    project = arguments.project.resolve()
    hosts = ("claude", "codex") if arguments.host == "both" else (arguments.host,)
    updated: set[str] = set()
    removed, legacy = review_legacy(hosts, project)
    relaunch_allowed = "claude" in hosts and not arguments.no_relaunch and not arguments.verify_only
    if not (arguments.all or arguments.verify or arguments.verify_only):
        result = launch_check.check(project, update=lambda host, repositories, root:
                                    launch_check.update_host(host, repositories, root, updated))
        if result != "unconfigured":
            summary = {"check": result}
            if removed:
                summary["legacy_removed"] = removed
            if legacy:
                summary["legacy_problems"] = legacy
            relaunched = relaunch_session(project, updated) if relaunch_allowed and result != "failed" else None
            if relaunched:
                summary["claude"] = relaunched
            print(json.dumps(summary, indent=2))
            if result == "updated":
                print(ADOPTION, file=sys.stderr)
            for line in [line for found in legacy.values() for line in found]:
                print("plugins: " + line, file=sys.stderr)
            failed = bool(legacy) or bool(relaunched and relaunched["relaunch"] == "failed")
            return int(result in {"failed", "offline", "busy"} or failed)
    reports = []
    for host in hosts:
        try:
            executable = executable_for(host)
            marketplaces, plugins = selection(host, executable, project)
            changed = [] if arguments.verify_only else refresh(host, executable, project, marketplaces, plugins)
            updated.update(changed)
            report = (verify(host, executable, project, marketplaces, plugins)
                      if arguments.verify or arguments.verify_only else {"host": host, "plugins": plugins, "problems": []})
        except (RefreshError, agent_cli.LaunchError, OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
            report = {"host": host, "problems": [str(error)]}
        refreshed = not report["problems"]
        report["problems"] = report["problems"] + legacy.get(host, [])
        report["legacy_removed"] = [name for name in removed if name.startswith(host + ":")]
        if host == "claude" and relaunch_allowed and refreshed:
            relaunched = relaunch_session(project, updated)
            if relaunched:
                report["relaunch"] = relaunched
                if relaunched["relaunch"] == "failed":
                    report["problems"].append("relaunch failed: " + relaunched["error"])
        reports.append(report)
    print(json.dumps(reports, indent=2))
    for report in reports:
        for problem in report["problems"]:
            print(f"plugins: {report['host']}: {problem}", file=sys.stderr)
    print(ADOPTION, file=sys.stderr)
    return int(any(report["problems"] for report in reports))


if __name__ == "__main__":
    raise SystemExit(main())
