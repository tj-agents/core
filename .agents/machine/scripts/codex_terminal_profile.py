#!/usr/bin/env python3
"""Install minimal terminal adapters for the active machine plugin's ``codex`` launcher."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from claude_terminal_profile import BOOTSTRAP, documents_directory, profile_encoding, profile_paths


START = "# >>> base-agents codex launcher >>>"
END = "# <<< base-agents codex launcher <<<"
OPT_OUT_ENV = "BASE_AGENTS_CODEX_PROFILE"

POWERSHELL_BLOCK = "\r\n".join((
    START,
    "$baseAgentsPython = $null",
    "$baseAgentsWindows = $IsWindows -or $env:OS -eq 'Windows_NT'",
    "foreach ($baseAgentsName in $(if ($baseAgentsWindows) { @('python', 'python3', 'py') } else { @('python3', 'python') })) {",
    "    foreach ($baseAgentsCandidate in @(Get-Command $baseAgentsName -CommandType Application -ErrorAction SilentlyContinue)) {",
    "        if ($baseAgentsWindows -and $baseAgentsCandidate.Source -match '\\\\WindowsApps\\\\') { continue }",
    "        $baseAgentsArguments = if ($baseAgentsName -eq 'py') { @('-3') } else { @() }",
    "        & $baseAgentsCandidate.Source @baseAgentsArguments -I -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>$null",
    "        if ($LASTEXITCODE -eq 0) { $baseAgentsPython = [pscustomobject]@{ Path = $baseAgentsCandidate.Source; Arguments = $baseAgentsArguments }; break }",
    "    }",
    "    if ($baseAgentsPython) { break }",
    "}",
    "$baseAgentsBootstrap = @'",
    BOOTSTRAP,
    "'@",
    "if ($PSVersionTable.PSVersion -lt [version]'7.3' -or (Get-Variable PSNativeCommandArgumentPassing -ValueOnly -ErrorAction SilentlyContinue) -eq 'Legacy') {",
    '    $baseAgentsBootstrap = $baseAgentsBootstrap -replace \'(\\\\*)"\', \'$1$1\\"\'',
    '}',
    "function Invoke-BaseAgentsBootstrap {",
    "    param([string]$baseAgentsKind, [string]$baseAgentsTarget, [string]$baseAgentsProject, [string[]]$baseAgentsArguments, [object]$baseAgentsStatus)",
    "    $baseAgentsStatus.Ran = $false",
    "    $baseAgentsStatus.ExitCode = 125",
    "    $baseAgentsPreviousPayload = [Environment]::GetEnvironmentVariable('BASE_AGENTS_TERMINAL_PAYLOAD', 'Process')",
    "    $baseAgentsHadPayload = $null -ne $baseAgentsPreviousPayload",
    "    $baseAgentsPayload = [ordered]@{ kind = $baseAgentsKind; target = $baseAgentsTarget; project = $baseAgentsProject; arguments = @($baseAgentsArguments) } | ConvertTo-Json -Compress",
    "    try {",
    "        $env:BASE_AGENTS_TERMINAL_PAYLOAD = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($baseAgentsPayload))",
    "        & $baseAgentsPython.Path @($baseAgentsPython.Arguments) -I -B -c $baseAgentsBootstrap --payload --probe",
    "        if ($LASTEXITCODE -eq 0) {",
    "            $env:BASE_AGENTS_TERMINAL_PAYLOAD = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($baseAgentsPayload))",
    "            & $baseAgentsPython.Path @($baseAgentsPython.Arguments) -I -B -c $baseAgentsBootstrap --payload",
    "            $baseAgentsStatus.Ran = $true",
    "            $baseAgentsStatus.ExitCode = $LASTEXITCODE",
    "            return",
    "        }",
    "        return",
    "    } finally {",
    "        if ($baseAgentsHadPayload) { $env:BASE_AGENTS_TERMINAL_PAYLOAD = $baseAgentsPreviousPayload } else { Remove-Item Env:BASE_AGENTS_TERMINAL_PAYLOAD -ErrorAction SilentlyContinue }",
    "    }",
    "}",
    "function global:codex {",
    "    $baseAgentsTarget = @(Get-Command codex -All -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)[0]",
    "    if (-not $baseAgentsTarget) { Write-Error 'codex executable not found on PATH'; return }",
    "    if ($baseAgentsPython) {",
    "        $baseAgentsStatus = [pscustomobject]@{ Ran = $false; ExitCode = 125 }",
    "        Invoke-BaseAgentsBootstrap -baseAgentsKind 'codex' -baseAgentsTarget $baseAgentsTarget.Source -baseAgentsProject (Get-Location).Path -baseAgentsArguments (@($args)) -baseAgentsStatus $baseAgentsStatus",
    "        if ($baseAgentsStatus.Ran) { return }",
    "    } else { Write-Warning 'standards: no usable Python was found; running the typed CLI without refresh' }",
    "    & $baseAgentsTarget.Source @args",
    "}",
    "function global:codex-hooks {",
    "    $baseAgentsTarget = @(Get-Command codex -All -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)[0]",
    "    if (-not $baseAgentsTarget -or -not $baseAgentsPython) { Write-Error 'Codex hook-control utility is not installed'; return }",
    "    $baseAgentsStatus = [pscustomobject]@{ Ran = $false; ExitCode = 125 }",
    "    Invoke-BaseAgentsBootstrap -baseAgentsKind 'codex-hooks' -baseAgentsTarget $baseAgentsTarget.Source -baseAgentsProject (Get-Location).Path -baseAgentsArguments (@($args)) -baseAgentsStatus $baseAgentsStatus",
    "    if ($baseAgentsStatus.Ran) { return }",
    "}",
    END,
))

BASH_BLOCK = "\n".join((
    START,
    "_base_agents_python() {",
    "  local candidate",
    "  for candidate in python3 python; do",
    "    command -v \"$candidate\" >/dev/null 2>&1 && \"$candidate\" -I -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1 && { command -v \"$candidate\"; return; }",
    "  done",
    "  return 1",
    "}",
    "_base_agents_bootstrap='" + BOOTSTRAP.replace("'", "'\\''") + "'",
    "codex() {",
    "  local target python",
    "  target=$(type -P codex) || { printf '%s\\n' 'codex executable not found on PATH' >&2; return 127; }",
    "  if python=$(_base_agents_python); then",
    "    if \"$python\" -I -B -c \"$_base_agents_bootstrap\" --probe codex \"$target\" \"$PWD\"; then",
    "      if \"$python\" -I -B -c \"$_base_agents_bootstrap\" codex \"$target\" \"$PWD\" \"$@\"; then return 0; else return $?; fi",
    "    fi",
    "  else printf '%s\\n' 'standards: no usable Python was found; running the typed CLI without refresh' >&2; fi",
    "  \"$target\" \"$@\"",
    "}",
    "codex-hooks() {",
    "  local target python",
    "  target=$(type -P codex) || { printf '%s\\n' 'Codex hook-control utility is not installed' >&2; return 1; }",
    "  python=$(_base_agents_python) || { printf '%s\\n' 'Codex hook-control utility requires Python 3.9 or newer' >&2; return 1; }",
    "  \"$python\" -I -B -c \"$_base_agents_bootstrap\" codex-hooks \"$target\" \"$PWD\" \"$@\"",
    "}",
    END,
))

BLOCK = POWERSHELL_BLOCK


def terminal_paths(home: Path, documents: Path | None = None) -> list[tuple[Path, str]]:
    if documents is not None:
        return [(path, POWERSHELL_BLOCK) for path in profile_paths(documents)]
    if os.name == "nt":
        return [(path, POWERSHELL_BLOCK) for path in profile_paths(documents or documents_directory())]
    return [
        (home / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1", POWERSHELL_BLOCK),
        (home / ".bashrc", BASH_BLOCK),
    ]


def ensure(path: Path, block: str = POWERSHELL_BLOCK) -> bool:
    raw = path.read_bytes() if path.is_file() else b""
    encoding = profile_encoding(raw)
    text = raw.decode(encoding)
    starts, ends = text.count(START), text.count(END)
    if starts != ends or starts > 1 or (starts and text.index(END) < text.index(START)):
        raise ValueError(f"malformed launcher block in {path}")
    if START in text:
        before, rest = text.split(START, 1)
        body, after = rest.split(END, 1)
        if (START + body + END).replace("\r\n", "\n") == block.replace("\r\n", "\n"):
            return False
        updated = before + block + after
    else:
        prefix = text.rstrip()
        newline = "\r\n" if "\r\n" in text or path.suffix.casefold() == ".ps1" else "\n"
        updated = (prefix + newline * 2 if prefix else "") + block + newline
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(updated.encode(encoding))
    os.replace(temporary, path)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--documents", type=Path)
    parser.add_argument("--home", type=Path)
    arguments = parser.parse_args(argv)
    if os.environ.get(OPT_OUT_ENV, "").strip().lower() == "off":
        return 0
    try:
        paths = terminal_paths(arguments.home or Path.home(), arguments.documents)
    except OSError as error:
        print(f"standards: the Codex terminal launchers were not installed ({error})")
        return 0
    changed = []
    for path, block in paths:
        try:
            if ensure(path, block):
                changed.append(path)
        except (OSError, UnicodeError, ValueError) as error:
            print(f"standards: the Codex terminal launcher was not installed in {path} ({error})")
    if changed:
        print(f"standards: new terminals now refresh Codex plugins before `codex` starts ({', '.join(str(path) for path in changed)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
