# The usable python on this machine, skipping the Windows Store alias stub (a `python`/`python3`/`py`
# placed under \WindowsApps\ that only opens the Store listing rather than running anything) and
# preferring, in order:
#   - Windows ($IsWindows is unset in Windows PowerShell 5.1, hence the $env:OS fallback): `python`, then
#     the python.org launcher `py -3` -- `python3` is not a convention on Windows and nothing ships it.
#   - Everywhere else: `python3`, then `python` -- a bare `python` on some Linux distributions is Python 2
#     or absent entirely, while `python3` is the one name every real install provides.
function Find-CodexPython {
    $isWindowsHost = $IsWindows -or $env:OS -eq 'Windows_NT'
    $names = if ($isWindowsHost) { @('python', 'py') } else { @('python3', 'python') }
    foreach ($name in $names) {
        foreach ($candidate in @(Get-Command $name -CommandType Application -ErrorAction SilentlyContinue)) {
            if ($candidate.Source -match '\\WindowsApps\\') { continue }
            $arguments = if ($name -eq 'py') { @('-3') } else { @() }
            return [pscustomobject]@{ Path = $candidate.Source; Arguments = $arguments }
        }
    }
    return $null
}

function codex {
    $exe = @(Get-Command codex -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)[0]
    if (-not $exe) { throw 'codex executable not found on PATH' }
    $target = $exe.Source
    if ($args.Count -eq 0 -or $args[0] -ne 'plugin') {
        try {
            $sync = Join-Path $PSScriptRoot 'codex_marketplace_sync.py'
            if (-not (Test-Path -LiteralPath $sync -PathType Leaf)) { throw "Codex sync script missing: $sync" }
            $python = Find-CodexPython
            if (-not $python) {
                Write-Warning 'standards: no usable python was found on PATH; this session loads installed plugins'
            }
            else {
                # --codex is omitted deliberately: $target here can be the npm/shell shim ($exe matches
                # ExternalScript too), and the sync script resolves the real native executable itself
                # (agent_cli.resolve_codex_executable()) whenever --codex is absent or names a shim.
                & $python.Path @($python.Arguments) -B $sync --project (Get-Location).Path | ForEach-Object { Write-Host $_ }
                if ($LASTEXITCODE -ne 0) { throw 'Codex standards sync failed' }
            }
        }
        catch {
            Write-Warning "standards: Codex refresh failed; this session loads installed plugins: $($_.Exception.Message)"
        }
    }
    & $target @args
}
