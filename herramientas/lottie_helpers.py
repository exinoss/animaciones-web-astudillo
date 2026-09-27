"""Utilidades para construir Lottie a mano (compartidas por los proyectos de Glaxnimate)."""
from svgpathtools import parse_path, CubicBezier, QuadraticBezier, Line

DUR = 180

# ---------- utilidades ----------
def hexc(h, a=1):
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [a]


def st(v):
    return {"a": 0, "k": v}


def ease(x1, y1, x2, y2, dims=1):
    return {"o": {"x": [x1] * dims, "y": [y1] * dims}, "i": {"x": [x2] * dims, "y": [y2] * dims}}


def anim(keys, dims=1):
    """keys: [(frame, value, easing-or-None)]; easing = (x1,y1,x2,y2) o 'hold'."""
    out = []
    for t, v, e in keys:
        k = {"t": t, "s": v if isinstance(v, list) else [v]}
        if e == "hold":
            k["h"] = 1
        elif e:
            k.update(ease(*e, dims=dims))
        out.append(k)
    return {"a": 1, "k": out}


LINEAR = (0, 0, 1, 1)


def tr(a=(0, 0), p=(0, 0), s=None, o=None, r=0):
    return {"ty": "tr", "a": st(list(a)), "p": st(list(p)) if isinstance(p, tuple) else p,
            "s": s if isinstance(s, dict) else st(list(s or (100, 100))),
            "r": st(r), "o": o if isinstance(o, dict) else st(o if o is not None else 100),
            "sk": st(0), "sa": st(0)}


def group(name, items, transform=None):
    return {"ty": "gr", "nm": name, "it": items + [transform or tr()]}


def fill(color, o=100):
    return {"ty": "fl", "c": st(hexc(color)), "o": st(o), "r": 1}


def lgrad(p0, p1, c0, c1):
    a, b = hexc(c0), hexc(c1)
    return {"ty": "gf", "o": st(100), "r": 1, "t": 1, "s": st(list(p0)), "e": st(list(p1)),
            "g": {"p": 2, "k": st([0, *a[:3], 1, *b[:3]])}}


def rgrad(center, radius, c0, c1):
    a, b = hexc(c0), hexc(c1)
    return {"ty": "gf", "o": st(100), "r": 1, "t": 2, "s": st(list(center)),
            "e": st([center[0] + radius, center[1]]), "h": st(0), "a": st(0),
            "g": {"p": 2, "k": st([0, *a[:3], 1, *b[:3]])}}


def stroke(color, w, o=100):
    return {"ty": "st", "c": st(hexc(color)), "o": st(o), "w": st(w), "lc": 2, "lj": 2, "ml": 4}


def rect(cx, cy, w, h, r=0):
    return {"ty": "rc", "p": st([cx, cy]), "s": st([w, h]), "r": st(r), "d": 1}


def ellipse(cx, cy, w, h):
    return {"ty": "el", "p": st([cx, cy]), "s": st([w, h]), "d": 1}


def bezier_shapes(d):
    """Convierte un atributo d de SVG en uno o varios shapes 'sh' de Lottie."""
    shapes = []
    for sub in parse_path(d).continuous_subpaths():
        segs = list(sub)
        closed = abs(segs[-1].end - segs[0].start) < 1e-3
        v, i, o = [], [], []
        for s in segs:
            if isinstance(s, QuadraticBezier):
                c1 = s.start + 2 / 3 * (s.control - s.start)
                c2 = s.end + 2 / 3 * (s.control - s.end)
            elif isinstance(s, CubicBezier):
                c1, c2 = s.control1, s.control2
            else:
                c1, c2 = s.start, s.end
            v.append([s.start.real, s.start.imag])
            o.append([(c1 - s.start).real, (c1 - s.start).imag])
            i.append(c2 - s.end)  # tangente de entrada del vértice siguiente
        i = i[-1:] + i[:-1]
        i = [[z.real, z.imag] for z in i]
        if not closed:
            v.append([segs[-1].end.real, segs[-1].end.imag]); o.append([0, 0]); i.append([0, 0])
        shapes.append({"ty": "sh", "ks": st({"i": i, "o": o, "v": v, "c": closed})})
    return shapes


def poly(points):
    return {"ty": "sh", "ks": st({"i": [[0, 0]] * len(points), "o": [[0, 0]] * len(points),
                                  "v": [list(p) for p in points], "c": True})}


def layer(name, ind, shapes, masks=None):
    L = {"ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1, "ao": 0, "bm": 0,
         "ks": {"o": st(100), "r": st(0), "p": st([0, 0, 0]), "a": st([0, 0, 0]), "s": st([100, 100, 100])},
         "shapes": shapes, "ip": 0, "op": DUR, "st": 0}
    if masks:
        L["hasMask"] = True
        L["masksProperties"] = masks
    return L


