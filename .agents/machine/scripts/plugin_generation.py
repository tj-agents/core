#!/usr/bin/env python3
"""Tell a running Claude or Codex session when the tj-agents generation it loaded is no longer the newest.

A host binds its plugin roots once, when the process starts. A later refresh installs a newer generation
for the next process and leaves this one executing the old hooks and skills. This gate runs at each prompt,
reads only local state, and reports that difference until the session adopts the new generation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Iterable, Mapping

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from generation_record import SHA, generations_path, read_generations  # noqa: E402

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SESSION_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
MARKER = ".tj-agents-rolling.json"
RUNTIME_MARKETPLACE = "tj-run-"
RECEIPT_ENV = "TJ_AGENTS_CODEX_RUNTIME_RECEIPT"
RECEIPT_SHA256_ENV = "TJ_AGENTS_CODEX_RUNTIME_RECEIPT_SHA256"
CODEX_ROOT_VARIABLES = ("PLUGIN_ROOT", "CODEX_PLUGIN_ROOT")
STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"
STATE_RETENTION_SECONDS = 14 * 24 * 60 * 60
HOSTS = ("claude", "codex")


@dataclass(frozen=True)
class Binding:
    identity: str
    repository: str
    revision: str | None
    root: str
    problem: str | None = None


def normalized(path: str | Path) -> str:
    return os.path.normcase(str(Path(path).resolve()))


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def state_directory(environ: Mapping[str, str]) -> Path:
    configured = environ.get(STATE_DIRECTORY_ENV)
    return Path(configured) if configured else Path.home() / ".agents-state"


def plugins_root(host: str, environ: Mapping[str, str]) -> Path:
    if host == "claude":
        if environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR"):
            return Path(environ["CLAUDE_CODE_PLUGIN_CACHE_DIR"])
        return Path(environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "plugins"
    return Path(environ.get("CODEX_HOME") or Path.home() / ".codex") / "plugins"


class NoticeState:
    def __init__(self, host: str, session_id: str, environ: Mapping[str, str], now: float):
        self.path = state_directory(environ) / "plugin-generation" / f"{host}-{session_id}.json"
        self.now = now
        stored = read_json(self.path)
        self.notified = stored.get("notified") if isinstance(stored, dict) else None

    def save(self, notified: str | None) -> None:
        if notified == self.notified:
            self.touch()
        else:
            temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                temporary.write_text(json.dumps({"notified": notified}) + "\n", encoding="utf-8")
                os.replace(temporary, self.path)
            except OSError:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
                return
        self.sweep()

    def touch(self) -> None:
        try:
            os.utime(self.path)
        except OSError:
            pass

    def sweep(self) -> None:
        for candidate in [*self.path.parent.glob("*.json"), *self.path.parent.glob(".*.tmp")]:
            try:
                if candidate != self.path and self.now - candidate.stat().st_mtime > STATE_RETENTION_SECONDS:
                    candidate.unlink()
            except OSError:
                continue


def ownership(root: Path) -> Mapping[str, object] | None:
    value = read_json(root.parent / MARKER)
    if not isinstance(value, dict) or not isinstance(value.get("identity"), str) \
            or not isinstance(value.get("repository"), str):
        return None
    return value


def applies(record: Mapping[str, object], project: Path | None) -> bool:
    scope = record.get("scope")
    if scope in {"user", "managed"}:
        return True
    owner = record.get("projectPath")
    if scope not in {"project", "local"} or not isinstance(owner, str) or project is None:
        return False
    try:
        project.resolve().relative_to(Path(owner).resolve())
    except (OSError, ValueError):
        return False
    return True


def claude_install_paths(environ: Mapping[str, str], project: Path | None) -> list[str]:
    registry = read_json(plugins_root("claude", environ) / "installed_plugins.json")
    plugins = registry.get("plugins") if isinstance(registry, dict) else None
    paths = []
    for records in plugins.values() if isinstance(plugins, dict) else ():
        if isinstance(records, list):
            paths.extend(record["installPath"] for record in records if isinstance(record, dict)
                         and isinstance(record.get("installPath"), str) and applies(record, project))
    return paths


def claude_binding(root: Path, environ: Mapping[str, str], project: Path | None) -> Binding | None:
    owner = ownership(root)
    if owner is None:
        loaded, plugin = normalized(root), normalized(root.parent)
        replacement = next((path for path in claude_install_paths(environ, project)
                            if normalized(Path(path).parent) == plugin and normalized(path) != loaded), None)
        if replacement is None:
            return None
        return Binding(root.parent.name, str(root.parent), None, str(root),
                       f"this process loaded {root.name}, but {Path(replacement).name} is installed")
    revision = root.name if SHA.fullmatch(root.name) else None
    problem = None if revision else "its install directory does not name a verified revision"
    return Binding(owner["identity"], owner["repository"], revision, str(root), problem)


def codex_binding(root: Path) -> Binding | None:
    owner = ownership(root)
    if owner is None:
        return None
    if not root.parent.parent.name.startswith(RUNTIME_MARKETPLACE):
        return Binding(owner["identity"], owner["repository"], None, str(root),
                       "it was not launched through the tj-agents launcher, so its shared install can change under it")
    revision = owner.get("revision")
    if not isinstance(revision, str) or not SHA.fullmatch(revision):
        return Binding(owner["identity"], owner["repository"], None, str(root), "its binding marker names no revision")
    return Binding(owner["identity"], owner["repository"], revision, str(root))


def receipt_roots(environ: Mapping[str, str]) -> list[Path]:
    digest = environ.get(RECEIPT_SHA256_ENV)
    if not digest or not SHA256.fullmatch(digest):
        raise ValueError("its Codex runtime receipt digest is missing")
    receipt = Path(environ[RECEIPT_ENV]).resolve(strict=True)
    content = receipt.read_bytes()
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError("its Codex runtime receipt failed its integrity check")
    value = json.loads(content)
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("its Codex runtime receipt has an unsupported schema")
    home = Path(environ.get("CODEX_HOME") or Path.home() / ".codex").resolve()
    if not isinstance(value.get("codex_home"), str) or Path(value["codex_home"]).resolve() != home:
        raise ValueError("its Codex runtime receipt names another Codex home")
    cache = (home / "plugins" / "cache").resolve()
    session = receipt.parent
    session.relative_to((cache / ".tj-agents-rolling" / "codex" / "sessions").resolve())
    if not isinstance(value.get("catalog"), str) or Path(value["catalog"]).resolve(strict=True) != session / "catalog":
        raise ValueError("its Codex runtime receipt names another catalog")
    roots = value.get("roots")
    unmanaged = value.get("unmanaged_roots", [])
    if not isinstance(roots, list) or not roots or not isinstance(unmanaged, list) \
            or not all(isinstance(item, str) for item in [*roots, *unmanaged]):
        raise ValueError("its Codex runtime receipt names no valid plugin roots")
    resolved = []
    for item, managed in [*((item, True) for item in roots), *((item, False) for item in unmanaged)]:
        root = Path(item).resolve(strict=managed)
        parts = root.relative_to(cache).parts
        if len(parts) != 3 or (managed and (not parts[0].startswith(RUNTIME_MARKETPLACE) or parts[2] != "local")) \
                or (not managed and parts[0].startswith(".")):
            raise ValueError("its Codex runtime receipt names a root outside the runtime cache layout")
        if root not in resolved:
            resolved.append(root)
    return resolved


def session_bindings(host: str, environ: Mapping[str, str], project: Path | None) -> tuple[list[Binding], list[str]]:
    if host == "claude":
        own = environ.get("CLAUDE_PLUGIN_ROOT")
        binding = claude_binding(Path(own), environ, project) if own else None
        return ([binding] if binding is not None else []), []
    if environ.get(RECEIPT_ENV) or environ.get(RECEIPT_SHA256_ENV):
        try:
            roots = receipt_roots(environ)
        except (KeyError, OSError, ValueError, TypeError) as error:
            reason = str(error) if str(error).startswith("its ") else f"its Codex runtime receipt is invalid ({error})"
            return [], [reason]
    else:
        root = next((environ[name] for name in CODEX_ROOT_VARIABLES if environ.get(name)), None)
        if root is None:
            return [], ["neither a Codex runtime receipt nor a plugin root is available"]
        roots = [Path(root)]
    bindings = [codex_binding(root) for root in roots]
    return [binding for binding in bindings if binding is not None], []


def installed_generations(environ: Mapping[str, str]) -> dict[str, list[dict[str, object]]] | None:
    by_repository: dict[str, list[dict[str, object]]] = {}
    for host in HOSTS:
        entries = read_generations(generations_path(plugins_root(host, environ), host))
        if entries is None:
            return None
        for entry in entries:
            by_repository.setdefault(entry["repository"], []).append(entry)
    for entries in by_repository.values():
        entries.sort(key=lambda entry: entry["verified_at"])
    return by_repository


def short(revision: str | None) -> str:
    return revision[:12] if revision else "unknown"


def findings(bindings: Iterable[Binding], installed: Mapping[str, list[dict[str, object]]]) -> list[str]:
    grouped: dict[str, list[Binding]] = {}
    for binding in bindings:
        grouped.setdefault(binding.repository, []).append(binding)
    lines = []
    for repository in sorted(grouped):
        members = sorted(grouped[repository], key=lambda binding: binding.identity)
        name = repository.removeprefix("https://github.com/").removesuffix(".git")
        for binding in members:
            if binding.problem:
                lines.append(f"{name}: {binding.identity} has no verifiable generation because {binding.problem}.")
        revisions = sorted({binding.revision for binding in members if binding.revision})
        if len(revisions) > 1:
            loaded = ", ".join(f"{binding.identity} {short(binding.revision)}" for binding in members if binding.revision)
            lines.append(f"{name}: this session loaded several generations at once ({loaded}), so its behavior is "
                         "not one coherent generation.")
        history = installed.get(repository) or []
        if not history or not revisions:
            continue
        newest = history[-1]["revision"]
        known = {entry["revision"] for entry in history}
        for revision in revisions:
            if revision == newest:
                continue
            if revision in known:
                lines.append(f"{name}: this session runs {short(revision)}, superseded by {short(newest)}, "
                             "the newest revision verified as published main and installed for new sessions.")
            else:
                lines.append(f"{name}: this session runs {short(revision)}, which no verified install recorded; "
                             f"the newest verified install is {short(newest)}.")
    return lines


def adoption(host: str, session_id: str) -> str:
    if host == "claude":
        action = ("To adopt it, ask the user to run /reload-plugins. This check runs again at the next prompt "
                  "and still reports the old revision if the reload did not rebind this session's hooks; then "
                  f"the user restarts it with `claude --resume {session_id}` from a tj-agents terminal.")
    else:
        action = ("Codex cannot reload plugins inside a running process. To adopt it, the user resumes this "
                  f"conversation from a tj-agents terminal with `codex resume {session_id}`; that launch binds the "
                  "newest verified generation.")
    return (f"{action} Until then this session's hooks and skills execute the generation it loaded, and "
            "instructions already loaded into this conversation are unchanged. Its task and ownership are "
            "unchanged.")


def check(host: str, session_id: str, environ: Mapping[str, str], project: Path | None = None,
          now: float | None = None) -> dict[str, object] | None:
    bindings, problems = session_bindings(host, environ, project)
    if not bindings and not problems:
        return None
    installed = installed_generations(environ) if bindings else {}
    if installed is None:
        return None
    lines = [f"this session's generation cannot be verified because {problem}." for problem in problems]
    lines.extend(findings(bindings, installed))
    state = NoticeState(host, session_id, environ, time.time() if now is None else now)
    if not lines:
        state.save(None)
        return None
    report = "plugin generation: " + " ".join(lines)
    output: dict[str, object] = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                        "additionalContext": f"{report} {adoption(host, session_id)}"}}
    key = hashlib.sha256(report.encode("utf-8")).hexdigest()
    if state.notified != key:
        output["systemMessage"] = report
    state.save(key)
    return output


def payload(stream) -> Mapping[str, object]:
    try:
        value = json.loads(stream.read() or "{}")
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def main(argv: list[str] | None = None, environ: Mapping[str, str] | None = None, stdin=None, stdout=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=HOSTS, required=True)
    arguments = parser.parse_args(argv)
    environ = os.environ if environ is None else environ
    stdout = sys.stdout if stdout is None else stdout
    data = payload(sys.stdin if stdin is None else stdin)
    session_id = data.get("session_id")
    if not isinstance(session_id, str) or not SESSION_ID.fullmatch(session_id):
        return 0
    cwd = data.get("cwd")
    project = Path(cwd) if isinstance(cwd, str) and cwd else None
    try:
        output = check(arguments.host, session_id, environ, project)
    except Exception as error:  # noqa: BLE001
        output = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext":
                  f"plugin generation: this session's generation could not be checked ({error})."}}
    if output:
        print(json.dumps(output), file=stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
