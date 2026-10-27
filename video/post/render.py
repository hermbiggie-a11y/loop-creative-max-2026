"""Render cards.html cards/overlays to 1920x1080 PNGs with headless Chrome.
   python render.py cards            -> cards/<name>.png for every card
   (imported by edit.py for captions/overlays)"""
import subprocess, sys, hashlib
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CARDS = ["title", "built", "diagram", "rules", "beat1", "beat2", "beat3", "beat4", "ask", "spot", "spanish", "close"]

def render(params, out):
    out = Path(out).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    url = (HERE / "cards.html").as_uri() + "?" + urlencode(params)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--default-background-color=00000000", "--virtual-time-budget=4000", "--window-size=1920,1080",
                    f"--user-data-dir={HERE / '.chrome'}", f"--screenshot={out}", url],
                   check=True, capture_output=True)
    return out

def overlay(params):
    """Cached transparent overlay PNG for a dict of params."""
    key = hashlib.md5(repr(sorted(params.items())).encode()).hexdigest()[:12]
    out = HERE / "ov" / f"{key}.png"
    return out if out.exists() else render(params, out)

if __name__ == "__main__" and sys.argv[1:] == ["cards"]:
    for c in CARDS:
        print(render({"card": c}, HERE / "cards" / f"{c}.png"))
