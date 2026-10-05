"""Emit the selected engineering contract without reading or changing caller state."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instruction-fragment", action="store_true")
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
    else:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": context
        }}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
