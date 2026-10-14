# Reset the Cabana demo to its starting state (run between demo runs, ~15 s).
#   powershell -ExecutionPolicy Bypass -File "C:\Users\Dell Demo\Desktop\Demo\Loop Agency\tools\reset-cabana.ps1"
# 1. closes the Premiere project (saved, no prompt) so Premiere releases and forgets the old work copy
# 2. wipes the writable folders (work, social, cut) and restores working copies from _master
# 3. reopens the fresh work project in Premiere
# _master, raw, brand.md and prompts.txt are read-only and never touched.

$ErrorActionPreference = 'Stop'
$Tools  = $PSScriptRoot
$Cabana = Join-Path $PSScriptRoot '..\cabana' | Resolve-Path | Select-Object -ExpandProperty Path
$env:HERMES_HOME = Join-Path $env:USERPROFILE '.hermes'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $env:HERMES_HOME 'python'
$env:UV_CACHE_DIR = Join-Path $env:HERMES_HOME 'uv-cache'
$uv = Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe'
function Adobe($app, $action, $json = '{}') {
    $ErrorActionPreference = 'Continue'   # uv/socket log lines on stderr are not errors
    $f = New-TemporaryFile
    [IO.File]::WriteAllText($f, "[{`"app`":`"$app`",`"action`":`"$action`",`"timeout`":60,`"options`":$json}]")
    Push-Location $Tools
    try { & (Join-Path $Tools '.venv\Scripts\python.exe') ps_step.py $f 2>$null | Select-Object -First 1 }
    finally { Pop-Location; Remove-Item $f }
}

Write-Host 'Closing Photoshop documents and the Premiere project...'
Adobe photoshop closeAllDocuments | Out-Host
Adobe premiere closeProject | Out-Host

foreach ($d in 'work', 'social', 'cut') {
    $p = Join-Path $Cabana $d
    if (Test-Path $p) {
        foreach ($item in Get-ChildItem -LiteralPath $p -Force) {
            try { Remove-Item -LiteralPath $item.FullName -Recurse -Force -ErrorAction Stop }
            catch { Write-Warning "kept $($item.Name) (in use - close it in Photoshop/Premiere if it matters)" }
        }
    }
    else { New-Item -ItemType Directory $p | Out-Null }
}

# Working copies the agent is allowed to edit
$master = Join-Path $Cabana '_master'
foreach ($f in 'hero.psd', 'hero-extended.psd', 'cabana.prproj') {
    $src = Join-Path $master $f
    if (Test-Path $src) {
        $dst = Join-Path $Cabana "work\$f"
        Copy-Item $src $dst -Force
        Set-ItemProperty $dst -Name IsReadOnly -Value $false   # copies inherit the master's read-only attribute
    }
}

Write-Host 'Opening fresh work project in Premiere...'
$proj = ((Join-Path $Cabana 'work\cabana.prproj') -replace '\\', '/')
Adobe premiere openProject "{`"filePath`":`"$proj`"}" | Out-Host

Write-Host "`nCabana reset: work, social, cut cleared; working copies restored from _master."
Write-Host 'Next: in Telegram send /new, confirm both Adobe panels say Connected, re-plug ethernet, /model back to online.'
