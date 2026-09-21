#Requires -Version 7
<#
.SYNOPSIS
List, inspect and close the other Claude CLI sessions on this machine, addressed by the tab title the
user can see.

.DESCRIPTION
`list` prints every recorded session with its tab title, directory, pid and whether its process is still
alive. `close` ends one. `resolve` maps a tab title to a session id, which is what lets an agent name a
peer the way the user sees it rather than by a branch-derived internal name.

A session is recorded at SessionStart by register_session.py. A session started before that hook existed,
or outside the launcher, has no entry; `list -IncludeUnrecorded` also reports live claude.exe processes
with no entry so nothing is invisible.
#>
[CmdletBinding(DefaultParameterSetName = 'List')]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('list', 'close', 'resolve')]
    [string] $Action,

    # Tab title (exact or unique prefix) or session id. Required by close and resolve.
    [Parameter(Position = 1)]
    [string] $Session,

    [switch] $IncludeUnrecorded,

    # close only: end the process without the confirmation prompt.
    [switch] $Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-StateDirectory {
    $override = $env:AGENT_STATE_DIRECTORY
    $root = if ($override) { $override } else { Join-Path $HOME '.agents-state' }
    Join-Path $root 'cli-sessions'
}

function Get-RecordedSessions {
    $directory = Get-StateDirectory
    if (-not (Test-Path -LiteralPath $directory)) { return @() }

    Get-ChildItem -LiteralPath $directory -Filter '*.json' -File | ForEach-Object {
        $entry = try { Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json } catch { $null }
        if (-not $entry) { return }

        $process = try { Get-Process -Id $entry.pid -ErrorAction Stop } catch { $null }
        # A pid is reused once its owner exits, so age-match before believing a live process is this one.
        $alive = $null -ne $process -and $process.StartTime.ToUniversalTime() -le
            [DateTimeOffset]::FromUnixTimeSeconds([long]$entry.started_at).UtcDateTime.AddMinutes(1)

        [pscustomobject]@{
            Title     = $entry.title
            SessionId = $entry.session_id
            Cwd       = $entry.cwd
            Pid       = $entry.pid
            Alive     = $alive
            Recorded  = $true
        }
    }
}

function Get-UnrecordedSessions {
    param([object[]] $Known)

    $knownPids = @($Known | ForEach-Object { $_.Pid })
    Get-Process -Name 'claude' -ErrorAction SilentlyContinue |
        Where-Object { $_.Id -notin $knownPids } |
        ForEach-Object {
            [pscustomobject]@{
                Title     = $null
                SessionId = $null
                Cwd       = $null
                Pid       = $_.Id
                Alive     = $true
                Recorded  = $false
            }
        }
}

function Find-Session {
    param([object[]] $Sessions, [string] $Needle)

    if (-not $Needle) { throw "'$Action' needs a tab title or session id." }

    $matched = @($Sessions | Where-Object { $_.SessionId -eq $Needle -or $_.Title -eq $Needle })
    if ($matched.Count -eq 0) {
        $matched = @($Sessions | Where-Object {
            $_.Title -and $_.Title.StartsWith($Needle, [StringComparison]::OrdinalIgnoreCase)
        })
    }

    if ($matched.Count -eq 0) { throw "No session matches '$Needle'. Run 'list' to see what is recorded." }
    if ($matched.Count -gt 1) {
        $titles = ($matched | ForEach-Object { "$($_.Title) [$($_.SessionId)]" }) -join ', '
        throw "'$Needle' matches more than one session: $titles. Use a session id."
    }
    $matched[0]
}

$sessions = @(Get-RecordedSessions)
if ($IncludeUnrecorded) { $sessions += @(Get-UnrecordedSessions -Known $sessions) }

switch ($Action) {
    'list' {
        if ($sessions.Count -eq 0) { Write-Output 'No CLI sessions recorded.'; break }
        $sessions |
            Sort-Object -Property @{ Expression = 'Alive'; Descending = $true }, 'Title' |
            Format-Table -AutoSize Title, SessionId, Alive, Pid, Cwd
    }
    'resolve' {
        (Find-Session -Sessions $sessions -Needle $Session).SessionId
    }
    'close' {
        $target = Find-Session -Sessions $sessions -Needle $Session
        if (-not $target.Alive) {
            Write-Output "'$($target.Title ?? $target.SessionId)' is already gone."
            break
        }
        if (-not $Force) {
            $answer = Read-Host "Close '$($target.Title ?? $target.SessionId)' (pid $($target.Pid))? [y/N]"
            if ($answer -notmatch '^(y|yes)$') { Write-Output 'Left running.'; break }
        }
        Stop-Process -Id $target.Pid -ErrorAction Stop
        Write-Output "Closed '$($target.Title ?? $target.SessionId)' (pid $($target.Pid))."
    }
}
