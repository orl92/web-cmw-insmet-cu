# Ningún cliente se imprime como `None`

## Objetivo

Que ninguna superficie de la aplicación muestre el literal `None` en lugar del
nombre de una persona natural: `__str__` de modelos, logs de operador, mensajes al
usuario y plantillas.

## Problema

`Customer.company_name` sólo existe para personas jurídicas (`blank=True, null=True`,
`apps/commercial/models.py:128`). En una persona natural es NULL, y el defecto se
escapa por doce puertas:

| Superficie | Ubicación |
|---|---|
| `__str__` de modelos | `models.py:373` (ServiceSubscription), `:615` (Invoice), `:777` (Contract), `:842` (Certificate) |
| Logs de operador | `views/invoices.py:560,574,715,729`; `views/subscriptions.py:162,196,355,371`; `views/contracts.py:53`; `views/certificates.py:56`; `views/customers.py:141,155` |
| Mensaje al usuario | `views/subscriptions.py:382` |
| Dashboard | `apps/dashboard/views/dashboard/dashboard.py:37` → muestra `N/A` en vez del nombre |
| Plantillas | `customer/list.html:39` (`reeup`), `:41` (`nit`) — sin `default` |

La propiedad `Customer.display_name` (`models.py:184-204`) ya resuelve el nombre a
mostrar y degrada a `—` cuando no hay ninguno. El defecto es que no todos los
caminos la usan.

`CompanySettings` **no** entra en esta lista: esa tabla usa `nombre`
(`apps/core/models.py:235`), que no es nullable y corresponde a la empresa que
emite la factura, no al cliente.

## Por qué importa

`None` en pantalla es ruido que el operador no puede interpretar, y en los logs es
pista falsa: quien audite una suscripción eliminada ve «Cliente desactivado: None» y
no sabe a quién se le quitó el servicio.

## Alcance

- **T1** Los cuatro `__str__` usan `customer.display_name`.
- **T2** Los doce logs de operador y el mensaje al usuario usan `display_name`.
- **T3** El dashboard devuelve el nombre de la persona natural, no `N/A`.
- **T4** `customer/list.html` muestra `—` cuando no hay REEUP ni NIT.
- **T5** Tests que afirmen que ninguna de esas superficies contiene `None`.
- **T6** El panel ordena por la clave que muestra, no por `company_name` (NULL en
  naturales: las agrupaba al principio en SQLite y al final en PostgreSQL, y el
  orden entre ellas quedaba al azar).

Fuera de alcance: renombrar campos, cambiar el modelo de datos, o tocar el
`display_name` ya implementado. `identity_document` ya está protegido con
`|default:'—'` y no se toca.

## Restricciones

- No hay migraciones: este repo no las versiona.
- No se inventan fallbacks nuevos: `display_name` ya degrada a `—`.
- Comentarios y copy en español es-mx neutro.

## Criterios de aceptación

- `str(suscripción)`, `str(factura)`, `str(contrato)` y `str(certificado)` de una
  persona natural contienen su nombre y no `None`.
- Ningún log de operador de suscripciones, facturas, contratos, certificados ni
  clientes contiene `None` donde va el nombre del cliente.
- El listado de clientes muestra `—` (no `None`) cuando no hay REEUP ni NIT.
- El dashboard muestra el nombre de la persona natural en la lista de suscripciones.

## Verificación

| Cambio | Comando |
|---|---|
| Modelos, vistas y dashboard | `.venv/bin/python manage.py test apps.commercial apps.dashboard` |
| Sistema | `.venv/bin/python manage.py check` |
| Estilo Python | `.venv/bin/ruff check apps/commercial apps/dashboard && .venv/bin/ruff format --check apps/commercial apps/dashboard` |
| Plantilla | `.venv/bin/djlint apps/commercial/templates/pages/commercial/customer/list.html --lint` |

## Progreso

- [x] T1–T5
- [x] T6

## Evidencia

**RED** — `apps.commercial.tests.test_models.ClienteNaturalSinNoneEnStrTests`,
`apps.commercial.tests.test_operator_logs`,
`apps.commercial.tests.test_customer_list_fiscal_data`,
`apps.dashboard.tests.test_serialize_sub`: `Ran 18 tests` / `FAILED (failures=18)`,
con mensajes como `'None' unexpectedly found in 'Suscripción eliminada físicamente:
None - Servicio Log'` y `'N/A' != 'Ana Norte'`.

**RED (T6)** — `apps.dashboard.tests.test_dashboard_ordering`:
`AssertionError: 1 not less than 0` → la persona natural (NULL en `company_name`)
se colaba delante de la empresa en SQLite.

**GREEN** — misma selección: `Ran 20 tests` / `OK`; suite completa
`apps.commercial apps.dashboard`: `Ran 611 tests in 136.491s` / `OK`;
`manage.py check` sin issues; `ruff check` y `ruff format --check` limpios;
`customer/list.html` con 0 errores de djlint.

**Aprendizaje del verificador** — los tests de facturación encolan de verdad en
el `MemoryStorage` de Huey que comparte `config/test_runner.py` durante toda la
corrida: un test que factura deja trabajo vivo y rompe el test que afirma que la
cola quedó vacía (`test_la_facturacion_no_deja_trabajo_en_la_cola_compartida`).
Los tests de esta unidad mockean `generate_invoice_pdf_and_email_task`.
