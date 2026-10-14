---
name: cabana-social-resize
description: "Loop Creative beat 2b: build the Cabana social sizes live in Photoshop from the approved headline and export PNGs (also the 30-second 'Instagram Story' request)."
version: 1.1.0
author: Loop Creative
platforms: [windows]
metadata:
  hermes:
    tags: [photoshop, cabana, loop, social, resize]
    related_skills: [cabana-hero]
---

# Cabana social resize

## When to Use
- After the user approves a headline (a number reply to cabana-hero).
- "Resize the Cabana hero for Instagram Story / Reel / feed / LinkedIn / X banner ..." (any subset of sizes).

## Sizes
| Name | Size |
|---|---|
| Instagram square | 1080x1080 |
| Instagram Story / Reel / TikTok | 1080x1920 |
| Instagram portrait | 1080x1350 |
| Facebook / LinkedIn link | 1200x628 |
| X / web landscape | 1600x900 |
| X header banner | 1500x500 |

## Procedure
1. Headline = the one the user approved (memory). If none is approved yet, use "ICE, MIAMI." and say so.
2. Run ONE terminal command (it drives Photoshop through the bridge; each size is built as a real document:
   hero smart object cover-scaled, Generative Fill sky for 9:16, logo placed, headline re-laid - never scaled):
   `powershell -NoProfile -File C:/Loop/tools/py.ps1 social_resize.py "<HEADLINE>" [WxH ...]`
   - all six: no size arguments (~3 min). Story only: `1080x1920` (~45 s).
   - output lines look like `1080x1920 ok (45s) -> .../cabana/social/1080x1920.png`; `done: N sizes in Ts`.
3. If a line says FAILED: run `powershell -NoProfile -File C:/Loop/tools/start-loop.ps1 -ReloadOnly`, wait 5 s, rerun only the failed sizes once.
4. Reply (short): how many sizes and the total time from the `done:` line, then attach the files, one per line:
   MEDIA:C:/Loop/cabana/social/1080x1920.png  (Story first when it was asked for; for all six attach 1080x1080 and 1080x1920 and list the rest)

## Spanish / language variant (beat 4, works offline on the local model)
"Make a Spanish version of the square post (Little Havana)": translate the approved headline into short, natural Miami
Spanish in the same 2-3 word style (e.g. ICED MIAMI -> MIAMI HELADO, MIAMI, COLD -> MIAMI, FRÍO), then:
`powershell -NoProfile -File C:/Loop/tools/py.ps1 social_resize.py "<SPANISH HEADLINE>" 1080x1080 --suffix es`
Reply with the Spanish line + `MEDIA:C:/Loop/cabana/social/1080x1080-es.png`. No Firefly is needed, so this runs with the cable out.

## Pitfalls
- Do NOT resize with ffmpeg or Python imaging - the point is that Photoshop does it, visibly.
- Do not call save_document_image_as_png (broken here). The script already saves PNGs.
- MEDIA: paths must use C:/Loop/... (no spaces).

## Verification
The PNGs exist in C:/Loop/cabana/social/ and `done:` reports every requested size. Optionally `vision_analyze` one PNG to confirm the headline is readable and uncropped.
