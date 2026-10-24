import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys


PROMPT_CONTEXT_HEADINGS = (
    "## When the user calls out a mistake",
    "## A task has an owning lifecycle — load it before the first edit",
    "## Repository routine-decision delegation",
)

SESSION_START_HEADINGS = (
    "## When the user calls out a mistake",
    "## A task has an owning lifecycle — load it before the first edit",
    "## Finish the session",
)


def prompt_context_section(body, heading):
    heading_match = re.search(rf"(?m)^{re.escape(heading)}[ \t]*$", body)
    if heading_match is None:
        raise ValueError(f"missing prompt context section {heading!r}")
    next_heading = re.search(r"(?m)^## ", body[heading_match.end():])
    end = heading_match.end() + (next_heading.start() if next_heading else len(body[heading_match.end():]))
    section = body[heading_match.end():end].strip()
    if not section:
        raise ValueError(f"prompt context section {heading!r} is empty")
    return section


def prompt_context(body):
    return "\n\n".join(
        prompt_context_section(body, heading) for heading in PROMPT_CONTEXT_HEADINGS
    )


def stdin_text():
    if sys.stdin.isatty():
        return None
    value = sys.stdin.read()
    return value if value.strip() else None


def hook_root():
    text = stdin_text()
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"hook payload is not valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("hook payload must be an object")
    value = payload.get("cwd")
    if not isinstance(value, str) or not value:
        raise ValueError("hook payload must provide an absolute cwd")
    root = Path(value)
    if not root.is_absolute() or not root.is_dir():
        raise ValueError(f"hook cwd must be an existing absolute directory: {value!r}")
    return root


def configuration_reader():
    source_agents = Path(__file__).resolve().parents[4]
    candidates = (
        source_agents / "workflows" / "repository_configuration.py",
        source_agents.parent / "workflows" / "repository_configuration.py",
    )
    for path in candidates:
        if path.is_file():
            spec = importlib.util.spec_from_file_location(
                "tj_agents_repository_configuration", path
            )
            if spec is None or spec.loader is None:
                break
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            return module
    raise RuntimeError("repository settings reader is unavailable from this package")


def delegation_context(root):
    try:
        enabled, provenance = configuration_reader().auto_approve_design_provenance(root)
    except (OSError, ValueError, RuntimeError) as error:
        enabled = False
        provenance = f"unavailable; diagnostic=cannot resolve repository routine delegation: {error}"
    return (
        "Repository routine-decision delegation: "
        f"auto_approve_design={str(enabled).lower()}; source={provenance}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--instruction-fragment", action="store_true")
    mode.add_argument("--prompt-context", action="store_true")
    mode.add_argument("--session-start-context", action="store_true")
    args = parser.parse_args()
    if sys.version_info < (3, 9):
        print("session: Python 3.9 or newer is required.", file=sys.stderr)
        return 1

    contract = Path(__file__).resolve().parent.parent / "SKILL.md"
    try:
        text = contract.read_text(encoding="utf-8-sig")
        _, body = text.removeprefix("---\n").split("\n---\n", 1)
        if not text.startswith("---\n") or not body.strip():
            raise ValueError("missing frontmatter or contract body")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"session: cannot read contract at {contract}: {error}", file=sys.stderr)
        return 1

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    context = f"engineering:session (source SHA-256 {digest})\nSource: {contract}\n\n{body.strip()}"
    if args.instruction_fragment:
        print(f"<!-- BEGIN engineering:session sha256:{digest} -->\n{context}\n<!-- END engineering:session -->")
        return 0
    if args.session_start_context:
        try:
            section = "\n\n".join(
                f"{heading}\n\n{prompt_context_section(body, heading)}" for heading in SESSION_START_HEADINGS
            )
        except ValueError as error:
            print(f"session: {error}", file=sys.stderr)
            return 1
        context = f"engineering:session (source SHA-256 {digest})\nSource: {contract}\n\n{section}"
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": context
        }}, ensure_ascii=True))
        return 0
    try:
        root = hook_root()
        dynamic_context = None if root is None else delegation_context(root)
    except ValueError as error:
        dynamic_context = (
            "Repository routine-decision delegation: "
            "auto_approve_design=false; source=unavailable; "
            f"diagnostic={error}"
        )
    if args.prompt_context:
        try:
            context = (
                f"engineering:session (source SHA-256 {digest})\n"
                f"Source: {contract}\n\n{prompt_context(body)}"
            )
        except ValueError as error:
            print(f"session: {error}", file=sys.stderr)
            return 1
        if dynamic_context is not None:
            context = f"{context}\n\n{dynamic_context}"
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit", "additionalContext": context
        }}, ensure_ascii=True))
    else:
        if dynamic_context is not None:
            context = f"{context}\n\n{dynamic_context}"
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": context
        }}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
