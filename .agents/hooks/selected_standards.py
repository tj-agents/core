"""The standards a repository's plugin selection requires, and those an agent read."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

PLUGIN_IDENTITY = re.compile(r"[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\Z")
SKILL_FIELDS = re.compile(
    r"^(name|kind|profile):[ \t]*([a-z][a-z0-9-]*)[ \t]*$", re.MULTILINE
)
STANDARD_KINDS = frozenset({"convention", "contract"})
REQUIRED_PROFILES = frozenset({"core", ""})
LEDGER_DIRECTORY = "standards-loaded"
LEDGER_RETENTION_SECONDS = 7 * 24 * 60 * 60


@dataclass(frozen=True, slots=True)
class PluginSelection:
    path: Path
    sha256: str
    identities: tuple[str, ...]

    @classmethod
    def read(cls, repository: Path) -> PluginSelection | None:
        path = repository / ".agents" / "plugins.json"
        try:
            raw = path.read_bytes()
        except FileNotFoundError:
            return None
        invalid = f"Invalid repository plugin selection in {path}"
        try:
            document = json.loads(raw.decode("utf-8-sig"))
        except ValueError as error:
            raise ValueError(invalid) from error
        if not isinstance(document, dict):
            raise ValueError(invalid)
        identities = document.get("plugins")
        marketplaces = document.get("marketplaces")
        if (
            document.get("schema_version") != 1
            or not isinstance(identities, list)
            or not identities
            or not isinstance(marketplaces, dict)
            or any(
                not isinstance(item, str)
                or not PLUGIN_IDENTITY.fullmatch(item)
                or item.partition("@")[2] not in marketplaces
                for item in identities
            )
            or len(set(identities)) != len(identities)
        ):
            raise ValueError(invalid)
        return cls(path, hashlib.sha256(raw).hexdigest(), tuple(identities))


@dataclass(frozen=True, slots=True)
class Standard:
    name: str
    plugin: str
    path: Path
    profile: str

    @property
    def required(self) -> bool:
        return self.profile in REQUIRED_PROFILES


def skill_metadata(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---\n"):
        return {}
    return dict(SKILL_FIELDS.findall(text.split("---", 2)[1]))


def payload_standards(payload: Path, plugin: str, identity: str) -> dict[str, Standard]:
    payload = payload.resolve()
    discovered: list[tuple[Path, dict[str, str]]] = []
    for path in sorted((payload / "skills").glob("*/SKILL.md")):
        if not path.resolve().is_relative_to(payload):
            raise ValueError(f"Skill escapes its selected payload: {path}")
        fields = skill_metadata(path)
        if (
            fields.get("kind") in STANDARD_KINDS
            and fields.get("name") == path.parent.name
        ):
            discovered.append((path, fields))
    canonical: dict[tuple[str, str], list[Path]] = {}
    if discovered:
        for candidate in (payload / ".agents").rglob("SKILL.md"):
            if candidate.resolve().is_relative_to(payload):
                fields = skill_metadata(candidate)
                key = (fields.get("name", ""), fields.get("kind", ""))
                canonical.setdefault(key, []).append(candidate)
    standards = {}
    for path, fields in discovered:
        sources = canonical.get((fields["name"], fields["kind"]), [path])
        if len(sources) > 1:
            raise ValueError(
                f"Ambiguous canonical definition for {plugin}:{fields['name']}"
            )
        name = f"{plugin}:{fields['name']}"
        standards[name] = Standard(
            name, identity, sources[0], fields.get("profile", "")
        )
    return standards


def path_key(path: str, windows: bool) -> str:
    """A comparable spelling of a path; on Windows, case and slashes do not matter."""
    return path.replace("\\", "/").casefold() if windows else path


def standard_key(path: Path) -> str:
    return path_key(str(path), os.name == "nt")


@dataclass(frozen=True, slots=True)
class AgentIdentity:
    session_id: str
    agent_id: str

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> AgentIdentity | None:
        session = payload.get("session_id")
        if not isinstance(session, str) or not session:
            return None
        agent = payload.get("agent_id")
        return cls(session, agent if isinstance(agent, str) else "")


@dataclass(frozen=True, slots=True)
class LoadLedger:
    """The canonical standard files one agent has read, one marker file per path.

    A marker per path keeps concurrent recorders, such as parallel reads, from
    overwriting each other's records.
    """

    agent: AgentIdentity
    directory: Path

    @classmethod
    def for_agent(cls, state_directory: Path, agent: AgentIdentity) -> LoadLedger:
        identity = f"{agent.session_id}\0{agent.agent_id}".encode()
        name = hashlib.sha256(identity).hexdigest()
        return cls(agent, state_directory / LEDGER_DIRECTORY / name)

    def loaded(self, key: str) -> bool:
        return self._marker(key).is_file()

    def record(self, keys: Iterable[str], now: float) -> None:
        keys = list(keys)
        if not keys:
            return
        if not self.directory.is_dir():
            self.directory.parent.mkdir(parents=True, exist_ok=True)
            self._prune(now - LEDGER_RETENTION_SECONDS)
            self.directory.mkdir(exist_ok=True)
        for key in keys:
            self._marker(key).touch()

    def forget(self) -> None:
        shutil.rmtree(self.directory, ignore_errors=True)

    def _marker(self, key: str) -> Path:
        return self.directory / hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _prune(self, cutoff: float) -> None:
        for entry in self.directory.parent.iterdir():
            try:
                if entry.stat().st_mtime < cutoff:
                    shutil.rmtree(entry)
            except (FileNotFoundError, NotADirectoryError, PermissionError):
                continue
