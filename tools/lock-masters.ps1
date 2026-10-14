# Make the Loop source files read-only for this Windows user (and therefore for Hermes, which runs as this user).
#   powershell -ExecutionPolicy Bypass -File "C:\Users\Dell Demo\Desktop\Demo\Loop Agency\tools\lock-masters.ps1"           # lock
#   powershell -ExecutionPolicy Bypass -File "C:\Users\Dell Demo\Desktop\Demo\Loop Agency\tools\lock-masters.ps1" -Unlock   # to edit masters
# Locked: cabana\_master, cabana\raw, cabana\assets, brand.md, prompts.txt, AGENTS.md, tools\ (scripts), docs\, hermes\ (snapshot)
#         .git (history), README/.gitignore/launch .cmd files, and %USERPROFILE%\.hermes\skills\loop (live Cabana skills)
# Workflow to change anything: -Unlock -> edit -> copy skills to hermes\skills -> git commit -> lock again.
# Writable: cabana\work, cabana\social, cabana\cut (what Hermes produces; wiped by the reset).
# (This script lives in tools\ but stays runnable when locked: reading is never denied.)
param([switch]$Unlock)
$Loop = Split-Path $PSScriptRoot -Parent
$me = New-Object Security.Principal.NTAccount("$env:USERDOMAIN\$env:USERNAME")
$dirs  = @('cabana\_master', 'cabana\raw', 'cabana\assets', 'tools', 'docs', 'hermes', '.git' | ForEach-Object { Join-Path $Loop $_ }) +
         (Join-Path $env:USERPROFILE '.hermes\skills\loop')   # live Cabana skills: Hermes reads them, can't edit them
$files = 'cabana\brand.md', 'cabana\prompts.txt', 'cabana\AGENTS.md', 'README.md', '.gitignore',
         'Start Loop Demo.cmd', 'Reset Cabana.cmd', 'Reload Adobe Plugins.cmd' | ForEach-Object { Join-Path $Loop $_ }

# Exact write rights only. Generic "W" (icacls) also carries SYNCHRONIZE, which would block reading.
$R = [Security.AccessControl.FileSystemRights]
$deny = $R::WriteData -bor $R::AppendData -bor $R::WriteExtendedAttributes -bor $R::WriteAttributes -bor $R::Delete

foreach ($p in $dirs + $files) {
    if (-not (Test-Path $p)) { Write-Warning "missing $p"; continue }
    $isDir = (Get-Item $p).PSIsContainer
    $acl = Get-Acl $p
    $rights = if ($isDir) { $deny -bor $R::DeleteSubdirectoriesAndFiles } else { $deny }
    $inherit = if ($isDir) { 'ContainerInherit, ObjectInherit' } else { 'None' }
    $rule = New-Object Security.AccessControl.FileSystemAccessRule($me, $rights, $inherit, 'None', 'Deny')
    if ($Unlock) {
        $acl.RemoveAccessRuleAll((New-Object Security.AccessControl.FileSystemAccessRule($me, $rights, $inherit, 'None', 'Deny')))
        Set-Acl $p $acl
        Write-Host "unlocked $p"
    } else {
        $acl.AddAccessRule($rule)
        Set-Acl $p $acl
        Write-Host "locked   $p"
    }
}
