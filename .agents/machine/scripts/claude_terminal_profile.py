#!/usr/bin/env python3
"""Install minimal terminal adapters for the active machine plugin's ``claude`` launcher."""

from __future__ import annotations

import argparse
import codecs
import os
from pathlib import Path
import sys
import stat
import tempfile

START = "# >>> base-agents claude launcher >>>"
END = "# <<< base-agents claude launcher <<<"
OPT_OUT_ENV = "BASE_AGENTS_CLAUDE_PROFILE"

BOOTSTRAP = r'''# This source string is necessary: the active package's launcher path is unknown until its registry is read.
import base64, json, os, subprocess, sys
from pathlib import Path

payload = sys.argv[1:2] == ["--payload"]
probe = sys.argv[2:3] == ["--probe"] if payload else sys.argv[1:2] == ["--probe"]
if payload:
    try:
        encoded = os.environ.pop("BASE_AGENTS_TERMINAL_PAYLOAD")
        data = json.loads(base64.b64decode(encoded, validate=True).decode("utf-8"))
        kind = data["kind"]
        target = data["target"]
        project = data["project"]
        rest = data.get("arguments", [])
        if rest is None:
            rest = []
        if not all(isinstance(value, str) for value in (kind, target, project)) or not isinstance(rest, list) or not all(isinstance(value, str) for value in rest):
            raise TypeError("payload")
    except (KeyError, TypeError, ValueError, UnicodeError):
        print("standards: terminal launcher arguments are invalid; running the typed CLI without refresh", file=sys.stderr)
        sys.exit(1 if probe else 125)
else:
    kind, target, project, *rest = sys.argv[2 if probe else 1:]
typed_target = target
hooks = kind == "codex-hooks"
if hooks:
    kind = "codex"
def unavailable(message):
    print("standards: " + message + "; running the typed CLI without refresh", file=sys.stderr)
    sys.exit(1 if probe else 125)

if kind == "claude":
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
    plugins = Path(os.environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR", config / "plugins"))
    try:
        registry = json.loads((plugins / "installed_plugins.json").read_text(encoding="utf-8-sig"))
        if not isinstance(registry, dict) or not isinstance(registry.get("plugins"), dict):
            raise TypeError("registry root")
        entries = registry["plugins"].get("machine@base-agents")
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            raise TypeError("plugin entries")
        root = next(Path(entry["installPath"]) for entry in entries if entry.get("scope") == "user" and entry.get("installPath"))
    except OSError as error:
        unavailable("Claude plugin registry could not be read (" + str(error) + ")")
    except (ValueError, TypeError, KeyError):
        unavailable("Claude plugin registry is malformed")
    except StopIteration:
        unavailable("the active machine Claude package is not installed")
else:
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    try:
        # The npm .cmd/.ps1 entry point is not suitable for maintenance. Locate its vendored native
        # executable before inventory; final typed execution still receives the original target.
        candidate = Path(target)
        shim = candidate.suffix.casefold() in {".cmd", ".bat", ".ps1"}
        if not shim:
            try:
                with candidate.open("rb") as handle:
                    shim = handle.read(2) == b"#!"
            except OSError:
                shim = True
        if shim:
            name = "codex.exe" if os.name == "nt" else "codex"
            roots = (candidate.parent / "node_modules" / "@openai" / "codex", Path(os.path.realpath(target)).parent.parent)
            natives = []
            for root in roots:
                natives.extend(sorted(root.glob("node_modules/@openai/codex-*/vendor/*/bin/" + name)))
            target = str(next(path for path in natives if path.is_file()))
        result = subprocess.run([target, "plugin", "list", "--json"], capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=10)
        if result.returncode:
            raise RuntimeError((result.stderr or result.stdout).strip() or "Codex returned " + str(result.returncode))
        inventory = json.loads(result.stdout)
        if not isinstance(inventory, dict) or not isinstance(inventory.get("installed"), list):
            raise TypeError("inventory")
        installed = inventory["installed"]
        if any(not isinstance(item, dict) for item in installed):
            raise TypeError("installed plugin")
        entry = next(item for item in installed if item.get("pluginId") == "machine@base-agents" and item.get("enabled"))
        version = str(entry["version"])
        if not version or "/" in version or "\\" in version or ".." in version:
            raise ValueError("unsafe plugin version")
        root = home / "plugins" / "cache" / "base-agents" / "machine" / version
    except StopIteration:
        unavailable("a native Codex executable could not be found beside the selected shim")
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        unavailable("Codex package inventory failed (" + str(error) + ")")
script = root / "resources" / "machine" / "scripts" / f"{kind}_terminal_launcher.py"
if not script.is_file():
    unavailable("the active machine " + kind + " launcher is unavailable")
if probe:
    sys.exit(0)
launcher = [sys.executable, "-I", "-B", str(script), "--project", project, "--target", typed_target]
if hooks:
    launcher += ["--hooks", "--", *rest]
else:
    launcher += ["--", *rest]
sys.exit(subprocess.run(launcher).returncode)
'''

POWERSHELL_BLOCK = "\r\n".join((
    START,
    "$baseAgentsPython = $null",
    "$baseAgentsWindows = $IsWindows -or $env:OS -eq 'Windows_NT'",
    "foreach ($baseAgentsName in $(if ($baseAgentsWindows) { @('python', 'python3', 'py') } else { @('python3', 'python') })) {",
    "    foreach ($baseAgentsCandidate in @(Get-Command $baseAgentsName -All -CommandType Application -ErrorAction SilentlyContinue)) {",
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
    "function global:claude {",
    "    $baseAgentsTarget = @(Get-Command claude -All -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)[0]",
    "    if (-not $baseAgentsTarget) { Write-Error 'claude executable not found on PATH'; return }",
    "    if ($baseAgentsPython) {",
    "        $baseAgentsStatus = [pscustomobject]@{ Ran = $false; ExitCode = 125 }",
    "        Invoke-BaseAgentsBootstrap -baseAgentsKind 'claude' -baseAgentsTarget $baseAgentsTarget.Source -baseAgentsProject (Get-Location).Path -baseAgentsArguments (@($args)) -baseAgentsStatus $baseAgentsStatus",
    "        if ($baseAgentsStatus.Ran) { return }",
    "    } else { Write-Warning 'standards: no usable Python was found; running the typed CLI without refresh' }",
    "    & $baseAgentsTarget.Source @args",
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
    "claude() {",
    "  local target python",
    "  target=$(type -P claude) || { printf '%s\\n' 'claude executable not found on PATH' >&2; return 127; }",
    "  if python=$(_base_agents_python); then",
    "    if \"$python\" -I -B -c \"$_base_agents_bootstrap\" --probe claude \"$target\" \"$PWD\"; then",
    "      if \"$python\" -I -B -c \"$_base_agents_bootstrap\" claude \"$target\" \"$PWD\" \"$@\"; then return 0; else return $?; fi",
    "    fi",
    "  else printf '%s\\n' 'standards: no usable Python was found; running the typed CLI without refresh' >&2; fi",
    "  \"$target\" \"$@\"",
    "}",
    END,
))

BLOCK = POWERSHELL_BLOCK


def documents_directory() -> Path:
    import ctypes

    buffer = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) != 0 or not buffer.value:
        raise OSError("the Documents folder could not be resolved")
    return Path(buffer.value)


def profile_paths(documents: Path) -> list[Path]:
    return [documents / edition / "Microsoft.PowerShell_profile.ps1" for edition in ("PowerShell", "WindowsPowerShell")]


def terminal_paths(home: Path, documents: Path | None = None) -> list[tuple[Path, str]]:
    if documents is not None:
        return [(path, POWERSHELL_BLOCK) for path in profile_paths(documents)]
    if os.name == "nt":
        return [(path, POWERSHELL_BLOCK) for path in profile_paths(documents or documents_directory())]
    return [
        (home / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1", POWERSHELL_BLOCK),
        (home / ".bashrc", BASH_BLOCK),
    ]


def profile_encoding(raw: bytes) -> str:
    if raw.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return "utf-16"
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return "mbcs" if os.name == "nt" else "latin-1"
    return "utf-8"


def write_profile(path: Path, data: bytes) -> None:
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            if os.name != "nt":
                os.fchmod(stream.fileno(), mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


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
    write_profile(path, updated.encode(encoding))
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
        print(f"standards: the PowerShell claude launcher was not installed ({error})")
        return 0
    changed = []
    for path, block in paths:
        try:
            if ensure(path, block):
                changed.append(path)
        except (OSError, UnicodeError, ValueError) as error:
            print(f"standards: the PowerShell claude launcher was not installed in {path} ({error})")
    if changed:
        print(
            "standards: new terminals now refresh Claude plugins before `claude` starts "
            f"({', '.join(str(path) for path in changed)})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
