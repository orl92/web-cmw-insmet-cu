# install.sh / deploy.sh interactivos: bootstrap completo en un solo comando

## Objetivo

Que la instalación de producción se ejecute con **un solo archivo descargado y ejecutado**, sin
que el operador clonar el repo ni copiar comandos a mano, y que las decisiones de configuración
(base de datos, superusuario, correo, Nginx) se pregunten **interactivamente** en vez de quedar
escritas como `CHANGE_ME` en un archivo que alguien tiene que editar después.

## El problema que se resuelve

Hoy hay dos huecos que se complementan:

1. `deploy/install.sh` se declara explícitamente parcial en su propio encabezado (líneas 22-27):
   NO genera el `.env`, NO crea el venv, NO instala prerrequisitos, NO toca Nginx. Deja una lista
   de "Falta (no lo hace este script)" con seis ítems, cuatro de los cuales son decisiones del
   operador (dominio, credenciales, correo, tipo de proxy). El resultado es que el procedimiento
   se ejecuta a medias, y el README ya documenta que varios de esos pasos "no funcionan como
   están escritos".
2. `scripts/generate_env.py` es deliberadamente **no interactivo** (documentado: "un generador
   que adivina el entorno es un generador que un día escribe el `.env` equivocado") y escribe
   `CHANGE_ME` en DB y EMAIL. Correcto para un script invocado por CI; incorrecto como único
   punto de entrada de una instalación humana.

El hueco de `deploy.sh` es el espejo: es invocado por SSH desde GitHub Actions, donde **no hay
TTY**, y su health check está cableado a `--resolve "$PUBLIC_HOSTNAME:443:127.0.0.1"`. Si el
reverse proxy no es el Nginx local (la opción "Nginx Proxy Manager externo"), ese health check
falla por construcción y el deploy se bloquea con un sitio perfectamente sano.

## Decisiones de diseño (tomadas en exploración, no son preguntas abiertas)

| Decisión | Motivo |
|---|---|
| `install.sh` queda **auto-contenido**: no importa nada del checkout | Es lo que permite `curl … \| sudo bash`. Antes de clonar el repo no hay ningún archivo del proyecto disponible. |
| Las prompts viven en `install.sh`; `deploy.sh` **no** se vuelve interactivo en su camino de deploy | El camino de deploy es no-interactivo por contrato (CI por SSH, sin TTY). Forzar prompts ahí rompe el workflow. En su lugar `deploy.sh` gana un modo `--configure` explícito y sigue leyendo `/etc/webcmp/deploy.env`. |
| Detección de TTY: sin TTY y sin `--non-interactive` → `die` con instrucciones | Fallar cerrado. Un instalador que adivina en un管道 escribe el `.env` equivocado y nadie lo ve. |
| Idempotencia preservada: en una re-corrida, cada prompt muestra el valor actual como default y nada se sobrescribe a ciegas | El script ya es idempotente por diseño (comentario de cabecera). Una reinstalación no puede regenerar la `SECRET_KEY` ni tirar la base. |
| Dos opciones de proxy, y el health check se vuelve parametrizable | Es lo que hace que la opción "Nginx Proxy Manager externo" sea viable: el health check apunta al upstream local en vez de a `127.0.0.1:443`. |
| PostgreSQL local es el default de DB; MySQL y SQLite offered con advertencia explícita | `generate_env.py` ya separa el caso producción (PostgreSQL) del de desarrollo (SQLite); SQLite en producción rompe el modelo de `MEDIA_ROOT`/volúmenes y no tiene `DB_*`. |

## Alcance

| ID | Tarea | Archivo principal |
|---|---|---|
| T1 | `install.sh` auto-contenido: preflight de root + TTY + distro; prerrequisitos de sistema (apt) | `deploy/install.sh` |
| T2 | Clonar el repo a `APP_DIR` (default `/srv/webcmp`) como `webcmp`, idempotente; `git` ya instalado por T1 | `deploy/install.sh` |
| T3 | Usuario de servicio `webcmp` + directorios (`media/`, `logs/`, `staticfiles/`, `.cache/`) con owner correcto | `deploy/install.sh` |
| T4 | Prompts de dominio: `EXTERNAL_HOSTNAME`, `www`, puertos, `PUBLIC_HOSTNAME` (se deriva del anterior para que coincidan los tres lugares que hoy hay que editar a mano) | `deploy/install.sh` |
| T5 | Prompts de DB: engine (postgresql/mysql/sqlite), name, user, password (generada si se deja vacía), host, port, `DB_SSL_MODE`; creación real del rol y la base con el usuario prompted | `deploy/install.sh` |
| T6 | Prompts de correo: backend, host, port, user, password, `DEFAULT_FROM_EMAIL`, TLS/SSL; respeta el assert de `production.py` (leer `config/settings/production.py` antes de decidir) | `deploy/install.sh` |
| T7 | Prompts de superusuario: username, email, password (o generada e impresa una vez), idioma, y `createsuperuser` no-interactivo vía `systemd-run -p Environment=` (el bug documentado en `deploy.sh:200-207`) | `deploy/install.sh` |
| T8 | Otros campos del `.env`: `REDIS_URL`, `USE_REDIS_CACHE`, `LOG_LEVEL`, `FTP_OBS_*` (bloque opcional), `LDAP_*` (opcional, comentado) | `deploy/install.sh` |
| T9 | Generar el `.env` con `scripts/generate_env.py --production` y luego sustituir los `CHANGE_ME` con los valores prompted, sin pisar un `.env` afinado a mano sin confirmación | `deploy/install.sh` |
| T10 | venv + `requirements/prod.txt`, `makemigrations`, `migrate`, `collectstatic`, `check --deploy` | `deploy/install.sh` |
| T11 | Unidades systemd templadas a `APP_DIR`/`SERVICE_USER` reales, `daemon-reload`, `enable --now` | `deploy/install.sh` |
| T12 | Opción de proxy **A**: instalar y configurar Nginx local (vhost desde `deploy/nginx/webcmp.conf.example` renderizado con el dominio, `www-data` en el grupo `webcmp`, cert: certbot si el DNS es público o autofirmado con aviso explícito) | `deploy/install.sh` |
| T13 | Opción de proxy **B**: Nginx Proxy Manager externo — no se instala ni se toca Nginx; se imprimen los datos exactos del upstream (socket, `Host`/`X-Forwarded-*`, timeouts) y el health check se apunta al upstream local | `deploy/install.sh` |
| T14 | Escribir `/etc/webcmp/deploy.env` con `PUBLIC_HOSTNAME` y el destino del health check coherentes con T4/T12/T13; **no** pisar si existe sin confirmación | `deploy/install.sh` |
| T15 | Andamiaje de deploy automático que hoy vive en `install.sh`: usuario de despliegue, keypair, `webcmp-deploy` en `/usr/local/sbin`, sudoers validado con `visudo` | `deploy/install.sh` |
| T16 | `deploy.sh`: parametrizar el health check (host/port/esquema/TLS) para que funcione con proxy externo, conservando el comportamiento actual por default | `deploy/deploy.sh` |
| T17 | `deploy.sh`: `--configure` interactivo que (re)escribe `/etc/webcmp/deploy.env` reutilizando el mismo criterio de defaults, y `--check` que solo valida la config sin desplegar | `deploy/deploy.sh` |
| T18 | `deploy/README-deploy.md`: el flujo nuevo es descargar `install.sh` y correrlo; el camino manual queda como alternativa documentada | `deploy/README-deploy.md` |

Fuera de alcance: tocar `config/settings/**` (el `.env` tiene que alcanzar con lo que ya existe),
el workflow `.github/workflows/deploy.yml`, y la suite de `apps/`. Si algo de T1-T18 descubre que
un setting no alcanza, se documenta en la sección de abajo y se escala, no se parchea a ciegas.

## Superficie de edición autorizada

```
deploy/install.sh
deploy/deploy.sh
deploy/README-deploy.md
```

## Criterios de aceptación

- [ ] `curl -fsSL <raw>/deploy/install.sh | sudo bash -s -- --help` imprime uso y sale 0, sin tocar
      el sistema (no exige TTY para `--help`).
- [ ] Sin TTY y sin `--non-interactive`, el script aborta ANTES de cualquier cambio, con el mensaje
      que dice cómo correrlo.
- [ ] `bash -n deploy/install.sh` y `bash -n deploy/deploy.sh` pasan.
- [ ] `shellcheck` no reporta errores de severidad `error` en ambos scripts (los `warning`/`info`
      preexistentes se anotan, no se silencian).
- [ ] Ninguna ruta de `install.sh` deja un `.env` con `CHANGE_ME` cuando el operador respondió los
      prompts (o cuando eligió explícitamente la opción "dejar sin configurar").
- [ ] Una segunda corrida del script no regenera claves, no borra la base, y no pisa `/etc/webcmp/deploy.env`
      ni un `.env` existente sin confirmarlo.
- [ ] La opción B (proxy externo) deja `HEALTHCHECK_*` apuntando al upstream local y `deploy.sh` con
      esa config pasa el health check sin TLS de por medio.
- [ ] `python manage.py check` sigue pasando (el `.env` de desarrollo del repo no se toca).

## Checks

| Qué cambió | Verificación |
|---|---|
| Dos scripts bash, sin Django | `bash -n` + `shellcheck` + `sh -n` sobre ambos |
| Documentación | `djlint` no aplica; revisar el markdown renderizado a ojo |
| Nada de `apps/**`, `config/**`, `requirements/**` | `python manage.py check` |

## Progreso

- [x] T0 — Exploración: los tres scripts y el flujo de settings leídos
- [ ] T1-T5 — Preliminares, clone, usuario, dominio, base de datos
- [ ] T6-T9 — Correo, superusuario, resto del `.env`, generación
- [ ] T10-T13 — Venv, migrate, systemd, las dos opciones de proxy
- [ ] T14-T15 — `deploy.env` y andamiaje de deploy automático
- [ ] T16-T17 — `deploy.sh`: health check parametrizable y `--configure`
- [ ] T18 — README

## Decisiones pendientes que hay que escalar (no resolver a ciegas)

Ninguna bloqueante ahora. Si durante la implementación aparece que un campo del `.env` que el
operador decide no tiene contraparte en `config/settings/**`, se para la tarea y se reporta en vez
de agregar el setting.

## Próximo paso

T1.
