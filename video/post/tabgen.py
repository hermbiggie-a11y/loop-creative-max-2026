"""From out/narr2-schedule.json: per-slide JSON for the Word/PDF (narration-by-slide-v2.json) and the doc tab markdown
(tab-head.json, tab-groups.json)."""
import json
from pathlib import Path

OUT = Path(__file__).parent / "out"
s = json.load(open(OUT / "narr2-schedule.json", encoding="utf-8"))
tl = json.load(open(OUT / "timeline.json", encoding="utf-8"))
d = []
for p in tl:
    ls = [x for x in s if p["start"] <= x["start"] < p["end"]]
    talk = sum(max(0, min(x["end"], p["end"]) - max(x["start"], p["start"])) for x in s)
    d.append({"name": p["name"], "start": p["start"], "end": p["end"], "show": round(p["end"] - p["start"], 1),
              "talk": round(talk, 1), "lines": [(round(x["start"], 1), round(x["end"] - x["start"], 1), x["text"]) for x in ls]})
json.dump(d, open(OUT / "narration-by-slide-v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

names = {"title": "Title card", "hook": "Cold open: Story resize", "built": "Built with AI", "diagram": "How it fits together",
         "rules": "Four rules", "login": "Telegram login (simulated)", "beat1-card": "Beat 1 card", "beat1": "Beat 1: the brief",
         "beat2-card": "Beat 2 card", "beat2-hero": "Beat 2: hero + Firefly", "ask": "Audience question",
         "beat2-six": "Beat 2: six sizes", "beat3-card": "Beat 3 card", "beat3": "Beat 3: rough cut", "spot-card": "Spot card",
         "spot": "The 30-second spot", "beat4-card": "Beat 4 card", "beat4": "Beat 4: offline",
         "spanish": "Missouri + Spanish line", "close": "Close + QR codes"}
notes = {"spot": "No narration: the spot plays with its own voice-over (your cloned read of the ad script).",
         "close": "The last 29 seconds are silent so you can take the first question with the QR codes still up."}
def m(t): x = int(round(t)); return f"{x // 60}:{x % 60:02d}"
def ln(x): return f"{round(x)} s" if x < 59.5 else m(x)
def clean(t):
    for a, b in (("Loop...", "Loop"), ("G P U", "GPU"), ("F F probe", "ffprobe"), ("F F mpeg", "ffmpeg"), ("S R T", "SRT"), ("N D A", "NDA"), ("|", "/")):
        t = t.replace(a, b)
    return t
groups = [("Open", ["title", "hook", "built", "diagram", "rules", "login"]), ("Beat 1", ["beat1-card", "beat1"]),
          ("Beat 2", ["beat2-card", "beat2-hero", "ask", "beat2-six"]), ("Beat 3", ["beat3-card", "beat3", "spot-card", "spot"]),
          ("Beat 4", ["beat4-card", "beat4", "spanish"]), ("Close", ["close"])]
by = {p["name"]: (k, p) for k, p in enumerate(d, 1)}
out = {}
for g, keys in groups:
    md = [f"## {g}"]
    for key in keys:
        k, p = by[key]
        md.append(f"### {k}. {names[key]} · {m(p['start'])}–{m(p['end'])}")
        extra = ", plus the 5-second Spanish clip" if key == "spanish" else ""
        md.append(f"Shown {ln(p['show'])} · talking {ln(p['talk'])} ({100 * p['talk'] / p['show']:.0f}%){extra}")
        if p["lines"]:
            t = ["| At | Length | Line |", "| --- | --- | --- |"] + [f"| {m(a)} | {ln(b)} | {clean(x)} |" for a, b, x in p["lines"]]
            if key == "spanish":
                t.insert(3, "| 19:01 | 5 s | *(Spanish clip, cloned voice)* Cabana Cold Brew. Sol en una lata. Ya en la Pequeña Habana. |")
            md.append("\n".join(t))
        if key in notes:
            md.append(notes[key])
    out[g] = "\n\n".join(md)
json.dump(out, open(OUT / "tab-groups.json", "w", encoding="utf-8"), ensure_ascii=False)
print("ok", sum(len(p["lines"]) for p in d), "lines")
