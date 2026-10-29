# Animaciones "Somos la 6"

Repositorio: **`animaciones-web-astudillo`**

Animaciones web para la campaña de la **Lista 6** (y el logo animado de **Mercado Local**), hechas con **Glaxnimate** y exportadas a **Lottie** (reproducidas con `lottie-web`).

> **Para otra IA o dev:** lee este archivo completo antes de tocar nada. Los `.json`, `.rawr`, `.gif` y las demos HTML **se generan**. No se editan a mano; se regeneran con el pipeline (ver [Flujo de trabajo](#flujo-de-trabajo)).

## 🚀 Qué usar en el sitio web

**Solo estos archivos van a producción.** Todo lo demás es material de trabajo.

| Uso | Archivo | Tamaño (gzip) |
|---|---|---|
| Loading de datos | [`loading_vote/glaxnimate/produccion/loader-vota6.min.json`](loading_vote/glaxnimate/produccion/loader-vota6.min.json) | 29 KB (≈6.6 KB) |
| Transición entre páginas | [`marca_vota6/glaxnimate/produccion/marca-vota6.min.json`](marca_vota6/glaxnimate/produccion/marca-vota6.min.json) | 26 KB (≈7.5 KB) |
| Logo Mercado Local animado (entrada + bucle) | [`mercado_local/glaxnimate/produccion/logo-mercado-local.min.json`](mercado_local/glaxnimate/produccion/logo-mercado-local.min.json) | 55 KB (≈6 KB) |

Reproductor: **`lottie_light`** (versión ligera de lottie-web: solo SVG, sin expresiones, ≈47 KB gzip frente a ≈77 KB del completo):

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie_light.min.js"></script>
<script>
  const anim = lottie.loadAnimation({
    container: document.getElementById('loader'),
    renderer: 'svg', loop: true, autoplay: true,
    path: '/animaciones/loader-vota6.min.json'   // ruta donde lo publique tu sitio
  });
</script>
```

Por qué este formato:
- **Lottie JSON** es vectorial, así que se ve nítido a cualquier tamaño, con transparencia real y en unos 7 KB. El GIF pesa entre 100 y 285 KB, se pixela y no tiene transparencia.
- **Optimizado**: números redondeados a 3 decimales, sin nombres internos ni metadatos del editor. Es un 38 % más ligero comprimido que el `.json` de Glaxnimate y **se verificó píxel a píxel que se ve idéntico**.
- **dotLottie (`.lottie`) descartado**: su reproductor usa WebAssembly y es bastante más pesado. Solo compensa con imágenes o con muchas animaciones.
- Sirve los `.json` con compresión **gzip o brotli** (casi todos los hosting lo hacen por defecto) y con caché larga. Si el sitio es de producción, puedes alojar tú mismo `lottie_light.min.js` en lugar de usar el CDN.
- La carpeta `produccion/` **la escribe el pipeline**: no se edita a mano. Tras un cambio, ejecuta el pipeline y copia de nuevo esos dos archivos al sitio.

## Qué hay

| Carpeta / archivo | Qué es | README propio |
|---|---|---|
| [`loading_vote/`](loading_vote/) | **Loader** para cargas de datos: el 6 se construye, la papeleta se despliega, una mano raya la casilla, se dobla y cae en la urna "LISTA 6". | [loading_vote/README.md](loading_vote/README.md) |
| [`marca_vota6/`](marca_vota6/) | **Transición entre páginas** del header: papeleta centrada, una mano raya en vertical la línea de la casilla. | [marca_vota6/README.md](marca_vota6/README.md) |
| [`mercado_local/`](mercado_local/) | **Logo Mercado Local animado**, sin cambiar el diseño: entrada (el logo se arma) y bucle de 3 s (olas, ave y toldo en movimiento). | [mercado_local/README.md](mercado_local/README.md) |
| [`demo-completa.html`](demo-completa.html) | Web de ejemplo con las **dos animaciones trabajando juntas** (transición al cambiar de sección + loading al esperar datos). Se abre con doble clic. | — |
| [`herramientas/`](herramientas/) | Scripts que construyen las animaciones, vectores fuente y plantillas de las demos. Se documenta aquí abajo. | — |
| [`resources/`](resources/) | Material de marca original: `favicon.jpg` (el 6 de cinta), `somos6.png` (lockup "Somos la 6"), `logo.avif` (logo PS6), `mercado-local.svg` (logo Mercado Local, fuente de su animación). **No hay archivos de fuente tipográfica.** | — |
| `disenos/circulo-rebote.svg` | Prueba inicial sin relación con la campaña. Se puede borrar. | — |
| `herramientas/_salida/` | Temporal (fotogramas renderizados, hojas de verificación). Se puede borrar; se regenera. | — |

## Requisitos (Windows)

| Herramienta | Para qué | Instalación |
|---|---|---|
| **Glaxnimate 0.6** | Convertir a proyecto `.rawr`, exportar Lottie y renderizar fotogramas | `winget install --id KDE.Glaxnimate -e` |
| **uv** | Ejecutar los scripts de Python con sus dependencias | `winget install astral-sh.uv` |
| **CPython 3.11 (vía uv)** | Lo necesita la CLI de Glaxnimate (ver [Problemas conocidos](#problemas-conocidos)) | `uv python install 3.11` (el pipeline lo instala solo si falta) |
| Inkscape 1.4 | Solo para convertir **textos nuevos** a trazados | `winget install Inkscape.Inkscape` |
| Chrome | Solo para probar las demos | — |

### Linux

Glaxnimate 0.6 no está en los repositorios de Ubuntu 24.04 y el wheel de PyPI (`glaxnimate`) está compilado para otra distribución (no carga en Ubuntu). Si no puedes usar el AppImage o el Flatpak de KDE, **compila la versión 0.6.0** con Qt5/KF5, que sí están en Ubuntu 24.04. Con ese binario, `pipeline.py loader`, `marca` y `demos` generan los mismos `produccion/*.min.json`, GIF y demos, byte a byte, que los que hay en el repositorio.

```bash
sudo apt-get install -y build-essential cmake ninja-build extra-cmake-modules qtbase5-dev qtbase5-private-dev qttools5-dev libqt5svg5-dev libkf5i18n-dev libkf5coreaddons-dev libkf5widgetsaddons-dev libkf5xmlgui-dev libkf5archive-dev libkf5completion-dev libkf5iconthemes-dev libkf5config-dev libkf5crash-dev libpotrace-dev python3-dev libavformat-dev libavcodec-dev libavutil-dev libswscale-dev libarchive-dev zlib1g-dev gettext inkscape
git clone --depth 1 --branch v0.6.0 --recurse-submodules https://github.com/KDE/glaxnimate.git
cmake -S glaxnimate -B glaxnimate/build -G Ninja -DCMAKE_BUILD_TYPE=Release -DQT_MAJOR_VERSION=5 -DCMAKE_INSTALL_PREFIX=/opt/glaxnimate
ninja -C glaxnimate/build install
```

Después, antes de ejecutar el pipeline: `export GLAXNIMATE_EXE=/opt/glaxnimate/bin/glaxnimate` (si no, busca `glaxnimate` en el `PATH`) y, en un servidor sin pantalla, `export QT_QPA_PLATFORM=offscreen`. En Linux el pipeline no toca `PYTHONHOME` (eso solo hace falta en Windows). Inkscape 1.2 de `apt` convierte texto a trazados con el mismo comando (`inkscape` en lugar de `inkscape.com`), pero **Arial Black no viene en Linux**: instálala antes de convertir textos de marca o usará otra fuente.

## Flujo de trabajo

Todo se regenera con **un solo comando** desde la raíz del proyecto:

```powershell
uv run --no-project --with svgpathtools --with pillow python herramientas/pipeline.py all
```

Qué hace, en orden, para cada animación:

```
construir_*.py ──► *.fuente.json ──► Glaxnimate ──► *.rawr (proyecto editable)
                                                      │
                                                      ├─► Glaxnimate ──► *.json (Lottie final) ──► + marcadores
                                                      │                     └─► optimizar ──► produccion/*.min.json  ◄── lo que usa la web
                                                      ├─► Glaxnimate render de todos los fotogramas ──► *.gif
                                                      └─► plantillas/*.tpl.html + produccion/*.min.json incrustado ──► demos HTML
```

Subcomandos:

| Comando | Qué regenera |
|---|---|
| `pipeline.py all` | Todo: loader, transición, demos y logo Mercado Local |
| `pipeline.py loader` | `loading_vote/glaxnimate/*` (las dos variantes, `produccion/`, GIF y `demo.html`) |
| `pipeline.py marca` | `marca_vota6/glaxnimate/*` (incluido `produccion/`), GIF y `marca_vota6/demo-header.html` |
| `pipeline.py demos` | Solo `demo-completa.html` (a partir de los `.json` actuales) |
| `pipeline.py mercado` | `mercado_local/glaxnimate/*` (incluido `produccion/`), GIF y `mercado_local/demo.html` |
| `pipeline.py desde-rawr loader\|marca\|mercado` | Respeta un `.rawr` **editado a mano en Glaxnimate** y regenera desde él `.json`, marcadores, GIF y demos (no ejecuta `construir_*.py`) |
| `pipeline.py verificar <archivo.rawr> [fotogramas…]` | Hoja de contactos en `herramientas/_salida/hoja.png` renderizada por Glaxnimate, para **revisar visualmente** |

### Reglas del flujo (importante para IAs)

1. **Después de cualquier cambio, ejecuta el pipeline completo de esa animación.** No basta con regenerar el `.json`: el archivo de **`produccion/`**, el **GIF** y las **demos HTML** quedarían desactualizados. Una IA que no conozca este flujo suele olvidar alguno de ellos. El pipeline los hace siempre.
2. **No edites a mano** `*.json`, `*.fuente.json`, `produccion/*.min.json`, `*.gif`, `demo.html`, `demo-header.html` ni `demo-completa.html`. Edita el script o la plantilla en `herramientas/` y regenera.
2b. **Las demos usan los mismos archivos de `produccion/` y el mismo reproductor `lottie_light`** que la web. Si una demo se ve bien, lo que va a producción también.
3. **Verifica visualmente antes de dar algo por terminado.** Usa `pipeline.py verificar` con los fotogramas clave (cada README de animación tiene su tabla de tiempos) y mira la imagen. Así se detectaron casi todos los errores durante el desarrollo.
4. **Las dos animaciones comparten estilo.** Misma mano, mismo plumón azul y misma casilla con línea negra. Si cambias uno de esos elementos en una, cámbialo también en la otra.

### Dos formas de modificar una animación

**A. Por código (recomendada para cambios de tiempos, estructura o textos)**
1. Edita `herramientas/construir_loader.py` o `herramientas/construir_marca.py`. Las constantes de tiempo están arriba y están comentadas.
2. Ejecuta `pipeline.py loader` o `pipeline.py marca`.
3. Ejecuta `pipeline.py verificar …` y revisa `herramientas/_salida/hoja.png`.

**B. A mano en Glaxnimate (recomendada para retoques visuales)**
1. Abre el `.rawr` en Glaxnimate, edita y guarda.
2. Ejecuta `pipeline.py desde-rawr loader` o `desde-rawr marca`.
3. ⚠️ **Si después alguien ejecuta `pipeline.py loader`, `marca` o `all`, el `.rawr` se reconstruye desde el código y los retoques manuales se pierden.** Hay dos salidas: trasladar el retoque al script, o no volver a usar el modo A para esa animación. Deja constancia en el README de la animación.
4. El loader tiene **dos `.rawr`** (con fondo y transparente). Un retoque manual hay que hacerlo en ambos.

## Marca

| Color | Hex | Uso |
|---|---|---|
| Amarillo | `#FEBF12` | Fondos, franja de la papeleta |
| Rojo | `#E82128` | Cinta del 6, "6" de "LISTA 6", destellos (variante transparente) |
| Azul | `#004EA1` | Urna, plumón, rayón, "LISTA", casillas marcadas |
| Tinta | `#1D2433` | Línea impresa de la casilla |

- **El 6 de cinta** (`fuentes/trace6.json`) y **el lockup "Somos la 6"** (`fuentes/trace_lockup.json`) están **vectorizados** desde `resources/` con `trazar_seis.py` y `trazar_lockup.py`, que requieren `--with scikit-image --with numpy --with pillow`. Solo hay que volver a ejecutarlos si cambian las imágenes de `resources/`.
- **Tipografía:** no hay archivos de fuente. "LISTA 6" se convirtió a trazado con **Arial Black** usando Inkscape. Para un texto nuevo:
  ```powershell
  # 1) crear herramientas/fuentes/mi-texto.svg con un <text font-family="Arial Black">…</text>
  & "C:\Program Files\Inkscape\bin\inkscape.com" herramientas/fuentes/mi-texto.svg --actions="select-all;object-to-path;path-combine;export-filename:herramientas/fuentes/mi-texto_p.svg;export-plain-svg;export-do"
  & "C:\Program Files\Inkscape\bin\inkscape.com" herramientas/fuentes/mi-texto_p.svg --query-all   # bbox para centrarlo
  ```
  Usa `inkscape.com` (consola), no `inkscape.exe`: el `.exe` no escribe archivos desde la línea de comandos.
- **La mano** es el emoji ✍🏽 de [Noto Emoji](https://github.com/googlefonts/noto-emoji) (Google, **Apache 2.0**, hay que mantener el crédito). `preparar_mano.py` aplana sus `clipPath` (Lottie no los admite) y pinta el lápiz de azul de marca. Requiere `--with skia-pathops --with fonttools`. La punta del plumón está en `(15.6, 112.6)` del viewBox 128×128; los scripts la usan como ancla para que el trazo siga la punta.

## Problemas conocidos

| Problema | Solución aplicada |
|---|---|
| La **CLI** de Glaxnimate 0.6 (instalador de winget) se cierra con código `-1073740791` porque su Python interno viene sin librería estándar. La ventana normal funciona. | `pipeline.py` pone `PYTHONHOME` apuntando a un CPython 3.11 de uv. Se puede forzar con la variable `GLAXNIMATE_PYTHONHOME`. |
| Los exportadores **SVG, GIF y dotLottie** de Glaxnimate 0.6 fallan: el SVG pierde las animaciones de transformación y los otros dos cierran el programa. | Solo se exporta **Lottie**. El GIF se arma con Pillow a partir del render de fotogramas de Glaxnimate. |
| Glaxnimate **borra los marcadores** Lottie (`markers`) al exportar. | El pipeline los copia del `.fuente.json` al `.json` final. |
| En el PC del autor, los **"Efectos de animación" de Windows están desactivados**, así que los navegadores activan `prefers-reduced-motion`. | Las demos no bloquean la animación por esa preferencia. Si se añade esa regla, en ese PC la animación se verá quieta. |
| Chrome *headless* (para pruebas automáticas) activa "reducir movimiento" y casi no avanza `requestAnimationFrame` con `--virtual-time-budget`. | En pruebas: `--force-prefers-no-reduced-motion` y sustituir `requestAnimationFrame` por `setTimeout(…, 16)`. Para ver un fotograma exacto de un Lottie, usar `anim.goToAndStop(frame, true)`. |
| Se probó el MCP de Inkscape (`sandraschi/inkscape-mcp`) y se descartó: Inkscape no anima y su vectorizador falla con Inkscape 1.4. | Eliminado del proyecto. |

## Historial de decisiones

1. Un primer loader en SVG + CSS dibujado a mano se descartó por baja calidad visual. Desde entonces **todo el arte sale de la marca vectorizada o de ilustraciones profesionales** (la mano de Noto), y la animación se hace en Glaxnimate/Lottie.
2. **Loader:** fondo amarillo a sangre; texto de la urna "LISTA 6" (LISTA azul, 6 rojo); el check se reemplazó por una **papeleta en dos tarjetas** con rayón vertical; el rayón dura 0.4 s (duración total 3.5 s). Para la web se usa la **variante transparente** sobre un velo blanco, porque la de fondo amarillo parecía una tarjeta pegada.
3. **Transición:** primero era una X sobre el 6. Se cambió a una **casilla con línea negra y rayón vertical** (así marca la gente), compacta, **sin giro** y **centrada y grande** sobre el contenido durante el cambio de página.

## Software libre para animación (resumen del análisis inicial)

| Necesidad | Software recomendado |
|---|---|
| Loaders, íconos y animación web | **Glaxnimate** (Lottie, el elegido) o **Friction** (SVG + SMIL, alternativa libre a After Effects) |
| Dibujar el arte vectorial | **Inkscape** (no anima: no tiene línea de tiempo) |
| Personajes y 2D cuadro a cuadro | **Synfig**, **OpenToonz**, **Krita**, **Pencil2D** |
| 2D + 3D, lo más potente | **Blender** (Grease Pencil) |
| Animación por código | **Motion Canvas**, **Theatre.js**, **lottie-web** / **dotlottie-web** (reproductores) |

Rive (editor) y GSAP son gratuitos pero **no** son software libre.

## Créditos

- Mano: [Noto Emoji](https://github.com/googlefonts/noto-emoji) ✍🏽, © Google, licencia Apache 2.0 (modificada: lápiz recoloreado y recortes aplanados).
- Reproductor: [lottie-web](https://github.com/airbnb/lottie-web), MIT.
- Editor: [Glaxnimate](https://glaxnimate.org/), GPL-3.0 (solo herramienta; no se distribuye).
