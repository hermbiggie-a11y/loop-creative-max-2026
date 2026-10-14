# Send one turn to a named Hermes session (rehearsal from the terminal, same agent/tools as Telegram).
#   powershell -File tools\ask.ps1 -Session rehearsal -Message "..."   [-New]
param([Parameter(Mandatory)][string]$Message, [string]$Session = 'rehearsal', [switch]$New)
$env:HERMES_HOME = Join-Path $env:USERPROFILE '.hermes'
$hermes = Join-Path $env:HERMES_HOME 'bin\hermes.exe'
$q = New-TemporaryFile
[IO.File]::WriteAllText($q, $Message, (New-Object Text.UTF8Encoding $false))
Set-Location (Join-Path (Split-Path $PSScriptRoot -Parent) 'cabana')
$sw = [Diagnostics.Stopwatch]::StartNew()
if ($New) { $name = "$Session-$(Get-Date -Format HHmmss)"; Set-Content (Join-Path $env:TEMP 'loop-session.txt') $name }
else { $name = Get-Content (Join-Path $env:TEMP 'loop-session.txt') -ErrorAction SilentlyContinue; if (-not $name) { $name = $Session } }
& $hermes chat -Q --query-file $q -c $name --create-if-missing 2>&1 | Where-Object { $_ -notmatch '^session_id:' }
Write-Host "--- ($([int]$sw.Elapsed.TotalSeconds)s, session $name)"
Remove-Item $q
