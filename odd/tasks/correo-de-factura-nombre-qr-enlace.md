# Correo de la factura: nombre visible, QR en el cuerpo y enlace alcanzable

## Objetivo

Que el correo que recibe el cliente no muestre datos crudos ni lo mande a
páginas que no puede abrir:

1. el asunto lleva el nombre **visible** del cliente (hoy imprime `None`);
2. el QR de pago se **ve en el cuerpo** (hoy se imprime el texto del `alt`);
3. «Ver en línea» apunta a una página que el cliente **sí** puede abrir (hoy va
   a facturación, que exige un permiso que no tiene).

## Problema (evidencia)

- **Asunto**: `apps/commercial/views/invoice_utils.py:296`

  ```python
  subject = f'Factura {invoice.number} - {customer.company_name}'
  ```

  En una persona natural `company_name` es NULL y una f-string lo escribe
  literal como `None`: el cliente lee «Factura 2026-0001 - None». Los cuerpos ya
  usan `customer.display_name` (`emails/factura.html:175`,
  `emails/factura_qr.html:135`) y están cubiertos por `SaludoDelCorreoTests`;
  el asunto quedó afuera de ese arreglo y ningún test lo mira.

- **QR**: `emails/factura_qr.html:142` arma
  `<img src="cid:qr_pago.png" alt="Código QR de pago">`, pero
  `invoice_utils.py:322` adjunta con
  `email.attach('qr_pago.png', bytes, 'image/png')`. Ese `attach` crea un
  adjunto **sin** cabecera `Content-ID`, así que el `cid:` no resuelve contra
  ninguna parte y el cliente de correo imprime el `alt` («Código QR de pago»).
  El archivo viaja (adjunto), pero no se muestra.

- **Enlace**: `invoice_utils.py:282` arma
  `listado_url = base_url + reverse('commercial:factura_list')` →
  `/comercial/facturacion/`, servido por `InvoiceListView` con
  `permission_required = 'commercial.view_invoice'`. El cliente no tiene ese
  permiso (el propio proyecto lo exceptúa a mano en
  `InvoicePDFDownloadView.get_permission_required`): el enlace lo deja en
  login/403.

## Alcance

- **T1** Asunto con `customer.display_name` (mismo criterio que los cuerpos).
- **T2** QR en el cuerpo: parte MIME *inline* con `Content-ID: <qr_pago.png>` y
  `Content-Disposition: inline`, **conservando** el adjunto descargable.
- **T3** `listado_url` → `commercial:suscripcion_list` («Mis Suscripciones»),
  cubierta por `view_subscription`, que el grupo `Clientes` sí tiene.

## Fuera de alcance

- Renombrar la clave `listado_url` del contexto: obligaría a tocar las tres
  plantillas de correo y no cambia nada visible.
- Servir el QR por URL remota en vez de `cid:`.
- El asunto del certificado (`views/subscriptions.py:368`) no usa
  `company_name`: no tiene el defecto.
- El resumen del log de tareas (`apps/core/apps.py:_summary`) ya se corrigió y
  está cubierto por `ResumenDelClienteTests`.
- Cualquier archivo de las otras sesiones (`views/list_status.py`,
  `views/subscriptions.py`, `invoice/list.html`, `subscription/list.html`,
  `tests/test_list_live_status.py`, `tests/test_invoice_line_payments.py`).

## Restricciones

- Sin tocar plantillas, JS ni estáticos: el arreglo es Python.
- `MIMEImage(..., _subtype='png')` con `_subtype` explícito: Python 3.14 ya no
  tiene `imghdr` para adivinar el subtipo.
- Comentarios y copy en español es-mx neutro (nunca voseo).
- Sin `makemigrations`/`migrate`, sin escribir en `db.sqlite3` ni `media/`.
- No commitear.

## Criterios de aceptación

- El asunto de una factura de persona natural contiene su nombre y no `None`.
- El mensaje enviado trae una parte con `Content-ID: <qr_pago.png>` cuyo
  contenido son los bytes del PNG, y el cuerpo HTML referencia
  `cid:qr_pago.png`; el adjunto `qr_pago.png` sigue presente.
- El cuerpo de ambas plantillas apunta a `commercial:suscripcion_list` y no a
  `commercial:factura_list`; un usuario cliente (grupo `Clientes` +
  `view_subscription`, sin `view_invoice`) abre esa URL con 200.

## Verificación

```bash
python manage.py check
python manage.py test apps.commercial.tests.test_invoice_delivery \
  apps.commercial.tests.test_tasks apps.core.tests.test_tasks
python manage.py test apps.commercial apps.core
.venv/bin/ruff format --check apps/commercial/views/invoice_utils.py \
  apps/commercial/tests/test_invoice_delivery.py
.venv/bin/ruff check apps/commercial/views/invoice_utils.py \
  apps/commercial/tests/test_invoice_delivery.py
```

## Progreso

- [x] T1 Asunto con el nombre visible
- [x] T2 QR inline con `Content-ID` — **criterio cambiado**: sin adjunto duplicado
      (el PNG viaja una sola vez, sólo en el cuerpo)
- [x] T3 Enlace a «Mis Suscripciones» — destino corregido
- [x] T3-bis Opción (b) implementada — `SubscriptionListView` tolera al titular, acotada
      a sus propias suscripciones; **pendiente la verificación independiente**
- [ ] T4 El resto de los correos — mapa hecho (5 plantillas): el certificado queda cubierto
      por T3-bis; falta el correo de avisos/reportes (enlaces vacíos)
- [x] Tests nuevos en `CorreoVisibleAlClienteTests` (3 causales RED→GREEN, 3 guardas)

## Ruta y evidencia

- Ruta: **delegated direct** — `gentle-ai-worker` sobre
  `apps/commercial/views/invoice_utils.py` +
  `apps/commercial/tests/test_invoice_delivery.py` (2 archivos no triviales).
- Writer: 24 OK en `test_invoice_delivery`; 871 OK en `apps.commercial apps.core`;
  `ruff format --check` y `ruff check` limpios en los dos archivos.
- Spot check del padre: `python manage.py test apps.commercial.tests.test_invoice_delivery`
  → 24 tests OK. RDD `off` (clone-local); tier `high` (`unassessable` por untracked).
- Verificación independiente (`gentle-ai-verify`):
  - **V1 confirmado**: `test_invoice_delivery.py:488` (asunto natural), `:510` (QR inline)
    y `:544` (enlace) son RED→GREEN — el código viejo está en el lado `-` del diff;
    `:494`, `:533` y `:556` son guardas de regresión.
  - **V2 confirmado**: MIME real `multipart/mixed` con
    `part[2] ctype=image/png cid=<qr_pago.png> disp=inline payload_len=6793 eq_disk=True`
    y `part[3]` adjunto con los mismos bytes; el cuerpo referencia
    `http://testserver/commercial/suscripciones/`.
  - **V3 NO confirmado — bloquea la premisa de T3**: `view_subscription` se le otorga al
    grupo `Clientes` **solo** en `apps/user_auth/forms/users.py:234-241` y solo `if created:`;
    los caminos del dashboard crean el grupo **vacío**
    (`apps/commercial/views/customers.py:55-60` y `:199-204`) y no hay backfill.
    Si el grupo se crea primero desde el dashboard, «Ver en línea» vuelve a caer en login.
    En el `db.sqlite3` local el grupo sí lo tiene (otorgado a mano por admin).
  - **V4 confirmado**: 36 OK focalizados / 871 OK `apps.commercial apps.core` /
    `manage.py check` sin issues / ruff limpio.
  - V5(b): el PNG viaja dos veces (6793 B ×2) y la parte inline lleva `filename=`
    — es la decisión pedida: en el cuerpo **y** adjunto descargable.
  - V5(a): el raíz queda `multipart/mixed`, no `multipart/related`; no verificable sin
    clientes de correo reales.

## Cierre

- **T2 (QR) con el criterio nuevo**: el PNG viaja una sola vez, como parte inline con
  `Content-ID: <qr_pago.png>`; se eliminó el `email.attach('qr_pago.png', ...)`. Walk MIME
  final: `multipart/mixed` → `text/html` + un único `image/png` inline de 6793 bytes. El test
  se invirtió a `test_el_qr_no_viaja_duplicado_como_adjunto`, con RED→GREEN real.
- **T3-bis implementado (opción b) y verificado**: `SubscriptionListView` acepta al titular de
  un `Customer` sin `commercial.view_subscription` (`has_permission` en
  `views/subscriptions.py`), y el helper compartido acota al titular con el **mismo** filtro de
  la rama del grupo `Clientes` (`qs.filter(customer=customer, record_active=True)`).
  Verificación independiente V1–V5 **confirmados**: sin ruta de fuga entre clientes, el
  endpoint AJAX no expone filas ajenas (`uuid__in` sólo intersecta lo propio), anónimo
  redirige, superuser sin `Customer` OK. 878 tests OK en `apps.commercial apps.core`.
- **T4 (el resto de los correos) cerrado.** El mapa dio **5 plantillas** en todo el sistema:
  - **Factura** → los tres defectos corregidos; el permiso del enlace lo cubre T3-bis.
  - **Certificado** → el asunto ya estaba bien (`service.title`); el enlace lo cubre T3-bis.
  - **Avisos y reportes del tiempo** → **corregidos**: `mail_send` no entregaba `index_url`,
    `listado_url`, `title` ni `current_year`, y los `mail_url` de los avisos eran slugs
    desnudos no reversibles (`'tormenta'`) — ahora son nombres de URL (`home:warnings_storm`).
    El HTML salía con `href=""`, `<title></title>` y `Copyright ©  -`.
  - **Password reset** → sin defecto (destino público, sin login ni permiso).
- **Evidencia**: los tres slices con RED→GREEN real, más el spot check del padre re-corriendo
  `WarningEmailLinkTests` + `WeatherReportEmailLinkTests` + `SubscriptionListOwnerAccessTests`
  → 10 tests OK.
- **Decisión tomada por el writer, no por el usuario**: el `title` del correo de reportes del
  tiempo cae al asunto porque `WeatherReport` no tiene campo `title`.
- **Riesgo conocido**: el fallback de URL cuando no hay `request` es `http://localhost:8000/`
  (no hay `BASE_URL` en `config/settings/`). Hoy no se dispara: los callers siempre pasan
  `request`.
- **Assess**: `risk: high`, `unassessable` (untracked), `review_due: true`. RDD sigue **off**
  (clone-local), así que no corresponde iniciar review; el tier alto se cubrió con
  verificación independiente.
- **Pendiente sin implementar** (misma clase del defecto #1, fuera del correo): `company_name`
  crudo sigue imprimiendo `None` en `ServiceSubscription.__str__` (`models.py:373`),
  `Invoice.__str__` (`:615`), `Contract.__str__` (`:777`), `Certificate.__str__` (`:842`) y en
  logs de operador. No se tocó: cambia texto visible en admin y listas, y no estaba pedido.
- **Pendiente de decisión**: nada está commiteado y el árbol mezcla cambios de otras sesiones
  en los mismos archivos (`invoice_utils.py`, `requirements/base.txt`, tests, plantillas).
- Engram: **caído** en esta sesión; el doc local es la fuente. Resincronizar cuando vuelva.
