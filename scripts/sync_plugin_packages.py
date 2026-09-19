"""Build self-contained plugin payloads from shared definitions and host adapters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys


FRONTMATTER = re.compile(r"\A---\n(?P<header>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def load(path: Path):
    return json.loads(read(path))


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
        "model": role["model"],
    }
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
                "description": f"Bounded delegated work at {lane}.",
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

def build(root: Path):
    config = load(root / ".agents/plugins/sources.json")
    payloads = load(root / ".agents/plugins/payloads.json")["payloads"]
    compatibility = load(root / ".agents/plugins/compatibility.json")
    skills = discover(root, config)
    adapters = validate_adapters(root, config, skills)
    plugins = validate_configuration(root, config)

    output: dict[str, bytes] = {}

    def emit(relative: str, data: str | bytes):
        if relative in output:
            raise ValueError(f"Duplicate generated output: {relative}")
        output[relative] = data.encode("utf-8") if isinstance(data, str) else data

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
        for host, tree in (("codex", "codex-skills"), ("claude", "skills")):
            manifest_path = root / f".{host}/plugins/{plugin}/plugin.json"
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

    emit(
        ".agents/plugins/marketplace.json",
        read(root / ".codex/plugins/marketplace.json"),
    )
    emit(
        ".claude-plugin/marketplace.json",
        read(root / ".claude/plugins/marketplace.json"),
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
