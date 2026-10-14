"""Run a list of Photoshop/Premiere bridge commands from a JSON file (avoids shell quoting).

    uv run ... tools/ps_step.py steps.json
steps.json: [{"app":"photoshop","action":"createDocument","options":{...},"timeout":60}, ...]
Stops at the first FAILURE. Prints each response (truncated).
"""
import json
import sys
import time

from adobe import call

steps = json.load(open(sys.argv[1], encoding="utf-8"))
for i, s in enumerate(steps, 1):
    t0 = time.time()
    try:
        r = call(s.get("app", "photoshop"), s["action"], s.get("options", {}), s.get("timeout", 60))
    except Exception as e:
        print(f"[{i}] {s['action']} FAILED ({time.time()-t0:.0f}s): {e}")
        sys.exit(1)
    brief = {k: r.get(k) for k in ("status", "response") if r}
    layers = [(l.get("id"), l.get("name"), l.get("type")) for l in (r or {}).get("layers", [])]
    print(f"[{i}] {s['action']} ok ({time.time()-t0:.0f}s): {json.dumps(brief, default=str)[:400]}")
    if layers:
        print(f"     layers: {layers}")
