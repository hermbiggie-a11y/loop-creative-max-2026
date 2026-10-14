---
name: cabana-brief
description: "Loop Creative beat 1: turn a client brief (text or voice note) into brief.md with two creative directions, then stop and ask 'A or B?'."
version: 1.0.0
author: Loop Creative
platforms: [windows]
metadata:
  hermes:
    tags: [cabana, loop, brief]
    related_skills: [cabana-hero]
---

# Cabana brief

## When to Use
A new client / campaign brief arrives ("New client: ...", "write the brief"), by text or voice note.

## Procedure
1. Read C:/Loop/cabana/brand.md.
2. Write C:/Loop/cabana/work/brief.md (one page, markdown):
   - Client, product, launch (if the year is ambiguous, write "June 1, 2027 (to confirm)" - do NOT ask about it).
   - Deliverables checklist: hero key visual; six social sizes (1080x1080, 1080x1920, 1080x1350, 1200x628, 1600x900, 1500x500); 30-second spot from raw footage; captions.
   - **Direction A** and **Direction B**: a name, one line of mood, palette emphasis, headline style - genuinely different.
   - Shot list for the spot: pour, ice, beach, can in sand, cooler grab, waves, Ocean Drive, cheers, hero can.
   - The three gates (direction, headline, edit notes + go).
3. Reply in <= 6 short lines: what's in the brief, Direction A in one line, Direction B in one line, then exactly: **A or B?**

## Gate
STOP after the question. Do not open Photoshop, do not propose headlines, do not start the hero.

When the user answers ("B, and make the headline shorter"): update brief.md (chosen direction, the note, e.g. headlines 2-3 words),
save the choice to memory, reply in 2 lines confirming the choice and the note, and STOP again - the hero starts only when the
user asks for it.

## Pitfalls
- One question only: "A or B?". No extra questions (year, end card, budget) - note them in brief.md under "Open items" instead.
- Never write outside C:/Loop/cabana/work.
