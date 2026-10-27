"""Local server for the recording rig: the simulated Telegram page, its live state, GPU/network stats, and media
from C:/Loop. Only listens on 127.0.0.1.   python server.py"""
import json, mimetypes, subprocess, threading, time, socket
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

HERE = Path(__file__).parent
STATE = HERE / "state.json"
MEDIA_ROOT = Path("C:/Loop").resolve()
stats = {"gpu": 0, "vram_used": 0, "vram_total": 24463, "online": True, "t": 0}

def sample():
    while True:
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                                  "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=3,
                                 creationflags=0x08000000).stdout.strip().split(",")
            stats.update(gpu=int(out[0]), vram_used=int(out[1]), vram_total=int(out[2]))
        except Exception:
            pass
        try:   # the Wi-Fi adapter is the truth for "offline"; a slow ping is not
            st = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-NetAdapter -Name 'Wi-Fi').Status"],
                                capture_output=True, text=True, timeout=5, creationflags=0x08000000).stdout.strip()
            stats["online"] = st == "Up"
        except Exception:
            pass
        stats["t"] = time.time()
        time.sleep(1)

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def send(self, body, ctype, code=200):
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        u = urlparse(self.path)
        if u.path in ("/", "/chat"):
            return self.send((HERE / "chat.html").read_bytes(), "text/html; charset=utf-8")
        if u.path == "/state":
            try: body = STATE.read_bytes()
            except OSError: body = b"{}"
            return self.send(body, "application/json")
        if u.path == "/stats":
            return self.send(json.dumps(stats).encode(), "application/json")
        if u.path == "/media":
            p = Path(unquote(parse_qs(u.query).get("p", [""])[0])).resolve()
            if MEDIA_ROOT not in p.parents or not p.is_file():
                return self.send(b"not found", "text/plain", 404)
            return self.send(p.read_bytes(), mimetypes.guess_type(p.name)[0] or "application/octet-stream")
        if u.path.startswith("/static/"):
            p = (HERE / "static" / u.path[8:]).resolve()
            if (HERE / "static") in p.parents and p.is_file():
                return self.send(p.read_bytes(), mimetypes.guess_type(p.name)[0] or "application/octet-stream")
        self.send(b"not found", "text/plain", 404)

threading.Thread(target=sample, daemon=True).start()
print("rig server on http://127.0.0.1:8765", flush=True)
ThreadingHTTPServer(("127.0.0.1", 8765), H).serve_forever()
