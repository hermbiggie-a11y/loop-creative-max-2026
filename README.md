# Loop Creative — Adobe MAX 2026 agentic agency demo

Hermes (on this laptop) drives real Photoshop and Premiere through adb-mcp and reports to the creative director on Telegram.

- **Start:** `Start Loop Demo.cmd` · **between runs:** `Reset Cabana.cmd` · **after an Adobe restart:** `Reload Adobe Plugins.cmd`
- Checklist + fallbacks: `docs/LAUNCH-CHECKLIST.md` · exact phone prompts: `cabana/prompts.txt`
- Alias: `C:\Loop` → this folder (Telegram attachment paths can't contain spaces)

## Layout
| Path | What |
|---|---|
| `cabana/_master`, `raw`, `assets`, `brand.md`, `prompts.txt`, `AGENTS.md` | client job sources — read-only for Hermes |
| `cabana/work`, `social`, `cut` | Hermes output (git-ignored, wiped by reset) |
| `tools/` | launch/reset/lock scripts, `social_resize.py`, `rough_cut.py`, bridge driver — read-only for Hermes |
| `hermes/skills/` | snapshot of the Hermes skills (live copy: `%USERPROFILE%\.hermes\skills\loop`, read-only for Hermes) |
| `hermes/config.yaml` | snapshot of the Hermes config (no secrets; keys live in `%USERPROFILE%\.hermes\.env`) |

## Not in this repo
- `tools/adb-mcp` — its own git repo (github.com/mikechambers/adb-mcp, `main` + local branch **loop-demo** with the Windows/PS27/PR26 patches).
- Faster-Whisper-XXL, the adb proxy exe, the Python venv, node_modules — reinstall per `docs/`.

## Editing locked files
`powershell -ExecutionPolicy Bypass -File tools\lock-masters.ps1 -Unlock` → edit → run again without `-Unlock`.
After changing a skill, copy it to both places (live + `hermes/skills`) and commit.
