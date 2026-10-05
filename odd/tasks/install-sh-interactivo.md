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
| Detección de TTY: sin TTY y sin `--non-interactive` → `die` con instrucciones | Fallar cerrado. Un instalador que adivina en un pipeline escribe el `.env` equivocado y nadie lo ve. |
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
| T19 | `deploy.sh`: invocar pip como `python -m pip` en vez del shim `bin/pip`, que no existe | `deploy/deploy.sh` |
| T20 | `deploy.sh`: `--configure` debe poder **crear** `/etc/webcmp/deploy.env` en un host limpio | `deploy/deploy.sh` |
| T21 | `install.sh`: `need_checkout` debe cortar de verdad los bloques que renderizan desde el checkout | `deploy/install.sh` |
| T22 | `install.sh`: la elección de motor de base de datos desaparece; PostgreSQL es constante y el puerto se pregunta con default 5432 | `deploy/install.sh` |
| T23 | `install.sh`: tres validadores de correo roto impedían configurar SMTP; se arreglan y el prompt del host dice dónde va el `@` | `deploy/install.sh` |
| T24 | `install.sh`: los defaults reales del proyecto — `meteocamaguey.cu` como dominio y `mx.caonao.cu` como servidor SMTP | `deploy/install.sh` |

Fuera de alcance: tocar `config/settings/**` (el `.env` tiene que alcanzar con lo que ya existe),
el workflow `.github/workflows/deploy.yml`, y la suite de `apps/`. Si algo de T1-T18 descubre que
un setting no alcanza, se documenta en la sección de abajo y se escala, no se parchea a ciegas.

T19-T21 no son alcance nuevo: son **correcciones de defectos** detectados al leer el diff del
commit `a9e01c6`, es decir el alcance original se entregó con tres bugs deterministas.

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

## Defectos post-entrega (encontrados leyendo el diff de `a9e01c6`)

Los tres son **deterministas**: no dependen del entorno, se disparan siempre que se llega al
camino de código. Ninguno lo detectó `bash -n` ni `manage.py check`, porque son errores de
lógica y de rutas, no de sintaxis.

### T19 — `PIP` apunta a un archivo inexistente (`deploy/deploy.sh:274`)

```bash
: "${PIP:=$APP_DIR/.venv/bin/python/pip}"
```

`bin/python` es el **intérprete**, no un directorio que contenga a `pip`. `pip` es un script
hermano de `python`, no un hijo suyo. Rompe las dos invocaciones reales del símbolo: la línea 742
(instalación de `requirements/prod.txt`) y la línea 664 ( reinstall del rollback).

Evidencia que impide el arreglo obvio: el `.venv` de este repo **no tiene `pip`** — solo
`pip3` y `pip3.14`. Un venv creado con `uv` no trae ese shim. Entonces cambiar a `bin/pip`
seguiría roto.

**Decisión:** invocar `python -m pip`. No depende del shim, funciona siempre que el módulo esté
instalado, y `PIP` sigue siendo sobreescribible desde `deploy.env`. Pasa a ser un array
(`PIP_CMD`) porque son dos palabras y `"$PIP"` con texto partido rompería el quoting.

### T20 — `--configure` muere antes de poder crear el archivo que exige (`deploy/deploy.sh:254` vs `:421`)

```
254:  [ -r "$CONFIG" ] || die "No existe $CONFIG ..."
257:  source "$CONFIG"
...
351:  configure_deploy_env() {     # ya sabe crear el archivo: linea 388, [ ! -f "$CONFIG" ]
421:  if [ "$MODE" = configure ]; then configure_deploy_env; fi
```

El guard y el `source` corren **167 líneas antes** del branch `configure`. En un host limpio,
donde `/etc/webcmp/deploy.env` todavía no existe, `--configure` muere en el `die` y nunca llega
a la función que sí sabe crearlo. Anula el propósito completo del flag.

**Decisión:** el guard y el `source` se saltan cuando `MODE=configure`. Los defaults de las
líneas 268-311 ya dan a los prompts los mismos valores que habría dado el `source`, que es justo
lo que un host limpio necesita.

### T21 — `need_checkout` no puede cortar nada (`deploy/install.sh:1256-1260`)

```bash
need_checkout() {
    [ "$HAVE_CHECKOUT" -eq 1 ] && return 0
    printf '  [dry-run] sin checkout: %s\n' "$1" >&2
    return 0     # ← devuelve 0 en AMBAS ramas
}
```

Sus cuatro consumidores lo usan como cortocircuito, y los cuatro ejecutan trabajo real desde
`$APP_DIR/deploy/**`, que solo existe si hay checkout:

| Línea | Consumidor | Trabajo que se dispara sin checkout |
|---|---|---|
| 1589 | `if need_checkout ...; then` | `render_unit` desde `deploy/systemd/` |
| 1734 | `[ -f "$vhost_src" ] \|\| need_checkout ...` | `render_vhost` desde `deploy/nginx/` |
| 2088 | `[ -f ...deploy.sh ] \|\| need_checkout ...` | instala un `deploy.sh` inexistente |
| 2096 | `[ -f ...webcmp-deploy ] \|\| need_checkout ...` | `render_template` + `visudo` |

Con `return 0` en ambas ramas el `||` nunca corta: los cuatro bloques corren en `--dry-run` sin
checkout y fallan leyendo rutas ausentes.

**Decisión:** `return 1` cuando no hay checkout. Imprime el mismo aviso (es efecto secundario) y
hace que el consumidor se salte el bloque, que es lo que el nombre de la función promete.

### Cuarto hallazgo: **retirado**, no era bug

`install.sh:2070` genera el keypair con `ssh-keygen -N ''` y deja la clave pública en
`$CONFIG_DIR/deploy_key.pub`. Se Lea como "no instala la clave en `authorized_keys`", pero el
flujo es correcto: la CI pega la **pública** en GitHub como secret y la **privada** nunca sale
del servidor. `authorized_keys` no aplica. Queda anotado para que nadie lo "arregle" después.

### T22 — Se quitó la elección de motor de base de datos (decisión del usuario)

El instalador preguntaba el motor entre `postgresql`, `mysql` y `sqlite3`. Ya no se pregunta:
`DB_ENGINE=postgresql` es una **constante**, asignada y no tomada del entorno, para que un
`DB_ENGINE=mysql` exportado por error no contradiga la decisión.

Qué se eliminó al dejar de haber elección:

| Se fue | Por qué ya no aplica |
|---|---|
| `ask_one_of DB_ENGINE` y su bloque explicativo | El motor es único |
| `valid_db_engine()` | Sin entrada del operador, no hay qué validar |
| Bloque MySQL de C.4 (`sql_quote`, `CREATE USER IF NOT EXISTS`) | Sin motor MySQL |
| `MYSQL_BUILD_DEPS` + aviso de driver fuera de pins en C.1 | `psycopg[binary]` trae su binario, no compila |
| `case "$DB_ENGINE"` del `DB_SERVER_PACKAGE` | Ahora es `postgresql` fijo, y `psql` es el único cliente a buscar |
| Instalación de `mysqlclient` en el venv (C.5) | Fuera de los pins era un riesgo que ya no se corre |
| `sql_quote()` | Solo la usaba el bloque MySQL. `psql_quote()` sigue, y es la que protege la contraseña real |
| `if [ "$DB_ENGINE" != sqlite3 ]` que envolvía los `apply_env_value` | Los seis `DB_*` se escriben siempre |

El puerto se sigue preguntando, con el default del motor: `ask DB_PORT 5432`. Cambiarlo sigue
siendo una decisión del operador, que es lo que se pidió; lo que se quitó fue la elección de
**motor**, no la de dirección de conexión. `DB_SSL_MODE` también queda con su default `prefer`
y su lista de valores de PostgreSQL, sin las opciones de MySQL.

**Lo que NO cambió:** `config/settings/base.py`. `get_database_config()` sigue aceptando `mysql`
y `sqlite3`, y el `.env` de desarrollo del repo sigue en `sqlite3`. El cambio es del instalador
de producción, no de la capa de settings. Tocar `base.py` saldría de la superficie autorizada de
esta feature y rompería el desarrollo local.

### Bug opportunista corregido de paso (T22)

C.5 invocaba `'$VENV_DIR/bin/pip'` para instalar requirements: **el mismo shim que T19
eliminó de `deploy.sh`**. Un venv creado con `uv` no lo trae, y el `.venv` de este repo es
justo ese caso. Ahora es `'$VENV_DIR/bin/python' -m pip`. Sin esto, quitar el motor MySQL
dejaba el camino de PostgreSQL installando requirements por un shim que puede no existir.

### T23 — Los validadores de correo impedían configurar SMTP

El operadorTrying de configurar el correo en el servidor real y el instalador le rejected tres
veces con `Valor invalido para EMAIL_HOST`. Al reproducirlo en local aparecieron **tres defectos
deterministas**, todos en el mismo archivo y todos del mismo tipo: un validador que rechaza el
valor que la pregunta pide.

**1. `valid_email` rechazaba TODO correo.** La clase de caracteres del `case` era
`[!a-zA-Z0-9._%+-]`: no incluía `@`. El `case` corría **antes** que el regex, así que ninguna
dirección llegaba a validarse. `ACME_EMAIL` y `SUPERUSER_EMAIL` eran inalcanzables: con un correo
válido el operador perdía tres intentos y el instalador moría. Agregar `@` a la clase.

**2. `valid_smtp_host` no existía; `valid_host` no daba ninguna pista.** El error decía
`Valor invalido para EMAIL_HOST`, que no dice qué se espera ni por qué falló. Se agregó un
validador dedicado que además rechaza explícitamente el `@`, y el prompt dice "SIN @ (ej.
smtp.caonao.cu)" y el `die` final repite dónde va el correo. La restricción del `@` en el host
se mantiene a propósito: `EMAIL_HOST` llega a `settings.py`, al vhost de Nginx y al `source` de
`deploy.env`, donde un `@` rompe el archivo.

**3. `EMAIL_HOST_USER` usaba `valid_app_user`, que rechaza `@`.** El usuario de AUTH de casi
todo proveedor público **es** la dirección completa. Con `valid_app_user` el correo entero se
rechazaba tres veces, igual que en el host. Se agregó `valid_smtp_user`, que acepta las dos
formas reales: login corto (`admin`, relays internos) y dirección completa.

**Sobre "aunque el servidor no esté disponible":** el instalador **nunca** prueba conectividad
SMTP — no hay `nc`, ni `telnet`, ni `swaks`, ni un `timeout` contra el host. Se verificó con grep
sobre el archivo. Solo valida formato, así que configurar un host que todavía no responde es un
camino soportado: el correo funciona en cuanto el servidor esté arriba. Eso se dice explícito en
el texto del bloque, porque la ausencia de la prueba no era evidente.

**Bug de rango encontrado de paso.** Al validar `valid_email` con `:`, `/`, `<`, `=`, `?` se
aceptaban. La clase `+-@` no es tres literales: bash la lee como el rango 0x2B..0x40 y arrastra
todo lo que hay en medio. Se movió el guion al final (`@+-`), donde sí es literal.

Verificación: `bash -n`; los cuatro validadores extraídos del archivo real con `sed` (no
reimplementados) reproducen los tres rechazos del operador y aceptan el camino correcto;
`valid_smtp_user` acepta login corto, dirección completa y vacío; `valid_email` sigue rechazando
`@x.cu`, `a@b`, espacios y `a@b@c.cu`; dry-run completo pasa con `EMAIL_CONFIGURED=1` y puerto
465 → `EMAIL_USE_SSL=si`, `EMAIL_USE_TLS=no`.

### T24 — Defaults reales del proyecto

`install.sh` traía `web.cmw.insmet.cu` y `EMAIL_HOST` vacío como defaults. Son valores de otro
dominio, no de este proyecto, y convertían cada instalación real en una tanda de correcciones
manuales. Ahora el default del dominio es `meteocamaguey.cu` y el del servidor SMTP es
`mx.caonao.cu`.

Consecuencia que vale la pena registrar: `EMAIL_HOST` con default **no vacío** cambia el punto de
entrada del correo. `EMAIL_CONFIGURED` pasa a ser `1` pordefault (antes solo lo era si el operador
escribía algo), así que el bloque `.env` ya no deja `CHANGE_ME` en la sección de correo y el gate
del `.env` no se para. Ese es el comportamiento correcto para este proyecto: hay un servidor de
correo que se va a usar.

`ACME_EMAIL` se dejó con default vacío a propósito. El bloque de TLS va **antes** del bloque de
correo, así que `EMAIL_HOST_USER` todavía no está preguntado ahí; usarlo como default sería leer
una variable sin asignar, y con `set -u` en bash eso no es `""` sino un error que mata el
instalador. Se intentó primero y se revirtió por esa razón.

Verificado: `bash -n`; el dominio fluye correctamente a `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`,
`CORS_ALLOWED_ORIGINS`, `server_name`, CN y SAN del certificado, `--cert-name`, health check con
SNI y rutas de `TLS_CERT`/`TLS_KEY`; `www.meteocamaguey.cu` se deriva solo; el override por
entorno (`PUBLIC_HOSTNAME`, `EMAIL_HOST`) sigue mandando sobre el default en modo no interactivo;
`mx.caonao.cu` pasa su propio validador; dry-run completo sale 0 con ambos defaults.

## Ruta de ejecución: inline, no delegada

| Tarea | Ruta | Evidencia del trigger |
|---|---|---|
| T19, T20 | **inline** | Una sola edición por archivo, sin diseño pendiente: el valor correcto y la ubicación exacta ya están verificados con número de línea. |
| T21 | **inline** | Una línea. El cambio de `return 0` a `return 1` está determinado por los cuatro call sites ya leídos. |
| T22 | **inline** | Un archivo ya leído de punta a punta; el diseño (motor constante, puerto con default) estaba decidido por el usuario antes de abrir el archivo. |
| T23 | **inline** | Defectos deterministas con evidencia ya observada en la sesión: el error del operador se reprodujo y los tres call sites del archivo se leyeron antes de editar. Delegar exigiría transferir el hallazgo, no reducir contexto. |

Se ejecuta en el padre y no en un subagente, por dos razones concretas, no por preferencia:

1. Un worker arranca sin esta evidencia. El fallo #1 no era "cambiar la ruta de `pip`": era
   descubrir que el shim no existe. Un worker que rehaga la investigación puede volver a fijar
   `bin/pip` y reintroducir el bug sin enterarse de por qué se descartó.
2. El trabajo son cinco líneas en dos archivos ya leídos. Delegarlo agregaría transferencia de
   contexto y riesgo de handoff sin capacidad adicional.

## Revisión nativa: bloqueada por el proveedor, no por Gentle AI

Los cuatro actores (`review-risk`, `review-resilience`, `review-readability`, `review-reliability`)
fallaron en **dos rondas** con el mismo error del proveedor:

```
Error from provider (Console): OpenCode's free tier can only be used from within OpenCode
```

El lineage `review-bdbb39eaabc3cc82` sigue en `reviewing` con `action: collect`. No se capturó
ningún `reviewer_result`, no se quemó autoridad y no se tocó el árbol. **No es un defecto de
Gentle AI**: es el proveedor del modelo rechazando subagentes en este runtime, así que no
corresponde abrir reporte de defecto de producto.

Consecuencia práctica: la corrección nativa (`review.capture-correction-plan`, unificada sobre
los findings corroborados) **no está disponible**, porque solo se puede abrir desde una captura
de revisor y nunca hubo una. Los tres fixes se aplican por la vía normal y el receipt anterior
queda invalidado por el cambio de bytes, que es lo que corresponde.

`gentle-ai review abandon` exige `--maintainer-authorization`, o sea una decisión del
mantenedor: no se rellena desde el agente. Queda pendiente del usuario.

## Checks

T19-T21 no cambian Django, settings ni requirements. Evidencia observada:

| # | Verificación | Resultado |
|---|---|---|
| 1 | `bash -n deploy/deploy.sh` | OK |
| 2 | `bash -n deploy/install.sh` | OK |
| 3 | `manage.py check` | `no issues (0 silenced)` |
| 4 | `install.sh --help` sin TTY y sin root | `exit=0`, imprime uso |
| 5 | `install.sh --dry-run` sin TTY, sin `--non-interactive` | `exit=1` en el preflight, antes de cualquier cambio |
| 6 | `need_checkout` sin checkout / con checkout | `return 1` (salta) / `return 0` (ejecuta) |
| 7 | `PIP_CMD` default, override y override con espacios | `python -m pip` (3 args) / 1 arg / 1 arg con espacio preservado |
| 8 | `.venv/bin/pip` existe | **no existe**; `.venv/bin/python -m pip --version` → `pip 26.2.1` |
| 9 | `--configure` con `deploy.env` ausente | llega intacto a `configure_deploy_env` |
| 10 | `--check` con `deploy.env` ausente | **sigue fallando**, el guard no se relajó de más |

Check 8 es la prueba directa del T19: el shim que el código original invocaba no existe en este
repo, y el reemplazo responde. Check 10 evita que el arreglo del T20 abra un agujero: solo
`configure` salta el guard, `--check` y `deploy` lo siguen exigiendo.

**No ejecutado:** `shellcheck` no está instalado en esta máquina, así que el criterio de
"cero errores de shellcheck" queda pendiente, no aprobado. Tampoco hay servidor real: `nginx -t`,
`certbot`, `systemctl`, clone real, migración real, health check externo y rollback siguen sin
verificarse en ejecución.

## Progreso

- [x] T0 — Exploración: los tres scripts y el flujo de settings leídos
- [x] T1-T5 — Preliminares, clone, usuario, dominio, base de datos
- [x] T6-T9 — Correo, superusuario, resto del `.env`, generación
- [x] T10-T13 — Venv, migrate, systemd, las dos opciones de proxy
- [x] T14-T15 — `deploy.env` y andamiaje de deploy automático
- [x] T16-T17 — `deploy.sh`: health check parametrizable y `--configure`
- [x] T18 — README
- [x] T19 — `PIP` como `python -m pip`
- [x] T20 — `--configure` puede crear `deploy.env` en host limpio
- [x] T21 — `need_checkout` corta de verdad
- [x] T22 — PostgreSQL como constante, puerto con default 5432
- [x] T23 — Validadores de correo reparados (`valid_email`, `valid_smtp_host`, `valid_smtp_user`)
- [x] T24 — Defaults reales: `meteocamaguey.cu` y `mx.caonao.cu`

Los ocho bloques T1-T18 se marcan como entregados porque el commit `a9e01c6` los contiene y sus
checks pasaron. T19-T21 se marcan según su propia evidencia, registrada abajo.

## Decisiones pendientes que hay que escalar (no resolver a ciegas)

Ninguna bloqueante ahora. Si durante la implementación aparece que un campo del `.env` que el
operador decide no tiene contraparte en `config/settings/**`, se para la tarea y se reporta en vez
de agregar el setting.

## Próximo paso

T19-T21 aplicados y verificados (checks 1-10 de arriba). El commit de trabajo de estos tres fixes
va aparte del de la functionality original, para que el diff revisable sea el diff del bug.

Pendiente de decisión del usuario, no bloqueante para el código:

1. Autoridad del review congelado `review-bdbb39eaabc3cc82`. `gentle-ai review abandon` exige
   `--maintainer-authorization`, que es una decisión del mantenedor y no se rellena desde el
   agente. Hasta que se resuelva, el lineage sigue en `reviewing` y el receipt anterior está
   invalidado por el cambio de bytes.
2. `shellcheck`, si se quiere cerrar ese criterio de aceptación.
3. Validación en servidor real de los flujos que estos scripts ejecutan en producción.
