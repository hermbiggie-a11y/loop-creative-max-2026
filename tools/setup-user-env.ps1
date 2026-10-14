# Loop Creative demo - one-time user environment setup.
# Run this yourself in a normal PowerShell window (NOT from inside the Claude app,
# whose sandbox redirects registry/AppData writes). No admin needed.
#   powershell -ExecutionPolicy Bypass -File "C:\Users\Dell Demo\Desktop\Demo\Loop Agency\tools\setup-user-env.ps1"

$ErrorActionPreference = 'Stop'
$H = Join-Path $env:USERPROFILE '.hermes'
$Loop = Join-Path $env:USERPROFILE 'Desktop\Demo\Loop Agency'

function Set-UserVar($name, $value) {
    [Environment]::SetEnvironmentVariable($name, $value, 'User')
    Write-Host "  $name = $value"
}

Write-Host 'Setting user environment variables...'
Set-UserVar HERMES_HOME $H
Set-UserVar LOOP_ROOT $Loop
# Ollama (lighter local model): Hermes rejects Ollama's default 4K context
Set-UserVar OLLAMA_CONTEXT_LENGTH 65536
Set-UserVar OLLAMA_FLASH_ATTENTION 1
Set-UserVar OLLAMA_KV_CACHE_TYPE q8_0
Set-UserVar OLLAMA_KEEP_ALIVE 24h

Write-Host 'Checking user PATH...'
$path = [Environment]::GetEnvironmentVariable('Path', 'User')
$want = @("$H\bin", "$Loop\tools\Faster-Whisper-XXL")
foreach ($p in $want) {
    if (($path -split ';') -notcontains $p) { $path = ($path.TrimEnd(';') + ';' + $p); Write-Host "  + $p" }
    else { Write-Host "  = $p (already there)" }
}
[Environment]::SetEnvironmentVariable('Path', $path, 'User')

Write-Host ''
Write-Host 'Done. Now:'
Write-Host '  1. Quit Ollama from the system tray and start it again (so the OLLAMA_* settings apply).'
Write-Host '  2. Open a NEW PowerShell window and run:  hermes --version'
Write-Host '     Expect: Hermes Agent v0.21.x'
