<#
.SYNOPSIS
Close a Windows Terminal tab by its title.

.DESCRIPTION
Windows Terminal exposes no command-line verb for closing a tab: `wt` can open, split and focus one, and
that is all. Killing the tab's process is not the same thing — under the default `closeOnExit: automatic`
a killed process exits non-zero and Terminal keeps the dead pane, which is how stale tabs accumulate.

This drives UI Automation instead: it finds the TabItem whose Name matches, takes that tab's own
`CloseButton`, and invokes it. Targeting is by title through the accessibility tree rather than by
keystroke, so it cannot act on whichever tab happens to have focus.

Two guards, both learned by breaking them. A wildcard never closes on its own — it reports what it would
close and stops — because a pattern meant to match several can match exactly one and take it silently. And
a tab whose Claude process is still running is refused without `-Force`: the case this exists for is a tab
left behind by a process that has already gone.

Pair it with `closeOnExit: always` in Terminal's profile defaults, which makes a tab close with its
process and leaves this for tabs that are already stale.
#>
[CmdletBinding(DefaultParameterSetName = 'Close', SupportsShouldProcess)]
param(
    # Exact tab title, or a wildcard pattern. A wildcard reports and stops unless -All is passed.
    [Parameter(Mandatory, Position = 0, ParameterSetName = 'Close')]
    [string] $Title,

    [Parameter(Mandatory, ParameterSetName = 'List')]
    [switch] $List,

    [Parameter(Mandatory, ParameterSetName = 'Json')]
    [switch] $Json,

    # Act on a wildcard's matches rather than only reporting them.
    [Parameter(ParameterSetName = 'Close')]
    [switch] $All,

    # Close even a tab whose process is still alive.
    [Parameter(ParameterSetName = 'Close')]
    [switch] $Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes

function Get-TabEntryProperty {
    param($Entry, [string] $Name)

    $property = $Entry.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Test-PidStartedAtLive {
    param([int] $ProcessId, [double] $PidStartedAt)

    $process = try { Get-Process -Id $ProcessId -ErrorAction Stop } catch { $null }
    $startTime = if ($process) { try { $process.StartTime } catch { $null } } else { $null }
    if ($null -eq $startTime) { return $false }
    $actual = ([DateTimeOffset]($startTime.ToUniversalTime())).ToUnixTimeMilliseconds() / 1000.0
    return [math]::Abs($actual - $PidStartedAt) -le 2.0
}

function Test-TabIsLive {
    param([string] $Title)

    # Registered sessions carry their tab title, so liveness is answered per tab rather than per window:
    # one window holds many tabs, and counting its processes refuses a stale tab whenever any sibling runs.
    # A title with no entry predates the registry, and unknown is not the same as dead - it needs -Force.
    $root = if ($env:AGENT_STATE_DIRECTORY) { $env:AGENT_STATE_DIRECTORY } else { Join-Path $HOME '.agents-state' }
    $directory = Join-Path $root 'cli-sessions'
    if (-not (Test-Path -LiteralPath $directory)) { return $true }

    $entries = @(Get-ChildItem -LiteralPath $directory -Filter '*.json' -File | ForEach-Object {
        try { Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $null }
    } | Where-Object { $_ -and $_.title -eq $Title })

    if ($entries.Count -eq 0) { return $true }

    foreach ($entry in $entries) {
        if ($null -eq (Get-TabEntryProperty -Entry $entry -Name 'pid_started_at')) { return $true }
    }

    foreach ($entry in $entries) {
        $pidStartedAt = Get-TabEntryProperty -Entry $entry -Name 'pid_started_at'
        if (Test-PidStartedAtLive -ProcessId $entry.pid -PidStartedAt $pidStartedAt) { return $true }
    }
    return $false
}

function Get-TerminalTabs {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $terminals = Get-Process -Name 'WindowsTerminal' -ErrorAction SilentlyContinue
    if (-not $terminals) { return @() }

    $tabType = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::TabItem)

    foreach ($terminal in $terminals) {
        $byPid = New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ProcessIdProperty, $terminal.Id)
        $window = $root.FindFirst([System.Windows.Automation.TreeScope]::Children, $byPid)
        if (-not $window) { continue }

        foreach ($tab in $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $tabType)) {
            [pscustomobject]@{
                Title      = $tab.Current.Name
                TerminalId = $terminal.Id
                Live       = Test-TabIsLive -Title $tab.Current.Name
                Element    = $tab
            }
        }
    }
}

function Resolve-TabMatches {
    param([object[]] $Tabs, [string] $Title)

    $exact = @($Tabs | Where-Object { $_.Title -eq $Title })
    $wildcard = $exact.Count -eq 0
    $matched = @(if ($wildcard) { $Tabs | Where-Object { $_.Title -like $Title } } else { $exact })
    return [pscustomobject]@{ Matched = $matched; Wildcard = $wildcard }
}

function Close-Tab {
    param([object] $Tab)

    if (-not $PSCmdlet.ShouldProcess($Tab.Title, 'Close Terminal tab')) { return }

    $byId = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::AutomationIdProperty, 'CloseButton')
    $button = $Tab.Element.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $byId)
    if (-not $button) {
        Write-Warning "'$($Tab.Title)' exposes no close button; leaving it."
        return
    }

    $button.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    Write-Output "Closed '$($Tab.Title)'."
}

$tabs = @(Get-TerminalTabs)

if ($List) {
    if ($tabs.Count -eq 0) { Write-Output 'No Windows Terminal tabs found.'; return }
    $tabs | Format-Table -AutoSize Title, Live, TerminalId
    return
}

if ($Json) {
    $payload = @($tabs | ForEach-Object {
        [pscustomobject]@{ title = $_.Title; live = $_.Live; terminalId = $_.TerminalId }
    })
    Write-Output (ConvertTo-Json -InputObject $payload -Depth 4)
    return
}

$resolved = Resolve-TabMatches -Tabs $tabs -Title $Title
$matched = $resolved.Matched
$wildcard = $resolved.Wildcard

if ($matched.Count -eq 0) {
    throw "No tab titled '$Title'. Run with -List to see what is open."
}

# A pattern is a request to find tabs, not yet a decision to close them. An exact title is the decision.
if ($wildcard -and -not $All) {
    Write-Output "'$Title' is a pattern, so nothing was closed. It matches:"
    $matched | ForEach-Object { Write-Output "  - $($_.Title)" }
    Write-Output 'Pass the exact title to close one, or -All to close every match.'
    return
}

foreach ($tab in $matched) {
    if ($tab.Live -and -not $Force) {
        Write-Warning ("'$($tab.Title)' is live, or predates the session registry. This closes tabs whose " +
            'process has already gone; pass -Force to close it anyway.')
        continue
    }
    Close-Tab -Tab $tab
}
