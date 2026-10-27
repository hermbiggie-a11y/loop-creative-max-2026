"""The edit: which takes, what's on screen when, and the captions that cue Logan. Times are seconds in each recording
(see rig/runs/<take>/events.jsonl). Captions are written as stage cues, not as a script: short, present tense."""
from pathlib import Path
from edit import Rec, HERE

RUNS = HERE.parent / "rig" / "runs"
ASSETS = HERE / "assets"
VOICE = HERE.parent / "voice" / "takes"

def cap(k, x, kind=None):
    p = {"k": k, "cap": x}
    if kind:
        p["kind"] = kind
    return p

def tag(text):
    return {"btag": text}

def grid(title, key, files, cols=2, cls="", heights=None):
    p = {"grid": "|".join(Path(f).as_uri() for f in files), "gx": title, "gk": key, "gcols": cols, "gcls": cls}
    if heights:
        p["gh"] = "|".join(str(h) for h in heights)
    return p

def PLAN():
    login = Rec("login", RUNS / "20261024-141110-login")
    hook = Rec("hook", RUNS / "20261024-141357-hook")
    b1 = Rec("beat1", RUNS / "20261024-141535-beat1")
    b2 = Rec("beat2", RUNS / "20261024-141653-beat2")
    b3 = Rec("beat3", RUNS / "20261024-142209-beat3")
    b4 = Rec("beat4", RUNS / "20261024-172423-beat4")
    frames = ASSETS / "cut" / "frames"
    six = [ASSETS / "social" / f for f in ("1080x1920.png", "1080x1350.png", "1080x1080.png", "1600x900.png", "1200x628.png", "1500x500.png")]
    six_h = [560, 500, 420, 330, 290, 210]

    return [
        {"name": "title", "type": "card", "card": "title", "seconds": 12},

        {"name": "hook", "type": "clip", "rec": hook, "spans": [(1.0, 76.0, 1)], "overlays": [
            (1.0, 76.0, tag("<b>COLD OPEN</b> · 30-second version")),
            (3.0, 14.0, cap("Logan texts the agent", "“Resize the Cabana hero for Instagram Story.”")),
            (15.0, 30.0, cap("Going into Hermes", "It loads its resize skill, then drives real Photoshop")),
            (30.0, 70.0, cap("Real Photoshop, real layers", "New 1080×1920 doc · places the hero · re-lays the headline · exports")),
            (70.6, 76.0, cap("Back on the phone", "I made the creative call. It did the clicking.")),
        ]},

        {"name": "built", "type": "card", "card": "built", "seconds": 45},
        {"name": "diagram", "type": "card", "card": "diagram", "seconds": 45},
        {"name": "rules", "type": "card", "card": "rules", "seconds": 30},

        {"name": "login", "type": "clip", "rec": login, "spans": [(0.5, 16.0, 1)], "overlays": [
            (0.5, 9.0, cap("How you connect", "Telegram on your phone → a bot → Hermes on this laptop")),
            (9.0, 16.0, cap("Simulated for this recording", "Live, I'll show you the real thing")),
        ]},

        # ---------------------------------------------------------------- beat 1
        {"name": "beat1-card", "type": "card", "card": "beat1", "seconds": 8},
        {"name": "beat1", "type": "clip", "rec": b1, "spans": [(1.0, 77.5, 1)], "overlays": [
            (1.0, 77.5, tag("<b>BEAT 1</b> · Brief")),
            (3.0, 13.0, cap("The brief, in one message", "Client · product · launch date · deliverables")),
            (13.0, 34.0, cap("Going into Hermes", "Reads the brand sheet, writes brief.md: two directions, a shot list")),
            (34.0, 46.0, cap("Gate · a human decides", "It asks “A or B?” instead of guessing", "gate")),
            (46.0, 65.0, cap("Logan picks", "“B, and make the headline shorter.” Saved to memory", "gate")),
            (65.0, 77.5, cap("brief.md, updated", "Direction B is locked in for every beat that follows")),
        ]},

        # ---------------------------------------------------------------- beat 2
        {"name": "beat2-card", "type": "card", "card": "beat2", "seconds": 8},
        {"name": "beat2-hero", "type": "clip", "rec": b2, "spans": [(1.0, 99.5, 1), (99.5, 99.6, 0.02)], "overlays": [
            (1.0, 99.6, tag("<b>BEAT 2</b> · Photoshop + Firefly")),
            (3.0, 24.0, cap("Going into Photoshop", "Opens the real hero.psd: layers, not a mockup")),
            (24.0, 74.0, cap("Firefly, inside Photoshop", "Generative Fill extends the beach, called by the agent")),
            (74.0, 93.8, cap("Headline from the brief", "Brand font, brand coral, saved as a real PSD")),
            (93.8, 99.6, cap("Gate · pick a headline", "Three options on the phone. Logan picks #2", "gate")),
        ]},
        {"name": "ask", "type": "card", "card": "ask", "seconds": 15},
        {"name": "beat2-six", "type": "clip", "rec": b2, "spans": [(99.5, 314.0, 1), (314.0, 314.1, 0.01)],
         "timer": (100.2, 309.1), "overlays": [
            (99.5, 314.1, tag("<b>BEAT 2</b> · Six social sizes")),
            (99.5, 123.0, cap("Picked: BREW LOUD", "It edits the text layer and remembers the choice", "gate")),
            (123.0, 302.0, cap("Six sizes, one skill", "1080×1080 · 1080×1920 · 1080×1350 · 1200×628 · 1600×900 · 1500×500")),
            (302.0, 309.1, cap("Checks its own work", "Looks at the square post before it reports back")),
            (309.1, 314.1, grid("All six, exported, with the headline re-laid for each", "Six sizes · about 3 minutes", six,
                                cls="full six", heights=six_h)),
        ]},

        # ---------------------------------------------------------------- beat 3
        {"name": "beat3-card", "type": "card", "card": "beat3", "seconds": 8},
        {"name": "beat3", "type": "clip", "rec": b3, "spans": [(1.0, 84.3, 1), (84.3, 84.4, 0.02), (84.4, 135.6, 1),
                                                                (135.6, 135.7, 0.025), (135.7, 186.0, 1)], "overlays": [
            (1.0, 186.0, tag("<b>BEAT 3</b> · Premiere Pro")),
            (3.0, 20.0, cap("The ask", "“Cut the 30-second spot in shot-list order. Send me frames.”")),
            (20.0, 26.0, cap("Going into Hermes", "Inventories the raw footage with ffprobe")),
            (26.0, 37.0, cap("Captions, offline", "Whisper transcribes the voice-over on this GPU")),
            (37.0, 45.0, cap("Vision tags", "Looks at stills: pour · ice · beach · can")),
            (45.0, 84.3, cap("Premiere timeline builds", "Imports · sequences in shot-list order · trims to 30 s · dissolves")),
            (84.3, 87.0, grid("Frames sent to Logan's phone: cut v1", "0 · 10 · 20 · 29 seconds",
                              [frames / f"v1-{s}s.jpg" for s in ("00", "10", "20", "29")])),
            (87.0, 100.0, cap("Editor's notes", "“Open on the pour, drop the beach shot, shorter dissolves.”", "gate")),
            (100.0, 135.6, cap("Notes honored", "v2: beach shot out, 0.25 s dissolves, re-timed to 30 s")),
            (135.6, 138.5, grid("Frames sent to Logan's phone: cut v2", "Beach shot gone",
                                [frames / f"v2-{s}s.jpg" for s in ("00", "10", "20", "29")])),
            (138.5, 147.0, cap("Approved", "“go”", "gate")),
            (147.0, 177.5, cap("Export", "H.264 1080p · captions.srt · captioned preview via ffmpeg")),
            (177.5, 186.0, cap("Preview lands on the phone", "Next: the spot itself")),
        ]},
        {"name": "spot-card", "type": "card", "card": "spot", "seconds": 7},
        {"name": "spot", "type": "media", "path": ASSETS / "cut" / "preview.mp4"},

        # ---------------------------------------------------------------- beat 4
        {"name": "beat4-card", "type": "card", "card": "beat4", "seconds": 8},
        {"name": "beat4", "type": "clip", "rec": b4, "spans": [(36.0, 225.0, 1), (575.0, 616.0, 1)], "overlays": [
            (36.0, 225.0, tag("<b>BEAT 4</b> · Offline")),
            (36.0, 50.0, cap("Wi-Fi off", "Watch the badge: Offline. Nothing leaves this laptop.", "local")),
            (50.0, 57.0, cap("Brain swap", "gpt-oss 20B, running on the RTX PRO 5000", "local")),
            (57.0, 143.0, cap("Same job, local model", "Spanish square post, built in real Photoshop with the network off", "local")),
            (143.0, 147.0, cap("Little Havana", "CAFÉ FUERTE, made offline", "local")),
            (147.0, 225.0, cap("“What did you learn today?”", "It keeps notes and skills it reuses on the next job", "local")),
            (575.0, 616.0, tag("<b>BEAT 4</b> · Back online")),
            (575.0, 583.0, cap("Back online", "Claude again, for the overnight job")),
            (583.0, 616.0, cap("“Every morning at 8, send me the project status.”", "A scheduled job: the agency runs while the humans sleep")),
        ]},
        {"name": "spanish", "type": "card", "card": "spanish", "seconds": 16, "audio": VOICE / "es-take1.wav", "audio_delay": 6.0},

        {"name": "close", "type": "card", "card": "close", "seconds": 75},
    ]
