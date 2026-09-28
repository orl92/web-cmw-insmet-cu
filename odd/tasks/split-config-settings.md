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
config que no tienen nada que ver con él. Cuando Django 6 depreca una API o un default, no hay un
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

Rama `refactor/settings-profiles`, 2 work-unit commits sobre `16fe5ff`, árbol limpio.

| Commit | Unidad |
|---|---|
| `b6afa9a` | `refactor(settings)`: paquete de perfiles + tests + corrección de la guarda de media/ |
| `385280b` | `chore(odd)`: este documento |

### Verificación ejecutada

| Chequeo | Resultado |
|---|---|
| Equivalencia del objeto settings vs. el monolito de `HEAD`, 3 perfiles | **Byte a byte idéntica** (170/169/169 settings). Se excluyen `SETTINGS_MODULE` (nombre del módulo del probe) y `SECRET_KEY` (aleatorio por sesión). |
| `python manage.py test` | **838/838 OK** (811 previos + 27 nuevos). |
| `manage.py check` en dev y testing | 0 issues. |
| `ruff check` | limpio. |
| `pre-commit run` (8 hooks) | verde. |
| `ruff format` (hook mutante) | reformateó 2 archivos → **equivalencia re-verificada sobre esos bytes** antes de commitear. |

### Desviación del plan, y por qué

`test_media_root_init.py` no estaba en el alcance y hubo que arreglarlo. Usaba
`inspect.getsource(config.settings)`, que tras el split devuelve solo el `__init__.py` de 70
líneas: la guarda de la spec 014 quedó **incapaz de fallar**. Ahora lee todos los módulos del
paquete, y su eficacia está probada por mutación (inyectar `MEDIA_ROOT.mkdir` en `base.py` hace
fallar el test con `module='base.py'`).

Un test verde no distingue una guarda real de una decorativa. La mutación sí.

### Deuda que este change dejó documentada, no resuelta

- `apply_external_hostname()` deriva el puerto con `external_hostname.split(':')[-1]`: una URL con
  path termina en el puerto.
- `production.py` no pinea `DEBUG = False`; hereda el valor de `base.py`. Un `DEBUG=True` suelto en
  el `.env` de producción sigue sirviendo tracebacks, igual que antes del split. **Decisión
  pendiente del mantenedor**: pinearlo agrega `DEBUG` a la línea de diff del estado híbrido.
- `DJANGO_SETTINGS_MODULE=config.settings.base` pasa `check` pero no tiene `DATABASES`. Válido solo
  para orden de importación.
- `DEBUG=False` en una máquina cuyo `.env` tenga `DB_ENGINE` sin los otros cuatro vars falla al
  importar. Preexistente, verificado idéntico contra `HEAD`.

## Revisión nativa

**No revisada.** RDD sigue apagado a nivel de clon (`clone_local: off`, `global: on`), así que la
entrega va por política ordinaria del repo y se reporta `disabled/unmanaged`. No hay PASS ni
aprobación inventada. La apertura del PR es decisión del mantenedor.

## Ruta de ejecución

Delegado: un solo writer para los 5 archivos del paquete más los tests. Los archivos son no triviales
y comparten el mismo razonamiento de orden de evaluación — separarlos entre varios workers
introduciría exactamente el tipo de inconsistencia que la restricción dura busca evitar.
