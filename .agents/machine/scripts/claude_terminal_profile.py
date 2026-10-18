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

BOOTSTRAP = r'''import base64, json, os, shutil, subprocess, sys, tempfile
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
        print("standards: terminal launcher arguments are invalid; session launch is unavailable", file=sys.stderr)
        sys.exit(1 if probe else 125)
else:
    kind, target, project, *rest = sys.argv[2 if probe else 1:]
typed_target = target
hooks = kind == "codex-hooks"
if hooks:
    kind = "codex"
def unavailable(message):
    print("standards: " + message + "; session launch is unavailable", file=sys.stderr)
    sys.exit(1 if probe else 125)

class Missing(Exception):
    def __init__(self, message, package=None):
        super().__init__(message)
        self.package = package

def repository(source):
    if isinstance(source, dict):
        declared = source.get("repo")
        if isinstance(declared, str):
            parts = declared.strip().split("/")
            if len(parts) == 2 and all(parts):
                return "/".join(part.casefold() for part in parts)
        source = source.get("url") or source.get("source")
    if not isinstance(source, str):
        return None
    value = source.strip().replace("\\\\", "/")
    if value.startswith("git@github.com:"):
        value = value[len("git@github.com:"):]
    elif value.startswith("https://github.com/") or value.startswith("http://github.com/"):
        value = value.split("github.com/", 1)[1]
    else:
        return None
    value = value.rstrip("/")
    if value.endswith(".git"):
        value = value[:-4]
    parts = value.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return "/".join(part.casefold() for part in parts)

def reparse(path):
    try:
        if path.is_symlink():
            return True
        return bool(os.lstat(path).st_file_attributes & 0x400)
    except AttributeError:
        return False

def contained(root, cache):
    root = Path(root).absolute()
    cache = Path(cache).absolute()
    try:
        relative = root.relative_to(cache)
    except ValueError:
        return None
    current = cache
    while True:
        if reparse(current):
            return None
        if current == current.parent:
            break
        current = current.parent
    current = cache
    for part in relative.parts:
        current = current / part
        if reparse(current):
            return None
    try:
        resolved = root.resolve(strict=True)
        resolved.relative_to(cache.resolve(strict=True))
    except (OSError, ValueError):
        return None
    return resolved

def inside(path, parent):
    try:
        Path(path).absolute().relative_to(Path(parent).absolute())
        return True
    except ValueError:
        return False

def enabled_identities(config, project):
    state = {}
    for path in (config / "settings.json", Path(project) / ".claude" / "settings.json",
                 Path(project) / ".claude" / "settings.local.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        enabled = data.get("enabledPlugins") if isinstance(data, dict) else None
        if isinstance(enabled, dict):
            state.update({key: value for key, value in enabled.items() if isinstance(key, str) and isinstance(value, bool)})
    return {identity for identity, value in state.items() if value}

def coordinator(candidates, enabled):
    matching = [candidate for candidate in candidates if candidate[0] in enabled]
    pool = matching or candidates
    unique = {}
    for identity, rank, root in pool:
        previous = unique.get(root)
        if previous is None or (rank, identity) > (previous[1], previous[0]):
            unique[root] = (identity, rank)
    if not unique:
        raise ValueError("no authenticated tj-agents machine coordinator is installed")
    identity, _rank, root = sorted(((identity, rank, root) for root, (identity, rank) in unique.items()),
                                   key=lambda candidate: (-candidate[1], candidate[0], str(candidate[2])))[0]
    return identity, root

def component(value):
    return isinstance(value, str) and value not in ("", ".", "..") and "/" not in value and "\\" not in value

def native_codex(target):
    candidate = Path(target)
    if candidate.suffix.casefold() not in (".cmd", ".bat", ".ps1"):
        return str(candidate)
    name = "codex.exe" if os.name == "nt" else "codex"
    roots = (
        candidate.parent / "node_modules" / "@openai" / "codex",
        Path(os.path.realpath(target)).parent.parent,
    )
    paths = []
    for base in roots:
        paths.extend(path for path in base.glob("node_modules/@openai/codex-*/vendor/*/bin/" + name)
                     if path.is_file())
    if not paths:
        raise ValueError("native Codex executable")
    return str(sorted(set(paths))[0])

def locate():
    if kind == "claude":
        config = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))
        plugins = Path(os.environ.get("CLAUDE_CODE_PLUGIN_CACHE_DIR", config / "plugins"))
        try:
            registry = json.loads((plugins / "installed_plugins.json").read_text(encoding="utf-8-sig"))
            if not isinstance(registry, dict) or not isinstance(registry.get("plugins"), dict):
                raise TypeError("registry root")
            known = json.loads((plugins / "known_marketplaces.json").read_text(encoding="utf-8-sig"))
            if not isinstance(known, dict):
                raise TypeError("marketplace registry")
            candidates = []
            scopes = {}
            for identity in ("machine@tj-agents", "machine@base-agents"):
                marketplace = identity.rsplit("@", 1)[1]
                expected = "tj-agents/marketplace" if marketplace == "tj-agents" else "tj-agents/core"
                entry = known.get(marketplace)
                source = entry.get("source") if isinstance(entry, dict) else None
                if repository(source) != expected:
                    continue
                entries = registry["plugins"].get(identity, [])
                if not isinstance(entries, list):
                    raise TypeError("plugin entries")
                for entry in entries:
                    path = entry.get("installPath") if isinstance(entry, dict) else None
                    if isinstance(path, str):
                        candidate = contained(path, plugins)
                        if candidate is not None and candidate.parent.name == "machine" and (candidate / "catalog" / "catalog.json").is_file():
                            scope = entry.get("scope")
                            project_path = entry.get("projectPath")
                            if scope in ("project", "local"):
                                if not isinstance(project_path, str) or not inside(project, project_path):
                                    continue
                                rank = 2
                                scopes[candidate] = (scope, project_path)
                            else:
                                rank = 1
                                scopes[candidate] = ("user", project)
                            candidates.append((identity, rank, candidate))
            identity, root = coordinator(candidates, enabled_identities(config, project))
            package = (identity, *scopes[root])
        except OSError as error:
            raise Missing("Claude plugin registry could not be read (" + str(error) + ")")
        except (ValueError, TypeError, KeyError):
            raise Missing("Claude plugin registry is malformed")
    else:
        home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        try:
            cache = home / "plugins" / "cache"
            native = subprocess.run([native_codex(typed_target), "plugin", "list", "--json"], capture_output=True,
                                    text=True, encoding="utf-8", errors="replace", timeout=15)
            if native.returncode != 0:
                raise ValueError("native plugin inventory")
            inventory = json.loads(native.stdout)
            installed = inventory.get("installed") if isinstance(inventory, dict) else None
            if not isinstance(installed, list):
                raise TypeError("native plugin inventory")
            candidates = []
            expected = {
                "machine@base-agents": "tj-agents/core",
                "machine@tj-agents": "tj-agents/marketplace",
            }
            for item in installed:
                if not isinstance(item, dict) or item.get("pluginId") not in expected:
                    continue
                marketplace = item.get("marketplaceSource")
                if not isinstance(marketplace, dict) or marketplace.get("sourceType") != "git":
                    continue
                if repository(marketplace.get("source")) != expected[item["pluginId"]]:
                    continue
                marketplace_name = item.get("marketplaceName")
                name = item.get("name")
                version = item.get("version") or "local"
                if not all(component(value) for value in (marketplace_name, name, version)):
                    continue
                root = contained(cache / marketplace_name / name / version, cache)
                if root is not None and root.parent.name == "machine" and (root / "catalog" / "catalog.json").is_file():
                    candidates.append((item["pluginId"], int(item.get("enabled") is True), root))
            identity, root = coordinator(candidates, {identity for identity, enabled, _root in candidates if enabled})
            package = (identity, None, project)
        except (OSError, ValueError, TypeError) as error:
            raise Missing("Codex machine coordinator is unavailable (" + str(error) + ")")
    script = root / "resources" / "machine" / "scripts" / f"{kind}_terminal_launcher.py"
    if not script.is_file():
        raise Missing("the active machine " + kind + " launcher is unavailable", package)
    return package, script

def native_cli():
    if kind == "codex":
        return [native_codex(typed_target)]
    if os.name == "nt" and Path(typed_target).suffix.casefold() == ".ps1":
        shell = shutil.which("powershell.exe")
        if shell is None:
            raise ValueError("Windows PowerShell")
        return [shell, "-NoProfile", "-File", typed_target]
    return [typed_target]

def repair(package):
    identity, scope, directory = package
    marketplace = identity.rsplit("@", 1)[1]
    try:
        executable = native_cli()
    except ValueError:
        return False
    if kind == "claude":
        commands = ([*executable, "plugin", "marketplace", "update", marketplace], [*executable, "plugin", "update", identity, "--scope", scope])
    else:
        commands = ([*executable, "plugin", "marketplace", "upgrade", marketplace], [*executable, "plugin", "add", identity])
    print("standards: reinstalling " + identity + " from its marketplace", file=sys.stderr)
    for command in commands:
        try:
            completed = subprocess.run(command, cwd=directory, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, timeout=180)
        except (OSError, subprocess.SubprocessError):
            return False
        if completed.returncode != 0:
            return False
    return True

def resolve():
    try:
        return locate()
    except Missing as missing:
        if hooks or missing.package is None or not repair(missing.package):
            unavailable(str(missing))
    try:
        return locate()
    except Missing as missing:
        unavailable(str(missing))

def launch(script):
    descriptor, state = tempfile.mkstemp(prefix="base-agents-launch-")
    os.close(descriptor)
    command = [sys.executable, "-I", "-B", str(script), "--project", project, "--target", typed_target]
    command += ["--hooks", "--", *rest] if hooks else ["--", *rest]
    try:
        code = subprocess.run(command, env=dict(os.environ, BASE_AGENTS_LAUNCH_STATE=state)).returncode
        try:
            reached = Path(state).read_text(encoding="utf-8")
        except OSError:
            reached = ""
    finally:
        try:
            os.unlink(state)
        except OSError:
            pass
    return code, reached

package, script = resolve()
if probe:
    sys.exit(0)
code, reached = launch(script)
if code != 0 and reached == "ready" and not hooks and repair(package):
    package, script = resolve()
    code, reached = launch(script)
sys.exit(code)
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
    "    } else { Write-Error 'standards: no usable Python was found; session launch is unavailable'; return 125 }",
    "    Write-Error 'standards: terminal coordinator is unavailable'; return 125",
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
    "  else printf '%s\\n' 'standards: no usable Python was found; session launch is unavailable' >&2; return 125; fi",
    "  printf '%s\\n' 'standards: terminal coordinator is unavailable' >&2; return 125",
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
