# Unattended rehearsal of beats 1-3 through Hermes (same agent, tools and skills as Telegram, minus the phone).
# Sends the exact prompts.txt lines in order and logs replies + timings to cabana/work/rehearsal-<time>.log
#   powershell -ExecutionPolicy Bypass -File C:/Loop/tools/rehearse.ps1 [-NoReset] [-Beats 123]
param([switch]$NoReset, [string]$Beats = '123')
$ask = Join-Path $PSScriptRoot 'ask.ps1'
$log = Join-Path $PSScriptRoot "..\cabana\work\rehearsal-$(Get-Date -Format HHmmss).log"
if (-not $NoReset) { & (Join-Path $PSScriptRoot 'reset-cabana.ps1') 2>$null | Out-Null }

$script = @{
  '1' = @('New client: Cabana Cold Brew, a canned cold brew launching in Miami on June 1st. We need one hero key visual, six social sizes, a 30-second spot cut from our raw footage, and captions. Write the brief.',
        'B, and make the headline shorter.')
  '2' = @('Open the Cabana hero, extend the beach with Generative Fill, put our headline on it, and send me three headline options.',
        '2')
  '3' = @('Cut the 30-second spot from the raw footage in shot-list order and send me frames at 0, 10, 20 and 29 seconds.',
        'Open on the pour, drop the beach shot, shorter dissolves.',
        'go')
}
$first = $true
foreach ($b in $Beats.ToCharArray() | ForEach-Object { "$_" }) {
  foreach ($msg in $script[$b]) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $args2 = @('-ExecutionPolicy', 'Bypass', '-File', $ask, '-Message', $msg)
    if ($first) { $args2 += '-New'; $first = $false }
    $out = & powershell @args2 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'NativeCommandError|CategoryInfo|^At |^\+ |Resumed session|Starting fresh|has no messages' }
    $block = "`n===== BEAT $b  >> $msg  ($([int]$sw.Elapsed.TotalSeconds)s)`n" + ($out -join "`n")
    $block | Tee-Object -FilePath $log -Append
  }
}
Write-Host "`nlog: $log"
