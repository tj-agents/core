<#
.SYNOPSIS
One operating-system scheduled task per delivery owner, so a continuation outlives its session.

.DESCRIPTION
`persistent-workflow` is explicit that an in-session mechanism is not persistence: a goal, a loop, a
Monitor and a background shell all die with the session, and restoring a conversation is not a wake.
On this harness that leaves a real hole. Claude Code's own scheduler is session-scoped - its jobs are
held in memory and a durable flag has no effect - and a cloud routine runs against a fresh remote
clone, so it cannot touch the local worktree a bound delivery names.

An operating-system scheduled task closes it. It runs whether or not any session is open, it runs in
the owning worktree, and it drives the delivery through the same headless harness invocation the
foreground would use. That is the same surface the Codex form of the skill already relies on, reached
through the OS rather than through a desktop application.

The task's identity is the delivery owner, never the head: rebinding to a repaired head updates the
existing task rather than adding a second one, which is what `persistent-delivery` means by exactly
one owner per PR/head pair. Registering a task requires the binding artifact to exist, because the
prompt IS the binding - a task with no binding would wake up owning nothing.

.PARAMETER Command
  register - create or update this delivery owner's task (idempotent; safe on every rebind)
  remove   - delete it, which is what a terminal owes
  list     - show every delivery task this machine holds

.PARAMETER Worktree
The absolute checkout that owns the delivery. Defaults to the repository root of the current
location. Its `.agents/persistent-workflow-binding.json` supplies every bound value.

.PARAMETER Harness
`claude` (default) runs `claude -p`; `codex` runs `codex exec`. Both are headless and non-interactive.

.PARAMETER IntervalMinutes
How often the task wakes. Defaults to 20. A wake that observes unchanged authoritative state does
nothing and reports nothing, so this is a floor on latency, not a cost per interval.

.EXAMPLE
pwsh scripts/delivery-continuation.ps1 register
pwsh scripts/delivery-continuation.ps1 remove -Reason merged
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Position = 0)]
    [ValidateSet('register', 'remove', 'list')]
    [string] $Command = 'list',
    [string] $Worktree,
    [ValidateSet('claude', 'codex')]
    [string] $Harness = 'claude',
    [ValidateRange(5, 720)]
    [int] $IntervalMinutes = 20,
    [string] $Reason
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$taskPrefix = 'AgentStandards-Delivery'
$bindingRelativePath = '.agents/persistent-workflow-binding.json'

# The version test must short-circuit first: `$IsWindows` does not exist in Windows PowerShell 5.1, and
# StrictMode is already in force, so reading it there throws before the script does anything.
if ($PSVersionTable.PSVersion.Major -ge 6 -and -not $IsWindows) {
    throw 'delivery-continuation.ps1 registers a Windows scheduled task. On macOS or Linux, register the equivalent launchd or systemd timer with the same identity and prompt.'
}

function Resolve-Worktree {
    if ($Worktree) { return [IO.Path]::GetFullPath($Worktree) }
    $top = & git rev-parse --show-toplevel
    if ($LASTEXITCODE -ne 0) { throw 'Not inside a git checkout, and no -Worktree was given.' }
    return [IO.Path]::GetFullPath(($top -replace '/', [IO.Path]::DirectorySeparatorChar))
}

function Get-Binding([string] $root) {
    $path = Join-Path $root $bindingRelativePath
    if (-not (Test-Path -LiteralPath $path)) {
        throw "$path does not exist. Bind the delivery first: python .agents/workflows/workflow_ops.py --workflow-run-id <id> delivery-bind"
    }
    return Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
}

# The delivery owner, not the head. A repair push rebinds this same task; a different PR or worktree
# is a different owner and gets its own.
function Get-TaskName($binding, [string] $root) {
    $identity = '{0}|{1}|{2}' -f $binding.repo, $binding.pr, $root.ToLowerInvariant()
    $bytes = [Text.Encoding]::UTF8.GetBytes($identity)
    $hash = [BitConverter]::ToString([Security.Cryptography.SHA256]::HashData($bytes)).Replace('-', '').Substring(0, 12)
    return '{0}-{1}-PR{2}-{3}' -f $taskPrefix, ($binding.repo -replace '[^A-Za-z0-9]', ''), $binding.pr, $hash
}

function Get-ContinuationPrompt($binding) {
    $evidence = if ($binding.pending_evidence.Count -gt 0) {
        ($binding.pending_evidence | ForEach-Object { "check $($_.check_id) / run $($_.run_id) at $($_.head_sha)" }) -join '; '
    } else { 'none pending at bind time' }
    $authorization = if ($binding.merge_authorization.mode -eq 'absent') {
        'absent - stop at the merge gate and record why'
    } else {
        '{0} - {1}' -f $binding.merge_authorization.mode, $binding.merge_authorization.instruction
    }
    $watermark = if ($binding.review.reviewed_sha) { $binding.review.reviewed_sha } else { 'pending' }
    return @"
Continue exactly this delivery owner until its terminal condition. Enter the persistent-workflow
skill first; it supplies the decision contract this prompt only binds.

Repository: $($binding.repo)
PR: $($binding.pr_url) #$($binding.pr)
Worktree: $($binding.worktree)
Branch: $($binding.branch)
Bound remote head: $($binding.head)
Pending evidence: $evidence
Review work order: $($binding.review.work_order)
Reviewed-SHA watermark: $watermark
Merge authorization: $authorization
Completion condition: $($binding.completion_condition)

Read authoritative forge state once this wake and route it through the shared persistent-delivery
decision contract. Reject an observation from another PR or head. Unchanged state produces no
report, no mutation, and no replacement continuation.

For an exact-head failure, classify its tier and dispatch one fresh context with the selected debug
skill, the complete binding, the exact failed check and run IDs, and the failure signature. Validate
what it returns, commit and push one stable repair, then re-run
``python .agents/workflows/workflow_ops.py --workflow-run-id <id> delivery-bind`` so the binding and
this task follow the new head with a freshly resolved authorization.

For a green exact head, obtain independent current-head review, address findings, renew the
watermark, and enter merge only under the recorded authorization above.

On terminal merge, closure, supersession, external head replacement, absent authorization, or any
genuine human gate: run ``workflow_ops.py delivery-release --reason <terminal>`` and
``pwsh scripts/delivery-continuation.ps1 remove``, record the final binding and decision, and stop.
"@
}

function Get-HarnessCommand([string] $root, [string] $prompt) {
    $promptPath = Join-Path $root '.agents/persistent-workflow-continuation.txt'
    Set-Content -LiteralPath $promptPath -Value $prompt -Encoding utf8
    # The prompt reaches the harness on stdin, and Task Scheduler runs the executable directly with no
    # shell, so the action is cmd.exe and the redirection is its business. `/s` makes cmd strip only the
    # outermost quote pair and take the rest verbatim, which is what keeps a spaced path intact.
    # The prompt is a file rather than an argument because Task Scheduler truncates long ones and every
    # quoting layer between here and the harness is another way to corrupt a bound SHA.
    $harness = if ($Harness -eq 'codex') {
        @{ Program = 'codex'; Arguments = "exec --cd `"$root`" -" }
    } else {
        # acceptEdits, never bypassPermissions: this agent runs unattended, so it may write in the
        # worktree it owns and must still be refused everything that needs a human.
        @{ Program = 'claude'; Arguments = '-p --permission-mode acceptEdits' }
    }
    $executable = Find-Executable $harness.Program
    return @{
        Program   = $env:ComSpec
        Arguments = '/d /s /c ""{0}" {1} < "{2}""' -f $executable, $harness.Arguments, $promptPath
    }
}

function Find-Executable([string] $name) {
    $found = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $found) { throw "$name was not found on PATH as an executable, so a scheduled task could not launch it." }
    return $found.Source
}

switch ($Command) {
    'list' {
        Get-ScheduledTask -TaskName "$taskPrefix*" -ErrorAction SilentlyContinue |
            Select-Object TaskName, State, @{ Name = 'NextRun'; Expression = { (Get-ScheduledTaskInfo $_).NextRunTime } }
    }
    'register' {
        $root = Resolve-Worktree
        $binding = Get-Binding $root
        $taskName = Get-TaskName $binding $root
        $prompt = Get-ContinuationPrompt $binding
        $launch = Get-HarnessCommand $root $prompt
        if ($PSCmdlet.ShouldProcess($taskName, 'register delivery continuation')) {
            $action = New-ScheduledTaskAction -Execute $launch.Program -Argument $launch.Arguments -WorkingDirectory $root
            $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes($IntervalMinutes) `
                -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
            $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
                -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
            $description = "Delivery continuation for $($binding.repo) PR #$($binding.pr) at $($binding.head) in $root. Registered by scripts/delivery-continuation.ps1; remove it at the delivery's terminal."
            Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings `
                -Description $description -Force | Out-Null
            Write-Host "Registered $taskName - wakes every $IntervalMinutes minutes for PR #$($binding.pr) at $($binding.head.Substring(0, 12))."
        }
    }
    'remove' {
        $root = Resolve-Worktree
        $existing = @(Get-ScheduledTask -TaskName "$taskPrefix*" -ErrorAction SilentlyContinue |
            Where-Object { $_.Description -like "*$root*" })
        if ($existing.Count -eq 0) {
            Write-Host "No delivery continuation is registered for $root."
            return
        }
        foreach ($task in $existing) {
            if ($PSCmdlet.ShouldProcess($task.TaskName, 'remove delivery continuation')) {
                Unregister-ScheduledTask -TaskName $task.TaskName -Confirm:$false
                Write-Host "Removed $($task.TaskName)$(if ($Reason) { " - $Reason" })."
            }
        }
        Remove-Item -LiteralPath (Join-Path $root '.agents/persistent-workflow-continuation.txt') -ErrorAction SilentlyContinue
    }
}
