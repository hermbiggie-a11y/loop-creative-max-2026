"""Assemble the Loop backup video from the recorded segments (rig/runs/*) and the cards.

Each recorded segment comes with events.jsonl (seconds from the first recorded frame). The edit is described in
plan.py as a list of pieces: cards, clips (spans of a recording at chosen speeds, with caption overlays anchored to
events), and media inserts (the finished spot with its audio). Every piece is rendered to a uniform 1920x1080/30 fps
H.264 + AAC file, then the pieces are joined.

    python edit.py            # render everything, write out/loop-backup.mp4 + out/timeline.json
    python edit.py --only 3   # re-render one piece (index) and re-join
"""
import argparse, json, subprocess
from pathlib import Path
from render import overlay

HERE = Path(__file__).parent
RUNS = HERE.parent / "rig" / "runs"
OUT = HERE / "out"; PIECES = OUT / "pieces"
FPS = 30
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart"]

def ff(args):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip())

# ------------------------------------------------------------------ recordings + events
class Rec:
    def __init__(self, seg, pick=None):
        dirs = sorted(d for d in RUNS.glob(f"*-{seg}") if (d / "screen.mkv").exists() and
                      any('"done"' in l for l in (d / "events.jsonl").open(encoding="utf-8")))
        self.dir = Path(pick) if pick else dirs[-1]
        self.video = self.dir / "screen.mkv"
        self.ev = [json.loads(l) for l in (self.dir / "events.jsonl").open(encoding="utf-8")]
        self.length = dur(self.video)

    def t(self, kind, n=0, **match):
        """Time of the n-th event of a kind (optionally matching fields, substring match on strings)."""
        hits = [e for e in self.ev if e["kind"] == kind and all(
            (str(v).lower() in str(e.get(k, "")).lower()) for k, v in match.items())]
        return hits[n]["t"]

    def turns(self):
        """(start, reply) times of every Hermes turn."""
        s = [e["t"] for e in self.ev if e["kind"] == "hermes_start"]
        r = [e["t"] for e in self.ev if e["kind"] == "hermes_reply"]
        return list(zip(s, r))

# ------------------------------------------------------------------ pieces
def render_card(name, seconds, audio=None, audio_delay=0.0, out=None):
    img = HERE / "cards" / f"{name}.png"
    fade = f"fade=t=in:st=0:d=0.35,fade=t=out:st={seconds - 0.35:.2f}:d=0.35"
    args = ["-loop", "1", "-framerate", str(FPS), "-t", f"{seconds}", "-i", str(img)]
    if audio:
        args += ["-i", str(audio)]
        af = f"[1:a]adelay={int(audio_delay * 1000)}:all=1,apad,atrim=0:{seconds},aformat=sample_rates=48000:channel_layouts=stereo[a]"
    else:
        args += ["-f", "lavfi", "-t", f"{seconds}", "-i", "anullsrc=r=48000:cl=stereo"]
        af = "[1:a]anull[a]"
    ff([*args, "-filter_complex", f"[0:v]format=yuv420p,{fade}[v];{af}", "-map", "[v]", "-map", "[a]",
        "-t", f"{seconds}", *ENC, str(out)])

def render_media(path, out, title_png=None, pad_color="0x0b0f14"):
    """Full-screen insert of a finished video (keeps its audio)."""
    d = dur(path)
    ff(["-i", str(path), "-filter_complex",
        f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:{pad_color},"
        f"fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.4,fade=t=out:st={d - 0.4:.2f}:d=0.4[v];"
        f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo[a]", "-map", "[v]", "-map", "[a]", *ENC, str(out)])

def mapper(spans):
    """Source time -> output time for a list of (src_start, src_end, speed) spans."""
    def to_out(t):
        acc = 0.0
        for a, b, s in spans:
            if t <= a:
                return acc
            if t <= b:
                return acc + (t - a) / s
            acc += (b - a) / s
        return acc
    return to_out

def stopwatch_frames(seconds):
    """PNG per second: a stopwatch box bottom-right of the app area."""
    from PIL import Image, ImageDraw, ImageFont
    d = HERE / "ov" / "watch"; d.mkdir(parents=True, exist_ok=True)
    big = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 78); small = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 19)
    for i in range(int(seconds) + 2):
        f = d / f"w{i:04d}.png"
        if f.exists():
            continue
        im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
        x1, y1 = 1240, 1036; x0, y0 = x1 - 270, y1 - 150
        g.rounded_rectangle((x0, y0, x1, y1), 16, fill=(11, 15, 20, 235), outline=(255, 200, 69, 255), width=3)
        g.text((x1 - 24, y0 + 16), "STOPWATCH", font=small, fill=(255, 200, 69, 255), anchor="ra")
        g.text((x1 - 24, y1 - 18), f"{i // 60}:{i % 60:02d}", font=big, fill=(244, 241, 234, 255), anchor="rd")
        im.save(f)
    return d / "w%04d.png"

def render_clip(rec, spans, overlays, out, timer=None):
    """spans: [(src_start, src_end, speed)], overlays: [(src_t0, src_t1, params)] in source time.
    A span with speed > 1 gets the 'SPED UP n×' badge automatically. timer: (src_start, src_stop) stopwatch."""
    to_out = mapper(spans)
    total = to_out(spans[-1][1] + 1e9)
    parts, labels = [], []
    for i, (a, b, s) in enumerate(spans):
        parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=(PTS-STARTPTS)/{s},fps={FPS}[s{i}]")
        labels.append(f"[s{i}]")
    fc = ";".join(parts) + f";{''.join(labels)}concat=n={len(spans)}:v=1:a=0,format=yuv420p[base]"
    ovs = [(to_out(t0), to_out(t1), p) for t0, t1, p in overlays]
    for a, b, s in spans:
        if s > 1.01:
            ovs.append((to_out(a), to_out(b), {"speed": f"SPED UP {s:g}×"}))
    args, cur, n = [], "[base]", 1
    for j, (o0, o1, params) in enumerate(ovs):
        if o1 - o0 < 0.2:
            continue
        args += ["-loop", "1", "-framerate", str(FPS), "-i", str(overlay(params))]
        fc += f";{cur}[{n}:v]overlay=0:0:enable='between(t,{o0:.2f},{o1:.2f})':shortest=1[o{j}]"
        cur = f"[o{j}]"; n += 1
    if timer:
        t0, t1 = to_out(timer[0]), to_out(timer[1])
        args += ["-framerate", "1", "-i", str(stopwatch_frames(timer[1] - timer[0]))]
        fc += (f";[{n}:v]fps={FPS},setpts=PTS-STARTPTS+{t0:.3f}/TB[w];"
               f"{cur}[w]overlay=0:0:eof_action=repeat:enable='between(t,{t0:.2f},{total:.2f})'[tw]")
        cur = "[tw]"; n += 1
    fc += f";{cur}fade=t=in:st=0:d=0.3,fade=t=out:st={total - 0.3:.2f}:d=0.3[v]"
    ff(["-i", str(rec.video), *args, "-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
        "-filter_complex", fc, "-map", "[v]", "-map", f"{n}:a", "-t", f"{total:.3f}", *ENC, str(out)])
    return total

def build(plan, only=None):
    PIECES.mkdir(parents=True, exist_ok=True)
    timeline, files, clock = [], [], 0.0
    for i, p in enumerate(plan):
        out = PIECES / f"{i:02d}-{p['name']}.mp4"
        if only is None or i in only or not out.exists():
            print(f"render {i:02d} {p['name']}", flush=True)
            if p["type"] == "card":
                render_card(p["card"], p["seconds"], p.get("audio"), p.get("audio_delay", 0.0), out)
            elif p["type"] == "media":
                render_media(p["path"], out)
            else:
                render_clip(p["rec"], p["spans"], p.get("overlays", []), out, p.get("timer"))
        d = dur(out)
        cues = []
        if p["type"] == "clip":          # caption overlays become script cues, in output time
            m = mapper(p["spans"])
            cues = [(round(clock + m(t0), 1), o.get("k", ""), o.get("cap", "")) for t0, t1, o in p.get("overlays", []) if o.get("cap")]
        timeline.append({"i": i, "name": p["name"], "start": round(clock, 1), "end": round(clock + d, 1), "cues": cues})
        clock += d; files.append(out)
    lst = OUT / "list.txt"
    lst.write_text("".join(f"file '{f.as_posix()}'\n" for f in files), encoding="utf-8")
    ff(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(OUT / "loop-backup.mp4")])
    (OUT / "timeline.json").write_text(json.dumps(timeline, indent=1), encoding="utf-8")
    print(f"total {clock / 60:.1f} min -> {OUT / 'loop-backup.mp4'}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--only", type=int, nargs="*")
    a = ap.parse_args()
    from plan import PLAN
    build(PLAN(), set(a.only) if a.only else None)
