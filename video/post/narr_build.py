"""Generate every narration line in Logan's cloned voice, check each by transcribing it back, and retake the ones
that don't match (new seed), up to 4 rounds.   python narr_build.py"""
import difflib, json, re, subprocess
from pathlib import Path
from narration import LINES

HERE = Path(__file__).parent
NARR = HERE / "narr"; TXT = NARR / "txt"
VOICE = HERE.parent / "voice"
WHISPER = Path(r"C:\Users\Dell Demo\Desktop\Demo\Loop Agency\tools\Faster-Whisper-XXL\faster-whisper-xxl.exe")
SEEDS = NARR / "seeds.json"
NUM = {"one", "two", "three", "four", "five", "six", "eight", "ten", "twenty", "thirty", "half", "a"}

def norm(s):
    s = s.lower().replace("-", "").replace("...", " ")
    s = re.sub(r"\b([a-z]) (?=[a-z]\b)", r"\1", s)          # "g p u" -> "gpu"
    words = re.findall(r"[a-z]+", s)
    return [w for w in words if w not in NUM]

def score(want, got):
    return difflib.SequenceMatcher(None, norm(want), norm(got)).ratio()

def main():
    seeds = json.loads(SEEDS.read_text()) if SEEDS.exists() else {}
    TXT.mkdir(parents=True, exist_ok=True)
    for rnd in range(4):
        todo = [{"id": i, "text": t, "seed": seeds.get(i, (extra[0] if extra else 1))} for _, i, t, *extra in LINES]
        (NARR / "lines.json").write_text(json.dumps(todo, ensure_ascii=False), encoding="utf-8")
        subprocess.run([str(VOICE / ".venv" / "Scripts" / "python.exe"), str(VOICE / "narrate.py"), str(NARR / "lines.json"),
                        str(NARR)], env={**__import__("os").environ, "HF_HOME": str(VOICE / ".hf")}, capture_output=True)
        need = [i for _, i, *_ in LINES if not (TXT / f"{i}.txt").exists()]
        if need:
            subprocess.run([str(WHISPER), *[str(NARR / f"{i}.wav") for i in need], "--model", "turbo", "--language", "en",
                            "--compute_type", "float32", "--output_dir", str(TXT), "--output_format", "txt", "--beep_off"],
                           capture_output=True, cwd=str(WHISPER.parent))
        bad = []
        for _, i, t, *_ in LINES:
            got = re.sub(r"\[[^\]]*\]\s*", "", (TXT / f"{i}.txt").read_text(encoding="utf-8", errors="replace"))
            sc = score(t, got)
            if sc < 0.9:
                bad.append((i, round(sc, 2), got.strip()[:120]))
        print(f"round {rnd}: {len(LINES) - len(bad)}/{len(LINES)} ok", flush=True)
        for b in bad:
            print("   retake", *b, flush=True)
        if not bad:
            break
        for i, *_ in bad:
            seeds[i] = seeds.get(i, 1) + 1
            (NARR / f"{i}.wav").unlink(missing_ok=True); (TXT / f"{i}.txt").unlink(missing_ok=True)
        SEEDS.write_text(json.dumps(seeds))

if __name__ == "__main__":
    main()
