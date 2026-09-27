"""Vectoriza el 6 de cinta (rojo + azul) del favicon en paths suaves."""
import numpy as np
from PIL import Image, ImageFilter
from skimage import measure

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "resources" / "favicon.jpg"
DEST = ROOT / "herramientas" / "fuentes" / "trace6.json"
UP = 8  # factor de escalado antes de trazar

img = Image.open(SRC).convert("RGB")
W, H = img.size
big = np.asarray(img.resize((W * UP, H * UP), Image.LANCZOS)).astype(float)
r, g, b = big[..., 0], big[..., 1], big[..., 2]

masks = {
    "red": (r > 150) & (g < 110) & (b < 110),
    "blue": (b > 110) & (r < 90),
    # caras interiores de la cinta (rojo sombreado)
    "shade": (r > 120) & (r < 218) & (g < 90) & (b < 90),
}


def smooth_mask(m):
    im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(UP * 1.4))
    return np.asarray(im).astype(float) / 255


def catmull_to_bezier(pts):
    n = len(pts)
    d = f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = p1 + (p2 - p0) / 6
        c2 = p2 - (p3 - p1) / 6
        d += f"C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
    return d + "Z"


out = {}
for name, m in masks.items():
    sm = smooth_mask(m)
    paths = []
    for c in measure.find_contours(np.pad(sm, 2), 0.5):
        c = c - 2
        if len(c) < 25 * UP:
            continue
        poly = measure.approximate_polygon(c, tolerance=0.9 * UP)[:-1]
        pts = np.array([[p[1] / UP, p[0] / UP] for p in poly])  # (x, y) en px del favicon
        paths.append(catmull_to_bezier(pts))
    out[name] = paths
    print(name, len(paths), [len(p) for p in paths])

import json
json.dump({"size": [W, H], **out}, open(DEST, "w"))
