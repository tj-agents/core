param([Parameter(Mandatory)][string] $TabId)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$root = [System.Windows.Automation.AutomationElement]::RootElement
$tabCondition = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::AutomationIdProperty, $TabId)
$windowType = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
    [System.Windows.Automation.ControlType]::Window)
$matches = @()
foreach ($window in @($root.FindAll([System.Windows.Automation.TreeScope]::Children, $windowType))) {
    $process = Get-Process -Id $window.Current.ProcessId -ErrorAction SilentlyContinue
    if (-not $process -or $process.ProcessName -notin @('WindowsTerminal', 'WindowsTerminalPreview')) { continue }
    $matches += @($window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $tabCondition))
}
if ($matches.Count -ne 1) { throw "Expected one Windows Terminal tab with AutomationId '$TabId', found $($matches.Count)." }
$close = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::AutomationIdProperty, 'CloseButton')
$button = $matches[0].FindFirst([System.Windows.Automation.TreeScope]::Descendants, $close)
if (-not $button) { throw "Windows Terminal tab '$TabId' has no close button." }
$button.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
