# Loop Creative — launch checklist (cold start → demo-ready in ~3 min)

Everything lives in `C:\Users\Dell Demo\Desktop\Demo\Loop Agency` (alias **C:\Loop**, no spaces — Telegram attachments need it).

## 1. Open the apps (in this order)
1. **Photoshop**, **Premiere Pro**, **UXP Developer Tools** (Start menu). Wait until all three are idle.
2. Premiere: if the **Premiere MCP Agent** panel isn't visible, `Window > UXP Plugins > Premiere MCP Agent` (only needed after a workspace reset).

## 2. Double-click `Start Loop Demo.cmd` (in the Loop Agency folder)
It starts the Adobe bridge (window titled *adb-mcp proxy* — leave it open), Ollama, reloads both MCP plugins
(they auto-connect), checks the Telegram gateway, and prints a health check. Expect:
```
OK  photoshop connected
OK  premiere connected
Ready. From your phone: ping
```

## 3. Reset the job — double-click `Reset Cabana.cmd`
Closes Photoshop docs + the Premiere project, wipes work/social/cut, restores working copies from `_master`, reopens the
fresh Premiere project. Then in Telegram send **/new**.

## 4. Screen layout
Left 2/3 Photoshop (beat 2) or Premiere (beat 3) · right 1/3 Telegram Desktop · Task Manager → Performance → GPU bottom-right.

## 5. Smoke test from the phone (before anyone watches)
`ping` → reply. Then: *"Open C:/Loop/cabana/work/hero.psd and tell me its size"* → 3200x1600.

## Between runs (90 s)
`Reset Cabana.cmd` → Telegram `/new` → re-plug ethernet → `/model` back to the online model if you switched.

## If something breaks (never debug on stage)
| You see | 10-second move |
|---|---|
| "Could not connect to photoshop/premiere" | Hermes reloads the plugins itself once. If not: double-click `Reload Adobe Plugins.cmd`. |
| Premiere crashes | "Premiere's doing a Premiere" → play `Golden\beat3-golden.mp4`, carry on with beat 4. Relaunch later; panel reconnects by itself after `Reload Adobe Plugins.cmd`. |
| Firefly / Generative Fill errors | Hermes falls back to `hero-extended.psd` (already extended) — say Firefly ran in rehearsal. |
| Internet down | Phone hotspot for Telegram; `/model` → local Qwen3.8 27B. Beats 1, 2 (minus Fill), 3, 4 all run. |
| Telegram dead | Windows Terminal: `hermes` (same agent, same skills). |
| Hermes off-script | `/stop`, then resend the exact line from `cabana\prompts.txt`. |

## Timings measured in rehearsal (online model, Oct 13)
Beat 1 brief 24 s · gate 15 s · Beat 2 hero + Fill + options 86 s · six sizes ~3 min (Story alone 45 s) ·
Beat 3 first cut 63 s · notes → v2 48 s · go → export + captions + preview 42 s · Beat 4 (local Qwen, cold) 152 s.

## Read-only
`_master`, `raw`, `assets`, `brand.md`, `prompts.txt`, `AGENTS.md`, `tools`, `docs` are locked (Windows deny-write for this
user — Hermes runs as this user). To edit masters: `powershell -ExecutionPolicy Bypass -File C:\Loop\tools\lock-masters.ps1 -Unlock`,
then run it again without `-Unlock` to re-lock.
