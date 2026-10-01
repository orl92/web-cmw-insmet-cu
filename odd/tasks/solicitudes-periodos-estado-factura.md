# Solicitudes libres, periodos elegibles y estado real de la factura

## Objetivo

Que el cliente pueda pedir un servicio **las veces que quiera, en las fechas que
quiera y con la duración que elija en días o meses**, y que el dashboard diga la
verdad sobre si el PDF se generó y si el correo salió, en lugar de un único
"reintentando" que no distingue nada.

## Problema

Son tres problemas distintos que se NOS diagnosticaron en producción y que hoy
viven en el mismo flujo.

### 1. El periodo no lo elige el cliente

`ServiceSubscription` ya **es** la solicitud: tiene `start_date`, `end_date`,
`quantity` y `payment_status`. No hay modelo nuevo que crear. El problema es
quién decide la duración:

- La **unidad** sale del servicio, no del cliente. `Service.compute_end_date()`
  hace `agrometeo → relativedelta(months=quantity)`, todo lo demás
  `timedelta(days=quantity)`.
- El **formulario del dashboard** tiene un `period` rígido de cuatro opciones
  (`1m`, `3m`, `6m`, `1y`, `custom`) que no corresponde a la unidad real.
- El **formulario público de home** sí usa `start_date` + `quantity`, pero con
  la unidad forzada por el servicio.

Consecuencia: un cliente que necesita 45 días no tiene forma de pedirlo sin
elegir `custom` y calcular la fecha a mano, y no puede pedir "2 años".

### 2. El guard de duplicados va al revés de lo que se recuerda

`apps/home/views/servicios/comerciales/views.py:152-160` bloquea una segunda
petición si ya hay una en `requested` o `pending`:

```python
existing = (
    ServiceSubscription.objects.filter(customer=customer, service=self.service)
    .filter(payment_status__in=['requested', 'pending'])
    .first()
)
if existing:
    messages.warning(request, 'Ya tienes una solicitud o suscripción para este servicio.')
```

Esto es lo **opuesto** al comportamiento buscado, y está fijado por tests
(`apps/commercial/tests/test_views.py:1371` y `:1394` aceptan el mensaje;
`apps/home/tests/test_services_ui.py:947` exige que no aparezca). Hay que
eliminar el guard **y** los tests que lo.codifican.

### 3. El estado del worker no distingue PDF de correo

`generate_invoice_pdf_and_email_task` hace las dos cosas en una sola función. Si
el correo falla, Huey reintenta la tarea **entera** y vuelve a renderizar el PDF
que ya estaba bien. El dashboard muestra `RETRYING` y el usuario no sabe si lo
que falló fue el PDF o el correo. En `Invoice` hoy existen `email_sent` y
`email_error`, pero **no hay estado ni error del PDF**: la única señal de que el
PDF existe es que el archivo esté en disco.

De ahí salen las dos quejas de UX:

- **Botones siempre visibles.** `invoice/list.html:69` y `:81-87` pintan el
  enlace de descarga y el modal de vista previa sin condicionar a que el PDF
  exista.
- **El reintento abre una fila nueva.** `TaskMonitoringActionView.post()`
  (`apps/dashboard/views/dashboard/dashboard.py:462-477`) reencola la función y
  **nunca toca el registro**: la tarea nueva nace con otro `task.id`, y
  `apps/core/apps.py:108-120` hace `update_or_create(task_id=task.id)`, así que
  crea una fila nueva. La fila del error original queda congelada para siempre.

La tabla tampoco dice de quién es la tarea: solo `task_name` y `task_id`.

## Por qué importa

El PDF se genera bien y el correo falla —que es el caso normal sin SMTP real— y
el operador ve "reintentando" sobre un PDF que ya existe. Eso hace creer que
hay un problema de renderizado que no existe, y hace que el botón de "ver
factura" aparezca para facturas que quizá ni siquiera tienen archivo.

## Alcance

### A. Persona natural con nombre y carnet

- **A1** Nombre y apellidos en la persona natural, junto al documento de
  identidad, para que el bloque de la factura no sea un campo suelto.
- **A2** El listado de clientes debe mostrar el carnet en la columna
  Identificación cuando es persona natural. Hoy `customer/list.html:42-44` solo
  renderiza `reeup` y `nit`, que son de la jurídica.

### B. Solicitudes y periodos

- **B1** Quitar el guard de duplicados: tantas solicitudes como quiera el
  cliente. Actualizar los tests que lo codifican.
- **B2** Que el cliente elija la unidad del periodo (días o meses) y la fecha de
  inicio libremente, incluso en el pasado.
- **B3** Formularios de crear y editar suscripción alineados al modelo nuevo.
- **B4** Facturación manual alineada al mismo modelo.
- **B5** Quitar la columna Expiración del listado de suscripciones
  (`subscription/list.html:15` y celda `:46-47`): con historial completo la
  expiración deja de ser el eje de la tabla.
- **B6** Home "mis servicios" y dashboard: mostrar **todas** las solicitudes
  como histórico, no solo las vigentes.

### C. Estado real de la factura

- **C1** Estado y error explícitos del PDF en `Invoice`, no implícitos en la
  existencia del archivo.
- **C2** Botones de ver y descargar solo cuando el PDF se generó bien.
- **C3** Poder reintentar solo el paso que falló, sin re-renderizar el PDF.
- **C4** El reintento actualiza la **misma** fila de la tabla de tareas.
- **C5** La tabla de tareas dice de qué cliente es cada tarea.

### D. Pendientes anteriores

- **D1** `Invoice #14` quedó con `subscription_id = NULL`, así que no encuentra
  el contrato aunque exista en su suscripción. Averiguar por qué la factura
  manual no enganchó la suscripción.
- **D2** `Profile.save()` revienta con `OSError: Truncated File Read` al
  re-guardar el avatar (Pillow). Falla en aislamiento; `apps/user_auth` no fue
  tocado por este trabajo.
- **D3** Documentar que **todo cambio en `apps/core/tasks.py` exige reiniciar el
  consumer**. El módulo se importa al arrancar el worker, mientras que
  `invoice_utils` se importa dentro de la función: si no se reinicia, el worker
  ejecuta una llamada vieja contra una firma nueva y tira
  `TypeError: takes 5 positional arguments but 6 were given`. Es exactamente lo
  que pasó hoy.

## Decisiones abiertas (bloquean la implementación)

1. **¿Dónde vive el nombre de la persona natural?** Reusar
   `User.first_name`/`last_name` (ya existen, la factura ya lee
   `get_full_name()`, cero migración, una sola fuente de verdad) o agregar campos
   a `Customer` (migración, autosuficiente, sobrevive a que se edite el usuario).
2. **¿Cómo se separa el estado del PDF del correo?** Agregar a `Invoice` estado
   y error de PDF y mantener **una sola** tarea Huey que va marcando cada paso
   (recomendado: los botones dependen del estado del PDF, y el reintento
   naturally cae en la misma fila) o partir en **dos** tareas Huey independientes
   (más fiel a "saber qué falló", pero duplica filas en la tabla de monitoreo).
3. **¿Cómo se representa el periodo?** Agregar `period_unit` con opciones
   días/meses y dejar la fecha de inicio libre, conservando `quantity` para el
   precio; o pedir fecha de inicio y fin y derivar cantidad y unidad del delta.

## Restricciones

- `requirements/` ya no es WIP del usuario: `redis` y `whitenoise` pasaron a
  `prod.txt` en el commit `534286b`, junto con el fix que impedía que un driver
  ausente se convirtiera en un 500.
- Las migraciones no se versionan en este repo.
- Los datos reales de la BD (`admin`, `osniel`, factura `2026-0001`) no se tocan.
- Nada de npm ni bundler; el frontend es JS vanilla.

## Criterios de aceptación

- Un cliente natural ve nombre, apellidos y carnet en la factura y en el listado
  de clientes, sin líneas vacías.
- Un cliente puede crear una segunda suscripción del mismo servicio sin
  bloqueo, con fecha de inicio pasada y duración en días o en meses.
- El listado de suscripciones no tiene columna Expiración y muestra el histórico
  completo.
- La factura manual acepta el mismo modelo de periodo.
- Los botones de ver y descargar una factura solo existen si el PDF se generó.
- Un fallo de correo no hace que el PDF se vuelva a renderizar ni que la tarea
  aparezca como reintentándose cuando el PDF ya está bien.
- Reintentar una tarea actualiza su fila y no crea otra.
- La tabla de tareas muestra el cliente.

## Checks aplicables

| Cambio | Verificación |
|---|---|
| Modelos, vistas, formularios, permisos | `python manage.py test apps.commercial apps.home apps.core apps.dashboard` |
| Plantillas | `djlint . --lint` y `djlint . --reformat --check` (los hooks) |
| Todo | `python manage.py check` + Ruff |

## Progreso

- [x] Diagnóstico completo de los tres problemas, con file:line.
- [ ] A1, A2
- [ ] B1, B2, B3, B5, B6 → B1 y B5 cerrados en `2a7dbad`
- [x] B4 — commit `385c12a`
- [x] C1, C2, C3, C4, C5 — commit `4b1dff5`
- [ ] D1
- [x] D2 — commits `0ce468a`…`1b644fc`
- [ ] D3

**B4 cerrado.** La línea manual ya deriva `codigo`, `precio` y `unidad_medida`
del `Service` en `clean()`, así que el POST no fija el precio; `cantidad` es
required y editable, y la plantilla propone. `service_category` viaja al
navegador porque la unidad no es elegible: sale de la categoría.

**Un límite del modelo que conviene no olvidar:** el servidor calcula el
vencimiento como `start + relativedelta(months=N)`, y eso no reproduce
cualquier par (inicio, fin) — entre 01/01 y 31/01 no existe ningún N entero.
La cantidad en meses que propone el navegador redondea contra el promedio real
del año (mediana de 2 días de desvío), pero el residuo no baja de medio mes
mientras el modelo acepte sólo meses enteros. Es una decisión de B2 pendiente:
si el cliente elige inicio y fin, el servidor tendría que derivar la cantidad
en vez de al revés.

**B1 cerrado.** El bloqueo de duplicados estaba en **dos** capas: `form_valid`
descartaba el POST (`apps/home/views/servicios/comerciales/views.py:152`) y el
template escondía el formulario (`service_detail.html:65`). Quitar solo una
deja el comportamiento a medias, así que caerán las dos: el aviso queda
informativo sobre lo ya solicitado y la vía de pedir sigue abierta. Los
cuatro tests que afirmaban el bloqueo se reescribieron como afirmaciones del
comportamiento nuevo, no se borraron.

**B5 cerrado.** El listado de suscripciones perdió la columna Expiración y el
badge Vencido que colgaba de ella. Ningún test dependía de esa columna.

**Siguiente paso:** B2 es el que decide el modelo de periodo y conviene hacerlo
antes que B3, porque B3 alinea los formularios con lo que B2 defina.

**Ruta prevista:** B y C tocan modelos, formularios, vistas y templates, así que
van delegados a un escritor por bloque. D3 es documentación y va inline.
