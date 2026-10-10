#!/usr/bin/env python3
"""Refresh enabled Claude plugins from their registered marketplaces before a session loads them."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"
STATE_FILE = "claude-standards-sync.json"
LOCK_FILE = "claude-standards-sync.lock"
REMOTE_TIMEOUT_SECONDS = 20
MARKETPLACE_TIMEOUT_SECONDS = 180
PLUGIN_TIMEOUT_SECONDS = 120
LOCK_WAIT_SECONDS = 180
STALE_LOCK_SECONDS = 900
GIT_SOURCES = {"github", "git"}
FULL_SHA = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class Install:
    identity: str
    scope: str
    project: Path | None
    version: str

    @property
    def name(self) -> str:
        return self.identity.rsplit("@", 1)[0]

    @property
    def marketplace(self) -> str:
        return self.identity.rsplit("@", 1)[1]

    @property
    def key(self) -> str:
        return "|".join((self.identity, self.scope, comparable(self.project) if self.project else ""))


@dataclass
class Marketplace:
    name: str
    checkout: Path | None
    url: str | None
    ref: str | None
    installs: list[Install] = field(default_factory=list)
    owned: bool = True


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def comparable(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path))).rstrip("\\/")


def within(child: Path, parent: Path) -> bool:
    child_key, parent_key = comparable(child), comparable(parent)
    return child_key == parent_key or child_key.startswith(parent_key + os.sep)


def config_root(environ) -> Path:
    configured = environ.get("CLAUDE_CONFIG_DIR")
    return Path(configured) if configured else Path.home() / ".claude"


def plugins_root(config: Path, environ) -> Path:
    configured = environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR")
    return Path(configured) if configured else config / "plugins"


def state_root(environ) -> Path:
    configured = environ.get(STATE_DIRECTORY_ENV)
    return Path(configured) if configured else Path.home() / ".agents-state"


def enabled_plugins(config: Path, project: Path) -> set[str]:
    merged: dict = {}
    for path in (
        config / "settings.json",
        project / ".claude" / "settings.json",
        project / ".claude" / "settings.local.json",
    ):
        values = read_json(path).get("enabledPlugins")
        if isinstance(values, dict):
            merged.update(values)
    return {identity for identity, enabled in merged.items() if enabled is True}


def installs(plugins: Path, project: Path, enabled: set[str]) -> list[Install]:
    records = read_json(plugins / "installed_plugins.json").get("plugins")
    found = []
    for identity, entries in records.items() if isinstance(records, dict) else ():
        if identity not in enabled or "@" not in identity or not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            scope = entry.get("scope")
            version = str(entry.get("version") or "unknown")
            owner = entry.get("projectPath")
            if scope in ("user", "managed"):
                found.append(Install(identity, scope, None, version))
            elif scope in ("project", "local") and isinstance(owner, str) and owner and within(project, Path(owner)):
                found.append(Install(identity, scope, Path(owner), version))
    return found


def source_url(source: dict) -> str | None:
    if source.get("source") == "github" and isinstance(source.get("repo"), str):
        return f"https://github.com/{source['repo']}.git"
    url = source.get("url")
    return url if isinstance(url, str) and url else None


def marketplaces(plugins: Path, found: list[Install]) -> list[Marketplace]:
    known = read_json(plugins / "known_marketplaces.json")
    grouped: dict[str, list[Install]] = {}
    for install in found:
        grouped.setdefault(install.marketplace, []).append(install)
    selected = []
    for name, members in sorted(grouped.items()):
        entry = known.get(name)
        source = entry.get("source") if isinstance(entry, dict) else None
        if not isinstance(source, dict) or source.get("source") not in GIT_SOURCES:
            continue
        location = entry.get("installLocation")
        checkout = Path(location) if isinstance(location, str) and location else None
        if checkout is not None and checkout.exists() and not is_checkout(checkout):
            continue
        ref = source.get("ref")
        selected.append(Marketplace(name, checkout, source_url(source), ref if isinstance(ref, str) and ref else None, members))
    return selected


def plugin_entry_sources(checkout: Path | None) -> dict[str, dict]:
    if checkout is None:
        return {}
    entries = read_json(checkout / ".claude-plugin" / "marketplace.json").get("plugins")
    found = {}
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                found[entry["name"]] = entry.get("source")
    return found


def repo_label(url: str) -> str:
    stripped = url[:-4] if url.endswith(".git") else url
    segments = [segment for segment in re.split(r"[\\/]+", stripped) if segment]
    return "/".join(segments[-2:]) if len(segments) >= 2 else (segments[-1] if segments else stripped)


def normalize_url(url: str) -> str:
    stripped = url.strip()
    if "://" in stripped:
        stripped = re.sub(r"^[a-z][a-z0-9+.-]*://", "", stripped, flags=re.IGNORECASE)
    else:
        scp = re.match(r"^[^/@]+@([^:/]+):(.+)$", stripped)
        if scp:
            stripped = f"{scp.group(1)}/{scp.group(2)}"
    stripped = stripped.rstrip("/")
    if stripped.lower().endswith(".git"):
        stripped = stripped[:-4]
    host, separator, rest = stripped.partition("/")
    return host.rsplit("@", 1)[-1].lower() + separator + rest


def external_groups(markets: list[Marketplace]) -> list[Marketplace]:
    grouped: dict[tuple[str, str | None], tuple[str, list[Install]]] = {}
    for market in markets:
        sources = plugin_entry_sources(market.checkout)
        own = normalize_url(market.url) if market.url else None
        native = []
        for install in market.installs:
            override = sources.get(install.name)
            resolved = source_url(override) if isinstance(override, dict) else None
            if resolved and normalize_url(resolved) != own:
                ref = override.get("ref")
                key = (normalize_url(resolved), ref if isinstance(ref, str) and ref else None)
                raw_url, members = grouped.get(key, (resolved, []))
                members.append(install)
                grouped[key] = (raw_url, members)
            else:
                native.append(install)
        market.installs = native
    ordered = sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1] or ""))
    return [Marketplace(repo_label(raw_url), None, raw_url, ref, members, owned=False) for (_, ref), (raw_url, members) in ordered]


def run(command: list[str], cwd: Path | None = None, timeout: float = REMOTE_TIMEOUT_SECONDS) -> tuple[int | None, str, str]:
    environment = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            **options,
        )
    except subprocess.TimeoutExpired:
        return None, "", f"timed out after {timeout:g}s"
    except OSError as error:
        return None, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr


def last_line(*texts: str) -> str:
    for text in texts:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            return lines[-1]
    return "no output"


def git(checkout: Path, *arguments: str) -> str | None:
    code, output, _ = run(["git", "-C", str(checkout), *arguments])
    return output.strip() or None if code == 0 else None


def is_checkout(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def checkout_head(market: Marketplace) -> str | None:
    if market.checkout is None or not is_checkout(market.checkout):
        return None
    return git(market.checkout, "rev-parse", "HEAD")


def remote_commit(market: Marketplace) -> tuple[str | None, str | None]:
    if market.ref and FULL_SHA.fullmatch(market.ref):
        return market.ref, None
    present = market.checkout is not None and is_checkout(market.checkout)
    url = (git(market.checkout, "remote", "get-url", "origin") if present else None) or market.url
    if not url:
        return None, "no remote URL"
    wanted = market.ref or (git(market.checkout, "symbolic-ref", "--quiet", "--short", "HEAD") if present else None)
    code, output, error = run(["git", "ls-remote", url, wanted or "HEAD"])
    if code != 0:
        return None, last_line(error, output)
    refs = {}
    for line in output.splitlines():
        commit, _, name = line.partition("\t")
        if FULL_SHA.fullmatch(commit.strip()):
            refs[name.strip()] = commit.strip()
    names = (wanted, f"refs/tags/{wanted}^{{}}", f"refs/heads/{wanted}", f"refs/tags/{wanted}") if wanted else ("HEAD",)
    for name in names:
        if name in refs:
            return refs[name], None
    return None, f"{wanted or 'HEAD'} not found"


def probe(market: Marketplace) -> tuple[str | None, str | None, str | None]:
    remote, error = remote_commit(market)
    return remote, checkout_head(market), error


def load_state(root: Path) -> dict[str, str]:
    recorded = read_json(root / STATE_FILE).get("installs")
    if not isinstance(recorded, dict):
        return {}
    return {key: value for key, value in recorded.items() if isinstance(key, str) and isinstance(value, str)}


def save_state(root: Path, state: dict[str, str]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    temporary = root / f".{STATE_FILE}.{os.getpid()}.tmp"
    temporary.write_text(json.dumps({"schema_version": 1, "installs": dict(sorted(state.items()))}, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, root / STATE_FILE)


@contextmanager
def exclusive(root: Path, wait: float):
    root.mkdir(parents=True, exist_ok=True)
    path = root / LOCK_FILE
    deadline = time.monotonic() + wait
    while True:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                if time.time() - path.stat().st_mtime > STALE_LOCK_SECONDS:
                    path.unlink()
                    continue
            except FileNotFoundError:
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError("another launch is still updating plugins") from None
            time.sleep(0.25)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        yield lambda: os.utime(path)
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def claude(executable: str, arguments: list[str], cwd: Path, timeout: float) -> tuple[bool, str]:
    code, output, error = run([executable, *arguments], cwd=cwd, timeout=timeout)
    lines = [line for line in output.splitlines() if line.strip()]
    if lines:
        try:
            result = json.loads(lines[-1])
        except ValueError:
            result = None
        if isinstance(result, dict) and "outcome" in result:
            return result["outcome"] == "ok", str(result.get("message") or "")
    return code == 0, last_line(error, output)


def short(commit: str | None) -> str:
    return commit[:12] if commit else "none"


def describe(members: list[Install]) -> str:
    return ", ".join(
        f"{install.name} {install.version}" + ("" if install.scope == "user" else f" ({install.scope})")
        for install in members
    )


def current(install: Install, remote: str, state: dict[str, str]) -> bool:
    return state.get(install.key) == remote or install.version == remote[:12]


def default_claude() -> str | None:
    native = Path.home() / ".local" / "bin" / ("claude.exe" if os.name == "nt" else "claude")
    return str(native) if native.is_file() else shutil.which("claude")


def update(market: Marketplace, remote: str, executable: str, project: Path, plugins: Path, state: dict[str, str],
           renew, out) -> int:
    pending = [install for install in market.installs if not current(install, remote, state)]
    before = checkout_head(market)
    print(f"standards: updating {market.name} to {short(remote)} (installed: {describe(pending or market.installs)})", file=out, flush=True)
    if market.owned and before != remote:
        renew()
        ok, detail = claude(executable, ["plugin", "marketplace", "update", market.name], project, MARKETPLACE_TIMEOUT_SECONDS)
        if not ok:
            print(f"standards: {market.name} was not refreshed ({detail}); this session loads {describe(market.installs)}", file=out)
            return 1
    reached = checkout_head(market) or remote
    failed = []
    for install in market.installs:
        if state.get(install.key) == reached or install.version == reached[:12]:
            state[install.key] = reached
            continue
        arguments = ["plugin", "update", install.identity, "--scope", install.scope, "--json"]
        renew()
        ok, detail = claude(executable, arguments, install.project or project, PLUGIN_TIMEOUT_SECONDS)
        if ok:
            state[install.key] = reached
        else:
            failed.append((install, detail))
    refreshed = {install.key: install for install in installs(plugins, project, {install.identity for install in market.installs})}
    print(f"standards: {market.name} at {short(reached)}: {describe([refreshed.get(install.key, install) for install in market.installs])}", file=out)
    for install, detail in failed:
        print(f"standards: {install.identity} ({install.scope}) was not updated ({detail}); this session loads {install.version}", file=out)
    return len(failed)


def synchronize(config: Path, plugins: Path, project: Path, state_dir: Path, executable: str | None,
                check: bool = False, out=sys.stdout, lock_wait: float = LOCK_WAIT_SECONDS) -> int:
    owned = marketplaces(plugins, installs(plugins, project, enabled_plugins(config, project)))
    groups = external_groups(owned)
    markets = [market for market in owned if market.installs] + groups
    if not markets:
        return 0
    with ThreadPoolExecutor(max_workers=min(8, len(markets))) as pool:
        probes = list(pool.map(probe, markets))
    state = load_state(state_dir)
    problems = 0
    stale = []
    for market, (remote, head, error) in zip(markets, probes):
        if remote is None:
            print(f"standards: could not check {market.name} ({error}); this session loads {describe(market.installs)}", file=out)
            problems += 1
        elif (market.owned and head != remote) or not all(current(install, remote, state) for install in market.installs):
            stale.append((market, remote))
    if check:
        for market, remote in stale:
            print(f"standards: {market.name} needs a refresh to {short(remote)} (installed: {describe(market.installs)})", file=out)
        return int(bool(problems or stale))
    if not stale:
        return int(bool(problems))
    if not executable:
        print("standards: the claude executable was not found; this session loads the installed plugins", file=out)
        return 1
    try:
        with exclusive(state_dir, lock_wait) as renew:
            state = load_state(state_dir)
            for market, remote in stale:
                problems += update(market, remote, executable, project, plugins, state, renew, out)
                save_state(state_dir, state)
    except TimeoutError as error:
        print(f"standards: {error}; this session loads the installed plugins", file=out)
        return 1
    return int(bool(problems))


def apply_harness_permissions(run=subprocess.run) -> None:
    """Converge this machine's declared harness permissions. Fire-and-forget: any failure here is
    swallowed rather than turned into a sync failure, because a permissions converge is strictly
    additional to a standards refresh. `run` defaults to the real `subprocess.run` but is accepted so a
    caller -- this module's own `main`, or codex_marketplace_sync.py's own sync, which imports this
    function rather than duplicating it -- can supply a fake for its own tests.
    """
    package_root = Path(__file__).resolve().parents[3]
    script = package_root / ".agents" / "machine" / "utility" / "bootstrap-capabilities" / "scripts" / "harness_permissions_sync.py"
    if not script.is_file():
        return
    try:
        run(
            [sys.executable, "-B", str(script), "--apply"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30,
        )
    except Exception:  # noqa: BLE001
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--claude")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    config = config_root(os.environ)
    try:
        code = synchronize(
            config,
            plugins_root(config, os.environ),
            arguments.project.resolve(),
            state_root(os.environ),
            arguments.claude or default_claude(),
            arguments.check,
        )
    except Exception as error:  # noqa: BLE001
        print(f"standards: sync failed ({error}); this session loads the installed plugins")
        code = 1
    apply_harness_permissions()
    return code


if __name__ == "__main__":
    sys.exit(main())
