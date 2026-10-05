#!/usr/bin/env bash
# Despliegue de web-cmw-insmet-cu en el servidor de produccion.
#
# Se ejecuta EN el servidor, como root, y es la fuente unica de verdad del
# procedimiento. El workflow .github/workflows/deploy.yml lo invoca por SSH; el
# operador tambien puede correrlo a mano cuando Actions no llega o cuando hay que
# volver atras sin pasar por un PR.
#
#   sudo /usr/local/sbin/webcmp-deploy <commit-sha> [ref-de-respaldo]
#
# Que hace, en este orden (el orden ES la garantia):
#   1. lock, para que dos despliegues no se pisen
#   2. git checkout del SHA exacto
#   3. pip install requirements/prod.txt
#   4. gate 1: makemigrations --check (el modelo cambio y no hay migracion)
#   5. gate 2: check --deploy con la configuracion REAL de produccion
#   6. migrate  (antes de que el codigo nuevo atienda requests)
#   7. collectstatic (antes de que el codigo nuevo sirva HTML que los referencia)
#   8. restart de webcmp y webcmp-huey (reload NO sirve: ver nota de Gunicorn)
#   9. health check contra el Nginx local
#
# Si algo falla despues del punto 6, se revierte el codigo y se reinicia. La
# base de datos NO se revierte sola: Django no genera migraciones inversas y una
# operacion destructiva (DROP COLUMN) no tiene hacia atras. El script lo dice por
# pantalla y quien lee la salida sabe que tiene que mirar la base a mano.
#
# INSTALACION (una vez, y de ahi en adelante el archivo vive FUERA del checkout):
#   sudo install -o root -g root -m 0755 deploy/deploy.sh /usr/local/sbin/webcmp-deploy
#
# Fuera del checkout a proposito: este script corre como root y el checkout es
# escribible por el usuario de servicio. Si el script se ejecutara desde
# /srv/webcmp/deploy/deploy.sh con sudo, bastaria editar el archivo para obtener
# root: es una escalada de privilegios trivial. En /usr/local/sbin, propiedad de
# root, el dueño de la clave de despliegue no puede escribirlo.

set -Eeuo pipefail

readonly LOCKFILE=/var/lock/webcmp-deploy.lock
readonly CONFIG=/etc/webcmp/deploy.env

log() { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mAVISO:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# TODO git corre como DEPLOY_USER, nunca como root.
#
# El checkout es de webcmp y este script corre como root. Git >= 2.35.2 se niega a
# trabajar sobre un repo de otro usuario ("detected dubious ownership") por una
# buena razon: un repo escribible por otro usuario puede tener un .git/config que
# ejecute comandos. El sintoma es un "fatal: dubious ownership" en el primer
# `git rev-parse`, antes de tocar nada.
#
# Correr git con el dueno del checkout es lo que pedia el bug de entrada. La
# alternativa, agregar /srv/webcmp a safe.directory de root, teaches a root a
# confiar en un repo que webcmp controla: lo mismo que hace el check, pero
# permanente y global.
gitapp() {
    sudo -u "$DEPLOY_USER" git -C "$APP_DIR" "$@"
}

# --------------------------------------------------------------------------
# Configuracion
# --------------------------------------------------------------------------

[ -r "$CONFIG" ] || die "No existe $CONFIG (root, 600). Vease deploy/README-deploy.md."

# shellcheck disable=SC1090
source "$CONFIG"

: "${APP_DIR:=/srv/webcmp}"
: "${DEPLOY_USER:=webcmp}"
: "${GUNICORN_UNIT:=webcmp}"
: "${HUEY_UNIT:=webcmp-huey}"
: "${ENCRYPTION_ENV:=/etc/webcmp/encryption.env}"
: "${PYTHON:=$APP_DIR/.venv/bin/python}"
: "${PIP:=$APP_DIR/.venv/bin/pip}"
: "${PUBLIC_HOSTNAME:=web.cmw.insmet.cu}"
# Solo para servidores de prueba con certificado autofirmado. Vacio (lo normal) =
# el health check verifica el TLS de verdad. Ponerlo en produacion anula la
# unica comprobacion que detecta un certificado vencido o ajeno.
: "${HEALTHCHECK_INSECURE:=}"
# Cache de pip. Sin esto no hay ninguno: `webcmp` es una cuenta de sistema sin
# home, pip no encuentra donde escribir ~/.cache y avisa "the cache has been
# disabled". El efecto practico es que cada deploy re-descarga las ruedas desde
# PyPI, lo que multiplica el tiempo del deploy y convierte cada corte de red en un
# deploy fallido. Todas las versiones van pinadas con `==`, asi que un cache no
# puede servir un artefacto equivocado.
: "${PIP_CACHE_DIR:=/var/cache/webcmp-pip}"
# Cache de config de Matplotlib. Mismo motivo que el de pip: sin un directorio
# escribible, cada import regenera el indice de fuentes y escupe un WARNING que
# tapa el resto del log. Lo declara tambien webcmp.service.
: "${MPLCONFIGDIR:=$APP_DIR/.cache/matplotlib}"

readonly APP_DIR DEPLOY_USER GUNICORN_UNIT HUEY_UNIT ENCRYPTION_ENV PYTHON PIP
readonly PUBLIC_HOSTNAME HEALTHCHECK_INSECURE PIP_CACHE_DIR MPLCONFIGDIR

[ "$(id -u)" -eq 0 ] || die "Este script necesita root (systemctl, systemd-run, /etc/webcmp)."
[ -d "$APP_DIR/.git" ] || die "$APP_DIR no es un checkout de git."
[ -x "$PYTHON" ] || die "No existe el venv: $PYTHON"

# El cache es de DEPLOY_USER, no de root: si fuera de root, los artefactos
# cacheados serian ilegibles para el pip del deploy y el cache no serviria de
# nada, que es exactamente el problema que vino a resolver.
install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" -m 0700 "$PIP_CACHE_DIR"
export PIP_CACHE_DIR
install -d -o "$DEPLOY_USER" -g "$DEPLOY_USER" -m 0700 "$MPLCONFIGDIR"

target_sha=${1:-}
[ -n "$target_sha" ] || die "Uso: $0 <commit-sha> [ref-de-respaldo]"

# --------------------------------------------------------------------------
# Lock: dos pushes seguidos no pueden migrar a la vez
# --------------------------------------------------------------------------

exec 9>"$LOCKFILE"
flock -n 9 || die "Ya hay un despliegue en curso (lock $LOCKFILE). No se toca nada."

# --------------------------------------------------------------------------
# Estado previo, para el rollback
# --------------------------------------------------------------------------

previous_sha=$(gitapp rev-parse HEAD)
previous_sha=${2:-$previous_sha}
migrated=0
current_sha="$previous_sha"

# OJO: aca NO se hace `rev-parse --short "$target_sha"`. Ese comando solo resuelve
# objetos que ya estan en el repo local, y el `fetch` de mas abajo todavia no
# corrio: desplegar un commit recien pusheado fallaria con un "unknown revision"
# antes de haber tocado nada, con un error que no dice nada del deploy. Se loguea
# el SHA crudo y el corto se resuelve despues del checkout.
log "Deploy $target_sha sobre $(gitapp rev-parse --short "$previous_sha")"

# --------------------------------------------------------------------------
# Rollback
# --------------------------------------------------------------------------

rollback() {
    local status=$?
    trap - ERR

    if [ "$status" -eq 0 ] || [ "$current_sha" = "$previous_sha" ]; then
        exit "$status"
    fi

    warn "El despliegue fallo (status $status). Se revierte el codigo a $(gitapp rev-parse --short "$previous_sha")."
    warn "NO se tocan la base de datos ni los archivos de media/."

    if [ "$migrated" -eq 1 ]; then
        warn "Las migraciones YA se aplicaron. Django no genera rollback automatico:"
        warn "si una migracion fue destructiva, la base quedo con el esquema nuevo."
        warn "Revisala a mano antes de volver a exponer el sitio."
    fi

    gitapp fetch --quiet origin || true
    gitapp checkout --force --quiet "$previous_sha" || {
        warn "No se pudo volver al commit anterior. El servidor quedo en $current_sha."
        warn "Corrigilo a mano: sudo -u $DEPLOY_USER git -C $APP_DIR checkout $previous_sha && systemctl restart $GUNICORN_UNIT"
        exit 1
    }

    sudo -u "$DEPLOY_USER" "$PIP" install --quiet -r "$APP_DIR/requirements/prod.txt" || warn "Falló el pip install del rollback; se reinicia igual."

    manage collectstatic --no-input || warn "Falló collectstatic en el rollback."
    systemctl restart "$GUNICORN_UNIT" || warn "Falló el restart de $GUNICORN_UNIT."
    systemctl restart "$HUEY_UNIT" || warn "Falló el restart de $HUEY_UNIT."

    warn "Codigo revertido a $(gitapp rev-parse --short "$previous_sha"). El sitio vuelve al estado anterior."
    exit "$status"
}

# Corre `manage.py` en el MISMO contexto que corre Gunicorn.
#
# systemd-run --pipe --wait crea una unidad transitoria con el EnvironmentFile de
# la clave de descifrado y PRODUCTION=1, exactamente igual que webcmp.service. Sin
# esto, un `manage.py` corrido a mano sin PRODUCTION cae en el perfil de DESARROLLO
# (ver config/settings/__init__.py): migra contra sqlite3 y dice que todo bien,
# mientras el sitio sigue en PostgreSQL.
#
# --uid webcmp: los archivos los escribe el usuario de servicio, que es el dueno
# del venv, de media/ y de staticfiles/. Como root quedarian con dueno root y el
# servicio dejaria de poder escribir en ellos.
manage() {
    systemd-run --quiet --pipe --wait \
        --uid="$DEPLOY_USER" --gid="$DEPLOY_USER" \
        -p "EnvironmentFile=$ENCRYPTION_ENV" \
        -p Environment=PRODUCTION=1 \
        -p "Environment=MPLCONFIGDIR=$MPLCONFIGDIR" \
        --working-directory="$APP_DIR" \
        "$PYTHON" manage.py "$@"
}

trap rollback ERR

# --------------------------------------------------------------------------
# 1. Codigo
# --------------------------------------------------------------------------

if [ -n "$(gitapp status --porcelain --untracked-files=no)" ]; then
    die "El checkout tiene cambios versionados sin commitear. Se aborta para no perderlos:
  sudo -u $DEPLOY_USER git -C $APP_DIR status
  sudo -u $DEPLOY_USER git -C $APP_DIR diff

El \`sudo -u\` no es decorativo: el checkout es de $DEPLOY_USER y git se niega a
operar sobre un repo de otro usuario."
fi

gitapp fetch --quiet origin
gitapp checkout --force --quiet "$target_sha"
current_sha=$(gitapp rev-parse HEAD)

# 2. Dependencias
log "Instalando requirements/prod.txt"
sudo -u "$DEPLOY_USER" "$PIP" install --quiet --disable-pip-version-check -r "$APP_DIR/requirements/prod.txt"

# 3. Generar migraciones desde los modelos
#
# OJO con el flujo de este proyecto: NO versiona las migraciones. El .gitignore
# tiene `**/migrations/*` con la unica excepcion de `__init__.py`, asi que un
# clone limpio llega SIN migraciones y el esquema se deriva de los modelos.
#
# Por eso el gate que se suele poner aca, `makemigrations --check --dry-run`
# ("el modelo cambio y nadie escribio la migracion"), NO sirve: en un clone
# limpio falla siempre, porque las migracionestodavia no existen y `--check`
# interpreta "no hay migraciones para el modelo" como "falta la migracion".
# El CI no lo sufre porque su job corre `makemigrations` antes de `migrate`.
#
# Consecuencia que hay que tener presente: una migracion se genera y se aplica en
# el mismo deploy, sin revision. Si un cambio de modelo llega con un ALTER
# destructivo, se aplica contra produccion sin que nadie lo mire. Versionar las
# migraciones es la unica forma de que eso sea revisable; mientras no se haga, el
# deploy es el unico lugar donde el schema se decide.
log "Generando migraciones desde los modelos"
manage makemigrations

# 4. Gate: la configuracion REAL de produccion
#
# El CI corre este mismo check con valores de mentira (db que no existe, sin
# SMTP). Aca corre contra el .env de verdad: es la primera vez que se verifica
# que la SECRET_KEY se descifra, que DB_* apunta al PostgreSQL real y que
# EMAIL_BACKEND no es el de consola. Tarda segundos y evita un sitio caido.
log "Gate: check --deploy (configuracion real)"
manage check --deploy --fail-level WARNING

# 5. Migraciones: antes de que el codigo nuevo atienda un solo request
log "Aplicando migraciones"
manage migrate --noinput
migrated=1

# `--check` sale con codigo 1 si queda algo sin aplicar. Es la unica forma de
# confirmar que el esquema quedo donde tiene que estar y no "migrate no dijo
# nada", que es lo mismo que no haber corrido nada.
manage migrate --check

# 6. Estaticos: antes de que el codigo nuevo emita HTML que los referencia
log "Recolectando estaticos"
manage collectstatic --no-input

# 7. Reinicio
#
# `systemctl reload` (SIGHUP) NO alcanza para un despliegue: Gunicorn hace que el
# master recargue su configuracion y los workers se re-forkean desde el master.
# El master tiene el codigo viejo en memoria, asi que los workers nuevos tambien.
# El sitio serviria el template viejo con los estaticos nuevos.
log "Reiniciando $GUNICORN_UNIT y $HUEY_UNIT"
systemctl restart "$GUNICORN_UNIT"
systemctl restart "$HUEY_UNIT"

systemctl is-active --quiet "$GUNICORN_UNIT" || die "$GUNICORN_UNIT quedo inactivo."
systemctl is-active --quiet "$HUEY_UNIT" || die "$HUEY_UNIT quedo inactivo."

# 8. Health check
#
# Sale al puerto 443 de 127.0.0.1 con el SNI y el Host correctos, o sea que
# atraviesa Nginx, TLS y el socket de Gunicorn: prueba el camino completo, sin
# salir del servidor y sin depender de que DNS resuelva desde aca.
log "Health check"
code=$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
    --max-time 15 \
    ${HEALTHCHECK_INSECURE:+--insecure} \
    --resolve "$PUBLIC_HOSTNAME:443:127.0.0.1" \
    "https://$PUBLIC_HOSTNAME/" || echo 000)

case "$code" in
    2* | 3*) log "El sitio responde $code." ;;
    000)
        if [ -n "${HEALTHCHECK_INSECURE:-}" ]; then
            die "Sin respuesta aun con --insecure (ver journalctl -u $GUNICORN_UNIT)."
        fi
        die "Sin respuesta de https://$PUBLIC_HOSTNAME.
Si el servidor tiene un certificado autofirmado, poné
HEALTHCHECK_INSECURE=1 en /etc/webcmp/deploy.env para este servidor de prueba.
NUNCA en produccion: --insecure deja de detectar un certificado vencido o de otro
dominio, que es exactamente lo que el health check deberia estar mirando."
        ;;
    *) die "El sitio responde $code, se esperaba 2xx o 3xx." ;;
esac

trap - ERR

log "Desplegado $(gitapp rev-parse --short HEAD)."
printf '  Web:  https://%s\n' "$PUBLIC_HOSTNAME"
printf '  Logs: journalctl -u %s -f\n' "$GUNICORN_UNIT"
printf '  Huey: journalctl -u %s -f\n' "$HUEY_UNIT"
printf '  Volver atras: sudo %s %s\n' "$0" "$previous_sha"
