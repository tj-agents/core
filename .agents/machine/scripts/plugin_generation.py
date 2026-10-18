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

from rolling_plugins import SHA, generations_path, read_generations  # noqa: E402

MARKER = ".tj-agents-rolling.json"
RUNTIME_MARKETPLACE = "tj-run-"
RECEIPT_ENV = "TJ_AGENTS_CODEX_RUNTIME_RECEIPT"
RECEIPT_SHA256_ENV = "TJ_AGENTS_CODEX_RUNTIME_RECEIPT_SHA256"
STATE_DIRECTORY_ENV = "AGENT_STATE_DIRECTORY"
SESSION_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
HOSTS = ("claude", "codex")


@dataclass(frozen=True)
class Binding:
    identity: str
    repository: str
    revision: str | None
    root: str
    problem: str | None = None


def state_directory(environ: Mapping[str, str]) -> Path:
    configured = environ.get(STATE_DIRECTORY_ENV)
    return Path(configured) if configured else Path.home() / ".agents-state"


def plugins_root(host: str, environ: Mapping[str, str]) -> Path:
    if host == "claude":
        if environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR"):
            return Path(environ["CLAUDE_CODE_PLUGIN_CACHE_DIR"])
        return Path(environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "plugins"
    return Path(environ.get("CODEX_HOME") or Path.home() / ".codex") / "plugins"


def session_path(host: str, session_id: str, environ: Mapping[str, str]) -> Path:
    return state_directory(environ) / "plugin-generation" / f"{host}-{session_id}.json"


def read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def ownership(root: Path) -> Mapping[str, object] | None:
    value = read_json(root.parent / MARKER)
    if not isinstance(value, dict) or not isinstance(value.get("identity"), str) \
            or not isinstance(value.get("repository"), str):
        return None
    return value


def claude_binding(root: Path) -> Binding | None:
    owner = ownership(root)
    if owner is None:
        return None
    revision = root.name if SHA.fullmatch(root.name) else None
    problem = None if revision else "its install directory does not name a verified revision"
    return Binding(owner["identity"], owner["repository"], revision, str(root), problem)


def codex_binding(root: Path) -> Binding | None:
    owner = ownership(root)
    if owner is None:
        return None
    marketplace = root.parent.parent.name
    if not marketplace.startswith(RUNTIME_MARKETPLACE):
        return Binding(owner["identity"], owner["repository"], None, str(root),
                       "it was not launched through the tj-agents launcher, so its shared install can change under it")
    revision = owner.get("revision")
    if not isinstance(revision, str) or not SHA.fullmatch(revision):
        return Binding(owner["identity"], owner["repository"], None, str(root), "its binding marker names no revision")
    return Binding(owner["identity"], owner["repository"], revision, str(root))


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


def claude_registry_roots(environ: Mapping[str, str], project: Path | None) -> list[str]:
    registry = read_json(plugins_root("claude", environ) / "installed_plugins.json")
    plugins = registry.get("plugins") if isinstance(registry, dict) else None
    roots = []
    for records in plugins.values() if isinstance(plugins, dict) else ():
        applicable = [record for record in records if isinstance(record, dict)
                      and isinstance(record.get("installPath"), str) and applies(record, project)]             if isinstance(records, list) else []
        project_scoped = [record for record in applicable if record.get("scope") in {"project", "local"}]
        chosen = (project_scoped or applicable)[-1:]
        roots.extend(record["installPath"] for record in chosen)
    return roots


def claude_session_roots(environ: Mapping[str, str], project: Path | None) -> list[str]:
    own = environ.get("CLAUDE_PLUGIN_ROOT")
    roots = [root for root in claude_registry_roots(environ, project)
             if not own or Path(root).parent != Path(own).parent]
    if own:
        roots.append(own)
    return sorted(set(roots))


def record_claude_session(session_id: str, environ: Mapping[str, str], project: Path | None) -> None:
    path = session_path("claude", session_id, environ)
    stored = read_json(path)
    stored = stored if isinstance(stored, dict) else {}
    write_json(path, {**stored, "roots": claude_session_roots(environ, project)})


def session_bindings(host: str, session_id: str, environ: Mapping[str, str],
                     project: Path | None = None) -> tuple[list[Binding], list[str]]:
    if host == "claude":
        stored = read_json(session_path("claude", session_id, environ))
        roots = stored.get("roots") if isinstance(stored, dict) else None
        own = environ.get("CLAUDE_PLUGIN_ROOT")
        if isinstance(roots, list) and own and Path(own) not in {Path(root) for root in roots if isinstance(root, str)}:
            record_claude_session(session_id, environ, project)
            roots = claude_session_roots(environ, project)
        if not isinstance(roots, list):
            roots = [own] if own else []
        bindings = [claude_binding(Path(root)) for root in roots if isinstance(root, str)]
        return [binding for binding in bindings if binding is not None], []
    receipt = environ.get(RECEIPT_ENV)
    if receipt:
        try:
            encoded = Path(receipt).read_bytes()
        except OSError as error:
            return [], [f"its Codex runtime receipt could not be read ({error})"]
        if hashlib.sha256(encoded).hexdigest() != environ.get(RECEIPT_SHA256_ENV):
            return [], ["its Codex runtime receipt failed its integrity check"]
        try:
            roots = json.loads(encoded.decode("utf-8")).get("roots")
        except (ValueError, AttributeError):
            roots = None
        if not isinstance(roots, list):
            return [], ["its Codex runtime receipt names no plugin roots"]
    else:
        roots = [environ["PLUGIN_ROOT"]] if environ.get("PLUGIN_ROOT") else []
    bindings = [codex_binding(Path(root)) for root in roots if isinstance(root, str)]
    return [binding for binding in bindings if binding is not None], []


def installed_generations(environ: Mapping[str, str]) -> dict[str, list[dict[str, object]]]:
    by_repository: dict[str, list[dict[str, object]]] = {}
    for host in HOSTS:
        for entry in read_generations(generations_path(plugins_root(host, environ), host)):
            by_repository.setdefault(entry["repository"], []).append({**entry, "host": host})
    for entries in by_repository.values():
        entries.sort(key=lambda entry: entry["installed_at"])
    return by_repository


def short(revision: str | None) -> str:
    return revision[:12] if revision else "unknown"


def stamp(moment: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(moment))


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
        newest = history[-1]
        known = {entry["revision"] for entry in history}
        for revision in revisions:
            if revision == newest["revision"]:
                continue
            if revision in known:
                lines.append(f"{name}: this session runs {short(revision)}, superseded by {short(newest['revision'])}, "
                             f"installed {stamp(newest['installed_at'])} for new {newest['host']} sessions.")
            else:
                lines.append(f"{name}: this session runs {short(revision)}, which no verified install recorded; "
                             f"the newest verified install is {short(newest['revision'])}.")
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


def check(host: str, session_id: str, environ: Mapping[str, str],
          project: Path | None = None) -> dict[str, object] | None:
    bindings, problems = session_bindings(host, session_id, environ, project)
    lines = [f"this session's generation cannot be verified because {problem}." for problem in problems]
    lines.extend(findings(bindings, installed_generations(environ)))
    if not lines:
        return None
    report = "plugin generation: " + " ".join(lines)
    context = f"{report} {adoption(host, session_id)}"
    output: dict[str, object] = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                                        "additionalContext": context}}
    state_path = session_path(host, session_id, environ)
    state = read_json(state_path)
    state = state if isinstance(state, dict) else {}
    key = hashlib.sha256(report.encode("utf-8")).hexdigest()
    if state.get("notified") != key:
        output["systemMessage"] = report
        try:
            write_json(state_path, {**state, "notified": key})
        except OSError:
            pass
    return output


def payload(stream) -> Mapping[str, object]:
    try:
        value = json.loads(stream.read() or "{}")
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def main(argv: list[str] | None = None, environ: Mapping[str, str] | None = None, stdin=None, stdout=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", choices=("session-start", "prompt"))
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
    if arguments.event == "session-start":
        if arguments.host == "claude":
            try:
                record_claude_session(session_id, environ, project)
            except OSError:
                pass
        return 0
    try:
        output = check(arguments.host, session_id, environ, project)
    except Exception as error:  # noqa: BLE001 - an unverifiable session must say so, never pass silently
        output = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext":
                  f"plugin generation: this session's generation could not be checked ({error})."}}
    if output:
        print(json.dumps(output), file=stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
