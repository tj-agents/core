. (Join-Path $PSScriptRoot 'agent-cli.ps1')

$script:ClaudeCommandsWithoutSession = @(
    'agents', 'attach', 'auth', 'auto-mode', 'doctor', 'gateway', 'import', 'install', 'kill', 'logs',
    'mcp', 'plugin', 'plugins', 'project', 'rm', 'setup-token', 'stop', 'ultrareview', 'update', 'upgrade',
    '-h', '--help', '-v', '--version'
)

# Every bare `claude` launch gets a name, so the built-in /resume picker has something to print per row.
# Without it every session shows up unlabeled and the only way back into one is knowing its uuid.
# Any arguments at all (subcommands, -r, -p, --continue, an explicit -n) pass straight through untouched.
function claude {
    $exe = @(Get-Command claude -All -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandType -ne 'Function' -and $_.CommandType -ne 'Alias' })
    if ($exe.Count -eq 0) { Write-Host "claude executable not found on PATH" -ForegroundColor Red; return }
    $target = $exe[0].Source

    if ($args.Count -eq 0 -or $script:ClaudeCommandsWithoutSession -notcontains [string]$args[0]) {
        Sync-ClaudeStandards -WorkingDirectory (Get-Location).Path
    }

    if ($args.Count -gt 0) { & $target @args; return }

    $label = Split-Path (Get-Location).Path -Leaf
    $b = git branch --show-current 2>$null
    if ($LASTEXITCODE -eq 0 -and $b) { $label = "$label/$b" }
    & $target -n $label
}
