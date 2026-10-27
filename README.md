# Loop Creative — an agentic agency demo (Adobe MAX 2026)

Three people, one agent, one workstation. **Hermes**, an open-source agent running on a Dell Pro Max 16 Plus
(NVIDIA RTX PRO 5000 Blackwell, 24 GB), drives **real Photoshop and Premiere Pro** through the open-source
[adb-mcp](https://github.com/mikechambers/adb-mcp) bridge and reports to the creative director on Telegram. A human
makes every creative call; the agent does the clicking.

Built by Logan Lawler (AI strategy, Dell Pro Precision) — and built almost entirely with AI.

**Watch it first:** the 20-minute walkthrough videos (narrated and silent) and the narration script are under
[Releases](../../releases).

## The four beats
| Beat | What happens | Human gate |
|---|---|---|
| 1 · Brief | One message → `brief.md` with two directions and a shot list | "A or B?" |
| 2 · Hero + six sizes | Firefly Generative Fill extends the hero in Photoshop; six social sizes built and exported | Pick a headline |
| 3 · Rough cut | ffprobe → Whisper → vision tags → Premiere sequence → export, captions, captioned preview | Editor's notes, then "go" |
| 4 · Offline | Wi-Fi off; a local open-weight model (gpt-oss 20B on the GPU) makes the Spanish post | — |

## What's in this repo
| Path | What |
|---|---|
| `cabana/` | The fictional client job: brand sheet, Firefly-generated assets, footage, master PSDs and Premiere project, exact demo prompts (`prompts.txt`), agent rules (`AGENTS.md`) |
| `hermes/skills/` | The four Hermes skills (`cabana-brief`, `cabana-hero`, `cabana-social-resize`, `cabana-rough-cut`) |
| `hermes/config.yaml` | Hermes config snapshot — no secrets (keys live in `%USERPROFILE%\.hermes\.env`) |
| `tools/` | Launch / reset scripts, the deterministic helpers the skills call (`social_resize.py`, `rough_cut.py`), the bridge driver |
| `patches/adb-mcp-loop-demo.patch` | Our fixes to adb-mcp for Windows / Photoshop 27 / Premiere 26 (apply on top of upstream `main`) |
| `docs/` | Launch checklist with fallbacks |
| `video/` | How the backup video was made: recording rig (simulated Telegram panel fed by Hermes' live output, ffmpeg capture), cards, the editor, voice-clone narration pipeline, Word/PDF script generator |

## Setup (Windows 11)
1. Install Photoshop, Premiere Pro and UXP Developer Tools (Creative Cloud), Python 3.11+, Node.js, ffmpeg.
2. Install Hermes Agent natively on Windows and point `terminal.cwd` at `cabana/` (see `hermes/config.yaml`).
   Put your model keys (e.g. OpenRouter) and Telegram bot token in `%USERPROFILE%\.hermes\.env`.
3. Clone adb-mcp, apply `patches/adb-mcp-loop-demo.patch` (`git am`), and place it at `tools/adb-mcp`.
   Run its proxy from source (`node proxy.js`); load the Photoshop and Premiere UXP plugins.
4. Download Faster-Whisper-XXL into `tools/Faster-Whisper-XXL` and create `tools/.venv`.
5. Make the space-free alias the scripts expect: `mklink /J C:\Loop "<this folder>"`.
6. Copy the skills to `%USERPROFILE%\.hermes\skills\loop\`.
7. Start: `Start Loop Demo.cmd` · between runs: `Reset Cabana.cmd` · after an Adobe restart: `Reload Adobe Plugins.cmd`.
   Full checklist and fallbacks: `docs/LAUNCH-CHECKLIST.md`.

Notes from the build: the adb proxy must run from source (the prebuilt exe rejects Premiere's polling); MCP servers
need `mcp[cli]<2`; Premiere's API wants backslash paths; Windows Smart App Control can block llama.cpp DLLs — the
offline beat in the video uses gpt-oss 20B on Ollama instead.

## Credits
- [Hermes Agent](https://github.com/NousResearch) (Nous Research) — the agent.
- [adb-mcp](https://github.com/mikechambers/adb-mcp) by Mike Chambers (MIT) — the Photoshop/Premiere bridge. Not an
  official Adobe product.
- Claude (Anthropic) via OpenRouter — the online model; Claude Code wrote the scripts, skills and the video tooling.
- gpt-oss 20B (OpenAI, open weights) on Ollama — the offline model.
- Adobe Firefly — generative fill and the Cabana stills.
- Faster-Whisper — local transcription and captions.
- Chatterbox (Resemble AI, MIT) — the narration voice clone (the presenter's own voice, with his consent; the clone
  source recordings are not published).

Cabana Cold Brew is a fictional brand.
