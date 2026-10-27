# Opens the simulated Telegram panel (Edge app window, own profile, 100% scale) on the right third of the screen.
$R = $PSScriptRoot
Start-Process "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" -ArgumentList "--app=http://127.0.0.1:8765/", "--user-data-dir=`"$R\edge-profile`"", "--no-first-run", "--force-device-scale-factor=1", "--window-size=640,1080"
Start-Sleep 4
& "$R\winpos.ps1" -Proc msedge-loopchat -X 1273 -Y -36 -W 654 -H 1116
