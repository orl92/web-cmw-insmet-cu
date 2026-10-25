# Estados en vivo en los listados de facturación y suscripciones

Deriva de `odd/tasks/periodo-facturacion-meses.md` (T18, que estaba en backlog).
Se separa porque es otra feature: no toca el formulario de período.

## Objetivo

Que los listados de **Facturación** y **Suscripciones** muestren el estado real de
cada fila sin recargar la página ni redibujar la tabla, y que **"Aprobar Pago"**
sólo esté disponible cuando la factura esté **emitida** (PDF listo).

## Problema (verificado contra código)

- El PDF y el correo de la factura se generan en una tarea Huey asíncrona
  (`apps/core/tasks.py::generate_invoice_pdf_and_email_task`), así que durante
  unos segundos la fila muestra un estado que ya no es el real. Hoy la única
  forma de verlo es recargar.
- `apps/commercial/templates/pages/commercial/subscription/list.html:105-112`
  muestra "Aprobar Pago" (link GET a `commercial:suscripcion_approve`) apenas
  `payment_status == 'pending'`, es decir **al crear la factura**, antes de que
  exista el PDF. Decisión del usuario: ocultarlo hasta que el PDF esté listo
  (`latest_invoice_pdf_ready`).
- Los dos listados extienden `templates/layouts/list.html`, que inicializa
  **DataTables client-side** (`new DataTable(selector, cfg)`) sobre filas ya
  renderizadas y **sin `paginate_by`** → todas las filas están en el DOM. Las
  instancias viven en `window.dataTableInstances`.
- No hay polling ni `EventSource` en el proyecto. El único AJAX del módulo
  (`ajax_pending_subscriptions`, `apps/commercial/views/invoices.py:806`)
  devuelve HTML, no JSON.

## Decisiones tomadas

- **Refresh in-place por fragmentos**: un GET devuelve el HTML ya renderizado de
  las celdas **Estado** y **Acciones** de cada fila, y el JS reemplaza el
  `innerHTML` de esas celdas. No se redibuja DataTables ni se recarga la página.
- **Una sola fuente de verdad**: la celda se extrae a un partial que usan *tanto*
  el listado como el endpoint. Nada de rearmar los botones en JS.
- **Polling acotado**: cada ~10 s, y **sólo mientras alguna fila esté en estado
  transitorio** (`pdf_status`/`email_status` pendientes). Sin transitorios no hay
  request. Pausa en pestaña oculta (`visibilitychange`).
- **"Aprobar Pago"**: visible sólo con
  `record_active and payment_status == 'pending' and latest_invoice_pdf_ready`.
  "Regenerar factura" queda como está (no lo pidió el usuario).
- La rama no-staff del listado de suscripciones (botón "Pagar con QR") **no se
  toca**.

## Restricciones

- JS vanilla, sin bundlers; el archivo nuevo va a `static/dist/js/`. Prohibido
  npm/transpilación.
- Los endpoints heredan los permisos de las vistas:
  facturas → `commercial.view_invoice`; suscripciones →
  `commercial.view_subscription` **y** el mismo filtro que
  `SubscriptionListView` (staff/superuser ven todo; grupo `Clientes` sólo lo
  propio). No filtrar datos de clientes ajenos.
- Son GET: no hay CSRF.
- Plantillas con 2 espacios, formato djlint.

## Tareas

- [x] **T1 — Partials de celdas.** Extraer de
      `apps/commercial/templates/pages/commercial/invoice/list.html` las celdas
      "Estado" (L50-58) y "Acciones" (L59-150) a partials reutilizables; ídem las
      de `subscription/list.html` (Estado L29-39, Acciones L40-240). Los
      listados las incluyen; el markup visible no cambia.
- [x] **T2 — Endpoints de estado.** Dos vistas GET que devuelven JSON con los
      fragmentos de Estado/Acciones por `uuid` (reusa `render_to_string` con
      `request=` para que `perms` y `is_superuser` sigan funcionando). URLs
      `commercial:ajax_invoice_status` y `commercial:ajax_subscription_status`.
      Con tests de permisos y de filtrado por cliente.
- [x] **T3 — Regla "Aprobar Pago".** Gatear el link con
      `latest_invoice_pdf_ready` en el partial y ajustar los tests existentes que
      asumen que el botón aparece (`apps/commercial/tests/test_views.py`,
      `apps/commercial/tests/test_subscription_list_actions.py`): sus fixtures
      necesitan una factura con PDF listo, o el botón ya no aparece.
- [x] **T4 — JS de polling.** `static/dist/js/list-live-status.js`: lee las filas
      con `data-uuid`, pide el fragmento, parchea celdas, sólo mientras haya
      transitorios, pausa en pestaña oculta. Engancharlo en los dos listados
      (marca de fila + URL del endpoint).
- [x] **T5 — Cierre.** Tests de integración del fragmento (sin PDF no aparece
      "Aprobar Pago"; con PDF sí; el payload no filtra filas de otro cliente).

## Criterios de aceptación

- Con una factura recién creada (PDF aún generándose), el listado se actualiza
  solo: aparecen descarga/ver y "Aprobar Pago" sin recargar.
- Sin PDF listo, "Aprobar Pago" **no** se ofrece.
- Un usuario del grupo `Clientes` no recibe estado de suscripciones ajenas.
- Nada de DataTables redibujado ni recarga completa.
- `apps.commercial` completo en verde, ruff y djlint limpios.

## Checks

- `.venv/bin/python manage.py test apps.commercial`
- `.venv/bin/ruff check apps/` y `.venv/bin/ruff format --check apps/`
- `.venv/bin/djlint apps/commercial/templates/ --check`

## Progreso

Evidencia observada en la rama `feat/invoice-form-period-redesign`. Implementado por un
worker (`gentle-ai-worker`), verificado por `gentle-ai-verify`, corregido y commiteado por el
parent en **`64ce37b`**.

- **T1** — Creados `includes/commercial/invoice/{status_cell,actions_cell}.html`
  y `includes/commercial/subscription/{status_cell,actions_cell}.html` con el
  markup exacto de los listados; ambos listados los incluyen. Verificado con
  `manage.py test apps.commercial` (incluye los que afirman aria-labels y títulos
  de botones) y `djlint ... --check` + `--reformat --check` (0 archivos pendientes).
- **T2** — `apps/commercial/views/list_status.py` con `ajax_invoice_status` y
  `ajax_subscription_status` (JSON + fragmentos vía `render_to_string(request=)`),
  URLs `commercial:ajax_invoice_status` (`/commercial/ajax/estado/facturas/`) y
  `commercial:ajax_subscription_status` (`/commercial/ajax/estado/suscripciones/`).
  `apps/commercial/tests/test_list_live_status.py`. Nota: un usuario logueado sin
  permiso recibe 302 al login y no 403 — comportamiento del decorador
  `permission_required` sin `raise_exception`, igual que
  `ajax_pending_subscriptions`.
- **T3** — En el partial de acciones, "Aprobar Pago" anidado en
  `{% if subscription.latest_invoice_pdf_ready %}`, "Regenerar factura" intacto
  bajo el mismo gate; rama no-staff ("Pagar con QR") sin tocar. Fixture ajustada
  en `test_views.py::SubscriptionListStateAndActionsTests` (helper
  `_invoice_with_pdf`). `test_subscription_list_actions.py` no requirió cambios:
  sus aserciones son ausencias y pasan.
- **T4** — `static/dist/js/list-live-status.js` (ES5, vanilla) expone
  `window.initListLiveStatus(cfg)`; ambos listados cargan el script en `extrajs`
  e inicializan con la URL del endpoint; filas marcadas con `data-live-status`,
  `data-live-actions` y `data-live-pending` condicional.
- **T5** — Tests de integración del fragmento: sin PDF listo el payload trae
  `pending: true` y `actions_html` sin "Aprobar Pago"; con PDF listo lo trae y
  `pending: false`; el endpoint de suscripciones no filtra filas ajenas para el
  grupo `Clientes`.

### Verificación y correcciones posteriores

`gentle-ai-verify` confirmó los 7 puntos de la revisión (gate exacto en el partial,
sin fuga de datos entre clientes, permisos alineados con `ajax_pending_subscriptions`,
contrato JS↔endpoint correcto, partials como única fuente de verdad) y sugirió dos
ajustes, ambos aplicados:

1. **Transitorio mal definido.** Una suscripción pendiente **sin factura** se marcaba
   `pending: true`; el PDF nunca iba a llegar y el polling quedaba vivo para siempre.
   Ahora `fila_pendiente` exige `latest_invoice_uuid is not None and not
   latest_invoice_pdf_ready`. El marcador `data-live-pending` del listado se alineó con
   la misma regla (test `SubscriptionListMarkersTests` ata ambos lados).
2. **Parentizado del `except` revertido.** El verificador lo marcó como riesgo de
   portabilidad, pero `ruff format` (target `py314`) normaliza a la forma sin paréntesis
   (PEP 758, igual que `views/invoices.py:610`); con paréntesis el `ruff format --check`
   fallaba. Se volvió a la forma canónica del repo.

Dos tests propios estaban mal, no el código: uno afirmaba `latest_invoice_uuid` sobre una
instancia cruda (es **anotación del queryset**, no campo del modelo) y otro usaba
`assertNotIn('Aprobar Pago', html)`, que matcheaba un comentario JS del propio template;
ambos se corrigieron a `title="Aprobar Pago"`, el marcador real del botón. Además
`detect-secrets` marcó la contraseña literal del helper de usuarios como falso positivo: se
resolvió con `# pragma: allowlist secret`, la convención ya usada en
`test_invoice_cost_allocation.py`.

### Resultado

- `manage.py check` → 0 issues.
- `manage.py test apps.commercial` → **488 tests, OK** (141,8 s).
- `ruff check` / `ruff format --check` sobre los archivos tocados → limpios.
- `djlint --check` sobre los templates tocados → 0 archivos pendientes.
- Commiteado en `64ce37b` (14 archivos). El hunk ajeno de `test_views.py`
  (`AjaxPendingSubscriptionsTests`, `payment_status='pending'` → `'requested'`) quedó fuera
  del commit: pertenece a otro change en curso en el mismo worktree.

Criterios de aceptación: cubiertos (sin PDF → sin "Aprobar Pago"; cliente no ve
suscripciones ajenas; nada de redibujado DataTables; `apps.commercial` verde,
ruff y djlint limpios).
