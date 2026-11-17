"""Resolve a repository's selected plugins and their published standards."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from tj_cli.git import repository_file

PLUGIN_IDENTITY = re.compile(r"[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\Z")
SKILL_FIELDS = re.compile(
    r"^(name|kind|profile):[ \t]*([a-z][a-z0-9-]*)[ \t]*$", re.MULTILINE
)
STANDARD_KINDS = frozenset({"convention", "contract"})


@dataclass(frozen=True, slots=True)
class PluginSelection:
    path: Path
    sha256: str
    identities: tuple[str, ...]

    @classmethod
    def read(cls, repository: Path) -> PluginSelection | None:
        path = repository_file(repository, ".agents/plugins.json")
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
