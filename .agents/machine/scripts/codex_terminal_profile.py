#!/usr/bin/env python3
"""Keep PowerShell profiles loading the installed machine plugin's Codex launcher."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from claude_terminal_profile import documents_directory, profile_encoding, profile_paths


START = "# >>> base-agents codex launcher >>>"
END = "# <<< base-agents codex launcher <<<"
OPT_OUT_ENV = "BASE_AGENTS_CODEX_PROFILE"
BLOCK = "\r\n".join((
    START,
    "$baseAgentsCodexProfile = $null",
    "try {",
    "    $baseAgentsCodexCommand = @(Get-Command codex -CommandType Application, ExternalScript"
    " -ErrorAction SilentlyContinue)[0]",
    "    if ($baseAgentsCodexCommand) {",
    "        $baseAgentsCodexInventory = & $baseAgentsCodexCommand.Source plugin list --json |"
    " ConvertFrom-Json -ErrorAction Stop",
    "        if ($LASTEXITCODE -eq 0) {",
    "            $baseAgentsCodexMachine = @($baseAgentsCodexInventory.installed |"
    " Where-Object { $_.pluginId -eq 'machine@base-agents' -and $_.enabled })[0]",
    "            if ($baseAgentsCodexMachine.version -match '^[A-Za-z0-9._-]+$') {",
    "                $baseAgentsCodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME }"
    " else { Join-Path $env:USERPROFILE '.codex' }",
    "                $baseAgentsCodexProfile = Join-Path $baseAgentsCodexHome"
    " ('plugins\\cache\\base-agents\\machine\\' + $baseAgentsCodexMachine.version +"
    " '\\resources\\machine\\scripts\\codex-profile.ps1')",
    "            }",
    "        }",
    "    }",
    "} catch { }",
    "if ($baseAgentsCodexProfile -and (Test-Path -LiteralPath $baseAgentsCodexProfile)) {"
    " . $baseAgentsCodexProfile }",
    END,
))


def ensure(path: Path) -> bool:
    raw = path.read_bytes() if path.is_file() else b""
    encoding = profile_encoding(raw)
    text = raw.decode(encoding)
    starts, ends = text.count(START), text.count(END)
    if starts != ends or starts > 1 or (starts and text.index(END) < text.index(START)):
        raise ValueError(f"malformed launcher block in {path}")
    if START in text:
        before, rest = text.split(START, 1)
        body, after = rest.split(END, 1)
        if (START + body + END).replace("\r\n", "\n") == BLOCK.replace("\r\n", "\n"):
            return False
        updated = before + BLOCK + after
    else:
        prefix = text.rstrip()
        updated = (prefix + "\r\n\r\n" if prefix else "") + BLOCK + "\r\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(updated.encode(encoding))
    os.replace(temporary, path)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--documents", type=Path)
    arguments = parser.parse_args(argv)
    if os.environ.get(OPT_OUT_ENV, "").strip().lower() == "off" or (os.name != "nt" and arguments.documents is None):
        return 0
    try:
        paths = profile_paths(arguments.documents or documents_directory())
    except OSError as error:
        print(f"standards: the PowerShell Codex launcher was not installed ({error})")
        return 0
    changed = []
    for path in paths:
        try:
            if ensure(path):
                changed.append(path)
        except (OSError, UnicodeError, ValueError) as error:
            print(f"standards: the PowerShell Codex launcher was not installed in {path} ({error})")
    if changed:
        print("standards: new PowerShell terminals now refresh Codex plugins before `codex` starts "
              f"({', '.join(str(path) for path in changed)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
