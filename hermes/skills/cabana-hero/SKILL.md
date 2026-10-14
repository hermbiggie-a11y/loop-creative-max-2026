---
name: cabana-hero
description: "Loop Creative beat 2a: open the Cabana hero in Photoshop, extend the beach with Generative Fill, comp the headline, send three headline options."
version: 1.0.1
author: Loop Creative
platforms: [windows]
metadata:
  hermes:
    tags: [photoshop, cabana, loop, firefly]
    related_skills: [cabana-social-resize]
---

# Cabana hero (Generative Fill + headline options)

## When to Use
User asks to open / extend / work on the Cabana hero, or asks for headline options. Runs after the brief
(direction is in memory and in C:/Loop/cabana/work/brief.md).

## Procedure (Photoshop MCP tools, in this order - the audience watches the layers appear)
1. `open_photoshop_file` C:/Loop/cabana/work/hero.psd (3200x1600; beach layer is 2400 wide, centred, sand-coloured bands left and right).
2. `get_layers` -> note the id of the layer named **beach**.
3. `select_rectangle` on the beach layer, bounds {top:0,left:0,bottom:1600,right:440}; then `generative_fill`
   layer_name "extend left", prompt "continue the sunny Miami beach: white sand, turquoise ocean and clear blue sky, matching light and perspective", content_type "photo".
4. Same for the right band: bounds {top:0,left:2760,bottom:1600,right:3200}, layer_name "extend right".
5. Clear the selection (select_rectangle with all-zero bounds on the beach layer).
6. Write three headline options that follow the brief + brand.md voice (2-5 words, Bebas Neue, no "fuel/grind/hustle").
7. `create_single_line_text_layer` with option 1 as a working comp: font BebasNeue-Regular, size 190, color Cabana Coral {255,111,89},
   position {x:1080, y:210} (baseline; keeps the headline above the can top at y~240). Name it "headline".
8. `save_document_as` C:/Loop/cabana/work/hero.psd (PSD) and C:/Loop/cabana/work/hero-preview.jpg (JPG).
9. Reply (short): one line on what changed, the three options numbered 1-3, "Which number?", and on its own line:
   MEDIA:C:/Loop/cabana/work/hero-preview.jpg

## Gate
Stop after step 9. Never pick the headline yourself. When the user answers with a number, `edit_text_layer` the
headline layer to that option, save hero.psd + hero-preview.jpg again, remember the approved headline (memory), then use
**cabana-social-resize**.

## Pitfalls
- If generative_fill errors (Firefly down): open C:/Loop/cabana/work/hero-extended.psd instead (already extended) and carry on from step 6. Say so in one line.
- Use C:/Loop/... paths (no spaces) - MEDIA: paths must not contain spaces.
- Never save into _master.

## Verification
hero-preview.jpg exists and `get_document_image` shows the beach filling the full width with no sand bands.
