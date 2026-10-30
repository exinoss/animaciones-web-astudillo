"""Velero "Carlos Astudillo" animado como transición: entra navegando, se mece sobre el agua y sale navegando.

El diseño NO se toca: formas, colores y degradados se leen de resources/carlos-astudillo.svg. Lo único que se añade
es el relleno blanco del hueco de la vela mayor (en el SVG es transparente). En reposo el velero es idéntico al SVG.
- El barco cabecea y sube y baja (bucle de 3 s).
- La bandera ondea suavemente y el 6, sin deformarse, sigue a la tela.
- Las velas se hinchan con el viento: se deforman solo por el borde libre; los bordes sujetos (mástil y botavara)
  no se mueven, así que nunca se separan del mástil.
Marcadores Lottie: "entrar" (0-45), "bucle" (45-225) y "salir" (225-270). En los fotogramas 45, 135 y 225 el
velero está en reposo: desde ahí se puede pasar a "salir" sin salto."""
import json, math
import xml.etree.ElementTree as ET
from pathlib import Path
from svgpathtools import parse_path, CubicBezier, QuadraticBezier, Line
import lottie_helpers as H
from lottie_helpers import st, anim, group, layer, hexc, ellipse, LINEAR

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "resources" / "carlos-astudillo.svg"
OUT = ROOT / "barco_transicion" / "glaxnimate"
OUT.mkdir(parents=True, exist_ok=True)

FPS = 60
ENTRAR, BUCLE, SALIR = 45, 180, 45           # 0.75 s + 3 s + 0.75 s
DUR = ENTRAR + BUCLE + SALIR
H.DUR = DUR
LADO = 320                                    # lienzo 320×320 (el SVG es 1254×1254)
ESCALA = LADO / 1254
SENO = (.37, 0, .63, 1)                       # ease-in-out sine: une dos extremos de un vaivén senoidal

# ---------- lectura del SVG ----------
NS = "{http://www.w3.org/2000/svg}"
raiz = ET.parse(SRC).getroot()
assert raiz.get("viewBox") == "0 0 1254 1254"
por_id = {el.get("id"): el for el in raiz.iter() if el.get("id")}
degradados = {}
for g in raiz.iter(f"{NS}linearGradient"):
    paradas = [(float(s.get("offset", 0)), s.get("stop-color")) for s in g.iter(f"{NS}stop")]
    degradados[g.get("id")] = ([float(g.get(k)) for k in ("x1", "y1", "x2", "y2")], paradas)


def ruta(id_):
    el = por_id[id_]
    return el.get("d") if el.tag == f"{NS}path" else next(el.iter(f"{NS}path")).get("d")


def rgba(c):
    """#rgb o #rrggbb -> [r, g, b, a] de Lottie."""
    c = c.lstrip("#")
    return hexc("".join(x * 2 for x in c) if len(c) == 3 else c)


def relleno(id_):
    """Relleno de Lottie (plano o degradado) igual al del elemento del SVG, con su regla de relleno."""
    el = por_id[id_]
    color, regla = el.get("fill"), 2 if el.get("fill-rule") == "evenodd" else 1
    if color.startswith("url(#"):
        return degradado(color[5:-1], regla)
    return {"ty": "fl", "c": st(rgba(color)), "o": st(100), "r": regla}


def degradado(id_, regla=1, trazo=None):
    (x1, y1, x2, y2), paradas = degradados[id_]
    g = {"p": len(paradas), "k": st([v for o, c in paradas for v in (o, *rgba(c)[:3])])}
    base = {"o": st(100), "s": st([x1, y1]), "e": st([x2, y2]), "t": 1, "g": g}
    if trazo is None:
        return {"ty": "gf", "r": regla, **base}
    return {"ty": "gs", "w": st(trazo), "lc": 1, "lj": 2, "ml": 4, **base}


# ---------- trazados: segmentos cúbicos absolutos, para poder deformarlos ----------
def segmentos(d, partir=None):
    """Subtrayectos del SVG como [(p0, c1, c2, p1), ...] + cerrado. Las rectas con `partir(recta)` = n se
    dividen en n tramos (en reposo siguen siendo la misma recta) para que puedan curvarse al deformarlas."""
    for sub in parse_path(d).continuous_subpaths():
        segs = []
        for s in sub:
            if isinstance(s, CubicBezier):
                segs.append((s.start, s.control1, s.control2, s.end))
            elif isinstance(s, QuadraticBezier):
                segs.append((s.start, s.start + 2 / 3 * (s.control - s.start), s.end + 2 / 3 * (s.control - s.end), s.end))
            else:
                n = partir(s) if partir else 1
                for k in range(n):
                    a, b = s.start + (s.end - s.start) * k / n, s.start + (s.end - s.start) * (k + 1) / n
                    segs.append((a, a + (b - a) / 3, a + 2 * (b - a) / 3, b))
        yield segs, abs(segs[-1][3] - segs[0][0]) < 1e-3


def forma(segs, cerrado, deforma=lambda p: p):
    """Shape de Lottie a partir de segmentos absolutos, aplicando `deforma` a vértices y puntos de control."""
    v = [deforma(s[0]) for s in segs]
    o = [deforma(s[1]) - deforma(s[0]) for s in segs]
    entra = [deforma(s[2]) - deforma(s[3]) for s in segs]          # tangente de entrada del vértice siguiente
    if cerrado:
        i = entra[-1:] + entra[:-1]
    else:
        v.append(deforma(segs[-1][3])); o.append(0j); i = [0j] + entra
    xy = lambda zs: [[z.real, z.imag] for z in zs]
    return {"v": xy(v), "i": xy(i), "o": xy(o), "c": cerrado}


def ciclo(f):
    """Tiempo del bucle en fotogramas: 0 al empezar el bucle (fotograma 45). Todo el movimiento es periódico."""
    return f - ENTRAR


def fotogramas(paso):
    """Fotogramas de muestreo: siempre incluyen 45, 135, 225 (reposo) y el último."""
    assert ENTRAR % paso == 0 and BUCLE % (2 * paso) == 0
    return list(range(0, DUR + 1, paso))


# Lo que oscila como un seno entre dos extremos se anima con keyframes solo en los extremos y la curva SENO
# (exacto salvo < 1 %); lo demás se muestrea con keyframes lineales.
def claves(fs, valor, curva=LINEAR):
    return anim([(f, valor(f), None if f == DUR else curva) for f in fs], dims=len(valor(0)) if isinstance(valor(0), list) else 1)


def animada(segs, cerrado, campo, fs, curva=LINEAR):
    """Shape animado: en cada fotograma de `fs` se deforma con campo(p, f)."""
    return {"ty": "sh", "ks": claves(fs, lambda f: forma(segs, cerrado, lambda p: campo(p, f)), curva)}


def fija(segs, cerrado):
    return {"ty": "sh", "ks": st(forma(segs, cerrado))}


# ---------- bandera: ondea; sujeta al mástil por su borde izquierdo ----------
ASTA0, ASTA1 = 650 + 157j, 691 + 388j          # borde de la bandera pegado al mástil
ONDA_A, ONDA_L, ONDA_T = 18, 420, 90           # amplitud (unidades del SVG), longitud de onda, periodo (1.5 s)
_dir = (ASTA1 - ASTA0) / abs(ASTA1 - ASTA0)


def lejos_del_asta(p):
    """Distancia (con signo) de p al borde de la bandera pegado al mástil; positiva hacia la punta."""
    return -((p - ASTA0) * _dir.conjugate()).imag


LARGO = lejos_del_asta(1115 + 255j)


def ondea(p, f):
    """Desplazamiento vertical de la tela: onda que viaja hacia la punta, nula junto al mástil y en reposo
    (fotogramas 45, 135 y 225), más amplia cuanto más lejos del mástil."""
    s = max(0, lejos_del_asta(p))
    w = min(1, s / LARGO) ** 1.3
    k, fase = 2 * math.pi / ONDA_L, 2 * math.pi * ciclo(f) / ONDA_T
    return ONDA_A * w * (math.sin(k * s - fase) - math.sin(k * s))


def bandera_campo(p, f):
    return p + 1j * ondea(p, f)


SEIS_C = 826 + 290j                             # centro del 6


def seis_pos(f):
    return [SEIS_C.real, SEIS_C.imag + ondea(SEIS_C, f)]


def seis_giro(f):
    """El 6 no se deforma: se inclina como la tela bajo su centro."""
    paso = 20 * (-1j * _dir)                    # hacia la punta de la bandera
    a, b = SEIS_C - paso, SEIS_C + paso
    pa, pb = bandera_campo(a, f), bandera_campo(b, f)
    return [math.degrees(math.atan2((pb - pa).imag, (pb - pa).real) - math.atan2((b - a).imag, (b - a).real))]


# ---------- velas: se hinchan por el borde libre ----------
def baricentricas(p, a, b, c):
    det = ((b - c).conjugate() * (a - c)).imag
    la = ((b - c).conjugate() * (p - c)).imag / det
    lb = ((c - a).conjugate() * (p - a)).imag / det
    return la, lb, 1 - la - lb


def vela(puno_alto, amura, puno_bajo, hincha):
    """Campo de una vela triangular: los bordes puño alto-amura (mástil) y amura-puño bajo (botavara) no se mueven;
    el borde libre (puño alto-puño bajo) se aleja de la amura hasta `hincha` unidades con cada racha de viento."""
    normal = (puno_bajo - puno_alto) * 1j
    normal /= abs(normal)
    if ((amura - puno_alto) * normal.conjugate()).real > 0:
        normal = -normal

    def peso(p):
        la, _, lc = baricentricas(p, puno_alto, amura, puno_bajo)
        return min(1, 4 * max(0, la) * max(0, lc))

    def campo(p, f):
        racha = math.sin(math.pi * ciclo(f) / ONDA_T) ** 2      # 0 en reposo, 1 en mitad de la racha
        return p + hincha * racha * peso(p) * normal

    return campo, peso


mayor, peso_mayor = vela(616 + 190j, 692 + 850j, 140 + 920j, 24)
menor, peso_menor = vela(695 + 387j, 745 + 835j, 989 + 783j, 18)


def partir_si_se_curva(peso):
    """Divide en tramos de ~180 unidades las rectas cuyo centro se mueve (las que quedan quietas, enteras)."""
    return lambda s: max(1, round(abs(s.end - s.start) / 180)) if peso((s.start + s.end) / 2) > .05 else 1


def pieza_vela(nombre, id_, campo, peso, color=None, d=None):
    # La deformación es lineal en la racha (sin², que va de 0 a 1 y vuelve como un ease-in-out sine): bastan
    # keyframes cada 45 fotogramas, en reposo y con la racha al máximo, unidos con la curva SENO.
    extremos = fotogramas(ONDA_T // 2)          # 0, 45, 90, ...: racha máxima y reposo, alternando
    trazos = [animada(sg, c, campo, extremos, SENO) for sg, c in segmentos(d or ruta(id_), partir_si_se_curva(peso))]
    return group(nombre, trazos + [color or relleno(id_)])


# El hueco de la vela mayor (segundo subtrayecto de "marco-vela-mayor") se rellena de blanco: es lo único que se añade
hueco = ruta("marco-vela-mayor")
hueco = hueco[hueco.index("M", 1):]
assert hueco.startswith("M623 307"), hueco
velas = group("Velas", [
    pieza_vela("Reflejo vela menor", "reflejo-vela-menor", menor, peso_menor),
    pieza_vela("Vela menor", "vela-menor", menor, peso_menor),
    pieza_vela("Vela mayor", "vela-mayor", mayor, peso_mayor),
    pieza_vela("Marco vela mayor", "marco-vela-mayor", mayor, peso_mayor),
    pieza_vela("Hueco blanco", None, mayor, peso_mayor, {"ty": "fl", "c": st(rgba("#FFFFFF")), "o": st(100), "r": 1}, hueco),
])

# La onda de la bandera viaja: se muestrea cada 9 fotogramas (error < 1 unidad del SVG)
bandera = group("Bandera", [animada(sg, c, bandera_campo, fotogramas(9)) for sg, c in segmentos(ruta("bandera"))]
                + [relleno("bandera")])
seis = group("6", [fija(sg, c) for sg, c in segmentos(ruta("lista-6"))] + [relleno("lista-6")],
             H.tr() | {"a": st([SEIS_C.real, SEIS_C.imag]), "p": claves(fotogramas(9), seis_pos),
                       "r": claves(fotogramas(9), seis_giro)})

mastil_bola = next(por_id["mastil"].iter(f"{NS}circle"))
cx, cy, r = (float(mastil_bola.get(k)) for k in ("cx", "cy", "r"))
mastil = group("Mástil", [fija(sg, c) for sg, c in segmentos(ruta("mastil"))] + [ellipse(cx, cy, 2 * r, 2 * r), relleno("mastil")])


def fija_id(nombre, id_):
    return group(nombre, [fija(sg, c) for sg, c in segmentos(ruta(id_))] + [relleno(id_)])


nombre_el = por_id["nombre"]
assert nombre_el.get("paint-order") == "stroke fill" and nombre_el.get("stroke") == nombre_el.get("fill")
nombre = group("Nombre", [fija(sg, c) for sg, c in segmentos(ruta("nombre"))]
               + [relleno("nombre"), degradado(nombre_el.get("stroke")[5:-1], trazo=float(nombre_el.get("stroke-width")))])

# ---------- el barco sobre el agua ----------
PIVOTE = (620, 1030)                            # centro del casco a la altura del agua
CABECEO, OLEAJE = 3, 10                          # grados y unidades del SVG
ENTRA_X, SALE_X = -140, 170                      # llega desde la izquierda y se va por la derecha


def barco_giro(f):
    return [CABECEO * math.sin(2 * math.pi * ciclo(f) / BUCLE)]


def barco_pos(f):
    dx = 0
    if f < ENTRAR:
        dx = ENTRA_X * (1 - f / ENTRAR) ** 3                       # frena al llegar
    elif f > ENTRAR + BUCLE:
        dx = SALE_X * ((f - ENTRAR - BUCLE) / SALIR) ** 3            # acelera al irse
    return [PIVOTE[0] + dx, PIVOTE[1] + OLEAJE * math.sin(2 * math.pi * ciclo(f) / (BUCLE / 2))]


def barco_opacidad(f):
    entra, sale = min(1, f / FUNDIDO), min(1, (DUR - f) / FUNDIDO)
    return [100 * (3 * min(entra, sale) ** 2 - 2 * min(entra, sale) ** 3)]


CABECEO_EXTREMOS = [ENTRAR - BUCLE // 4 + k * BUCLE // 2 for k in range(4)]   # -3°, +3°, -3°, +3°; pasa por 0 en el reposo
assert all(abs(abs(barco_giro(f)[0]) - CABECEO) < 1e-9 for f in CABECEO_EXTREMOS)
# Posición: muestreo denso al entrar y salir (frenada y arrancada), espaciado en el bucle (solo el oleaje)
POSICION = sorted(set(range(0, ENTRAR, 3)) | set(range(ENTRAR, ENTRAR + BUCLE, 9)) | set(range(ENTRAR + BUCLE, DUR + 1, 3)))
FUNDIDO = 18
opacidad = anim([(f, barco_opacidad(f), "hold" if f == FUNDIDO else LINEAR) for f in range(0, FUNDIDO + 1, 3)]
                + [(f, barco_opacidad(f), None if f == DUR else LINEAR) for f in range(DUR - FUNDIDO, DUR + 1, 3)])
barco = group("Barco", [nombre, fija_id("Quilla", "quilla"), fija_id("Casco", "casco"), fija_id("Borda", "borda"),
                        mastil, seis, bandera, velas],
              H.tr() | {"a": st(list(PIVOTE)), "p": claves(POSICION, barco_pos),
                        "r": claves(CABECEO_EXTREMOS, barco_giro, SENO),
                        "o": opacidad})

# ---------- comprobaciones ----------
REPOSO = (ENTRAR, ENTRAR + BUCLE // 2, ENTRAR + BUCLE)        # aquí todo está exactamente como en el SVG
for f in REPOSO:
    for p in (650 + 157j, 1115 + 255j, 900 + 300j, 140 + 920j, 378 + 555j, 989 + 783j, 860 + 600j):
        assert abs(bandera_campo(p, f) - p) < 1e-9 and abs(mayor(p, f) - p) < 1e-9 and abs(menor(p, f) - p) < 1e-9
    assert abs(seis_giro(f)[0]) < 1e-9 and abs(barco_giro(f)[0]) < 1e-9
    assert abs(barco_pos(f)[0] - PIVOTE[0]) < 1e-9 and abs(barco_pos(f)[1] - PIVOTE[1]) < 1e-9
for p in (616 + 190j, 692 + 850j, 140 + 920j, 654 + 520j, 416 + 885j):           # mástil y botavara de la vela mayor
    assert peso_mayor(p) < 1e-9
for p in (695 + 387j, 745 + 835j, 989 + 783j, 720 + 611j, 867 + 809j):           # mástil y botavara de la vela menor
    assert peso_menor(p) < 1e-9
for p in (ASTA0, ASTA1, (ASTA0 + ASTA1) / 2):                                    # la bandera no se separa del mástil
    assert all(abs(bandera_campo(p, f) - p) < 1e-9 for f in range(DUR + 1))

data = {"v": "5.7.0", "fr": FPS, "ip": 0, "op": DUR, "w": LADO, "h": LADO, "nm": "Velero Carlos Astudillo", "ddd": 0,
        "assets": [], "layers": [layer("Velero", 1, [group("Escena", [barco], H.tr(s=(ESCALA * 100, ESCALA * 100)))])],
        "markers": [{"tm": 0, "cm": "entrar", "dr": ENTRAR}, {"tm": ENTRAR, "cm": "bucle", "dr": BUCLE},
                    {"tm": ENTRAR + BUCLE, "cm": "salir", "dr": SALIR}]}
(OUT / "barco-transicion.fuente.json").write_text(json.dumps(data), encoding="utf-8")
print("ok", OUT / "barco-transicion.fuente.json")
