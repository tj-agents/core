#!/usr/bin/env python3
"""Compose and render shipped harness permission declarations (`requires.permissions`)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import bootstrap_capabilities as bootstrap


PLUGIN_ROOT_TOKEN = "${PLUGIN_ROOT}"


def _require_tokens(value: Any, label: str) -> None:
    if isinstance(value, str):
        if not value:
            raise bootstrap.BootstrapError(f"{label} must be a non-empty string")
        return
    if isinstance(value, list):
        if not value or any(not isinstance(item, str) or not item for item in value):
            raise bootstrap.BootstrapError(f"{label} must be a list of non-empty strings")
        return
    raise bootstrap.BootstrapError(f"{label} must be a string or a list of strings")


def _require_rule_field(value: Any, label: str) -> None:
    if not isinstance(value, list) or not value:
        raise bootstrap.BootstrapError(f"{label} must be a non-empty list")
    for index, item in enumerate(value):
        _require_tokens(item, f"{label}[{index}]")


def validate_requires(requires: dict, label: str) -> None:
    if not isinstance(requires, dict) or set(requires) != {"marketplaces", "plugins", "hooks", "permissions"}:
        raise bootstrap.BootstrapError(f"{label}: invalid harness requirements")
    if not isinstance(requires["marketplaces"], list) or not isinstance(requires["hooks"], list):
        raise bootstrap.BootstrapError(f"{label}: invalid marketplace or hook requirements")
    bootstrap.require_string_list(requires["plugins"], f"{label}.plugins")
    permissions = requires["permissions"]
    if not isinstance(permissions, dict) or set(permissions) != {"claude_allow", "codex_prefix_rules"}:
        raise bootstrap.BootstrapError(f"{label}: invalid harness permissions")
    bootstrap.require_string_list(permissions["claude_allow"], f"{label}.claude_allow")
    rules = permissions["codex_prefix_rules"]
    if not isinstance(rules, list):
        raise bootstrap.BootstrapError(f"{label}: invalid Codex prefix rules")
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {"pattern", "justification", "match", "not_match"}:
            raise bootstrap.BootstrapError(f"{label}: invalid Codex prefix rule")
        for field in ("pattern", "match", "not_match"):
            _require_rule_field(rule[field], f"{label}.{field}")
        bootstrap.require_string(rule["justification"], f"{label}.justification")


def contains_template(value: Any) -> bool:
    if isinstance(value, str):
        return PLUGIN_ROOT_TOKEN in value
    if isinstance(value, list):
        return any(contains_template(item) for item in value)
    if isinstance(value, dict):
        return any(contains_template(item) for item in value.values())
    return False


def path_spellings(root: Path | str) -> tuple[str, str]:
    text = str(root)
    return text.replace("\\", "/"), text.replace("/", "\\")


def _forward_spelling(template: str, root_forward: str) -> str:
    return template.replace(PLUGIN_ROOT_TOKEN, root_forward).replace("\\", "/")


def _backslash_spelling(template: str, root_backslash: str) -> str:
    return template.replace(PLUGIN_ROOT_TOKEN, root_backslash).replace("/", "\\")


def render_claude_allow(templates: list[str], plugin_root: Path | str) -> list[str]:
    root_forward, root_backslash = path_spellings(plugin_root)
    rendered: list[str] = []
    for template in templates:
        if PLUGIN_ROOT_TOKEN in template:
            rendered.append(_forward_spelling(template, root_forward))
            rendered.append(_backslash_spelling(template, root_backslash))
        else:
            rendered.append(template)
    return rendered


def _render_codex_token(token: Any, plugin_root: Path | str, alternate: bool) -> Any:
    if isinstance(token, list):
        return [_render_codex_token(item, plugin_root, alternate) for item in token]
    if isinstance(token, str) and PLUGIN_ROOT_TOKEN in token:
        root_forward, root_backslash = path_spellings(plugin_root)
        if alternate:
            return [_backslash_spelling(token, root_backslash), _forward_spelling(token, root_forward)]
        return _backslash_spelling(token, root_backslash)
    return token


def render_codex_rule(rule: dict, plugin_root: Path | str) -> dict:
    return {
        "pattern": [_render_codex_token(token, plugin_root, True) for token in rule["pattern"]],
        "justification": rule["justification"],
        "match": [_render_codex_token(example, plugin_root, False) for example in rule["match"]],
        "not_match": [_render_codex_token(example, plugin_root, False) for example in rule["not_match"]],
    }


def render_permissions(permissions: dict, plugin_root: Path | str) -> tuple[list[str], list[dict]]:
    claude_allow = render_claude_allow(permissions["claude_allow"], plugin_root)
    codex_rules = [render_codex_rule(rule, plugin_root) for rule in permissions["codex_prefix_rules"]]
    return claude_allow, codex_rules


def fold_permissions(requirements: list[dict]) -> tuple[list[str], list[dict]]:
    claude_allow: set[str] = set()
    codex_rules: dict[str, dict] = {}
    for requires in requirements:
        claude_allow.update(requires["permissions"]["claude_allow"])
        for rule in requires["permissions"]["codex_prefix_rules"]:
            codex_rules[json.dumps(rule, sort_keys=True)] = rule
    return sorted(claude_allow), [codex_rules[key] for key in sorted(codex_rules)]


def codex_rule_lines(rules: list[dict]) -> list[str]:
    lines: list[str] = []
    for rule in rules:
        lines += [
            "prefix_rule(",
            f"    pattern = {json.dumps(rule['pattern'], ensure_ascii=False)},",
            '    decision = "allow",',
            f"    justification = {json.dumps(rule['justification'], ensure_ascii=False)},",
            f"    match = {json.dumps(rule['match'], ensure_ascii=False)},",
            f"    not_match = {json.dumps(rule['not_match'], ensure_ascii=False)},",
            ")",
            "",
        ]
    return lines
