# Hermes command-STT adapter: transcribe a voice note with Faster-Whisper-XXL and write plain text
# to the path Hermes expects. float32 is required on the RTX PRO 5000 Blackwell (float16 cuBLAS fails).
param([Parameter(Mandatory)] [string]$InputPath, [Parameter(Mandatory)] [string]$OutputPath, [string]$Language = 'en')

$ErrorActionPreference = 'Stop'
$exe = Join-Path $PSScriptRoot 'Faster-Whisper-XXL\faster-whisper-xxl.exe'
$work = Join-Path ([IO.Path]::GetTempPath()) ("loop-stt-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $work | Out-Null
try {
    & $exe $InputPath --model turbo --language $Language --compute_type float32 `
        --output_format txt --output_dir $work --beep_off *> $null
    $txt = Get-ChildItem $work -Filter *.txt | Select-Object -First 1
    if (-not $txt) { throw "faster-whisper-xxl produced no transcript (exit $LASTEXITCODE)" }
    # XXL's txt output prefixes each segment with "[mm:ss.xxx --> mm:ss.xxx]"; Hermes wants plain text
    $lines = Get-Content $txt.FullName -Encoding UTF8 | ForEach-Object { ($_ -replace '^\s*\[[^\]]*\]\s*', '').Trim() }
    $text = (($lines | Where-Object { $_ }) -join ' ').Trim()
    [IO.File]::WriteAllText($OutputPath, $text, (New-Object Text.UTF8Encoding $false))
}
finally { Remove-Item $work -Recurse -Force -ErrorAction SilentlyContinue }
