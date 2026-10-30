# barco_transicion — Transición "Velero Carlos Astudillo"

Animación del velero **Carlos Astudillo · Lista 6** para usar como **transición entre páginas**: el velero entra navegando, se mece sobre el agua mientras carga la página nueva y sale navegando. **El diseño no cambia**: formas, colores y degradados se leen del SVG original (`resources/carlos-astudillo.svg`) y solo se añade movimiento:

- El **barco** cabecea (±3°) y sube y baja con el oleaje. Ciclo de 3 s.
- La **bandera** ondea suavemente y el **6 no se deforma**: se desplaza y se inclina (hasta 5°) siguiendo la tela.
- Las **velas** se hinchan con cada racha de viento. Solo se mueve su borde libre; los bordes sujetos al mástil y a la botavara no se mueven, así que nunca se separan.

**Única diferencia con el SVG:** el hueco de la vela mayor (el segundo subtrayecto de `marco-vela-mayor`), que en el SVG es transparente, se rellena de **blanco**. Las separaciones finas entre piezas siguen transparentes.

> Flujo de trabajo, requisitos y reglas generales: ver el [README de la raíz](../README.md). **No edites los `.json`, el `.gif` ni `demo.html` a mano.** Se regeneran con `pipeline.py barco`.

## Archivos

| Archivo | Qué es | ¿Se edita? |
|---|---|---|
| **`glaxnimate/produccion/barco-transicion.min.json`** | ⭐ **El archivo para el sitio web.** Optimizado (53 KB, ≈8.4 KB con gzip), **con los marcadores `entrar`, `bucle` y `salir`**. Se reproduce con `lottie_light.min.js`. | No, lo genera el pipeline |
| `glaxnimate/barco-transicion.rawr` | Proyecto Glaxnimate | Sí, en Glaxnimate (luego `pipeline.py desde-rawr barco`) |
| `glaxnimate/barco-transicion.json` | Lottie exportado por Glaxnimate con los marcadores reinyectados, sin optimizar | No, se genera |
| `glaxnimate/barco-transicion.gif` | GIF 320×320 sobre blanco, 30 fps (entrar + un bucle + salir) | No, se genera |
| `glaxnimate/barco-transicion.fuente.json` | Lottie intermedio que escribe `construir_barco.py` | No, se genera |
| `demo.html` | Demo: web de ejemplo cuyo menú usa la transición, con carga simulada (inmediata, 1.5 s, 4 s) y una vista previa del bucle. Plantilla: `herramientas/plantillas/demo-barco.tpl.html` | No, se genera |

## Especificaciones

- Lienzo **320×320** (el SVG es 1254×1254), **60 fps**, **270 fotogramas**, **fondo transparente**.
- **Marcadores Lottie** (Glaxnimate los borra al exportar; el pipeline los vuelve a poner):
  - `entrar`: fotogramas **0–45** (0.75 s). Llega desde la izquierda frenando, con fundido.
  - `bucle`: fotogramas **45–225** (3 s). Se mece en el sitio; se repite sin salto.
  - `salir`: fotogramas **225–270** (0.75 s). Se va por la derecha acelerando, con fundido.
- **Puntos de reposo:** en los fotogramas **45, 135 y 225** (al empezar y a mitad del bucle) el velero está exactamente como en el SVG. `entrar` termina en uno y `salir` empieza en otro, así que **solo se debe pasar del bucle a `salir` en un punto de reposo** (ver el código de abajo). El script comprueba que en esos fotogramas no hay deformación.
- Script: `herramientas/construir_barco.py`. Lee cada pieza del SVG por su `id` (`velas`, `bandera`, `lista-6`, `mastil`, `borda`, `casco`, `quilla`, `nombre`) con sus degradados.
- Una capa, **Velero**, con el grupo `Barco` (cabeceo, oleaje, entrada y salida) y dentro, en el orden de pintado del SVG: `Nombre`, `Quilla`, `Casco`, `Borda`, `Mástil`, `6`, `Bandera` y `Velas` (`Reflejo vela menor`, `Vela menor`, `Vela mayor`, `Marco vela mayor`, `Hueco blanco`).

### Cómo se mueven sin cambiar el dibujo

- **Bandera:** a cada punto se le suma un desplazamiento vertical en forma de onda que viaja hacia la punta. Es nulo en el borde pegado al mástil y crece hacia la punta (hasta ~24 unidades del SVG). Se resta la forma inicial de la onda, así que en los puntos de reposo el desplazamiento es 0.
- **Velas:** cada vela es un triángulo (puño alto, amura y puño bajo). El peso de cada punto vale 0 en los bordes sujetos y 1 en el centro del borde libre, y el borde libre se aleja de la amura hasta 24 (mayor) y 18 (menor) unidades con cada racha (`sin²`, dos por bucle). Las rectas que se curvan se dividen en tramos, que en reposo siguen siendo la misma recta.
- **Optimización:** la deformación de las velas es lineal en la racha, y la racha sigue la curva *ease-in-out sine*. Por eso bastan keyframes cada 45 fotogramas con esa curva, y el cabeceo igual. La bandera y el 6 se muestrean cada 9 fotogramas y la posición cada 3 en la entrada y la salida.

## Línea de tiempo (fotogramas a 60 fps)

| Fotogramas | Qué pasa | Constante en `construir_barco.py` |
|---|---|---|
| 0–45 | **Entrar**: llega desde 140 unidades a la izquierda frenando; fundido de entrada en 0–18 | `ENTRAR`, `ENTRA_X`, `FUNDIDO` |
| 45 | Reposo: idéntico al SVG (con el hueco blanco) | — |
| 45–225 | **Bucle**: cabeceo ±3° (ciclo 3 s) y oleaje ±10 unidades (dos por ciclo); la bandera ondea y las velas se hinchan dos veces | `BUCLE`, `CABECEO`, `OLEAJE`, `ONDA_A`, `ONDA_L`, `ONDA_T`, `vela(…)` |
| 135 | Reposo (mitad del bucle) | — |
| 225–270 | **Salir**: se va 170 unidades a la derecha acelerando; fundido de salida en 252–270 | `SALIR`, `SALE_X`, `FUNDIDO` |

## Cambios frecuentes

| Quiero… | Dónde |
|---|---|
| Más o menos vaivén | `CABECEO` (grados) y `OLEAJE` (unidades del SVG) |
| Bandera más o menos agitada | `ONDA_A` (amplitud), `ONDA_L` (longitud de onda) y `ONDA_T` (periodo; tiene que dividir a `BUCLE` / 2 para que haya reposo a mitad del bucle) |
| Velas más o menos hinchadas | El último número de `vela(…)` para `mayor` y `menor` |
| Entrada o salida más largas o más lejos | `ENTRAR`, `SALIR` (múltiplos de 45; el script lo comprueba), `ENTRA_X`, `SALE_X`. Los marcadores se calculan solos |
| Retoque visual fino | En Glaxnimate y luego `pipeline.py desde-rawr barco` (lee las advertencias del README raíz) |

Después de cualquier cambio: `pipeline.py barco`, luego `pipeline.py verificar barco_transicion/glaxnimate/barco-transicion.rawr 9 45 68 90 112 135 180 225 255`, y revisa `herramientas/_salida/hoja.png`. Los fotogramas 45 y 135 tienen que verse **igual que el SVG** (con el hueco de la vela en blanco).

## Cómo usarlo en la web (transición de página)

Archivo: **`glaxnimate/produccion/barco-transicion.min.json`** con `lottie_light.min.js`. Implementado en `navegar()` de `demo.html`:

1. Al pulsar una opción del menú, marca **al instante** el botón como activo y **lanza ya** la petición de la página nueva.
2. Muestra una capa fija que cubre el contenido (no el header) con el velero centrado (`width: clamp(220px, 32vw, 400px)`) y reproduce `entrar`.
3. Cambia el contenido detrás.
4. Si la página ya está lista, reproduce `salir` directamente. Si no, reproduce `bucle` y, cuando esté lista, espera al **siguiente punto de reposo** (como mucho 1.5 s) y reproduce `salir`.
5. Oculta la capa e ignora los clics mientras dura la transición.

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie_light.min.js"></script>
<script>
  const anim = lottie.loadAnimation({ container: document.getElementById('transicion-lottie'), renderer: 'svg',
                                      loop: false, autoplay: false, path: '/animaciones/barco-transicion.min.json' });
  // con path: los marcadores están en anim.animationData.markers una vez cargado (evento 'DOMLoaded')
  const marca = n => anim.animationData.markers.find(x => x.cm === n);
  const seg = n => [marca(n).tm, marca(n).tm + marca(n).dr];

  // Reproduce un segmento y espera a que termine
  const jugar = n => new Promise(ok => {
    const fin = () => { anim.removeEventListener('complete', fin); ok(); };
    anim.addEventListener('complete', fin);
    anim.loop = false;
    anim.playSegments(seg(n), true);
  });

  // Mece el velero hasta que listo() sea cierto y termina en el siguiente punto de reposo (inicio o mitad del bucle)
  const mecerHasta = listo => new Promise(ok => {
    const mitad = marca('bucle').dr / 2;
    let previo = 0;
    const mira = () => {
      const f = anim.currentFrame;                         // relativo al inicio del bucle
      const reposo = (previo < mitad && f >= mitad) || f < previo;
      previo = f;
      if (reposo && listo()) { anim.removeEventListener('enterFrame', mira); ok(); }
    };
    anim.addEventListener('enterFrame', mira);
    anim.loop = true;
    anim.playSegments(seg('bucle'), true);
  });

  // Uso: await jugar('entrar'); cambiarPagina(); if (!listo) await mecerHasta(() => listo); await jugar('salir');
</script>
```

- Toda la transición, si la carga es inmediata, dura 1.5 s (`entrar` + `salir`). Si se siente lenta, `anim.setSpeed(1.3)`.
- Para mostrar el velero **quieto** (por ejemplo, si respetas `prefers-reduced-motion`), usa `anim.goToAndStop(45, true)`: es el SVG con el hueco blanco.
