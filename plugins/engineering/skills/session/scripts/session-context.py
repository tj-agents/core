import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


IDENTITY = "engineering:session"
SESSION_START_HEADINGS = (
    "## When the user calls out a mistake",
    "## Select the engineering lifecycle before the first edit",
)


def section(body, heading):
    match = re.search(rf"(?m)^{re.escape(heading)}[ \t]*$", body)
    if match is None:
        raise ValueError(f"missing section {heading!r}")
    following = re.search(r"(?m)^## ", body[match.end():])
    text = body[match.end():match.end() + following.start() if following else len(body)].strip()
    if not text:
        raise ValueError(f"section {heading!r} is empty")
    return f"{heading}\n\n{text}"


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    if sys.version_info < (3, 9):
        print("session: Python 3.9 or newer is required.", file=sys.stderr)
        return 1

    contract = Path(__file__).resolve().parent.parent / "SKILL.md"
    try:
        text = contract.read_text(encoding="utf-8-sig")
        _, body = text.removeprefix("---\n").split("\n---\n", 1)
        if not text.startswith("---\n") or not body.strip():
            raise ValueError("missing frontmatter or contract body")
        sections = "\n\n".join(section(body, heading) for heading in SESSION_START_HEADINGS)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"session: cannot read contract at {contract}: {error}", file=sys.stderr)
        return 1
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    context = f"{IDENTITY} (source SHA-256 {digest})\nSource: {contract}\n\n{sections}"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}},
                     ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
