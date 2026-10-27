"""Mix narration v2 (out/narr2-schedule.json, narr2/*.wav) over the backup video.
   python mix2.py   -> out/loop-backup-narrated-v2.mp4
Lines are mixed in batches (Windows command-line length) and summed, then loudness-normalised once."""
import json, subprocess
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "out" / "loop-backup.mp4"
OUT = HERE / "out" / "loop-backup-narrated-v2.mp4"
TMP = HERE / "out" / "mix2"; TMP.mkdir(exist_ok=True)

def ff(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)

sched = json.load(open(HERE / "out" / "narr2-schedule.json", encoding="utf-8"))
total = dur(SRC)
stems = []
for b in range(0, len(sched), 40):
    part = sched[b:b + 40]
    args, fc, labels = [], [], []
    for k, x in enumerate(part):
        args += ["-i", str(HERE / "narr2" / f"{x['id']}.wav")]
        fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(x['start'] * 1000)}:all=1,apad[n{k}]")
        labels.append(f"[n{k}]")
    fc.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{total:.3f}[v]")
    stem = TMP / f"stem{b // 40}.wav"
    ff([*args, "-filter_complex", ";".join(fc), "-map", "[v]", "-t", f"{total:.3f}", str(stem)])
    stems.append(stem)
voice = TMP / "voice.wav"
ff([*sum((["-i", str(s)] for s in stems), []), "-filter_complex",
    f"{''.join(f'[{i}:a]' for i in range(len(stems)))}amix=inputs={len(stems)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=7[v]",
    "-map", "[v]", str(voice)])
ff(["-i", str(SRC), "-i", str(voice), "-filter_complex", "[0:a][1:a]amix=inputs=2:normalize=0:duration=first[a]",
    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT)])
print(OUT, round(dur(OUT), 1), "s")
