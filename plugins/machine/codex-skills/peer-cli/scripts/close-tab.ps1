#Requires -Version 7
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

function Test-TabIsLive {
    param([string] $Title)

    # Registered sessions carry their tab title, so liveness is answered per tab rather than per window:
    # one window holds many tabs, and counting its processes refuses a stale tab whenever any sibling runs.
    # A title with no entry predates the registry, and unknown is not the same as dead - it needs -Force.
    $root = if ($env:AGENT_STATE_DIRECTORY) { $env:AGENT_STATE_DIRECTORY } else { Join-Path $HOME '.agents-state' }
    $directory = Join-Path $root 'cli-sessions'
    if (-not (Test-Path -LiteralPath $directory)) { return $true }

    $entries = @(Get-ChildItem -LiteralPath $directory -Filter '*.json' -File | ForEach-Object {
        try { Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json } catch { $null }
    } | Where-Object { $_ -and $_.title -eq $Title })

    if ($entries.Count -eq 0) { return $true }
    foreach ($entry in $entries) {
        if (Get-Process -Id $entry.pid -ErrorAction SilentlyContinue) { return $true }
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

$exact = @($tabs | Where-Object { $_.Title -eq $Title })
$wildcard = $exact.Count -eq 0

$matched = if ($wildcard) { @($tabs | Where-Object { $_.Title -like $Title }) } else { $exact }

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
