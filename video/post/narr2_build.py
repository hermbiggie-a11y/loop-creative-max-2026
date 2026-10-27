"""Narration v2: generate every line in the Recording-2 clone, verify by transcription (retake up to 4 rounds), then
schedule against the video and report overlaps, quiet-zone hits and talk coverage.
   python narr2_build.py          -> narr2/*.wav + out/narr2-schedule.json"""
import difflib, hashlib, json, os, re, subprocess
from pathlib import Path
from narration2 import S, QUIET

HERE = Path(__file__).parent
NARR = HERE / "narr2"; TXT = NARR / "txt"
VOICE = HERE.parent / "voice"
REF = VOICE / "samples" / "ref2-c4.wav"
WHISPER = Path(r"C:\Users\Dell Demo\Desktop\Demo\Loop Agency\tools\Faster-Whisper-XXL\faster-whisper-xxl.exe")
SEEDS = NARR / "seeds.json"
GAP = 0.45
NUM = {"one", "two", "three", "four", "five", "six", "eight", "nine", "ten", "twenty", "thirty", "half", "a",
       "hundred", "and", "sixteen", "billion", "zero"}

def lid(k, text):
    return "l-" + hashlib.md5(text.encode()).hexdigest()[:8]

LINES = [(a, lid(k, t), t) for k, (a, t) in enumerate(S, 1)]

def norm(s):
    s = s.lower().replace("-", "").replace("...", " ")
    s = re.sub(r"\b([a-z]) (?=[a-z]\b)", r"\1", s)
    return [w for w in re.findall(r"[a-z]+", s) if w not in NUM]

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)

def build():
    seeds = json.loads(SEEDS.read_text()) if SEEDS.exists() else {}
    TXT.mkdir(parents=True, exist_ok=True)
    for rnd in range(5):
        todo = [{"id": i, "text": t, "seed": seeds.get(i, 1), "ex": 0.6, "cfg": 0.4} for _, i, t in LINES]
        (NARR / "lines.json").write_text(json.dumps(todo, ensure_ascii=False), encoding="utf-8")
        subprocess.run([str(VOICE / ".venv" / "Scripts" / "python.exe"), str(VOICE / "narrate.py"), str(NARR / "lines.json"),
                        str(NARR)], env={**os.environ, "HF_HOME": str(VOICE / ".hf"), "REF": str(REF)}, capture_output=True)
        need = [i for _, i, _ in LINES if not (TXT / f"{i}.txt").exists()]
        if need:
            subprocess.run([str(WHISPER), *[str(NARR / f"{i}.wav") for i in need], "--model", "turbo", "--language", "en",
                            "--compute_type", "float32", "--output_dir", str(TXT), "--output_format", "txt", "--beep_off"],
                           capture_output=True, cwd=str(WHISPER.parent))
        bad = []
        for _, i, t in LINES:
            got = re.sub(r"\[[^\]]*\]\s*", "", (TXT / f"{i}.txt").read_text(encoding="utf-8", errors="replace"))
            sc = difflib.SequenceMatcher(None, norm(t), norm(got)).ratio()
            if sc < 0.9:
                bad.append((i, round(sc, 2), got.strip()[:110]))
        print(f"round {rnd}: {len(LINES) - len(bad)}/{len(LINES)} ok", flush=True)
        for b in bad:
            print("   retake", *b, flush=True)
        if not bad or rnd == 4:
            break
        for i, *_ in bad:
            seeds[i] = seeds.get(i, 1) + 1
            (NARR / f"{i}.wav").unlink(missing_ok=True); (TXT / f"{i}.txt").unlink(missing_ok=True)
        SEEDS.write_text(json.dumps(seeds))

def schedule():
    sched, end, issues = [], 0.0, []
    for k, (a, i, t) in enumerate(LINES):
        d = dur(NARR / f"{i}.wav")
        start = a if a is not None else end + GAP
        if a is not None and a < end + 0.25:
            issues.append(f"line {k + 1} anchored {a:.1f} but previous ends {end:.1f} (+{end + 0.25 - a:.1f}s)")
        end = start + d
        for q0, q1 in QUIET:
            if start < q1 and end > q0:
                issues.append(f"line {k + 1} ({start:.1f}-{end:.1f}) runs into quiet zone {q0}-{q1}")
        sched.append({"start": round(start, 2), "end": round(end, 2), "id": i, "text": t})
    (HERE / "out" / "narr2-schedule.json").write_text(json.dumps(sched, indent=1, ensure_ascii=False), encoding="utf-8")
    tl = json.load(open(HERE / "out" / "timeline.json", encoding="utf-8"))
    for p in tl:
        talk = sum(max(0, min(s["end"], p["end"]) - max(s["start"], p["start"])) for s in sched)
        print(f"{p['name']:12} {p['end'] - p['start']:6.1f}s talk {talk:6.1f}s {100 * talk / (p['end'] - p['start']):4.0f}%")
    total = sum(s["end"] - s["start"] for s in sched)
    print(f"TOTAL talk {total:.0f}s of {tl[-1]['end']:.0f}s = {100 * total / tl[-1]['end']:.0f}%; last line ends {sched[-1]['end']:.1f}")
    for x in issues:
        print("ISSUE", x)

if __name__ == "__main__":
    import sys
    if "--schedule-only" not in sys.argv:
        build()
    schedule()
