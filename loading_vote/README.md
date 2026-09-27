# loading_vote — Loader "Lista 6"

Animación de **carga de datos**. Se construye el 6 de cinta sobre una papeleta, la papeleta se despliega en dos tarjetas, una mano raya en vertical la línea de la casilla, la tarjeta se dobla y cae en una urna azul con la etiqueta **"LISTA 6"**. Se repite en bucle mientras se espera al servidor.

> Flujo de trabajo, requisitos y reglas generales: ver el [README de la raíz](../README.md). **No edites los `.json`, `.gif` ni `demo.html` a mano.** Se regeneran con `pipeline.py loader`.

## Archivos (`glaxnimate/`)

| Archivo | Qué es | ¿Se edita? |
|---|---|---|
| `loader-vota6-transparente.rawr` | Proyecto Glaxnimate, **variante para la web**: sin fondo, sombras grises y destellos rojos | Sí, en Glaxnimate (luego `pipeline.py desde-rawr loader`) |
| `loader-vota6-transparente.json` | Lottie final de esa variante. **Es el que usa la web.** | No, se genera |
| `loader-vota6.rawr` | Proyecto Glaxnimate, **variante con fondo amarillo** a sangre (para GIF, redes y presentaciones) | Igual que arriba |
| `loader-vota6.json` | Lottie final con fondo | No, se genera |
| `loader-vota6.gif` | GIF 240×240 a 30 fps, sacado de la variante con fondo | No, se genera |
| `*.fuente.json` | Lottie intermedio que escribe `construir_loader.py` antes de pasar por Glaxnimate | No, se genera |
| `demo.html` | Demo: tabla de candidatos, botón "Cargar", servidor simulado lento y loader sobre la tabla. Lleva el `.json` incrustado. | No; la plantilla es `herramientas/plantillas/demo-loader.tpl.html` |

## Especificaciones

- Lienzo **240×240**, **60 fps**, **210 fotogramas (3.5 s)**, en bucle.
- Script: `herramientas/construir_loader.py`. Sin argumentos genera la variante con fondo; con `transparente`, la variante web.
- Capas (de arriba abajo): **Papeleta** (con la máscara **"Ranura"**, que recorta la papeleta por encima de la ranura para que parezca que entra en la urna), **Destellos**, **Urna** y **Fondo** (este último solo en la variante con fondo).
- Grupos con nombre dentro de las capas, visibles en Glaxnimate:
  - **Papeleta › Abierta:** `Mano`, `Tarjeta casilla` (`Rayón`, `Línea impresa`, `Casilla`, `Pliegue`, `Hoja`, `Sombra`), `Unión`, `Seis` (`Azul`, `Pliegues`, `Cinta roja`), `Hoja`, `Sombra hoja`.
  - **Urna:** `Texto LISTA 6` (`6` en rojo, `LISTA` en azul), `Etiqueta`, `Ranura`, `Borde tapa`, `Tapa`, `Sombra interna`, `Cuerpo`, `Sombra suelo`.

## Línea de tiempo (fotogramas a 60 fps)

| Fotogramas | Qué pasa | Constante en `construir_loader.py` |
|---|---|---|
| 0–18 | La papeleta entra desde arriba con rebote | `F(0)`–`F(10)` |
| 22–47 | Aparece la cinta roja del 6 (zoom + fundido) | `F(12)`–`F(26)` |
| 40–58 | Aparecen los pliegues oscuros | `F(22)`–`F(32)` |
| 47–68 | Aparece la parte azul con rebote | `F(26)`–`F(38)` |
| 64–78 | La tarjeta del 6 se desliza 32 px a la izquierda y **se despliega la tarjeta de la casilla** (pegada, con un pliegue fino) | `OPEN0`, `OPEN1` |
| 72–84 | Entra la mano | `HAND_IN`, `S0` |
| **84–108** | **Rayón vertical** sobre la línea negra (0.4 s); la punta del plumón sigue el trazo | `S0`, `S1` |
| 108–114 | La casilla se pone azul | `S1` |
| 108–128 | La mano se queda sobre la marca y luego sale por la derecha | `HAND_OUT0`, `HAND_OUT1` |
| 124–136 | La tarjeta derecha **se dobla** sobre la del 6 y la papeleta vuelve al centro | `FOLD0`, `FOLD1` |
| 136–157 | Anticipación hacia arriba y caída en la urna | `FOLD1 + 5`, `F(74) + POST` |
| 154–186 | La urna se aplasta y rebota | `F(72…90) + POST` |
| 157–193 | Destellos sobre la ranura | `F(74…94) + POST` |
| 193–210 | Pausa antes de repetir | `DUR` |

- `F(pct)` convierte un porcentaje de la **línea de tiempo original de 3 s** (180 fotogramas) a fotogramas.
- `POST = 24` es el retraso que se añadió a todo lo posterior al rayón cuando se alargó de 0.2 s a 0.4 s.
- Para alargar o acortar el rayón, cambia `S0`, `S1` y desplaza en la misma cantidad `HAND_OUT*`, `FOLD*`, `POST` y `DUR`.

## Cambios frecuentes

| Quiero… | Dónde |
|---|---|
| Cambiar el texto de la urna | Convertir el texto nuevo a trazado con Inkscape (ver README raíz), guardarlo en `herramientas/fuentes/` y cambiar `lista_p.svg` en `construir_loader.py`. Ajustar el ancho de `Etiqueta` y el centrado (bbox). Los glifos con x > 59 se pintan de rojo (el "6"): revisa ese umbral. |
| Cambiar colores | Constantes `Y`, `R`, `B` y los `lgrad(...)` de `construir_loader.py`. Las sombras y destellos por variante están en `SHADOW_C`, `SHADOW_K` y `SPARK_C` (al principio del archivo). |
| Cambiar velocidad global | Mejor hacerlo desde la web con `anim.setSpeed(x)` que tocar los fotogramas. |
| Retoque visual fino | Hazlo en Glaxnimate sobre **los dos** `.rawr` y ejecuta `pipeline.py desde-rawr loader` (lee las advertencias del README raíz). |

Después de cualquier cambio: `pipeline.py loader`, luego `pipeline.py verificar loading_vote/glaxnimate/loader-vota6.rawr 30 60 76 96 112 130 150 170`, y revisa `herramientas/_salida/hoja.png`.

## Cómo usarlo en la web

Hay que usar **`loader-vota6-transparente.json`**, no el de fondo amarillo: ese parece una tarjeta pegada sobre la página.

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js"></script>
```

Pautas, implementadas en `conLoader()` de `demo-completa.html` y en `demo.html`:

1. Pon un **velo** (`position:absolute; inset:0; background:rgba(255,255,255,.8); backdrop-filter:blur(2px)`) **solo sobre la zona que espera datos** (la tabla o el resultado), con el loader centrado a unos **160–170 px** y un texto como "Cargando candidatos…".
2. **Muéstralo solo si la respuesta tarda más de 200 ms**, para evitar parpadeos.
3. Una vez visible, **mantenlo al menos 1.2 s**.
4. Debajo, muestra **filas esqueleto** en gris; al llegar los datos, desvanece el velo y anima la entrada de las filas.
5. Marca la zona con `aria-busy="true"` y el velo con `role="status"`. Desactiva el botón mientras carga.
6. Llama a `anim.destroy()` al ocultarlo, para no dejar animaciones corriendo.

Si la carga ocurre justo después de una **transición de página** (`marca_vota6`), muestra el loader **sin los 200 ms de espera**, porque el usuario ya estuvo esperando. Ver `montar()` de Candidatos en `demo-completa.html`.
