# Endurecimiento de perfiles de settings y gate de deploy

## Objetivo

Que el perfil de producción sea imposible de arrancar mal, y que CI lo demuestre antes del día
del deploy en vez de a las 3 de la mañana.

## Lo que YA funciona (verificado, no hay que hacerlo)

- El `.env` del repo tiene `SECRET_KEY` y `ENCRYPTION_KEY` cifradas; `SECRET_KEY` mide 50
  caracteres. **Dev NO usa la clave efímera.** El fallback solo aplica en un clon sin `.env`.
- `EMAIL_BACKEND` en dev es `django.core.mail.backends.console.EmailBackend`. El objetivo
  "dev consola, prod SMTP" **ya se cumple**, accionado por `.env` y no por el perfil.
- `python manage.py check --deploy` con el perfil de producción: **1 solo warning**, y es
  artefacto de la clave de prueba de 5 caracteres usada en la medición. `W008` ya está silenciado
  a propósito (`security.W008`, Nginx termina TLS). El gate pasa limpio y es barato de agregar.

Esto corrige el marco del pedido original: el problema no es que falte configuración, es que
**nada impide que producción arranque con la configuración equivocada**.

## Bloqueo conocido: "fail-closed en todos los entornos" NO es implementable

`generate_env` es un management command. `manage.py` → `execute_from_command_line()` →
`django.setup()` → **importa los settings antes de despachar el comando**. Si `dev.py` fallara
cerrado cuando falta la clave, `python manage.py generate_env` —el comando que existe para
generar la clave— dejaría de arrancar. Paradoja de bootstrap.

**Decisión: el fallback a clave efímera se queda en `base.py` (es el bypass de bootstrap), pero
deja de ser silencioso.** Pasa a emitir un warning visible. Ese es el máximo fail-closed
alcanzable sin reescribir `generate_env` como script plano fuera de Django, que es un cambio
mayor y fuera de alcance.

Efecto real para el usuario: hoy el fallback es invisible. Después es imposible no verlo.

## Alcance

1. `production.py`: `DEBUG = False` pineado (no heredado de `base.py`).
2. `production.py`: **assert anti-consola**. Si el `EMAIL_BACKEND` resuelto es el de consola,
   `ImproperlyConfigured`. El pie real no es "dev usa consola", es "producción usa consola en
   silencio": los usuarios no reciben correo y no sale ningún error.
3. `dev.py`: `EMAIL_BACKEND` por defecto consola **solo si `.env` no lo define**. No pisa un valor
   explícito, para conservar la capacidad de probar envío real desde dev (SMTP de pruebas,
   MailHog, servidor real con destinatario de test).
4. `base.py`: el fallback a `get_random_secret_key()` emite un warning explícito.
5. `.github/workflows/ci.yml`: job nuevo que genera el par Fernet y corre
   `manage.py check --deploy` bajo `PRODUCTION=1`.
6. `openspec/specs/013-check-deploy-ci/spec.md`: actualizar la premisa que queda falsa.

## Fuera de alcance

- Partir `base.py` por dominio (eje 2). Es legibilidad, no corrección. Se decide después de
  Django 6.
- Reescribir `generate_env` fuera de Django para permitir fail-closed real.
- Endurecer el `.env` en staging: no hay staging.

## Decisiones

| Decisión | Razón |
|---|---|
| Assert anti-consola en prod, no hardcode de consola en dev | Hardcodear consola en `dev.py` quita la capacidad de probar envío real desde dev. El assert previene el pie real sin quitar nada. |
| El fallback de `SECRET_KEY` se queda, pasa a warning | `generate_env` no puede arrancar con fail-closed en dev. El silencio es el defecto, no el fallback. |
| `DEBUG = False` explícito en `production.py` | Un `DEBUG=True` colado en el `.env` de producción sirve tracebacks con paths del servidor. Costo: una línea más de diff en el estado híbrido `PRODUCTION=1 DEBUG=True`, que nadie ejecuta. |
| El gate de CI genera su propio par Fernet, no reusa `.env` | El `.env` no está en el repo. CI no puede tener claves reales. Generarlas ahí prueba el camino completo, incluido el cifrado. |
| `EMAIL_BACKEND` por defecto en `dev.py` respeta `.env` | Un dev sin config de email no debe romper al enviar. `base.py:468` hoy defaultea a SMTP, que con `EMAIL_HOST=None` revienta al mandar. |

## Verificación

- `check --deploy` con perfil de producción y clave real: **0 warnings**.
- El assert anti-consola **se prueba por los dos lados**: con backend consola levanta, con SMTP
  no. Un assert que nunca se ejecutó en su rama negativa no es un assert.
- El warning de clave efímera aparece sin `.env` y desaparece con `.env`.
- `python manage.py test`: verde, sin regresión de conteo.
- `manage.py check` limpio en dev, testing y production.
- `ruff check` + hooks verdes.
- El YAML del workflow parsea y el paso nuevo es coherente con el job existente.

TDD: **off**. No hay `strict_tdd` registrado para este repo. Runner: `python manage.py test`.
Justificación: son guards de configuración, no comportamiento de aplicación. La prueba es que
**la rama negativa del assert se exercise**, que es lo que un test de valor aporta acá.

## Riesgo

| Riesgo | Mitigación |
|---|---|
| El assert de consola rompe un deploy si alguien dejó consola en el `.env` de producción | Exactamente el comportamiento buscado: es un `.env` regenerable con `generate_env --production`, y el mensaje dice cómo arreglarlo. |
| Tocar la spec 013 la deja inconsistente con `openspec/changes/archive/` | Se edita `openspec/specs/013-...` (la spec viva), no el archivo archivado. |
| El job nuevo de CI duplica instalación de dependencias | Reutiliza el patrón del job `test` existente; si queda demasiado acoplado, se extrae a un job propio sin matrices. |

## Progreso

Implementado y verificado. Los 6 puntos de alcance están completos.

### Qué se implementó

| # | Alcance | Dónde | Estado |
|---|---|---|---|
| 1 | `DEBUG = False` pineado en producción | `config/settings/production.py` | Hecho |
| 2 | Assert anti-consola de `EMAIL_BACKEND` | `config/settings/production.py` | Hecho |
| 3 | `EMAIL_BACKEND` consola solo si `.env` no lo define | `config/settings/dev.py` | Hecho |
| 4 | `EphemeralSecretKeyWarning` visible + constante compartida | `config/settings/base.py` | Hecho |
| 5 | Job `deploy-check` en CI (sin `needs: detect`) | `.github/workflows/ci.yml` | Hecho |
| 6 | Premisas falsas corregidas | `openspec/specs/013-check-deploy-ci/spec.md` | Hecho |

Tests: +8 en `apps/core/tests/test_settings_profiles.py` (35 en total). El assert anti-consola
está probado por sus DOS ramas: con consola levanta `ImproperlyConfigured`, con SMTP y con el
backend custom no.

### Corrección durante la verificación

`load_profile()` del test suite recargaba `base` sin par de claves, así que cada reload
recorría el fallback y escupía 6 líneas de `EphemeralSecretKeyWarning` a la salida del runner
(4 de ellas en este módulo, y el ruido crecía con la suite). El fallback es visible a propósito
en runtime; en la salida de tests es ruido que tapa los avisos que importan. Se silencia con un
filtro por MENSAJE (`^SECRET_KEY ausente`) dentro de `load_profile`, no por categoría: `reload`
crea un `EphemeralSecretKeyWarning` nuevo en cada pasada y un filtro por clase quedaría viejo al
segundo reload. Los tests que necesitan observar el aviso usan su propio helper y no pasan por
`load_profile`.

### Evidencia de verificación (observada, no declarada)

| Check | Resultado |
|---|---|
| `python manage.py test` | 846/846 OK (202 s) — mismo conteo que la base, sin regresión |
| `python manage.py test apps.core.tests.test_settings_profiles` | 35/35 OK |
| `check --deploy --fail-level WARNING` perfil producción, `.env` real, `EMAIL_BACKEND`=consola | `ImproperlyConfigured` con mensaje accionable (rama negativa) |
| `check --deploy --fail-level WARNING` perfil producción, `.env` real, `EMAIL_BACKEND`=SMTP | `System check identified no issues (1 silenced)` → 0 warnings |
| `python manage.py check` (dev) | `no issues (0 silenced)` |
| `python manage.py check` (producción, SMTP + `DB_*`) | `no issues (0 silenced)` |
| `ruff check .` | All checks passed |
| `ruff format --check` | 6 files already formatted |
| `yaml.safe_load(.github/workflows/ci.yml)` | jobs: detect, test, **deploy-check**, lint, security, templates, precommit |

`W008` sigue siendo el único silenciado, y es intencional (Nginx termina TLS).

### Hallazgo NO introducido por este trabajo (corregido acá)

`DEBUG=False python manage.py check` con el `.env` local **fallaba**, y no por el perfil de
producción:

```
config/settings/testing.py:49 → base.get_database_config(is_production=False, prefer_sqlite=False)
  → base.py:308  raise ImproperlyConfigured('Para producción defina DB_NAME, DB_USER, DB_HOST y DB_PASS...')
```

`get_database_config` exigía las 4 credenciales **antes** de mirar el engine: con
`DB_ENGINE=sqlite3` —que no usa usuario, ni password, ni host— el perfil `testing` no podía
arrancar sin inventar credenciales que no existen. El mensaje además decía "Para producción" en un
perfil que NO es producción, así que mandaba a buscar el archivo equivocado.

- **Origen**: commit `b6afa9a` (split de settings), NO este trabajo. Se encontró al cumplir la
  línea de verificación "`manage.py check` limpio en dev, testing y production", que era la única
  que no daba verde.
- **Alcance real**: CI no lo sufría (sin `.env` → `DB_ENGINE` no está en `os.environ` → cae a
  sqlite) y `production.py` tampoco (credenciales de verdad). Lo sufría quien corre en local con
  `DEBUG=False` o un staging mal configurado. No era un outage de producción.
- **Corrección**: `sqlite3` (y `sqlite`/vacío) se decide ANTES del chequeo de credenciales, y el
  mensaje del chequeo nombra el motor que las pide en vez de decir "Para producción". 4 tests en
  `apps/core/tests/test_production_settings.py`: sqlite3 sin credenciales en `testing` y en
  `production`, motor de red sigue exigiendo las cuatro, y `DB_ENGINE` vacío en producción sigue
  siendo fail-closed (el corte no abre un rodeo).
- **Efecto colateral que vale la pena**: el job `deploy-check` ya no necesita `DB_USER`/`DB_PASS`/
  `DB_HOST` de mentira. Eso lo dejó más honesto (el gate no carga ni un secreto falso) y de paso
  destapó un falso positivo de `detect-secrets`, que marcaba `DB_PASS: ci_placeholder...` como
  "Secret Keyword" y frenaba el commit. Se resolvió **eliminando la causa**, no con un
  `pragma: allowlist`: el gate no tiene por qué fingir credenciales.

### Verificación post-fix (todo re-corrido, nada heredado del reporte anterior)

| Check | Resultado |
|---|---|
| `python manage.py test` | **850/850** OK (194 s) — 846 base + 4 del fix |
| `apps.core.tests.test_production_settings` + `test_settings_profiles` | 44/44 OK |
| `DEBUG=False python manage.py check` (perfil `testing`, `.env` real) | `no issues (0 silenced)` — antes fallaba |
| `PRODUCTION=1 DB_ENGINE=sqlite3 EMAIL_BACKEND=<smtp> manage.py check --deploy --fail-level WARNING` | `no issues (1 silenced)` — el gate exacto de CI, sin credenciales falsas |
| `PRODUCTION=1` + `EMAIL_BACKEND`=consola | `ImproperlyConfigured` (rama negativa del assert) |
| `ruff check .` | All checks passed |


## Commits

| Commit | Alcance |
|---|---|
| (pendiente) `refactor(settings):` endurecer perfil de producción + gate de deploy en CI | los 6 puntos de alcance + los 8 tests + la corrección de ruido + el fix de `get_database_config` que la verificación destapó |
| (pendiente) `chore(odd):` | este registro de verificación, hallazgo y corrección |

> Nota de proceso: la sesión anterior cerró declarando en memoria un commit `4f43d51` que
> **nunca existió** (`git cat-file -t 4f43d51` → `Not a valid object name`). El trabajo estaba
> implementado en el working tree pero sin commitear y con este doc en "Sin empezar". Cerrado acá:
> la evidencia se registra con lo observado hoy, no con lo declarado antes.
