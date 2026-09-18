[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Path,

    # Copy the literal text only — no HTML flavour, backticks left exactly as typed.
    [switch]$PlainOnly
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Path)) {
    throw "Draft file not found: $Path"
}

$raw = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $Path), [System.Text.UTF8Encoding]::new($false))
$raw = ($raw -replace "`r`n", "`n") -replace '\s+$', ''

if ([string]::IsNullOrWhiteSpace($raw)) {
    throw "Draft file is empty: $Path"
}

# Backticks are markup, not content. The plain flavour is what an app that cannot
# take HTML receives, so they come out of it.
$plain = if ($PlainOnly) { $raw } else { $raw -replace '`([^`]+)`', '$1' }

if ($PlainOnly) {
    Set-Clipboard -Value $plain
    $back = Get-Clipboard -Raw
    if ($null -ne $back) { $back = $back -replace '\s+$', '' }
    if ($back -ne $plain) { throw 'Clipboard verification failed.' }
    "Copied $($plain.Length) chars (plain text only)."
    return
}

$escaped = $raw.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;')
$withCode = [regex]::Replace($escaped, '`([^`]+)`', {
        param($m)
        '<code style="font-family:Consolas,''Courier New'',monospace;">' + $m.Groups[1].Value + '</code>'
    })
# No block elements: Teams gives <p> and <div> their own margins/indent on paste,
# so paragraphs are separated with breaks instead.
$fragment = (($withCode -split "`n{2,}") | ForEach-Object { $_ -replace "`n", '<br>' }) -join '<br><br>'

$pre = '<html><body><!--StartFragment-->'
$post = '<!--EndFragment--></body></html>'
$headerTemplate = "Version:0.9`r`nStartHTML:{0:D10}`r`nEndHTML:{1:D10}`r`nStartFragment:{2:D10}`r`nEndFragment:{3:D10}`r`n"

$enc = [System.Text.UTF8Encoding]::new($false)
$startHtml = ($headerTemplate -f 0, 0, 0, 0).Length
$startFragment = $startHtml + $enc.GetByteCount($pre)
$endFragment = $startFragment + $enc.GetByteCount($fragment)
$endHtml = $endFragment + $enc.GetByteCount($post)

$cfHtml = ($headerTemplate -f $startHtml, $endHtml, $startFragment, $endFragment) + $pre + $fragment + $post

# WinForms clipboard needs an STA apartment; PowerShell 7 runs MTA by default.
$rs = [runspacefactory]::CreateRunspace()
$rs.ApartmentState = 'STA'
$rs.Open()
try {
    $ps = [powershell]::Create()
    $ps.Runspace = $rs
    [void]$ps.AddScript({
            param($h, $t)
            Add-Type -AssemblyName System.Windows.Forms
            $d = [System.Windows.Forms.DataObject]::new()
            $d.SetData([System.Windows.Forms.DataFormats]::Html, $h)
            $d.SetData([System.Windows.Forms.DataFormats]::UnicodeText, $t)
            [System.Windows.Forms.Clipboard]::SetDataObject($d, $true)
        }).AddArgument($cfHtml).AddArgument($plain)
    [void]$ps.Invoke()
    if ($ps.Streams.Error.Count) { throw "Clipboard write failed: $($ps.Streams.Error[0])" }
}
finally {
    $rs.Close()
}

# Verify BOTH flavours off the live clipboard. A plain-only round-trip passes while
# the HTML is absent, which is exactly how a paste loses its code formatting.
$verifyRs = [runspacefactory]::CreateRunspace()
$verifyRs.ApartmentState = 'STA'
$verifyRs.Open()
try {
    $vps = [powershell]::Create()
    $vps.Runspace = $verifyRs
    [void]$vps.AddScript({
            Add-Type -AssemblyName System.Windows.Forms
            $d = [System.Windows.Forms.Clipboard]::GetDataObject()
            [pscustomobject]@{
                Formats = @($d.GetFormats())
                Html    = [string]$d.GetData('HTML Format')
                Text    = [string]$d.GetData([System.Windows.Forms.DataFormats]::UnicodeText)
            }
        })
    $state = $vps.Invoke() | Select-Object -Last 1
}
finally {
    $verifyRs.Close()
}

$spans = ([regex]::Matches($fragment, '<code')).Count

if ($state.Formats -notcontains 'HTML Format') {
    throw "Clipboard verification failed: no HTML flavour present (formats: $($state.Formats -join ', ')). Something overwrote the clipboard."
}
if (($state.Text -replace '\s+$', '') -ne $plain) {
    throw 'Clipboard verification failed: plain flavour did not round-trip.'
}
$landedSpans = ([regex]::Matches($state.Html, '<code')).Count
if ($landedSpans -ne $spans) {
    throw "Clipboard verification failed: expected $spans code spans, found $landedSpans on the clipboard."
}

"Copied $($plain.Length) chars, $spans code spans, HTML + plain verified on the clipboard."
