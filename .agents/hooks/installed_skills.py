"""Find an installed skill's SKILL.md across this plugin, linked skill roots and native plugin installs."""

import functools
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from host_cli import plugin_inventory_command
from tj_cli import process

LINKED_SKILL_ROOTS = {
    "claude": ("skills",),
    "codex": (".agents/skills", ".codex/skills"),
}


class NativePluginDiscoveryError(Exception):
    def __init__(self, harness, detail):
        self.harness = harness
        super().__init__(f"{harness} plugin inventory failed: {detail}")


@functools.lru_cache(maxsize=2)
def _native_install_roots(harness):
    binary = shutil.which(harness)
    if binary is None:
        return NativePluginDiscoveryError(harness, "CLI executable is unavailable")
    command, environment = plugin_inventory_command(binary)
    try:
        result = process.run(
            command, capture_output=True, text=True, env=environment,
            encoding="utf-8", errors="replace", timeout=8, check=False,
        )
        if result.returncode != 0:
            return NativePluginDiscoveryError(harness, f"CLI exited with status {result.returncode}")
        data = json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return NativePluginDiscoveryError(harness, "CLI timed out after 8 seconds")
    except OSError as error:
        return NativePluginDiscoveryError(harness, f"CLI could not run: {str(error)[:256]}")
    except ValueError:
        return NativePluginDiscoveryError(harness, "CLI returned invalid JSON")
    plugins = data.get("installed") if harness == "codex" and isinstance(data, dict) else data
    if not isinstance(plugins, list):
        return NativePluginDiscoveryError(harness, "CLI returned an invalid roster")
    roots = []
    for plugin in plugins:
        if not isinstance(plugin, dict) or not plugin.get("enabled"):
            continue
        if harness == "codex":
            marketplace, name, version = plugin.get("marketplaceName"), plugin.get("name"), plugin.get("version")
            if not all(isinstance(value, str) for value in (marketplace, name, version)):
                continue
            path = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "plugins" / "cache" / marketplace / name / version
        else:
            path = plugin.get("installPath")
        if isinstance(path, (str, Path)):
            roots.append(Path(path))
    return tuple(roots)


def native_install_roots(harness):
    roots = _native_install_roots(harness)
    if isinstance(roots, NativePluginDiscoveryError):
        raise roots
    return roots


def skill_search_dirs(harness):
    yield Path(__file__).resolve().parent.parent / "skills"
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    home = Path.home()
    linked_base = Path(configured) if configured and harness == "claude" else (
        home / ".claude" if harness == "claude" else home
    )
    for relative in LINKED_SKILL_ROOTS[harness]:
        yield linked_base / relative
    for root in native_install_roots(harness):
        yield root / "skills"


def plugin_of(skills_dir):
    parents = skills_dir.parents
    if len(parents) >= 4 and parents[3].name == "cache":
        return parents[1].name
    parent = skills_dir.parent
    if parent.name in {".agents", ".claude"}:
        return None
    return parent.name


def description_of(body):
    match = re.search(r"^description:[ \t]*(.+?)(?=^\w+:|^---)", body, re.M | re.S)
    return " ".join(match.group(1).split()) if match else None


def resolved_skill(name, harness):
    wanted_plugin, _, bare = name.rpartition(":")
    first = None
    for root in skill_search_dirs(harness):
        if wanted_plugin and plugin_of(root) != wanted_plugin:
            continue
        skill = root / bare / "SKILL.md"
        if not skill.is_file():
            continue
        try:
            text = skill.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        if description_of(text) is None:
            first = first or (skill, text)
            continue
        return skill, text
    return first
