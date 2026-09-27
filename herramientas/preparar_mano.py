"""Aplana los clipPath del emoji Noto ✍🏽 (Apache 2.0) en trazados simples y recolorea el lápiz con la paleta."""
import json, re
import xml.etree.ElementTree as ET
from pathlib import Path
import pathops
from fontTools.svgLib.path import parse_path
from fontTools.pens.svgPathPen import SVGPathPen

HERE = Path(__file__).resolve().parent / "fuentes"
SRC = HERE / "emoji_u270d_1f3fd.svg"
NS = {"s": "http://www.w3.org/2000/svg"}
RECOLOR = {"#78909C": "#004EA1", "#82AEC0": "#5B9BE0"}  # lápiz en azul de marca


def to_skia(d):
    p = pathops.Path()
    parse_path(d, p.getPen())
    return p


def to_d(p):
    pen = SVGPathPen(None)
    p.draw(pen)
    return pen.getCommands()


def fill_of(el):
    m = re.search(r"fill:(#[0-9A-Fa-f]{6})", el.get("style", ""))
    return m.group(1).upper() if m else None


root = ET.parse(SRC).getroot()
defs = {el.get("id"): el.get("d") for el in root.iter("{http://www.w3.org/2000/svg}path") if el.get("id")}
shapes = []
for child in root:
    tag = child.tag.split("}")[1]
    if tag == "path":
        shapes.append((fill_of(child), child.get("d")))
    elif tag == "g":
        clip_d = next(el.get("d") for el in child.iter("{http://www.w3.org/2000/svg}path") if el.get("id"))
        clip = to_skia(clip_d)
        for el in child.iter("{http://www.w3.org/2000/svg}path"):
            if el.get("id"):
                continue
            res = pathops.op(to_skia(el.get("d")), clip, pathops.PathOp.INTERSECTION)
            shapes.append((fill_of(el), to_d(res)))

shapes = [(RECOLOR.get(c, c), d) for c, d in shapes if d]
json.dump(shapes, open(HERE / "hand.json", "w"))
svg = "".join(f'<path fill="{c}" d="{d}"/>' for c, d in shapes)
(HERE / "hand_flat.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="384" height="384"><rect width="128" height="128" fill="#fff"/>{svg}'
    f'<circle cx="15.6" cy="112.6" r="1.5" fill="red"/></svg>')
print(len(shapes), [c for c, _ in shapes])
