# Run a Loop tools/*.py script with the dedicated venv (tools/.venv: python-socketio, websocket-client, requests).
#   powershell -NoProfile -File C:/Loop/tools/py.ps1 social_resize.py "ICE, MIAMI." 1080x1920
# stdout is the script's result; stderr (bridge chatter, tracebacks) goes to cabana/work/py.log for debugging.
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$log = Join-Path $PSScriptRoot '..\cabana\work\py.log'   # tools/ is read-only
$script, $rest = $args
"`n=== $(Get-Date -Format s) $script $($rest -join ' ')" | Out-File -Append -Encoding utf8 $log
& $python $script @rest 2>> $log
$rc = $LASTEXITCODE
if ($rc -ne 0) { Write-Output "py.ps1: $script exited $rc - last log lines:"; Get-Content $log -Tail 8 | Where-Object { $_ -notmatch 'LOGGER' } }
exit $rc
