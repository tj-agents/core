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

`list` scopes to what the caller plausibly cares about: sessions under the current repository and under
its parent folder (the sibling repos beside it - an "org" of related checkouts). Pass `-Under` for an
explicit scope instead, or `-All` to see every recorded session on the machine unfiltered. A caller not
inside a git repository gets `-All` behavior automatically, since there is no repo root to scope to.
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

    # list only: show every recorded session, ignoring the repo/org scope.
    [switch] $All,

    # list only: scope to sessions whose directory is under this path instead of the auto-detected scope.
    [string] $Under,

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
        # StartTime is null, not an exception, for a process this account cannot query (e.g. a reused pid
        # now owned by another user's or a protected process) - that is not provably our session either.
        $startTime = if ($process) { try { $process.StartTime } catch { $null } } else { $null }
        $alive = $null -ne $startTime -and $startTime.ToUniversalTime() -le
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

function Get-RepoRoot {
    param([string] $From = (Get-Location).Path)

    $current = Get-Item -LiteralPath $From
    while ($current) {
        if (Test-Path -LiteralPath (Join-Path $current.FullName '.git')) { return $current.FullName }
        $current = $current.Parent
    }
    return $null
}

function Test-UnderPath {
    param([string] $Path, [string] $Root)

    if (-not $Path -or -not $Root) { return $false }
    $normalizedPath = $Path.TrimEnd('\', '/')
    $normalizedRoot = $Root.TrimEnd('\', '/')
    if ($normalizedPath.Equals($normalizedRoot, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    return $normalizedPath.StartsWith($normalizedRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)
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

        $scoped = $sessions
        $scopeNote = $null
        if (-not $All) {
            if ($Under) {
                $scoped = @($sessions | Where-Object { Test-UnderPath -Path $_.Cwd -Root $Under })
                $scopeNote = "scoped to '$Under'"
            }
            else {
                $repoRoot = Get-RepoRoot
                if ($repoRoot) {
                    $orgRoot = (Get-Item -LiteralPath $repoRoot).Parent.FullName
                    $scoped = @($sessions | Where-Object {
                        (Test-UnderPath -Path $_.Cwd -Root $repoRoot) -or (Test-UnderPath -Path $_.Cwd -Root $orgRoot)
                    })
                    $scopeNote = "scoped to '$orgRoot' (pass -All for every machine session, -Under <path> for a different scope)"
                }
                else {
                    $scopeNote = 'not in a git repository; showing every recorded session (pass -Under <path> to scope)'
                }
            }
        }

        if ($scopeNote) { Write-Output $scopeNote }
        if ($scoped.Count -eq 0) {
            Write-Output 'No CLI sessions in scope.'
            break
        }
        $scoped |
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
        # Stop-Process only kills the named pid, not its children. Each Bash-tool call spawns its own
        # bash.exe/sh.exe tree, and an orphaned child left running after the parent dies can still hold
        # a real directory lock on whatever it was cd'd into - taskkill /T kills the whole tree.
        & taskkill.exe /PID $target.Pid /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "taskkill exited $LASTEXITCODE closing pid $($target.Pid)" }
        Write-Output "Closed '$($target.Title ?? $target.SessionId)' (pid $($target.Pid))."
    }
}
