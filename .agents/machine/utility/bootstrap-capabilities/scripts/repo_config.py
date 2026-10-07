#!/usr/bin/env python3
"""Generate project host settings from a committed capability lock."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import subprocess

import harness_permissions
import bootstrap_capabilities as bootstrap


CORE_PLUGINS = {"base-agents/base", "base-agents/engineering", "base-agents/machine"}
MANAGED_START = "# BEGIN repo-declared agent capabilities"
MANAGED_END = "# END repo-declared agent capabilities"
TABLE = re.compile(r"^\s*\[\s*(marketplaces|plugins)(?:\.|\])")
HEADER = re.compile(r"^\s*\[")


def declarations(lock_path: Path, catalog_path: Path) -> tuple[dict[str, dict], dict[str, bool], list[str], list[dict]]:
    catalog = bootstrap.load_json(catalog_path)
    releases, plugins = bootstrap.catalog_index(catalog)
    selections = bootstrap.validate_lock(bootstrap.load_json(lock_path), releases, plugins)
    selected = {selection["id"] for selection in selections}
    missing = sorted(CORE_PLUGINS - selected)
    if missing:
        raise bootstrap.BootstrapError("Repository lock omits core plugins: " + ", ".join(missing))
    sources: dict[str, dict] = {}
    required_plugins: set[str] = set()
    requirements = []
    for selection in selections:
        plugin = plugins[selection["id"]]
        release = plugin["_release"]
        marketplace = release["marketplace"]
        expected = release["owner_repository"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", expected):
            raise bootstrap.BootstrapError(f"Invalid marketplace owner: {marketplace}")
        source = release["source"].removesuffix(".git")
        if source != f"https://github.com/{expected}":
            raise bootstrap.BootstrapError(f"Marketplace source disagrees with catalog owner: {source}")
        prior = sources.get(marketplace)
        if prior is not None and prior["id"] != release["id"]:
            raise bootstrap.BootstrapError(f"Conflicting marketplace releases: {marketplace}")
        sources[marketplace] = release
        requires = plugin.get("harness")
        harness_permissions.validate_requires(requires, selection["id"])
        requirements.append(requires)
    overlay_path = lock_path.resolve().parent / "repository-harness.json"
    if overlay_path.is_file():
        overlay = bootstrap.load_json(overlay_path)
        if not isinstance(overlay, dict) or set(overlay) != {"schema_version", "requires"} or overlay["schema_version"] != 1:
            raise bootstrap.BootstrapError(f"{overlay_path}: invalid repository harness overlay")
        harness_permissions.validate_requires(overlay["requires"], str(overlay_path))
        requirements.append(overlay["requires"])
    for requires in requirements:
        required_plugins.update(requires["plugins"])
        for marketplace in requires["marketplaces"]:
            if not isinstance(marketplace, dict) or set(marketplace) != {"id", "repository"}:
                raise bootstrap.BootstrapError("Invalid required marketplace")
            source_release = sources.get(marketplace["id"])
            if source_release is None or source_release["owner_repository"] != marketplace["repository"]:
                raise bootstrap.BootstrapError(f"Required marketplace disagrees with selected release: {marketplace['id']}")
    missing = sorted(required_plugins - selected)
    if missing:
        raise bootstrap.BootstrapError("Repository lock omits harness-required plugins: " + ", ".join(missing))
    identities = {
        f"{plugin['name']}@{marketplace}": plugin["id"] in selected
        for marketplace, release in sorted(sources.items())
        for plugin in release["plugins"]
    }
    claude_allow, codex_rules = harness_permissions.fold_permissions(requirements)
    claude_allow = [entry for entry in claude_allow if not harness_permissions.contains_template(entry)]
    codex_rules = [rule for rule in codex_rules if not harness_permissions.contains_template(rule)]
    return dict(sorted(sources.items())), dict(sorted(identities.items())), claude_allow, codex_rules


def claude_settings(path: Path, sources: dict[str, dict], identities: dict[str, bool], allow: list[str]) -> str:
    settings = bootstrap.load_json(path) if path.is_file() else {}
    settings["extraKnownMarketplaces"] = {
        name: {"source": {"source": "github", "repo": release["owner_repository"], "ref": release["revision"]}, "autoUpdate": False}
        for name, release in sources.items()
    }
    settings["enabledPlugins"] = identities
    permissions = settings.get("permissions", {})
    if not isinstance(permissions, dict):
        raise bootstrap.BootstrapError(f"{path}: permissions must be an object")
    existing_allow = permissions.get("allow", [])
    if not isinstance(existing_allow, list) or any(not isinstance(entry, str) for entry in existing_allow):
        raise bootstrap.BootstrapError(f"{path}: permissions.allow must be a string list")
    unmanaged_allow = sorted(set(existing_allow) - set(allow))
    if unmanaged_allow:
        raise bootstrap.BootstrapError(f"{path}: unmanaged permissions.allow entries: " + ", ".join(unmanaged_allow))
    permissions["allow"] = allow
    settings["permissions"] = permissions
    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n"


def unmanaged_codex(text: str) -> str:
    if text.count(MANAGED_START) != text.count(MANAGED_END) or text.count(MANAGED_START) > 1:
        raise bootstrap.BootstrapError("Malformed managed section in .codex/config.toml")
    if MANAGED_START in text:
        before, rest = text.split(MANAGED_START, 1)
        _, after = rest.split(MANAGED_END, 1)
        text = before + after.lstrip("\r\n")
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    skip = False
    for line in lines:
        if HEADER.match(line):
            skip = bool(TABLE.match(line))
        if not skip:
            kept.append(line)
    return "".join(kept).rstrip()


def codex_settings(path: Path, sources: dict[str, dict], identities: dict[str, bool]) -> str:
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    prefix = unmanaged_codex(existing)
    return (prefix + "\n\n" if prefix else "") + codex_block(sources, identities)


def codex_block(sources: dict, identities: dict) -> str:
    lines = [MANAGED_START]
    for marketplace, release in sources.items():
        sparse_paths = sorted({".agents/plugins", ".claude-plugin", *(
            plugin["package_path"].split("/", 1)[0] for plugin in release["plugins"]
        )})
        lines += [f"[marketplaces.{marketplace}]", 'source_type = "git"',
                  f'source = "https://github.com/{release["owner_repository"]}.git"',
                  f'ref = "{release["revision"]}"',
                  f"sparse_paths = {json.dumps(sparse_paths)}", ""]
    for identity, enabled in identities.items():
        lines += [f'[plugins."{identity}"]', f"enabled = {str(enabled).lower()}", ""]
    lines.append(MANAGED_END)
    return "\n".join(lines) + "\n"


def codex_rules(rules: list[dict]) -> str:
    lines = ["# Generated from repository-declared agent harness requirements.", ""]
    lines += harness_permissions.codex_rule_lines(rules)
    return "\n".join(lines)


LOCAL_STATE = ".agents/repo-capabilities.local.json"
EXCLUDE_START = "# BEGIN local repo-declared agent capabilities"
EXCLUDE_END = "# END local repo-declared agent capabilities"


def contained(root: Path, path: Path) -> Path:
    candidate = path if path.is_absolute() else root / path
    candidate = candidate.parent.resolve() / candidate.name
    if not candidate.is_relative_to(root) or not candidate.resolve().is_relative_to(root):
        raise bootstrap.BootstrapError(f"Target escapes repository root: {candidate}")
    for ancestor in candidate.parents:
        if ancestor == root:
            break
        if ancestor.exists() and not ancestor.is_dir():
            raise bootstrap.BootstrapError(f"Target parent is not a directory: {ancestor}")
    if candidate.exists() and not candidate.is_file():
        raise bootstrap.BootstrapError(f"Target is not a file: {candidate}")
    if candidate.is_file() and candidate.stat().st_nlink > 1:
        raise bootstrap.BootstrapError(f"Target has multiple hard links: {candidate}")
    return candidate


def file_identity(path: Path):
    if not path.exists():
        return None
    stat = path.stat()
    return stat.st_dev, stat.st_ino


def validate_aliases(targets: list[Path], read_paths: list[Path]) -> None:
    canonical = set()
    identities = set()
    inputs = {path.resolve() for path in read_paths}
    input_identities = {identity for path in read_paths if (identity := file_identity(path)) is not None}
    for path in targets:
        resolved = path.resolve()
        identity = file_identity(path)
        if resolved in canonical or identity is not None and identity in identities:
            raise bootstrap.BootstrapError("Repository configuration targets alias the same file")
        if resolved in inputs or identity is not None and identity in input_identities:
            raise bootstrap.BootstrapError(f"Repository configuration target aliases a read input: {path}")
        canonical.add(resolved)
        if identity is not None:
            identities.add(identity)


def preflight_paths(root: Path, paths: list[Path], *, scope: str = "local", read_paths: list[Path] = (), run=subprocess.run) -> Path | None:
    if scope not in {"project", "local"}:
        raise bootstrap.BootstrapError(f"Unknown repository scope: {scope}")
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise bootstrap.BootstrapError(f"Repository root does not exist: {root}")
    targets = [contained(root, path) for path in paths]
    exclude = None
    if not (root / ".git").exists():
        if any((parent / ".git").exists() for parent in root.parents):
            raise bootstrap.BootstrapError(f"Root is not the exact Git checkout: {root}")
    else:
        top = Path(bootstrap.git(run, ["rev-parse", "--show-toplevel"], root)).resolve()
        if top != root:
            raise bootstrap.BootstrapError(f"Root is not the exact Git checkout: {root}")
        if scope == "local":
            tracked_paths = sorted({relative for path in targets for relative in (path.relative_to(root).as_posix(), path.resolve().relative_to(root).as_posix())})
            tracked = bootstrap.git(run, ["ls-files", "--cached", "-z", "--", *tracked_paths], root)
            if tracked:
                raise bootstrap.BootstrapError("Local targets are tracked: " + tracked.replace("\0", ", "))
            common = Path(bootstrap.git(run, ["rev-parse", "--path-format=absolute", "--git-common-dir"], root)).resolve()
            exclude = Path(bootstrap.git(run, ["rev-parse", "--git-path", "info/exclude"], root))
            if not exclude.is_absolute():
                exclude = root / exclude
            if not exclude.resolve().is_relative_to(common):
                raise bootstrap.BootstrapError(f"Git exclusion target escapes Git metadata: {exclude}")
            contained(common, exclude)
    validate_aliases([*targets, *([exclude] if exclude is not None else [])], read_paths)
    return exclude


def text_at(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.is_file() else None


def local_state(path: Path) -> dict:
    if not path.is_file():
        return {"schema_version": 1, "claude": {}, "codex": None, "rules": None}
    state = bootstrap.load_json(path)
    if set(state) != {"schema_version", "claude", "codex", "rules"} or state["schema_version"] != 1:
        raise bootstrap.BootstrapError(f"{path}: invalid local ownership state")
    if not isinstance(state["claude"], dict) or any(state[key] is not None and not isinstance(state[key], str) for key in ("codex", "rules")):
        raise bootstrap.BootstrapError(f"{path}: invalid local ownership state")
    for key, value in state["claude"].items():
        if key not in {"extraKnownMarketplaces", "enabledPlugins", "allow"}:
            raise bootstrap.BootstrapError(f"{path}: invalid Claude ownership key")
        if key == "allow":
            bootstrap.require_string_list(value, "owned Claude approvals")
        elif not isinstance(value, dict) or any(not isinstance(record, dict) or set(record) != {"present", "before", "written"} or not isinstance(record["present"], bool) for record in value.values()):
            raise bootstrap.BootstrapError(f"{path}: invalid Claude ownership records")
    return state


def local_claude(path: Path, sources: dict, identities: dict, allow: list[str], previous: dict) -> tuple[str, dict]:
    settings = bootstrap.load_json(path) if path.is_file() else {}
    wanted = {
        "extraKnownMarketplaces": {name: {"source": {"source": "github", "repo": release["owner_repository"], "ref": release["revision"]}, "autoUpdate": False} for name, release in sources.items()},
        "enabledPlugins": identities,
    }
    owned = {}
    for key, desired in wanted.items():
        current = settings.get(key, {})
        if not isinstance(current, dict):
            raise bootstrap.BootstrapError(f"{path}: {key} must be an object")
        records = previous.get(key, {})
        for name, record in records.items():
            if name not in current or current[name] != record["written"]:
                raise bootstrap.BootstrapError(f"{path}: owned setting was changed: {key}.{name}")
            if record["present"]:
                current[name] = record["before"]
            else:
                current.pop(name, None)
        owned[key] = {}
        for name, value in desired.items():
            if name not in current or current[name] != value:
                owned[key][name] = {"present": name in current, "before": current.get(name), "written": value}
                current[name] = value
        settings[key] = current
    permissions = settings.get("permissions", {})
    if not isinstance(permissions, dict):
        raise bootstrap.BootstrapError(f"{path}: permissions must be an object")
    existing = permissions.get("allow", [])
    bootstrap.require_string_list(existing, "Claude approvals")
    survivors = [entry for entry in existing if entry not in previous.get("allow", [])]
    owned["allow"] = [entry for entry in allow if entry not in survivors]
    permissions["allow"] = survivors + owned["allow"]
    settings["permissions"] = permissions
    return json.dumps(settings, indent=2, ensure_ascii=False) + "\n", owned


def local_codex(path: Path, sources: dict, identities: dict, previous: str | None) -> tuple[str, str]:
    try:
        import tomllib
    except ImportError as error:
        raise bootstrap.BootstrapError("Local repository settings require Python 3.11 or newer") from error
    existing = text_at(path) or ""
    if existing.count(MANAGED_START) != existing.count(MANAGED_END) or existing.count(MANAGED_START) > 1 or (MANAGED_START in existing and existing.index(MANAGED_START) > existing.index(MANAGED_END)):
        raise bootstrap.BootstrapError("Malformed managed section in .codex/config.toml")
    if MANAGED_START in existing:
        before, rest = existing.split(MANAGED_START, 1)
        body, after = rest.split(MANAGED_END, 1)
        block = MANAGED_START + body + MANAGED_END + "\n"
        if previous != block:
            raise bootstrap.BootstrapError("Codex managed section is not owned or was changed")
        prefix = before + after.lstrip("\r\n")
    else:
        prefix = existing
    try:
        parsed = tomllib.loads(prefix)
    except tomllib.TOMLDecodeError as error:
        raise bootstrap.BootstrapError(f"{path}: invalid unmanaged TOML: {error}") from error
    for key, desired in (("marketplaces", sources), ("plugins", identities)):
        foreign = parsed.get(key, {})
        if not isinstance(foreign, dict) or set(foreign) & set(desired):
            raise bootstrap.BootstrapError(f"{path}: unmanaged {key} collision")
    block = codex_block(sources, identities)
    expected = (prefix.rstrip() + "\n\n" if prefix.strip() else "") + block
    try:
        tomllib.loads(expected)
    except tomllib.TOMLDecodeError as error:
        raise bootstrap.BootstrapError(f"{path}: conflicting TOML tables: {error}") from error
    return expected, block


def exclusion_text(path: Path, root: Path, targets: list[Path]) -> str:
    existing = text_at(path) or ""
    owner = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()
    relatives = {relative for target in targets for relative in (target.relative_to(root).as_posix(), target.resolve().relative_to(root).as_posix())}
    patterns = {"/" + re.sub(r"([*?\[\] ])", r"\\\1", relative) for relative in relatives}
    block = "\n".join([EXCLUDE_START + " " + owner, *sorted(patterns), EXCLUDE_END + " " + owner]) + "\n"
    kept = []
    active = None
    owners = set()
    for line in existing.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        if stripped.startswith(EXCLUDE_START):
            suffix = stripped[len(EXCLUDE_START):]
            if active is not None or suffix in owners or suffix and not re.fullmatch(r" [a-f0-9]{64}", suffix):
                raise bootstrap.BootstrapError(f"{path}: malformed managed exclusions")
            active = suffix
            owners.add(suffix)
            if suffix == " " + owner:
                kept.append(block)
        elif stripped.startswith(EXCLUDE_END):
            if active is None or stripped != EXCLUDE_END + active:
                raise bootstrap.BootstrapError(f"{path}: malformed managed exclusions")
            if active != " " + owner:
                kept.append(line)
            active = None
            continue
        if active != " " + owner:
            kept.append(line)
    if active is not None:
        raise bootstrap.BootstrapError(f"{path}: malformed managed exclusions")
    existing = "".join(kept)
    if " " + owner in owners:
        return existing
    return existing + ("\n" if existing and not existing.endswith("\n") else "") + block


def plan(lock_path: Path, catalog_path: Path, *, root: Path | None = None, scope: str = "project", prospective_paths: list[Path] = (), execute=subprocess.run) -> dict[Path, str | None]:
    if scope not in {"project", "local"}:
        raise bootstrap.BootstrapError(f"Unknown repository scope: {scope}")
    root = (root or lock_path.resolve().parent.parent).expanduser().resolve()
    claude = root / ".claude" / ("settings.local.json" if scope == "local" else "settings.json")
    codex = root / ".codex/config.toml"
    rules_path = root / ".codex/rules/agent-harness.rules"
    state_path = root / LOCAL_STATE
    paths = [claude, codex, rules_path] + ([state_path] if scope == "local" else [])
    inputs = [lock_path, catalog_path, lock_path.resolve().parent / "repository-harness.json"]
    exclude = preflight_paths(root, [*paths, *prospective_paths], scope=scope, read_paths=inputs, run=execute)
    sources, identities, allow, rules = declarations(lock_path, catalog_path)
    expected_rules = codex_rules(rules) if rules else None
    if scope == "local":
        state = local_state(state_path)
        claude_text, claude_owned = local_claude(claude, sources, identities, allow, state["claude"])
        codex_text, codex_owned = local_codex(codex, sources, identities, state["codex"])
        actual_rules = text_at(rules_path)
        if actual_rules is not None and actual_rules != state["rules"]:
            raise bootstrap.BootstrapError(f"{rules_path}: harness rules are not owned or were changed")
        updated = {"schema_version": 1, "claude": claude_owned, "codex": codex_owned, "rules": expected_rules}
        targets = {claude: claude_text, codex: codex_text, rules_path: expected_rules, state_path: json.dumps(updated, indent=2, ensure_ascii=False) + "\n"}
        if exclude is not None:
            targets[exclude] = exclusion_text(exclude, root, [*paths, *[contained(root, path) for path in prospective_paths]])
    else:
        targets = {claude: claude_settings(claude, sources, identities, allow), codex: codex_settings(codex, sources, identities), rules_path: expected_rules}
    for path in targets:
        text_at(path)
    return targets


def write_batch(targets: dict[Path, str | None]) -> None:
    originals = {path: path.read_bytes() if path.is_file() else None for path in targets}
    attempted = []
    try:
        for path, expected in targets.items():
            attempted.append(path)
            if expected is None:
                path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(expected, encoding="utf-8")
    except BaseException as error:
        failures = []
        for path in reversed(attempted):
            before = originals[path]
            try:
                actual = path.read_bytes() if path.is_file() else None
                if actual == before:
                    continue
                if before is None:
                    path.unlink()
                else:
                    path.write_bytes(before)
            except OSError as rollback_error:
                failures.append(f"{path}: {rollback_error}")
        if failures:
            raise bootstrap.BootstrapError("Repository configuration rollback failed: " + "; ".join(failures)) from error
        raise


def run(lock_path: Path, catalog_path: Path, mode: str, *, root: Path | None = None, scope: str = "project") -> list[str]:
    if mode not in {"write", "check", "preview"}:
        raise bootstrap.BootstrapError(f"Unknown repository mode: {mode}")
    root = (root or lock_path.resolve().parent.parent).expanduser().resolve()
    targets = plan(lock_path, catalog_path, root=root, scope=scope)
    changed = {path: expected for path, expected in targets.items() if text_at(path) != expected}
    drift = [path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path) for path in changed]
    if mode == "write":
        write_batch(changed)
    return drift


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--mode", required=True, choices=("write", "check", "preview"))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--scope", choices=("project", "local"), default="project")
    args = parser.parse_args(argv)
    try:
        catalog = args.catalog or bootstrap.catalog_for_lock(args.lock, Path(__file__).resolve())
        drift = run(args.lock, catalog, args.mode, root=args.root, scope=args.scope)
    except (bootstrap.BootstrapError, OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if drift:
        print(("Updated" if args.mode == "write" else "Would update" if args.mode == "preview" else "Drift in") + ": " + ", ".join(drift))
    return int(args.mode == "check" and bool(drift))


if __name__ == "__main__":
    raise SystemExit(main())
