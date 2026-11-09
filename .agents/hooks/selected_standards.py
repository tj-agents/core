"""The standards a repository's plugin selection supplies, delivered once per agent."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

PLUGIN_IDENTITY = re.compile(r"[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\Z")
SKILL_FIELDS = re.compile(
    r"^(name|kind|profile):[ \t]*([a-z][a-z0-9-]*)[ \t]*$", re.MULTILINE
)
STANDARD_KINDS = frozenset({"convention", "contract"})
FRONT_MATTER = re.compile(
    r"\A---[ \t]*\r?\n.*?^---[ \t]*\r?(?:\n|\Z)", re.DOTALL | re.MULTILINE
)
LEDGER_DIRECTORY = "standards-injection"
LEDGER_RETENTION_SECONDS = 7 * 24 * 60 * 60
INJECTION_CHARACTERS = 40_000
INJECTION_HEADER = (
    "Stack standards selected by this repository's `.agents/plugins.json` for the "
    "file being written. They govern this write and every later change to that "
    "code; each is injected once per agent."
)


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

    def body(self) -> str:
        text = self.path.read_text(encoding="utf-8-sig")
        return FRONT_MATTER.sub("", text, count=1).strip()


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
class InjectionLedger:
    agent: AgentIdentity
    path: Path

    @classmethod
    def for_agent(cls, state_directory: Path, agent: AgentIdentity) -> InjectionLedger:
        identity = f"{agent.session_id}\0{agent.agent_id}".encode()
        name = hashlib.sha256(identity).hexdigest() + ".json"
        return cls(agent, state_directory / LEDGER_DIRECTORY / name)

    def injected(self) -> frozenset[str]:
        try:
            document = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return frozenset()
        names = document.get("injected") if isinstance(document, dict) else None
        if not isinstance(names, list):
            return frozenset()
        return frozenset(name for name in names if isinstance(name, str))

    def record(self, names: Iterable[str], now: float) -> None:
        created = not self.path.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if created:
            self._prune(now - LEDGER_RETENTION_SECONDS)
        document = {
            "session_id": self.agent.session_id,
            "agent_id": self.agent.agent_id,
            "injected": sorted(self.injected() | set(names)),
        }
        temporary = self.path.with_name(f"{self.path.stem}.{uuid.uuid4().hex}.tmp")
        temporary.write_text(json.dumps(document), encoding="utf-8")
        temporary.replace(self.path)

    def forget(self) -> None:
        self.path.unlink(missing_ok=True)

    def _prune(self, cutoff: float) -> None:
        for entry in self.path.parent.iterdir():
            try:
                if entry.stat().st_mtime < cutoff:
                    entry.unlink()
            except (FileNotFoundError, PermissionError):
                continue


@dataclass(frozen=True, slots=True)
class Injection:
    delivered: tuple[str, ...]
    text: str


def compose_injection(standards: Sequence[Standard], limit: int) -> Injection:
    blocks: list[str] = []
    delivered: list[str] = []
    deferred: list[Standard] = []
    size = 0
    for standard in standards:
        if deferred:
            deferred.append(standard)
            continue
        block = (
            f'<standard name="{standard.name}" source="{standard.path}">\n'
            f"{standard.body()}\n</standard>"
        )
        if blocks and size + len(block) > limit:
            deferred.append(standard)
            continue
        blocks.append(block)
        delivered.append(standard.name)
        size += len(block)
    sections = [INJECTION_HEADER, *blocks]
    if deferred:
        names = ", ".join(f"`{item.name}` ({item.path})" for item in deferred)
        sections.append(
            f"Deferred by the {limit}-character injection bound and injected on "
            f"later writes; read one now when this change depends on it: {names}."
        )
    return Injection(tuple(delivered), "\n\n".join(sections))
