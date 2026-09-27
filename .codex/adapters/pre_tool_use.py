import json
import subprocess
import sys


def deny(reason):
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
    return 0


def main():
    if len(sys.argv) < 2:
        return deny("The Codex pre-tool standards hook has no target script.")

    try:
        result = subprocess.run(
            [sys.executable, "-B", *sys.argv[1:]],
            input=sys.stdin.buffer.read(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        return deny(f"The Codex pre-tool standards hook could not start: {error}")

    if result.returncode == 0:
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        return 0

    detail = result.stderr.decode("utf-8", errors="replace").strip()
    if result.returncode == 2:
        return deny(detail or "The Codex pre-tool standards hook denied this tool call.")
    return deny(f"The Codex pre-tool standards hook failed with exit code {result.returncode}: {detail}".strip())


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())