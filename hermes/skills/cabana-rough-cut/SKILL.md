---
name: cabana-rough-cut
description: "Loop Creative beat 3: inventory + transcribe + tag the raw footage, build the 30-second Cabana spot in Premiere, send review frames, apply editor notes, export with captions and a captioned preview."
version: 1.0.0
author: Loop Creative
platforms: [windows]
metadata:
  hermes:
    tags: [premiere, cabana, loop, video, captions, whisper]
    related_skills: [cabana-hero, cabana-social-resize]
---

# Cabana rough cut

## When to Use
"Cut the 30-second spot", "rough cut", "edit the footage", editor notes on the cut, or "go" after review frames.

## Footage (C:/Loop/cabana/raw, 4 s each, 1080p30)
clip01-pour, clip02-ice, clip03-beach, clip04-can-sand, clip05-cooler, clip06-waves, clip07-ocean-drive,
clip08-cheers, clip09-sunset, clip10-hero-can; voice-over vo-30.wav (28.4 s incl. silence pad; Logan's voice cloned locally with Chatterbox, script in vo-script.txt).
Default shot-list order (brief): pour, ice, beach, can-sand, cooler, waves, ocean-drive, cheers, hero-can (9 shots).

## Procedure - first cut
1. Narrate the chain in one line, then do it:
   - `ffprobe` inventory of raw/*.mp4 (duration, resolution) - one terminal call with a loop.
   - Transcribe the VO: `faster-whisper-xxl.exe C:/Loop/cabana/raw/vo-30.wav --model turbo --language en --compute_type float32 --output_format srt --output_dir C:/Loop/cabana/work`
   - Tag shots: `vision_analyze` 3-4 stills from C:/Loop/cabana/assets/stills/*.jpg (pour, ice, beach, can) - one short tag each.
2. Build the cut in Premiere (one command; the timeline fills in on screen):
   `powershell -NoProfile -File C:/Loop/tools/py.ps1 rough_cut.py frames --name v1 --order clip01-pour,clip02-ice,clip03-beach,clip04-can-sand,clip05-cooler,clip06-waves,clip07-ocean-drive,clip08-cheers,clip10-hero-can --dissolve 0.5`
   (opens work/cabana.prproj, sequence "spot-v1", trims every shot so the spot is 30 s, lays the VO, cross dissolves, frame grabs)
3. Reply: one line ("30 s, 9 shots, 0.5 s dissolves"), then the four frames, one per line:
   MEDIA:C:/Loop/cabana/cut/frames/v1-00s.jpg  ... -10s ... -20s ... -29s
   Ask for notes.

## Gate 1 - editor notes
Apply notes by changing the order / dropping shots / dissolve length and rebuild with the next version name:
- "open on X" -> X first; "drop the beach shot" -> remove clip03-beach; "shorter dissolves" -> --dissolve 0.25; "longer" -> 1.0.
`... rough_cut.py frames --name v2 --order <new order> --dissolve <d>` then send the four v2 frames and ask "go?".

## Gate 2 - "go"
Only on an explicit go: `... rough_cut.py export --name <approved version>` (exports cabana/cut/cabana-spot.mp4 with the
H.264 1080p preset, writes cabana/cut/captions.srt, burns cabana/cut/preview.mp4). Reply with one line + `MEDIA:C:/Loop/cabana/cut/preview.mp4`.
Mention captions.srt is next to the MP4 for the editor (drag into Premiere for a caption track).

## Pitfalls
- Never export before "go". Never call create_project. Never write to _master.
- If rough_cut prints FAILED with "Could not connect to premiere": run start-loop.ps1 -ReloadOnly once, retry once.
- Sequence names must be new per version (v1, v2, v3...).
- MEDIA: paths must use C:/Loop/... (no spaces).

## Verification
Frames exist for the version; after export, cabana-spot.mp4 is ~30 s (ffprobe) and preview.mp4 exists.
