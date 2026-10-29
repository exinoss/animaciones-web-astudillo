"""Logo "Mercado Local" animado: entrada (se arma el logo) + bucle de 3 s (olas, ave y toldo en movimiento).

El diseño NO se toca: todas las formas, colores y grosores se leen de resources/mercado-local.svg y, al final de
la entrada y al empezar/terminar el bucle, el logo es idéntico al SVG. Solo se añade movimiento.
Marcadores Lottie: "entrada" (0-90) y "bucle" (90-270)."""
import json, math
import xml.etree.ElementTree as ET
from pathlib import Path
from svgpathtools import parse_path
import lottie_helpers as H
from lottie_helpers import st, anim, group, fill, bezier_shapes, layer, hexc, LINEAR

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "resources" / "mercado-local.svg"
OUT = ROOT / "mercado_local" / "glaxnimate"
OUT.mkdir(parents=True, exist_ok=True)

FPS = 60
ENTRADA, BUCLE = 90, 180          # 1.5 s de entrada, 3 s de bucle
DUR = ENTRADA + BUCLE
H.DUR = DUR
ESCALA = 2                         # viewBox 120×144 -> lienzo 240×288
SMOOTH = (.4, 0, .2, 1)
OUT_BACK = (.2, .9, .3, 1.25)
DRAW = (.45, 0, .25, 1)

# ---------- partes del SVG (en su orden de pintado) ----------
SVG = "{http://www.w3.org/2000/svg}"
svg = ET.parse(SRC).getroot()
assert svg.get("viewBox") == "0 0 120 144"
partes = {el.get("data-logo-part") or "pared": el for el in svg if el.tag in (f"{SVG}path", f"{SVG}rect")}
assert list(partes) == ["bird", "pared", "door", "frame", "roof", "wave-1", "wave-2"], list(partes)


def num(el, k):
    return float(el.get(k))


def trazo(el, lc=None, lj=None):
    """Stroke de Lottie con los mismos valores que el SVG (por defecto SVG usa butt / miter / 4)."""
    caps, joins = {"butt": 1, "round": 2, "square": 3}, {"miter": 1, "round": 2, "bevel": 3}
    return {"ty": "st", "c": st(hexc(el.get("stroke"))), "o": st(100), "w": st(num(el, "stroke-width")),
            "lc": caps[el.get("stroke-linecap", "butt")], "lj": joins[el.get("stroke-linejoin", "miter")], "ml": 4}


def trx(a=(0, 0), p=(0, 0), s=(100, 100), o=100, r=0):
    v = lambda x: x if isinstance(x, dict) else st(list(x) if isinstance(x, tuple) else x)
    return {"ty": "tr", "a": v(a), "p": v(p), "s": v(s), "r": v(r), "o": v(o), "sk": st(0), "sa": st(0)}


def muestreo(fn, desde=0, paso=4):
    """Keyframes lineales cada `paso` fotogramas desde `desde` hasta el final (el valor previo se mantiene)."""
    fs = list(range(desde, DUR, paso)) + [DUR]
    keys = [(0, fn(0), "hold")] if desde > 0 else []
    return keys + [(f, fn(f), None if f == DUR else LINEAR) for f in fs]


def suave(u):
    """0 -> 1 con arranque y llegada suaves (smoothstep), recortado a [0, 1]."""
    u = min(1, max(0, u))
    return u * u * (3 - 2 * u)


def ciclo(f):
    """Fase del bucle: 0 en el fotograma 90 y 1 en el 270 (puede ser negativa durante la entrada)."""
    return (f - ENTRADA) / BUCLE


# ---------- olas: la onda se desplaza sin cambiar de silueta ----------
# Cada ola del SVG son 4 arcos cuadráticos (q + t) cuyo dibujo se repite cada dos arcos (los controles van a 11
# y a 12 unidades del inicio, alternando). Se toma esa ola infinita, se desplaza y se recorta al mismo tramo de x.
# Los vértices son los cortes entre arcos: se mueven con la ola y, al salir del tramo, se quedan en el extremo.
# Así cada tramo es un trozo exacto de un arco del SVG y el número de vértices no cambia (Lottie lo exige).


def patron_ola(el):
    """Los dos arcos (P0, P1, P2) que se repiten, el periodo y el tramo [x0, x1] de la ola."""
    arcos = [(seg.start, seg.control, seg.end) for seg in parse_path(el.get("d"))]
    periodo = arcos[2][0] - arcos[0][0]
    for a, b in zip(arcos, arcos[2:]):
        assert all(abs(q - p - periodo) < 1e-9 for p, q in zip(a, b)), "la ola no es periódica"
    return arcos[:2], periodo.real, (arcos[0][0].real, arcos[-1][2].real)


def arco_de(patron, periodo, x):
    """Arco (P0, P1, P2) de la ola infinita que contiene x."""
    n = math.floor((x - patron[0][0].real) / periodo)
    for m in (n - 1, n, n + 1):
        for arco in patron:
            p0, p1, p2 = (p + periodo * m for p in arco)
            if p0.real <= x <= p2.real:
                return p0, p1, p2
    raise ValueError(x)


def t_de(arco, x):
    """Parámetro t del arco cuya abscisa es x (la x de estos arcos crece siempre)."""
    p0, p1, p2 = arco
    a, b, c = p0.real - 2 * p1.real + p2.real, 2 * (p1.real - p0.real), p0.real - x
    t = -c / b if abs(a) < 1e-12 else (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
    return min(1, max(0, t))


def punto(arco, t):
    p0, p1, p2 = arco
    return (1 - t) ** 2 * p0 + 2 * t * (1 - t) * p1 + t * t * p2, 2 * ((1 - t) * (p1 - p0) + t * (p2 - p1))


def forma_ola(ola_, desplaza, cortes):
    """Ola desplazada `desplaza` en x. `cortes` son los índices de los cortes entre arcos que usa (fijos)."""
    patron, periodo, (x0, x1) = ola_
    # Los cortes que quedan fuera se apilan a 0.01 del extremo (no en él): un primer o último tramo de longitud 0
    # deja sin dirección a la punta redondeada y el reproductor la dibuja cortada.
    xs = [x0] + [min(x1 - .01, max(x0 + .01, x0 + periodo / 2 * n + desplaza)) for n in cortes] + [x1]
    v, i, o = [[x0, 0]], [[0, 0]], []
    for xa, xb in zip(xs, xs[1:]):
        arco = arco_de(patron, periodo, (xa + xb) / 2 - desplaza)   # el punto medio no cae en un corte
        ta, tb = t_de(arco, xa - desplaza), t_de(arco, xb - desplaza)
        (pa, da), (pb, _) = punto(arco, ta), punto(arco, tb)
        pa, pb = pa + desplaza, pb + desplaza
        if xb - xa < 1e-9:                        # corte que está fuera del tramo: tramo de longitud 0
            sale = entra = 0j
        else:
            ctrl = pa + (tb - ta) / 2 * da         # sub-arco cuadrático -> cúbica exacta
            sale, entra = 2 / 3 * (ctrl - pa), 2 / 3 * (ctrl - pb)
        v[-1] = [pa.real, pa.imag]
        o.append([sale.real, sale.imag])
        v.append([pb.real, pb.imag]); i.append([entra.real, entra.imag])
    o.append([0, 0])
    return {"i": i, "o": o, "v": v, "c": False}


def error_ola(ola_, forma, desplaza):
    """Máxima diferencia vertical entre una forma Lottie y la ola exacta desplazada."""
    patron, periodo, _ = ola_
    peor = 0
    for n in range(len(forma["v"]) - 1):
        a, b = complex(*forma["v"][n]), complex(*forma["v"][n + 1])
        c1, c2 = a + complex(*forma["o"][n]), b + complex(*forma["i"][n + 1])
        for k in range(21):
            s = k / 20
            p = (1 - s) ** 3 * a + 3 * (1 - s) ** 2 * s * c1 + 3 * (1 - s) * s * s * c2 + s ** 3 * b
            arco = arco_de(patron, periodo, p.real - desplaza)
            peor = max(peor, abs(punto(arco, t_de(arco, p.real - desplaza))[0].imag - p.imag))
    return peor


def mezcla(a, b, u):
    return {k: (a[k] if k == "c" else [[p + (q - p) * u for p, q in zip(pa, pb)] for pa, pb in zip(a[k], b[k])]) for k in a}


RETRASO = 2            # la segunda ola se retrasa y adelanta hasta 2 unidades respecto a la primera


def desplaza_ola(nombre, f):
    """Las dos olas fluyen hacia la derecha, un periodo por bucle. La segunda va con un pequeño desfase que vuelve a
    0 en el fotograma 90: así nunca quedan en contrafase (la cresta de una tocaría el valle de la otra)."""
    periodo = patron_ola(partes[nombre])[1]
    return periodo * ciclo(f) - (RETRASO * math.sin(2 * math.pi * ciclo(f)) if nombre == "wave-2" else 0)


def ola(nombre, dibujo):
    ola_ = patron_ola(partes[nombre])
    _, periodo, (x0, x1) = ola_
    # Ya fluye mientras se dibuja (fase continua en el fotograma 90).
    # Keyframes cada 10 fotogramas desde el 40: caen justo en el 90 y en el 270, así el bucle empalma exacto.
    tiempos = [f for f, _, _ in muestreo(lambda f: 0, desde=40, paso=10)][1:]
    desplazas = [desplaza_ola(nombre, f) for f in tiempos]
    media = periodo / 2
    cortes = range(math.ceil(-max(desplazas) / media), math.floor((x1 - x0 - min(desplazas)) / media) + 1)
    formas = [forma_ola(ola_, d, cortes) for d in desplazas]
    # Comprobaciones: en reposo es el SVG exacto; entre keyframes (interpolación lineal) el error es despreciable
    assert error_ola(ola_, forma_ola(ola_, 0, cortes), 0) < 1e-9
    peor = max(error_ola(ola_, mezcla(fa, fb, u / 10), da + (db - da) * u / 10)
               for fa, fb, da, db in zip(formas, formas[1:], desplazas, desplazas[1:]) for u in range(10))
    assert peor < .08, peor                   # 0.08 unidades = 0.16 px en el lienzo
    forma = anim([(0, formas[0], "hold")] + [(f, fo, None if f == DUR else LINEAR) for f, fo in zip(tiempos, formas)])
    recorte = {"ty": "tm", "s": st(0), "o": st(0), "m": 1,
               "e": anim([(0, 0, "hold"), (dibujo[0], 0, DRAW), (dibujo[1], 100, None)])}
    return group(f"Ola {nombre[-1]}", [{"ty": "sh", "ks": forma}, recorte, trazo(partes[nombre])])


# ---------- ave: aletea (la "m" se deforma) y planea subiendo y bajando ----------
ave_el = partes["bird"]
(a0, c0, a1), (_, c1, a2) = [(s.start, s.control, s.end) for s in parse_path(ave_el.get("d"))]


def forma_ave(k):
    """k = 0 es el SVG; k > 0 baja las puntas de las alas, k < 0 las sube."""
    p0 = complex(a0.real + abs(k), a0.imag + 4 * k)
    p2 = complex(a2.real - abs(k), a2.imag + 4 * k)
    q0, q1 = c0 + 3j * k, c1 + 3j * k
    cub = lambda p, q: [(q - p).real * 2 / 3, (q - p).imag * 2 / 3]
    return {"v": [[p0.real, p0.imag], [a1.real, a1.imag], [p2.real, p2.imag]],
            "o": [cub(p0, q0), cub(a1, q1), [0, 0]], "i": [[0, 0], cub(a1, q0), cub(p2, q1)], "c": False}


assert forma_ave(0)["v"] == [[87, 17], [99, 17], [111, 17]]
ALETEOS = [56, 72, ENTRADA, ENTRADA + 16]        # inicio de cada aleteo (16 fotogramas); el resto planea


def aleteo(f):
    for t0 in ALETEOS:
        if t0 <= f <= t0 + 16:
            return math.sin(2 * math.pi * (f - t0) / 16) * (.9 if t0 < ENTRADA else .7)
    return 0


AVE_C = (a1.real, a1.imag - 2)                    # centro del ave
LLEGA0, LLEGA1 = 54, 88                           # entra volando desde la derecha


def ave_pos(f):
    u = suave((f - LLEGA0) / (LLEGA1 - LLEGA0))
    entra = (26 * (1 - u) ** 2, 10 * (1 - u) ** 2)
    env = suave((f - 70) / (ENTRADA - 70))
    planea = (.8 * math.sin(2 * math.pi * ciclo(f) * 2) * env, -1.6 * math.sin(2 * math.pi * ciclo(f)) * env)
    return [AVE_C[0] + entra[0] + planea[0], AVE_C[1] + entra[1] + planea[1]]


FIN_ALETEO = ALETEOS[-1] + 16
aleteo_keys = ([(0, forma_ave(0), "hold")] + [(f, forma_ave(aleteo(f)), LINEAR) for f in range(ALETEOS[0], FIN_ALETEO, 2)]
               + [(FIN_ALETEO, forma_ave(0), "hold"), (DUR, forma_ave(0), None)])

ave = group("Ave", [{"ty": "sh", "ks": anim(aleteo_keys)}, trazo(ave_el)], trx(
    a=AVE_C, p=anim(muestreo(ave_pos, desde=LLEGA0, paso=2), dims=2),
    r=anim(muestreo(lambda f: [2.5 * math.sin(2 * math.pi * ciclo(f)) * suave((f - 70) / (ENTRADA - 70))], desde=70)),
    o=anim([(0, 0, "hold"), (LLEGA0, 0, SMOOTH), (LLEGA0 + 10, 100, "hold"), (DUR, 100, None)])))

# ---------- tienda: el marco se dibuja, la puerta aparece y el toldo se despliega y se mece ----------
marco_el, toldo_el, puerta_el, pared_el = partes["frame"], partes["roof"], partes["door"], partes["pared"]
MARCO0, MARCO1 = 0, 28
TOLDO0, TOLDO1 = 16, 42
PUERTA0, PUERTA1 = 36, 54
CUELGA = (60, 30)                                  # el toldo cuelga del borde de arriba


def mece(f):
    """Giro muy leve del toldo (aparece poco a poco tras desplegarse)."""
    return [1.2 * math.sin(2 * math.pi * ciclo(f)) * suave((f - TOLDO1) / (ENTRADA - TOLDO1))]


def estira(f):
    """Estiramiento vertical leve, dos veces por bucle, como tela con brisa."""
    k = (1 - math.cos(4 * math.pi * ciclo(f))) / 2 * suave((f - TOLDO1) / (ENTRADA - TOLDO1))
    return [100, 100 + 2 * k]


toldo = group("Toldo", [group("Despliegue", [*bezier_shapes(toldo_el.get("d")), trazo(toldo_el), fill(toldo_el.get("fill"))],
                              trx(a=CUELGA, p=CUELGA,
                                  s=anim([(0, [100, 0], "hold"), (TOLDO0, [100, 0], OUT_BACK), (TOLDO1, [100, 100], "hold"),
                                          (DUR, [100, 100], None)], dims=2),
                                  o=anim([(0, 0, "hold"), (TOLDO0, 0, SMOOTH), (TOLDO0 + 4, 100, "hold"), (DUR, 100, None)])))],
              trx(a=CUELGA, p=CUELGA, r=anim(muestreo(mece, desde=TOLDO1)), s=anim(muestreo(estira, desde=TOLDO1), dims=2)))

marco = group("Marco", [*bezier_shapes(marco_el.get("d")),
                        {"ty": "tm", "s": st(0), "o": st(0), "m": 1,
                         "e": anim([(MARCO0, 0, DRAW), (MARCO1, 100, "hold"), (DUR, 100, None)])},
                        trazo(marco_el)])

x, y, w, h = (num(puerta_el, k) for k in ("x", "y", "width", "height"))
BASE_PUERTA = (x + w / 2, y + h)
puerta = group("Puerta", [{"ty": "rc", "p": st([x + w / 2, y + h / 2]), "s": st([w, h]), "r": st(num(puerta_el, "rx")), "d": 1},
                          fill(puerta_el.get("fill"))],
               trx(a=BASE_PUERTA, p=BASE_PUERTA,
                   s=anim([(0, [0, 0], "hold"), (PUERTA0, [0, 0], OUT_BACK), (PUERTA1, [100, 100], "hold"), (DUR, [100, 100], None)], dims=2)))

pared = group("Pared", [*bezier_shapes(pared_el.get("d")), fill(pared_el.get("fill"))],
              trx(o=anim([(0, 0, "hold"), (6, 0, SMOOTH), (24, 100, "hold"), (DUR, 100, None)])))

# ---------- capas (orden del SVG: lo último pintado queda arriba) ----------
escena = lambda nombre, items: group(nombre, items, trx(s=(ESCALA * 100, ESCALA * 100)))
capas = [("Olas", [ola("wave-2", (48, 76)), ola("wave-1", (40, 68))]),
         ("Tienda", [toldo, marco, puerta, pared]),
         ("Ave", [ave])]
data = {"v": "5.7.0", "fr": FPS, "ip": 0, "op": DUR, "w": 120 * ESCALA, "h": 144 * ESCALA, "nm": "Logo Mercado Local",
        "ddd": 0, "assets": [],
        "layers": [layer(n, i + 1, [escena(f"Escena {n.lower()}", items)]) for i, (n, items) in enumerate(capas)],
        "markers": [{"tm": 0, "cm": "entrada", "dr": ENTRADA}, {"tm": ENTRADA, "cm": "bucle", "dr": BUCLE}]}
(OUT / "logo-mercado-local.fuente.json").write_text(json.dumps(data), encoding="utf-8")
print("ok", OUT / "logo-mercado-local.fuente.json")
