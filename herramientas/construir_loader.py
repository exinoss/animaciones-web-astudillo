"""Construye el loader "Vota por la 6" como animación Lottie (capas + keyframes) para abrirla en Glaxnimate."""
import json, re, sys
from pathlib import Path

# Variante: "fondo" (cuadro amarillo, para GIF/redes) o "transparente" (para usar como loading sobre una página)
TRANSP = "transparente" in sys.argv[1:]
NAME = "loader-vota6-transparente" if TRANSP else "loader-vota6"
SHADOW_C, SHADOW_K = ("#1D2433", .35) if TRANSP else ("#C98A00", 1)   # color y factor de opacidad de sombras
SPARK_C = "#E82128" if TRANSP else "#FFFFFF"
from svgpathtools import parse_path, CubicBezier, QuadraticBezier, Line

HERE = Path(__file__).resolve().parent / "fuentes"
OUT = Path(__file__).resolve().parents[1] / "loading_vote" / "glaxnimate"
OUT.mkdir(parents=True, exist_ok=True)

FPS, DUR = 60, 210  # 3.5 s
F = lambda pct: round(pct / 100 * 180)  # porcentajes sobre la línea de tiempo original de 3 s
POST = 24                               # desplazamiento de todo lo que ocurre después del rayón

six = json.loads((HERE / "trace6.json").read_text())
vota_d = re.search(r'\sd="([^"]+)"', (HERE / "lista_p.svg").read_text()).group(1)


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


# ---------- paleta oficial ----------
Y, R, B = "#FEBF12", "#E82128", "#004EA1"

# Curvas (equivalentes a cubic-bezier CSS)
OUT_BACK = (.2, .9, .3, 1.25)
POP = (.2, .9, .3, 1.5)
SMOOTH = (.3, 0, .4, 1)
DROP = (.6, 0, .95, .5)
SQUASH = (.3, 0, .5, 1)

# ---------- capa: Fondo ----------
fondo = layer("Fondo", 6, [group("Fondo", [rect(120, 120, 240, 240), rgrad((120, 84), 170, "#FFD24D", Y)])])

# ---------- capa: Urna (aplasta y rebota desde la base) ----------
urna_items = [
    group("Texto LISTA 6", [
        group("6", [*[s for s in bezier_shapes(vota_d) if min(v[0] for v in s["ks"]["k"]["v"]) > 59], fill(R)]),
        group("LISTA", [*[s for s in bezier_shapes(vota_d) if min(v[0] for v in s["ks"]["k"]["v"]) <= 59], fill(B)]),
    ], tr(p=(120 - 40.62, 178 - 35.35))),
    group("Etiqueta", [rect(120, 178, 84, 24, 12), fill("#FFFFFF")]),
    group("Ranura", [rect(120, 140, 76, 6, 3), fill("#00224D")]),
    group("Borde tapa", [rect(120, 151, 130, 10, 5), fill("#0B4E9C")]),
    group("Tapa", [poly([(72, 134), (168, 134), (181, 148), (59, 148)]), stroke("#2468BD", 4), lgrad((0, 134), (0, 148), "#3A82D6", "#2468BD")]),
    group("Sombra interna", [rect(120, 155, 120, 6), fill("#003A80", 50)]),
    group("Cuerpo", [rect(120, 181, 120, 58, 10), lgrad((0, 152), (0, 210), "#0B5BB5", B)]),
    group("Sombra suelo", [ellipse(120, 210, 132, 12), fill(SHADOW_C, 45 * SHADOW_K)]),
]
urna = layer("Urna", 3, [group("Urna", urna_items, tr(
    a=(120, 208), p=(120, 208),
    s=anim([(F(0), [100, 100], "hold"), (F(72) + POST, [100, 100], SQUASH), (F(77) + POST, [105, 93], SQUASH),
            (F(83) + POST, [98, 103], SQUASH), (F(90) + POST, [100, 100], None)], dims=2)))])

# ---------- capa: Destellos ----------
rayos = [((92, 118), (84, 108)), ((106, 108), (103, 96)), ((120, 105), (120, 92)), ((134, 108), (137, 96)), ((148, 118), (156, 108))]
destellos = layer("Destellos", 2, [group("Destellos", [
    *[{"ty": "sh", "ks": st({"i": [[0, 0]] * 2, "o": [[0, 0]] * 2, "v": [list(a), list(b)], "c": False})} for a, b in rayos],
    stroke(SPARK_C, 4),
], tr(a=(120, 140), p=(120, 140),
      s=anim([(F(0), [55, 55], "hold"), (F(74) + POST, [55, 55], (.15, .8, .3, 1)), (F(94) + POST, [115, 115], None)], dims=2),
      o=anim([(F(0), 0, "hold"), (F(74) + POST, 0, LINEAR), (F(78) + POST, 100, LINEAR), (F(94) + POST, 0, None)])))])

# ---------- capa: Papeleta (la capa es fija; el grupo interno se mueve y la máscara recorta en la ranura) ----------
S = 0.37
seis = group("Seis", [
    group("Azul", [*[s for d in six["blue"] for s in bezier_shapes(d)], lgrad((0, 80), (0, 167), "#0A58B0", "#003A80")],
          tr(a=(128, 122), p=(128, 122),
             s=anim([(F(0), [0, 0], "hold"), (F(26), [0, 0], POP), (F(38), [100, 100], None)], dims=2))),
    group("Pliegues", [*[s for d in six["shade"] for s in bezier_shapes(d)], lgrad((0, 27), (0, 115), "#A8141B", "#D41E26")],
          tr(o=anim([(F(0), 0, "hold"), (F(22), 0, SMOOTH), (F(32), 100, None)]))),
    group("Cinta roja", [*[s for d in six["red"] for s in bezier_shapes(d)], fill(R)],
          tr(a=(96, 96), p=(96, 96), r=0,
             s=anim([(F(0), [60, 60], "hold"), (F(12), [60, 60], OUT_BACK), (F(26), [100, 100], None)], dims=2),
             o=anim([(F(0), 0, "hold"), (F(12), 0, SMOOTH), (F(20), 100, None)]))),
], tr(p=(120 - 100 * S, 86 - 96.5 * S), s=(S * 100, S * 100)))

# ---------- papeleta en dos tarjetas: se despliega, se raya y se dobla ----------
hand = json.loads((HERE / "hand.json").read_text())
INK = "#1D2433"
DRAW = (.45, 0, .25, 1)
OPEN0, OPEN1 = 64, 78      # se desliza a la izquierda y se despliega la tarjeta derecha
HAND_IN = 72               # la mano empieza a acercarse
S0, S1 = 84, 108           # rayón vertical (0.4 s)
HAND_OUT0, HAND_OUT1 = 116, 128   # la mano se queda un momento y se va
FOLD0, FOLD1 = 124, 136    # la tarjeta derecha se dobla sobre la del 6 y vuelve al centro


def trx(a=(0, 0), p=(0, 0), s=(100, 100), o=100, r=0):
    v = lambda x: x if isinstance(x, dict) else st(list(x) if isinstance(x, tuple) else x)
    return {"ty": "tr", "a": v(a), "p": v(p), "s": v(s), "r": v(r), "o": v(o), "sk": st(0), "sa": st(0)}


def cubic_ease(e, x):
    x1, y1, x2, y2 = e
    lo, hi = 0.0, 1.0
    for _ in range(40):
        t = (lo + hi) / 2
        bx = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3
        lo, hi = (t, hi) if bx < x else (lo, t)
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3


def seg(p0, p1, bow=0.0):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = (dx * dx + dy * dy) ** .5
    px, py = -dy / n * bow, dx / n * bow
    ctrl = [p0, (p0[0] + dx / 3 + px, p0[1] + dy / 3 + py), (p0[0] + 2 * dx / 3 + px, p0[1] + 2 * dy / 3 + py), p1]
    shape = {"ty": "sh", "ks": st({"v": [list(p0), list(p1)], "c": False,
                                   "o": [[ctrl[1][0] - p0[0], ctrl[1][1] - p0[1]], [0, 0]],
                                   "i": [[0, 0], [ctrl[2][0] - p1[0], ctrl[2][1] - p1[1]]]})}
    at = lambda t: [sum(c * q[i] for c, q in zip(((1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3), ctrl)) for i in (0, 1)]
    return shape, at


# Tarjeta derecha (coordenadas base: x 152..216, y 38..122; pliegue en x=152)
BOXC = (184, 82)
line_sh, _ = seg((173, 82), (195, 82))
strk_sh, strk_at = seg((184.8, 69), (183.2, 95), 1)
trim = {"ty": "tm", "s": st(0), "o": st(0), "m": 1, "e": anim([(0, 0, "hold"), (S0, 0, DRAW), (S1, 100, None)])}
borde = {"ty": "st", "o": st(100), "w": st(2), "lc": 2, "lj": 2, "ml": 4,
         "c": anim([(0, hexc("#C9CED6"), "hold"), (S1, hexc("#C9CED6"), SMOOTH), (S1 + 6, hexc(B), None)], dims=4)}
tarjeta_der = group("Tarjeta casilla", [
    group("Rayón", [strk_sh, trim, stroke(B, 4.5), stroke("#FFFFFF", 7.5)]),
    group("Línea impresa", [line_sh, stroke(INK, 2.2)]),
    group("Casilla", [rect(*BOXC, 46, 34, 7), borde, fill("#FFFFFF")]),
    group("Pliegue", [seg((152.5, 40), (152.5, 120))[0], stroke("#E3E6EA", 1)]),
    group("Hoja", [rect(184, 80, 64, 84, 7), rect(158, 80, 12, 84), fill("#FFFFFF")]),
    group("Sombra", [rect(187, 84, 64, 84, 7), rect(161, 84, 12, 84), fill(SHADOW_C, 35 * SHADOW_K)]),
], trx(a=(152, 80), p=(152, 80),
       s=anim([(0, [0, 100], "hold"), (OPEN0, [0, 100], SMOOTH), (OPEN1, [100, 100], "hold"),
               (FOLD0, [100, 100], SMOOTH), (FOLD1, [0, 100], None)], dims=2)))

# Esquinas rectas del lado derecho de la tarjeta del 6 solo mientras está abierta
union = group("Unión", [rect(146, 80, 12, 84), fill("#FFFFFF")],
              trx(o=anim([(0, 0, "hold"), (OPEN0, 0, "hold"), (OPEN0 + 1, 100, "hold"), (FOLD1 - 1, 100, "hold"), (FOLD1, 0, None)])))

# Mano (misma ilustración que la transición del header): la punta sigue el rayón
TIP = (15.6, 112.6)
follow = [(f, strk_at(cubic_ease(DRAW, (f - S0) / (S1 - S0))), (0, 0, 1, 1)) for f in range(S0, S1, 2)]
hand_pos = [(0, [268, 96], "hold"), (HAND_IN, [268, 96], (.25, .6, .3, 1))] + follow + \
           [(S1, strk_at(1), SMOOTH), (HAND_OUT0, [strk_at(1)[0] + 3, strk_at(1)[1] + 2], EXIT_H := (.5, 0, .9, .6)),
            (HAND_OUT1, [270, 58], None)]
mano = group("Mano", [group(f"Mano {i}", [*bezier_shapes(d), fill(c)]) for i, (c, d) in reversed(list(enumerate(hand)))],
             trx(a=TIP, p=anim(hand_pos, dims=2), s=(40, 40),
                 r=anim([(0, 10, "hold"), (HAND_IN, 10, (.25, .6, .3, 1)), (S0, -4, (0, 0, 1, 1)), (S1, 4, SMOOTH),
                         (HAND_OUT0, 6, EXIT_H), (HAND_OUT1, 12, None)])))

papeleta_grp = group("Papeleta", [
    group("Abierta", [
        mano,
        tarjeta_der,
        union,
        seis,
        group("Hoja", [rect(120, 80, 64, 84, 7), fill("#FFFFFF")]),
        group("Sombra hoja", [rect(123, 84, 64, 84, 7), fill(SHADOW_C, 35 * SHADOW_K)]),
    ], trx(p=anim([(0, [0, 0], "hold"), (OPEN0, [0, 0], SMOOTH), (OPEN1, [-32, 0], "hold"),
                   (FOLD0, [-32, 0], SMOOTH), (FOLD1, [0, 0], None)], dims=2))),
], tr(
    p=anim([(F(0), [0, -26], OUT_BACK), (F(10), [0, 0], "hold"), (FOLD1, [0, 0], SMOOTH),
            (FOLD1 + 5, [0, -9], DROP), (F(74) + POST, [0, 112], None)], dims=2),
    o=anim([(F(0), 0, SMOOTH), (F(10), 100, "hold"), (F(74) + POST, 100, "hold"), (F(74) + POST + 1, 0, None)])))

ranura_mask = {"inv": False, "mode": "a", "nm": "Ranura", "x": st(0), "o": st(100),
               "pt": st({"i": [[0, 0]] * 4, "o": [[0, 0]] * 4, "v": [[0, 0], [240, 0], [240, 140], [0, 140]], "c": True})}
papeleta = layer("Papeleta", 1, [papeleta_grp], masks=[ranura_mask])

anim_json = {"v": "5.7.0", "fr": FPS, "ip": 0, "op": DUR, "w": 240, "h": 240, "nm": "Loader Vota 6", "ddd": 0,
             "assets": [], "layers": [papeleta, destellos, urna] + ([] if TRANSP else [fondo])}
(OUT / f"{NAME}.fuente.json").write_text(json.dumps(anim_json), encoding="utf-8")
print("ok", OUT / f"{NAME}.fuente.json")
