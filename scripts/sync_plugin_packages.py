"""Build self-contained plugin payloads from shared definitions and host adapters."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


FRONTMATTER = re.compile(r"\A---\n(?P<header>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)
DEFAULT_HANDOFF_SKILLS = frozenset({"cd", "handoff", "handoff-codex"})


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def load(path: Path):
    return json.loads(read(path))


def validate_hook_outputs(output: dict[str, bytes], config: dict, plugins: set[str]) -> None:
    known_roots = ("${PLUGIN_ROOT}", "%PLUGIN_ROOT%", "${CLAUDE_PLUGIN_ROOT}", "os.environ['PLUGIN_ROOT']")
    host_fields = {
        "codex": (
            ("command", "${PLUGIN_ROOT}", re.compile(r"\$\{PLUGIN_ROOT\}/([^\"']+)")),
            (
                "commandWindows",
                "${PLUGIN_ROOT}",
                re.compile(r"\$\{PLUGIN_ROOT\}/([^\"']+)"),
            ),
        ),
        "claude": (
            ("command", "${CLAUDE_PLUGIN_ROOT}", re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"'@]+)")),
        ),
    }
    exec_form_hosts = {"claude"}
    declarations = config.get("host_hook_sources", {})
    for plugin in plugins:
        declared = declarations.get(plugin, {})
        shipped = set()
        for path, data in output.items():
            if path.startswith(f"plugins/{plugin}/hooks/") and path.endswith(".json"):
                payload = json.loads(data)
                if isinstance(payload, dict) and isinstance(payload.get("hooks"), dict):
                    shipped.add(path)
        expected = {f"plugins/{plugin}/hooks/{host}.json" for host in declared}
        if shipped != expected:
            raise ValueError(f"{plugin}: shipped hooks disagree with source map")
        for host, fields in host_fields.items():
            manifest_path = f"plugins/{plugin}/.{host}-plugin/plugin.json"
            manifest = json.loads(output[manifest_path])
            pointer = manifest.get("hooks")
            if host not in declared:
                if pointer is not None:
                    raise ValueError(f"{manifest_path}: undeclared hook pointer")
                continue
            expected_pointer = f"./hooks/{host}.json"
            if pointer != expected_pointer:
                raise ValueError(f"{manifest_path}: hook pointer must be {expected_pointer}")
            relative_pointer = PurePosixPath(pointer)
            if relative_pointer.is_absolute() or ".." in relative_pointer.parts:
                raise ValueError(f"{manifest_path}: hook pointer escapes package")
            hook_path = f"plugins/{plugin}/{relative_pointer.as_posix()}"
            if hook_path not in output:
                raise ValueError(f"{manifest_path}: hook pointer target is missing")
            payload = json.loads(output[hook_path])
            events = payload.get("hooks")
            if not isinstance(events, dict) or not events:
                raise ValueError(f"{hook_path}: no hook events")
            for groups in events.values():
                if not isinstance(groups, list) or not groups:
                    raise ValueError(f"{hook_path}: hook event has no groups")
                for group in groups:
                    hooks = group.get("hooks") if isinstance(group, dict) else None
                    if not isinstance(hooks, list) or not hooks:
                        raise ValueError(f"{hook_path}: hook group has no commands")
                    for hook in hooks:
                        hook_type = hook.get("type") if isinstance(hook, dict) else None
                        if hook_type != "command":
                            raise ValueError(f"{hook_path}: unsupported hook type: {hook_type!r}")
                        for field, root_token, script_pattern in fields:
                            command = hook.get(field)
                            if not isinstance(command, str) or not command:
                                raise ValueError(f"{hook_path}: command hook is missing {field}")
                            parts = [command]
                            if host in exec_form_hosts:
                                arguments = hook.get("args")
                                if (
                                    not isinstance(arguments, list)
                                    or not all(isinstance(argument, str) for argument in arguments)
                                    or any(character.isspace() for character in command)
                                    or any(character.isspace() for argument in arguments for character in argument)
                                ):
                                    raise ValueError(
                                        f"{hook_path}: {host} hooks must use exec form: an executable "
                                        "command plus an args list, never a shell command line"
                                    )
                                parts.extend(arguments)
                            if any(token != root_token and token in part for part in parts for token in known_roots):
                                raise ValueError(f"{hook_path}: {field} uses the wrong plugin root")
                            matches = [match for part in parts for match in script_pattern.finditer(part)]
                            if not matches:
                                raise ValueError(f"{hook_path}: {field} has no package-relative script")
                            for match in matches:
                                script = PurePosixPath(match.group(1))
                                if script.is_absolute() or ".." in script.parts:
                                    raise ValueError(f"{hook_path}: {field} script escapes package")
                                target = f"plugins/{plugin}/{script.as_posix()}"
                                if target not in output:
                                    raise ValueError(f"{hook_path}: {field} script target is missing: {script}")


def catalog_index(catalog: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    if catalog.get("schema_version") != 1 or catalog.get("digest_format") != "sha256-tree-v1":
        raise ValueError("Unsupported capability catalog schema or digest format")
    releases: dict[str, dict] = {}
    plugins: dict[str, dict] = {}
    for release in catalog.get("releases", []):
        release_id = release.get("id")
        if not release_id or release_id in releases:
            raise ValueError(f"Invalid or duplicate catalog release: {release_id}")
        releases[release_id] = release
        marketplace = release.get("marketplace")
        for plugin in release.get("plugins", []):
            plugin_id = plugin.get("id")
            if not plugin_id or plugin_id in plugins:
                raise ValueError(f"Invalid or duplicate catalog plugin: {plugin_id}")
            if plugin_id != f"{marketplace}/{plugin.get('name')}":
                raise ValueError(f"Catalog plugin identity disagrees with its marketplace: {plugin_id}")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", plugin.get("digest", "")):
                raise ValueError(f"Invalid catalog digest: {plugin_id}")
            plugin["_release"] = release
            plugins[plugin_id] = plugin
    if not releases:
        raise ValueError("Capability catalog has no releases")
    for plugin_id, plugin in plugins.items():
        dependencies = plugin.get("dependencies", {})
        for kind in ("required", "optional"):
            for dependency in dependencies.get(kind, []):
                if dependency not in plugins:
                    raise ValueError(f"{plugin_id} names unknown dependency {dependency}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(plugin_id: str):
        if plugin_id in visiting:
            raise ValueError(f"Catalog dependency cycle includes {plugin_id}")
        if plugin_id in visited:
            return
        visiting.add(plugin_id)
        for dependency in plugins[plugin_id]["dependencies"]["required"]:
            visit(dependency)
        visiting.remove(plugin_id)
        visited.add(plugin_id)

    for plugin_id in plugins:
        visit(plugin_id)
    return releases, plugins


def render_capabilities(catalog: dict) -> str:
    releases, _ = catalog_index(catalog)
    lines = [
        "# Agent capabilities",
        "",
        "Generated from [`catalog/catalog.json`](.agents/catalog/catalog.json).",
        "Select exact releases in a project's `.agents/capabilities.lock.json`; do not copy definitions between repositories.",
        "",
    ]
    for release in releases.values():
        lines.extend((
            f"## {release['marketplace']} {release['version']}",
            "",
            f"Owner: [`{release['owner_repository']}`]({release['source'].removesuffix('.git')}) "
            f"· immutable revision `{release['revision']}`",
            "",
        ))
        for plugin in release["plugins"]:
            marker = " (deprecated)" if plugin["status"] == "deprecated" else ""
            lines.append(f"- **`{plugin['id']}`{marker}** — {plugin['description']}")
            if plugin.get("replacement"):
                lines.append(
                    f"  Replacement: {', '.join(f'`{value}`' for value in plugin['replacement'])}; "
                    f"remove after {plugin['remove_after']}."
                )
        lines.append("")
    return "\n".join(lines)


def canonical_output_bytes(data: str | bytes) -> bytes:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def output_tree_digest(output: dict[str, bytes], package_path: str, excluded: list[str]) -> str:
    prefix = package_path.rstrip("/") + "/"
    excluded_paths = {PurePosixPath(value).as_posix() for value in excluded}
    digest = hashlib.sha256()
    members = []
    for path, data in output.items():
        if path.startswith(prefix):
            relative = path[len(prefix):]
            if relative not in excluded_paths:
                members.append((relative, data))
    for relative, data in sorted(members):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(data)).encode("ascii"))
        digest.update(b"\0")
        digest.update(data)
    return "sha256:" + digest.hexdigest()


def bind_codex_hook_snapshots(root: Path, output: dict[str, bytes], plugins: set[str]) -> None:
    loader = read(inside(root, ".agents/hooks/codex_hook_snapshot.py"))
    if "'" in loader:
        raise ValueError("Codex hook snapshot loader must use only double-quoted strings")
    expression = "exec(" + repr(loader).replace('"', r'\x22') + ")"
    for plugin in sorted(plugins):
        hook_path = f"plugins/{plugin}/hooks/codex.json"
        excluded = ["hooks/codex.json"]
        if plugin == "machine":
            excluded.append("catalog/catalog.json")
        expected = output_tree_digest(output, f"plugins/{plugin}", excluded)
        payload = json.loads(output[hook_path])
        for groups in payload["hooks"].values():
            for group in groups:
                for hook in group["hooks"]:
                    for field in ("command", "commandWindows"):
                        command = hook[field]
                        prefix = "python3 -B " if field == "command" else "python -B "
                        if not command.startswith(prefix + '"${PLUGIN_ROOT}/'):
                            raise ValueError(f"Unsupported Codex {field} for {plugin}: {command}")
                        hook[field] = (
                            prefix + f'-c "{expression}" "${{PLUGIN_ROOT}}" "{expected}" '
                            f'"{plugin}" ' + command[len(prefix):]
                        )
        output[hook_path] = canonical_output_bytes(json.dumps(payload, indent=2) + "\n")


def inside(root: Path, relative: str | PurePosixPath) -> Path:
    candidate = (root / Path(*PurePosixPath(relative).parts)).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes repository: {relative}")
    return candidate


def metadata(body: str, source: Path) -> dict[str, str]:
    match = FRONTMATTER.match(body)
    if match is None:
        raise ValueError(f"Missing frontmatter: {source}")
    values: dict[str, str] = {}
    for line in match.group("header").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    for required in ("name", "description", "kind", "domain"):
        if not values.get(required):
            raise ValueError(f"{source}: missing {required}")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", values["name"]):
        raise ValueError(f"{source}: invalid public skill name {values['name']}")
    if not re.fullmatch(r"[a-z]+", values["kind"]):
        raise ValueError(f"{source}: kind must be one lowercase ASCII word")
    return values


def validate_configuration(root: Path, config: dict) -> set[str]:
    plugins = {scope["plugin"] for scope in config["scopes"]}
    if set(config["prerequisites"]) != plugins:
        raise ValueError("Prerequisite owners do not match declared plugins")
    for plugin, prerequisites in config["prerequisites"].items():
        unknown = set(prerequisites) - plugins
        if unknown:
            raise ValueError(f"Unknown prerequisite for {plugin}: {sorted(unknown)}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(plugin: str):
        if plugin in visiting:
            raise ValueError(f"Prerequisite cycle includes {plugin}")
        if plugin in visited:
            return
        visiting.add(plugin)
        for prerequisite in config["prerequisites"][plugin]:
            visit(prerequisite)
        visiting.remove(plugin)
        visited.add(plugin)

    for plugin in sorted(plugins):
        visit(plugin)

    authored = [inside(root, scope["root"]) for scope in config["scopes"]]
    authored.extend(inside(root, value) for value in config["host_adapter_roots"].values())
    authored.extend(inside(root, value) for value in config["host_manifest_roots"].values())
    generated = [inside(root, value) for value in config["generated_roots"]]
    for generated_path in generated:
        for authored_path in authored:
            if (generated_path == authored_path or generated_path.is_relative_to(authored_path)
                    or authored_path.is_relative_to(generated_path)):
                raise ValueError(
                    f"Generated root overlaps authored source: {generated_path.relative_to(root)}"
                )
    return plugins


def validate_default_selection(
    root: Path,
    config: dict,
    skills: dict[str, dict],
    compatibility: dict,
) -> None:
    codex_marketplace_path = inside(
        root, f"{config['host_manifest_roots']['codex']}/marketplace.json"
    )
    claude_marketplace_path = inside(
        root, f"{config['host_manifest_roots']['claude']}/marketplace.json"
    )
    codex_marketplace = load(codex_marketplace_path)
    claude_marketplace = load(claude_marketplace_path)
    marketplace_name = codex_marketplace.get("name")
    if not marketplace_name:
        raise ValueError(f"{codex_marketplace_path}: missing marketplace name")
    if claude_marketplace.get("name") != marketplace_name:
        raise ValueError("Codex and Claude marketplace names must match")

    fresh_entries = compatibility.get("fresh_selection")
    if not isinstance(fresh_entries, list) or not fresh_entries:
        raise ValueError("Compatibility fresh_selection must be a non-empty list")
    expected_suffix = f"@{marketplace_name}"
    if any(
        not isinstance(entry, str)
        or not entry.endswith(expected_suffix)
        or entry == expected_suffix
        for entry in fresh_entries
    ):
        raise ValueError(
            f"Fresh selection entries must use <plugin>{expected_suffix}"
        )
    fresh_plugins = [entry[: -len(expected_suffix)] for entry in fresh_entries]
    if len(fresh_plugins) != len(set(fresh_plugins)):
        raise ValueError("Fresh selection contains duplicate plugins")

    default_plugins = [
        plugin.get("name")
        for plugin in codex_marketplace.get("plugins", [])
        if plugin.get("policy", {}).get("installation") == "INSTALLED_BY_DEFAULT"
    ]
    if fresh_plugins != default_plugins:
        raise ValueError(
            "Compatibility fresh_selection must exactly match the Codex "
            "INSTALLED_BY_DEFAULT marketplace order"
        )

    claude_plugins = claude_marketplace.get("plugins", [])
    claude_roster = [plugin.get("name") for plugin in claude_plugins]
    if fresh_plugins != claude_roster:
        raise ValueError(
            "Compatibility fresh_selection must exactly match the Claude "
            "marketplace roster"
        )

    codex_by_name = {
        plugin.get("name"): plugin for plugin in codex_marketplace.get("plugins", [])
    }
    claude_by_name = {plugin.get("name"): plugin for plugin in claude_plugins}
    for plugin in fresh_plugins:
        expected_path = f"./plugins/{plugin}"
        codex_source = codex_by_name[plugin].get("source")
        if (
            not isinstance(codex_source, dict)
            or codex_source.get("source") != "local"
            or codex_source.get("path") != expected_path
        ):
            raise ValueError(
                f"Codex marketplace source for {plugin} must be {expected_path}"
            )
        if claude_by_name[plugin].get("source") != expected_path:
            raise ValueError(
                f"Claude marketplace source for {plugin} must be {expected_path}"
            )

    known_plugins = set(config["prerequisites"])
    unknown = set(fresh_plugins) - known_plugins
    if unknown:
        raise ValueError(f"Fresh selection contains unknown plugins: {sorted(unknown)}")
    selected = set(fresh_plugins)
    for plugin in fresh_plugins:
        missing = set(config["prerequisites"][plugin]) - selected
        if missing:
            raise ValueError(
                f"Fresh selection omits prerequisites for {plugin}: {sorted(missing)}"
            )

    selected_skills = {
        name for name, skill in skills.items() if skill["plugin"] in selected
    }
    required_values = compatibility.get("fresh_required_skills")
    if (
        not isinstance(required_values, list)
        or len(required_values) != len(set(required_values))
        or set(required_values) != DEFAULT_HANDOFF_SKILLS
    ):
        raise ValueError(
            "Compatibility fresh_required_skills must exactly declare "
            f"{sorted(DEFAULT_HANDOFF_SKILLS)}"
        )
    required_skills = set(required_values)
    missing_skills = required_skills - selected_skills
    if missing_skills:
        raise ValueError(
            f"Fresh selection is missing required skills: {sorted(missing_skills)}"
        )

    replacement_release = compatibility.get("replacement_release")
    for plugin in sorted(known_plugins):
        manifest_path = inside(
            root, f"{config['host_manifest_roots']['codex']}/{plugin}.json"
        )
        version = load(manifest_path).get("version")
        if version != replacement_release:
            raise ValueError(
                f"{manifest_path}: version {version!r} does not match "
                f"replacement release {replacement_release!r}"
            )


def discover(root: Path, config: dict) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for scope in config["scopes"]:
        source_root = inside(root, scope["root"])
        if not source_root.is_dir():
            raise ValueError(f"Missing canonical scope root: {scope['root']}")
        if scope["layout"] == "flat":
            candidates = sorted(source_root.glob("*/SKILL.md"))
        elif scope["layout"] == "kind":
            candidates = sorted(source_root.glob("*/*/SKILL.md"))
        else:
            raise ValueError(f"Unknown source layout: {scope['layout']}")
        for path in candidates:
            body = read(path)
            values = metadata(body, path)
            name = values["name"]
            if name in found:
                raise ValueError(f"Duplicate public skill name: {name}")
            if values["domain"] != scope["domain"]:
                raise ValueError(
                    f"{path}: domain {values['domain']} does not match {scope['domain']}"
                )
            if scope["layout"] == "kind" and values["kind"] != path.parent.parent.name:
                raise ValueError(
                    f"{path}: kind {values['kind']} does not match kind folder "
                    f"{path.parent.parent.name}"
                )
            found[name] = {
                "path": path,
                "body": body,
                "metadata": values,
                "plugin": scope["plugin"],
                "scope": scope["name"],
                "relative": path.relative_to(root).as_posix(),
            }
    return found


def expected_adapter_body(shared: dict, host: str) -> str:
    title = next(
        (line for line in shared["body"].splitlines() if line.startswith("# ")),
        f"# {shared['metadata']['name']}",
    )
    return (
        f"\n{title}\n\n"
        f"Read and follow the [canonical shared definition](../../../{shared['relative']}) in full.\n"
        f"This entry point supplies only {host.capitalize()} discovery metadata; "
        "the shared procedure is authored once under `.agents/`.\n"
    )


def validate_host_neutral(config: dict, skills: dict[str, dict]) -> None:
    patterns = {
        host: [re.compile(term, re.MULTILINE) for term in terms]
        for host, terms in config.get("host_only_terms", {}).items()
    }
    for name, shared in skills.items():
        for document in sorted(shared["path"].parent.rglob("*.md")):
            text = document.read_text(encoding="utf-8")
            for host, compiled in patterns.items():
                for pattern in compiled:
                    match = pattern.search(text)
                    if match:
                        raise ValueError(
                            f"{document.as_posix()}: {host}-only term {match.group(0)!r} belongs in "
                            f".{host}/skills/{name}/SKILL.md, registered in extended_host_adapters, "
                            "not the shared definition"
                        )


def validate_adapters(root: Path, config: dict, skills: dict[str, dict]) -> dict:
    adapters: dict[str, dict[str, Path]] = {}
    extended = set(config.get("extended_host_adapters", []))
    unknown_extended = extended - set(skills)
    if unknown_extended:
        raise ValueError(f"Unknown extended host adapters: {sorted(unknown_extended)}")
    lane_tables = {
        host: load(root / f".agents/lanes/{host}.json") for host in ("codex", "claude")
    }
    for host, adapter_root_value in config["host_adapter_roots"].items():
        adapter_root = inside(root, adapter_root_value)
        host_adapters: dict[str, Path] = {}
        actual_names = {path.parent.name for path in adapter_root.glob("*/SKILL.md")}
        if actual_names != set(skills):
            missing = sorted(set(skills) - actual_names)
            extra = sorted(actual_names - set(skills))
            raise ValueError(f"{host} adapter roster mismatch; missing={missing}, extra={extra}")
        table = lane_tables[host]
        for name, shared in skills.items():
            path = adapter_root / name / "SKILL.md"
            body = read(path)
            values = metadata(body, path)
            shared_fields = ("name", "kind", "domain") if name in extended else (
                "name", "description", "kind", "domain"
            )
            for field in shared_fields:
                if values[field] != shared["metadata"][field]:
                    raise ValueError(f"{path}: {field} differs from canonical definition")
            if "lane" in values:
                raise ValueError(f"{path}: host adapter must resolve lane metadata")
            lane = shared["metadata"].get("lane")
            if lane:
                rung = table["lanes"].get(lane)
                if not rung or values.get("model") != rung.get("model"):
                    raise ValueError(f"{path}: model does not resolve canonical lane {lane}")
                effort_key = table.get("effort_key")
                if table.get("skill_supports_effort") and effort_key in rung:
                    if values.get("effort") != rung[effort_key]:
                        raise ValueError(f"{path}: effort does not resolve canonical lane {lane}")
            elif "model" in values or "effort" in values:
                raise ValueError(
                    f"{path}: model/effort without a canonical lane re-points the session"
                )
            match = FRONTMATTER.match(body)
            if match is None:
                raise ValueError(f"{path}: adapter has no body")
            if name in extended:
                reference = f"](../../../{shared['relative']})"
                if body.count(reference) != 1:
                    raise ValueError(
                        f"{path}: extended adapter must reference its canonical definition once"
                    )
            elif match.group("body") != expected_adapter_body(shared, host):
                raise ValueError(f"{path}: adapter must be a thin canonical reference")
            host_adapters[name] = path
        adapters[host] = host_adapters
    return adapters



def agent_payload(role: dict, body: str, host: str) -> str:
    """Render a host-native agent from one shared role body and host metadata."""
    if host == "codex":
        values = {
            "name": role["agent_name"],
            "description": role["description"],
            "model": role["model"],
            "model_reasoning_effort": role["reasoning_effort"],
            "sandbox_mode": role["sandbox_mode"],
            "developer_instructions": body,
        }
        return (
            "\n".join(
                f"{key} = {json.dumps(value, ensure_ascii=False)}"
                for key, value in values.items()
            )
            + "\n\n[agents]\nenabled = false\n"
        )
    values = {
        "name": role["agent_name"],
        "description": role["description"],
    }
    if role.get("kind"):
        values["kind"] = role["kind"]
    values["model"] = role["model"]
    if role.get("effort"):
        values["effort"] = role["effort"]
    values.update(
        tools=", ".join(role["tools"]),
        disallowedTools="Agent",
    )
    if role.get("isolation"):
        values["isolation"] = role["isolation"]
    return (
        "---\n"
        + "\n".join(f"{key}: {value}" for key, value in values.items())
        + "\n---\n\n"
        + body
        + "\n"
    )


def emit_workflow_agents(root: Path, config: dict, emit):
    workflow = config.get("workflow")
    if not workflow:
        return
    source = inside(root, workflow["source"])
    plugin = workflow["plugin"]
    hosts = {
        host: load(source / f"hosts/{host}.json")
        for host in ("claude", "codex")
    }
    if set(hosts["claude"]["roles"]) != set(hosts["codex"]["roles"]):
        raise ValueError("Workflow host role sets disagree")
    for capability in hosts["codex"]["roles"]:
        roles = {host: hosts[host]["roles"][capability] for host in hosts}
        if roles["claude"]["body"] != roles["codex"]["body"]:
            raise ValueError(f"Workflow role bodies disagree: {capability}")
        body = read(inside(source, f"hosts/{roles['codex']['body']}")).strip()
        for host, role in roles.items():
            directory = "agents" if host == "claude" else "codex-agents"
            emit(
                f"plugins/{plugin}/{directory}/{role['filename']}",
                agent_payload(role, body, host),
            )

    lane_body = read(root / ".agents/lanes/agent-body.md").strip()
    for host in ("claude", "codex"):
        table = load(root / f".agents/lanes/{host}.json")
        for lane, rung in table["lanes"].items():
            role = {
                "agent_name": f"lane-{lane.lower()}" if host == "claude" else f"lane_{lane.lower()}",
                "description": f"Runs one delegated task at lane {lane}. {rung['summary']}",
                "kind": "lane",
                "tools": ["Read", "Glob", "Grep", "Write", "Edit", "Bash"],
                "sandbox_mode": "workspace-write",
                **rung,
            }
            extension = "md" if host == "claude" else "toml"
            directory = "agents" if host == "claude" else "codex-agents"
            emit(
                f"plugins/{plugin}/{directory}/lane-{lane.lower()}.{extension}",
                agent_payload(role, lane_body, host),
            )

    fixtures = source / "fixtures"
    template = read(fixtures / "workflow-contract-fixture.template.md")
    rendered = template.replace(
        "{{WORKFLOW_CONTRACT_V2_GATES}}",
        read(source / "contract/v2/gates.md").strip(),
    )
    if "{{" in rendered:
        raise ValueError("Unresolved workflow fixture token")
    emit(f"plugins/{plugin}/workflows/fixtures/workflow-contract-fixture.md", rendered)
    fixture = load(fixtures / "role.json")
    body = read(fixtures / fixture["body"]).strip()
    for host in hosts:
        role = {
            "agent_name": fixture["name"],
            "description": fixture["description"],
            "effort": "medium",
            **fixture[host],
        }
        extension = "claude.md" if host == "claude" else "toml"
        emit(
            f"plugins/{plugin}/workflows/fixtures/workflow-contract-fixture.{extension}",
            agent_payload(role, body, host),
        )

def build(root: Path, validate_catalog_digests: bool = True):
    root = root.resolve()
    config = load(root / ".agents/plugins/sources.json")
    payloads = load(root / ".agents/plugins/payloads.json")["payloads"]
    compatibility = load(root / ".agents/plugins/compatibility.json")
    catalog = load(root / ".agents/catalog/catalog.json")
    if any(release["owner_repository"] != "tj-agents/core" for release in catalog["releases"]):
        raise ValueError("Core's authored catalog may contain only core releases")
    _, catalog_plugins = catalog_index(catalog)
    harnesses = {
        path.stem: load(path)
        for path in (root / ".agents/plugins/harness").glob("*.json")
    }
    skills = discover(root, config)
    validate_host_neutral(config, skills)
    adapters = validate_adapters(root, config, skills)
    plugins = validate_configuration(root, config)
    validate_default_selection(root, config, skills, compatibility)

    output: dict[str, bytes] = {}

    def emit(relative: str, data: str | bytes):
        if relative in output:
            raise ValueError(f"Duplicate generated output: {relative}")
        output[relative] = canonical_output_bytes(data)

    # Ship the canonical definition once. Resource siblings are also copied into each
    # generated discovery entry so <skill-directory> remains valid after installation;
    # these are generated payload copies, never additional authored sources.
    for name, shared in skills.items():
        capability = shared["path"].parent
        shared_resources: list[tuple[str, bytes]] = []
        for path in sorted(capability.rglob("*")):
            if not path.is_file() or path.suffix == ".pyc" or "__pycache__" in path.parts:
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(capability.resolve()):
                raise ValueError(f"Resource escapes capability: {path}")
            destination = (
                f"plugins/{shared['plugin']}/"
                + path.relative_to(root).as_posix()
            )
            emit(destination, path.read_bytes())
            if path != shared["path"]:
                shared_resources.append((path.relative_to(capability).as_posix(), path.read_bytes()))

        for host, tree in (("codex", "codex-skills"), ("claude", "skills")):
            adapter_dir = adapters[host][name].parent
            for path in sorted(adapter_dir.rglob("*")):
                if not path.is_file() or path.suffix == ".pyc" or "__pycache__" in path.parts:
                    continue
                relative = path.relative_to(adapter_dir).as_posix()
                data = path.read_bytes()
                if relative == "SKILL.md":
                    data = read(path).replace(
                        "../../../.agents/", "../../.agents/"
                    ).encode("utf-8")
                emit(f"plugins/{shared['plugin']}/{tree}/{name}/{relative}", data)
            for relative, data in shared_resources:
                emit(f"plugins/{shared['plugin']}/{tree}/{name}/{relative}", data)

    # Declared shared runtime stays under the owning plugin's canonical .agents tree.
    for resource in config.get("resources", []):
        plugin = resource["plugin"]
        if plugin not in plugins:
            raise ValueError(f"Unknown resource owner: {plugin}")
        source = inside(root, resource["source"])
        destination = PurePosixPath(resource["destination"])
        if destination.is_absolute() or ".." in destination.parts:
            raise ValueError(f"Invalid resource destination: {destination}")
        paths = sorted(source.rglob("*")) if source.is_dir() else [source]
        for path in paths:
            if not path.is_file() or path.suffix == ".pyc" or "__pycache__" in path.parts:
                continue
            suffix = path.relative_to(source).as_posix() if source.is_dir() else ""
            target = f"plugins/{plugin}/{destination}" + (f"/{suffix}" if suffix else "")
            emit(target, path.read_bytes())

    emit_workflow_agents(root, config, emit)

    manifests: dict[str, dict[str, dict]] = {plugin: {} for plugin in plugins}
    for plugin in sorted(plugins):
        harness = harnesses.get(plugin)
        if harness is None or harness.get("plugin") != f"base-agents/{plugin}":
            raise ValueError(f"Missing or mismatched harness manifest: {plugin}")
        emit(f"plugins/{plugin}/harness.json", json.dumps(harness, indent=2) + "\n")
        for host, tree in (("codex", "codex-skills"), ("claude", "skills")):
            manifest_path = inside(root, f"{config['host_manifest_roots'][host]}/{plugin}.json")
            manifest = load(manifest_path)
            manifests[plugin][host] = manifest
            if manifest.get("name") != plugin or manifest.get("skills") != f"./{tree}/":
                raise ValueError(f"{manifest_path}: invalid name or skills root")
            hook_source = config.get("host_hook_sources", {}).get(plugin, {}).get(host)
            if hook_source:
                hook_target = f"plugins/{plugin}/hooks/{host}.json"
                emit(hook_target, read(inside(root, hook_source)))
                if manifest.get("hooks") != f"./hooks/{host}.json":
                    raise ValueError(f"{manifest_path}: hook path disagrees with source map")
            elif "hooks" in manifest:
                raise ValueError(f"{manifest_path}: undeclared hook source")
            emit(f"plugins/{plugin}/.{host}-plugin/plugin.json", read(manifest_path))
        for field in ("name", "description", "author", "repository", "keywords"):
            if manifests[plugin]["codex"].get(field) != manifests[plugin]["claude"].get(field):
                raise ValueError(f"{plugin}: host manifests disagree on {field}")

        owned = sorted(name for name, skill in skills.items() if skill["plugin"] == plugin)
        index = [f"# {plugin} capabilities", "", "Generated from canonical `.agents/` definitions.", ""]
        for name in owned:
            skill = skills[name]
            index.append(
                f"- `{name}` — {skill['metadata']['kind']} — `{skill['relative']}`"
            )
        index.append("")
        emit(f"plugins/{plugin}/INDEX.md", "\n".join(index))
        selection = {
            "plugin": plugin,
            "payloads": payloads[plugin],
            "prerequisites": config["prerequisites"][plugin],
            "skills": owned,
        }
        emit(f"plugins/{plugin}/selection.json", json.dumps(selection, indent=2) + "\n")

    emit("CAPABILITIES.md", render_capabilities(catalog))

    emit(
        ".agents/plugins/marketplace.json",
        read(inside(root, f"{config['host_manifest_roots']['codex']}/marketplace.json")),
    )
    emit(
        ".claude-plugin/marketplace.json",
        read(inside(root, f"{config['host_manifest_roots']['claude']}/marketplace.json")),
    )

    # Every packaged adapter must resolve to the one packaged canonical definition.
    for path, data in output.items():
        if not re.match(r"plugins/[^/]+/(?:skills|codex-skills)/[^/]+/SKILL\.md$", path):
            continue
        body = data.decode("utf-8")
        match = re.search(r"\]\((\.\./\.\./\.agents/[^)]+/SKILL\.md)\)", body)
        if match is None:
            raise ValueError(f"{path}: no packaged canonical reference")
        adapter = PurePosixPath(path)
        target = adapter.parent.joinpath(match.group(1))
        normalized = PurePosixPath(*[part for part in target.parts if part != "."])
        parts: list[str] = []
        for part in normalized.parts:
            if part == "..":
                if not parts:
                    raise ValueError(f"{path}: canonical reference escapes plugin")
                parts.pop()
            else:
                parts.append(part)
        resolved = "/".join(parts)
        if resolved not in output:
            raise ValueError(f"{path}: missing packaged canonical definition {resolved}")

    bind_codex_hook_snapshots(root, output, plugins)
    validate_hook_outputs(output, config, plugins)

    for plugin in sorted(plugins):
        plugin_id = f"base-agents/{plugin}"
        entry = catalog_plugins.get(plugin_id)
        if entry is None:
            raise ValueError(f"Catalog is missing local plugin {plugin_id}")
        expected_dependencies = [f"base-agents/{value}" for value in config["prerequisites"][plugin]]
        if entry["dependencies"]["required"] != expected_dependencies:
            raise ValueError(f"Catalog prerequisite drift: {plugin_id}")
        if entry["skills"] != sorted(name for name, skill in skills.items() if skill["plugin"] == plugin):
            raise ValueError(f"Catalog skill roster drift: {plugin_id}")
        if entry["package_path"] != f"plugins/{plugin}":
            raise ValueError(f"Catalog package path drift: {plugin_id}")
        if entry.get("harness") != harnesses[plugin]["requires"]:
            raise ValueError(f"Catalog harness drift: {plugin_id}")
        allowed_excludes = ["catalog/catalog.json"] if plugin_id == "base-agents/machine" else []
        if entry.get("digest_excludes", []) != allowed_excludes:
            raise ValueError(f"Catalog digest exclusion drift: {plugin_id}")
        manifest_version = manifests[plugin]["codex"].get("version")
        if entry["version"] != manifest_version:
            raise ValueError(f"Catalog version drift: {plugin_id}")
        release = entry["_release"]
        if release["marketplace"] != "base-agents" or release["owner_repository"] != "tj-agents/core":
            raise ValueError(f"Catalog owner drift: {plugin_id}")
        if validate_catalog_digests:
            actual_digest = output_tree_digest(
                output,
                entry["package_path"],
                entry.get("digest_excludes", []),
            )
            if entry["digest"] != actual_digest:
                raise ValueError(
                    f"Catalog digest drift for {plugin_id}: expected {entry['digest']}, actual {actual_digest}. "
                    "Run python -B scripts/update_catalog_digests.py"
                )

    return config, output, skills, compatibility


def generate(root: Path, check: bool = False):
    root = root.resolve()
    config, output, skills, _ = build(root)
    generated_roots = [inside(root, value) for value in config["generated_roots"]]
    existing: dict[str, Path] = {}
    for generated_root in generated_roots:
        if generated_root.is_file():
            existing[generated_root.relative_to(root).as_posix()] = generated_root
        elif generated_root.is_dir():
            for path in generated_root.rglob("*"):
                if path.is_file():
                    existing[path.relative_to(root).as_posix()] = path

    def equivalent(path: Path, data: bytes) -> bool:
        current = path.read_bytes()
        try:
            current.decode("utf-8")
            data.decode("utf-8")
        except UnicodeDecodeError:
            return current == data
        return current.replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n")

    stale = sorted(
        relative for relative, data in output.items()
        if relative not in existing or not equivalent(existing[relative], data)
    )
    orphans = sorted(set(existing) - set(output))
    if check:
        if stale or orphans:
            raise ValueError(
                f"Stale generated files: {len(stale)}; orphans: {len(orphans)}. "
                "Run pwsh .agents/sync-generated.ps1"
            )
    else:
        for relative in stale:
            target = inside(root, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(output[relative])
        for relative in orphans:
            target = inside(root, relative)
            if not any(target == declared or target.is_relative_to(declared) for declared in generated_roots):
                raise ValueError(f"Unsafe prune target: {relative}")
            target.unlink()
        for generated_root in generated_roots:
            if not generated_root.is_dir():
                continue
            for directory in sorted(
                (path for path in generated_root.rglob("*") if path.is_dir()),
                key=lambda path: len(path.parts), reverse=True,
            ):
                try:
                    directory.rmdir()
                except OSError:
                    pass
    print(
        f"{'Checked' if check else 'Synchronized'} {len(output)} package files from "
        f"{len(skills)} shared definitions; {len(stale)} changed, {len(orphans)} pruned."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        generate(arguments.root, arguments.check)
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Package synchronization failed: {error}", file=sys.stderr)
        raise SystemExit(1)
