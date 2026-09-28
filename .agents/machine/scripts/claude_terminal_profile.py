#!/usr/bin/env python3
"""Keep PowerShell profiles loading the installed machine plugin's `claude` launcher."""

from __future__ import annotations

import argparse
import codecs
import os
from pathlib import Path
import sys

START = "# >>> base-agents claude launcher >>>"
END = "# <<< base-agents claude launcher <<<"
OPT_OUT_ENV = "BASE_AGENTS_CLAUDE_PROFILE"
BLOCK = "\r\n".join((
    START,
    "$baseAgentsClaudeProfile = $null",
    "try {",
    "    $baseAgentsClaudePlugins = if ($env:CLAUDE_CODE_PLUGIN_CACHE_DIR) { $env:CLAUDE_CODE_PLUGIN_CACHE_DIR }"
    " elseif ($env:CLAUDE_CONFIG_DIR) { Join-Path $env:CLAUDE_CONFIG_DIR 'plugins' }"
    " else { Join-Path $env:USERPROFILE '.claude\\plugins' }",
    "    $baseAgentsClaudeMachine = @((Get-Content -LiteralPath (Join-Path $baseAgentsClaudePlugins"
    " 'installed_plugins.json') -Raw -ErrorAction Stop | ConvertFrom-Json).plugins.'machine@base-agents' |"
    " Where-Object { $_.scope -eq 'user' })[0]",
    "    $baseAgentsClaudeProfile = Join-Path $baseAgentsClaudeMachine.installPath"
    " 'resources\\machine\\scripts\\claude-profile.ps1'",
    "} catch { }",
    "if ($baseAgentsClaudeProfile -and (Test-Path -LiteralPath $baseAgentsClaudeProfile)) {"
    " . $baseAgentsClaudeProfile }",
    END,
))


def documents_directory() -> Path:
    import ctypes

    buffer = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) != 0 or not buffer.value:
        raise OSError("the Documents folder could not be resolved")
    return Path(buffer.value)


def profile_paths(documents: Path) -> list[Path]:
    return [documents / edition / "Microsoft.PowerShell_profile.ps1" for edition in ("PowerShell", "WindowsPowerShell")]


def ensure(path: Path) -> bool:
    raw = path.read_bytes() if path.is_file() else b""
    bom = raw.startswith(codecs.BOM_UTF8)
    text = raw[len(codecs.BOM_UTF8):].decode("utf-8") if bom else raw.decode("utf-8")
    if text.count(START) != text.count(END) or text.count(START) > 1:
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
    temporary.write_bytes((codecs.BOM_UTF8 if bom else b"") + updated.encode("utf-8"))
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
        changed = [path for path in paths if ensure(path)]
    except (OSError, UnicodeError, ValueError) as error:
        print(f"standards: the PowerShell claude launcher was not installed ({error})")
        return 0
    if changed:
        print(
            "standards: new PowerShell terminals now refresh Claude plugins before `claude` starts "
            f"({', '.join(str(path) for path in changed)})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
