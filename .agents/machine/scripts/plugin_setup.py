#!/usr/bin/env python3
"""Converge setup declared by verified, repository-selected native plugins (Python 3.9+)."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

import required_plugins


CHECK_TIMEOUT_SECONDS = 90
ONBOARD_TIMEOUT_SECONDS = 660
MAX_OUTPUT = 1024


class PluginSetupError(RuntimeError):
    pass


@dataclass(frozen=True)
class Target:
    identity: str
    script: Path
    declaration: str
    runtime: bytes


def bounded(result: subprocess.CompletedProcess) -> str:
    return ((result.stderr or result.stdout or f"exit {result.returncode}").strip()[:MAX_OUTPUT])


def private_path(root: Path, relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts or candidate.suffix != ".py":
        raise PluginSetupError(f"invalid setup script declaration {relative!r}")
    path = root.joinpath(*candidate.parts)
    current = root
    if is_reparse(current):
        raise PluginSetupError(f"declared setup script is unsafe: {relative}")
    for part in candidate.parts:
        current /= part
        if is_reparse(current):
            raise PluginSetupError(f"declared setup script is unsafe: {relative}")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise PluginSetupError(f"declared setup script is unavailable: {relative}") from error
    if not resolved.is_relative_to(root.resolve()) or is_reparse(path) or not resolved.is_file():
        raise PluginSetupError(f"declared setup script is unsafe: {relative}")
    return resolved


def is_reparse(path: Path) -> bool:
    try:
        return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)
    except OSError:
        return True


def runtime_bytes(root: Path) -> bytes:
    if is_reparse(root):
        raise PluginSetupError("plugin setup runtime directory is a reparse point")
    digest = hashlib.sha256()
    directories = [root]
    while directories:
        directory = directories.pop()
        for path in sorted(directory.iterdir(), reverse=True):
            relative = path.relative_to(root)
            if "__pycache__" in relative.parts or path.suffix == ".pyc":
                continue
            if is_reparse(path):
                raise PluginSetupError(f"plugin setup runtime contains a reparse point: {relative}")
            if path.is_dir():
                directories.append(path)
            elif path.is_file():
                digest.update(relative.as_posix().encode() + b"\0" + path.read_bytes())
    return digest.digest()


def harness_document(root: Path) -> tuple[dict, str]:
    harness = root / "harness.json"
    if not harness.is_file() or is_reparse(harness):
        raise PluginSetupError("verified runtime has no harness declaration")
    try:
        document = json.loads(harness.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PluginSetupError("cannot read harness declaration") from error
    plugin = document.get("plugin") if isinstance(document, dict) else None
    marketplace, separator, name = plugin.partition("/") if isinstance(plugin, str) else ("", "", "")
    identity = f"{name}@{marketplace}"
    if not separator or not required_plugins.IDENTITY.fullmatch(identity):
        raise PluginSetupError("harness plugin identity is invalid")
    return document, identity


def declaration(root: Path, identity: str, document: dict | None = None) -> Target | None:
    name, marketplace = identity.split("@", 1)
    document, declared = harness_document(root) if document is None else (document, identity)
    if declared != identity:
        raise PluginSetupError(f"{identity}: harness identity does not match the selected plugin")
    requires = document.get("requires", {})
    if not isinstance(requires, dict):
        raise PluginSetupError(f"{identity}: harness requires declaration is invalid")
    setup = requires.get("setup")
    if setup is None:
        return None
    if not isinstance(setup, dict) or set(setup) != {"script"} or not isinstance(setup["script"], str):
        raise PluginSetupError(f"{identity}: requires.setup must be {{\"script\": \"relative/path.py\"}}")
    script = private_path(root, setup["script"])
    return Target(identity, script, setup["script"], runtime_bytes(script.parent))


def targets(project: Path, host: str, executable: str | None) -> list[Target]:
    roots = required_plugins.check(project, host, executable)
    if roots is None:
        return []
    selected = required_plugins.selected(required_plugins.project_root(project))
    found = []
    for identity in selected:
        for root in roots:
            if not (root / "harness.json").exists():
                continue
            try:
                document, declared = harness_document(root)
                if declared != identity:
                    continue
                target = declaration(root, identity, document)
            except PluginSetupError:
                raise
            if target is not None:
                found.append(target)
            break
        else:
            raise PluginSetupError(f"{identity}: verified native installation did not provide its harness")
    return found


def collect(project: Path, hosts: tuple[str, ...], executables: dict[str, str | None]) -> tuple[list[Target], list[str]]:
    discovered, errors = {}, []
    for host in hosts:
        try:
            discovered[host] = {target.identity: target for target in targets(project, host, executables.get(host))}
        except (required_plugins.RequiredPluginsError, PluginSetupError) as error:
            errors.append(f"{host}: {error}")
    if not errors and discovered:
        reference_host = next(iter(discovered))
        reference = discovered[reference_host]
        for host, current in discovered.items():
            if set(current) != set(reference):
                errors.append(f"{host}: native host setup declarations disagree with {reference_host}")
                continue
            for identity, target in current.items():
                expected = reference[identity]
                if expected.declaration != target.declaration or expected.runtime != target.runtime:
                    errors.append(f"{identity}: native host runtimes disagree on its setup declaration")
    return ([] if errors else [reference[key] for key in sorted(reference)]), errors


def invoke(target: Target, arguments: list[str], timeout: int, inherit: bool = False) -> subprocess.CompletedProcess:
    command = [sys.executable, "-B", str(target.script), "setup", *arguments]
    if inherit:
        return subprocess.run(command, timeout=timeout, check=False)
    return subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout, check=False)


def check(project: Path, hosts: tuple[str, ...], executables: dict[str, str | None]) -> list[str]:
    targets_found, errors = collect(project, hosts, executables)
    for target in targets_found:
        try:
            result = invoke(target, ["--check"], CHECK_TIMEOUT_SECONDS)
            if result.returncode:
                errors.append(f"{target.identity}: setup --check failed: {bounded(result)}")
        except (OSError, subprocess.SubprocessError) as error:
            errors.append(f"{target.identity}: setup --check could not run: {error}")
    return errors


def converge(project: Path, hosts: tuple[str, ...], executables: dict[str, str | None], onboard: bool = False) -> list[str]:
    targets_found, errors = collect(project, hosts, executables)
    for target in targets_found:
        try:
            checked = invoke(target, ["--check"], CHECK_TIMEOUT_SECONDS)
            if checked.returncode:
                applied = invoke(target, ["--onboard"] if onboard else [],
                                 ONBOARD_TIMEOUT_SECONDS if onboard else CHECK_TIMEOUT_SECONDS, inherit=onboard)
                if applied.returncode:
                    errors.append(f"{target.identity}: setup failed: {bounded(applied)}")
                    continue
                checked = invoke(target, ["--check"], CHECK_TIMEOUT_SECONDS)
            if checked.returncode:
                errors.append(f"{target.identity}: setup did not converge: {bounded(checked)}")
        except (OSError, subprocess.SubprocessError) as error:
            errors.append(f"{target.identity}: setup could not run: {error}")
    return errors
