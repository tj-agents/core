import hashlib
import importlib.util
import json
import os
import re
import stat
from pathlib import Path


class SkillSourceError(RuntimeError):
    pass


_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_QUALIFIED = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):([A-Za-z0-9][A-Za-z0-9_.-]*)$")
_CANONICAL_LINK = re.compile(r"\[canonical shared definition\]\(([^)]+)\)")
_ROUTER = None


def _router():
    global _ROUTER
    if _ROUTER is not None:
        return _ROUTER
    path = Path(__file__).resolve().parents[1] / "hooks" / "skill_router.py"
    spec = importlib.util.spec_from_file_location("installed_skill_router", path)
    if spec is None or spec.loader is None:
        raise SkillSourceError("native skill inventory helper is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _ROUTER = module
    return module


def _error(reference, reason):
    raise SkillSourceError(f"skill {reference!r}: {reason}")


def _safe_name(value, reference, label):
    if not isinstance(value, str) or not _NAME.fullmatch(value):
        _error(reference, f"invalid {label}")
    return value


def _relative(value, reference, label, allow_parent=False):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        _error(reference, f"invalid {label}")
    path = Path(value)
    if path.is_absolute() or any(part in {"", "."} for part in path.parts):
        _error(reference, f"invalid {label}")
    if not allow_parent and ".." in path.parts:
        _error(reference, f"invalid {label}")
    return path


def _contained(root, path, reference, label):
    try:
        path.relative_to(root)
    except ValueError:
        _error(reference, f"{label} escapes its declared package")
    return path


def _redirect(path):
    metadata = path.lstat()
    attributes = getattr(metadata, "st_file_attributes", 0)
    return path.is_symlink() or stat.S_ISLNK(metadata.st_mode) or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def _safe_existing(root, path, reference, label):
    _contained(root, path, reference, label)
    current = root
    if _redirect(current):
        _error(reference, f"{label} has a redirected package root")
    for part in path.relative_to(root).parts:
        current /= part
        if not current.exists() or _redirect(current):
            _error(reference, f"{label} is missing or redirected")
    return current


def _raw_hash(path):
    data = path.read_bytes()
    return data, hashlib.sha256(data).hexdigest()


def _front_matter_name(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return None
    match = re.match(r"^---\r?\n.*?^name:\s*([^\r\n]+)\r?$.*?^---\r?$", text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else None


def _local_path(root, value, reference):
    relative = _relative(value, reference, "repository-local path")
    candidate = root / relative
    path = _safe_existing(root, candidate, reference, "repository-local path")
    if not path.is_file():
        _error(reference, "repository-local body does not exist")
    return path, relative.as_posix()


def _local_candidates(root, bare):
    legacy = root / ".agents" / "skills" / bare / "SKILL.md"
    if legacy.is_file():
        return [legacy]
    declared = root / ".agents" / "plugins" / "sources.json"
    roots = []
    if declared.is_file():
        try:
            scopes = json.loads(declared.read_text(encoding="utf-8")).get("scopes", [])
        except (OSError, ValueError):
            _error(bare, "local sources declaration is invalid")
        for scope in scopes:
            value = scope.get("root") if isinstance(scope, dict) else None
            if not isinstance(value, str):
                _error(bare, "local sources declaration is invalid")
            relative = _relative(value, bare, "local source root")
            candidate = root / relative
            _safe_existing(root, candidate, bare, "local source root")
            roots.append(candidate)
    else:
        agents = root / ".agents"
        roots = [path for path in agents.iterdir() if path.is_dir() and not path.name.startswith(".")] if agents.is_dir() else []
    candidates = []
    for owner in roots:
        for kind in owner.iterdir():
            if not kind.is_dir():
                continue
            candidate = kind / bare / "SKILL.md"
            if candidate.is_file():
                safe = _safe_existing(root, candidate, bare, "local canonical skill")
                if _front_matter_name(safe) == bare:
                    candidates.append(safe)
    return candidates


def _resolve_local(reference, repository_root, local_body_root):
    if "=" in reference:
        name, raw_path = reference.split("=", 1)
        _safe_name(name, reference, "skill name")
        path, relative = _local_path(local_body_root, raw_path, reference)
    else:
        if ":" in reference:
            return None
        _safe_name(reference, reference, "skill name")
        candidates = _local_candidates(local_body_root, reference)
        if not candidates:
            return None
        if len(candidates) != 1:
            _error(reference, "local canonical skill is ambiguous")
        path = candidates[0]
        relative = path.relative_to(local_body_root).as_posix()
    _, body_hash = _raw_hash(path)
    return {
        "name": reference.split("=", 1)[0],
        "resolved_name": reference.split("=", 1)[0],
        "source_type": "repository_local",
        "path": relative,
        "sha256": body_hash,
        "body_path": relative,
        "body_sha256": body_hash,
        "resolved_path": str(path),
    }


def _scope_rank(record, project_root, reference):
    scope = record.get("scope")
    project_path = record.get("projectPath")
    if scope is not None and not isinstance(scope, str):
        _error(reference, "native scope is invalid")
    if project_path is not None and not isinstance(project_path, str):
        _error(reference, "native project scope is invalid")
    normalized = str(project_root.resolve())
    if project_path is not None and os.path.normcase(str(Path(project_path).resolve())) != os.path.normcase(normalized):
        if str(scope or "").lower() in {"project", "local"}:
            return None
        _error(reference, "native project metadata contradicts the query context")
    lowered = str(scope or "").lower()
    if lowered in {"project", "local"}:
        if project_path is None:
            _error(reference, "native project scope has no project path")
        return 2
    if lowered in {"user", "managed", "global"}:
        return 1
    return 0


def _plugin_parts(record, host, reference):
    if host == "codex":
        name = record.get("name")
        marketplace = record.get("marketplaceName")
        plugin_id = record.get("pluginId")
        if not isinstance(name, str) or not isinstance(marketplace, str):
            if isinstance(plugin_id, str) and "@" in plugin_id:
                name, marketplace = plugin_id.rsplit("@", 1)
            else:
                _error(reference, "native Codex record lacks plugin identity")
    else:
        plugin_id = record.get("id") or record.get("pluginId")
        if not isinstance(plugin_id, str) or "@" not in plugin_id:
            _error(reference, "native Claude record lacks plugin identity")
        name, marketplace = plugin_id.rsplit("@", 1)
    return _safe_name(name, reference, "plugin name"), _safe_name(marketplace, reference, "marketplace name")


def _select_native(plugin, host, project_root, inventory):
    wanted_name = _safe_name(plugin, plugin, "plugin name")
    owners = {}
    enabled_owners = {}
    for record in inventory:
        if not isinstance(record, dict):
            continue
        name, marketplace = _plugin_parts(record, host, plugin)
        if name != wanted_name:
            continue
        owners.setdefault((name, marketplace), []).append(record)
        if record.get("enabled") is True and not (host == "codex" and record.get("installed") is False):
            enabled_owners.setdefault((name, marketplace), []).append(record)
    if not owners:
        _error(plugin, "native owner is absent")
    if not enabled_owners:
        _error(plugin, "native owner is disabled or unavailable")
    if len(enabled_owners) != 1:
        _error(plugin, "enabled native installation is ambiguous across marketplaces")
    candidates = []
    owner_name, owner_marketplace = next(iter(enabled_owners))
    for record in enabled_owners[(owner_name, owner_marketplace)]:
        rank = _scope_rank(record, project_root, plugin)
        if rank is not None:
            candidates.append((rank, owner_name, owner_marketplace, record))
    if not candidates:
        _error(plugin, "native owner is disabled or unavailable")
    highest = max(item[0] for item in candidates)
    candidates = [item for item in candidates if item[0] == highest]
    locations = {(item[1], item[2], str(item[3].get("installPath") or "")) for item in candidates}
    if len(candidates) != 1 or len(locations) != 1:
        _error(plugin, "enabled native installation is ambiguous")
    _, name, marketplace, record = candidates[0]
    return name, marketplace, record


def _package_root(host, name, marketplace, record, reference):
    if host == "claude":
        value = record.get("installPath")
        if not isinstance(value, str):
            _error(reference, "native Claude record lacks installPath")
        root = Path(value)
    else:
        version = record.get("version")
        if not isinstance(version, str) or not _NAME.fullmatch(version):
            _error(reference, "native Codex record has an unsafe version")
        home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        root = home / "plugins" / "cache" / marketplace / name / version
    if not root.is_absolute() or not root.is_dir() or _redirect(root):
        _error(reference, "native installation root is unavailable or redirected")
    return root.resolve()


def _manifest(root, host, reference):
    names = (f".{host}-plugin/plugin.json", "plugin.json")
    matches = [root / name for name in names if (root / name).is_file()]
    if len(matches) > 1:
        _error(reference, "installation has conflicting manifests")
    if not matches:
        return None, None
    path = _safe_existing(root, matches[0], reference, "manifest")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        _error(reference, f"manifest is invalid: {error}")
    if not isinstance(value, dict):
        _error(reference, "manifest is invalid")
    return path, value


def _roots(root, manifest, host, reference):
    if manifest is None or "skills" not in manifest:
        candidate = root / "skills"
        _safe_existing(root, candidate, reference, "native default skills root")
        return [candidate], "native-default"
    values = manifest["skills"] if isinstance(manifest["skills"], list) else [manifest["skills"]]
    if not values or not all(isinstance(item, str) for item in values):
        _error(reference, "manifest skills declaration is invalid")
    roots = []
    for value in values:
        relative = _relative(value.removeprefix("./"), reference, "manifest skills root")
        candidate = root / relative
        _safe_existing(root, candidate, reference, "manifest skills root")
        if candidate in roots:
            _error(reference, "manifest has duplicate skills roots")
        roots.append(candidate)
    return roots, "manifest"


def _canonical_body(root, entry, reference):
    entry_data, entry_hash = _raw_hash(entry)
    try:
        text = entry_data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return entry, entry_hash, entry_hash
    links = _CANONICAL_LINK.findall(text)
    if not links:
        return entry, entry_hash, entry_hash
    if len(links) != 1:
        _error(reference, "generated canonical definition link is ambiguous")
    relative = _relative(links[0], reference, "generated canonical definition link", allow_parent=True)
    parts = list(entry.parent.relative_to(root).parts)
    for part in relative.parts:
        if part == "..":
            if not parts:
                _error(reference, "generated canonical definition link escapes its declared package")
            parts.pop()
        else:
            parts.append(part)
    candidate = root.joinpath(*parts)
    _contained(root, candidate, reference, "generated canonical definition link")
    body = _safe_existing(root, candidate, reference, "generated canonical definition link")
    if not body.is_file():
        _error(reference, "generated canonical definition target is not a file")
    _, body_hash = _raw_hash(body)
    return body, entry_hash, body_hash


def resolve_installed_skill(plugin, bare_name, host, project_root, inventory):
    if host not in {"codex", "claude"}:
        _error(plugin, "an explicit host is required for installed skills")
    name, marketplace, record = _select_native(plugin, host, Path(project_root), inventory)
    bare = _safe_name(bare_name, plugin, "skill name")
    root = _package_root(host, name, marketplace, record, plugin)
    manifest_path, manifest = _manifest(root, host, plugin)
    if manifest is not None and manifest.get("name") not in {None, name}:
        _error(plugin, "manifest name does not match the native plugin")
    roots, declaration_method = _roots(root, manifest, host, plugin)
    matches = []
    for skill_root in roots:
        candidate = skill_root / bare / "SKILL.md"
        if candidate.is_file():
            matches.append(_safe_existing(root, candidate, plugin, "declared skill entry"))
    if len(matches) != 1:
        _error(plugin, "declared skill entry is missing or ambiguous")
    entry = matches[0]
    body, entry_hash, body_hash = _canonical_body(root, entry, plugin)
    native_version = record.get("version") if isinstance(record.get("version"), str) else None
    native_revision = record.get("revision") if isinstance(record.get("revision"), str) else None
    scope = record.get("scope") if isinstance(record.get("scope"), str) else "native-effective"
    project = record.get("projectPath") if isinstance(record.get("projectPath"), str) else str(Path(project_root).resolve())
    source = record.get("source") if isinstance(record.get("source"), (str, dict, list)) else None
    resolved_name = f"{name}:{bare}"
    return {
        "name": f"{name}:{bare}",
        "requested_name": f"{plugin}:{bare}",
        "resolved_name": resolved_name,
        "source_type": "installed_plugin",
        "path": body.relative_to(root).as_posix(),
        "sha256": body_hash,
        "host": host,
        "plugin_id": f"{name}@{marketplace}",
        "marketplace": marketplace,
        "native_version": native_version,
        "native_revision": native_revision,
        "native_scope": scope,
        "project_path": project,
        "advertised_source": source,
        "declaration_method": declaration_method,
        "manifest_path": manifest_path.relative_to(root).as_posix() if manifest_path else None,
        "manifest_sha256": _raw_hash(manifest_path)[1] if manifest_path else None,
        "manifest_version": manifest.get("version") if isinstance(manifest, dict) and isinstance(manifest.get("version"), str) else None,
        "entry_path": entry.relative_to(root).as_posix(),
        "entry_sha256": entry_hash,
        "body_path": body.relative_to(root).as_posix(),
        "body_sha256": body_hash,
        "resolved_path": str(body),
        "package_root": str(root),
    }


def resolve_skill(reference, repository_root, local_body_root, host=None, inventory=None):
    if not isinstance(reference, str) or not reference:
        _error(str(reference), "skill reference is invalid")
    local = _resolve_local(reference, Path(repository_root), Path(local_body_root))
    if local is not None:
        return local
    if "=" in reference:
        _error(reference, "repository-local body does not exist")
    if host is None:
        _error(reference, "no unique repository-local skill exists")
    inventory = _router().native_plugin_inventory(host, repository_root) if inventory is None else inventory
    match = _QUALIFIED.fullmatch(reference)
    if match is None:
        bare = _safe_name(reference, reference, "skill name")
        owners = sorted({
            _plugin_parts(record, host, reference)[0]
            for record in inventory
            if isinstance(record, dict) and record.get("enabled") is True
            and not (host == "codex" and record.get("installed") is False)
        })
        matches = []
        for owner in owners:
            try:
                matches.append(resolve_installed_skill(owner, bare, host, repository_root, inventory))
            except SkillSourceError as error:
                if "declared skill entry is missing" not in str(error):
                    raise
        if len(matches) != 1:
            _error(reference, "installed declared skill is missing or ambiguous")
        matches[0]["name"] = reference
        matches[0]["requested_name"] = reference
        return matches[0]
    try:
        return resolve_installed_skill(match.group(1), match.group(2), host, repository_root, inventory)
    except SkillSourceError as direct:
        alias = _router().skill_aliases().get(reference)
        if "native owner is absent" not in str(direct) or alias is None or not _QUALIFIED.fullmatch(alias):
            raise direct
        target = _QUALIFIED.fullmatch(alias)
        record = resolve_installed_skill(target.group(1), target.group(2), host, repository_root, inventory)
        record["alias_from"] = reference
        record["name"] = reference
        record["requested_name"] = reference
        return record


def identity_key(record):
    if record.get("source_type") == "repository_local":
        return tuple(record.get(key) for key in ("kind", "name", "path", "sha256"))
    fields = (
        "kind", "name", "requested_name", "resolved_name", "source_type", "host", "plugin_id", "marketplace",
        "native_version", "native_revision", "native_scope", "project_path", "advertised_source", "declaration_method",
        "manifest_path", "manifest_sha256", "manifest_version", "entry_path", "entry_sha256", "body_path", "body_sha256",
        "alias_from",
    )
    return tuple(json.dumps(record.get(field), sort_keys=True, separators=(",", ":")) for field in fields)


def validate_pinned_installed_rules(records, host, project_root):
    if not isinstance(records, list):
        raise SkillSourceError("installed rules are invalid")
    inventory = _router().native_plugin_inventory(host, project_root)
    for pinned in records:
        if not isinstance(pinned, dict) or pinned.get("source_type") != "installed_plugin":
            raise SkillSourceError("installed rules are invalid")
        reference = pinned.get("name")
        if not isinstance(reference, str):
            raise SkillSourceError("installed rule identity is invalid")
        current = resolve_skill(reference, project_root, project_root, host, inventory)
        if identity_key(current) != identity_key(pinned):
            raise SkillSourceError("installed rule identity changed; start a fresh review run")
