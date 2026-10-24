import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


IDENTITY = "workflow:session-lifecycle"
FINISH_HEADING = "## Finish the session"
FINISH_REMINDER = "Nothing owned left to do before this reply? Select `machine:close`."


def finish_section(body):
    heading = re.search(rf"(?m)^{re.escape(FINISH_HEADING)}[ \t]*$", body)
    if heading is None:
        raise ValueError(f"missing section {FINISH_HEADING!r}")
    following = re.search(r"(?m)^## ", body[heading.end():])
    section = body[heading.end():heading.end() + following.start() if following else len(body)].strip()
    if not section:
        raise ValueError(f"section {FINISH_HEADING!r} is empty")
    return section


def emit(event, context):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}},
                     ensure_ascii=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", action="store_true")
    args = parser.parse_args()
    if sys.version_info < (3, 9):
        print("session-lifecycle: Python 3.9 or newer is required.", file=sys.stderr)
        return 1
    if args.prompt:
        emit("UserPromptSubmit", FINISH_REMINDER)
        return 0

    contract = Path(__file__).resolve().parent.parent / "SKILL.md"
    try:
        text = contract.read_text(encoding="utf-8-sig")
        _, body = text.removeprefix("---\n").split("\n---\n", 1)
        if not text.startswith("---\n") or not body.strip():
            raise ValueError("missing frontmatter or contract body")
        section = finish_section(body)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"session-lifecycle: cannot read contract at {contract}: {error}", file=sys.stderr)
        return 1
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    emit("SessionStart", f"{IDENTITY} (source SHA-256 {digest})\nSource: {contract}\n\n{section}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
