function codex {
    $exe = @(Get-Command codex -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)[0]
    if (-not $exe) { throw 'codex executable not found on PATH' }
    $target = $exe.Source
    if ($args.Count -eq 0 -or @('plugin', '--version', '-V', '--help', '-h') -notcontains [string]$args[0]) {
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
