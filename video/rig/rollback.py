"""Retake helper: drop every panel message from <run dir> onwards.   python rollback.py runs/<dir>"""
import json, sys
from pathlib import Path
start = json.loads(Path(sys.argv[1], "events.jsonl").open(encoding="utf-8").readline())["wall"]
st = json.loads(Path("state.json").read_text(encoding="utf-8"))
n = len(st["messages"]); st["messages"] = [m for m in st["messages"] if m["ts"] < start - 1]
Path("state.json").write_text(json.dumps(st), encoding="utf-8"); print(n, "->", len(st["messages"]))
