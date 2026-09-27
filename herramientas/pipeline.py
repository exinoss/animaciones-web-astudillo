"""Pipeline completo de las animaciones "Somos la 6".

Uso (desde la raíz del proyecto):
    uv run --no-project --with svgpathtools --with pillow python herramientas/pipeline.py all
    uv run --no-project --with svgpathtools --with pillow python herramientas/pipeline.py loader
    uv run --no-project --with svgpathtools --with pillow python herramientas/pipeline.py marca
    uv run --no-project --with svgpathtools --with pillow python herramientas/pipeline.py demos
    uv run --no-project --with svgpathtools --with pillow python herramientas/pipeline.py desde-rawr loader|marca
    uv run --no-project --with svgpathtools --with pillow python herramientas/pipeline.py verificar <archivo.rawr|.json> [fotogramas...]

Cada animación sigue SIEMPRE el mismo flujo:
    construir_*.py  ->  *.fuente.json  ->  Glaxnimate  ->  *.rawr  ->  Glaxnimate  ->  *.json
                                                             |-> render de fotogramas -> *.gif
    + reinyectar marcadores (Glaxnimate los borra al exportar)  + regenerar las demos HTML
"""
import json, os, shutil, subprocess, sys
from pathlib import Path

HERR = Path(__file__).resolve().parent
ROOT = HERR.parent
SALIDA = HERR / "_salida"                     # temporal: fotogramas y hojas de verificación
LOADER = ROOT / "loading_vote" / "glaxnimate"
MARCA = ROOT / "marca_vota6" / "glaxnimate"
PLANT = HERR / "plantillas"
# Únicos archivos que usa la web (las demos también los usan, para probar exactamente lo que va a producción)
LOADER_PROD = LOADER / "produccion" / "loader-vota6.min.json"     # variante transparente, optimizada
MARCA_PROD = MARCA / "produccion" / "marca-vota6.min.json"         # con marcadores "marcar" / "salir"

GX = Path(os.environ.get("GLAXNIMATE_EXE", Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Glaxnimate/bin/glaxnimate.exe"))


def gx_env():
    """La CLI de Glaxnimate 0.6 en Windows trae vacía la librería estándar de su Python interno:
    sin PYTHONHOME apuntando a un CPython 3.11 se cierra con código -1073740791."""
    env = dict(os.environ)
    home = os.environ.get("GLAXNIMATE_PYTHONHOME")
    if not home:
        # Buscar un CPython 3.11 completo gestionado por uv (no el de un entorno virtual temporal)
        def buscar():
            base = Path(subprocess.run(["uv", "python", "dir"], capture_output=True, text=True).stdout.strip())
            return next((p for p in sorted(base.glob("cpython-3.11*")) if (p / "Lib" / "encodings").is_dir()), None)
        encontrado = buscar()
        if not encontrado:
            subprocess.run(["uv", "python", "install", "3.11"], check=True)
            encontrado = buscar()
        home = str(encontrado)
    env["PYTHONHOME"] = home
    return env


def gx(*args):
    r = subprocess.run([str(GX), *map(str, args)], env=gx_env(), capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise SystemExit(f"Glaxnimate falló ({r.returncode}) con {args}:\n{r.stderr[-800:]}")


def py(script, *args):
    subprocess.run([sys.executable, str(HERR / script), *args], check=True)


def convertir(carpeta: Path, nombre: str, desde_rawr=False):
    """fuente.json -> .rawr (proyecto) -> .json (Lottie exportado por Glaxnimate) + marcadores.
    Con desde_rawr=True se respeta el .rawr tal cual (editado a mano en Glaxnimate) y solo se exporta."""
    fuente = carpeta / f"{nombre}.fuente.json"
    if not desde_rawr:
        gx(fuente, "-o", carpeta / f"{nombre}.rawr")
    gx(carpeta / f"{nombre}.rawr", "-o", carpeta / f"{nombre}.json", "-f", "lottie")
    marcadores = json.loads(fuente.read_text(encoding="utf-8")).get("markers")
    if marcadores:
        final = carpeta / f"{nombre}.json"
        data = json.loads(final.read_text(encoding="utf-8"))
        data["markers"] = marcadores
        final.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    print(f"  ✔ {nombre}: .rawr y .json actualizados" + (" (+ marcadores)" if marcadores else ""))


def produccion(origen: Path, destino: Path, decimales=3):
    """Versión para la web: redondea números a `decimales`, quita nombres internos (nm/mn/ix) y metadatos
    del editor, y compacta el JSON. Conserva los marcadores (su campo es `cm`, no `nm`).
    Reproducir con lottie_light (sin expresiones, solo SVG): nuestras animaciones no usan expresiones."""
    def limpiar(o):
        if isinstance(o, float):
            r = round(o, decimales)
            return int(r) if r == int(r) else r
        if isinstance(o, list):
            return [limpiar(x) for x in o]
        if isinstance(o, dict):
            return {k: limpiar(v) for k, v in o.items() if k not in ("nm", "mn", "ix", "meta")}
        return o
    data = limpiar(json.loads(origen.read_text(encoding="utf-8")))
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"  ✔ producción {destino.relative_to(ROOT)} ({destino.stat().st_size / 1024:.1f} KB)")


def gif(rawr: Path, destino: Path, colores=160):
    """Renderiza todos los fotogramas con el motor de Glaxnimate y arma un GIF a 30 fps sobre blanco.
    (El exportador GIF de Glaxnimate 0.6 se cierra en Windows, por eso se hace así.)"""
    from PIL import Image
    d = SALIDA / f"frames_{rawr.stem}"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    gx(rawr, "-r", d / "f.png", "--frame", "all")
    ims = []
    for f in sorted(d.glob("f*.png"))[::2]:
        im = Image.open(f).convert("RGBA")
        fondo = Image.new("RGBA", im.size, (255, 255, 255, 255))
        fondo.alpha_composite(im)
        ims.append(fondo.convert("RGB").quantize(colors=colores, method=Image.Quantize.MEDIANCUT))
    ims[0].save(destino, save_all=True, append_images=ims[1:], duration=33, loop=0, optimize=True)
    print(f"  ✔ GIF {destino.name} ({len(ims)} fotogramas)")


def incrustar(plantilla: str, destino: Path, **datos):
    html = (PLANT / plantilla).read_text(encoding="utf-8")
    for clave, ruta in datos.items():
        data = json.loads(Path(ruta).read_text(encoding="utf-8"))
        html = html.replace(f"/*{clave}*/null", json.dumps(data, separators=(",", ":")))
    destino.write_text(html, encoding="utf-8")
    print(f"  ✔ {destino.relative_to(ROOT)}")


def loader(desde_rawr=False):
    print("Loader (loading_vote)")
    if not desde_rawr:
        py("construir_loader.py")                     # versión con fondo amarillo (GIF / redes)
        py("construir_loader.py", "transparente")     # versión para usar como loading en la web
    convertir(LOADER, "loader-vota6", desde_rawr)
    convertir(LOADER, "loader-vota6-transparente", desde_rawr)
    produccion(LOADER / "loader-vota6-transparente.json", LOADER_PROD)
    gif(LOADER / "loader-vota6.rawr", LOADER / "loader-vota6.gif")
    incrustar("demo-loader.tpl.html", LOADER / "demo.html", LOTTIE_DATA=LOADER_PROD)


def marca(desde_rawr=False):
    print("Transición (marca_vota6)")
    if not desde_rawr:
        py("construir_marca.py")
    convertir(MARCA, "marca-vota6", desde_rawr)
    produccion(MARCA / "marca-vota6.json", MARCA_PROD)
    gif(MARCA / "marca-vota6.rawr", MARCA / "marca-vota6.gif")
    incrustar("demo-header.tpl.html", ROOT / "marca_vota6" / "demo-header.html", LOTTIE_DATA=MARCA_PROD)


def demos():
    print("Demo combinada")
    incrustar("demo-completa.tpl.html", ROOT / "demo-completa.html", MARCA_DATA=MARCA_PROD, LOADER_DATA=LOADER_PROD)


def verificar(archivo, fotogramas):
    """Hoja de contactos renderizada por Glaxnimate para revisar visualmente fotogramas concretos."""
    from PIL import Image, ImageDraw
    archivo = Path(archivo).resolve()
    d = SALIDA / "verificar"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    fotogramas = [int(f) for f in fotogramas] or [0, 15, 30, 45, 60, 90, 120, 150]
    tiles = []
    for f in fotogramas:
        png = d / f"f{f:03d}.png"
        gx(archivo, "-r", png, "--frame", f)
        im = Image.open(png).convert("RGBA")
        fondo = Image.new("RGBA", im.size, "white"); fondo.alpha_composite(im)
        im = fondo.convert("RGB").resize((im.width * 2, im.height * 2))
        ImageDraw.Draw(im).text((6, 4), f"f{f}", fill="black")
        tiles.append(im)
    w, h = tiles[0].size
    hoja = Image.new("RGB", (4 * w, -(-len(tiles) // 4) * h), "white")
    for i, im in enumerate(tiles):
        hoja.paste(im, ((i % 4) * w, (i // 4) * h))
    hoja.save(SALIDA / "hoja.png")
    print(f"  ✔ {SALIDA / 'hoja.png'}")


if __name__ == "__main__":
    if not GX.exists():
        raise SystemExit(f"No encuentro Glaxnimate en {GX}. Instálalo con: winget install --id KDE.Glaxnimate -e")
    cmd, *resto = sys.argv[1:] or ["all"]
    if cmd == "loader": loader()
    elif cmd == "marca": marca()
    elif cmd == "demos": demos()
    elif cmd == "all": loader(); marca(); demos()
    elif cmd == "desde-rawr" and resto[:1] == ["loader"]: loader(desde_rawr=True); demos()
    elif cmd == "desde-rawr" and resto[:1] == ["marca"]: marca(desde_rawr=True); demos()
    elif cmd == "verificar": verificar(resto[0], resto[1:])
    else: raise SystemExit(__doc__)
