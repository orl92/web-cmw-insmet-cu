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

- `python -m scripts.generate_env --development` y `--production` escriben un `.env` válido en un
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

TDD: **off** (no hay `strict_tdd` registrado; los guards de configuración se prueban por sus
ramas negativas, que es donde un test de valor aporta). Runner: `python manage.py test`.

## Riesgo

| Riesgo | Mitigación |
|---|---|
| Sacar el management command rompe el flujo de quien ya lo conoce | El mensaje de error del fail-closed dice el comando exacto a ejecutar, y `make setup` lo hace solo. |
| Fail-closed en `base.py` rompe el arranque de cualquier comando sin `.env` | Es el objetivo. El `testing.py` cubre la suite; el script cubre el primer arranque. |
| Un unit con rutas hardcodeadas no sirve para la simulación local | Rutas como variables documentadas al tope del archivo; la simulación en Debian 14 usa `systemd --user` o copia con rutas locales. |
| Sacar `gunicorn.sh` y que el servidor actual lo necesite | Se retira **después** de que el unit esté verificado, y el PR dice explícitamente que el deploy pasa a systemd. |

## Progreso

Rama `feat/production-deploy`, apilada sobre `refactor/settings-profiles-hardening` (PR #80): el
paquete de perfiles todavía no está en `main` y T2 lo necesita.

- [ ] T1 `scripts/generate_env.py`
- [ ] T2 `base.py` fail-closed 100%
- [ ] T3 par determinista en `testing.py`
- [ ] T4 borrar el management command y sus referencias
- [ ] T5 `deploy/systemd/` + `deploy/nginx/`
- [ ] T6 retirar `gunicorn.sh`
- [ ] T7 CI `deploy-check` usa el script
- [ ] T8 `ENCRYPTION_KEY` fuera del `.env`
- [ ] T9 onboarding y docs
