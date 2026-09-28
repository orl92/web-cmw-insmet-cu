# Partición de `config/settings.py` por perfil

## Objetivo

Convertir el monolito de 491 líneas en un paquete `config/settings/` con un archivo por perfil,
para que cada ajuste de entorno sea localizable y la migración a Django 6 no se pierda dentro de
un archivo(reordered.

## Problema

`config/settings.py` mezcla dos cosas que hoy no están separadas: configuración compartida
(plantillas, apps, DRF, i18n) y decisiones de entorno dispersas en nueve ramas
`if not DEBUG:` / `if IS_PRODUCTION:` a lo largo del archivo. Cada ajuste de entorno — cookies
seguras, `STORAGES`, debug toolbar, WhiteNoise, base de datos — vive buried entre 60 líneas de
config que no tienen nada que ver con él. Cuando Django 6的一个 una API o un default, no hay un
lugar obvious donde aplicar el cambio ni una forma de verificar que el perfil equivocado no cambió.

## Restricción dura (no negociable)

**El mecanismo de selección de perfil NO puede cambiar.**

Hoy el perfil lo eligen variables de entorno leídas *dentro* del módulo:
`IS_PRODUCTION = 'PRODUCTION' in os.environ` y `DEBUG = os.getenv('DEBUG','False') == 'True'`.

`gunicorn.sh` **no** exporta `PRODUCTION`. El `supervisord.conf` que lo envuelve vive en el
servidor de deploy, fuera del repo, así que desde este checkout es imposible verificar si define
esa variable. Si el split pasa a seleccionar el perfil de producción por otro mecanismo (una
variable nueva, un módulo explícito en `DJANGO_SETTINGS_MODULE`), y el supervisor no define esa
variable, **producción arranca con el perfil de tests** — sin manifest storage, sin validación
estricta de DB, sin WhiteNoise. Eso es un outage silencioso.

Consecuencia de diseño: el dispatcher vive en `config/settings/__init__.py` y lee **las mismas**
variables de entorno, con **la misma** precedencia. La tabla de verdad se preserva por
construcción, no por disciplina.

## Tabla de verdad a preservar

| Estado | `PRODUCTION` | `DEBUG` | secure cookies | STORAGES static | toolbar | DB | WhiteNoise MW |
|---|---|---|---|---|---|---|---|
| `dev` | no | `True` | no | `StaticFilesStorage` | sí | sqlite | removido |
| `testing` | no | no/falso | **sí** | `StaticFilesStorage` | no | sqlite¹ | removido |
| `production` | **sí** | irrelevant | **sí** | `CompressedManifest…` | no | exige `DB_ENGINE` | insertado idx 1 |

¹ `testing` usa la lógica real de `get_database_config()`: sqlite salvo que `DB_ENGINE` esté
definida. Es exactamente lo que hace hoy el estado `DEBUG=False, IS_PRODUCTION=False`.

## Alcance

- Nuevo paquete `config/settings/`: `__init__.py` (dispatcher), `base.py` (compartido +
  `.env`), `dev.py`, `testing.py`, `production.py`.
- `base.py` conserva `get_database_config()`, `decrypt_secret_key()`, `build_caches()` y toda la
  config accionada por `.env` (secrets, hosts, CORS, email, LDAP, FTP) sin rama de `DEBUG`.
- `dev.py` re-declara `DEBUG = True` y recalcula `DATABASES` **después** del `import *`, para que
  sqlite gane sobre un `DB_ENGINE` presente en `.env` (hoy `DEBUG=True` fuerza sqlite).
- `testing.py` añade el bloque de secure cookies, `StaticFilesStorage`, y los fast-paths de test.
- `production.py` añade secure cookies, `CompressedManifestStaticFilesStorage`, la rama estricta de
  DB, y WhiteNoise en `MIDDLEWARE[1]`.
- `config/settings.py` (monolito) se borra. **Ningún** consumidor operativo cambia de nombre:
  `manage.py`, `config/wsgi.py`, `config/asgi.py` y `run_huey.sh` siguen diciendo `config.settings`.
- Tests nuevos en `apps/core/tests/test_settings_profiles.py` que fijan la tabla de verdad.

## Fuera de alcance

- Migración a Django 6: change diferido. Django queda en `5.2.17`.
- Fail-fast de `SECRET_KEY` en el perfil `testing`: hoy `CI` genera una key aleatoria por sesión y
  la spec `013-check-deploy-ci` **afirma** ese comportamiento ("does not false-positive in CI").
  Endurecerlo rompe esa spec.
- Partición por *dominio* (`settings/api.py`, `settings/meteo.py`): otra forma de partir el mismo
  archivo, ortogonal a la de perfil. No se hace ahora; con dos ejes el resultado es 15 archivos.

## Decisiones

| Decisión | Razón |
|---|---|
| Dispatcher en `__init__.py`, no `DJANGO_SETTINGS_MODULE` explícito | Es el único diseño que preserva la tabla de verdad sin depender de una variable que el supervisor puede no exportar (restricción dura). |
| Cuatro perfiles, no dos | El estado `DEBUG=False, IS_PRODUCTION=False` existe y es real: es CI. Colapsarlo dentro de `dev` o `production` cambia comportamiento en uno de los dos. |
| `base.py` sin ninguna rama `DEBUG`/`IS_PRODUCTION` | Si `base` lee esas variables, el `import *` del hijo corre la lógica de DB con el `DEBUG` equivocado antes de que el hijo pueda sobreescribirlo. Separar por *orden de evaluación*, no por gusto. |
| `dev.py` recalcula `DATABASES` post-import | Orden de artefacto directo de la fila anterior. Sin esto, un dev con `DB_ENGINE` en `.env` connectaría a la DB real. |
| Perfil de test se llama `testing`, no `ci` | El estado que representa no es "CI", es "sin `DEBUG` y sin `PRODUCTION`", que también ocurre en un `manage.py test` local y en un staging mal configurado. |
| Sin fast-path de `PASSWORD_HASHERS` extra más allá de test | Agregar uno que no existe hoy es un cambio de comportamiento disfrazado de refactor. |

## Verificación

- `python manage.py check`: 0 issues, en los **tres** perfiles
  (`DJANGO_SETTINGS_MODULE=config.settings{,.dev,.testing,.production}` con las variables
  correspondientes).
- **Equivalencia de settings, byte a byte**: dump de `vars(django.conf.settings)` con el módulo
  monolith viejo vs. el paquete nuevo, en los tres estados de la tabla de verdad. Diff vacío. Este
  es el criterio de aceptación real — la suite de tests pasa igual, pero el diff es lo que prueba
  que no cambió nada.
- `python manage.py test`: **797/797** (o lo que sea el conteo vigente) verde.
- `ruff check config/` limpio.
- Los perfiles importables directamente: `config.settings.production` funciona sin pasar por el
  dispatcher.

TDD: **off**. No hay `strict_tdd` registrado en el proyecto para este repo, y el modo no aplica a
una refactorización de configuración: no hay comportamiento nuevo quespec-first. El runner es
`python manage.py test` (verificado en `AGENTS.md` y `.github/workflows/ci.yml`). La prueba
equivalente es el diff de settings described arriba, que es estrictamente más fuerte que un test
nuevo porque compara el objeto completo, no los valores que alguien se acuerde de fijar.

## Riesgo

| Riesgo | Mitigación |
|---|---|
| Producción arranca con el perfil equivocado (el `supervisor` no exporta `PRODUCTION`) | El dispatcher lee las mismas variables; el perfil de producción es inalcanzable sin `PRODUCTION` en el entorno, igual que hoy. |
| `DB_ENGINE` en `.env` + `DEBUG=True` ahora connecta a la DB real | `dev.py` recalcula `DATABASES` después del `import *`. Cubierto por un test. |
| Un perfil nuevo hereda a medias porque el nombre "obvio" no coincide con la realidad | Los tests fijan la tabla de verdad completa, no casos sueltos. |
| `import *` no exporta algo con guion bajo (`_CONTENT_SECURITY_POLICY_DIRECTIVES`) | `base.py` lo expone explícitamente con un alias sin guion bajo. Verificar con el dump de settings. |

## Progreso

Sin empezar.

## Ruta de ejecución

Delegado: un solo writer para los 5 archivos del paquete más los tests. Los archivos son no triviales
y comparten el mismo razonamiento de orden de evaluación — separarlos entre varios workers
introduciría exactamente el tipo de inconsistencia que la restricción dura busca evitar.
