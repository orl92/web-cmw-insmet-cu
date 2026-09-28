# Deploy de producción: generate_env como script, fail-closed real, systemd + Nginx

## Objetivo

Que el servidor de producción se monte **desde cero**, con un procedimiento reproducible y sin
la paradoja de bootstrap que hoy obliga a dejar una puerta trasera abierta en los settings.

## El problema que se resuelve

`generate_env` es un management command. `manage.py` → `execute_from_command_line()` →
`django.setup()` → **importa los settings antes de despachar el comando**. Para que el comando
que genera la clave pueda arrancar, `base.py` tiene que tolerate no tener clave: hoy cae a
`get_random_secret_key()` y avisa (`EphemeralSecretKeyWarning`, PR #80). Es un bypass de
bootstrap, y mientras exista, un perfil de producción sin clave correcta no se distingue del
que la tiene.

Mover el generador fuera de Django rompe la paradoja: un script plano que solo depende de
`cryptography` puede correr cuando los settings no pueden, y entonces los settings sí pueden
fallar cerrado.

## Second-order: por qué `ENCRYPTION_KEY` no puede vivir en el `.env`

Hoy el `.env` guarda `SECRET_KEY` **cifrada con** `ENCRYPTION_KEY`, y las dos están en el mismo
archivo. Eso no es cifrado: es teatro. Si el `.env` se filtra, la clave con la que estaba cifrado
filtra junto a él y el secreto sale en un `Fernet.decrypt`. La clave de descifrado tiene que vivir
en un archivo que el `.env` no puede alcanzar: `/etc/webcmp/encryption.env`, `chmod 600`, root.

`load_dotenv(override=False)` no pisa variables ya presentes en el entorno, así que el unit puede
inyectar `ENCRYPTION_KEY` desde `EnvironmentFile=-` y el `.env` nunca la pisa. Con eso, un `.env`
filtrado no entrega nada por sí solo.

## Alcance

| ID | Tarea | Archivo principal |
|---|---|---|
| T1 | `scripts/generate_env.py`: script plano, sin Django, no interactivo, flags `--development`/`--production`/`--rotate-keys` | nuevo |
| T2 | `base.py` falla cerrado 100%: sin par descifrable → `ImproperlyConfigured`, en TODOS los perfiles. Se borra `EphemeralSecretKeyWarning` y su test | `config/settings/base.py` |
| T3 | `testing.py` inyecta un par determinista ANTES de `from .base import *` | `config/settings/testing.py` |
| T4 | Un solo entry point: se borra el management command y toda referencia a `manage.py generate_env` | `apps/core/management/commands/` |
| T5 | `deploy/systemd/webcmp.service` + `deploy/nginx/webcmp.conf.example` versionados, sin secretos | nuevo |
| T6 | Se retira `gunicorn.sh` (el unit lo reemplaza con `ExecStart` directo) | borrar |
| T7 | `deploy-check` de CI usa el script en vez del snippet inline de Fernet | `.github/workflows/ci.yml` |
| T8 | `.env` de producción **no** lleva `ENCRYPTION_KEY`; el unit la toma de `encryption.env` | script + unit |
| T9 | Onboarding: `make setup` genera el `.env`; README y AGENTS.md dejan de mandar a `manage.py generate_env` | `Makefile`, docs |

## Decisiones cerradas (acordadas antes de escribir código)

| Decisión | Razón |
|---|---|
| El generador es un script, no un comando | Es lo único que rompe la paradoja de bootstrap. Sin esto, T2 es imposible. |
| `ENCRYPTION_KEY` en `/etc/webcmp/encryption.env`, no en el `.env` | El `.env` se filtra; una clave de descifrado junto al texto cifrado no protege nada. |
| systemd, no supervisor | El servidor se monta desde cero: no hay legado que conservar. systemd da `Restart=`, `RuntimeDirectory=` y `EnvironmentFile=` sin depender de un `.conf` que alguien tiene que acordarse de regenerar. |
| Configs deterministas versionadas; secretos solo en el servidor | El `.service` y el `.conf.example` se revisan en un PR. Un `.conf` con contraseña viviente en el repo es un secreto en el repo. |
| PostgreSQL + `psycopg[binary]` | Ya decidido y aterrizado en `requirements/prod.txt` (PR #80). |
| `Type=notify` + socket en `/run/webcmp` | systemd sabe si el proceso arrancó de verdad. Con un script en `/tmp` y `Type=simple`, un worker que muere al segundo se ve "activo" para siempre. |
| T2 en todos los perfiles, no solo producción | Un perfil que arranca sin clave no está endurecido, está mentido. La unauthorized-by-default vale para los tres. |

## Restricciones

- **Un solo entry point.** Si quedan dos formas de generar el `.env`, alguien usa la que no
  endurece nada. Por eso T4 es parte del mismo trabajo, no una limpieza posterior.
- El `.env` nunca se commitea (ya está en `.gitignore`).
- Los archivos de `deploy/` no pueden contener secretos: son placeholders explícitos.
- Ubuntu 26.04 LTS, Python 3.14 nativo, usuario dedicado `webcmp`, app en `/srv/webcmp`.

## Verificación

- `python scripts/generate_env.py --development` y `--production` escriben un `.env` válido en un
  directorio temporal, sin Django importado (se comprueba con `sys.modules`).
- El par generado descifra: el script se relee con `config.settings.base.decrypt_secret_key`.
- Fail-closed por los DOS lados: sin `.env` revienta con mensaje que dice qué ejecutar; con `.env`
  válido arranca.
- `python manage.py test` verde **sin `.env`** (el perfil `testing` inyecta su par).
- `PRODUCTION=1 ... check --deploy --fail-level WARNING` limpio con el `.env` de producción.
- `systemd-analyze verify deploy/systemd/webcmp.service` acepta la unidad.
- `nginx -t -c deploy/nginx/webcmp.conf.example` si hay nginx disponible; si no, se documenta el
  chequeo pendiente en vez de darlo por bueno.
- `grep -rn "manage.py generate_env"` no devuelve nada.

### Estado de la verificación tras `d5170a4`

- 868 tests OK (12 del script, 43 de perfiles de los cuales 13 son el fail-closed nuevo).
- `python manage.py check --deploy --fail-level WARNING` limpio en clon sin `.env`: 0 issues,
  1 silenciado (W008, lo resuelve Nginx).
- Las 4 ramas del fail-closed verificadas con el `.env` real movido aside, en `dev`,
  `production` y `testing`.
- El par del script descifra con `config.settings.base.decrypt_secret_key` y pasa `_check_secret_key`.
- Ruff check + format limpios; `detect-secrets` limpio sin ampliar el baseline.

Correcciones sobre lo planificado, y por que:

- El dispatcher de `config/settings/__init__.py` tuvo que leer `.env` y las banderas él mismo.
  Leía `DEBUG` desde `base`, así que importar el paquete importaba `base`, y `base` fail-closed
  mataba al perfil `testing` antes de que este pudiera inyectar su par. El plan daba por hecho
  que alcanza con inyectar en `testing.py`; no alcanza, y el fallo se ve solo en un clon limpio.
- El par determinista quedo en `config/settings/_testing_keys.py` y no dentro de `testing.py`:
  lo necesitan los dos caminos (dispatcher e import directo) ANTES de importar `base`, y duplicar
  la constante en dos sitios es como el par de testing se desincroniza del suyo propio.
- La clave Fernet de testing se DERIVA (`sha256` de una constante publica) en vez de escribirse.
  Una cadena de 32 bytes literal en el repo es un string de alta entropia que `detect-secrets`
  marca como secreto; derivado no hay nada que alguien pueda intentar usar.

TDD: **off** (no hay `strict_tdd` registrado; los guards de configuración se prueban por sus
ramas negativas, que es donde un test de valor aporta). Runner: `python manage.py test`.

## Riesgo

| Riesgo | Mitigación |
|---|---|
| Sacar el management command rompe el flujo de quien ya lo conoce | El mensaje de error del fail-closed dice el comando exacto a ejecutar, y `make setup` lo hace solo. |
| Fail-closed en `base.py` rompe el arranque de cualquier comando sin `.env` | Es el objetivo. El `testing.py` cubre la suite; el script cubre el primer arranque. |
| Un unit con rutas hardcodeadas no sirve para otra instalación | Las rutas están escritas y documentadas al tope del archivo, con el aviso de re-verificar. **No** se pueden abstraer en una variable: `APP_DIR=/srv/webcmp` no es clave válida de systemd (ver desviación 4). |
| Sacar `gunicorn.sh` y que el servidor actual lo necesite | Se retira **después** de que el unit esté verificado, y el PR dice explícitamente que el deploy pasa a systemd. |

## Progreso

Rama `feat/production-deploy`, apilada sobre `refactor/settings-profiles-hardening` (PR #80): el
paquete de perfiles todavía no está en `main` y T2 lo necesita.

- [x] T1 `scripts/generate_env.py` — commit `d5170a4`
- [x] T2 `base.py` fail-closed 100% — `d5170a4`
- [x] T3 par determinista en `testing.py` — `d5170a4`, con `_testing_keys.py` como dueño unico
- [x] T4 borrar el management command y sus referencias — `d5170a4`
- [x] T5 `deploy/systemd/` + `deploy/nginx/` — commit `320dc12`
- [x] T6 retirar `gunicorn.sh` — commit `ee96f8d` (`feat(deploy)`, ver historial)
- [x] T7 CI `deploy-check` usa el script — commit `ee96f8d`
- [x] T8 `ENCRYPTION_KEY` fuera del `.env` — script en `d5170a4`, unit en `320dc12`
- [x] T9 onboarding y docs — commit `ee96f8d`

### Commits

| Commit | Qué |
|---|---|
| `d5170a4` | T1–T4: script plano, fail-closed, par de testing, command borrado |
| `9cf1831` | Registro de T1–T4 y sus desviaciones |
| `320dc12` | T5: unidades systemd + ejemplo de Nginx |
| `ee96f8d` | T6 + T7 + T9: fuera `gunicorn.sh`, CI usa el script, docs y Makefile |
| `e8a9722` | Default del `.env` anclado a la raíz del repo |

### Estado de la verificación tras `e8a9722`

- 870 tests OK (14 del script, 43 de perfiles con 13 de fail-closed).
- `systemd-analyze verify` acepta **ambos** units. Los avisos restantes son de
  paths del servidor (`/srv/webcmp`), que no existen en la máquina que verifica.
- Procedimiento del README ejecutado de punta a punta, con el `.env` real del
  repo ausente: el script genera el `.env` de producción **sin** `ENCRYPTION_KEY`,
  `EnvironmentFile=-` lo inyecta y `check --deploy` da 0 issues, 1 silenciado.
- Sin la clave inyectada, el fallo nombra el archivo exacto que falta.
- Job de CI simulado con el `.env` real del repo movido aside (checkout limpio):
  el script genera el par, el gate corre con 0 issues.
- `make env` con un `.env` presente no lo toca (mismo md5 antes y después).
- `detect-secrets` con pragma inline sobre el `PASSWORD 'CAMBIAR_ESTA_CLAVE'` del
  README, que es un placeholder deliberado.

### Pendiente que no se puede cerrar desde acá

- `nginx -t` sobre `deploy/nginx/webcmp.conf.example`: **nginx no está instalado**
  en la máquina de desarrollo. La configuración se valida en el servidor, antes
  de reloadear. Queda anotado acá a propósito, no dado por bueno.
- `specs/013-check-deploy-ci/spec.md` sigue exigiendo `EphemeralSecretKeyWarning` y
  `manage.py generate_env`, que este trabajo retiró. El spec promovido se cambia
  por un delta spec nuevo, no editándolo acá.

### Desviaciones 4 a 7, y por qué

4. **Las rutas del unit van escritas, no en una variable.** El primer `webcmp.service`
   usaba `APP_DIR=/srv/webcmp` en `[Service]`, y `systemd-analyze verify` lo rechazó:
   `Unknown key 'APP_DIR' in section [Service]`, más `WorkingDirectory= path is not
   absolute: ${APP_DIR}`. systemd no expande variables de entorno en esas
   directivas, así que la indirección no funcionaba. Con rutas escritas, el unit
   verifica y el operador edita seis paths si el checkout cambia de lugar.
5. **`WatchdogSec` quedó solo en el unit de Gunicorn.** El de Huey lo declaraba con un
   comentario que decía que mataba un consumer trabado, y eso era falso: el watchdog
   mide un heartbeat que solo existe con `Type=notify`, así que en un `Type=simple`
   no vigila nada. Huey no implementa `sd_notify`. El comentario ahora dice la
   verdad: un consumer trabado no se detecta solo, hay que mirarlo.
6. **T7 no es solo "usar el script": el gate tiene que seguir siendo ciego a lo que
   era.** Una primera simulación local falló con el rechazo de `EMAIL_BACKEND`
   console, y la causa era el `.env` real del repo filtrándose al entorno, no el
   cambio. La lección es que el gate se valida con el repo en estado de CI (`.env`
   ausente), no con el checkout del desarrollador: los dos se corrieron.
7. **El default de `--env-file` se ancló a la raíz del repo.** La prueba de punta a
   punta del README mostró que el default era relativo al CWD mientras los settings
   leen `BASE_DIR/'.env'`: dos paths distintos para el mismo archivo. Un `--env-file`
   fuera de la raíz ahora avisa, porque el flag se usa justamente en los tests y en
   CI, donde el archivo no es para Django.
