# marca_vota6 — Transición entre páginas "Marca la 6"

Animación de **transición entre páginas** para los botones del header. Aparece una papeleta centrada y grande (franja amarilla con el lockup "Somos la 6" y una casilla con una línea negra); una mano con plumón azul **raya en vertical** la línea, formando una cruz, y la papeleta se va. Mientras tanto, la página cambia detrás.

> Flujo de trabajo, requisitos y reglas generales: ver el [README de la raíz](../README.md). **No edites el `.json`, el `.gif` ni los HTML a mano.** Se regeneran con `pipeline.py marca`.

## Archivos

| Archivo | Qué es | ¿Se edita? |
|---|---|---|
| `glaxnimate/marca-vota6.rawr` | Proyecto Glaxnimate | Sí, en Glaxnimate (luego `pipeline.py desde-rawr marca`) |
| `glaxnimate/marca-vota6.json` | Lottie final, **con los marcadores `marcar` y `salir`** | No, se genera |
| `glaxnimate/marca-vota6.gif` | GIF 240×200 sobre blanco, 30 fps | No, se genera |
| `glaxnimate/marca-vota6.fuente.json` | Lottie intermedio que escribe `construir_marca.py` | No, se genera |
| `demo-header.html` | Demo solo de la transición con un header de ejemplo. Plantilla: `herramientas/plantillas/demo-header.tpl.html` | No, se genera |

La demo con las dos animaciones juntas es [`../demo-completa.html`](../demo-completa.html).

## Especificaciones

- Lienzo **240×200**, **60 fps**, **56 fotogramas (0.93 s)**, **fondo transparente** y **sin giro**.
- Script: `herramientas/construir_marca.py` (usa `herramientas/lottie_helpers.py`).
- Una sola capa, **Papeleta**, con los grupos `Mano`, `Tachado`, `Casilla` (`Línea impresa`, `Recuadro`), `Somos la 6` (`Azul`, `Pliegues`, `Rojo`), `Franja`, `Hoja` y `Sombra`.
- **Marcadores Lottie** (Glaxnimate los borra al exportar; el pipeline los vuelve a poner a partir del `.fuente.json`):
  - `marcar`: fotogramas **0–44** (0.73 s).
  - `salir`: fotogramas **44–56** (0.2 s).

## Línea de tiempo (fotogramas a 60 fps)

| Fotogramas | Qué pasa | Constante en `construir_marca.py` |
|---|---|---|
| 0–12 | La papeleta entra centrada con zoom (85 % → 100 %) y fundido | — |
| 0–14 | Entra la mano desde abajo a la derecha | `S0` |
| **14–30** | **Rayón vertical** de arriba abajo, cruzando la línea negra; la punta del plumón sigue el trazo | `S0`, `S1`, `STRK0`, `STRK1`, `BOW` |
| 30–38 | El borde de la casilla se pone azul y el rayón da un pequeño pulso | — |
| 30–44 | Sale la mano | `MARK_END` |
| 44–56 | **Salir:** la papeleta se encoge al 92 % y se desvanece | `DUR` |

## Cambios frecuentes

| Quiero… | Dónde |
|---|---|
| Alargar el rayón | `S0` y `S1`. Si pasa de `MARK_END`, sube también `MARK_END` y `DUR`. Los marcadores se calculan solos. |
| Cambiar la forma del rayón | `STRK0` y `STRK1` (inicio y fin) y `BOW` (curvatura en px). La línea negra está en `LINE0` y `LINE1`. |
| Tamaño de la mano | `HS` (porcentaje) |
| Tamaño en pantalla | En el CSS de la web, no en la animación: `width: clamp(240px, 34vw, 420px)` |
| Retoque visual fino | En Glaxnimate y luego `pipeline.py desde-rawr marca` (lee las advertencias del README raíz) |

Después de cualquier cambio: `pipeline.py marca`, luego `pipeline.py verificar marca_vota6/glaxnimate/marca-vota6.rawr 3 10 20 28 36 44 50`, y revisa `herramientas/_salida/hoja.png`.

## Cómo usarlo en la web (transición de página)

Implementado en `navegar()` de `demo-completa.html`:

1. Al pulsar una opción del header, marca **al instante** el botón como activo (`aria-current="page"`).
2. Si la página nueva necesita datos, **lanza la petición ya**, en paralelo con la transición.
3. Muestra una capa **fija que cubre el contenido pero no el header** (`inset: <alto del header> 0 0 0`, fondo `rgba(255,248,225,.95)` con `backdrop-filter: blur(4px)`) con la papeleta **centrada** a `clamp(240px, 34vw, 420px)`.
4. Reproduce el segmento `marcar` y, al terminar, **cambia el contenido** detrás y hace scroll arriba.
5. Reproduce `salir` y oculta la capa.
6. Si los datos todavía no llegaron, la página nueva muestra el loader (`loading_vote`) en la zona que los espera.
7. Ignora los clics mientras dura la transición (variable `ocupado`).

```js
const seg = n => { const m = MARCA.markers.find(x => x.cm === n); return [m.tm, m.tm + m.dr]; };
const reproducir = n => new Promise(ok => { anim.addEventListener('complete', ok, { once: true }); anim.playSegments(seg(n), true); });
await reproducir('marcar'); cambiarPagina(); await reproducir('salir');
```

A velocidad 1× la transición dura 0.93 s. Si se siente lenta, usa `anim.setSpeed(1.3)` (≈0.7 s). Úsala solo al cambiar de sección desde el header, no en la carga inicial ni al volver atrás con el navegador.

## Créditos

La mano se basa en el emoji ✍🏽 de [Noto Emoji](https://github.com/googlefonts/noto-emoji) (Google, **Apache 2.0**), modificado: lápiz recoloreado con la paleta de la campaña y recortes aplanados.
