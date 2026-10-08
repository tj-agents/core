[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Position = 0)][ValidateSet('claim', 'register', 'remove', 'list', 'wake')][string] $Command = 'list',
    [string] $Worktree,
    [string] $OwnerPath,
    [ValidateRange(5, 720)][int] $IntervalMinutes = 20,
    [string] $Reason
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskPrefix = 'AgentStandards-Continuation-'
if ($env:OS -ne 'Windows_NT') {
    throw 'Continuation scheduling requires Windows. No scheduler adapter is provided for this platform.'
}
function Test-FullyQualifiedPath([string] $Path) { return $Path -match '^(?:[A-Za-z]:[\\/]|[\\/]{2})' }
function Assert-HostExecutable([string] $Path) {
    if (-not (Test-FullyQualifiedPath $Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf) -or [IO.Path]::GetExtension($Path) -ine '.exe') {
        throw 'The pinned host executable must be an existing absolute native .exe path.'
    }
}
function Find-Executable([string] $Name) {
    $found = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $found) { throw "Required executable '$Name' is missing from PATH." }
    return $found.Source
}
function Resolve-Helper {
    $directory = $PSScriptRoot
    while ($directory) {
        foreach ($relative in @('workflows/continuation_runtime.py', '.agents/workflows/continuation_runtime.py')) {
            $candidate = Join-Path $directory $relative
            if (Test-Path -LiteralPath $candidate -PathType Leaf) { return [IO.Path]::GetFullPath($candidate) }
        }
        $directory = Split-Path -Parent $directory
    }
    throw 'The continuation runtime is missing from this package. Restore the package and register this owner again.'
}
function Quote-Argument([string] $Value) {
    if ($Value.Contains('"') -or $Value.Contains("`r") -or $Value.Contains("`n")) { throw 'Scheduled paths must not contain quotes or newlines.' }
    return '"' + ($Value -replace '(\\+)$', '$1$1') + '"'
}
function Read-Json([string] $Path) { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json }
function Assert-ReceiptIdentity($Receipt) {
    if ($Receipt.owner_id -cne $owner.owner_id -or $Receipt.owner_path -cne $ownerFile -or
        $Receipt.task_name -cne $taskName -or $Receipt.task_path -cne '\') { throw 'Scheduler receipt does not match this exact continuation owner.' }
}
function Test-TaskReceipt($Task, $Receipt) {
    $actions = @($Task.Actions)
    return ($Task.Description -ceq $Receipt.description -and $actions.Count -eq 1 -and
        $actions[0].Execute -ceq $Receipt.execute -and $actions[0].Arguments -ceq $Receipt.arguments -and
        $actions[0].WorkingDirectory -ceq $Receipt.worktree)
}
function Get-ExactTask {
    $tasks = @(Get-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue)
    if ($tasks.Count -gt 1) { throw 'Scheduler returned an ambiguous task identity.' }
    if ($tasks.Count) { return $tasks[0] }
    return $null
}
function Get-OwnedTask($Receipt) {
    Assert-ReceiptIdentity $Receipt
    $task = Get-ExactTask
    if ($task -and -not (Test-TaskReceipt $task $Receipt)) { throw 'Scheduled task differs from its exact ownership receipt; refusing to change it.' }
    return $task
}
function Write-AtomicJson([string] $Path, $Value) {
    $temporary = "$Path.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        [IO.File]::WriteAllText($temporary, ($Value | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    } finally { if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary } }
}
function Resolve-PendingRegistration($CurrentReceipt) {
    if (-not (Test-Path -LiteralPath $pendingPath -PathType Leaf)) { return $CurrentReceipt }
    $pending = Read-Json $pendingPath
    Assert-ReceiptIdentity $pending.proposed
    if ($pending.previous) { Assert-ReceiptIdentity $pending.previous }
    if ($CurrentReceipt) {
        Assert-ReceiptIdentity $CurrentReceipt
        $currentJson = $CurrentReceipt | ConvertTo-Json -Depth 10 -Compress
        $previousJson = $pending.previous | ConvertTo-Json -Depth 10 -Compress
        $proposedJson = $pending.proposed | ConvertTo-Json -Depth 10 -Compress
        if ($currentJson -cne $previousJson -and $currentJson -cne $proposedJson) {
            throw 'Scheduler receipt matches neither pending registration record; preserving transaction evidence.'
        }
    }
    $task = Get-ExactTask
    if ($task) {
        if (Test-TaskReceipt $task $pending.proposed) { $resolved = $pending.proposed }
        elseif ($pending.previous -and (Test-TaskReceipt $task $pending.previous)) { $resolved = $pending.previous }
        else { throw 'Scheduled task matches neither pending registration identity; preserving task and transaction evidence.' }
    } else { $resolved = if ($pending.previous) { $pending.previous } else { $pending.proposed } }
    if ($PSCmdlet.ShouldProcess($taskName, 'Reconcile pending scheduler registration')) {
        Write-AtomicJson $receiptPath $resolved
        Remove-Item -LiteralPath $pendingPath
    }
    return $resolved
}
if ($Command -eq 'list') {
    Get-ScheduledTask -TaskName "$taskPrefix*" -ErrorAction SilentlyContinue | Select-Object TaskName, TaskPath, State, Description
    return
}
if ($OwnerPath) { $ownerFile = [IO.Path]::GetFullPath($OwnerPath) }
else {
    if (-not $Worktree) {
        $Worktree = & git rev-parse --show-toplevel
        if ($LASTEXITCODE -ne 0) { throw 'Specify -Worktree or -OwnerPath outside a git checkout.' }
    }
    $ownerFile = Join-Path ([IO.Path]::GetFullPath($Worktree)) '.agents/continuation/owner.json'
}
if (-not (Test-Path -LiteralPath $ownerFile -PathType Leaf)) { throw "Continuation owner is missing: $ownerFile. Initialize it with continuation_runtime.py init first." }
$owner = Read-Json $ownerFile
if (-not $owner.owner_id -or $owner.harness -notin @('codex', 'claude') -or -not (Test-FullyQualifiedPath $owner.worktree)) { throw 'Invalid continuation runtime owner.' }
$root = [IO.Path]::GetFullPath($owner.worktree)
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw "Owner worktree is unavailable: $root." }
if ($Worktree -and [IO.Path]::GetFullPath($Worktree) -ine $root) { throw 'Worktree does not match the runtime owner.' }
$sha256 = [Security.Cryptography.SHA256]::Create()
try { $hash = -join ($sha256.ComputeHash([Text.Encoding]::UTF8.GetBytes($owner.owner_id)) | ForEach-Object { $_.ToString('x2') }) }
finally { $sha256.Dispose() }
$taskName = $taskPrefix + $hash
$mutex = [Threading.Mutex]::new($false, ('Global\' + $taskName))
$acquired = $false
try {
    try { $acquired = $mutex.WaitOne([TimeSpan]::FromSeconds(10)) }
    catch [Threading.AbandonedMutexException] { $acquired = $true }
    if (-not $acquired) { throw 'Another scheduler lifecycle operation holds this owner; retry after it finishes.' }
$receiptPath = Join-Path (Split-Path -Parent $ownerFile) 'scheduler.json'
$pendingPath = Join-Path (Split-Path -Parent $ownerFile) 'scheduler.pending.json'
$receipt = $null
if ($Command -ne 'claim') {
    foreach ($name in @('Get-ScheduledTask', 'Register-ScheduledTask', 'Unregister-ScheduledTask', 'New-ScheduledTaskAction', 'New-ScheduledTaskTrigger', 'New-ScheduledTaskSettingsSet')) {
        if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { throw "Windows ScheduledTasks capability is unavailable: $name." }
    }
    $receipt = if (Test-Path -LiteralPath $receiptPath -PathType Leaf) { Read-Json $receiptPath } else { $null }
    $receipt = Resolve-PendingRegistration $receipt
}
function Remove-OwnedTask {
    if (-not $receipt) { Write-Output "No scheduler receipt exists for owner $($owner.owner_id)."; return }
    $task = Get-OwnedTask $receipt
    if ($PSCmdlet.ShouldProcess($taskName, "Remove continuation task ($Reason)")) {
        if ($task) { Unregister-ScheduledTask -TaskName $receipt.task_name -TaskPath $receipt.task_path -Confirm:$false }
        Remove-Item -LiteralPath $receiptPath
        Write-Output "Removed scheduler registration for owner $($owner.owner_id)."
    }
}
switch ($Command) {
    'claim' {
        if (-not $PSCmdlet.ShouldProcess($owner.owner_id, 'Claim foreground continuation owner')) { return }
        $helper = Resolve-Helper
        $python = Find-Executable 'python'
        $hostExecutable = $null
        if ($owner.PSObject.Properties['host_executable'] -and $owner.host_executable) { Assert-HostExecutable $owner.host_executable }
        $foregroundProcessId = [int]$PID
        $seen = @{}
        $hostProcessId = $null
        while ($foregroundProcessId -gt 0) {
            if ($seen.ContainsKey($foregroundProcessId)) { throw 'Foreground process ancestry contains a cycle.' }
            $seen[$foregroundProcessId] = $true
            $processRecords = @(Get-CimInstance -ClassName Win32_Process -Filter ("ProcessId = {0}" -f $foregroundProcessId) -ErrorAction SilentlyContinue)
            if ($processRecords.Count -ne 1) { throw "Foreground process $foregroundProcessId is unavailable." }
            $process = $processRecords[0]
            if (-not $process.PSObject.Properties['Name']) { throw "Foreground process $foregroundProcessId has no executable name." }
            $name = [IO.Path]::GetFileName([string]$process.Name)
            if ($name -ieq 'codex.exe' -or $name -ieq 'claude.exe') {
                if ($name -ine ($owner.harness + '.exe')) { throw "Nearest foreground host is $name, but owner requires $($owner.harness).exe." }
                $hostProcessId = [int]$process.ProcessId
                if (-not $owner.host_executable) {
                    if (-not $process.PSObject.Properties['ExecutablePath']) { throw "Foreground host $name has no executable path." }
                    $hostExecutable = [string]$process.ExecutablePath
                    if (-not (Test-FullyQualifiedPath $hostExecutable) -or -not (Test-Path -LiteralPath $hostExecutable -PathType Leaf) -or [IO.Path]::GetFileName($hostExecutable) -ine ($owner.harness + '.exe')) {
                        throw "Foreground host executable must be an existing absolute $($owner.harness).exe path."
                    }
                }
                break
            }
            $foregroundProcessId = [int]$process.ParentProcessId
        }
        if ($null -eq $hostProcessId) { throw "No codex.exe or claude.exe exists in the foreground process ancestry for $($owner.harness)." }
        $claimArguments = @('-B', $helper, 'claim', '--owner', $ownerFile, '--pid', $hostProcessId)
        if ($hostExecutable) { $claimArguments += @('--host-executable', $hostExecutable) }
        $claimOutput = @(& $python @claimArguments)
        if ($LASTEXITCODE -ne 0) { throw "Continuation runtime claim failed with exit code $LASTEXITCODE." }
        try { $claim = (($claimOutput -join [Environment]::NewLine) | ConvertFrom-Json -ErrorAction Stop) }
        catch { throw "Continuation runtime claim returned invalid JSON: $($_.Exception.Message)" }
        if (-not $claim.foreground -or -not $claim.foreground.token) { throw 'Continuation runtime claim returned no foreground lease token.' }
        $claim | ConvertTo-Json -Depth 10 -Compress
    }
    'register' {
        $legacyTasks = @(Get-ScheduledTask -TaskName 'AgentStandards-Delivery-*' -ErrorAction SilentlyContinue)
        foreach ($legacyTask in $legacyTasks) {
            foreach ($legacyAction in @($legacyTask.Actions)) {
                if ($legacyAction.WorkingDirectory -and [IO.Path]::GetFullPath($legacyAction.WorkingDirectory) -ieq $root) {
                    throw "Legacy delivery task '$($legacyTask.TaskName)' targets this worktree. Explicitly inspect and retire that task before activating this owner."
                }
            }
        }
        if ($owner.state -in @('blocked', 'complete')) { throw 'A terminal owner cannot be scheduled; reconcile its runtime state first.' }
        $python = Find-Executable 'python'
        $windowsPowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
        if (-not (Test-Path -LiteralPath $windowsPowerShell -PathType Leaf)) { throw "Windows PowerShell is missing: $windowsPowerShell." }
        if ($owner.PSObject.Properties['host_executable'] -and $owner.host_executable) {
            Assert-HostExecutable $owner.host_executable
        } else { $null = Find-Executable $owner.harness }
        if (Test-Path -LiteralPath (Join-Path $root '.agents/persistent-workflow-binding.json')) { $null = Find-Executable 'gh' }
        $helper = Resolve-Helper
        $packageRoot = Split-Path -Parent (Split-Path -Parent $helper)
        $lanes = @((Join-Path $packageRoot "lanes/$($owner.harness).json"), (Join-Path $packageRoot ".agents/lanes/$($owner.harness).json"))
        if (-not ($lanes | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })) { throw 'The package is missing the selected host lane resource.' }
        $arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File {0} wake -OwnerPath {1}' -f (Quote-Argument $PSCommandPath), (Quote-Argument $ownerFile)
        $description = "Continuation owner $($owner.owner_id)"
        $existing = @(Get-ScheduledTask -TaskName $taskName -TaskPath '\' -ErrorAction SilentlyContinue)
        if ($receipt) { $null = Get-OwnedTask $receipt }
        elseif ($existing.Count) { throw 'An existing task has no matching receipt; refusing to overwrite it.' }
        if ($PSCmdlet.ShouldProcess($taskName, 'Register deterministic continuation wake')) {
            $action = New-ScheduledTaskAction -Execute $windowsPowerShell -Argument $arguments -WorkingDirectory $root
            $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes($IntervalMinutes) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
            $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
            $registration = [ordered]@{ owner_id = $owner.owner_id; owner_path = $ownerFile; task_name = $taskName; task_path = '\'; description = $description; execute = $windowsPowerShell; arguments = $arguments; worktree = $root; helper = $helper; python = $python; script = $PSCommandPath }
            Write-AtomicJson $pendingPath ([ordered]@{ previous = $receipt; proposed = $registration })
            Register-ScheduledTask -TaskName $taskName -TaskPath '\' -Action $action -Trigger $trigger -Settings $settings -Description $description -Force | Out-Null
            $receipt = Resolve-PendingRegistration $receipt
            Write-Output "Registered $taskName every $IntervalMinutes minutes. Package paths must remain available: $helper"
        }
    }
    'remove' { Remove-OwnedTask }
    'wake' {
        if (-not $receipt) { throw 'Scheduled wake requires an exact registration receipt.' }
        $task = Get-OwnedTask $receipt
        if (-not $task) { throw 'The registered continuation task is missing.' }
        if ($receipt.script -cne $PSCommandPath) { throw 'Wake script does not match its registration receipt.' }
        foreach ($path in @($receipt.helper, $receipt.python, $receipt.script)) {
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Registered package prerequisite is missing: $path. Restore the package and register again." }
        }
        if ($PSCmdlet.ShouldProcess($owner.owner_id, 'Observe continuation state and run bounded runtime wake')) {
            & $receipt.python -B $receipt.helper wake --owner $ownerFile
            if ($LASTEXITCODE -ne 0) { throw "Continuation runtime wake failed with exit code $LASTEXITCODE. See owner logs in $(Split-Path -Parent $ownerFile)." }
            $owner = Read-Json $ownerFile
            if ($owner.state -in @('blocked', 'complete')) { Remove-OwnedTask }
        }
    }
}

} finally {
    if ($acquired) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
