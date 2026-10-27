# Move a window to an exact rectangle and bring it to the front (for the recording layout).
#   winpos.ps1 -Proc Photoshop|"Adobe Premiere Pro"|notepad|explorer|msedge-loopchat -X 0 -Y 0 -W 1280 -H 1080
param([string]$Proc, [int]$X, [int]$Y, [int]$W, [int]$H, [string]$Title, [switch]$Close, [switch]$NoCaption, [switch]$ZOnly)
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public class LoopWin {
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr p);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int w, int hh, uint f);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool f);
  [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
  [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, UIntPtr e);
  [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr v);
  [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr h, int i);
  [DllImport("user32.dll")] public static extern int SetWindowLong(IntPtr h, int i, int v);
  public static string Title(IntPtr h) { var s = new StringBuilder(512); GetWindowText(h, s, 512); return s.ToString(); }
}
"@
[void][LoopWin]::SetProcessDpiAwarenessContext([IntPtr](-4))   # physical pixels, ignore 125% scaling
$wins = New-Object System.Collections.ArrayList
[LoopWin]::EnumWindows({ param($h, $p) if ([LoopWin]::IsWindowVisible($h)) { [void]$wins.Add($h) }; $true }, [IntPtr]::Zero) | Out-Null

function PidOf($h) { $p = 0; [void][LoopWin]::GetWindowThreadProcessId($h, [ref]$p); $p }
$target = $null
if ($Title) { $target = $wins | Where-Object { [LoopWin]::Title($_) -like $Title } | Select-Object -First 1 }
else { switch ($Proc) {
  'msedge-loopchat' { $target = $wins | Where-Object { [LoopWin]::Title($_) -like 'Loop · Hermes*' } | Select-Object -First 1 }
  'explorer'        { $target = $wins | Where-Object { [LoopWin]::Title($_) -match '^social' } | Select-Object -First 1 }
  default {
    $ids = @(Get-Process -Name $Proc -ErrorAction SilentlyContinue | ForEach-Object Id)
    $target = $wins | Where-Object { $ids -contains (PidOf $_) -and [LoopWin]::Title($_) } |
      Sort-Object { -([LoopWin]::Title($_)).Length } | Select-Object -First 1
  }
} }
if (-not $target) { Write-Host "no window for $Proc$Title"; exit 1 }
if ($ZOnly) {   # raise above every normal window without needing focus: topmost, then back to normal
  [void][LoopWin]::SetWindowPos($target, [IntPtr](-1), 0, 0, 0, 0, 0x0013)
  [void][LoopWin]::SetWindowPos($target, [IntPtr](-2), 0, 0, 0, 0, 0x0013)
  exit 0
}
if ($Close) { [void][LoopWin]::PostMessage($target, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero); Write-Host "closed"; exit 0 }
[void][LoopWin]::ShowWindow($target, 9)            # restore (un-maximize) so the rect sticks
if ($NoCaption) {   # drop title bar + resize border so the page fills the exact rect
  $st = [LoopWin]::GetWindowLong($target, -16); [void][LoopWin]::SetWindowLong($target, -16, ($st -band (-bnot 0x00C40000)))
}
[void][LoopWin]::SetWindowPos($target, [IntPtr]::Zero, $X, $Y, $W, $H, 0x0060)   # SHOWWINDOW|FRAMECHANGED
# foreground: tap Alt so Windows lets a background process change focus
[LoopWin]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero); [LoopWin]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
[void][LoopWin]::SetForegroundWindow($target)
Write-Host "placed $Proc '$([LoopWin]::Title($target))' at $X,$Y ${W}x$H"
