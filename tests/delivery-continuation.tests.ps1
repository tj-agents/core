$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repository = Split-Path -Parent $PSScriptRoot
$adapter = Join-Path $repository '.agents/engineering/workflow/persistent-workflow/scripts/delivery-continuation.ps1'
$helper = Join-Path $repository '.agents/workflows/continuation_runtime.py'
$python = (Get-Command python -CommandType Application | Select-Object -First 1).Source
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('continuation scheduler ' + [guid]::NewGuid().ToString('N'))
$originalPath = $env:PATH
$global:ContinuationTasks = @{}
$global:ContinuationRegistrations = 0
$global:ContinuationRemovals = 0
$global:ContinuationFailRegistration = $false
function Assert([bool] $Condition, [string] $Message) { if (-not $Condition) { throw $Message } }
function Write-Json([string] $Path, $Value, [int] $Depth) { [IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth $Depth), [Text.UTF8Encoding]::new($false)) }
function Expect-Failure([scriptblock] $Action, [string] $Pattern) {
    $failure = $null
    try { & $Action } catch { $failure = $_ }
    Assert ($null -ne $failure) "Expected failure matching $Pattern"
    Assert ($failure.ToString() -match $Pattern) "Unexpected failure: $failure"
}
function Get-ScheduledTask {
    [CmdletBinding()]param($TaskName, $TaskPath)
    $global:ContinuationTasks.Values | Where-Object { $_.TaskName -like $TaskName -and (-not $TaskPath -or $_.TaskPath -eq $TaskPath) }
}
function New-ScheduledTaskAction { param($Execute, $Argument, $WorkingDirectory) [pscustomobject]@{ Execute=$Execute; Arguments=$Argument; WorkingDirectory=$WorkingDirectory } }
function New-ScheduledTaskTrigger { param([switch]$Once, $At, $RepetitionInterval) [pscustomobject]@{ At=$At } }
function New-ScheduledTaskSettingsSet {
    param([switch]$AllowStartIfOnBatteries, [switch]$DontStopIfGoingOnBatteries, [switch]$StartWhenAvailable, $MultipleInstances, $ExecutionTimeLimit)
    [pscustomobject]@{ MultipleInstances=$MultipleInstances }
}
function Register-ScheduledTask {
    param($TaskName, $TaskPath, $Action, $Trigger, $Settings, $Description, [switch]$Force)
    if ($global:ContinuationFailRegistration) { throw 'Injected scheduler registration failure' }
    $global:ContinuationRegistrations++
    $global:ContinuationTasks[$TaskName] = [pscustomobject]@{ TaskName=$TaskName; TaskPath=$TaskPath; Actions=@($Action); Description=$Description; State='Ready' }
}
function Unregister-ScheduledTask {
    param($TaskName, $TaskPath, [switch]$Confirm)
    $global:ContinuationRemovals++
    $global:ContinuationTasks.Remove($TaskName)
}
try {
    New-Item -ItemType Directory -Path $scratch | Out-Null
    $root = Join-Path $scratch 'owner checkout'
    $bin = Join-Path $scratch 'bin'
    New-Item -ItemType Directory -Path $root, $bin | Out-Null
    New-Item -ItemType File -Path (Join-Path $bin 'codex.exe') | Out-Null
    $env:PATH = $bin + [IO.Path]::PathSeparator + $originalPath
    & git init --quiet $root
    & git -C $root remote add origin https://github.com/example/isolated-test.git
    & git -C $root -c user.name=Test -c user.email=test@example.invalid commit --quiet --allow-empty -m initial
    if ($LASTEXITCODE) { throw 'Unable to initialize isolated git checkout.' }
    $goal = Join-Path $root 'GOAL.md'
    Set-Content -LiteralPath $goal -Value 'Wait for isolated acceptance evidence.'
    & $python -B $helper init --root $root --goal $goal --completion 'Isolated gate reached' --actions edit test --harness codex --authority 'Isolated test'
    if ($LASTEXITCODE) { throw 'Runtime init failed.' }
    $ownerPath = Join-Path $root '.agents/continuation/owner.json'
    $receiptPath = Join-Path $root '.agents/continuation/scheduler.json'
    $pendingPath = Join-Path $root '.agents/continuation/scheduler.pending.json'
    $before = Get-Content -LiteralPath $ownerPath -Raw
    $legacy = [pscustomobject]@{ TaskName='AgentStandards-Delivery-legacy'; TaskPath='\'; Actions=@([pscustomobject]@{ WorkingDirectory=(Get-Content $ownerPath -Raw | ConvertFrom-Json).worktree }); Description='legacy'; State='Ready' }
    $global:ContinuationTasks[$legacy.TaskName] = $legacy
    Expect-Failure { & $adapter register -OwnerPath $ownerPath } 'Legacy delivery task'
    Assert ($global:ContinuationTasks.ContainsKey($legacy.TaskName)) 'Registration removed an unowned legacy task.'
    $legacy.Actions[0].WorkingDirectory = $scratch
    & $adapter register -OwnerPath $ownerPath -WhatIf
    $global:ContinuationTasks.Remove($legacy.TaskName)
    & $adapter register -OwnerPath $ownerPath -WhatIf
    Assert ($global:ContinuationRegistrations -eq 0 -and -not (Test-Path $receiptPath)) 'WhatIf registered or wrote a receipt.'
    Assert ((Get-Content $ownerPath -Raw) -ceq $before) 'WhatIf changed runtime state.'
    $global:ContinuationFailRegistration = $true
    Expect-Failure { & $adapter register -OwnerPath $ownerPath } 'Injected scheduler registration failure'
    Assert ((Test-Path $pendingPath) -and -not (Test-Path $receiptPath) -and $global:ContinuationTasks.Count -eq 0) 'Failed registration orphaned a task or lost its recovery transaction.'
    & $adapter remove -OwnerPath $ownerPath
    $global:ContinuationFailRegistration = $false
    & $adapter register -OwnerPath $ownerPath
    $receipt = Get-Content $receiptPath -Raw | ConvertFrom-Json
    Assert ($receipt.helper -eq $helper) 'Authored runtime path resolution failed.'
    Assert ($receipt.execute -ieq (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -and $receipt.arguments -match ' wake -OwnerPath ') 'Scheduled task does not run deterministic wake under the inbox Windows PowerShell.'
    Assert ($receipt.arguments -notmatch 'cmd.exe| exec | -p ') 'Scheduled action launches a model directly.'
    & $adapter register -OwnerPath $ownerPath -IntervalMinutes 10
    Assert ($global:ContinuationTasks.Count -eq 1 -and $global:ContinuationRegistrations -eq 2) 'Registration did not retain one stable task.'
    Assert ((Get-Content $ownerPath -Raw) -ceq $before) 'Re-registration reset runtime state or budgets.'
    & git -C $root -c user.name=Test -c user.email=test@example.invalid commit --quiet --allow-empty -m next-head
    & $adapter register -OwnerPath $ownerPath
    Assert ($global:ContinuationTasks.Count -eq 1) 'A changed head created a second owner task.'
    Assert ((Get-Content $ownerPath -Raw) -ceq $before) 'Scheduler registration changed head bindings.'
    & $adapter wake -OwnerPath $ownerPath -WhatIf
    Assert ((Get-Content $ownerPath -Raw) -ceq $before) 'Wake WhatIf modified the owner.'
    & $adapter remove -OwnerPath $ownerPath -WhatIf
    Assert ($global:ContinuationRemovals -eq 0 -and (Test-Path $receiptPath)) 'Remove WhatIf modified registration.'
    $task = $global:ContinuationTasks[$receipt.task_name]
    $originalArguments = $task.Actions[0].Arguments
    $task.Actions[0].Arguments = 'foreign action'
    Expect-Failure { & $adapter remove -OwnerPath $ownerPath } 'differs from its exact ownership receipt'
    Expect-Failure { & $adapter register -OwnerPath $ownerPath } 'differs from its exact ownership receipt'
    Assert ($global:ContinuationRemovals -eq 0) 'Mismatch removed a foreign task.'
    $task.Actions[0].Arguments = $originalArguments
    $foreign = [pscustomobject]@{ TaskName='AgentStandards-Continuation-foreign'; TaskPath='\'; Actions=@(); Description=$root; State='Ready' }
    $global:ContinuationTasks[$foreign.TaskName] = $foreign
    & $adapter remove -OwnerPath $ownerPath
    Assert ($global:ContinuationTasks.ContainsKey($foreign.TaskName)) 'Cleanup removed an unrelated task.'
    Assert (-not (Test-Path $receiptPath) -and (Test-Path $ownerPath)) 'Cleanup damaged owner or retained its receipt.'
    $global:ContinuationTasks[$receipt.task_name] = $task
    Expect-Failure { & $adapter register -OwnerPath $ownerPath } 'no matching receipt'
    $global:ContinuationTasks.Remove($receipt.task_name)
    $package = Join-Path $scratch 'installed package'
    $packageAdapter = Join-Path $package 'skills/persistent-workflow/scripts/delivery-continuation.ps1'
    New-Item -ItemType Directory -Path (Split-Path $packageAdapter), (Join-Path $package 'workflows'), (Join-Path $package '.agents/lanes') -Force | Out-Null
    Copy-Item -LiteralPath $adapter -Destination $packageAdapter
    Copy-Item -LiteralPath $helper -Destination (Join-Path $package 'workflows/continuation_runtime.py')
    Copy-Item -LiteralPath (Join-Path $repository '.agents/lanes/codex.json') -Destination (Join-Path $package '.agents/lanes/codex.json')
    & $adapter register -OwnerPath $ownerPath
    $previousReceipt = Get-Content $receiptPath -Raw
    $global:ContinuationFailRegistration = $true
    Expect-Failure { & $packageAdapter register -OwnerPath $ownerPath } 'Injected scheduler registration failure'
    Assert ((Get-Content $receiptPath -Raw) -ceq $previousReceipt) 'Failed package replacement destroyed the previous receipt.'
    $knownReceipt = Get-Content $receiptPath -Raw | ConvertFrom-Json
    $unknownReceipt = Get-Content $receiptPath -Raw | ConvertFrom-Json
    $unknownReceipt.helper = 'unknown receipt evidence'
    Write-Json $receiptPath $unknownReceipt 10
    $unknownBefore = Get-Content $receiptPath -Raw
    Expect-Failure { & $adapter remove -OwnerPath $ownerPath } 'receipt matches neither pending registration record'
    Assert ((Get-Content $receiptPath -Raw) -ceq $unknownBefore -and (Test-Path $pendingPath)) 'Recovery overwrote unknown receipt evidence.'
    Write-Json $receiptPath $knownReceipt 10
    $transaction = Get-Content $pendingPath -Raw | ConvertFrom-Json
    Assert ($transaction.previous.script -eq $adapter -and $transaction.proposed.script -eq $packageAdapter) 'Transaction did not retain both package identities.'
    $pendingBefore = Get-Content $pendingPath -Raw
    & $packageAdapter register -OwnerPath $ownerPath -WhatIf
    Assert ((Get-Content $pendingPath -Raw) -ceq $pendingBefore -and (Get-Content $receiptPath -Raw) -ceq $previousReceipt) 'WhatIf reconciled or replaced pending registration files.'
    & $adapter remove -OwnerPath $ownerPath
    Assert (-not (Test-Path $receiptPath) -and -not (Test-Path $pendingPath)) 'Old live task recovery retained owned transaction files.'
    $global:ContinuationFailRegistration = $false
    & $adapter register -OwnerPath $ownerPath
    $global:ContinuationFailRegistration = $true
    Expect-Failure { & $packageAdapter register -OwnerPath $ownerPath } 'Injected scheduler registration failure'
    $transaction = Get-Content $pendingPath -Raw | ConvertFrom-Json
    $recoveryTask = $global:ContinuationTasks[$transaction.proposed.task_name]
    $recoveryTask.Actions[0].Arguments = 'unknown replacement'
    $pendingBefore = Get-Content $pendingPath -Raw
    Expect-Failure { & $adapter remove -OwnerPath $ownerPath } 'matches neither pending registration identity'
    Assert ((Get-Content $pendingPath -Raw) -ceq $pendingBefore -and $global:ContinuationTasks.ContainsKey($recoveryTask.TaskName)) 'Unknown task recovery changed the task or evidence.'
    $recoveryTask.Actions[0] = [pscustomobject]@{ Execute=$transaction.proposed.execute; Arguments=$transaction.proposed.arguments; WorkingDirectory=$transaction.proposed.worktree }
    $recoveryTask.Description = $transaction.proposed.description
    & $packageAdapter remove -OwnerPath $ownerPath -WhatIf
    Assert ((Get-Content $pendingPath -Raw) -ceq $pendingBefore -and $global:ContinuationTasks.ContainsKey($recoveryTask.TaskName)) 'New live task WhatIf recovery changed the task or evidence.'
    & $packageAdapter remove -OwnerPath $ownerPath
    Assert (-not (Test-Path $receiptPath) -and -not (Test-Path $pendingPath)) 'New live task recovery retained owned transaction files.'
    $global:ContinuationFailRegistration = $false
    & $packageAdapter register -OwnerPath $ownerPath
    $packagedReceipt = Get-Content $receiptPath -Raw | ConvertFrom-Json
    Assert ($packagedReceipt.helper -eq (Join-Path $package 'workflows/continuation_runtime.py')) 'Installed package runtime resolution failed.'
    Remove-Item -LiteralPath $packagedReceipt.helper
    Expect-Failure { & $packageAdapter wake -OwnerPath $ownerPath } 'package prerequisite is missing'
    & $packageAdapter remove -OwnerPath $ownerPath
    & $adapter register -OwnerPath $ownerPath
    $terminalOwner = Get-Content $ownerPath -Raw | ConvertFrom-Json
    $terminalOwner.state = 'blocked'
    Write-Json $ownerPath $terminalOwner 30
    & $adapter wake -OwnerPath $ownerPath
    Assert (-not (Test-Path $receiptPath)) 'Terminal runtime wake retained its scheduler receipt.'
    Assert ($global:ContinuationTasks.Count -eq 1 -and $global:ContinuationTasks.ContainsKey($foreign.TaskName)) 'Terminal wake removed unrelated tasks or retained its task.'
    Write-Output 'Scheduler adapter tests passed; no live scheduler was changed.'
} finally {
    $env:PATH = $originalPath
    if (([IO.Path]::GetFullPath($scratch)).StartsWith([IO.Path]::GetTempPath(), [StringComparison]::OrdinalIgnoreCase)) { Remove-Item -LiteralPath $scratch -Recurse -Force }
    Remove-Variable ContinuationTasks, ContinuationRegistrations, ContinuationRemovals, ContinuationFailRegistration -Scope Global -ErrorAction SilentlyContinue
}
