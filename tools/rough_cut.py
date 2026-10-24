"""Build (or rebuild) the Cabana 30-second rough cut in Premiere, grab review frames, optionally export.

    uv run ... tools/rough_cut.py frames  --order clip01-pour,clip02-ice,... [--dissolve 0.5] [--name v1]
    uv run ... tools/rough_cut.py export  --name v1

frames: opens cabana/work/cabana.prproj if needed, creates sequence "spot-<name>" from the clips in order,
        trims every shot so the cut runs 30 s, lays vo.wav on A1, adds cross dissolves, saves the project,
        and writes review frames at 0/10/20/29 s to cabana/cut/frames/<name>-NNs.jpg.
export: exports spot-<name> to cabana/cut/cabana-spot.mp4 (H.264 1080p preset), transcribes vo.wav to
        cabana/cut/captions.srt (Faster-Whisper, float32) and burns cabana/cut/preview.mp4 with ffmpeg.
"""
import argparse
import os
import subprocess
import sys
import time

from adobe import call

LOOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
PROJECT = f"{LOOP}/cabana/work/cabana.prproj"
PRESET = f"{LOOP}/cabana/_master/cabana-1080p.epr"
CUT = f"{LOOP}/cabana/cut"
VO = "vo-30.wav"      # 28.4 s (Logan's cloned voice + silence pad), fits the 30 s spot
TICKS = 254016000000          # Premiere ticks per second
SPOT = 30.0
WHISPER = f"{LOOP}/tools/Faster-Whisper-XXL/faster-whisper-xxl.exe"


def pr(action, timeout=60, **options):
    return call("premiere", action, options, timeout)


def sequence_id(name):
    for s in pr("getProjectInfo").get("sequences", []):
        if s.get("name") == name:
            return s["id"]
    raise RuntimeError(f"sequence {name} not found")


def ensure_project():
    """Make sure the WORK copy is the active project (never the read-only master)."""
    try:
        path = (pr("getProjectInfo", 30).get("project") or {}).get("path", "")
    except Exception:
        path = ""
    if "/cabana/work/cabana.prproj" not in path.replace("\\", "/"):
        pr("openProject", 60, filePath=PROJECT)
        time.sleep(2)


def frames(order, name, dissolve):
    ensure_project()
    seq = f"spot-{name}"
    clips = [c if c.endswith(".mp4") else f"{c}.mp4" for c in order]
    pr("createSequenceFromMedia", 60, itemNames=clips, sequenceName=seq)
    sid = sequence_id(seq)
    shot = SPOT / len(clips)
    # each raw clip is 4 s and sits at i*4 s; shorten every clip's end, then close the gaps
    for i in range(len(clips)):
        start = i * 4.0
        pr("setClipStartEndTimes", 30, sequenceId=sid, trackIndex=0, trackItemIndex=i, trackType="VIDEO",
           startTimeTicks=int(start * TICKS), endTimeTicks=int((start + shot) * TICKS))
        time.sleep(0.3)                     # pace the edits: back-to-back transactions can crash Premiere
    time.sleep(1.0)
    pr("closeGapsOnSequence", 30, sequenceId=sid, trackIndex=0, trackType="VIDEO")
    time.sleep(1.0)
    pr("addMediaToSequence", 30, sequenceId=sid, itemName=VO, videoTrackIndex=0, audioTrackIndex=0,
       insertionTimeTicks=0, overwrite=True)
    if dissolve > 0:
        for i in range(len(clips) - 1):
            pr("appendVideoTransition", 30, sequenceId=sid, videoTrackIndex=0, trackItemIndex=i,
               transitionName="AE.ADBE Cross Dissolve New", duration=dissolve, clipAlignment=0.5)
    pr("saveProject", 30)
    os.makedirs(f"{CUT}/frames", exist_ok=True)
    out = []
    for sec in (0, 10, 20, 29):
        path = f"{CUT}/frames/{name}-{sec:02d}s.jpg"
        pr("exportFrame", 60, sequenceId=sid, filePath=path, seconds=sec)
        out.append(path)
    print(f"sequence {seq}: {len(clips)} shots x {shot:.2f}s, dissolve {dissolve}s")
    for p in out:
        print(f"frame {p}")


def wait_for_file(path, timeout=240):
    last, stable, t0 = -1, 0, time.time()
    while time.time() - t0 < timeout:
        size = os.path.getsize(path) if os.path.exists(path) else -1
        stable = stable + 1 if size == last and size > 0 else 0
        if stable >= 3:
            return True
        last = size
        time.sleep(2)
    return False


def export(name):
    ensure_project()
    sid = sequence_id(f"spot-{name}")
    mp4 = f"{CUT}/cabana-spot.mp4"
    if os.path.exists(mp4):
        os.remove(mp4)
    try:
        pr("exportSequence", 300, sequenceId=sid, outputPath=mp4, presetPath=PRESET)
    except Exception as e:  # the proxy may time out while the encode keeps running
        print(f"(export call returned: {e}; waiting for the file)")
    if not wait_for_file(mp4):
        raise RuntimeError("export did not finish")
    print(f"export {mp4}")
    subprocess.run([WHISPER, f"{LOOP}/cabana/raw/{VO}", "--model", "turbo", "--language", "en", "--compute_type", "float32",
                    "--output_format", "srt", "--output_dir", CUT, "--beep_off",
                    "--max_line_width", "38", "--max_line_count", "2", "--max_comma_cent", "50"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    srt = f"{CUT}/captions.srt"
    os.replace(f"{CUT}/{VO[:-4]}.srt", srt)
    print(f"captions {srt}")
    preview = f"{CUT}/preview.mp4"
    # subtitles filter needs an escaped, relative path on Windows -> run from the cut folder
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "cabana-spot.mp4", "-vf",
                    "subtitles=captions.srt:force_style='FontName=Arial,Bold=1,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00182A3B,BorderStyle=1,Outline=2,Shadow=0,MarginV=40'",
                    "-c:v", "libx264", "-crf", "23", "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k", "preview.mp4"],
                   cwd=CUT, check=True)
    print(f"preview {preview}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["frames", "export"])
    ap.add_argument("--order", default="clip01-pour,clip02-ice,clip03-beach,clip04-can-sand,clip05-cooler,clip06-waves,clip07-ocean-drive,clip08-cheers,clip10-hero-can")
    ap.add_argument("--name", default="v1")
    ap.add_argument("--dissolve", type=float, default=0.5)
    a = ap.parse_args()
    try:
        if a.mode == "frames":
            frames(a.order.split(","), a.name, a.dissolve)
        else:
            export(a.name)
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
