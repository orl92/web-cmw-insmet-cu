# URL canónica del sitio para los correos

## Objetivo

Que los enlaces que viajan en los correos apunten a la URL pública del sitio, y que
la aplicación **no pueda arrancar en producción** si esa URL no está configurada.

## Problema

### 1. `BASE_URL` no existe y cuatro call sites lo asumen

| Ubicación | Qué hace |
|---|---|
| `apps/commercial/views/invoice_utils.py:281` | `getattr(settings, 'BASE_URL', 'http://localhost:8000/')` |
| `apps/core/utils.py:138` | idem (correos de avisos y reportes) |
| `apps/commercial/views/subscriptions.py:399` | `settings.BASE_URL` **sin `getattr`** → `AttributeError` latente en el reenvío de certificado |
| `apps/commercial/management/commands/send_test_invoice.py:164` | `getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000/')` |

No hay ningún perfil de settings que defina `BASE_URL` (`config/settings/base.py`,
`dev.py`, `testing.py`, `production.py`): el grep de `SITE_URL|BASE_URL` en
`config/` no devuelve ni una coincidencia.

### 2. La URL del request tampoco sirve para un correo

Los correos de factura, aviso y reporte salen hacia clientes que **no** están en la
red interna. Construir el enlace con `request.build_absolute_uri('/')` lo ata al host
por el que el operador entró (`http://10.0.0.5:8000/`) o al esquema con el que
llegó la petición, que no es el público.

### 3. Un backend SMTP sin verificar TLS pasa el control de producción

`config/mail_backends.py` define `InsecureDevEmailBackend`, que desactiva la
verificación de host y de cadena del certificado. `config/settings/production.py:22`
rechaza los backends de `base.silent_email_backends`, pero **ese backend no está en
la lista**: un `.env` de producción apuntando a él arranca sin que nadie se entere.

## Alcance

- **T1** `SITE_URL` en `config/settings/base.py`, leída del entorno, con default de
  desarrollo y normalizada con `/` final.
- **T2** `config/settings/production.py` **fail closed**: sin `SITE_URL` en el
  entorno, `ImproperlyConfigured` — mismo criterio que el guard de `EMAIL_BACKEND`
  que ya existe en `production.py:22`.
- **T3** `scripts/generate_env.py` escribe `SITE_URL` en la sección de dominio que
  ya existe (`generate_env.py:161-168`).
- **T4** Los cuatro call sites leen `settings.SITE_URL` (sin `getattr`) y ningún
  correo deriva su URL del request.
- **T5** El enlace del reinicio de contraseña (`apps/user_auth/forms/password.py:68`)
  usa `SITE_URL`: también sale del servidor hacia el cliente.
- **T6** `production.py` rechaza `config.mail_backends.InsecureDevEmailBackend`.
- **T7** Tests: default del ajuste, fail-closed de producción, enlace del correo de
  factura, enlace del correo de aviso/reporte, enlace del reinicio de contraseña y
  rechazo del backend inseguro.

Fuera de alcance: `SITE_ID` de `django.contrib.sites`, o mover la URL a la base de
datos (`SiteConfiguration`) — eso exige migración y las migraciones no se versionan.

## Restricciones

- El nombre es `SITE_URL` y no `BASE_URL`: el código existente lo llama así, pero
  `BASE_URL` en el mundo Django suele significar la raíz del sitio para resolver
  estáticos, y acá significa «la URL pública que el cliente puede abrir».
- El valor de producción viene del entorno (`.env`), no de un default: un default
  silencioso es exactamente el defecto que se cierra.
- La normalización conserva la barra final para que concatenar rutas no produzca
  doble barra.

## Convención de concatenación

`SITE_URL` se normaliza **con barra final** y las rutas se concatenan **sin barra
inicial**:

```python
url = settings.SITE_URL + reverse('commercial:suscripcion_list').lstrip('/')
```

Con `SITE_URL = 'https://cmw.insmet.cu/'` y `reverse(...) = '/suscripciones/'` sale
`'https://cmw.insmet.cu/suscripciones/'`: una sola barra entre host y ruta, sea cual
sea la forma en que el operador haya escrito la variable (`https://host`,
`https://host/`, `https://host///`).

## Progreso

- [x] T1 `SITE_URL` en `config/settings/base.py` (`normalize_site_url` + default de
  desarrollo `http://localhost:8000/`).
- [x] T2 `production.py` falla cerrado sin `SITE_URL` (`ImproperlyConfigured`).
- [x] T3 `scripts/generate_env.py` escribe `SITE_URL` (producción: `https://{host}/`;
  desarrollo: `http://localhost:8000/`).
- [x] T4 Los cuatro call sites leen `settings.SITE_URL`.
- [x] T5 El reinicio de contraseña arma `index_url` y `reset_url` con `SITE_URL`.
- [x] T6 `production.py` rechaza `InsecureDevEmailBackend` (lista
  `insecure_email_backends` en `base.py`).
- [x] T7 Tests nuevos: `apps/core/tests/test_site_url.py`,
  `apps/commercial/tests/test_site_url_links.py`,
  `apps/user_auth/tests/test_password_reset_site_url.py` y las extendidas en
  `apps/core/tests/test_settings_profiles.py`.

### Pendientes cerrados en esta unidad

1. ~~Dos asserts de `apps/meteo`~~ — **cerrado**: las dos pruebas envuelven la
   aserción en `override_settings(SITE_URL='http://testserver/')`, así que
   verifican el contrato nuevo (el enlace sigue a `SITE_URL`) en vez del host del
   request.
2. ~~Fuga en el camino encolado de la factura~~ — **cerrado**:
   `apps/commercial/views/invoices.py` pasa `settings.SITE_URL` a la tarea en los
   tres call sites. Nuevo test `EncoladoUsaSiteUrlTests` en
   `apps/commercial/tests/test_site_url_links.py` lo cubre.
3. **Faltan las plantillas del reinicio de contraseña** (defecto previo, no
   cerrado): no existe `templates/registration/password_reset_subject.txt` ni
   `templates/registration/password_reset_email.html`, que son los nombres por
   defecto de Django 5.2. El envío real del correo lanzaría
   `TemplateDoesNotExist`. La plantilla del proyecto en español ya existe
   (`apps/user_auth/templates/pages/user_auth/emails/password_reset_email.html`)
   …


## Criterios de aceptación

- En producción, sin `SITE_URL`, la aplicación no arranca y dice qué variable falta.
- El enlace del correo de factura, del correo de aviso, del reporte del tiempo y del
  reinicio de contraseña apunta a `SITE_URL`, no al host del request.
- Producción rechaza el backend SMTP sin verificación de certificado.

## Verificación

| Cambio | Comando |
|---|---|
| Todo | `.venv/bin/python manage.py test apps.commercial apps.core apps.meteo apps.user_auth` |
| Sistema | `.venv/bin/python manage.py check` |
| Perfiles de settings | `.venv/bin/python manage.py test apps.core.tests.test_settings_profiles` |
| Estilo Python | `.venv/bin/ruff check apps config && .venv/bin/ruff format --check apps config` |

### Estado de la verificación

| Comando | Resultado |
|---|---|
| `.venv/bin/python manage.py test apps.commercial apps.core apps.meteo apps.user_auth` | 1025 tests, `OK` |
| `.venv/bin/python manage.py test apps.core.tests.test_settings_profiles` | 51 tests, `OK` |
| `.venv/bin/python manage.py check` | `System check identified no issues` |
| `.venv/bin/ruff check config apps scripts` | `All checks passed!` |
| `.venv/bin/ruff format --check config apps scripts` | `283 files already formatted` |

### Nota del cierre

El test del reintento de PDF necesitó también `view_invoice`: la vista redirige al
listado y `follow=True` lo atraviesa, así que sin ese permiso el 403 no era del
reintento sino del destino. Ojo con eso al escribir tests de vistas que redirigen.
