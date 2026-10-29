# mercado_local — Logo "Mercado Local" animado

Animación del logo **Mercado Local** (tienda con toldo amarillo, puerta roja, un ave y dos olas). **El diseño no cambia**: formas, colores y grosores se leen del SVG original (`resources/mercado-local.svg`) y solo se añade movimiento. Tiene dos partes:

1. **Entrada** (1.5 s): el logo se arma (marco, toldo, puerta, olas y ave) y termina **idéntico al SVG**.
2. **Bucle** (3 s, se repite sin fin): las olas fluyen, el ave aletea y planea y el toldo se mece. La tienda no se mueve.

> Flujo de trabajo, requisitos y reglas generales: ver el [README de la raíz](../README.md). **No edites los `.json`, el `.gif` ni `demo.html` a mano.** Se regeneran con `pipeline.py mercado`.

## Archivos

| Archivo | Qué es | ¿Se edita? |
|---|---|---|
| **`glaxnimate/produccion/logo-mercado-local.min.json`** | ⭐ **El archivo para el sitio web.** Optimizado (55 KB, ≈6 KB con gzip), **con los marcadores `entrada` y `bucle`**. Se reproduce con `lottie_light.min.js`. | No, lo genera el pipeline |
| `glaxnimate/logo-mercado-local.rawr` | Proyecto Glaxnimate | Sí, en Glaxnimate (luego `pipeline.py desde-rawr mercado`) |
| `glaxnimate/logo-mercado-local.json` | Lottie exportado por Glaxnimate con los marcadores reinyectados, sin optimizar | No, se genera |
| `glaxnimate/logo-mercado-local.gif` | GIF 240×288 sobre blanco, 30 fps (entrada + un bucle; el GIF repite también la entrada) | No, se genera |
| `glaxnimate/logo-mercado-local.fuente.json` | Lottie intermedio que escribe `construir_mercado.py` | No, se genera |
| `demo.html` | Demo: el logo en un header, sobre blanco y sobre gris, con "Repetir entrada", pausa y velocidad. Plantilla: `herramientas/plantillas/demo-mercado.tpl.html` | No, se genera |

## Especificaciones

- Lienzo **240×288** (el viewBox 120×144 del SVG a escala 2), **60 fps**, **270 fotogramas**, **fondo transparente**.
- **Marcadores Lottie** (Glaxnimate los borra al exportar; el pipeline los vuelve a poner):
  - `entrada`: fotogramas **0–90** (1.5 s).
  - `bucle`: fotogramas **90–270** (3 s). El fotograma 90 y el final del bucle son el mismo estado, así que el bucle empalma sin salto.
- Script: `herramientas/construir_mercado.py`. Lee cada parte del SVG por su `data-logo-part` (`bird`, `door`, `frame`, `roof`, `wave-1`, `wave-2`, y la pared blanca) y **comprueba** que la geometría que genera coincide con la del SVG.
- Capas (de arriba abajo, en el mismo orden de pintado que el SVG): **Olas** (`Ola 2`, `Ola 1`), **Tienda** (`Toldo › Despliegue`, `Marco`, `Puerta`, `Pared`) y **Ave**.

### Cómo se mueven las olas sin cambiar el dibujo

Cada ola del SVG son 4 arcos cuadráticos que se repiten cada dos (sus controles van a 11 y a 12 unidades del inicio de cada arco, no al centro). El script toma esa ola infinita, la desplaza y la recorta al mismo tramo (x de 14 a 106), así que **la forma de cada arco no cambia, solo se desliza**. Los vértices del trazado son los cortes entre arcos: se mueven con la ola y, al salir del tramo, se quedan a 0.01 del extremo para no romper la punta redondeada. El script comprueba que en reposo la ola es exactamente la del SVG y que entre keyframes el error es menor de 0.08 unidades (0.16 px).

Las dos olas fluyen hacia la derecha a la misma velocidad; la segunda se retrasa y adelanta hasta 2 unidades (`RETRASO`) y vuelve a coincidir en el fotograma 90. **No uses sentidos opuestos**: cuando quedan en contrafase, la cresta de una toca el valle de la otra y parecen fundirse.

## Línea de tiempo (fotogramas a 60 fps)

| Fotogramas | Qué pasa | Constante en `construir_mercado.py` |
|---|---|---|
| 0–28 | El marco se dibuja (baja por la izquierda, cruza y sube por la derecha); la pared aparece (6–24) | `MARCO0`, `MARCO1` |
| 16–42 | El toldo se despliega hacia abajo desde su borde de arriba, con un pequeño rebote | `TOLDO0`, `TOLDO1` |
| 36–54 | La puerta crece desde el suelo con rebote | `PUERTA0`, `PUERTA1` |
| 40–68 / 48–76 | Se dibujan las olas, de izquierda a derecha (ya fluyendo) | `ola("wave-1", (40, 68))`, `ola("wave-2", (48, 76))` |
| 54–88 | El ave entra volando desde la derecha y aletea dos veces | `LLEGA0`, `LLEGA1`, `ALETEOS` |
| **90** | **Logo completo, idéntico al SVG**: empieza el bucle | `ENTRADA` |
| 90–122 | El ave aletea dos veces (las puntas de las alas bajan y suben) | `ALETEOS` |
| 90–270 | Las olas avanzan una longitud de onda; el ave planea (sube y baja 1.6, gira ±2.5°); el toldo se mece ±1.2° colgado de su borde de arriba y se estira un 2 % dos veces | `BUCLE`, `RETRASO`, `ave_pos`, `mece`, `estira` |

## Cambios frecuentes

| Quiero… | Dónde |
|---|---|
| Entrada más rápida o más lenta | Las constantes de la tabla (`MARCO*`, `TOLDO*`, `PUERTA*`, `LLEGA*`) y `ENTRADA`. Los marcadores se calculan solos |
| Bucle más largo o más corto | `BUCLE` (todo el movimiento del bucle está en función de `ciclo(f)` y se adapta solo) |
| Olas más rápidas | Que avancen 2 longitudes de onda por bucle: multiplica `ciclo(f)` por 2 en `desplaza_ola` (tiene que ser un número entero para que empalme) |
| Toldo más o menos movido | Amplitudes en `mece` (1.2°) y `estira` (2 %) |
| Ave más o menos movida | `ALETEOS` (cuándo aletea) y las amplitudes en `ave_pos` |
| Retoque visual fino | En Glaxnimate y luego `pipeline.py desde-rawr mercado` (lee las advertencias del README raíz) |

Después de cualquier cambio: `pipeline.py mercado`, luego `pipeline.py verificar mercado_local/glaxnimate/logo-mercado-local.rawr 12 20 30 45 60 75 90 135 180 225`, y revisa `herramientas/_salida/hoja.png`. El fotograma 90 tiene que verse **igual que el SVG**.

## Cómo usarlo en la web

Usa **`glaxnimate/produccion/logo-mercado-local.min.json`** con `lottie_light.min.js`: reproduce la entrada una vez y deja el bucle repitiéndose.

```html
<div id="logo" style="width: 120px; aspect-ratio: 120 / 144" role="img" aria-label="Mercado Local"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie_light.min.js"></script>
<script>
  const anim = lottie.loadAnimation({ container: document.getElementById('logo'), renderer: 'svg',
                                      loop: false, autoplay: false, path: '/animaciones/logo-mercado-local.min.json' });
  anim.addEventListener('DOMLoaded', () => {
    const seg = n => { const m = anim.animationData.markers.find(x => x.cm === n); return [m.tm, m.tm + m.dr]; };
    anim.addEventListener('complete', () => { anim.loop = true; anim.playSegments(seg('bucle'), true); });
    anim.playSegments(seg('entrada'), true);
  });
</script>
```

- Para mostrar el logo **quieto** (por ejemplo, si respetas `prefers-reduced-motion`), usa `anim.goToAndStop(90, true)`: es exactamente el SVG.
- Para la cabecera, el logo se ve bien a partir de unos 40 px de ancho.
- Si el bucle distrae, `anim.setSpeed(0.75)` lo hace más tranquilo.
