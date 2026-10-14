"""Build Cabana social sizes inside Photoshop (live, layer by layer) and export PNGs.

    uv run --no-project --python 3.13 --with python-socketio --with websocket-client --with requests \
        tools/social_resize.py "ICE, MIAMI." [1080x1920 ...]

Each size is a new Photoshop document: hero (smart object, cover-scaled), logo, and the headline
re-laid for that format (never scaled). Output: cabana/social/<w>x<h>.png. Prints one line per size.
"""
import json
import os
import sys
import time

from adobe import call

LOOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
HERO = f"{LOOP}/cabana/_master/hero-nologo.png"     # 3200x1600, can + extended beach, no logo/headline
LOGO = f"{LOOP}/cabana/assets/logo.png"             # 1200x520, dark wordmark
OUT = f"{LOOP}/cabana/social"
HERO_W, HERO_H = 3200, 1600
CAN = {"left": 1345, "top": 239, "right": 1883, "bottom": 1516}  # can bounds inside the hero
SIZES = [(1080, 1080), (1080, 1920), (1080, 1350), (1200, 628), (1600, 900), (1500, 500)]
SAND = {"red": 246, "green": 231, "blue": 203}
CORAL = {"red": 255, "green": 111, "blue": 89}
ESPRESSO = {"red": 59, "green": 36, "blue": 24}


def ps(action, timeout=60, **options):
    r = call("photoshop", action, options, timeout)
    return (r or {}).get("response")


def bounds(layer_id):
    b = ps("getLayerBounds", layerId=layer_id)
    return b["left"], b["top"], b["right"], b["bottom"]


def new_layer(name):
    before = {l["id"] for l in call("photoshop", "getLayers", {}, 30).get("layers", [])}
    r = call("photoshop", "createPixelLayer", {"layerName": name, "opacity": 100, "fillNeutral": False, "blendMode": "NORMAL"}, 30)
    return next(l["id"] for l in r["layers"] if l["id"] not in before)


def place(name, path):
    lid = new_layer(name)
    return ps("placeImage", 120, layerId=lid, imagePath=path, rasterize=False)["layerId"]


def move_to(layer_id, x=None, y=None, anchor="center-middle"):
    """Move the layer so its anchor point ("left|center|right"-"top|middle|bottom") lands on (x, y)."""
    l, t, r, b = bounds(layer_id)
    horiz, vert = anchor.split("-")
    dx = dy = 0
    if x is not None:
        dx = x - {"center": (l + r) / 2, "left": l, "right": r}[horiz]
    if y is not None:
        dy = y - {"top": t, "middle": (t + b) / 2, "bottom": b}[vert]
    if dx or dy:
        ps("translateLayer", layerId=layer_id, xOffset=int(round(dx)), yOffset=int(round(dy)))


def scale_to_width(layer_id, width):
    l, t, r, b = bounds(layer_id)
    pct = width / max(1, r - l) * 100
    ps("scaleLayer", layerId=layer_id, width=pct, height=pct, anchorPosition="MIDDLECENTER", interpolationMethod="AUTOMATIC")


def headline(text, max_w, max_h, color):
    size = int(min(max_h / 0.78, max_w / 4.2))
    r = call("photoshop", "createSingleLineTextLayer", {"layerName": "headline", "contents": text, "fontSize": size, "opacity": 100,
             "position": {"x": 10, "y": size}, "fontName": "BebasNeue-Regular", "textColor": color, "blendMode": "NORMAL"}, 30)
    lid = next(l["id"] for l in r["layers"] if l["name"] == "headline")
    for _ in range(2):  # fit: shrink if the real width/height overshoot
        l, t, rr, b = bounds(lid)
        k = min(max_w / max(1, rr - l), max_h / max(1, b - t), 1.0)
        if k >= 0.98:
            break
        size = int(size * k * 0.98)
        ps("editTextLayer", layerId=lid, contents=text, fontSize=size, fontName="BebasNeue-Regular", textColor=color)
    return lid


def build(text, w, h, suffix=""):
    # NB: Photoshop only transforms a smart object while it is the active layer, so each layer is
    # placed -> scaled -> moved before the next one is created.
    t0 = time.time()
    m = 0.05 * min(w, h)
    banner = w / h >= 2.5
    tall = h / w >= 1.5
    fit = min(w / HERO_W, h / HERO_H)
    if banner:                              # whole hero, slid right; headline + logo in the sand on the left
        s = fit
        hero_cx, hero_cy = w / 2 + (w * 0.5 - HERO_W * s / 2) * 0.66, h / 2
    elif tall:                              # hero at the bottom, Generative Fill extends the sky above it
        sky = 0.20 * h
        s = max((h - sky) / HERO_H, w / HERO_W)
        hero_cx, hero_cy = w / 2, h - HERO_H * s / 2
    else:                                   # cover
        s = max(w / HERO_W, h / HERO_H)
        hero_cx, hero_cy = w / 2, h / 2
    can = {"left": hero_cx + (CAN["left"] - HERO_W / 2) * s, "right": hero_cx + (CAN["right"] - HERO_W / 2) * s,
           "top": hero_cy + (CAN["top"] - HERO_H / 2) * s, "bottom": hero_cy + (CAN["bottom"] - HERO_H / 2) * s}

    ps("createDocument", name=f"cabana-{w}x{h}", width=w, height=h, resolution=72, fillColor=SAND, colorMode="RGB")

    # 1. hero
    hero = place("hero", HERO)
    if abs(s / fit - 1) > 0.001:
        pct = s / fit * 100
        ps("scaleLayer", layerId=hero, width=pct, height=pct, anchorPosition="MIDDLECENTER", interpolationMethod="AUTOMATIC")
    move_to(hero, x=hero_cx, y=hero_cy)
    if tall:
        top = int(h - HERO_H * s) + 40      # overlap the hero edge so the fill blends
        ps("selectRectangle", layerId=hero, feather=0, antiAlias=True, bounds={"top": 0, "left": 0, "bottom": top, "right": w})
        ps("generativeFill", 300, layerName="sky", prompt="clear bright blue Miami summer sky, soft haze near the horizon",
           layerId=hero, contentType="photo")
        ps("selectRectangle", layerId=hero, feather=0, antiAlias=True, bounds={"top": 0, "left": 0, "bottom": 0, "right": 0})

    # 2. logo
    logo = place("logo", LOGO)
    if tall:
        scale_to_width(logo, 0.38 * w)
        move_to(logo, x=w / 2, y=m, anchor="center-top")
    elif banner:
        left_w = hero_cx - HERO_W * s / 2
        scale_to_width(logo, 0.50 * left_w)
        move_to(logo, x=left_w / 2, y=h - m, anchor="center-bottom")
    elif w / h >= 1.5:
        scale_to_width(logo, 0.20 * w)
        move_to(logo, x=(can["right"] + w) / 2, y=h - m, anchor="center-bottom")
    else:
        scale_to_width(logo, 0.26 * w)
        move_to(logo, x=w - m, y=h - m, anchor="right-bottom")
    logo_b = bounds(logo)[3]

    # 3. headline (re-laid per size, never scaled)
    if tall:
        hl = headline(text, 0.86 * w, (can["top"] - logo_b) * 0.62, CORAL)
        move_to(hl, x=w / 2, y=(logo_b + can["top"]) / 2)
    elif banner:
        hl = headline(text, 0.86 * left_w, 0.34 * h, ESPRESSO)
        move_to(hl, x=left_w / 2, y=0.40 * h)
    elif w / h >= 1.5:
        hl = headline(text, 0.86 * can["left"], 0.30 * h, CORAL)
        move_to(hl, x=can["left"] / 2, y=0.36 * h)
    else:
        hl = headline(text, 0.86 * w, can["top"] * 0.72, CORAL)
        move_to(hl, x=w / 2, y=can["top"] / 2)
    ps("addDropShadowLayerStyle", layerId=hl, blendMode="MULTIPLY", color=ESPRESSO, opacity=35, angle=120, distance=4, spread=0, size=10)
    path = f"{OUT}/{w}x{h}{suffix}.png"
    ps("saveDocumentAs", 120, filePath=path, fileType="PNG")
    print(f"{w}x{h} ok ({time.time() - t0:.0f}s) -> {path}", flush=True)


if __name__ == "__main__":
    # headline words may arrive split (shell quoting); anything shaped WxH is a size, the rest is the headline
    import re
    argv = sys.argv[1:]
    suffix = ""
    if "--suffix" in argv:                  # e.g. --suffix es -> 1080x1080-es.png (Spanish variant)
        i = argv.index("--suffix")
        suffix = "-" + argv[i + 1]
        del argv[i:i + 2]
    size_args = [a for a in argv if re.fullmatch(r"\d+x\d+", a.lower())]
    text = " ".join(a for a in argv if a not in size_args).strip().strip('"') or "ICE, MIAMI."
    sizes = [tuple(int(v) for v in a.lower().split("x")) for a in size_args] or SIZES
    os.makedirs(OUT, exist_ok=True)
    start = time.time()
    for w, h in sizes:
        try:
            build(text, w, h, suffix)
        except Exception as e:
            print(f"{w}x{h} FAILED: {e}", flush=True)
    print(f"done: {len(sizes)} sizes in {time.time() - start:.0f}s")
