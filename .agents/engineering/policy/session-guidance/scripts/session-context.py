"""Emit the selected engineering contract without reading or changing caller state."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


PROMPT_CONTEXT_HEADING = "## When the user calls out a mistake"


def prompt_context(body):
    heading = re.search(rf"(?m)^{re.escape(PROMPT_CONTEXT_HEADING)}[ \t]*$", body)
    if heading is None:
        raise ValueError(f"missing prompt context section {PROMPT_CONTEXT_HEADING!r}")
    next_heading = re.search(r"(?m)^## ", body[heading.end():])
    end = heading.end() + (next_heading.start() if next_heading else len(body[heading.end():]))
    section = body[heading.end():end].strip()
    if not section:
        raise ValueError(f"prompt context section {PROMPT_CONTEXT_HEADING!r} is empty")
    return section


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--instruction-fragment", action="store_true")
    mode.add_argument("--prompt-context", action="store_true")
    args = parser.parse_args()
    if sys.version_info < (3, 9):
        print("session-guidance: Python 3.9 or newer is required.", file=sys.stderr)
        return 1

    contract = Path(__file__).resolve().parent.parent / "SKILL.md"
    try:
        text = contract.read_text(encoding="utf-8-sig")
        _, body = text.removeprefix("---\n").split("\n---\n", 1)
        if not text.startswith("---\n") or not body.strip():
            raise ValueError("missing frontmatter or contract body")
    except (OSError, UnicodeError, ValueError) as error:
        print(f"session-guidance: cannot read contract at {contract}: {error}", file=sys.stderr)
        return 1

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    context = f"engineering:session-guidance (source SHA-256 {digest})\nSource: {contract}\n\n{body.strip()}"
    if args.instruction_fragment:
        print(f"<!-- BEGIN engineering:session-guidance sha256:{digest} -->\n{context}\n<!-- END engineering:session-guidance -->")
    elif args.prompt_context:
        try:
            context = (
                f"engineering:session-guidance (source SHA-256 {digest})\n"
                f"Source: {contract}\n\n{prompt_context(body)}"
            )
        except ValueError as error:
            print(f"session-guidance: {error}", file=sys.stderr)
            return 1
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit", "additionalContext": context
        }}, ensure_ascii=True))
    else:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": context
        }}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
