"""Keep personal tooling off work surfaces and agent lessons out of host memory.

Personal identifiers come from what this machine installed, never from a written list:
the marketplace that installed Base, each `plugin:skill` it installed, the owners of the
source repositories its plugins record, and the personal accounts and App a bot identity
declares, apart from its human reviewer. A work surface is a repository, or a remote
repository named in a tool call, that an installed employer declaration's origin
predicate matches.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import urlsplit

TEXT_BYTES = 256 * 1024
PATH_TOKENS = 256
PATH_LIKE = re.compile(r"[/\\.~]")
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")
TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|\'[^\']*\'|[^\s;|&<>()]+')
LEADING_CD = re.compile(
    r'^\s*cd\s+(?:/d\s+)?("[^"]+"|\'[^\']+\'|[^\s;&|]+)\s*(?:&&|;|\|\|)'
)
REMOTE_REFERENCE = re.compile(
    r"(?:https?://|git@|ssh://git@)(?P<host>[A-Za-z0-9.-]+)[/:](?P<path>[\w.-]+/[\w.-]+)"
    r"|(?<![\w./:@-])(?P<bare>[A-Za-z0-9][\w.-]*/[\w.-]+)(?![\w/])"
)
FILE_WRITERS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"})
COMMANDS = frozenset({"Bash", "PowerShell", "shell", "exec_command"})
MEMORY_LESSON = (
    "Host memory lives on one machine, so a lesson kept there repeats everywhere else. "
    "Fix the cause in its source instead: a defect in the installed agent tooling "
    "goes through template:self-repair, or `tj item create` in that tooling's own "
    "repository when fixing it now would derail the current task. A fact about a "
    "project belongs in that project's documentation."
)


class HostMemory(Enum):
    CLAUDE = ("projects", "*", "memory")
    CODEX = ("memories",)

    def __init__(self, *parts: str) -> None:
        self.parts = parts

    def holds(self, home: Path, target: Path) -> bool:
        try:
            relative = target.relative_to(home)
        except ValueError:
            return False
        names = relative.parts
        return len(names) > len(self.parts) and all(
            expected in ("*", name)
            for expected, name in zip(self.parts, names, strict=False)
        )


@dataclass(frozen=True, slots=True)
class Identifiers:
    names: tuple[str, ...]

    def find(self, text: str) -> str | None:
        if not self.names or not text:
            return None
        alternatives = "|".join(
            re.escape(name) for name in sorted(self.names, key=len, reverse=True)
        )
        match = re.search(
            rf"(?<![\w.-])(?:{alternatives})(?![\w-])", text, re.IGNORECASE
        )
        return match.group(0) if match else None


@dataclass(frozen=True, slots=True)
class Remote:
    host: str | None
    identity: str


@dataclass(frozen=True, slots=True)
class Outgoing:
    """What a tool call sends, the local paths it targets and the remotes it names."""

    text: str
    targets: tuple[Path, ...]
    remotes: tuple[Remote, ...]


def installed_identifiers(marketplace: Path, identity_file: Path) -> Identifiers:
    """Every name identifying one marketplace's tooling or a personal account."""
    names = {marketplace.name.lower()}
    for plugin in _directories(marketplace):
        for version in _directories(plugin):
            names.update(
                f"{plugin.name}:{skill.name}".lower()
                for skill in _directories(version / "skills")
            )
            names.update(_manifest_owners(version))
    names.update(_personal_accounts(identity_file))
    return Identifiers(tuple(sorted(names)))


def _directories(path: Path) -> Iterator[Path]:
    try:
        entries = list(path.iterdir())
    except OSError:
        return
    yield from (entry for entry in entries if entry.is_dir())


def _manifest_owners(payload: Path) -> Iterator[str]:
    for name in MANIFESTS:
        try:
            data = json.loads((payload / name).read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, ValueError):
            continue
        repository = data.get("repository") if isinstance(data, dict) else None
        if isinstance(repository, dict):
            repository = repository.get("url")
        remote = remote_from_url(repository) if isinstance(repository, str) else None
        if remote is not None:
            yield remote.identity.split("/")[0]


def _personal_accounts(identity_file: Path) -> Iterator[str]:
    try:
        data = json.loads(identity_file.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError):
        return
    if not isinstance(data, dict):
        return
    reviewer = data.get("reviewer")
    reviewer = reviewer.lower() if isinstance(reviewer, str) else ""
    accounts = data.get("accounts")
    for account in accounts if isinstance(accounts, list) else ():
        if isinstance(account, str) and account.lower() != reviewer:
            yield account.lower()
    app = data.get("app")
    slug = app.get("slug") if isinstance(app, dict) else None
    if isinstance(slug, str) and slug:
        yield slug.lower()


def remote_from_url(url: str) -> Remote | None:
    text = url.strip()
    if "://" in text:
        parts = urlsplit(text)
        host, path = parts.hostname, parts.path
    else:
        match = re.fullmatch(r"[^@/:\s]+@([^/:\s]+):(.+)", text)
        if match is None:
            return None
        host, path = match.groups()
    segments = [
        segment
        for segment in path.strip("/").removesuffix(".git").split("/")
        if segment
    ]
    if not host or len(segments) < 2:
        return None
    identity = f"{segments[-2]}/{segments[-1]}".lower()
    return Remote(host.rstrip(".").lower(), identity)


def origin(repository: Path) -> Remote | None:
    """The repository's `origin` remote, read from its Git configuration, not by Git."""
    marker = repository / ".git"
    try:
        if marker.is_file():
            gitdir = Path(
                marker.read_text(encoding="utf-8")
                .strip()
                .removeprefix("gitdir:")
                .strip()
            )
            gitdir = gitdir if gitdir.is_absolute() else repository / gitdir
            common = gitdir / "commondir"
            config = (
                gitdir / common.read_text(encoding="utf-8").strip()
                if common.is_file()
                else gitdir
            ) / "config"
        else:
            config = marker / "config"
        lines = config.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("["):
            section = stripped.replace(" ", "").lower()
            continue
        key, _, value = stripped.partition("=")
        if section == '[remote"origin"]' and key.strip().lower() == "url":
            return remote_from_url(value.strip().strip('"'))
    return None


def remote_matches(node: object, remote: Remote) -> bool:
    """Whether an employer origin predicate matches; only origin facts can match.

    A reference without a host, such as `owner/name` text, matches only through a
    repository-name pattern: its host is unknown, never assumed.
    """
    return _origin_fact(node, remote) is True


def _origin_fact(node: object, remote: Remote) -> bool | None:
    if not isinstance(node, Mapping) or len(node) != 1:
        return False
    operator, value = next(iter(node.items()))
    if operator in ("all", "any") and isinstance(value, list) and value:
        results = [_origin_fact(child, remote) for child in value]
        if operator == "any":
            return True in results
        if False in results:
            return False
        return True if True in results else None
    if operator == "remote_host" and isinstance(value, str):
        return None if remote.host is None else remote.host == value.rstrip(".").lower()
    if operator == "remote":
        patterns = value if isinstance(value, list) else [value]
        return any(
            isinstance(pattern, str) and _searches(pattern, remote.identity)
            for pattern in patterns
        )
    return False


def _searches(pattern: str, text: str) -> bool:
    try:
        return re.search(pattern, text, re.IGNORECASE) is not None
    except re.error:
        return False


def memory_target(
    targets: Iterable[Path], homes: Mapping[HostMemory, Path]
) -> Path | None:
    for target in targets:
        if any(host.holds(home, target) for host, home in homes.items()):
            return target
    return None


def outgoing(
    tool: str, tool_input: Mapping[str, object], cwd: Path, plugin_roots: Sequence[Path]
) -> Outgoing:
    if tool in FILE_WRITERS:
        written = _written(tool, tool_input)
        targets = tuple(_resolved(path, cwd) for path in written)
        return Outgoing("\n".join(written.values()), targets, ())
    if tool in COMMANDS:
        command = tool_input.get("command")
        if isinstance(command, list):
            command = " ".join(part for part in command if isinstance(part, str))
        if isinstance(command, str):
            return _command(command, cwd, plugin_roots)
        return Outgoing("", (), ())
    if tool.startswith("mcp__"):
        strings = list(_strings(tool_input))
        owner, name = tool_input.get("owner"), tool_input.get("repo")
        named = (
            [Remote(None, f"{owner}/{name}".lower())]
            if isinstance(owner, str) and isinstance(name, str)
            else []
        )
        text = "\n".join(strings)
        return Outgoing(text, (), (*named, *_remotes(text)))
    return Outgoing("", (), ())


def _written(tool: str, tool_input: Mapping[str, object]) -> dict[str, str]:
    if tool == "apply_patch":
        command = tool_input.get("command")
        return _patch_additions(command) if isinstance(command, str) else {}
    key = "notebook_path" if tool == "NotebookEdit" else "file_path"
    path = tool_input.get(key)
    if not isinstance(path, str) or not path:
        return {}
    if tool == "MultiEdit":
        edits = tool_input.get("edits")
        texts = (
            [edit.get("new_string") for edit in edits if isinstance(edit, dict)]
            if isinstance(edits, list)
            else []
        )
        return {path: "\n".join(text for text in texts if isinstance(text, str))}
    field = {"Write": "content", "Edit": "new_string", "NotebookEdit": "new_source"}[
        tool
    ]
    value = tool_input.get(field)
    return {path: value if isinstance(value, str) else ""}


def _patch_additions(patch: str) -> dict[str, str]:
    added: dict[str, list[str]] = {}
    current = None
    for line in patch.splitlines():
        header = re.fullmatch(
            r"\*\*\* (?:Update|Add|Delete) File: (.+)|\*\*\* Move to: (.+)", line
        )
        if header is not None:
            current = header.group(1) or header.group(2)
            added.setdefault(current, [])
        elif current is not None and line.startswith("+"):
            added[current].append(line[1:])
    return {path: "\n".join(lines) for path, lines in added.items()}


def _command(command: str, cwd: Path, plugin_roots: Sequence[Path]) -> Outgoing:
    leading = LEADING_CD.match(command)
    directory = _resolved(leading.group(1).strip("\"'"), cwd) if leading else cwd
    kept: list[str] = []
    targets = [directory]
    contents: list[str] = []
    for index, raw in enumerate(TOKEN.findall(command)):
        token = raw.strip("\"'")
        candidates = [token, *token.split("=", 1)[1:], token.removeprefix("@")]
        probed = index < PATH_TOKENS and PATH_LIKE.search(token) is not None
        local = next(
            (
                _resolved(candidate, directory)
                for candidate in candidates
                if probed and _exists(candidate, directory)
            ),
            None,
        )
        if local is None:
            kept.append(raw)
            continue
        targets.append(local)
        if not any(local.is_relative_to(root) for root in plugin_roots):
            contents.append(_text_of(local))
    text = " ".join(kept)
    return Outgoing("\n".join([text, *contents]), tuple(targets), tuple(_remotes(text)))


def _exists(candidate: str, directory: Path) -> bool:
    if not candidate or candidate.startswith("-") or len(candidate) > 1024:
        return False
    try:
        return _resolved(candidate, directory).exists()
    except (OSError, ValueError):
        return False


def _resolved(path: str, cwd: Path) -> Path:
    # PowerShell accepts `\` as a separator on every platform; on POSIX it would
    # otherwise be read as part of a file name.
    raw = Path(path if os.sep == "\\" else path.replace("\\", "/")).expanduser()
    return (raw if raw.is_absolute() else cwd / raw).resolve(strict=False)


def _text_of(path: Path) -> str:
    try:
        if not path.is_file() or path.stat().st_size > TEXT_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _remotes(text: str) -> Iterator[Remote]:
    for match in REMOTE_REFERENCE.finditer(text):
        if match.group("bare"):
            yield Remote(None, match.group("bare").lower())
        else:
            yield Remote(
                match.group("host").lower(),
                match.group("path").removesuffix(".git").lower(),
            )


def memory_reason(target: Path) -> str:
    return (
        f"Blocked: {target} is host memory, which agents do not write. {MEMORY_LESSON}"
    )


def work_reason(identifier: str, surface: str) -> str:
    return (
        f"Blocked: this call carries `{identifier}` onto the work surface {surface}. "
        "Personal tooling and personal projects are never named on a work surface: "
        "not in its files, commits, pull requests, work items, fields, comments or "
        "messages. "
        "Remove the reference and retry."
    )
