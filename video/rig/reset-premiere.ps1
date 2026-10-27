# Retake helper: reset only the Premiere side (beat 3) - close project, clear cut/, restore the work project, reopen.
$Tools = 'C:\Loop\tools'; $Cabana = 'C:\Loop\cabana'
function Adobe($app, $action, $json = '{}') {
    $f = New-TemporaryFile
    [IO.File]::WriteAllText($f, "[{`"app`":`"$app`",`"action`":`"$action`",`"timeout`":60,`"options`":$json}]")
    Push-Location $Tools; try { & "$Tools\.venv\Scripts\python.exe" ps_step.py $f 2>$null | Select-Object -First 1 } finally { Pop-Location; Remove-Item $f }
}
Adobe premiere closeProject
Get-ChildItem "$Cabana\cut" -Force | Remove-Item -Recurse -Force
Get-ChildItem "$Cabana\work" -Force | Where-Object { $_.Name -notmatch '^(brief\.md|hero.*)$' } | Remove-Item -Recurse -Force
Copy-Item "$Cabana\_master\cabana.prproj" "$Cabana\work\cabana.prproj" -Force; Set-ItemProperty "$Cabana\work\cabana.prproj" IsReadOnly $false
Adobe premiere openProject "{`"filePath`":`"C:/Loop/cabana/work/cabana.prproj`"}"
