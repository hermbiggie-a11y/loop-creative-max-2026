"""Lay the cloned-voice narration over the backup video.
   python mix.py [start end]   -> out/loop-backup-narrated.mp4 (or a sample clip of [start, end] seconds)"""
import subprocess, sys, json
from pathlib import Path
from narration import LINES

HERE = Path(__file__).parent
SRC = HERE / "out" / "loop-backup.mp4"

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)

def main():
    start, end = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) == 3 else (0.0, dur(SRC))
    out = HERE / "out" / ("loop-backup-narrated.mp4" if len(sys.argv) != 3 else f"sample-narrated-{int(start)}-{int(end)}.mp4")
    lines = [(t, i) for t, i, *_ in LINES if start <= t < end]
    # overlap check: a line must end before the next one starts
    for (t1, i1), (t2, i2) in zip(lines, lines[1:]):
        e = t1 + dur(HERE / "narr" / f"{i1}.wav")
        if e > t2 - 0.2:
            print(f"WARNING {i1} ends {e:.1f}s, {i2} starts {t2:.1f}s")
    inputs = ["-ss", f"{start}", "-t", f"{end - start}", "-i", str(SRC)]
    fc, labels = [], []
    for k, (t, i) in enumerate(lines, 1):
        inputs += ["-i", str(HERE / "narr" / f"{i}.wav")]
        ms = int((t - start) * 1000)
        fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}:all=1[n{k}]")
        labels.append(f"[n{k}]")
    fc.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=7[voice]")
    fc.append("[0:a][voice]amix=inputs=2:normalize=0:duration=first[a]")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
                    "-map", "0:v", "-map", "[a]", "-t", f"{end - start}", "-c:v", "copy" if len(sys.argv) != 3 else "libx264", "-crf", "19",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)], check=True)
    print(out, round(dur(out), 1), "s")

if __name__ == "__main__":
    main()
