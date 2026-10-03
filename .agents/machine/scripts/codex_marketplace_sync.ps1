function Invoke-CodexSyncCommand {
    param(
        [Parameter(Mandatory)][string] $CodexExecutable,
        [Parameter(Mandatory)][string[]] $Arguments,
        [double] $TimeoutSeconds = 60,
        [string] $RunnerPath = (Join-Path $PSScriptRoot 'bounded_process.py')
    )

    $python = Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $command = @($CodexExecutable) + $Arguments
    if ([IO.Path]::GetExtension($CodexExecutable) -eq '.ps1') {
        $hostName = if ($PSVersionTable.PSEdition -eq 'Desktop') { 'powershell.exe' } elseif ($env:OS -eq 'Windows_NT') { 'pwsh.exe' } else { 'pwsh' }
        $shell = Join-Path $PSHOME $hostName
        $command = @($shell, '-NoProfile', '-NonInteractive',
            '-ExecutionPolicy', 'Bypass', '-File', $CodexExecutable) + $Arguments
    }
    $duration = $TimeoutSeconds.ToString('R', [Globalization.CultureInfo]::InvariantCulture)
    $previousEncoding = [Console]::OutputEncoding
    try {
        [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
        $output = @(& $python.Source -B $RunnerPath --timeout $duration -- @command 2>&1)
        $exitCode = $LASTEXITCODE
    }
    finally {
        [Console]::OutputEncoding = $previousEncoding
    }
    if ($exitCode -ne 0) {
        throw "Codex plugin sync failed: $($Arguments -join ' '): $($output -join ' ')"
    }
    try {
        return ($output -join "`n" | ConvertFrom-Json -ErrorAction Stop)
    }
    catch {
        throw "Codex plugin sync returned invalid JSON: $($Arguments -join ' ')"
    }
}

function Sync-CodexStandards {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string] $CodexExecutable,
        [Parameter(Mandatory)][string] $WorkingDirectory,
        [ValidateRange(0.001, 3600)][double] $TimeoutSeconds = 60
    )

    Write-Host ('standards: refreshing Codex plugins ({0:g}s maximum)...' -f $TimeoutSeconds)
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $resolved = (Resolve-Path -LiteralPath $WorkingDirectory -ErrorAction Stop).Path
    $runnerSnapshot = Join-Path ([IO.Path]::GetTempPath()) ('core-plugin-sync-' + [guid]::NewGuid().ToString('N') + '.py')
    Push-Location -LiteralPath $resolved
    try {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'bounded_process.py') -Destination $runnerSnapshot -ErrorAction Stop
        $upgrade = Invoke-CodexSyncCommand -CodexExecutable $CodexExecutable -RunnerPath $runnerSnapshot -TimeoutSeconds ($TimeoutSeconds - $clock.Elapsed.TotalSeconds) -Arguments @(
            'plugin', 'marketplace', 'upgrade', '--json'
        )
        if ($upgrade.errors -and @($upgrade.errors).Count -gt 0) {
            throw "Codex marketplace upgrade failed: $($upgrade.errors | ConvertTo-Json -Compress)"
        }

        $inventory = Invoke-CodexSyncCommand -CodexExecutable $CodexExecutable -RunnerPath $runnerSnapshot -TimeoutSeconds ($TimeoutSeconds - $clock.Elapsed.TotalSeconds) -Arguments @(
            'plugin', 'list', '--available', '--json'
        )
        $selected = @($inventory.installed) + @($inventory.available) |
            Where-Object { $_ -and $_.enabled -and $_.marketplaceSource.sourceType -eq 'git' } |
            ForEach-Object { $_.pluginId } |
            Sort-Object -Unique
        foreach ($identity in $selected) {
            $installed = Invoke-CodexSyncCommand -CodexExecutable $CodexExecutable -RunnerPath $runnerSnapshot -TimeoutSeconds ($TimeoutSeconds - $clock.Elapsed.TotalSeconds) -Arguments @(
                'plugin', 'add', $identity, '--json'
            )
            if ($installed.pluginId -ne $identity) {
                throw "Codex installed $($installed.pluginId) while refreshing $identity"
            }
        }
        return @($selected)
    }
    finally {
        Pop-Location
        Remove-Item -LiteralPath $runnerSnapshot -Force -ErrorAction SilentlyContinue
    }
}
