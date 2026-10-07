function codex {
    $exe = @(Get-Command codex -CommandType Application, ExternalScript -ErrorAction SilentlyContinue)[0]
    if (-not $exe) { throw 'codex executable not found on PATH' }
    $target = $exe.Source
    if ($args.Count -eq 0 -or $args[0] -ne 'plugin') {
        try {
            $sync = Join-Path $PSScriptRoot 'codex_marketplace_sync.py'
            if (-not (Test-Path -LiteralPath $sync -PathType Leaf)) { throw "Codex sync script missing: $sync" }
            # python3 first, then python: a bare `python` on some Linux distributions is Python 2 or
            # absent entirely, while `python3` is never the Windows Store alias stub that fails outright.
            $python = @(Get-Command python3, python -CommandType Application -ErrorAction SilentlyContinue)[0]
            if (-not $python) {
                Write-Warning 'standards: neither python3 nor python was found on PATH; this session loads installed plugins'
            }
            else {
                & $python.Source -B $sync --codex $target --project (Get-Location).Path | ForEach-Object { Write-Host $_ }
                if ($LASTEXITCODE -ne 0) { throw 'Codex standards sync failed' }
            }
        }
        catch {
            Write-Warning "standards: Codex refresh failed; this session loads installed plugins: $($_.Exception.Message)"
        }
    }
    & $target @args
}
