. (Join-Path $PSScriptRoot '..\.agents\machine\scripts\agent-cli.ps1')

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

# "I closed the terminal, put me back in what I was doing" - from ANY directory, any project on this
# machine. Takes the most recently touched conversation across all of ~/.claude/projects, moves to the
# directory that session was rooted in, and resumes it. `cl -Pick` opens the cross-project picker instead.
function cl {
    param([switch]$Pick, [int]$Count = 30)

    $root = Join-Path $env:USERPROFILE '.claude\projects'
    if (-not (Test-Path $root)) { Write-Host "No Claude history at $root" -ForegroundColor Red; return }

    if ($Pick) { cr -All -Count $Count; return }

    $f = @(Get-ChildItem $root -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { Get-ChildItem $_.FullName -Filter *.jsonl -File -ErrorAction SilentlyContinue } |
        Where-Object { $_.Length -gt 2KB } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1)
    if ($f.Count -eq 0) { Write-Host "No conversations found." -ForegroundColor Red; return }
    $f = $f[0]
    $sid = [IO.Path]::GetFileNameWithoutExtension($f.Name)

    # The session's own cwd is recorded on its entries; resume from there or the project context is wrong.
    $cwd = ''
    try {
        $fs = New-Object IO.FileStream($f.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        $len = [Math]::Min(65536, $fs.Length)
        $fs.Seek(-$len, [IO.SeekOrigin]::End) | Out-Null
        $buf = New-Object byte[] $len
        $fs.Read($buf, 0, $len) | Out-Null
        $fs.Dispose()
        $tailText = [Text.Encoding]::UTF8.GetString($buf)
        $m = [regex]::Matches($tailText, '"cwd":"((?:[^"\\]|\\.)*)"')
        if ($m.Count -gt 0) { $cwd = ($m[$m.Count - 1].Groups[1].Value -replace '\\\\', '\') }
    }
    catch { }

    if ($cwd -and (Test-Path -LiteralPath $cwd)) {
        Write-Host "-> $cwd" -ForegroundColor DarkGray
        Set-Location -LiteralPath $cwd
    }
    Write-Host "-> claude --resume $sid  ($($f.LastWriteTime.ToString('MM-dd HH:mm')))" -ForegroundColor DarkGray
    claude --resume $sid
}
