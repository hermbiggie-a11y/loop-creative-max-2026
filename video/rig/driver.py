"""Records one segment of the Loop backup video.

Drives the real Hermes agent from the CLI (same agent, tools and skills as Telegram), mirrors the conversation into the
simulated Telegram page (state.json -> server.py -> chat.html), arranges the Adobe windows, and screen-records with
ffmpeg. Every event is logged with its time from the start of the clip, which the editor uses to place captions.

    python driver.py <segment> [--no-record] [--no-reset]
"""
import argparse, json, os, re, socket, subprocess, sys, tempfile, threading, time
from pathlib import Path

HERE = Path(__file__).parent
RUNS = HERE / "runs"
STATE = HERE / "state.json"
LOOP = Path("C:/Loop")
HERMES_HOME = Path(os.environ["USERPROFILE"]) / ".hermes"
HERMES = HERMES_HOME / "bin" / "hermes.exe"
FFMPEG = "ffmpeg"
NO_WINDOW = 0x08000000

CLOUD = {"name": "Claude Sonnet 5.5", "where": "cloud", "args": []}
LOCAL = {"name": "gpt-oss 20B", "where": "local", "args": ["--provider", "ollama", "-m", "gpt-oss:20b", "--reasoning", "low", "-s", "cabana-social-resize"]}

# ---------------------------------------------------------------- state shared with the page
state = {"scene": "chat", "model": {k: CLOUD[k] for k in ("name", "where")}, "messages": [], "composer": "",
         "working": None, "reset_id": 0}
_lock = threading.Lock()

def save():
    with _lock:
        tmp = STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8")
        os.replace(tmp, STATE)

class Run:
    def __init__(self, seg, record):
        self.seg = seg
        self.dir = RUNS / time.strftime(f"%Y%m%d-%H%M%S-{seg}")
        self.dir.mkdir(parents=True)
        self.log = open(self.dir / "events.jsonl", "a", encoding="utf-8")
        self.t0 = time.time()
        self.rec = None
        self.record = record

    def ev(self, kind, **kw):
        kw.update(kind=kind, t=round(time.time() - self.t0, 2), wall=time.time())
        self.log.write(json.dumps(kw) + "\n"); self.log.flush()
        print(f"[{kw['t']:7.1f}] {kind} {json.dumps({k: v for k, v in kw.items() if k not in ('kind', 't', 'wall')})[:160]}", flush=True)

    def start_recording(self):
        if not self.record:
            return
        out = self.dir / "screen.mkv"
        self.rec = subprocess.Popen(
            [FFMPEG, "-hide_banner", "-loglevel", "error", "-f", "lavfi",
             "-i", "ddagrab=output_idx=0:framerate=30:draw_mouse=0",
             "-vf", "hwdownload,format=bgra,crop=1920:1080:0:0,format=nv12",
             "-c:v", "h264_qsv", "-preset", "medium", "-global_quality", "21", "-bf", "0", str(out)],
            stdin=subprocess.PIPE, creationflags=NO_WINDOW)
        time.sleep(1.0)
        self.t0 = time.time()          # clip time 0 ~= first recorded frame
        self.ev("record_start", file=str(out))

    def stop_recording(self):
        if self.rec:
            self.ev("record_stop")
            self.rec.stdin.write(b"q"); self.rec.stdin.flush()
            self.rec.wait(timeout=30)

# ---------------------------------------------------------------- helpers
def msg(frm, text, media=None):
    state["messages"].append({"id": len(state["messages"]) + 1 + state["reset_id"] * 1000, "from": frm,
                              "text": text, "media": media or [], "ts": time.time()})
    save()

def type_into_composer(text, cps=28):
    for i in range(1, len(text) + 1):
        state["composer"] = text[:i]; save()
        time.sleep(1 / cps if text[i - 1] != " " else 1.6 / cps)
    time.sleep(0.5)
    state["composer"] = ""; save()

MEDIA_EXT = ("png", "jpg", "jpeg", "webp", "mp4", "mov", "webm")

def media_of(text):
    """Split a reply into text + attachments. MEDIA: lines (Telegram) and bare C:/Loop/... file paths (CLI) both
    become attachments, the way the Telegram gateway would send them."""
    media, keep = [], []
    def add(p):
        p = p.replace("\\", "/").rstrip(".,;:)`'\"")
        if p.rsplit(".", 1)[-1].lower() not in MEDIA_EXT or any(m["path"] == p for m in media):
            return
        ext = p.rsplit(".", 1)[-1].lower()
        media.append({"path": p, "kind": "video" if ext in ("mp4", "mov", "webm") else "image"})
    folder = None                          # "Frames, in C:/Loop/.../frames/:" followed by bare file names
    for line in text.splitlines():
        if not line.strip():
            folder = None
        m = re.match(r"\s*MEDIA:\s*(\S+)", line)
        if m:
            add(m.group(1)); continue
        listed = re.match(r"\s*(?:[-•*]\s*)?([\w.-]+\.(?:png|jpe?g|webp))\b", line, re.I)
        if folder and listed:
            add(folder + listed.group(1)); continue
        paths = re.findall(r"[Cc]:[/\\]Loop[/\\][^\s`'\")*,]+", line)
        for p in paths:
            if re.search(r"[/\\]:?$", p) or "." not in p.rsplit("/", 1)[-1].rstrip(":"):
                folder = p.replace("\\", "/").rstrip(":").rstrip("/") + "/"
            else:
                add(p)
        rest = line
        for p in paths:
            rest = rest.replace(p, "")
        if paths and len(re.findall(r"[A-Za-z]+", rest)) <= 2:
            continue                      # line was only a label + file path(s)
        keep.append(line)
    return "\n".join(keep).strip(), media

def pretty_tool(name, inp):
    """One short line per tool call for the activity card."""
    inp = inp or {}
    n = re.sub(r"^mcp_+", "", name)
    for app in ("photoshop", "premiere"):
        if n.startswith(app):
            n = f"{app} · {n[len(app):].strip('_')}"
    detail = ""
    if name == "terminal":
        c = inp.get("command", "")
        c = re.sub(r"powershell -NoProfile -File C:/Loop/tools/py\.ps1\s+", "", c)
        c = c.replace("C:/Loop/", "").replace("C:\\Loop\\", "")
        detail = c[:90]
    elif name in ("skill_view", "skills_view", "skill"):
        detail = inp.get("name") or inp.get("skill") or ""
    elif "path" in inp or "file_path" in inp:
        detail = str(inp.get("path") or inp.get("file_path")).replace("C:/Loop/", "")
    else:
        bits = [f"{k}={v}" for k, v in inp.items() if isinstance(v, (str, int, float)) and len(str(v)) < 40][:3]
        detail = " ".join(bits)
    return {"tool": n, "detail": detail}

def hermes_turn(run, text, session, model, title="Hermes is working"):
    q = Path(tempfile.mktemp(suffix=".txt"))
    q.write_text(text, encoding="utf-8")
    cmd = [str(HERMES), "chat", "--query-file", str(q), "-c", session, "--create-if-missing",
           "--format", "stream-json"] + model["args"]
    env = dict(os.environ, HERMES_HOME=str(HERMES_HOME), PYTHONIOENCODING="utf-8")
    state["working"] = {"active": True, "since": time.time(), "tools": [], "title": title}; save()
    run.ev("hermes_start", text=text, model=model["name"])
    p = subprocess.Popen(cmd, cwd=str(LOOP / "cabana"), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         creationflags=NO_WINDOW)
    final, err = None, None
    for raw in p.stdout:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("{"):
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "tool_use":
            pt = pretty_tool(e.get("name", ""), e.get("input"))
            state["working"]["tools"].append(pt); save()
            run.ev("tool", name=e.get("name"), input=e.get("input"))
        elif e.get("type") == "tool_result":
            run.ev("tool_result", name=e.get("name"), ms=e.get("duration_ms"), error=e.get("is_error"),
                   output=str(e.get("output"))[:400])
        elif e.get("type") == "result":
            final = e.get("text") or ""
            if e.get("exit_code"):
                err = e
    p.wait()
    q.unlink(missing_ok=True)
    state["working"] = None
    body, media = media_of(final or "(no reply)")
    msg("bot", body, media)
    run.ev("hermes_reply", text=final, media=media, exit=p.returncode, error=bool(err))
    return final

def say(run, text, session, model, pause_after=2.0):
    run.ev("user_typing", text=text)
    type_into_composer(text)
    msg("user", text)
    run.ev("user_sent", text=text)
    time.sleep(0.8)
    reply = hermes_turn(run, text, session, model)
    time.sleep(pause_after)
    return reply

def ps(script, *args):
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), *map(str, args)],
                   creationflags=NO_WINDOW, check=False)

def place(proc, x, y, w, h):
    ps(HERE / "winpos.ps1", "-Proc", proc, "-X", x, "-Y", y, "-W", w, "-H", h)

def keep_front(proc, stop):
    """Every few seconds, restack the app and the panel above everything else (Logan's clicks can't bury them)."""
    while not stop.is_set():
        ps(HERE / "winpos.ps1", "-Proc", proc, "-ZOnly")
        ps(HERE / "winpos.ps1", "-Proc", "msedge-loopchat", "-ZOnly")
        stop.wait(3)

def layout_app(proc):
    place(proc, 0, 0, 1280, 1080)
    ps(HERE / "winpos.ps1", "-Proc", "msedge-loopchat", "-X", 1273, "-Y", -36, "-W", 654, "-H", 1116)

def wifi_up():
    out = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-NetAdapter -Name 'Wi-Fi').Status"],
                         capture_output=True, text=True, creationflags=NO_WINDOW).stdout.strip()
    return out == "Up"

def online():
    """Offline only when the Wi-Fi adapter is down AND the internet is unreachable (a slow ping alone is not offline)."""
    if wifi_up():
        return True
    for host in ("1.1.1.1", "8.8.8.8"):
        try:
            socket.create_connection((host, 443), timeout=2).close(); return True
        except OSError:
            pass
    return False

def wait_for_network(run, want_online, prompt):
    run.ev("waiting_for_logan", want_online=want_online)
    print("\n" + "=" * 60 + f"\n  LOGAN: {prompt}\n" + "=" * 60, flush=True)
    (HERE / "PING.txt").write_text(prompt, encoding="utf-8")
    hits = 0
    while hits < 3:                      # three checks in a row, so a blip doesn't count
        hits = hits + 1 if online() == want_online else 0
        time.sleep(1)
    (HERE / "PING.txt").unlink(missing_ok=True)
    run.ev("network", online=want_online)
    time.sleep(3)

def popup(text):
    subprocess.Popen(["powershell", "-NoProfile", "-Command",
                      f"Add-Type -A PresentationFramework; [System.Windows.MessageBox]::Show('{text}', 'Loop recording')"],
                     creationflags=NO_WINDOW)

def new_chat(session_label):
    state["reset_id"] += 1
    state["messages"] = []
    save()
    return f"{session_label}-{time.strftime('%H%M%S')}"

# ---------------------------------------------------------------- segments
PROMPTS = {
    "story": "Resize the Cabana hero for Instagram Story and send it to me.",
    "brief": "New client: Cabana Cold Brew, a canned cold brew launching in Miami on June 1st. We need one hero key "
             "visual, six social sizes, a 30-second spot cut from our raw footage, and captions. Write the brief.",
    "gate1": "B, and make the headline shorter.",
    "hero": "Open the Cabana hero, extend the beach with Generative Fill, put our headline on it, and send me three "
            "headline options.",
    "gate2": "2",
    "cut": "Cut the 30-second spot from the raw footage in shot-list order and send me frames at 0, 10, 20 and 29 seconds.",
    "notes": "Open on the pour, drop the beach shot, shorter dissolves.",
    "go": "go",
    "spanish": "Make a Spanish version of the square post for the Little Havana launch and send it to me.",
    "learn": "What did you learn today?",
    "cron": "Every morning at 8, send me the project status.",
}
SESSION_FILE = HERE / "session.txt"

def seg_login(run):
    """Simulated Telegram login (no real account)."""
    new_chat("login")
    state["scene"] = "login"; state["login"] = {"phone": ""}; save()
    time.sleep(1.5); run.ev("mark", label="login")
    phone = "+1 (816) 555-0142"
    for i in range(1, len(phone) + 1):
        state["login"]["phone"] = phone[:i]; save(); time.sleep(0.07)
    time.sleep(1.0); state["login"]["code"] = ""; save(); time.sleep(1.2)
    for i in range(1, 6):
        state["login"]["code"] = "• " * i; save(); time.sleep(0.25)
    time.sleep(0.6); state["login"]["done"] = True; save(); time.sleep(2.0)
    state["scene"] = "chat"; state.pop("login"); save()
    run.ev("mark", label="chat_open")
    msg("sys", "Loop · Hermes — your agent on the Dell Pro Max")
    time.sleep(1.0)
    type_into_composer("ping"); msg("user", "ping"); time.sleep(1.2)
    msg("bot", "Pong — Hermes here, on the Pro Max. Photoshop and Premiere are connected. What are we making?")
    run.ev("mark", label="ping_done"); time.sleep(4)

def seg_hook(run):
    session = new_chat("loop-hook")
    msg("sys", "Today")
    layout_app("Photoshop"); time.sleep(2)
    say(run, PROMPTS["story"], session, CLOUD, pause_after=5)

def seg_beat1(run):
    session = new_chat("loop-run"); SESSION_FILE.write_text(session)
    msg("sys", "/new — fresh session")
    place("Photoshop", 0, 0, 1280, 1080); ps(HERE / "winpos.ps1", "-Proc", "msedge-loopchat", "-X", 1273, "-Y", -36, "-W", 654, "-H", 1116); time.sleep(2)
    say(run, PROMPTS["brief"], session, CLOUD, pause_after=1)
    show_file(run, LOOP / "cabana/work/brief.md", 8)
    say(run, PROMPTS["gate1"], session, CLOUD, pause_after=1)
    show_file(run, LOOP / "cabana/work/brief.md", 8)

def show_file(run, path, secs):
    if not path.exists():
        cand = sorted((LOOP / "cabana").rglob("brief*.md"))
        if not cand:
            run.ev("mark", label="brief_missing"); return
        path = cand[0]
    subprocess.Popen(["notepad.exe", str(path)])
    time.sleep(2.0); ps(HERE / "winpos.ps1", "-Title", f"*{path.name}*", "-X", 0, "-Y", 0, "-W", 1280, "-H", 1080)
    run.ev("mark", label="brief_open", path=str(path)); time.sleep(secs)
    ps(HERE / "winpos.ps1", "-Title", f"*{path.name}*", "-Close"); run.ev("mark", label="brief_closed")

def resume_session():
    return SESSION_FILE.read_text().strip()

def seg_beat2(run):
    session = resume_session()
    layout_app("Photoshop"); time.sleep(2)
    say(run, PROMPTS["hero"], session, CLOUD, pause_after=3)
    explorer = subprocess.Popen(["explorer.exe", str(LOOP / "cabana" / "social")])
    time.sleep(2.5); place("explorer", 0, 640, 760, 440)
    say(run, PROMPTS["gate2"], session, CLOUD, pause_after=5)

def seg_beat3(run):
    session = resume_session()
    if os.environ.get("LOOP_NEW_SESSION"):          # retake: fresh session so Hermes doesn't think it's already cut
        session = f"loop-run3-{time.strftime('%H%M%S')}"; SESSION_FILE.write_text(session)
    layout_app("Adobe Premiere Pro"); time.sleep(2)
    say(run, PROMPTS["cut"], session, CLOUD, pause_after=3)
    say(run, PROMPTS["notes"], session, CLOUD, pause_after=3)
    say(run, PROMPTS["go"], session, CLOUD, pause_after=8)

def seg_beat4(run):
    session = f"loop-run4-{time.strftime('%H%M%S')}"   # fresh session: the local model must do the work, not recall it
    layout_app("Photoshop"); time.sleep(2)
    stop = threading.Event()
    threading.Thread(target=keep_front, args=("Photoshop", stop), daemon=True).start()
    wait_for_network(run, False, "Turn Wi-Fi OFF now (taskbar network icon -> Wi-Fi off).")
    layout_app("Photoshop"); run.ev("mark", label="relayout")     # Logan's clicks may have fronted other windows
    type_into_composer("/model"); msg("user", "/model"); time.sleep(1)
    state["model"] = {k: LOCAL[k] for k in ("name", "where")}; save()
    msg("bot", "Switched to **gpt-oss 20B** (Ollama, local, on the RTX PRO 5000). Nothing leaves this laptop.")
    run.ev("mark", label="model_local"); time.sleep(3)
    say(run, PROMPTS["spanish"], session, LOCAL, pause_after=4)
    say(run, PROMPTS["learn"], session, LOCAL, pause_after=4)
    popup("Offline part is done - click OK, turn Wi-Fi back ON, then tell Claude in the chat.")
    wait_for_network(run, True, "Turn Wi-Fi back ON now.")
    time.sleep(4); layout_app("Photoshop"); run.ev("mark", label="relayout")
    state["model"] = {k: CLOUD[k] for k in ("name", "where")}; save()
    msg("sys", "Back online — Claude Sonnet 5.5"); run.ev("mark", label="model_cloud"); time.sleep(3)
    say(run, PROMPTS["cron"], session, CLOUD, pause_after=6)
    stop.set(); time.sleep(1)
    popup("Beat 4 recording is finished - you can use the laptop and tell Claude.")

SEGMENTS = {"login": seg_login, "hook": seg_hook, "beat1": seg_beat1, "beat2": seg_beat2, "beat3": seg_beat3,
            "beat4": seg_beat4}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segment", choices=list(SEGMENTS) + ["say"])
    ap.add_argument("--no-record", action="store_true")
    ap.add_argument("--reset", action="store_true", help="run reset-cabana.ps1 first")
    ap.add_argument("--text", help="for 'say': one message on the current run session")
    a = ap.parse_args()
    if STATE.exists():
        state.update(json.loads(STATE.read_text(encoding="utf-8")))
    state["working"] = None; state["composer"] = ""; state["scene"] = "chat"; state.pop("login", None)
    state["model"] = {k: CLOUD[k] for k in ("name", "where")}
    save()
    if a.reset:
        ps(LOOP / "tools" / "reset-cabana.ps1")
    run = Run(a.segment, not a.no_record)
    run.start_recording()
    try:
        if a.segment == "say":
            say(run, a.text, resume_session(), CLOUD)
        else:
            SEGMENTS[a.segment](run)
    finally:
        run.stop_recording()
        run.ev("done")
    print("run dir:", run.dir)

if __name__ == "__main__":
    main()
