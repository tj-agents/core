#Requires -Version 7
<#
.SYNOPSIS
Repository-vendored worktree helper. `audit` is read-only and never deletes anything.

.DESCRIPTION
`audit` emits one line per finding to stdout for `worktree_cleanup_gate.py` to read. The gate blocks a
session's Stop event only on MERGED_NOT_IN_MAIN or ORPHAN_FOLDER lines; anything else is informational.
Local-only (no network, no gh) so it stays fast and reliable inside the gate's 10-second budget.
#>
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateSet('audit')]
    [string] $Action
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-DefaultBranch {
    $ref = git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>$null
    if ($LASTEXITCODE -eq 0 -and $ref) { return ($ref -replace '^origin/', '') }
    return 'main'
}

function Normalize-Path([string]$Path) {
    ($Path.TrimEnd('/', '\') -replace '\\', '/')
}

function Get-RegisteredWorktrees {
    $lines = git worktree list --porcelain 2>$null
    $trees = @(); $path = $null; $head = $null; $branch = $null; $detached = $false
    foreach ($line in $lines) {
        if ($line -like 'worktree *') { $path = $line.Substring(9) }
        elseif ($line -like 'HEAD *') { $head = $line.Substring(5) }
        elseif ($line -like 'branch *') { $branch = $line -replace '^branch refs/heads/', '' }
        elseif ($line -eq 'detached') { $detached = $true }
        elseif ($line -eq '') {
            if ($path) { $trees += [pscustomobject]@{ Path = $path; Head = $head; Branch = $branch; Detached = $detached } }
            $path = $null; $head = $null; $branch = $null; $detached = $false
        }
    }
    if ($path) { $trees += [pscustomobject]@{ Path = $path; Head = $head; Branch = $branch; Detached = $detached } }
    return $trees
}

# A freshly branched worktree (`git worktree add <path> -b <branch> origin/<default>`) is at the same
# commit as origin/<default> from the moment it exists, which makes it indistinguishable from a branch
# that was later fast-forwarded back onto origin/<default> after merging - by commit graph alone, both
# have zero commits ahead. The two differ in history: a branch that actually did work has `commit`
# reflog entries of its own, and a branch whose own remote tracking ref was merged and pruned reports
# its upstream as gone. Neither is true for a branch that was only ever created and never advanced.
function Test-FreshUnstartedBranch([string]$Branch) {
    $subjects = @(git reflog show --format='%gs' "refs/heads/$Branch" 2>$null)
    if ($LASTEXITCODE -ne 0) { return $false }
    if ($subjects | Where-Object { $_ -like 'commit*' }) { return $false }
    $track = git for-each-ref --format='%(upstream:track)' "refs/heads/$Branch" 2>$null
    if ($LASTEXITCODE -eq 0 -and $track -eq '[gone]') { return $false }
    return $true
}

switch ($Action) {
    'audit' {
        $main = Get-DefaultBranch
        $trees = @(Get-RegisteredWorktrees)
        if ($trees.Count -eq 0) { return }
        $root = $trees[0].Path
        $registered = @{}
        foreach ($t in $trees) { $registered[(Normalize-Path $t.Path)] = $true }

        foreach ($t in ($trees | Select-Object -Skip 1)) {
            if ($t.Detached) {
                if (-not $t.Head) { continue }
                git merge-base --is-ancestor $t.Head "origin/$main" 2>$null | Out-Null
                if ($LASTEXITCODE -ne 0) { Write-Output "DETACHED_UNSAFE $($t.Path)" }
                continue
            }
            if (-not $t.Branch) { continue }
            $ahead = git rev-list --count "origin/$main..$($t.Branch)" 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
            if ([int]$ahead -eq 0) {
                if (Test-FreshUnstartedBranch $t.Branch) { continue }
                Write-Output "MERGED_NOT_IN_MAIN $($t.Path)"; continue
            }
            $newCommits = @(git cherry "origin/$main" $t.Branch 2>$null | Where-Object { $_ -like '+*' })
            if ($newCommits.Count -eq 0) { Write-Output "MERGED_NOT_IN_MAIN $($t.Path)" }
        }

        $candidateBases = @(
            (Join-Path $root '.worktrees'),
            (Join-Path (Split-Path $root -Parent) "$(Split-Path $root -Leaf).worktrees")
        )
        foreach ($base in $candidateBases) {
            if (-not (Test-Path -LiteralPath $base)) { continue }
            Get-ChildItem -LiteralPath $base -Directory | ForEach-Object {
                if (-not $registered.ContainsKey((Normalize-Path $_.FullName))) {
                    Write-Output "ORPHAN_FOLDER $($_.FullName)"
                }
            }
        }
    }
}
