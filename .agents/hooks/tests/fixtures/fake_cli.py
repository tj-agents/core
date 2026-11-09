"""A recorded stand-in for the tj and agent-store CLIs, installed as executables on a temporary PATH."""

import contextlib
import json
import os
import sys
from pathlib import Path

RESPONSES = "FAKE_CLI_RESPONSES"
CALLS = "FAKE_CLI_CALLS"


def install(directory, responses, names=("tj", "agent-store")):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "responses.json").write_text(json.dumps(responses), encoding="utf-8")
    for name in names:
        if os.name == "nt":
            (directory / f"{name}.cmd").write_text(
                f'@echo off\r\n"{sys.executable}" "{Path(__file__).resolve()}" {name} %*\r\nexit /b %ERRORLEVEL%\r\n',
                encoding="utf-8",
            )
        else:
            launcher = directory / name
            launcher.write_text(
                f'#!/bin/sh\nexec "{sys.executable}" "{Path(__file__).resolve()}" {name} "$@"\n', encoding="utf-8"
            )
            launcher.chmod(0o755)
    return {RESPONSES: str(directory / "responses.json"), CALLS: str(directory / "calls.jsonl")}


@contextlib.contextmanager
def environment(values):
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def calls(installed):
    path = Path(installed[CALLS])
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    command = " ".join(sys.argv[1:])
    with Path(os.environ[CALLS]).open("a", encoding="utf-8") as log:
        log.write(json.dumps({"command": command, "cwd": str(Path.cwd())}) + "\n")
    responses = json.loads(Path(os.environ[RESPONSES]).read_text(encoding="utf-8"))
    response = responses.get(command)
    if response is None:
        sys.stderr.write(json.dumps({"error": f"unexpected fake command {command}"}))
        return 2
    stdout = response.get("stdout", "")
    sys.stdout.write(stdout if isinstance(stdout, str) else json.dumps(stdout))
    sys.stderr.write(response.get("stderr", ""))
    return response.get("code", 0)


if __name__ == "__main__":
    raise SystemExit(main())
