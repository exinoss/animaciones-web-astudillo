"""Animación "Marca la 6" (v2, compacta): la mano tacha con plumón azul la línea negra de la casilla.
Se muestra pequeña debajo del botón del header. Segmentos "marcar" y "salir", fondo transparente."""
import json
from pathlib import Path
import lottie_helpers as H
from lottie_helpers import st, anim, group, fill, lgrad, stroke, rect, bezier_shapes, layer, hexc

HERE = Path(__file__).resolve().parent / "fuentes"
OUT = Path(__file__).resolve().parents[1] / "marca_vota6" / "glaxnimate"
OUT.mkdir(parents=True, exist_ok=True)

W, HGT = 240, 200
FPS, DUR = 60, 56          # 0.93 s
H.DUR = DUR
MARK_END = 44              # fin del segmento "marcar" (0.73 s)

R, B, INK = "#E82128", "#004EA1", "#1D2433"
OUT_BACK = (.2, .9, .3, 1.25)
SMOOTH = (.4, 0, .2, 1)
DRAW = (.45, 0, .25, 1)
EXIT = (.5, 0, .9, .6)

lock = json.loads((HERE / "trace_lockup.json").read_text())
hand = json.loads((HERE / "hand.json").read_text())


def trx(a=(0, 0), p=(0, 0), s=(100, 100), o=100, r=0):
    v = lambda x: x if isinstance(x, dict) else st(list(x) if isinstance(x, tuple) else x)
    return {"ty": "tr", "a": v(a), "p": v(p), "s": v(s), "r": v(r), "o": v(o), "sk": st(0), "sa": st(0)}


def evenodd(f):
    f["r"] = 2
    return f


def cubic_ease(e, x):
    x1, y1, x2, y2 = e
    lo, hi = 0.0, 1.0
    for _ in range(40):
        t = (lo + hi) / 2
        bx = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3
        lo, hi = (t, hi) if bx < x else (lo, t)
    return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3


def line_sh(p0, p1, bow=0.0):
    """Trazo casi recto con una leve curva (bow en px) para que parezca hecho a mano."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = (dx * dx + dy * dy) ** .5
    px, py = -dy / n * bow, dx / n * bow
    c1 = (dx / 3 + px, dy / 3 + py)
    c2 = (-dx / 3 + px, -dy / 3 + py)
    return {"ty": "sh", "ks": st({"v": [list(p0), list(p1)], "o": [list(c1), [0, 0]], "i": [[0, 0], list(c2)], "c": False})}


def point_on(p0, p1, bow, t):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = (dx * dx + dy * dy) ** .5
    px, py = -dy / n * bow, dx / n * bow
    pts = [p0, (p0[0] + dx / 3 + px, p0[1] + dy / 3 + py), (p0[0] + 2 * dx / 3 + px, p0[1] + 2 * dy / 3 + py), p1]
    u = 1 - t
    return [u**3 * pts[0][i] + 3 * u * u * t * pts[1][i] + 3 * u * t * t * pts[2][i] + t**3 * pts[3][i] for i in (0, 1)]


# ---------- geometría ----------
CX = 120
CARD = (CX, 95, 160, 130)            # centro x, centro y, ancho, alto  -> y 30..160
BAND_Y, BAND_H = 55, 50               # franja 30..80
BOX = (CX, 121, 124, 48)              # casilla 97..145
LINE0, LINE1 = (88, 122), (152, 122)  # línea negra impresa
STRK0, STRK1, BOW = (122, 104), (118, 140), 2     # raya vertical que cruza la línea negra
S0, S1 = 14, 30                        # fotogramas del tachado

# ---------- mano (punta del plumón sigue el trazo) ----------
TIP = (15.6, 112.6)
HS = 55                                # escala de la mano (%)
follow = [(f, point_on(STRK0, STRK1, BOW, cubic_ease(DRAW, (f - S0) / (S1 - S0))), (0, 0, 1, 1))
          for f in range(S0, S1, 2)]
hand_pos = [(0, [250, 215], (.25, .6, .3, 1))] + follow + [(S1, list(STRK1), EXIT), (MARK_END, [262, 232], None)]
mano = group("Mano", [group(f"Mano {i}", [*bezier_shapes(d), fill(c)]) for i, (c, d) in reversed(list(enumerate(hand)))],
             trx(a=TIP, p=anim(hand_pos, dims=2), s=(HS, HS),
                 r=anim([(0, 10, (.25, .6, .3, 1)), (S0, -4, (0, 0, 1, 1)), (S1, 4, EXIT), (MARK_END, 12, None)])))

# ---------- tachado azul ----------
trim = {"ty": "tm", "s": st(0), "o": st(0), "m": 1, "e": anim([(0, 0, "hold"), (S0, 0, DRAW), (S1, 100, None)])}
tachado = group("Tachado", [line_sh(STRK0, STRK1, BOW), trim, stroke(B, 7), stroke("#FFFFFF", 11)],
                trx(a=(CX, 121), p=(CX, 121),
                    s=anim([(0, [100, 100], "hold"), (S1, [100, 100], SMOOTH), (35, [125, 104], SMOOTH), (40, [100, 100], None)], dims=2)))

# ---------- casilla ----------
borde = {"ty": "st", "o": st(100), "w": st(2.5), "lc": 2, "lj": 2, "ml": 4,
         "c": anim([(0, hexc("#C9CED6"), "hold"), (S1, hexc("#C9CED6"), SMOOTH), (38, hexc(B), None)], dims=4)}
casilla = group("Casilla", [
    group("Línea impresa", [line_sh(LINE0, LINE1), stroke(INK, 3)]),
    group("Recuadro", [rect(*BOX, 10), borde, fill("#FFFFFF")]),
])

# ---------- franja con "Somos la 6" ----------
SL = .36
lockup = group("Somos la 6", [
    group("Azul", [*bezier_shapes(lock["blue"]), evenodd(lgrad((0, 50), (0, 108), "#0A58B0", "#003A80"))]),
    group("Pliegues", [*bezier_shapes(lock["shade"]), evenodd(lgrad((0, 10), (0, 70), "#A8141B", "#D41E26"))]),
    group("Rojo", [*bezier_shapes(lock["red"]), evenodd(fill(R))]),
], trx(p=(CX - 191 * SL / 2, BAND_Y - 108 * SL / 2), s=(SL * 100, SL * 100)))

cx, cy, cw, ch = CARD
top = cy - ch / 2
papeleta = group("Papeleta", [
    mano,
    tachado,
    casilla,
    lockup,
    group("Franja", [rect(cx, top + BAND_H / 2, cw, BAND_H, 12), rect(cx, top + BAND_H - 8, cw, 16), fill("#FEBF12")]),
    group("Hoja", [rect(cx, cy, cw, ch, 12), fill("#FFFFFF")]),
    group("Sombra", [rect(cx + 2, cy + 5, cw + 4, ch + 4, 14), fill("#000000", 13)]),
], trx(a=(cx, cy), p=(cx, cy),   # centrada y sin giro: entra con zoom + fundido
       s=anim([(0, [85, 85], OUT_BACK), (12, [100, 100], "hold"), (MARK_END, [100, 100], EXIT), (DUR, [92, 92], None)], dims=2),
       o=anim([(0, 0, SMOOTH), (7, 100, "hold"), (MARK_END, 100, EXIT), (DUR, 0, None)])))

data = {"v": "5.7.0", "fr": FPS, "ip": 0, "op": DUR, "w": W, "h": HGT, "nm": "Marca la 6", "ddd": 0, "assets": [],
        "layers": [layer("Papeleta", 1, [papeleta])],
        "markers": [{"tm": 0, "cm": "marcar", "dr": MARK_END}, {"tm": MARK_END, "cm": "salir", "dr": DUR - MARK_END}]}
(OUT / "marca-vota6.fuente.json").write_text(json.dumps(data), encoding="utf-8")
print("ok", OUT / "marca-vota6.fuente.json")
