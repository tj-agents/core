#!/usr/bin/env python3
"""Build an isolated native Codex plugin runtime for one launched session."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
from typing import Mapping, Sequence

import codex_hook_trust
import codex_marketplace_sync
import rolling_plugins


RECEIPT_ENV = "TJ_AGENTS_CODEX_RUNTIME_RECEIPT"
RECEIPT_SHA256_ENV = "TJ_AGENTS_CODEX_RUNTIME_RECEIPT_SHA256"


class RuntimeBindingError(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeBinding:
    prepared: rolling_plugins.Prepared
    directory: Path
    aliases: Mapping[str, str]
    receipt: Path
    receipt_digest: str
    hook_state: Mapping[str, object]

    @property
    def environment(self) -> dict[str, str]:
        return {
            RECEIPT_ENV: str(self.receipt),
            RECEIPT_SHA256_ENV: self.receipt_digest,
        }


def toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RuntimeBindingError("Codex effective configuration contains a non-finite number")
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        items = []
        for key in sorted(value):
            if not isinstance(key, str):
                raise RuntimeBindingError("Codex effective configuration contains a non-string table key")
            if value[key] is None:
                continue
            items.append(f"{json.dumps(key, ensure_ascii=False)} = {toml_value(value[key])}")
        return "{ " + ", ".join(items) + " }"
    raise RuntimeBindingError("Codex effective configuration contains an unsupported value")


def _runtime_marketplace(marketplace: str, nonce: str) -> str:
    return f"tj-run-{nonce}-{rolling_plugins._cache_component(marketplace)}"


def _runtime_directory(prepared: rolling_plugins.Prepared) -> Path:
    try:
        cache = prepared.catalog_root.parents[2]
    except IndexError as error:
        raise RuntimeBindingError("Codex rolling catalog has no owned cache root") from error
    rolling_plugins._unlinked_ancestors(cache)
    directory = cache / "sessions" / secrets.token_hex(16)
    rolling_plugins._unlinked_ancestors(directory)
    directory.mkdir(parents=True)
    if os.name != "nt":
        directory.chmod(0o700)
    return directory


def _runtime_catalog(prepared: rolling_plugins.Prepared, directory: Path,
                     aliases: Mapping[str, str]) -> Path:
    packages = []
    for root in prepared.selected_roots:
        name, marketplace = root.identity.rsplit("@", 1)
        packages.append(rolling_plugins.Package(
            f"{name}@{aliases[marketplace]}", aliases[marketplace], root.repository,
            root.revision, ".", root.root,
        ))
    generated, _roots = rolling_plugins._projection("codex", packages, prepared.catalog_root.parents[2])
    catalog = directory / "catalog"
    rolling_plugins._write_tree(catalog, rolling_plugins._tree_bytes(generated))
    return catalog


def _configuration_value(configuration: Mapping[str, object], identity: str) -> dict[str, object]:
    value = configuration.get(identity)
    if value is None:
        return {}
    if isinstance(value, bool):
        return {"enabled": value}
    if not isinstance(value, dict):
        raise RuntimeBindingError(f"Codex effective configuration has invalid plugin settings for {identity}")
    return dict(value)


def _marketplace_value(configuration: Mapping[str, object], marketplace: str) -> dict[str, object]:
    value = configuration.get(marketplace)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise RuntimeBindingError(f"Codex effective configuration has invalid marketplace settings for {marketplace}")
    return dict(value)


def _runtime_arguments(prepared: rolling_plugins.Prepared, selection: Mapping[str, object],
                       catalog: Path, aliases: Mapping[str, str], arguments: Sequence[str]) -> tuple[str, ...]:
    try:
        maintenance = codex_marketplace_sync.maintenance_arguments(arguments)
    except codex_marketplace_sync.SyncError as error:
        raise RuntimeBindingError(str(error)) from None
    plugin_configuration = selection.get("effective_plugin_configuration", {})
    marketplaces = selection.get("effective_marketplace_configuration", {})
    if not isinstance(plugin_configuration, dict) or not isinstance(marketplaces, dict):
        raise RuntimeBindingError("Codex effective configuration did not preserve plugin settings")
    plugins = dict(plugin_configuration)
    configured_marketplaces = dict(marketplaces)
    for marketplace, alias in sorted(aliases.items()):
        value = _marketplace_value(marketplaces, marketplace)
        value.update({"source_type": "local", "source": str(catalog / alias)})
        configured_marketplaces[alias] = value
    for root in prepared.selected_roots:
        name, marketplace = root.identity.rsplit("@", 1)
        alias_identity = f"{name}@{aliases[marketplace]}"
        original = _configuration_value(plugin_configuration, root.identity)
        logical = dict(original)
        logical["enabled"] = False
        original["enabled"] = True
        plugins[root.identity] = logical
        plugins[alias_identity] = original
    return (*maintenance, "-c", f"marketplaces={toml_value(configured_marketplaces)}", "-c",
            f"plugins={toml_value(plugins)}")


def _runtime_prepared(prepared: rolling_plugins.Prepared, selection: Mapping[str, object], catalog: Path,
                      aliases: Mapping[str, str], arguments: Sequence[str]) -> rolling_plugins.Prepared:
    roots = []
    selections = []
    for root in prepared.selected_roots:
        name, marketplace = root.identity.rsplit("@", 1)
        identity = f"{name}@{aliases[marketplace]}"
        roots.append(rolling_plugins.VerifiedRoot(identity, root.root, root.revision, root.repository))
        selections.append(rolling_plugins.Selection(identity, root.repository, aliases[marketplace]))
    return rolling_plugins.Prepared(
        "codex", _runtime_arguments(prepared, selection, catalog, aliases, arguments), tuple(roots), catalog,
        {}, tuple(selections), prepared.source_revisions, prepared.plugins_root, prepared.deadline,
    )


def _disabled_hook_states(hook_state: Mapping[str, object], identities: Mapping[str, str]) -> dict[str, object]:
    mapped = {}
    for key, value in hook_state.items():
        if not isinstance(key, str) or not isinstance(value, dict) or value.get("enabled") is not False:
            continue
        for original, alias in identities.items():
            if key.startswith(original + ":"):
                mapped[alias + key[len(original):]] = dict(value)
                break
    return mapped


def _with_hook_state(prepared: rolling_plugins.Prepared, state: Mapping[str, object]) -> rolling_plugins.Prepared:
    arguments = (*prepared.launch_args, "-c", f"hooks.state={toml_value(dict(state))}")
    return rolling_plugins.Prepared(
        prepared.host, arguments, prepared.selected_roots, prepared.catalog_root, prepared.environment,
        prepared.selections, prepared.source_revisions, prepared.plugins_root, prepared.deadline, prepared.disabled,
    )


def _runtime_hook_state(disabled: Mapping[str, object], updates: Mapping[str, object]) -> dict[str, object]:
    state = dict(disabled)
    for key, update in updates.items():
        previous = state.get(key)
        if isinstance(previous, dict) and previous.get("enabled") is False and isinstance(update, dict):
            merged = dict(previous)
            merged.update(update)
            state[key] = merged
        else:
            state[key] = update
    return state


def _verify_trust(executable: str, project: Path, prepared: rolling_plugins.Prepared,
                  disabled: Mapping[str, object]) -> None:
    timeout = prepared.deadline.remaining() if prepared.deadline is not None else codex_hook_trust.TIMEOUT
    with codex_hook_trust.AppServer(executable, project, prepared.launch_args, prepared.environment, timeout) as server:
        listing = server.request("hooks/list", {"cwds": [str(project)]})
    seen = set()
    for entry in listing.get("data", ()):
        for hook in entry.get("hooks", ()):
            identity = hook.get("pluginId")
            if identity not in {root.identity for root in prepared.selected_roots}:
                continue
            key = hook.get("key")
            if not isinstance(key, str):
                raise RuntimeBindingError("Codex runtime hook inventory has an invalid key")
            seen.add(identity)
            expected_disabled = isinstance(disabled.get(key), dict) and disabled[key].get("enabled") is False
            if expected_disabled:
                if hook.get("enabled") is not False:
                    raise RuntimeBindingError(f"Codex runtime did not preserve disabled hook {key}")
            elif hook.get("enabled") and hook.get("trustStatus") in {"untrusted", "modified"}:
                raise RuntimeBindingError(f"Codex runtime did not trust hook {key}")


def _refresh_coordinator(executable: str, project: Path, configuration: Path,
                         prepared: rolling_plugins.Prepared) -> None:
    roots = tuple(root for root in prepared.selected_roots
                  if root.identity == "machine@tj-agents")
    if roots:
        identities = {root.identity for root in roots}
        coordinator = replace(prepared, selected_roots=roots,
                              selections=tuple(item for item in prepared.selections if item.identity in identities))
        rolling_plugins.materialize_native(coordinator, "codex", configuration, project, executable)


def _unmanaged_roots(executable: str, project: Path, configuration: Path,
                     prepared: rolling_plugins.Prepared) -> tuple[Path, ...]:
    inventory = rolling_plugins._native(
        [executable, *prepared.launch_args, "plugin", "list", "--json"], project,
        prepared.environment, prepared.deadline or rolling_plugins.Deadline(), True,
    )
    managed = {root.identity for root in prepared.selected_roots}
    cache = (configuration / "plugins" / "cache").resolve()
    roots = []
    for item in rolling_plugins._codex_inventory_entries(inventory):
        if not isinstance(item, dict) or not item.get("installed") or not item.get("enabled") or item.get("pluginId") in managed:
            continue
        components = (item.get("marketplaceName"), item.get("name"), item.get("version"))
        if not all(isinstance(value, str) and rolling_plugins._cache_component(value) == value for value in components[:2]):
            raise RuntimeBindingError("Codex unmanaged plugin inventory has an invalid cache path")
        version = components[2]
        if not isinstance(version, str) or not version or version in {".", ".."} or any(
                character in "/\\:\0" or ord(character) < 32 for character in version):
            raise RuntimeBindingError("Codex unmanaged plugin inventory has an invalid cache path")
        path = cache.joinpath(*components).resolve(strict=True)
        if path.relative_to(cache).parts != components or not path.is_dir():
            raise RuntimeBindingError("Codex unmanaged plugin root escapes its native cache path")
        if path not in roots:
            roots.append(path)
    return tuple(roots)


def _write_receipt(directory: Path, configuration: Path, prepared: rolling_plugins.Prepared,
                   unmanaged_roots: Sequence[Path] = ()) -> tuple[Path, str]:
    roots = [str(root.root.resolve()) for root in prepared.selected_roots]
    payload = {
        "schema_version": 1,
        "codex_home": str(configuration.resolve()),
        "catalog": str(prepared.catalog_root.resolve()),
        "roots": roots,
        "unmanaged_roots": [str(root.resolve()) for root in unmanaged_roots],
    }
    encoded = (json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")
    receipt = directory / "runtime-receipt.json"
    receipt.write_bytes(encoded)
    if os.name != "nt":
        receipt.chmod(0o600)
    return receipt, hashlib.sha256(encoded).hexdigest()


def prepare_runtime(executable: str, project: Path, configuration: Path, logical: rolling_plugins.Prepared,
                    selection: Mapping[str, object], arguments: Sequence[str]) -> RuntimeBinding:
    if not logical.selected_roots:
        raise RuntimeBindingError("Codex runtime aliases require selected packages")
    _refresh_coordinator(executable, project, configuration, logical)
    directory = _runtime_directory(logical)
    aliases = {
        marketplace: _runtime_marketplace(marketplace, directory.name)
        for marketplace in sorted({root.identity.rsplit("@", 1)[1] for root in logical.selected_roots})
    }
    try:
        catalog = _runtime_catalog(logical, directory, aliases)
        runtime = _runtime_prepared(logical, selection, catalog, aliases, arguments)
        runtime = rolling_plugins.materialize_native(runtime, "codex", configuration, project, executable)
        hook_state = selection.get("hook_state", {})
        if not isinstance(hook_state, dict):
            raise RuntimeBindingError("Codex effective configuration has invalid hooks.state")
        updates = codex_hook_trust.apply_trust(
            executable, project, preview=True, verified_roots=runtime.selected_roots,
            launch_args=runtime.launch_args, environment=runtime.environment,
            timeout=runtime.deadline.remaining() if runtime.deadline is not None else None,
        )
        disabled = _disabled_hook_states(hook_state, {
            root.identity: runtime.selected_roots[index].identity
            for index, root in enumerate(logical.selected_roots)
        })
        state = _runtime_hook_state(disabled, updates)
        runtime = _with_hook_state(runtime, state)
        _verify_trust(executable, project, runtime, disabled)
        unmanaged = _unmanaged_roots(executable, project, configuration, runtime)
        receipt, digest = _write_receipt(directory, configuration, runtime, unmanaged)
        return RuntimeBinding(runtime, directory, aliases, receipt, digest, state)
    except BaseException:
        try:
            cleanup_runtime(RuntimeBinding(logical, directory, aliases, directory / "runtime-receipt.json", "", {}), configuration)
        except BaseException:
            pass
        raise


def cleanup_runtime(binding: RuntimeBinding, configuration: Path) -> None:
    cache = configuration / "plugins" / "cache"
    for marketplace in sorted(set(binding.aliases.values())):
        path = cache / marketplace
        if path.exists():
            rolling_plugins._remove_cache_tree(path, cache)
    rolling_cache = binding.directory.parents[1]
    if binding.directory.exists():
        rolling_plugins._remove_cache_tree(binding.directory, rolling_cache)

