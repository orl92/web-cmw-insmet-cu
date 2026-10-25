# Centros de costo: elegirlos de una lista en vez de tipearlos de memoria

## Objetivo

Que quien emite una factura **no tenga que saberse de memoria** los códigos de
centro de costo: que la pantalla de factura se los ofrezca para elegir, sin perder
ninguno de los repartos que el CMP ya hizo de verdad.

## Problema

El campo «Centro de Costo» del formset de imputación es un `<input type="text">`
libre. El operador tiene que recordar que el centro de «Monitoreo del tiempo con el
uso del Radar» es `700.50107` y el de «Pronóstico especializado para la Apicultura»
es `700.50207`, porque el código del centro viaja escondido en el prefijo del código
de servicio (`700501072507005` → `700.50107`) y no se muestra en ningún lado.

Hoy el único alivio es `prefijarImputacion()`: al marcar suscripciones, el JS
**precarga** los centros que deduce de los códigos. Eso resuelve el camino por lote
cuando el servicio tiene código, pero no el reparto a mano:

- la factura 276 reparte **un solo ítem entre tres centros** (25/65/10);
- la 279 reparte a dos (90/10).

En esos casos hay que **agregar filas y escribir el centro a mano**. Si el operador
no se acuerda del código, inventa uno y la imputación contable sale mal.

## Evidencia (medida sobre la base real de desarrollo)

| Dato | Valor |
|---|---|
| Servicios comerciales | 4 |
| Centros derivados de sus códigos | `700.50107` (Radar, Tormentas Eléctricas), `700.50207` (Apicultura, Certificación Agrometeorológica) |
| Imputaciones guardadas | 2 filas, ambas `700.50207` al 100 % (facturas 2026-0001 y 2026-0002) |
| Catálogo resultante (servicios ∪ ya imputado) | `['700.50107', '700.50207']` |

Los centros `90/10` y `25/65/10` de las facturas 276 y 279 **no salen de ningún
código de servicio** (así lo documenta `InvoiceCostAllocation`). Por eso el catálogo
no puede ser una lista cerrada: tiene que ofrecer lo conocido **y** dejar escribir un
centro nuevo.

## Decisión

Se mantiene la tabla `InvoiceCostAllocation` con **porcentaje manual** (así las tres
facturas reales siguen siendo representables y el reparto sigue siendo la decisión de
quien emite), y se cambia **solamente cómo se entra el centro**: un `<datalist>` con
los centros conocidos.

`<datalist>` y no un `<select>` a propósito:

- **reconoce, no recuerda**: al enfocar o escribir dos dígitos aparecen los centros;
- **no cierra la puerta**: un centro nuevo (los que no salen de ningún servicio, como
  los de la 276/279) se puede escribir igual;
- es HTML nativo: cero librerías, cero build, coherente con la restricción de JS
  vanilla del proyecto;
- el campo sigue siendo un `CharField`: no cambia el POST, ni la migración, ni los
  valores históricos, así que no hay superficie de regresión.

## Alcance

**Dentro**

- **T1** `centros_de_costo_conocidos()` en `apps/commercial/views/invoice_utils.py`:
  unión de los centros derivados de los códigos de los servicios comerciales y de los
  `codigo` ya presentes en imputaciones guardadas. Ordenada, sin duplicados, sin
  inventar centros a partir de códigos que no los contienen.
- **T2** En `InvoiceCostAllocationForm`, el widget de `codigo` apunta al catálogo
  (`list="centros-de-costo"`, `autocomplete="off"`).
- **T3** La vista de creación pasa el catálogo al contexto.
- **T4** `<datalist id="centros-de-costo">` en `create.html`, **fuera** de
  `#cost-container` (`prefijarImputacion()` hace `innerHTML = ''` sobre ese
  contenedor y se lo llevaría puesto), más el copy ajustado.
- **T5** Tests del catálogo, del markup y del caso «centro fuera del catálogo».
- **T6** Arreglar el `ruff` F401 pendiente de `views/invoices.py:4`.

**Fuera**

- El reparto en sí (sigue manual, con la regla de sumar 100 % que ya vive en
  `InvoiceCostAllocationFormSet`).
- El prefill en partes iguales de `prefijarImputacion()`: sigue siendo el punto de
  partida que ya está documentado como tal, no una regla.
- El bug del picker de fechas (`tempus-init.js` / filas clonadas): hilo aparte, sin
  causa raíz confirmada.
- Endurecer `Invoice.clean()`/`_validar_contrato()` (no corre en estos caminos).

## Restricciones

- **Sesión paralela**: NO tocar `.../invoice/list.html`, `.../subscription/list.html`,
  `views/list_status.py`, `templates/includes/commercial/invoice/actions_cell.html`,
  `status_cell.html`, `views/subscriptions.py` ni `test_list_live_status.py`.
- Árbol compartido: **no commitear**.
- JS vanilla, sin bundlers. Copy y comentarios en español es-mx (neutro, sin voseo).
- No se tocan los datos reales de la BD; las migraciones no se versionan.

## Criterios de aceptación

- La pantalla de factura ofrece los centros conocidos al enfocar el campo «Centro de
  Costo», sin que el operador los escriba de memoria.
- **Las tres facturas reales siguen siendo posibles**: 182 (un centro al 100 %),
  279 (dos centros 90/10) y 276 (tres centros 25/65/10 sobre un solo ítem) se pueden
  cargar y guardar desde la pantalla.
- Un centro que no está en el catálogo se puede cargar igual (el `<datalist>` sugiere,
  no restringe) y se guarda tal cual.
- El `<datalist>` sobrevive a `prefijarImputacion()` (que borra y reconstruye las
  filas): después de marcar suscripciones, el campo sigue ofreciendo el catálogo.
- Un código de servicio que no contiene centro (corto o no numérico) no agrega nada
  al catálogo.
- `ruff`, `manage.py check` y la suite de `apps.commercial` en verde.

## Verificación

| Qué | Comando |
|---|---|
| Tests nuevos | `.venv/bin/python manage.py test apps.commercial.tests.test_invoice_cost_center_catalog` |
| Suite de la app | `.venv/bin/python manage.py test apps.commercial` |
| Sistema | `.venv/bin/python manage.py check` |
| Estilo Python | `.venv/bin/ruff check apps/commercial && .venv/bin/ruff format --check apps/commercial` |
| Plantilla | `.venv/bin/djlint apps/commercial/templates/pages/commercial/invoice/create.html --lint` |

## Ampliación: el centro sale solo y el reparto se ve en los dos caminos

Pedido del usuario: «cuando se selecciona un servicio ya no debería salir el centro de
costo automáticamente? […] la idea es que el usuario no tenga que teclearlo, sólo hacer
el reparto de porciento. En la factura por lote, o sea la que tiene las suscripciones
pendientes, el reparto de centro de costo que sea igual que en la manual.»

### Problema verificado

1. **Al elegir un servicio en una línea manual el centro no aparece.** El único
   disparador de `prefijarImputacion()` es el `change` delegado de los
   `.subscription-check` del lote (`create.html:849`). `updateRowFromService()`
   (`create.html:860`), que es el embudo por donde pasa toda selección de servicio de
   una línea manual (cambio, alta de fila y render inicial), nunca lo llama. El
   operador queda con la fila vacía y tiene que tipear el centro: exactamente lo que
   el `<datalist>` vino a evitar.
2. **En el lote el reparto no se ve.** La tarjeta «Imputación a centros de costo»
   está **dentro** de `#manual-container` (verificado por profundidad de `<div>`:
   `#items-container` abre en 99, la tarjeta de imputación abre en 144 y `#manual-container`
   en 72 sin cerrarse), y `loadPendingSubscriptions()` hace
   `manualContainer.style.display = 'none'` (`create.html:742`). Resultado: en el lote
   la imputación se precarga y se envía **a ciegas** — el operador no puede hacer el
   reparto, que es justo lo único que el usuario quiere seguir haciendo a mano.

### Decisión

- La tarjeta de imputación sale de `#manual-container`: se ve en los dos caminos.
- **Una sola** función deriva los centros según el modo activo: en manual, de los
  servicios elegidos en las líneas; en el lote, de las suscripciones marcadas. En los
  dos casos el centro sale del código del servicio y **el porcentaje lo pone el
  operador**.
- La regla del prefijo (`700501072507005` → `700.50107`) se resuelve **sólo en
  Python** (`_centro_de_costo_de_codigo`) y viaja resuelta al navegador
  (`commercial_services_json` y `data-centro` del endpoint de pendientes). Hoy está
  duplicada en JS (`centroDeCostoDeCodigo`, `create.html:773`) y esa duplicación es la
  que puede separar las dos mitades.
- Guarda de idempotencia: si el conjunto de centros derivados es el mismo que el de las
  filas que ya están en pantalla, **no se reconstruye nada**. Sin esa guarda, cualquier
  evento que pase por `updateRowFromService()` pisaría el reparto que el operador acaba
  de escribir.

### Alcance de la ampliación

- **W2-T1** Mover la tarjeta de imputación fuera de `#manual-container`, con un `id`
  estable en la tarjeta para poder testear que quedó afuera.
- **W2-T2** Derivación unificada y consciente del modo en el JS, con la guarda de
  idempotencia y enganchada en `updateRowFromService()`, alta y baja de fila y en los
  dos cambios de modo.
- **W2-T3** El centro viaja resuelto desde el servidor (`commercial_services_json` con
  `centro_de_costo`, `data-centro` en el endpoint de pendientes); se elimina la
  duplicación en JS.
- **W2-T4** Tests: el JSON de servicios trae el centro, el endpoint lo trae por
  suscripción, y la tarjeta de imputación quedó **fuera** de `#manual-container`
  (guarda estructural, verificada por profundidad de divs sobre el HTML renderizado).
- **W2-T5** Copy de la sección alineado (los centros se proponen solos; el reparto lo
  confirma quien emite).
- **W2-T6** Corregir la guarda de idempotencia para que decida contra el último conjunto
  **derivado** y conserve las filas que el operador agregó a mano (ver el defecto
  detectado en la verificación independiente).

### Defecto detectado en la verificación independiente (W2-T6)

La guarda de idempotencia compara el conjunto **derivado** contra **lo que hay en
pantalla** (`create.html:854`). Una fila que el operador agregó a mano nunca está en el
conjunto derivado, así que la comparación falla siempre y el rebuild
(`container.innerHTML = ''`, `create.html:860`) la descarta: se pierde el centro manual,
su porcentaje y también los porcentajes tipeados sobre los centros derivados, que
vuelven a partes iguales. Se dispara con cualquier cambio de servicio **posterior** al
reparto — por ejemplo, corregir una selección equivocada. Justo el caso de la factura
real con tres centros sobre un solo ítem.

**Corrección:** recordar aparte el último conjunto **derivado** (`ultimosDerivados`) y
decidir con él, nunca con la pantalla:

- si no falta ningún centro derivado y no sobra ninguno de los que se derivaron antes, no
  se toca nada (el reparto queda como está, con sus porcentajes);
- si hay que reconstruir, se conservan las filas que el operador agregó a mano (las que
  no estaban en `ultimosDerivados`) y el reparto se rehace en partes iguales sobre
  derivados + manuales, que sigue sumando 100 %;
- el conjunto se actualiza después de cada decisión, acierte o no reconstruya.

**Fuera:** la regla de sumar 100 % y el `<datalist>` (ya hechos); el prefill en partes
iguales como punto de partida; el bug del picker de fechas; preservar los porcentajes
tipeados sobre los centros derivados cuando el conjunto de servicios cambia (el reparto
vuelve a partes iguales; el operador lo rehace, que es justo lo que pidió hacer a mano).

### Criterios de aceptación de la ampliación

- Elegir un servicio en una línea manual hace aparecer su centro de costo sin que el
  operador escriba nada.
- Marcar suscripciones en el lote hace lo mismo, y la sección se ve (ya no se envía a
  ciegas).
- El operador puede cambiar los porcentajes y **no se le borran** mientras no cambie el
  conjunto de servicios en juego.
- Un centro fuera del catálogo se sigue pudiendo agregar a mano, y **sobrevive** a un
  cambio de servicio posterior.
- El centro se deriva con una sola regla (Python) y el navegador no la reimplementa.

## Progreso

- [x] Diagnóstico: catálogo medido sobre la base real y decisión (`datalist` sobre
      catálogo derivado, reparto manual intacto) acordada con el usuario.
- [x] T1 catálogo · T2 widget · T3 contexto · T4 `<datalist>` + copy · T5 tests · T6 F401
- [x] W2-T1 tarjeta fuera de `#manual-container`: `create.html:145`, `#manual-container`
      cierra en 144.
- [x] W2-T2 derivación unificada por modo: `prefijarImputacion()` en `create.html:845`,
      enganchada en `updateRowFromService()` (935), alta de fila (1012), las dos ramas de
      `.remove-row` (957 y 975), `switchToManualInvoice()` (659) y la carga del lote
      (762, después de `preseleccionarRegeneracion()` 758).
- [x] W2-T3 centro resuelto en el servidor: `invoices.py:158-160` agrega
      `centro_de_costo`; `invoices.py:926` emite `data-centro`; la copia JS
      `centroDeCostoDeCodigo` ya no existe.
- [x] W2-T4 tests: 14 tests nuevos en `test_invoice_cost_center_prefill.py`.
- [x] W2-T5 copy alineado.
- [x] W2-T6 guarda contra el último conjunto derivado + conservar filas manuales:
      `ultimosDerivados` en `create.html:832`, decisión con `faltan`/`sobran`
      (`865-877`), filas manuales como `enPantalla` menos `ultimosDerivados`
      (`885-887`) y `centrosFinales` sin duplicar (`890-892`). `mismoConjunto()`
      eliminado (0 referencias en `apps/`).

## Ruta y evidencia

- **Ruta por tarea:** delegada directa → un solo writer (`gentle-ai-worker`).
- **Trigger:** regla de escritura (2+ archivos no triviales: utils, form, vista,
  plantilla, tests).
- **TDD:** aplicable (runner determinista y resultado esperado claro) → exigir RED
  observado antes de implementar.
- **Verificación W2:** writer `partial` (todo verde salvo `ruff format --check
  apps/commercial`, que falla en `apps/commercial/tests/test_invoice_line_payments.py`,
  untracked de la sesión paralela: no es de esta unidad). Spot-check del padre: módulo
  nuevo 14/14 OK. Verificador independiente (RDD off + assess `high`): C1–C6 y C8
  confirmados con `archivo:línea`, C7 no verificable (árbol sucio y compartido), sin
  refutaciones. `db.sqlite3` sin restos atribuibles a esta unidad (los residuos
  `PROBE-INICIO` son del 2026-10-13).
- **TDD del JS inline:** no aplicable (el proyecto no tiene runner JS: sin npm, sin
  jsdom, sin playwright/selenium). Los tests del JS son contratos de fuente (leen el
  archivo de la plantilla) y se declaran como tales; el chequeo real es `node --check`
  más lectura.
- **Verificación W2-T6:** writer `completed` (16/16 en el módulo, 550 tests de
  `apps.commercial` OK, RED observado con 3 contratos de fuente en rojo antes del
  cambio). Verificador independiente: `partial` **sin refutaciones**; S1–S10 trazadas
  con `archivo:línea`; `check`, `ruff`, `djlint`, `node --check` y las dos suites en
  verde; `db.sqlite3` sin residuos nuevos.
- **Aristas conocidas de W2-T6 (declaradas, no bloquean):** dos filas manuales con el
  mismo código se funden en una si ocurre un rebuild; cambiar de modo sin nada
  seleccionado conserva en pantalla las filas del modo anterior; el `id` de los campos
  reconstruidos pierde el prefijo `id_` (Django usa `name`, el POST no se rompe, pero el
  `for` de la etiqueta deja de apuntar al campo); el reparto vuelve a partes iguales
  cuando el conjunto de servicios cambia, que es el punto de partida que el usuario
  pidió mantener manual.
- **RED del JS inline no verificable de forma independiente:** no hay runner y
  reproducirlo exigiría revertir código. La evidencia de RED es la del writer sobre los
  contratos de fuente.
