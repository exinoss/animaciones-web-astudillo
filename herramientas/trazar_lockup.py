"""Vectoriza el lockup "Somos la 6" (resources/somos6.png) por colores, conservando huecos (el "la" amarillo)."""
import json
import numpy as np
from PIL import Image, ImageFilter
from skimage import measure

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "resources" / "somos6.png"
DEST = ROOT / "herramientas" / "fuentes" / "trace_lockup.json"
UP = 8

img = Image.open(SRC).convert("RGB")
W, H = img.size
big = np.asarray(img.resize((W * UP, H * UP), Image.LANCZOS)).astype(float)
r, g, b = big[..., 0], big[..., 1], big[..., 2]

redish = (r > 110) & (g < 110) & (b < 110)
masks = {
    # rojo frontal + rojo sombreado juntos: el sombreado se dibuja encima
    "red": redish,
    "shade": redish & (r < 196),
    "blue": (b > 100) & (r < 110),
}
SETTINGS = {"red": (0.55, 0.30), "shade": (1.0, 0.6), "blue": (1.0, 0.6)}  # (blur, tolerancia) en px originales


def catmull(pts):
    n = len(pts)
    d = f"M{pts[0][0]:.2f} {pts[0][1]:.2f}"
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1, c2 = p1 + (p2 - p0) / 6, p2 - (p3 - p1) / 6
        d += f"C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
    return d + "Z"


out = {"size": [W, H]}
for name, m in masks.items():
    blur, tol = SETTINGS[name]
    sm = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(UP * blur))) / 255
    ds = []
    for c in measure.find_contours(np.pad(sm, 2), 0.5):
        c = c - 2
        if len(c) < 6 * UP:
            continue
        poly = measure.approximate_polygon(c, tolerance=tol * UP)[:-1]
        if len(poly) < 4:
            continue
        ds.append(catmull(np.array([[p[1] / UP, p[0] / UP] for p in poly])))
    out[name] = " ".join(ds)  # un solo path por color; huecos con evenodd
    print(name, len(ds))

json.dump(out, open(DEST, "w"))
