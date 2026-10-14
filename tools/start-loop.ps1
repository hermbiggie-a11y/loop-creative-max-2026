# Loop Creative demo - one-command launch (run from a normal PowerShell window, after opening
# Photoshop, Premiere Pro and UXP Developer Tools):
#   powershell -ExecutionPolicy Bypass -File "C:\Users\Dell Demo\Desktop\Demo\Loop Agency\tools\start-loop.ps1"
# Options: -ReloadOnly (just reload the Adobe plugins), -NoGateway (skip Telegram gateway)
param([switch]$ReloadOnly, [switch]$NoGateway)

$ErrorActionPreference = 'Stop'
$Loop  = Split-Path $PSScriptRoot -Parent
$Tools = $PSScriptRoot
$env:HERMES_HOME = Join-Path $env:USERPROFILE '.hermes'
$hermes = Join-Path $env:HERMES_HOME 'bin\hermes.exe'

function Step($m) { Write-Host "`n== $m" -ForegroundColor Cyan }
function Ok($m)   { Write-Host "   OK  $m" -ForegroundColor Green }
function Warn($m) { Write-Host "   !!  $m" -ForegroundColor Yellow }
function PortOpen($p) { try { (New-Object Net.Sockets.TcpClient('127.0.0.1', $p)).Close(); $true } catch { $false } }

if (-not $ReloadOnly) {
    # 1. adb-mcp proxy (from source: the prebuilt exe rejects Premiere's polling transport)
    Step 'Adobe bridge proxy (port 3001)'
    if (PortOpen 3001) { Ok 'already running' }
    else {
        $proxyDir = Join-Path $Tools 'adb-mcp\adb-proxy-socket'
        Start-Process powershell -ArgumentList '-NoExit', '-Command', "`$host.UI.RawUI.WindowTitle='adb-mcp proxy'; node proxy.js" -WorkingDirectory $proxyDir
        foreach ($i in 1..20) { if (PortOpen 3001) { break }; Start-Sleep -Milliseconds 500 }
        if (PortOpen 3001) { Ok 'started (window: adb-mcp proxy)' } else { Warn 'proxy did not open port 3001' }
    }

    # 2. Ollama (offline model 2) - only needs to be running, models load on demand
    Step 'Ollama'
    if (PortOpen 11434) { Ok 'running' }
    else {
        $ollama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama app.exe'
        if (Test-Path $ollama) { Start-Process $ollama; Ok 'started' } else { Warn 'Ollama not installed' }
    }
}

# 3. Reload the UXP plugins (they never survive an app restart)
Step 'Reload Photoshop + Premiere MCP plugins'
if (-not (PortOpen 14001)) {
    Warn 'UXP Developer Tools is not running - opening it'
    Start-Process 'C:\Program Files\Adobe\Adobe UXP Developer Tools\Adobe UXP Developer Tools.exe'
    foreach ($i in 1..30) { if (PortOpen 14001) { break }; Start-Sleep 1 }
}
$loaded = $false
foreach ($try in 1..5) {
    $out = & node (Join-Path $Tools 'uxp-load\load-plugins.js') 2>&1
    $out | ForEach-Object { Write-Host "   $_" }
    if (($out -match 'loaded ps') -and ($out -match 'loaded pr')) { $loaded = $true; break }
    Warn "not both apps yet (attempt $try/5) - is Photoshop AND Premiere open? retrying in 5 s"
    Start-Sleep 5
}
if ($loaded) { Ok 'both plugins loaded; they auto-connect in ~2 s' }
Write-Host '   Premiere only: the "Premiere MCP Agent" panel must be open (Window > UXP Plugins) the first time.'

if ($ReloadOnly) { return }

# 4. Telegram gateway
if (-not $NoGateway) {
    Step 'Hermes Telegram gateway'
    $status = & $hermes gateway status 2>&1 | Out-String
    if ($status -match 'Gateway process running') { Ok 'running' }
    else {
        schtasks /Run /TN (& $hermes gateway status 2>&1 | Select-String 'Hermes_Gateway_\w+' | ForEach-Object { $_.Matches[0].Value } | Select-Object -First 1) | Out-Null
        Start-Sleep 20
        if ((& $hermes gateway status 2>&1 | Out-String) -match 'Gateway process running') { Ok 'started' } else { Warn 'gateway not running - run: hermes gateway run' }
    }
}

# 5. Health check through the real bridge
Step 'Health check'
Start-Sleep 3
$uv = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $env:HERMES_HOME 'python'; $env:UV_CACHE_DIR = Join-Path $env:HERMES_HOME 'uv-cache'
foreach ($app in 'photoshop', 'premiere') {
    $action = if ($app -eq 'photoshop') { 'getDocuments' } else { 'getProjectInfo' }
    $r = & (Join-Path $Tools '.venv\Scripts\python.exe') (Join-Path $Tools 'adobe.py') $app $action --timeout 15 2>$null
    if ($r -match '"SUCCESS"' -or $r -match 'Requires an open') { Ok "$app connected" } else { Warn "$app NOT connected: $r" }
}
Write-Host "`nReady. From your phone: ping" -ForegroundColor Green
