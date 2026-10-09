function codex {
    $exe = @(Get-Command codex -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)[0]
    if (-not $exe) { throw 'codex executable not found on PATH' }
    $target = $exe.Source
    if ($args.Count -eq 0 -or $args[0] -ne 'plugin') {
        $sync = Join-Path $PSScriptRoot 'codex_marketplace_sync.ps1'
        try {
            if (-not (Test-Path -LiteralPath $sync -PathType Leaf)) { throw "Codex sync script missing: $sync" }
            . $sync
            Sync-CodexStandards -CodexExecutable $target -WorkingDirectory (Get-Location).Path | Out-Null
        }
        catch {
            Write-Warning "standards: Codex refresh failed; this session loads installed plugins: $($_.Exception.Message)"
        }
    }
    & $target @args
}

function codex-hooks {
    $candidates = @(
        (Join-Path $PSScriptRoot '..\utility\hook-control\scripts\hook_control.py'),
        (Join-Path $PSScriptRoot '..\..\..\.agents\machine\utility\hook-control\scripts\hook_control.py')
    )
    $script = @($candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })[0]
    if (-not $script) { throw 'Codex hook-control utility is not installed' }
    & python -B $script @args
}
