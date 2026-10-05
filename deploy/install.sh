#!/usr/bin/env bash
# Instalador del portal del CMP Camaguey. Auto-contenido: no lee NADA del
# checkout antes de clonarlo, asi que se puede ejecutar como archivo suelto.
#
#   curl -fsSL https://raw.githubusercontent.com/orl92/web-cmw-insmet-cu/main/deploy/install.sh \
#       | sudo bash -s -- --help
#
# Que instala, en este orden (el orden es una dependencia, no una preferencia):
#   1. prerrequisitos de sistema (apt) y version de Python
#   2. usuario de servicio webcmp + media/, logs/, staticfiles/, .cache/
#   3. clone del repo en APP_DIR, propiedad de webcmp
#   4. rol y base de datos, con las credenciales que se preguntaron
#   5. venv + requirements/prod.txt
#   6. .env con scripts/generate_env.py y los valores preguntados, sin CHANGE_ME
#   7. makemigrations, migrate, collectstatic, check --deploy
#   8. unidades systemd renderizadas a APP_DIR/SERVICE_USER reales
#   9. proxy: (A) Nginx local con TLS, o (B) reverse proxy externo
#  10. /etc/webcmp/deploy.env con el destino del health check que corresponde
#  11. andamiaje de deploy automatico (usuario, keypair, sudoers, webcmp-deploy)
#  12. superusuario, por systemd-run con la ENCRYPTION_KEY
#
# AUTO-CONTENIDO, y por que importa: este archivo se ejecuta por un pipe, sin
# checkout delante. Todo lo que necesita saber esta escrito aca o se pregunta.
# La version anterior leia deploy/deploy.sh, deploy/deploy.env.example y
# deploy/sudoers/webcmp-deploy de un repo que todavia no existia en el servidor,
# y por eso no podia correr de esta forma.
#
# IDEMPOTENCIA. Correrlo dos veces no cambia nada y no rompe lo ya armado:
#   - NO regenera SECRET_KEY ni ENCRYPTION_KEY: se conservan si el par descifra
#     (es lo que ya hace scripts/generate_env.py, y por que importa: regenerar
#     la SECRET_KEY invalida todas las sesiones y cookies firmadas del sitio)
#   - NO tira la base: el rol se altera, la base se crea solo si no existe
#   - NO pisa un .env ni un /etc/webcmp/deploy.env sin confirmacion
#   - cada pregunta muestra como default el valor que ya esta en vigor
# Un paso que regenera un secreto o pisa una config editada a mano convierte un
# reintento en un incidente.
#
# FALLA CERRADO. Sin terminal y sin --non-interactive, aborta ANTES de tocar
# nada: un instalador que adivina en un pipe escribe el .env equivocado y nadie
# lo ve hasta que el sitio responde con la base equivocada. Con
# --non-interactive todas las respuestas salen de variables de entorno o de los
# defaults, y el resumen final dice de donde salio cada una.
#
# --dry-run imprime el plan completo y no ejecuta nada. Los pasos nuevos lo
# respetan: las preguntas no se hacen y su respuesta se imprime como
# "[dry-run] CLAVE=valor", con los secretos enmascarados.

set -Eeuo pipefail

# --------------------------------------------------------------------------
# Defaults. Todos overridables por variable de entorno, para no tener que
# editar el script en un servidor con otro layout.
# --------------------------------------------------------------------------
#
# El repo se clona con `git clone` (no con curl|tar) porque el deploy depende de
# un checkout real: deploy.sh hace `git fetch`/`checkout` en produccion y
# aborta si el directorio no es un repo.
REPO_URL=${REPO_URL:-https://github.com/orl92/web-cmw-insmet-cu.git}
REPO_REF=${REPO_REF:-main}
APP_DIR=${APP_DIR:-/srv/webcmp}
SERVICE_USER=${SERVICE_USER:-webcmp}
SERVICE_GROUP=${SERVICE_GROUP:-$SERVICE_USER}
SERVICE_SHELL=${SERVICE_SHELL:-/usr/sbin/nologin}
DEPLOY_LOGIN_USER=${DEPLOY_LOGIN_USER:-deploy}
SCRIPT_PATH=${SCRIPT_PATH:-/usr/local/sbin/webcmp-deploy}
CONFIG_DIR=${CONFIG_DIR:-/etc/webcmp}
CONFIG_FILE=${CONFIG_FILE:-$CONFIG_DIR/deploy.env}
ENCRYPTION_ENV=${ENCRYPTION_ENV:-$CONFIG_DIR/encryption.env}
PIP_CACHE_DIR=${PIP_CACHE_DIR:-/var/cache/webcmp-pip}
MPLCONFIGDIR=${MPLCONFIGDIR:-$APP_DIR/.cache/matplotlib}
VENV_DIR=${VENV_DIR:-$APP_DIR/.venv}
DEPLOY_SSH_KEY=${DEPLOY_SSH_KEY:-$CONFIG_DIR/deploy_key}
DEPLOY_SUDOERS=${DEPLOY_SUDOERS:-/etc/sudoers.d/webcmp-deploy}
NGINX_AVAILABLE=${NGINX_AVAILABLE:-/etc/nginx/sites-available/webcmp.conf}
NGINX_ENABLED=${NGINX_ENABLED:-/etc/nginx/sites-enabled/webcmp.conf}
NGINX_DEFAULT_SITE=${NGINX_DEFAULT_SITE:-/etc/nginx/sites-enabled/default}
NGINX_ERROR_ROOT=${NGINX_ERROR_ROOT:-/var/www/webcmp-errors}
ACME_ROOT=${ACME_ROOT:-/var/www/letsencrypt}
TLS_DIR=${TLS_DIR:-$CONFIG_DIR/tls}
# El vhost NUNCA se copia tal cual: se renderiza desde el ejemplo del checkout
# (ver render_vhost). La ruta se declara aca para que quien lea el bloque de
# activacion vea de donde sale el archivo.
vhost_src=$APP_DIR/deploy/nginx/webcmp.conf.example
# El socket de Gunicorn sale de RuntimeDirectory=webcmp en el unit, o sea
# /run/<GUNICORN_UNIT>/gunicorn.sock. Los tres tienen que decir lo mismo: el
# vhost de Nginx, el health check de deploy.sh y el unit.
GUNICORN_UNIT=${GUNICORN_UNIT:-webcmp}
HUEY_UNIT=${HUEY_UNIT:-webcmp-huey}
GUNICORN_SOCKET=${GUNICORN_SOCKET:-/run/$GUNICORN_UNIT/gunicorn.sock}

# scripts/generate_env.py usa PEP 758 (except sin parentesis, `except A, B:`),
# que existe SOLO desde Python 3.14. Con 3.12 o 3.13 el generador no compila y
# falla con un SyntaxError que no menciona la version: el error dice
# "multiple exception types must be parenthesized" y no dice "instala Python
# 3.14". Se chequea aca, en el arranque, con el mensaje que si lo dice.
MIN_PYTHON=(3 14)

DRY_RUN=0
INTERACTIVE=1
HELP=0
ALLOW_INCOMPLETE_ENV=0
SKIP_DEPLOY_SCAFFOLD=0
HAVE_CHECKOUT=0
CHANGED=0
ANSWER_SOURCES=()

log()  { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mAVISO:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# --------------------------------------------------------------------------
# Wrappers de ejecucion
# --------------------------------------------------------------------------

# Todo lo que muta el sistema pasa por aca. En --dry-run se imprime en vez de
# ejecutarse, que es lo unico que hace util el modo: un dry-run que solo muestra
# texto fijo no se puede comparar contra el estado real del servidor.
run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  [dry-run] %s\n' "$*"
    else
        "$@"
        CHANGED=1
    fi
}

# Para los comandos que son shell puro (redirecciones, &&), que `run` no cubre.
run_sh() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  [dry-run] %s\n' "$1"
    else
        eval "$1"
        CHANGED=1
    fi
}

# install, pero solo si el destino no es ya identico.
#
# No es purismo. Tocar /etc/sudoers.d/webcmp-deploy obliga a sudo a releer el
# archivo en cada invocacion, y reescribir /usr/local/sbin/webcmp-deploy le
# cambia el mtime a un archivo que puede estar corriendo. Y sobre todo: un resumen
# que dice "cambio algo" cuando no cambio nada hace que la idempotencia sea una
# promesa que nadie puede verificar desde la salida.
install_if_changed() {
    local src=$1 dest=$2 mode=$3 owner=${4:-root} group=${5:-root}
    # `10#` quita los ceros de la izquierda. Sin esto la comparacion NUNCA puede
    # ser cierta: el script pide `0755` y `stat -c %a` devuelve `755`, asi que
    # "root:root 0755" != "root:root 755" y el script reescribe los archivos
    # identicos en cada corrida, que es justo lo que este helper evita.
    if [ -f "$dest" ] && cmp -s "$src" "$dest" \
        && [ "$(stat -c '%U:%G %a' "$dest")" = "$owner:$group $((10#$mode))" ]
    then
        printf '  %s ya esta al dia (%s:%s %s)\n' "$dest" "$owner" "$group" "$((10#$mode))"
        return 0
    fi
    run install -o "$owner" -g "$group" -m "$mode" "$src" "$dest"
}

# Como el de arriba, pero para directorios. Existe aparte y no reusa
# install_if_changed porque ese compara contenido, que un directorio no tiene.
ensure_dir() {
    local dir=$1 mode=$2 owner=$3 group=$4
    if [ -d "$dir" ] && [ "$(stat -c '%U:%G %a' "$dir")" = "$owner:$group $((10#$mode))" ]
    then
        printf '  %s ya esta al dia (%s:%s %s)\n' "$dir" "$owner" "$group" "$((10#$mode))"
        return 0
    fi
    run install -d -o "$owner" -g "$group" -m "$mode" "$dir"
}

usage() {
    cat <<'EOF'
Instalador de web-cmw-insmet-cu. Un solo archivo, sin checkout previo:

  curl -fsSL https://raw.githubusercontent.com/orl92/web-cmw-insmet-cu/main/deploy/install.sh \
      | sudo bash -s -- --help

Uso:
  sudo bash install.sh [opciones]
  curl -fsSL <raw-url>/deploy/install.sh | sudo bash -s -- [opciones]

Opciones:
  --non-interactive   No preguntar nada: cada valor sale de la variable de
                      entorno del mismo nombre o del default. Sin terminal esto
                      es obligatorio.
  --allow-incomplete-env
                      Dejar los CHANGE_ME que sobren en el .env (por ejemplo si
                      el SMTP todavia no existe). NO migra, NO crea el
                      superusuario y NO arranca los servicios: avisa de que el
                      sitio queda sin levantar.
  --skip-deploy-scaffold
                      No instalar el usuario de despliegue, su keypair ni el
                      sudoers: para un servidor donde el deploy va a correr a mano.
  --dry-run, -n      Imprimir el plan y no ejecutar nada.
  --help, -h         Esto. Sale 0 sin exigir root ni TTY y sin tocar nada.

Variables de entorno que se respetan (las preguntas usan el mismo nombre):
  REPO_URL, REPO_REF, APP_DIR, SERVICE_USER, DEPLOY_LOGIN_USER, SCRIPT_PATH,
  CONFIG_DIR, CONFIG_FILE, ENCRYPTION_ENV, DB_ENGINE, DB_NAME, DB_USER,
  DB_PASS, DB_HOST, DB_PORT, DB_SSL_MODE, EMAIL_HOST, EMAIL_PORT,
  EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL, PUBLIC_HOSTNAME,
  REDIS_URL, USE_REDIS_CACHE, LOG_LEVEL, SUPERUSER_USERNAME, SUPERUSER_EMAIL,
  SUPERUSER_PASSWORD.

Que NO hace: no administra el deploy. Para desplegar un commit:
  sudo $SCRIPT_PATH <commit-sha>
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run|-n)           DRY_RUN=1 ;;
        --non-interactive)      INTERACTIVE=0 ;;
        --allow-incomplete-env) ALLOW_INCOMPLETE_ENV=1 ;;
        --skip-deploy-scaffold) SKIP_DEPLOY_SCAFFOLD=1 ;;
        -h|--help)              HELP=1 ;;
        *) die "Opcion desconocida: $1 (--help para el uso)." ;;
    esac
    shift
done

# La ayuda sale 0 sin exigir root ni TTY y ANTES del preflight: es el contrato de
# `curl ... | sudo bash -s -- --help` que promete el README, y el unico comando
# que un operador puede correr sin consecuencias sobre un servidor real.
if [ "$HELP" -eq 1 ]; then
    usage
    exit 0
fi

# --------------------------------------------------------------------------
# Preguntas
# --------------------------------------------------------------------------
#
# Reglas, iguales a las de deploy.sh:
#   - vacio = conservar el default, y el default es SIEMPRE el valor vigente
#   - la validacion es una funcion aparte, para que el error sea del campo
#   - reintentos acotados y despues die: un bucle de repregunta infinito en un
#     instalador colgado deja al operador sin salida y sin saber por que
#
# `ask` y `ask_secret` devuelven el valor por stdout y escriben TODO lo demas en
# stderr. No es una mania de stdout: el llamador hace `X=$(ask ...)`, asi que
# cualquier texto por stdout que no sea la respuesta terminaria DENTRO del valor.
MAX_PROMPT_TRIES=3

# Un nombre de dominio o un ALLOWED_HOSTS con espacios, dos puntos, barras o
# comillas rompe el vhost de Nginx, el `source` de deploy.env y el
# `ALLOWED_HOSTS` de Django. Se acota aca, una vez.
valid_hostname() {
    [ -n "$1" ] || return 1
    case "$1" in
        *[!a-zA-Z0-9.-]*) return 1 ;;
        -* | .* | *..*) return 1 ;;
    esac
    printf '%s' "$1" | grep -Eq '^[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?$'
}

valid_email() {
    [ -n "$1" ] || return 1
    case "$1" in
        *[!a-zA-Z0-9._%+-]*) return 1 ;;
    esac
    printf '%s' "$1" | grep -Eq '^[^@ ]+@[^@ ]+\.[^@ ]+$'
}

valid_port() {
    printf '%s' "$1" | grep -Eq '^[0-9]{1,5}$' && [ "$1" -ge 1 ] && [ "$1" -le 65535 ]
}

valid_db_name() {
    [ -n "$1" ] || return 1
    case "$1" in
        -*) return 1 ;;
    esac
    printf '%s' "$1" | grep -Eq '^[a-zA-Z_][a-zA-Z0-9_$-]*$'
}

valid_db_user() {
    valid_db_name "$1"
}

valid_host() {
    [ -n "$1" ] || return 1
    case "$1" in
        *[!a-zA-Z0-9.:_-]*) return 1 ;;
    esac
    return 0
}

# db: nombre de usuario de la app. No el de root ni el de postgres: es el rol
# que Django usa para conectarse.
valid_app_user() {
    [ -n "$1" ] || return 1
    case "$1" in
        *[!a-zA-Z0-9._-]*) return 1 ;;
        -*) return 1 ;;
    esac
    return 0
}

valid_abs_path() {
    [ -n "$1" ] || return 1
    case "$1" in
        /*) ;;
        *) return 1 ;;
    esac
    case "$1" in
        *[[:space:]]* | *'"'* | *"'"* | *'$'* | *'`'*) return 1 ;;
    esac
    return 0
}

valid_choice() {
    # valid_choice <permitidos separados por espacio> <valor>
    case " $1 " in
        *" $2 "*) return 0 ;;
    esac
    return 1
}

# Los tres motores que get_database_config() sabe construir. La lista no es
# arbitraria: son exactamente los tres `elif` de config/settings/base.py, y un
# motor distinto termina en `django.db.backends.<engine>` inexistente.
valid_db_engine() {
    valid_choice 'postgresql mysql sqlite3' "$1"
}

# El generador escribe DEBUG|INFO|WARNING|ERROR|CRITICAL y Django no valida este
# valor: uno mal escrito no da error, solo desactiva el logging en un nivel y deja
# el deploy sin dejar rastro. Un enum explicito lo corta aca.
valid_log_level() {
    valid_choice 'DEBUG INFO WARNING ERROR CRITICAL' "$1"
}

# Enmascara un valor si la clave parece un secreto. El resumen final reimprime
# todas las respuestas, asi que una contrasena que llegue ahi queda en el
# scrollback del terminal y en el log de la sesion.
mask() {
    case "$1" in
        *PASS* | *SECRET* | *ENCRYPTION_KEY*) printf '<oculto>' ;;
        *) printf '%s' "$2" ;;
    esac
}

# Genera un secreto de 32 caracteres alfanumericos.
#
# Alfanumerico y nada mas, a proposito: estas cadenas van a un `CREATE ROLE`, a un
# `EMAIL_HOST_PASSWORD` y a un `--resolve` que se imprime en pantalla. Un alfabeto
# mas rico (comillas, $, espacios) obliga a que cada consumidor tenga su
# propio escapado, y el que se olvide de uno rompe la instalacion con un error
# que no menciona el caracter problematico. 32 caracteres alfanumericos son
# ~190 bits: por encima de lo que se puede forzar.
gen_secret() {
    LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom 2>/dev/null | head -c 32
    printf ''
}

print_once_secret() {
    # Imprime un secreto recien generado, UNA vez, con el aviso de guardarlo.
    # Un segundo aviso (por ejemplo en el resumen) lo convertiria en un secreto
    # impreso dos veces, que es la mitad de razon por la que se imprime.
    #
    # El tercer argumento NO es siempre el mismo texto: la clave de descifrado se
    # regenera con --rotate-keys y destruye las sesiones, y una contrasena de
    # base o de superusuario se cambia en el .env y nada mas. Decirle a un
    # operador que rotate-keys "restaura" una contrasena de PostgreSQL lo manda a
    # romper la SECRET_KEY por una perdida que no era la que tuvo.
    cat >&2 <<EOF

  ============================================================
  GUARDA ESTE VALOR AHORA. No se vuelve a mostrar:

      $1 = $2

EOF
    printf '  ' >&2
    "$3" >&2
    cat >&2 <<EOF
  ============================================================
EOF
}

# Textos de recuperacion de print_once_secret. Son functions y no texto plano
# porque cada secreto tiene un procedimiento distinto, y confundirlos es el error
# caro: --rotate-keys no restaura una contrasena de base de datos.
recover_django_keys() {
    printf 'Queda cifrada en %s, con la ENCRYPTION_KEY de %s.\n' "$ENV_FILE" "$ENCRYPTION_ENV"
    printf 'Se recupera con `python scripts/generate_env.py --production --rotate-keys`,\n'
    printf 'que regenera el par: eso invalida TODAS las sesiones y cookies firmadas.\n'
}

recover_env_password() {
    printf 'Queda escrita en %s. Para cambiarla se edita esa clave y se reinicia %s.\n' \
        "$ENV_FILE" "$GUNICORN_UNIT"
}

# ¿Esta corrida tiene que preguntar? En dry-run no: preguntar por valores que
# despues no se usan solo le roba tiempo al operador. En --non-interactive
# tampoco: responder por stdin sin tener terminal es un deadlock.
can_prompt() {
    [ "$INTERACTIVE" -eq 1 ] && [ "$DRY_RUN" -eq 0 ]
}

# ask <CLAVE> <default> <pregunta> [validador]
ask() {
    local key=$1 default=$2 question=$3 validator=${4:-}
    local answer='' tries=0 source=default
    if ! can_prompt; then
        if [ -n "${!key:-}" ] && [ "${!key}" != "$default" ]; then
            answer=${!key}
            source=entorno
        else
            answer=$default
        fi
        printf '  [dry-run] %s=%s (%s)\n' "$key" "$(mask "$key" "$answer")" \
            "$([ "$DRY_RUN" -eq 1 ] && echo dry-run || echo no-interactivo)" >&2
        printf '%s' "$answer"
        return 0
    fi
    while :; do
        printf '%s [%s]: ' "$question" "$default" >&2
        IFS= read -r answer || die "EOF leyendo la respuesta de $key."
        answer=${answer:-$default}
        # Vacio con default vacio es una respuesta valida y EXPLICITA: "esto todavia
        # no existe" (el SMTP que aun no hay, el correo de un registro opcional).
        # Sin esta excepcion el validador rechaza el vacio, el operador reintenta
        # tres veces y el instalador muere en el campo que justamente era opcional.
        if { [ -z "$answer" ] && [ -z "$default" ]; } \
            || [ -z "$validator" ] || "$validator" "$answer" >/dev/null 2>&1
        then
            source=pregunta
            printf '%s' "$answer"
            ANSWER_SOURCES+=("$key=$source")
            return 0
        fi
        tries=$((tries + 1))
        printf '  Valor invalido para %s.\n' "$key" >&2
        if [ "$tries" -ge "$MAX_PROMPT_TRIES" ]; then
            printf '  %s intentos agotados.\n' "$MAX_PROMPT_TRIES" >&2
            return 1
        fi
        printf '  Reintentos restantes: %s\n' "$((MAX_PROMPT_TRIES - tries))" >&2
    done
}

# ask_secret <CLAVE> <default> <pregunta> [validador]
#
# `read -s`: una contrasena tipeada en un servidor sale en el scrollback del
# terminal y en cualquier grabacion de sesion. Si se deja vacio se genera una y
# se imprime UNA vez. En una corrida no interactiva NO se imprime: el valor
# podria estar yendo a un log de CI, y un secreto en un log ya no es un secreto.
ask_secret() {
    local key=$1 default=$2 question=$3 validator=${4:-}
    local answer='' tries=0
    if ! can_prompt; then
        if [ -n "${!key:-}" ]; then
            answer=${!key}
        elif [ -n "$default" ]; then
            answer=$default
        else
            answer=$(gen_secret)
            printf '  [dry-run] %s=<generada, escrita en el .env, no impresa>\n' "$key" >&2
            printf '%s' "$answer"
            return 0
        fi
        printf '  [dry-run] %s=<oculto> (%s)\n' "$key" \
            "$([ "$DRY_RUN" -eq 1 ] && echo dry-run || echo no-interactivo)" >&2
        printf '%s' "$answer"
        return 0
    fi
    while :; do
        if [ -n "$default" ]; then
            printf '%s (Enter = se conserva la actual): ' "$question" >&2
        else
            printf '%s (Enter = generar una): ' "$question" >&2
        fi
        IFS= read -r -s answer || die "EOF leyendo $key."
        printf '\n' >&2
        answer=${answer:-$default}
        if [ -z "$answer" ]; then
            answer=$(gen_secret)
            printf '%s' "$answer"
            ANSWER_SOURCES+=("$key=generada")
            return 0
        fi
        if [ -z "$validator" ] || "$validator" "$answer" >/dev/null 2>&1; then
            printf '%s' "$answer"
            ANSWER_SOURCES+=("$key=pregunta")
            return 0
        fi
        tries=$((tries + 1))
        printf '  Valor invalido para %s.\n' "$key" >&2
        if [ "$tries" -ge "$MAX_PROMPT_TRIES" ]; then
            printf '  %s intentos agotados.\n' "$MAX_PROMPT_TRIES" >&2
            return 1
        fi
        printf '  Reintentos restantes: %s\n' "$((MAX_PROMPT_TRIES - tries))" >&2
    done
}

# ask_optional_secret <CLAVE> <default> <pregunta>
#
# Igual que ask_secret, salvo que el vacio es una respuesta valida: no genera
# nada. Existe para los secretos que son opcionales de verdad (el SMTP que todavia
# no hay, el bind de LDAP si el servidor no tiene password). Contrasena de la base
# y del superusuario NO usan esta: ahi el vacio significa generar.
ask_optional_secret() {
    local key=$1 default=$2 question=$3
    local answer=''
    if ! can_prompt; then
        if [ -n "${!key:-}" ]; then
            answer=${!key}
        else
            answer=$default
        fi
        printf '  [dry-run] %s=%s (%s)\n' "$key" \
            "$([ -n "$answer" ] && mask "$key" "$answer" || printf '<vacio>')" \
            "$([ "$DRY_RUN" -eq 1 ] && echo dry-run || echo no-interactivo)" >&2
        printf '%s' "$answer"
        return 0
    fi
    printf '%s (Enter = dejarlo vacio): ' "$question" >&2
    IFS= read -r -s answer || die "EOF leyendo $key."
    printf '\n' >&2
    printf '%s' "${answer:-$default}"
    ANSWER_SOURCES+=("$key=pregunta")
    return 0
}

# ask_yes_no <default si|no> <pregunta>
#
# Devuelve 0 por si. Acepta s/si/yes/y y n/no, en mayusculas y minusculas.
# Un bucle de repregunta infinito en un instalador colgado deja al operador sin
    # salida y sin saber por que, asi que los tres reintentos estan contados.
# Y con una respuesta que no sea si/no NO se asume el default: "se asume si" por
    # culpa de una tecla mal apretada es como se instala lo que no se queria.
ask_yes_no() {
    local default=$1 question=$2 answer='' other tries=0
    other=$([ "$default" = si ] && echo no || echo si)
    if ! can_prompt; then
        printf '  [dry-run] (si=%s, no=%s) %s -> %s\n' "$default" "$other" "$question" "$default" >&2
        [ "$default" = si ]
        return
    fi
    while :; do
        printf '%s [%s/%s] (vacio = %s): ' "$question" "$default" "$other" "$default" >&2
        IFS= read -r answer || die "EOF leyendo la respuesta."
        answer=${answer:-$default}
        case "$answer" in
            s | S | si | SI | yes | y | Y)
                ANSWER_SOURCES+=("($1)=si")
                return 0 ;;
            n | N | no | NO)
                ANSWER_SOURCES+=("($1)=no")
                return 1 ;;
        esac
        tries=$((tries + 1))
        printf '  Se entiende si/no. Reintenta.\n' >&2
        if [ "$tries" -ge "$MAX_PROMPT_TRIES" ]; then
            printf '  %s intentos agotados.\n' "$MAX_PROMPT_TRIES" >&2
            return 1
        fi
    done
}

# ask_one_of <CLAVE> <default> <pregunta> <opcion1> <opcion2> ...
# Devuelve el valor literal de la opcion elegida. Se usa donde la respuesta es
# una palabra y el numero es incomodo de recordar despues (que elijiste, 1 o 2).
ask_one_of() {
    local key=$1 default=$2 question=$3
    shift 3
    local index=0 option answer tries=0 shift_count=0
    for option in "$@"; do
        index=$((index + 1))
        printf '    %s) %s\n' "$index" "$option" >&2
    done
    local prompt="$question"
    if ! can_prompt; then
        printf '  [dry-run] %s=%s\n' "$key" "$(mask "$key" "$default")" >&2
        printf '%s' "$default"
        return 0
    fi
    while :; do
        printf '%s [%s]: ' "$prompt" "$default" >&2
        IFS= read -r answer || die "EOF leyendo la respuesta de $key."
        answer=${answer:-$default}
        if [ "$answer" = "$default" ]; then
            printf '%s' "$answer"
            ANSWER_SOURCES+=("$key=$default")
            return 0
        fi
        if printf '%s' "$answer" | grep -Eq '^[0-9]+$'; then
            index=$answer
            shift_count=0
            for option in "$@"; do
                shift_count=$((shift_count + 1))
                if [ "$shift_count" -eq "$index" ]; then
                    printf '%s' "$option"
                    ANSWER_SOURCES+=("$key=$option")
                    return 0
                fi
            done
        fi
        # No se repregunta para siempre: un bucle infinito de repregunta deja al
        # operador sin salida y sin saber por que.
        tries=$((tries + 1))
        printf '  Opcion invalida para %s (numero del 1 al %s, o el texto exacto).\n' \
            "$key" "$(($# + 0))" >&2
        if [ "$tries" -ge "$MAX_PROMPT_TRIES" ]; then
            printf '  %s intentos agotados.\n' "$MAX_PROMPT_TRIES" >&2
            return 1
        fi
    done
}

# --------------------------------------------------------------------------
# Utilidades de archivos
# --------------------------------------------------------------------------

# env_set <archivo> <CLAVE> <valor>
#
# Reemplaza la linea KEY=... o la agrega al final. El valor viaja por el ENTORNO
# y no por `-v` de awk a proposito: awk procesa escapes en el valor de `-v`, asi
# que una contrasena con `\n` o `\1` llegaria al archivo como dos caracteres. Por
# ENVIRON el valor sale literal, que es lo unico aceptable en un archivo con
# contrasenas.
env_set() {
    local file=$1 key=$2 value=$3 tmp
    [ -f "$file" ] || : > "$file"
    tmp=$(mktemp)
    EV_KEY=$key EV_VALUE=$value awk '
        BEGIN { key = ENVIRON["EV_KEY"]; value = ENVIRON["EV_VALUE"]; seen = 0 }
        index($0, key "=") == 1 { print key "=" value; seen = 1; next }
        { print }
        END { if (!seen) print key "=" value }
    ' "$file" > "$tmp" || { rm -f "$tmp"; return 1; }
    cat "$tmp" > "$file"
    rm -f "$tmp"
}

# env_get <archivo> <CLAVE>  -> valor, o vacio
env_get() {
    [ -f "$1" ] || return 0
    awk -v k="$2" 'index($0, k "=") == 1 { sub("^" k "=", ""); print; exit }' "$1"
}

# sql_quote <valor>  -> literal SQL con comillas simples
#
# Para MySQL/PostgreSQL. El escapado es la unica defensa contra una contrasena con
# comilla: sin esto, una contrasena con `'` cierra el literal y el resto se
# ejecuta. Los rollbacks de SQL por construccion, no por confianza.
sql_quote() {
    local v=$1
    v=${v//\'/\'\'}
    printf "'%s'" "$v"
}

# psql_quote <valor> -> argumento de \set de psql entre comillas simples
#
# Distinto de sql_quote porque va por el lexer de psql, no por SQL. Ahi el
# escapado es con barra invertida, no con comilla duplicada.
psql_quote() {
    local v=$1
    v=${v//\\/\\\\}
    v=${v//\'/\\\'}
    printf "'%s'" "$v"
}

# render_template <origen> <destino> <viejo><><nuevo> [<viejo><><nuevo> ...]
#
# Sustitucion LITERAL, no de expresion regular. No es purismo: `gsub` de awk
# trata el patron como regex, y el par de reemplazos mas importante aca es
# `webcmp` -> `<SERVICE_USER>`. Como regex, `webcmp` tambien matchea
# `webcmp-huey` y el nombre del zone de cache de Nginx, y el vhost renderizado
# apuntaria a un socket que no existe. Ademas los pares llegan por el entorno
# (ENVIRON) y no por `-v`, por el mismo motivo que env_set.
#
# El separador del par es `<>` y NO `=` a proposito: varios de los pares que este
# script necesita tienen un `=` adentro, tanto del lado viejo como del nuevo
# (`User=webcmp` -> `User=webcmp-app`, `deploy ALL=(root)` -> `ci-deploy
# ALL=(root)`). Con `viejo=nuevo`, el shell parte por el PRIMER `=`, que en esos
# casos esta en el medio de la clave, y el resultado no es un error visible sino
# un archivo generado con basura que pasa `bash -n` y revienta en el servidor.
render_template() {
    local src=$1 dest=$2
    shift 2
    local old_list='' new_list='' count=0 pair
    for pair in "$@"; do
        old_list+="${pair%%<>*}"$'\x1f'
        new_list+="${pair#*<>}"$'\x1f'
        count=$((count + 1))
    done
    RT_COUNT=$count RT_OLD_LIST="$old_list" RT_NEW_LIST="$new_list" awk '
        function litrep(s, old, new,   out, p) {
            if (old == "") return s
            out = ""
            while ((p = index(s, old)) > 0) {
                out = out substr(s, 1, p - 1) new
                s = substr(s, p + length(old))
            }
            return out s
        }
        BEGIN {
            n = ENVIRON["RT_COUNT"]
            split(ENVIRON["RT_OLD_LIST"], O, "\037")
            split(ENVIRON["RT_NEW_LIST"], W, "\037")
        }
        { line = $0; for (i = 1; i <= n; i++) line = litrep(line, O[i], W[i]); print line }
    ' "$src" > "$dest"
}

# manage <manage.py args...>
#
# Corre manage.py en el MISMO contexto que corre Gunicorn: una unidad transitoria
# con el EnvironmentFile de la clave de descifrado y PRODUCTION=1, exactamente
# como webcmp.service.
#
# Por que systemd-run y no un shell normal: `manage.py` necesita leer la
# ENCRYPTION_KEY de $ENCRYPTION_ENV (600, root) y correr como SERVICE_USER, que
# no puede leerla. systemd resuelve las dos cosas: lee el EnvironmentFile como
# root antes de hacer el drop de privilegios.
#
# Por que NO un `sudo -u webcmp manage.py`: sin PRODUCTION cae al perfil de
# desarrollo (config/settings/__init__.py elige perfil por variable de entorno),
# migra contra sqlite3 y dice que todo bien mientras el sitio va a PostgreSQL. Es
# el modo de fallo mas caro de este proyecto: el instalador "pasa" y deja la base
# equivocada.
#
# OJO: systemd-run NO hereda el entorno de quien llama. Por eso las variables
# extra van con -p Environment=NOMBRE=valor y nunca con un `VAR=x systemd-run`.
manage() {
    if [ "$DRY_RUN" -eq 1 ]; then
        # Se imprime la invocacion COMPLETA y no un "manage.py makemigrations"
        # de adorno: lo que hay que poder comparar contra el estado real del
        # servidor es si PRODUCTION=1 y el EnvironmentFile van a ir o no.
        printf '  [dry-run] systemd-run --quiet --pipe --wait --uid=%s --gid=%s \\\n' \
            "$SERVICE_USER" "$SERVICE_GROUP"
        printf '    -p EnvironmentFile=%s -p Environment=PRODUCTION=1 \\\n' "$ENCRYPTION_ENV"
        printf '    -p Environment=MPLCONFIGDIR=%s --working-directory=%s \\\n' \
            "$MPLCONFIGDIR" "$APP_DIR"
        printf '    %s manage.py' "$VENV_DIR/bin/python"
        printf ' %s\n' "$*"
        return 0
    fi
    systemd-run --quiet --pipe --wait \
        --uid="$SERVICE_USER" --gid="$SERVICE_USER" \
        -p "EnvironmentFile=$ENCRYPTION_ENV" \
        -p Environment=PRODUCTION=1 \
        -p "Environment=MPLCONFIGDIR=$MPLCONFIGDIR" \
        --working-directory="$APP_DIR" \
        "$VENV_DIR/bin/python" manage.py "$@"
}

# ¿Hay systemd para systemd-run? Sin esto, manage() no puede correr y no hay
# reemplazo honesto: el unico fallback seria el perfil de desarrollo.
require_systemd() {
    command -v systemd-run >/dev/null 2>&1 \
        || die "systemd-run no esta instalado. Sin el no se puede correr manage.py con PRODUCTION=1 y la ENCRYPTION_KEY, y el instalador no arranca el sitio en el perfil equivocado."
    [ -d /run/systemd/system ] \
        || die "systemd no esta corriendo (falta /run/systemd/system). Este instalador no funciona en un contenedor sin systemd: manage.py caeria al perfil de desarrollo y migraria la base equivocada."
}

# ==========================================================================
# FASE A. Preflight. SOLO LECTURA: nada de esto toca el sistema, para que un
# error aqui deje el servidor exactamente como estaba.
# ==========================================================================

log "Preflight"

[ "$(id -u)" -eq 0 ] || die "Hay que correrlo como root (sudo)."

# Fail closed en la terminal. El unico camino sin preguntas es --non-interactive,
# y --dry-run NO es una excepcion: aunque no muta nada, el mensaje de abajo dice
# el comando exacto que si funciona sin TTY, asi que dejarlo pasar solo agrega una
# forma de correr el instalador a medias. --help ya salio antes de llegar aca.
if [ "$INTERACTIVE" -eq 1 ] && [ ! -t 0 ]; then
    die "Este instalador necesita una terminal: va a preguntar el dominio, la base de datos y el correo.

Como no hay TTY (pipe, cron o CI) y no se paso --non-interactive, se aborta SIN
TOCAR NADA. Un instalador que adivina en un pipe escribe el .env equivocado y
el error aparece cuando el sitio ya esta sirviendo otra base de datos.

Para correrlo sin preguntas:

    curl -fsSL <raw-url>/deploy/install.sh | sudo bash -s -- --non-interactive

Cada valor sale de la variable de entorno del mismo nombre o del default; el
resumen final dice de donde salio cada uno. Para verlo primero, sin cambiar nada,
sumale --dry-run:

    curl -fsSL <raw-url>/deploy/install.sh | sudo bash -s -- --dry-run --non-interactive

O descargalo y corrélo con terminal:
    curl -fsSL -o install.sh <raw-url>/deploy/install.sh && sudo bash install.sh"
fi

# Distribucion. Todo el instalador es apt: no hay equivalente probado para
# dnf/apk y adivinar el gestor de paquetes produce un script que instala la
# mitad de las cosas.
if [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    DISTRO_ID=${ID:-desconocida}
    DISTRO_LIKE=${ID_LIKE:-}
else
    DISTRO_ID=desconocida
    DISTRO_LIKE=
fi
case " $DISTRO_ID $DISTRO_LIKE " in
    *" debian "* | *" ubuntu "*) ;;
    *) die "Solo Debian/Ubuntu: este instalador usa apt y esta probado ahi.
  Distribucion detectada: ID=$DISTRO_ID ID_LIKE=${DISTRO_LIKE:-ninguno}.
  En otra distro, corre a mano los pasos que imprime --dry-run." ;;
esac
echo "  distro: $PRETTY_NAME ($DISTRO_ID)"

command -v apt-get >/dev/null 2>&1 || die "apt-get no esta disponible."
command -v openssl >/dev/null 2>&1 || warn "openssl no esta: se necesita para el certificado autofirmado."
command -v curl >/dev/null 2>&1 || warn "curl no esta: se necesita para certbot y para el health check."

# Python >= MIN_PYTHON. El motivo concreto esta en el comment de MIN_PYTHON
# arriba; aca solo se traduce a un error que lo dice.
PYTHON_BIN=${PYTHON_BIN:-python3}
PYTHON_VERSION=$("$PYTHON_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo '')
if [ -z "$PYTHON_VERSION" ]; then
    die "No se pudo ejecutar $PYTHON_BIN. Instalá python3 y volve a correr."
fi
# El (3, 14) va con coma a proposito: `tuple(3 14)` no es Python valido y
# fallaria con un SyntaxError que no dice nada de la version.
if ! "$PYTHON_BIN" -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (${MIN_PYTHON[0]}, ${MIN_PYTHON[1]}) else 1)"; then
    die "Se necesita Python ${MIN_PYTHON[0]}.${MIN_PYTHON[1]} o superior; encontrado $PYTHON_VERSION.

No es una preferencia: scripts/generate_env.py usa PEP 758 (except sin parentesis,
\`except A, B:\`), que solo existe desde Python 3.14. Con una version anterior el
generador no compila y falla con un SyntaxError que no menciona la version."
fi
echo "  python: $PYTHON_VERSION (minimo ${MIN_PYTHON[0]}.${MIN_PYTHON[1]})"

require_systemd
echo "  systemd-run disponible."

# Estado previo, SOLO de lectura. Se usa para armar los defaults de las
# preguntas (el default es el valor vigente) y para avisar de re-corridas.
ENV_FILE=$APP_DIR/.env
ENV_FILE_EXISTS=0
[ -f "$ENV_FILE" ] && ENV_FILE_EXISTS=1
CONFIG_FILE_EXISTS=0
[ -f "$CONFIG_FILE" ] && CONFIG_FILE_EXISTS=1
APP_DIR_EXISTS=0
[ -d "$APP_DIR/.git" ] && APP_DIR_EXISTS=1

if [ "$APP_DIR_EXISTS" -eq 1 ]; then
    echo "  $APP_DIR ya es un checkout: se reusa (idempotente)."
fi
if [ "$ENV_FILE_EXISTS" -eq 1 ]; then
    echo "  $ENV_FILE ya existe: se conserva y sus valores son los defaults."
fi
if [ "$CONFIG_FILE_EXISTS" -eq 1 ]; then
    echo "  $CONFIG_FILE ya existe: NO se pisa sin confirmacion."
fi

# ==========================================================================
# FASE B. Preguntas. Tampoco muta nada: por eso el instalador puede fallar
# aqui sin dejar el servidor a medio instalar.
# ==========================================================================

log "Configuracion (todo tiene default; Enter para conservarlo)"

EXTERNAL_HOSTNAME=$(ask PUBLIC_HOSTNAME "${PUBLIC_HOSTNAME:-web.cmw.insmet.cu}" \
    'Dominio publico del sitio (EXTERNAL_HOSTNAME del .env, server_name de Nginx, SNI del health check)' \
    valid_hostname) || die 'Dominio invalido.'

USE_WWW=$(ask_one_of USE_WWW si 'Sirve tambien en www?' \
    'si: anade www.<dominio> al vhost, al ALLOWED_HOSTS y al certificado' \
    'no: solo el dominio sin www') || die 'Opcion invalida.'
if [ "$USE_WWW" = si ]; then
    WWW_HOSTNAME=www.$EXTERNAL_HOSTNAME
else
    WWW_HOSTNAME=
fi

HTTP_PORT=$(ask HTTP_PORT 80 'Puerto HTTP (se redirige a HTTPS si hay TLS)' valid_port) || die 'Puerto invalido.'
HTTPS_PORT=$(ask HTTPS_PORT 443 'Puerto HTTPS' valid_port) || die 'Puerto invalido.'

PROXY_MODE=$(ask_one_of PROXY_MODE nginx-local 'Reverse proxy' \
    'nginx-local: Nginx instalado y configurado en esta maquina, con TLS' \
    'external: hay un proxy externo (Nginx Proxy Manager). NO se instala Nginx' \
    ) || die 'Opcion invalida.'

TLS_MODE=none
ACME_EMAIL=
if [ "$PROXY_MODE" = nginx-local ]; then
    # El aviso va ACA y no despues de elegir, porque la eleccion de un
    # certificado autofirmado es la que deja el sitio en rojo en cada navegador
    # y la que obliga a HEALTHCHECK_INSECURE=1.
    cat >&2 <<EOF

  Con proxy nginx-local, el TLS se resuelve aca:

    certbot  -> requiere que $EXTERNAL_HOSTNAME resuelva a esta maquina desde
                Internet y que los puertos $HTTP_PORT y $HTTPS_PORT esten abiertos
                hacia afuera. Emite un certificado que los navegadores confian.
    autofirmado -> funciona sin DNS publico ni puertos abiertos, pero el
                navegador lo muestra como no seguro en cada visita y el health
                check de deploy.sh necesita HEALTHCHECK_INSECURE=1, con lo que
                deja de detectar un certificado vencido.
EOF
    TLS_MODE=$(ask_one_of TLS_MODE certbot 'TLS' \
        'certbot: DNS publico y puertos abiertos, certificado de confianza' \
        'self-signed: certificado autofirmado, con las consecuencias de arriba' \
        ) || die 'Opcion invalida.'
    if [ "$TLS_MODE" = certbot ]; then
        ACME_EMAIL=$(ask ACME_EMAIL "" "Correo para el registro de Let's Encrypt (vacio = sin registro)" valid_email) || die 'Correo invalido.'
    fi
fi

# --- Base de datos -------------------------------------------------------

cat >&2 <<EOF

  Base de datos. PostgreSQL es el default porque requirements/prod.txt trae
  psycopg[binary]; es lo que el README del proyecto asume.
  MySQL NO tiene driver en requirements/prod.txt: si se elige, el instalador
  instala mysqlclient en el venv y avisa de que queda fuera de los pins.
  SQLite no tiene concurrencia y no lee DB_NAME/DB_USER/DB_HOST/DB_PASS: sirve
  para una prueba, no para un sitio con usuarios entrando.
EOF
DB_ENGINE=$(ask_one_of DB_ENGINE postgresql 'Motor de base de datos' \
    'postgresql: driver en requirements/prod.txt' \
    'mysql: hay que instalar mysqlclient ademas' \
    'sqlite3: sin concurrencia, sin DB_* (solo prueba)' \
    ) || die 'Opcion invalida.'

if [ "$DB_ENGINE" = postgresql ]; then
    DEFAULT_DB_PORT=5432
    DEFAULT_SSL_MODE=prefer
elif [ "$DB_ENGINE" = mysql ]; then
    DEFAULT_DB_PORT=3306
    DEFAULT_SSL_MODE=PREFERRED
else
    DEFAULT_DB_PORT=
    DEFAULT_SSL_MODE=
fi

DB_NAME=$(ask DB_NAME webcmp 'Nombre de la base' valid_db_name) || die 'Nombre de base invalido.'
DB_USER=$(ask DB_USER webcmp 'Usuario de la base (rol en PostgreSQL, usuario en MySQL)' valid_app_user) || die 'Usuario de base invalido.'
DB_HOST=$(ask DB_HOST localhost 'Host de la base de datos' valid_host) || die 'Host invalido.'
if [ "$DB_ENGINE" != sqlite3 ]; then
    DB_PORT=$(ask DB_PORT "$DEFAULT_DB_PORT" 'Puerto de la base de datos' valid_port) || die 'Puerto invalido.'
    DB_SSL_MODE=$(ask DB_SSL_MODE "$DEFAULT_SSL_MODE" \
        'DB_SSL_MODE (postgresql: disable|allow|prefer|require|verify-ca|verify-full; mysql: DISABLED|PREFERRED|REQUIRED|VERIFY_CA|VERIFY_IDENTITY)' \
        ) || die 'Valor invalido.'
else
    DB_PORT=''
    DB_SSL_MODE=''
fi

# El default del password es el que YA esta en el .env, si lo hay. Es lo que
# hace segura una re-corrida: sin esto, cada pasada por el instalador cambiaria
# la contrasena de la base y dejaria al Django del servidor sin poder conectarse.
if [ "$ENV_FILE_EXISTS" -eq 1 ]; then
    EXISTING_DB_PASS=$(env_get "$ENV_FILE" DB_PASS)
else
    EXISTING_DB_PASS=
fi
DB_PASS_GENERATED=0
if [ -z "$EXISTING_DB_PASS" ]; then
    DB_PASS_GENERATED=1
fi
DB_PASS=$(ask_secret DB_PASS "$EXISTING_DB_PASS" 'Contrasena de la base de datos') || die 'Contrasena invalida.'
if [ "$DB_PASS_GENERATED" -eq 1 ] && [ "$DRY_RUN" -eq 0 ]; then
    print_once_secret 'DB_PASS' "$DB_PASS" recover_env_password
fi

# --- Correo --------------------------------------------------------------

cat >&2 <<EOF

  Correo. En produccion, config/settings/production.py RECHAZA los backends
  silenciosos (consola, filebased, locmem): aceptan el mensaje y lo descartan.
  El instalador no ofrece esa opcion a proposito.
EOF
EMAIL_HOST=$(ask EMAIL_HOST "" 'Servidor SMTP (vacio = todavia no hay correo)' valid_host) || die 'Host SMTP invalido.'
EMAIL_PORT=$(ask EMAIL_PORT 587 'Puerto SMTP' valid_port) || die 'Puerto SMTP invalido.'
EMAIL_USE_TLS=si
EMAIL_USE_SSL=no
if [ "$EMAIL_PORT" = 465 ]; then
    # 465 es SMTPS implicito: TLS desde el principio de la conexion. Preguntar
    # STARTTLS ahi produce una combinacion que no existe (SSL y TLS los dos) y
    # Django falla al abrir el socket con un error que no menciona el puerto.
    EMAIL_USE_TLS=no
    EMAIL_USE_SSL=si
    echo "  puerto 465: EMAIL_USE_SSL=si y EMAIL_USE_TLS=no (TLS implicito)."
elif ask_yes_no si 'STARTTLS en el SMTP? (EMAIL_USE_TLS)'; then
    EMAIL_USE_TLS=si
else
    EMAIL_USE_TLS=no
fi
EMAIL_HOST_USER=$(ask EMAIL_HOST_USER "" 'Usuario SMTP (vacio = SMTP sin usuario)' valid_app_user) || die 'Usuario SMTP invalido.'
EMAIL_HOST_PASSWORD=$(ask_optional_secret EMAIL_HOST_PASSWORD "" 'Contrasena SMTP (vacio = SMTP sin contrasena)') || die 'Contrasena SMTP invalida.'
DEFAULT_FROM_EMAIL=$(ask DEFAULT_FROM_EMAIL "" 'Remitente (nombre <correo>); vacio = $EMAIL_HOST_USER') || die 'Remitente invalido.'

# "Configurado" es solo "hay servidor SMTP". Un relay sin usuario ni contrasena
# (un relay interno en el puerto 25, tipico en un servidor de correo corporativo)
# es una configuracion valida, y exigirle usuario seria dejar un CHANGE_ME
# imposible de resolver sin cambiar de servidor de correo.
if [ -n "$EMAIL_HOST" ]; then
    EMAIL_CONFIGURED=1
else
    EMAIL_CONFIGURED=0
fi

# --- Superusuario --------------------------------------------------------

cat >&2 <<EOF

  Superusuario de Django. La cuenta se crea con `createsuperuser --noinput` por
  systemd-run, con la ENCRYPTION_KEY cargada y PRODUCTION=1.
EOF
SUPERUSER_USERNAME=$(ask SUPERUSER_USERNAME admin 'Usuario del superusuario' valid_app_user) || die 'Usuario invalido.'
SUPERUSER_EMAIL=$(ask SUPERUSER_EMAIL "$EMAIL_HOST_USER" 'Correo del superusuario' valid_email) || die 'Correo invalido.'
SUPERUSER_PASS_GENERATED=0
if [ -z "${SUPERUSER_PASSWORD:-}" ]; then
    SUPERUSER_PASS_GENERATED=1
fi
SUPERUSER_PASSWORD=$(ask_secret SUPERUSER_PASSWORD "${SUPERUSER_PASSWORD:-}" 'Contrasena del superusuario') || die 'Contrasena invalida.'
if [ "$SUPERUSER_PASS_GENERATED" -eq 1 ] && [ "$DRY_RUN" -eq 0 ]; then
    print_once_secret 'SUPERUSER_PASSWORD' "$SUPERUSER_PASSWORD" recover_env_password
fi

# --- Otros campos del .env ----------------------------------------------

USE_REDIS_CACHE=no
if ask_yes_no si 'Cache con Redis? (USE_REDIS_CACHE)'; then USE_REDIS_CACHE=si; fi
REDIS_URL=$(ask REDIS_URL redis://127.0.0.1:6379/1 'URL de Redis') || die 'URL de Redis invalida.'
LOG_LEVEL=$(ask LOG_LEVEL INFO 'Nivel de log' valid_log_level) || die 'Nivel de log invalido.'
FTP_OBS=no
if ask_yes_no no 'El deployment lee observaciones por FTP?'; then
    FTP_OBS=si
    FTP_OBS_HOST=$(ask FTP_OBS_HOST "" 'Host FTP de observaciones' valid_host) || die 'Host FTP invalido.'
    FTP_OBS_USER=$(ask FTP_OBS_USER "" 'Usuario FTP' valid_app_user) || die 'Usuario FTP invalido.'
    FTP_OBS_PASS=$(ask_optional_secret FTP_OBS_PASS "" 'Contrasena FTP (vacio = FTP sin contrasena)') || die 'Contrasena FTP invalida.'
    FTP_OBS_PORT=$(ask FTP_OBS_PORT 990 'Puerto FTP' valid_port) || die 'Puerto FTP invalido.'
else
    FTP_OBS_HOST= FTP_OBS_USER= FTP_OBS_PASS= FTP_OBS_PORT=990
fi
LDAP_ENABLED=no
if ask_yes_no no 'Autenticacion LDAP?'; then
    LDAP_ENABLED=si
    LDAP_SERVER_URI=$(ask LDAP_SERVER_URI ldap://ldap.ejemplo.cu:389 'LDAP_SERVER_URI') || die 'URI invalida.'
    LDAP_BIND_DN=$(ask LDAP_BIND_DN "" 'LDAP_BIND_DN (cn=admin,dc=ejemplo,dc=cu)') || die 'Bind DN invalido.'
    LDAP_BIND_PASSWORD=$(ask_optional_secret LDAP_BIND_PASSWORD "" 'LDAP_BIND_PASSWORD (vacio = sin contrasena)') || die 'Contrasena LDAP invalida.'
    LDAP_USER_SEARCH_BASE=$(ask LDAP_USER_SEARCH_BASE ou=people,dc=ejemplo,dc=cu 'LDAP_USER_SEARCH_BASE') || die 'Base de busqueda invalida.'
fi

# ==========================================================================
# FASE C. Ejecucion. De aca en adelante SI se toca el sistema.
# ==========================================================================

log "Resumen de lo que se va a instalar"
cat <<EOF
  checkout        $APP_DIR ($REPO_URL @ $REPO_REF)
  usuario         $SERVICE_USER:$SERVICE_GROUP (shell $SERVICE_SHELL)
  dominio         $EXTERNAL_HOSTNAME${WWW_HOSTNAME:+, $WWW_HOSTNAME}
  proxy           $PROXY_MODE (TLS: $TLS_MODE)
  base            $DB_ENGINE db=$DB_NAME user=$DB_USER host=${DB_HOST:-local}
  correo          ${EMAIL_HOST:-SIN CONFIGURAR}
  superusuario    $SUPERUSER_USERNAME
  deploy.sh       $SCRIPT_PATH
  deploy.env      $CONFIG_FILE
  health check    $([ "$PROXY_MODE" = nginx-local ] \
      && echo "https://$EXTERNAL_HOSTNAME/ en 127.0.0.1:$HTTPS_PORT con SNI" \
      || echo "socket $GUNICORN_SOCKET con Host: $EXTERNAL_HOSTNAME")
EOF
if [ "$DRY_RUN" -eq 1 ]; then
    echo
    echo "dry-run: se imprime el plan y no se ejecuta nada."
fi

# --- C.1 Prerrequisitos de sistema --------------------------------------

log "Prerrequisitos de sistema"

# La lista no es la del README del proyecto: esa no alcanza. La tabla de
# deploy/README-deploy.md documenta por que cada uno hace falta (build-essential
# para los pins sin ruedas en Python 3.14, libpango1.0-dev para WeasyPrint,
# libcairo2-dev para pycairo). Se replica aca porque este instalador tiene que
# ser autocontenido: no puede leer el README antes de clonar el repo.
APT_PACKAGES=(
    git
    sudo
    ca-certificates
    openssl
    python3
    python3-venv
    python3-dev
    build-essential
    pkg-config
    libcairo2-dev
    libpango1.0-dev
    redis-server
)
# Nginx SOLO con la opcion A. Con proxy externo, instalar Nginx seria dejar un
# servicio escuchando en 80/443 que nadie pidio y que ademas choca con el proxy
# de verdad si alguien abre el puerto por error.
if [ "$PROXY_MODE" = nginx-local ]; then
    APT_PACKAGES+=(nginx)
fi
# El driver de MySQL no esta en requirements/ (ver el bloque de arriba), asi que
# se instala aparte y con aviso, no en silencio.
if [ "$DB_ENGINE" = mysql ]; then
    warn "MySQL no tiene driver en requirements/prod.txt. Se va a instalar"
    warn "mysqlclient en el venv, fuera de los pins: si se actualiza el venv sin"
    warn "reinstalarlo, el sitio cae con ImproperlyConfigured."
    MYSQL_BUILD_DEPS=(libmysqlclient-dev pkg-config)
    APT_PACKAGES+=("${MYSQL_BUILD_DEPS[@]}")
fi

if [ "$DRY_RUN" -eq 1 ]; then
    printf '  [dry-run] apt-get install -y %s\n' "${APT_PACKAGES[*]}"
else
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq || die "apt-get update fallo."
    # Se instala lo que falte: `apt-get install` sobre un paquete ya presente no
    # hace nada, asi que no hace falta un ciclo de deteccion por paquete.
    apt-get install -y -qq "${APT_PACKAGES[@]}" \
        || die "apt-get install fallo. Revisa el repositorio de la distro y volve a correr."
fi

# El servidor de base de datos NO se instala sin permiso. Instalar PostgreSQL o
# MySQL es una decision de infraestructura (backup, locale, puerto, version) que
# el instalador no tiene derecho a tomar por su cuenta, y un `apt-get install
# postgresql` de surprise puede abrir el 5432 al mundo segun la configuracion de
# la distro.
DB_SERVER_PACKAGE=
case "$DB_ENGINE" in
    postgresql) DB_SERVER_PACKAGE=postgresql ;;
    mysql)      DB_SERVER_PACKAGE=default-mysql-server ;;
esac
if [ -n "$DB_SERVER_PACKAGE" ] && ! command -v "$([ "$DB_ENGINE" = postgresql ] && echo psql || echo mysql)" >/dev/null 2>&1
then
    warn "No encontre el cliente de $DB_ENGINE en el servidor."
    if ask_yes_no no "Instalar $DB_SERVER_PACKAGE con apt?"; then
        if [ "$DRY_RUN" -eq 1 ]; then
            printf '  [dry-run] apt-get install -y %s\n' "$DB_SERVER_PACKAGE"
        else
            apt-get install -y -qq "$DB_SERVER_PACKAGE" \
                || die "No se pudo instalar $DB_SERVER_PACKAGE. Instalalo a mano y volve a correr."
        fi
    else
        die "Sin $DB_SERVER_PACKAGE no se puede crear el rol y la base. El instalador no puede seguir sin saber si el servidor de base ya existe."
    fi
fi

# --- C.2 Usuario de servicio y directorios -------------------------------

log "Usuario de servicio $SERVICE_USER"

if id "$SERVICE_USER" >/dev/null 2>&1; then
    echo "  ya existe (shell: $(getent passwd "$SERVICE_USER" | cut -d: -f7))"
else
    # --system: es una cuenta de servicio. Shell nologin, porque existe para
    # correr Gunicorn y Huey, no para que alguien se loguee con el. El usuario
    # de despliegue (abajo) es el que tiene shell, y son dos cosas distintas.
    # El home se pone en APP_DIR para que los paths absolutos de los units
    # coincidan con el dueno y ProtectHome=true no corte el checkout.
    run useradd --system --home-dir "$APP_DIR" --shell "$SERVICE_SHELL" \
        --no-create-home "$SERVICE_USER"
    echo "  creado"
fi

# MEDIA_ROOT, LOG_FILE, STATIC_ROOT y MPLCONFIGDIR viven adentro de APP_DIR y los
# escribe el usuario de servicio. Con el directorio equivocado, collectstatic
# escribe en / y el servicio no puede escribir sus propios logs: dos fallos
# distintos que se ven igual.
ensure_dir "$APP_DIR" 0755 "$SERVICE_USER" "$SERVICE_GROUP"
ensure_dir "$APP_DIR/media" 0750 "$SERVICE_USER" "$SERVICE_GROUP"
ensure_dir "$APP_DIR/logs" 0750 "$SERVICE_USER" "$SERVICE_GROUP"
ensure_dir "$APP_DIR/staticfiles" 0755 "$SERVICE_USER" "$SERVICE_GROUP"
ensure_dir "$APP_DIR/.cache" 0750 "$SERVICE_USER" "$SERVICE_GROUP"
ensure_dir "$MPLCONFIGDIR" 0750 "$SERVICE_USER" "$SERVICE_GROUP"
# Cache de pip. Sin esto, cada deploy vuelve a descargar todas las dependencias
# desde PyPI: `webcmp` es cuenta de sistema sin home, asi que pip no encuentra
# donde escribir ~/.cache. Ver la nota de PIP_CACHE_DIR en deploy.env.example.
ensure_dir "$PIP_CACHE_DIR" 0700 "$SERVICE_USER" "$SERVICE_USER"
ensure_dir "$CONFIG_DIR" 0755 root root
ensure_dir "$TLS_DIR" 0700 root root

# --- C.3 Clone -----------------------------------------------------------

log "Checkout en $APP_DIR"

if [ "$APP_DIR_EXISTS" -eq 1 ]; then
    # Clone existente: se actualiza, NO se regenera. Un `rm -rf $APP_DIR` para
    # "empezar limpio" se llevaria por delante media/, .env y el venv, que es
    # justamente lo que este script existe para no perder.
    echo "  ya existe; se actualiza a $REPO_REF (idempotente)."
    CURRENT_ORIGIN=$(runuser -u "$SERVICE_USER" -- git -C "$APP_DIR" remote get-url origin 2>/dev/null || echo '')
    if [ -n "$CURRENT_ORIGIN" ] && [ "$CURRENT_ORIGIN" != "$REPO_URL" ]; then
        warn "El origen actual es $CURRENT_ORIGIN y se pidio $REPO_URL."
        if ask_yes_no no "Cambiar el remoto origin a $REPO_URL?"; then
            run_sh "runuser -u '$SERVICE_USER' -- git -C '$APP_DIR' remote set-url origin '$REPO_URL'"
        else
            warn "Se deja el origen como estaba."
        fi
    fi
    # `git` corre como SERVICE_USER y no como root, por la misma razon que en
    # deploy.sh: un repo escribible por otro usuario con un .git/config capaz de
    # ejecutar comandos es un vector de escalada de privilegios, y git >= 2.35.2
    # se niega a trabajar sobre el con "dubious ownership".
    run_sh "runuser -u '$SERVICE_USER' -- git -C '$APP_DIR' fetch --quiet origin"
    run_sh "runuser -u '$SERVICE_USER' -- git -C '$APP_DIR' checkout --quiet '$REPO_REF'"
    run_sh "runuser -u '$SERVICE_USER' -- git -C '$APP_DIR' merge --ff-only --quiet 'origin/$REPO_REF' \
        || echo '  [aviso] no se pudo hacer fast-forward a origin/$REPO_REF; se deja el checkout como esta'"
else
    # git clone acepta un directorio destino existente VACIO, que es lo que se
    # acaba de crear con ensure_dir. Clonar por el usuario de servicio y no
    # como root evita el "dubious ownership" en el primer gitapp() del deploy.
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  [dry-run] runuser -u %s -- git clone %s %s\n' "$SERVICE_USER" "$REPO_URL" "$APP_DIR"
    else
        runuser -u "$SERVICE_USER" -- git clone --quiet --branch "$REPO_REF" "$REPO_URL" "$APP_DIR" \
            || die "No se pudo clonar $REPO_URL en $APP_DIR. Revisa salida a Internet, DNS y permisos de $APP_DIR."
    fi
fi

for f in deploy/deploy.sh deploy/sudoers/webcmp-deploy deploy/nginx/webcmp.conf.example \
         deploy/systemd/webcmp.service deploy/systemd/webcmp-huey.service \
         scripts/generate_env.py requirements/prod.txt
do
    [ -f "$APP_DIR/$f" ] && continue
    # En un dry-run sobre un servidor limpio el clone NO se hizo, asi que no hay
    # nada que verificar todavia. Morir aqui dejaria al --dry-run sin poder
    #correrse nunca en el servidor donde mas lo necesita uno: antes de clonar.
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  [dry-run] todavia no hay checkout en %s; %s se usara del repo al clonar.\n' \
            "$APP_DIR" "$f" >&2
        continue
    fi
    die "Falta $APP_DIR/$f: el clon esta incompleto."
done
HAVE_CHECKOUT=0
[ -d "$APP_DIR/.git" ] && HAVE_CHECKOUT=1
if [ "$HAVE_CHECKOUT" -eq 1 ]; then
    echo "  checkout listo."
else
    echo "  dry-run: los renders que necesitan el checkout se omiten."
fi

# need_checkout <que se haria con el>
#
# Los renders (units, vhost, sudoers) leen del checkout archivos que este
# instalador tiene que self-contained: en un dry-run sobre un servidor limpio
# todavia no estan. La alternativa era dejar el render para adelante y fallar
# con un "awk: cannot open /srv/webcmp/deploy/..." que no dice que el problema es
# que --dry-run no clona.
need_checkout() {
    # Con checkout: hay con que trabajar, el consumidor sigue de largo.
    [ "$HAVE_CHECKOUT" -eq 1 ] && return 0
    # Sin checkout: se avisa Y se devuelve error, para que el consumidor se
    # SALTE el bloque. Antes devolvia 0 en las dos ramas, con lo cual los cuatro
    # `|| need_checkout` de mas abajo nunca cortaban: los bloques corrigual
    # renders desde deploy/systemd, deploy/nginx y deploy/sudoers, que en un
    # dry-run sin checkout no existen.
    printf '  [dry-run] sin checkout: %s\n' "$1" >&2
    return 1
}

# --- C.4 Base de datos ---------------------------------------------------

if [ "$DB_ENGINE" != sqlite3 ]; then
    log "Base de datos $DB_ENGINE: rol y base"
    if [ "$DB_ENGINE" = postgresql ]; then
        # El password viaja por el STDIN de psql, no por `-v` en la linea de
        # comandos: un `-v dbpass=...` queda visible en `ps aux` mientras el
        # comando corre, y basta otro usuario con permiso de ver la tabla de
        # procesos para leer la contrasena de la base.
        #
        # `\set` + `:'dbuser'` / `:"dbuser"` hacen el escapado por nosotros.
        # Interpolar el valor a mano dentro de un DO $$ ... $$ se rompe con
        # cualquier password que tenga un `$`, y se INYECTA con una que tenga una
        # comilla simple: por eso psql_quote() y no concatenacion de strings.
        #
        # Idempotencia: el rol se crea solo si no existe, la base idem, y la
        # contrasena se ALTERA al valor preguntado. Nunca hay DROP: tirar la
        # base de un sitio en produccion es el peor error que puede cometer un
        # instalador, y ningun idempotencia lo justifica.
        if [ "$DRY_RUN" -eq 1 ]; then
            printf '  [dry-run] runuser -u postgres -- psql (crea rol %s y base %s)\n' "$DB_USER" "$DB_NAME"
        else
            runuser -u postgres -- psql --quiet --set=ON_ERROR_STOP=1 <<SQL
\\set dbuser $(psql_quote "$DB_USER")
\\set dbpass $(psql_quote "$DB_PASS")
\\set dbname $(psql_quote "$DB_NAME")
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'dbuser', :'dbpass')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'dbuser')
\\gexec
ALTER ROLE :"dbuser" WITH LOGIN PASSWORD :'dbpass';
SELECT format('CREATE DATABASE %I OWNER %I ENCODING %L', :'dbname', :'dbuser', 'UTF8')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'dbname')
\\gexec
\\echo 'rol y base listos'
SQL
        fi
    else
        # MySQL: el cliente se ejecuta como root y el socket unix autentica por
        # credenciales del sistema, asi que no hay password de root que manejar.
        # `CREATE USER IF NOT EXISTS` y `CREATE DATABASE IF NOT EXISTS` existen
        # en MySQL 5.7+ y en MariaDB 10.1+, asi que la re-corredura es segura.
        if [ "$DRY_RUN" -eq 1 ]; then
            printf '  [dry-run] mysql (crea usuario %s y base %s)\n' "$DB_USER" "$DB_NAME"
        else
            mysql --protocol=socket <<SQL
CREATE USER IF NOT EXISTS $(sql_quote "$DB_USER")@'localhost'
    IDENTIFIED BY $(sql_quote "$DB_PASS");
ALTER USER $(sql_quote "$DB_USER")@'localhost'
    IDENTIFIED BY $(sql_quote "$DB_PASS");
CREATE DATABASE IF NOT EXISTS $(sql_quote "$DB_NAME")
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON $(sql_quote "$DB_NAME").* TO $(sql_quote "$DB_USER")@'localhost';
FLUSH PRIVILEGES;
SQL
        fi
    fi
    echo "  rol y base listos (nunca se borra una base existente)."
else
    log "Base de datos sqlite3"
    warn "SQLite: sin concurrencia y sin DB_NAME/DB_USER/DB_HOST/DB_PASS."
    warn "get_database_config() devuelve sqlite3 porque DB_ENGINE=sqlite3; la"
    warn "base es $APP_DIR/db.sqlite3 y Django la crea sola en el migrate."
fi

# --- C.5 venv ------------------------------------------------------------

log "Entorno virtual"

if [ -x "$VENV_DIR/bin/python" ]; then
    echo "  ya existe en $VENV_DIR (idempotente)."
else
    run_sh "$PYTHON_BIN -m venv '$VENV_DIR'"
fi

# requirements/prod.txt trae cryptography, que es lo unico que necesita
# scripts/generate_env.py. Por eso el venv va ANTES de generar el .env: el
# generador importa Fernet y no Django, asi que el venv es la unica forma de
# tener esa dependencia sin tocar el Python del sistema.
log "Instalando requirements/prod.txt"
run_sh "runuser -u '$SERVICE_USER' -- env 'PIP_CACHE_DIR=$PIP_CACHE_DIR' \
    '$VENV_DIR/bin/pip' install --quiet --disable-pip-version-check -r '$APP_DIR/requirements/prod.txt'"

if [ "$DB_ENGINE" = mysql ]; then
    log "Driver de MySQL (fuera de requirements/prod.txt)"
    run_sh "runuser -u '$SERVICE_USER' -- env 'PIP_CACHE_DIR=$PIP_CACHE_DIR' \
        '$VENV_DIR/bin/pip' install --quiet --disable-pip-version-check mysqlclient"
    warn "mysqlclient quedo en el venv pero NO en requirements/prod.txt. Si se"
    warn "recrea el venv, hay que volver a instalarlo."
fi

# --- C.6 .env ------------------------------------------------------------

log "Archivo .env"

# El generador es NO interactivo por diseño (su docstring lo dice: "un
# generador que adivina el entorno es un generador que un día escribe el .env
# equivocado"). Por eso NO se le pregunta nada: se lo corre y despues se
# sustituyen los CHANGE_ME con lo que el operador respondio. Toca hacerlo asi y
# no al reves porque el generador tiene invariants propios -- conserva el par de
# claves si descifra, escribe ENCRYPTION_KEY en /etc/webcmp/encryption.env y no
# en el .env, y aborta ANTES de tocar el .env si ese archivo no se puede escribir
# -- que no se pueden replicar con un `cat > .env`.
#
# --force solo se pasa con confirmacion: sin el, el generador se niega a pisar un
# .env afinado a mano, y el instalador respeta ese comportamiento en vez de
# quedar por encima.
ENV_GEN_ARGS=(--production --env-file "$ENV_FILE" --encryption-key-file "$ENCRYPTION_ENV")
if [ "$ENV_FILE_EXISTS" -eq 1 ]; then
    if ask_yes_no no "Regenerar $ENV_FILE con el generador (conserva SECRET_KEY y ENCRYPTION_KEY)?"; then
        echo "  se conserva el .env existente."
        ENV_REGENERATED=0
    else
        ENV_REGENERATED=1
    fi
else
    ENV_REGENERATED=1
fi

if [ "$ENV_REGENERATED" -eq 1 ]; then
    ENV_GEN_ARGS+=(--force)
    # Se corre COMO ROOT y no como webcmp: el generador tiene que escribir
    # $ENCRYPTION_ENV, que es root:root 600. Corrido como webcmp aborta sin
    # escribir nada (falla cerrado, que esta bien) y el servidor queda igual.
    run_sh "'$VENV_DIR/bin/python' '$APP_DIR/scripts/generate_env.py' $(printf '%q ' "${ENV_GEN_ARGS[@]}")"
    # Y despues hay que devolverle el .env a webcmp: Django corre como ese
    # usuario y tiene que poder leerlo. Con root:root 600 el sitio levanta y
    # falla al primer acceso con un 500 que no dice "no podi leer el .env".
    run chown "$SERVICE_USER:$SERVICE_GROUP" "$ENV_FILE"
    run chmod 0600 "$ENV_FILE"
fi

if [ "$ENV_REGENERATED" -eq 0 ]; then
    echo "  se aplica lo respondido sobre el .env existente."
fi

# Sustitucion de los valores preguntados. env_set reemplaza la linea KEY= o la
# agrega, asi que funciona igual con un .env recien generado (todo commented-out
# o con CHANGE_ME) y con uno afinado a mano (donde hay valores que hay que
# RESPETAR y no pisar a ciegas).
apply_env_value() {
    run env_set "$ENV_FILE" "$1" "$2"
    printf '  %s=%s\n' "$1" "$(mask "$1" "$2")"
}

log "Sustituyendo los valores del .env"
apply_env_value EXTERNAL_HOSTNAME "$EXTERNAL_HOSTNAME"
if [ -n "$WWW_HOSTNAME" ]; then
    ALLOWED_HOSTS="$EXTERNAL_HOSTNAME,$WWW_HOSTNAME"
    ORIGINS="https://$EXTERNAL_HOSTNAME,https://$WWW_HOSTNAME"
else
    ALLOWED_HOSTS="$EXTERNAL_HOSTNAME"
    ORIGINS="https://$EXTERNAL_HOSTNAME"
fi
# EXTERNAL_HOSTNAME ya mete el dominio en ALLOWED_HOSTS y en
# CSRF_TRUSTED_ORIGINS por apply_external_hostname() de production.py. Repetirlo
# en las tres listas no esta de mas: ALLOWED_HOSTS lo lee el middleware de host
# con la lista ya resuelta, y si el dominio no esta en el archivo (por ejemplo
# porque EXTERNAL_HOSTNAME se escribio despues del import) la respuesta es
# DisallowedHost en cada peticion.
apply_env_value ALLOWED_HOSTS "$ALLOWED_HOSTS"
apply_env_value CSRF_TRUSTED_ORIGINS "$ORIGINS"
apply_env_value CORS_ALLOWED_ORIGINS "$ORIGINS"

apply_env_value DB_ENGINE "$DB_ENGINE"
if [ "$DB_ENGINE" != sqlite3 ]; then
    apply_env_value DB_NAME "$DB_NAME"
    apply_env_value DB_USER "$DB_USER"
    apply_env_value DB_PASS "$DB_PASS"
    apply_env_value DB_HOST "$DB_HOST"
    apply_env_value DB_PORT "$DB_PORT"
    apply_env_value DB_SSL_MODE "$DB_SSL_MODE"
fi

if [ "$EMAIL_CONFIGURED" -eq 1 ]; then
    apply_env_value EMAIL_HOST "$EMAIL_HOST"
    apply_env_value EMAIL_PORT "$EMAIL_PORT"
    apply_env_value EMAIL_USE_TLS "$EMAIL_USE_TLS"
    apply_env_value EMAIL_USE_SSL "$EMAIL_USE_SSL"
    apply_env_value EMAIL_HOST_USER "$EMAIL_HOST_USER"
    apply_env_value EMAIL_HOST_PASSWORD "$EMAIL_HOST_PASSWORD"
    apply_env_value DEFAULT_FROM_EMAIL "${DEFAULT_FROM_EMAIL:-$EMAIL_HOST_USER}"
else
    # EMAIL_BACKEND se deja como lo escribio el generador
    # (config.custom_email_backend.CustomSTARTTLSBackend, que no es silencioso
    # y por eso production.py lo acepta), pero con EMAIL_HOST vacio el envio
    # falla. Se avisa y no se inventa nada.
    warn "Correo sin configurar: EMAIL_HOST quedo vacio, asi que los avisos y"
    warn "reportes que mandan correo van a fallar. Los CHANGE_ME de esa seccion"
    warn "del .env siguen ahi a proposito."
fi

apply_env_value USE_REDIS_CACHE "$USE_REDIS_CACHE"
apply_env_value REDIS_URL "$REDIS_URL"
apply_env_value LOG_LEVEL "$LOG_LEVEL"
apply_env_value FTP_OBS_HOST "$FTP_OBS_HOST"
apply_env_value FTP_OBS_USER "$FTP_OBS_USER"
apply_env_value FTP_OBS_PASS "$FTP_OBS_PASS"
apply_env_value FTP_OBS_PORT "$FTP_OBS_PORT"

if [ "$LDAP_ENABLED" = si ]; then
    # El generador deja el bloque LDAP comentado como plantilla. env_set no
    # pisa lineas comentadas (busca `^KEY=`), asi que estas claves se agregan
    # al final del archivo: es lo correcto, no un descuido, y la plantilla
    # comentada de arriba queda como recordatorio de las que faltan.
    apply_env_value LDAP_SERVER_URI "$LDAP_SERVER_URI"
    apply_env_value LDAP_BIND_DN "$LDAP_BIND_DN"
    apply_env_value LDAP_BIND_PASSWORD "$LDAP_BIND_PASSWORD"
    apply_env_value LDAP_USER_SEARCH_BASE "$LDAP_USER_SEARCH_BASE"
fi

# Gate del .env. Un CHANGE_ME que sobrevive es un sitio que responde 500 o se
# queda sin correo, y el sintoma (un error de SMTP o de DB en el log) no dice
# "falta un campo del .env". Falla cerrado salvo que el operador lo pida
# explicitamente con --allow-incomplete-env, que deja TODO sin arrancar.
PENDING_CHANGES=$(grep -n 'CHANGE_ME' "$ENV_FILE" 2>/dev/null || true)
if [ -n "$PENDING_CHANGES" ]; then
    if [ "$ALLOW_INCOMPLETE_ENV" -eq 1 ]; then
        warn "Quedan CHANGE_ME en $ENV_FILE (--allow-incomplete-env):"
        printf '%s\n' "$PENDING_CHANGES" | sed 's/^/    /' >&2
        warn "El sitio NO se va a arrancar con esta configuracion."
    else
        printf '%s\n' "$PENDING_CHANGES" | sed 's/^/    /' >&2
        die "Quedan CHANGE_ME en $ENV_FILE. Se paro ANTES de migrar y de arrancar el sitio.

Si de verdad todavia no hay SMTP o la base, se puede continuar a proposito con:

    sudo bash install.sh --allow-incomplete-env

pero el sitio va a quedar SIN LEVANTAR hasta que se completen esos valores."
    fi
fi
echo "  .env completo."

# --- C.7 Migraciones, estaticos, gate ------------------------------------

log "Migraciones y estaticos"

if [ -n "$PENDING_CHANGES" ]; then
    # Con un .env incompleto NO se migra. Las migraciones abren conexion a la base
    # y un CHANGE_ME en DB_PASS las hace fallar con un error de autenticacion que
    # no dice "falta completar el .env"; peor, si el CHANGE_ME esta en una parte
    # que todavia no importa, la migracion corre y el esquema queda medio aplicado.
    warn "No se corre makemigrations ni migrate: el .env esta incompleto."
    warn "collectstatic y check --deploy si se corren: no tocan la base y sus"
    warn "resultados sirven igual para diagnosticar."
    warn "La migracion queda pendiente: hay que volver a correr este instalador"
    warn "cuando esten completos los valores de arriba."
else
    run manage makemigrations
    run manage migrate --noinput
    run manage migrate --check
fi
run manage collectstatic --no-input
# El mismo gate que corre deploy.sh en cada deploy, corrido una vez con la
# configuracion real. security.W008 no aparece porque production.py lo silencia
# en SILENCED_SYSTEM_CHECKS: el TLS y el redirect los termina el proxy, no
# Django.
run manage check --deploy --fail-level WARNING

if [ -n "$PENDING_CHANGES" ]; then
    log "Superusuario omitido"
    warn "No se crea el superusuario con el .env incompleto: createsuperuser"
    warn "importa los settings y habria que hacerlo en el perfil equivocado."
else
    # El `.env` va al directorio del proyecto porque Django lo lee en
    # BASE_DIR/'.env' y en ningun otro lado. Passarlo en otro sitio no lo hace
    # aparecer.
    log "Superusuario $SUPERUSER_USERNAME"
    # OJO: systemd-run NO hereda el entorno de quien llama. Un
    # `DJANGO_SUPERUSER_PASSWORD=... systemd-run ... createsuperuser --noinput`
    # crea la cuenta con una contrasena inservible y sin avisar, porque la
    # variable se queda en la shell de root. Para pasar algo, va con
    # -p Environment=NOMBRE=valor. Es el bug documentado en deploy.sh:200-207 y
    # el que hace que este paso se escriba asi y no como un `export` de la
    # config de install.sh.
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  [dry-run] systemd-run ... createsuperuser --noinput --username %s\n' "$SUPERUSER_USERNAME"
    else
        if systemd-run --quiet --pipe --wait \
            --uid="$SERVICE_USER" --gid="$SERVICE_USER" \
            -p "EnvironmentFile=$ENCRYPTION_ENV" \
            -p Environment=PRODUCTION=1 \
            -p "Environment=MPLCONFIGDIR=$MPLCONFIGDIR" \
            -p "Environment=DJANGO_SUPERUSER_PASSWORD=$SUPERUSER_PASSWORD" \
            --working-directory="$APP_DIR" \
            "$VENV_DIR/bin/python" manage.py createsuperuser --noinput \
            --username "$SUPERUSER_USERNAME" --email "$SUPERUSER_EMAIL"
        then
            echo "  superusuario listo."
        else
            warn "No se pudo crear el superusuario. Se deja el resto instalado."
            warn "Crear a mano (mismo contexto que el sitio):"
            printf '  sudo systemd-run --quiet --pipe --wait --uid=%s -p EnvironmentFile=%s \\\n' \
                "$SERVICE_USER" "$ENCRYPTION_ENV" >&2
            printf '    -p Environment=PRODUCTION=1 -p Environment=DJANGO_SUPERUSER_PASSWORD=<clave> \\\n' >&2
            printf '    --working-directory=%s %s manage.py createsuperuser --noinput --username %s\n' \
                "$APP_DIR" "$VENV_DIR/bin/python" "$SUPERUSER_USERNAME" >&2
        fi
    fi
fi

# --- C.8 Unidades systemd ------------------------------------------------

log "Unidades systemd"

# RENDER, no copia. Las rutas de deploy/systemd/*.service estan escritas en el
# archivo a proposito (en un unit, `APP_DIR=/srv/webcmp` no es una clave valida
# de systemd y `systemd-analyze verify` falla con "Unknown key"), asi que un
# checkout en otra ruta necesita reescribir el archivo, no interpolarlo. El
# render es literal, no con regex: `webcmp` como patron matchearia tambien
# `webcmp-huey`, que es el nombre del otro unit.
render_unit() {
    local src=$1 dest=$2 tmp
    tmp=$(mktemp)
    render_template "$src" "$tmp" \
        "/srv/webcmp<>$APP_DIR" \
        "/etc/webcmp/encryption.env<>$ENCRYPTION_ENV" \
        "webcmp-huey<>$HUEY_UNIT" \
        "User=webcmp<>User=$SERVICE_USER" \
        "Group=webcmp<>Group=$SERVICE_GROUP" \
        "RuntimeDirectory=webcmp<>RuntimeDirectory=$GUNICORN_UNIT" \
        "/run/webcmp<>/run/$GUNICORN_UNIT" \
        || { rm -f "$tmp"; return 1; }
    install_if_changed "$tmp" "$dest" 0644
    rm -f "$tmp"
}

if need_checkout 'se renderizaran las dos unidades systemd desde deploy/systemd/'; then
    render_unit "$APP_DIR/deploy/systemd/webcmp.service" "/etc/systemd/system/$GUNICORN_UNIT.service"
    render_unit "$APP_DIR/deploy/systemd/webcmp-huey.service" "/etc/systemd/system/$HUEY_UNIT.service"
fi

run systemctl daemon-reload

# En nginx-local, www-data tiene que poder tocar el socket de Gunicorn (0770
# webcmp:webcmp). Sin esto Nginx devuelve 502 en cada respuesta y el log dice
# "connect() failed (13: Permission denied)", que parece un problema de permisos
# que no lo es. Con proxy externo NO se toca: el Nginx que hace de proxy no es
# este, asi que el grupo no le sirve de nada.
if [ "$PROXY_MODE" = nginx-local ]; then
    if id -nG www-data 2>/dev/null | tr ' ' '\n' | grep -qx "$SERVICE_GROUP"; then
        echo "  www-data ya esta en el grupo $SERVICE_GROUP"
    else
        run usermod -aG "$SERVICE_GROUP" www-data
        log "Reiniciando Nginx para que tome el grupo nuevo"
        run systemctl restart nginx
        echo "  www-data ahora puede tocar el socket"
    fi
fi

# --- C.9 Reverse proxy ---------------------------------------------------

HEALTHCHECK_INSECURE_VALUE=
TLS_CERT=
TLS_KEY=

# Pagina de error ESTATICA que sirve Nginx para 502/503/504. La del ejemplo
# apunta a `root /var/www/webcmp-errors` con `internal;`: si el archivo no esta,
# un Gunicorn caido produce un 404 DENTRO del manejo del error, que es el
# sintoma mas imposible de diagnosticar que existe ("la pagina de error fallo").
write_error_page() {
    local tmp
    tmp=$(mktemp)
    cat > "$tmp" <<'EOF'
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>Servicio temporalmente no disponible</title>
</head>
<body>
    <h1>Servicio temporalmente no disponible</h1>
    <p>El servicio del portal esta reiniciando o no responde en este momento.</p>
    <p>Reintentese en unos minutos.</p>
</body>
</html>
EOF
    install_if_changed "$tmp" "$NGINX_ERROR_ROOT/50x.html" 0644 root root
    rm -f "$tmp"
}

# El vhost del ejemplo, renderizado con los valores de esta instalacion.
#
# Se parte de deploy/nginx/webcmp.conf.example y no de un heredoc propio por una
# razon concreta: el ejemplo es lo que revisa la gente cuando el sitio devuelve
# 502, asi que si el vhost activo fuera OTRO archivo, cada diagnostico empezaria
# leyendo el equivocado. El render es literal (render_template), nunca regex.
render_vhost() {
    local src=$vhost_src dest=$1 tmp
    local -a pairs
    pairs=(
        # Rutas del checkout y del socket. El orden importa: /srv/webcmp va antes
        # que /srv/webcmp/staticfiles, si no el segundo par nunca se encuentra.
        "/srv/webcmp/staticfiles<>$APP_DIR/staticfiles"
        "/srv/webcmp/media<>$APP_DIR/media"
        "/srv/webcmp<>$APP_DIR"
        "/run/webcmp/gunicorn.sock<>$GUNICORN_SOCKET"
        "/var/www/webcmp-errors<>$NGINX_ERROR_ROOT"
        "/etc/nginx/certificate/web.cmw.insmet.cu.crt<>$TLS_CERT"
        "/etc/nginx/certificate/web.cmw.insmet.cu.key<>$TLS_KEY"
        "server_name web.cmw.insmet.cu;<>$SERVER_NAME_LINE"
        "listen 80 default_server;<>listen $HTTP_PORT default_server;"
        "listen [::]:80 default_server;<>listen [::]:$HTTP_PORT default_server;"
        "listen 443 ssl default_server;<>listen $HTTPS_PORT ssl default_server;"
        "listen [::]:443 ssl default_server;<>listen [::]:$HTTPS_PORT ssl default_server;"
    )
    tmp=$(mktemp)
    render_template "$src" "$tmp" "${pairs[@]}" || { rm -f "$tmp"; return 1; }
    # La redireccion de :80 a :https se mete dentro de `location /`, con la
    # excepcion de /.well-known/acme-challenge/ antes. Es lo unico que hace que
    # `certbot --webroot` funcione con este vhost: un `return 301` a nivel de
    # server se evalua ANTES de elegir location, asi que cualquier challenge de
    # ACME caeria en un redirect a https y la emision fallaria con un error que
    # no menciona el vhost.
    #
    # El `server { server_name _; }` del ejemplo es justamente esa caja: el
    # challenge se sirve por ahi, sin importar el dominio que se esta emitiendo.
    ACME_ROOT=$ACME_ROOT awk '
        /return 301 https:\/\/\$host\$request_uri;/ {
            print "        location ^~ /.well-known/acme-challenge/ {"
            print "            root " ENVIRON["ACME_ROOT"] ";"
            print "        }"
            print ""
            print "        location / {"
            sub(/^[ \t]+/, "", $0)
            print "            " $0
            print "        }"
            next
        }
        { print }
    ' "$tmp" > "$dest" || { rm -f "$tmp" "$dest"; return 1; }
    rm -f "$tmp"
}

# ngx_http_acme-challenge.conf de Debian. Su existence es lo que permite el
# `location ^~` que se acaba de agregar sin declarar `default_type`.
ensure_acme_root() {
    ensure_dir "$ACME_ROOT" 0755 www-data www-data
}

# gen_self_signed <certificado> <clave>
#
# OpenSSL, sin red: funciona con DNS privado, con puertos cerrados y en un
# servidor que todavia no tiene salida a Internet. El precio es el que ya se le
# dijo al operador: el navegador lo marca como no seguro.
gen_self_signed() {
    local cert=$1 key=$2 san="DNS:$EXTERNAL_HOSTNAME"
    [ -n "$WWW_HOSTNAME" ] && san="$san,DNS:$WWW_HOSTNAME"
    run openssl req -x509 -nodes -newkey rsa:2048 -days 825 \
        -subj "/CN=$EXTERNAL_HOSTNAME" -addext "subjectAltName=$san" \
        -keyout "$key" -out "$cert" \
        || die "No se pudo generar el certificado autofirmado en $cert."
    if [ "$DRY_RUN" -eq 0 ]; then
        chown root:root "$key" "$cert" 2>/dev/null || true
        chmod 0600 "$key" 2>/dev/null || true
        chmod 0644 "$cert" 2>/dev/null || true
    fi
}

# install_vhost <certificado> <clave>
#
# Renderiza el ejemplo, lo instala, lo habilita, verifica con `nginx -t` y
# recarga. Se llama MAS DE UNA VEZ en la primera corrida con Let's Encrypt: el
# challenge de ACME lo sirve el puerto 80 de este mismo vhost, asi que el vhost
# tiene que estar de pie antes de certbot; y un vhost con `ssl` no pasa `nginx -t`
# sin un certificado que cargar.
install_vhost() {
    TLS_CERT=$1
    TLS_KEY=$2
    local tmp

    # --- Archivo y activacion ---
    if [ -f "$vhost_src" ] || need_checkout 'el vhost se renderizaria desde deploy/nginx/webcmp.conf.example'; then
        tmp=$(mktemp)
        render_vhost "$tmp" || { rm -f "$tmp"; die "No se pudo renderizar el vhost."; }
        install_if_changed "$tmp" "$NGINX_AVAILABLE" 0644 root root
        rm -f "$tmp"
    fi

    # Nginx NO acepta dos vhost del mismo nombre en sites-enabled: el segundo se
    # ignora con un aviso que no se lee. Por eso el enlace se hace con ln -sf y no
    # con un ln a secas, que falla si ya existe (idempotencia).
    if [ -L "$NGINX_ENABLED" ]; then
        if [ "$(readlink "$NGINX_ENABLED")" != "$NGINX_AVAILABLE" ]; then
            run ln -sf "$NGINX_AVAILABLE" "$NGINX_ENABLED"
        else
            echo "  $NGINX_ENABLED ya apunta a $NGINX_AVAILABLE."
        fi
    elif [ -e "$NGINX_ENABLED" ]; then
        die "$NGINX_ENABLED existe y NO es un symlink. Decidir a mano si se reemplaza
  por un enlace a $NGINX_AVAILABLE; el instalador no borra un archivo regular."
    else
        run ln -s "$NGINX_AVAILABLE" "$NGINX_ENABLED"
    fi

    # nginx -t ANTES del reload, siempre. Un reload de una configuracion rota
    # deja al Nginx viejo sirviendo y el error queda en el log para cuando ya se
    # fue; con `nginx -t` primero, el instalador muere aca con el mensaje de Nginx.
    log "Verificando la configuracion de Nginx"
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  [dry-run] nginx -t && systemctl reload nginx\n'
    else
        nginx -t || die "La configuracion de Nginx no pasa nginx -t. No se recarga nada."
        systemctl reload nginx || die "No se pudo recargar Nginx."
        echo "  vhost activo: $NGINX_AVAILABLE"
    fi
}

setup_nginx_local() {
    SERVER_NAME_LINE="server_name $EXTERNAL_HOSTNAME;"
    if [ -n "$WWW_HOSTNAME" ]; then
        SERVER_NAME_LINE="server_name $EXTERNAL_HOSTNAME $WWW_HOSTNAME;"
    fi

    ensure_dir "$NGINX_ERROR_ROOT" 0755 root root
    write_error_page

    # --- default_server en conflicto ---
    # Va ANTES del certificado porque el conflicto lo destapa `nginx -t`, y el
    # primer `nginx -t` ya no es el ultimo: con Let's Encrypt hay una pasada
    # bootstrap antes de certbot.
    #
    # El vhost del ejemplo pide `listen 80 default_server` y `listen 443 ssl
    # default_server`. El sitio default de Debian tambien los pide, y dos
    # default_server en el mismo puerto hacen que `nginx -t` falle con
    # "a duplicate default server". No se borra a ciegas: puede estar sirviendo
    # otro sitio, asi que se pregunta y, si no, se dice que hay que resolverlo.
    # El sitio default de Debian es un symlink a sites-available/default, asi que
    # hace falta `-L` tambien: con un enlace roto, `-e` da falso y el conflicto
    # aparece despues como un fallo de nginx -t que no lo señala.
    if [ -e "$NGINX_DEFAULT_SITE" ] || [ -L "$NGINX_DEFAULT_SITE" ]; then
        log "Nginx ya tiene un sitio por defecto"
        warn "$NGINX_DEFAULT_SITE esta activo y pide los mismos puertos con"
        warn "default_server que el vhost de webcmp. Los dos no pueden levantar."
        if ask_yes_no si "Deshabilitar $NGINX_DEFAULT_SITE (se mueve a .disabled)?"; then
            run mv "$NGINX_DEFAULT_SITE" "$NGINX_DEFAULT_SITE.disabled"
            echo "  deshabilitado (el archivo quedo como $NGINX_DEFAULT_SITE.disabled)."
        else
            die "Sin resolver el conflicto de default_server, nginx -t falla y el sitio no levanta.
  Opciones: habilitar este instalador con esa pregunta en 'si', o quitar del
  vhost de webcmp las dos lineas 'default_server'."
        fi
    fi

    # --- Certificado ---
    if [ "$TLS_MODE" = self-signed ]; then
        TLS_CERT=$TLS_DIR/$EXTERNAL_HOSTNAME.crt
        TLS_KEY=$TLS_DIR/$EXTERNAL_HOSTNAME.key
        if [ -f "$TLS_CERT" ] && [ -f "$TLS_KEY" ]; then
            echo "  certificado autofirmado ya existe (no se regenera)."
        else
            gen_self_signed "$TLS_CERT" "$TLS_KEY"
        fi
        HEALTHCHECK_INSECURE_VALUE=1
        warn "Certificado AUTOFIRMADO en $TLS_CERT: el navegador lo marca como no"
        warn "seguro en cada visita y el health check de deploy.sh dejara de"
        warn "verificar el TLS (HEALTHCHECK_INSECURE=1)."
        install_vhost "$TLS_CERT" "$TLS_KEY"
    else
        # certbot con --webroot, no --standalone ni --nginx: --standalone exige
        # el puerto 80 libre (hay que parar Nginx), y --nginx reescribe el vhost
        # que este mismo script genera. Con --webroot la renovacion automatica
        # sigue funcionando porque el challenge queda en el archivo y la
        # configuracion de renovacion es de certbot, no del vhost.
        command -v certbot >/dev/null 2>&1 || {
            warn "certbot no esta instalado. Sin el no hay certificado de Let's Encrypt."
            if ask_yes_no si "Instalar certbot con apt?"; then
                if [ "$DRY_RUN" -eq 1 ]; then
                    printf '  [dry-run] apt-get install -y certbot\n'
                else
                    apt-get install -y -qq certbot \
                        || die "No se pudo instalar certbot. Instalalo a mano o elige TLS autofirmado."
                fi
            else
                die "Sin certbot no hay certificado de confianza. Volve a correr y elige 'self-signed'."
            fi
        }
        ensure_acme_root
        if ! getent hosts "$EXTERNAL_HOSTNAME" >/dev/null 2>&1; then
            warn "$EXTERNAL_HOSTNAME no resuelve desde este servidor. certbot va a fallar"
            warn "con 'Could not bind' o con un timeout de validacion: necesita que el"
            warn "DNS publico apunte a esta maquina y que los puertos esten abiertos."
        fi
        TLS_CERT=/etc/letsencrypt/live/$EXTERNAL_HOSTNAME/fullchain.pem
        TLS_KEY=/etc/letsencrypt/live/$EXTERNAL_HOSTNAME/privkey.pem
        log "Certificado de Let's Encrypt para $EXTERNAL_HOSTNAME"
        local -a certbot_args
        certbot_args=(certonly --non-interactive --agree-tos --webroot
            -w "$ACME_ROOT" --cert-name "$EXTERNAL_HOSTNAME")
        if [ -n "$ACME_EMAIL" ]; then
            certbot_args+=(--email "$ACME_EMAIL")
        else
            certbot_args+=(--register-unsafely-without-email)
            warn "Sin correo de registro en ACME: Lets Encrypt avisa que no se puede"
            warn "avisar de la expiracion del certificado."
        fi
        certbot_args+=(-d "$EXTERNAL_HOSTNAME")
        [ -n "$WWW_HOSTNAME" ] && certbot_args+=(-d "$WWW_HOSTNAME")

        if [ -f "$TLS_CERT" ] && [ -f "$TLS_KEY" ]; then
            # Ya hay certificado emitido: esta corrida es renovacion o no-op, y
            # el vhost puede cargar el certificado real de una.
            run certbot "${certbot_args[@]}" \
                || die "certbot fallo. Con --webroot necesita que el puerto $HTTP_PORT responda por $ACME_ROOT desde Internet.
  Diagnostico:  curl -I http://$EXTERNAL_HOSTNAME/.well-known/acme-challenge/  desde otra maquina.
  Alternativa:   volver a correr con TLS autofirmado y cambiar el DNS despues."
            install_vhost "$TLS_CERT" "$TLS_KEY"
        else
            # Primera emision. El challenge HTTP-01 lo responde el puerto 80 de
            # ESTE vhost, que todavia no esta instalado, y `nginx -t` no acepta
            # un `listen ... ssl` sin certificado. Por eso va primero un vhost
            # igual, con un autofirmado temporal: mismo archivo, mismo
            # `location ^~ /.well-known/acme-challenge/`, un certificado que Nginx
            # pueda cargar. El sitio queda sirviendo (con aviso del navegador)
            # durante la emision, en vez de estar caido.
            local boot_cert=$TLS_DIR/bootstrap-$EXTERNAL_HOSTNAME.crt
            local boot_key=$TLS_DIR/bootstrap-$EXTERNAL_HOSTNAME.key
            if [ ! -f "$boot_cert" ] || [ ! -f "$boot_key" ]; then
                ensure_dir "$TLS_DIR" 0755 root root
                gen_self_signed "$boot_cert" "$boot_key"
            fi
            log "Vhost temporal con certificado autofirmado, para el challenge de ACME"
            install_vhost "$boot_cert" "$boot_key"
            run certbot "${certbot_args[@]}" \
                || die "certbot fallo. Con --webroot necesita que el puerto $HTTP_PORT responda por $ACME_ROOT desde Internet.
  Diagnostico:  curl -sS -o /dev/null -w '%{http_code}\n' http://$EXTERNAL_HOSTNAME/.well-known/acme-challenge/prueba  desde otra maquina
                (probar con un archivo cualquiera en $ACME_ROOT: el codigo 404 es el esperado)
  Alternativa:   volver a correr con TLS autofirmado y cambiar el DNS despues."
            # Con el certificado real en disco, el mismo render cambia de rutas y
            # `install_if_changed` reinstala. El autofirmado temporal queda en
            # $TLS_DIR, ya sin uso: se puede borrar a mano.
            install_vhost "$TLS_CERT" "$TLS_KEY"
        fi
    fi
}

if [ "$PROXY_MODE" = external ]; then
    log "Proxy externo (Nginx Proxy Manager): NO se instala ni se toca Nginx"
    # El bloque de arriba es lo que el operador tiene que escribir en NPM. Se
    # imprime entero y no resumido: el error clasico de esta topologia es poner
    # el upstream bien y olvidar un header, y el sintoma (bucle de logout por
    # cookies seguras que no viajan) no dice "te falta X-Forwarded-Proto".
    cat <<EOF

  Datos del upstream para Nginx Proxy Manager:

    Domain Names        $EXTERNAL_HOSTNAME${WWW_HOSTNAME:+, $WWW_HOSTNAME}
    Scheme              https
    Forward Hostname    \$host
    Forward Proto       \$scheme
    Block Exploits      on
    Websockets Support  on      (el vhost de Nginx local lo deja puesto tambien)
    HTTP/2 Support      on
    SSL                 el que termine el proxy. Esta maquina NO emite
                        certificado en la opcion B: por eso el health check de
                        deploy.sh va al socket y no a https://\$EXTERNAL_HOSTNAME.

    Advanced > Custom Locations:
      /static/   ->  $APP_DIR/staticfiles/
      /media/    ->  $APP_DIR/media/

    Detalle del upstream:
      Si NPM corre en el mismo host y con acceso al sistema de archivos:
        Forward Hostname / IP  = 127.0.0.1
        Forward Port            = <puerto TCP en el que Gunicorn escuche>
        (el unit de systemd solo abre el socket unix $GUNICORN_SOCKET;
         para un upstream TCP hay que agregar un --bind tcp:127.0.0.1:<puerto>
         al ExecStart del unit y un daemon-reload)

      Si NPM corre en un contenedor: no puede ver $GUNICORN_SOCKET. Montar
      /run/$GUNICORN_UNIT del host dentro del contenedor, o usar un bind TCP en
      una IP de la LAN, no 127.0.0.1 (dentro del contenedor, 127.0.0.1 es el
      propio contenedor).

    Headers que tiene que mandar NPM (mismo criterio que el vhost de Nginx,
    que los repite en \`location /\` porque no se heredan):
      Host               = \$host
      X-Forwarded-Proto  = \$scheme
      X-Forwarded-For    = \$proxy_add_x_forwarded_for
      X-Forwarded-Host   = \$host

    Timeout / limites (copiados de deploy/nginx/webcmp.conf.example):
      proxy_read_timeout    300s     (exportacion de graficos y PDFs)
      proxy_connect_timeout 75s
      client_max_body_size  20M      (adjuntos PDF de avisos y reportes)

  Aviso importante sobre SSL y HSTS:
    production.py tiene SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https').
    Sin X-Forwarded-Proto=https, request.is_secure() da False, las cookies de
    sesion y CSRF SECURE no se envian y el usuario entra en un bucle de logout.
    SECURE_HSTS_SECONDS=31536000 con IncludeSubDomains y Preload: si NPM emite
    HSTS y despues se cae el TLS, el navegador se niega a volver en http://
    durante un ano. Habilitarlo recien cuando https este estable.

EOF
    log "Health check apuntando al upstream local"
    echo "  socket: $GUNICORN_SOCKET con Host: $EXTERNAL_HOSTNAME (sin TLS: ese lo hace el proxy)"
else
    setup_nginx_local
fi

# --- C.10 /etc/webcmp/deploy.env -----------------------------------------

log "Configuracion del deploy en $CONFIG_FILE"

# NO se pisa si existe sin confirmacion. Esta config se edita a mano
# (PUBLIC_HOSTNAME sobre todo) y pisarla en un reintento deja el health check
# pegado al host equivocado: el deploy falla aunque el sitio este perfecto.
#
# Y se escribe SIEMPRE con las claves que el health check necesita, incluso
# cuando el proxy es local y el comportamiento de deploy.sh sin tocar es
# exactamente el correcto. La alternativa (no escribir nada y dejar que el
# default se aplique) hace que la config de un servidor nuevo sea invisible:
# nadie puede ver de donde sale el host del health check.
if [ "$CONFIG_FILE_EXISTS" -eq 1 ]; then
    if ask_yes_no no "Actualizar $CONFIG_FILE con lo respondido?"; then
        warn "$CONFIG_FILE se conserva. Si el health check falla, empeza por ese archivo."
        CONFIG_WRITTEN=0
    else
        CONFIG_WRITTEN=1
    fi
else
    CONFIG_WRITTEN=1
fi

if [ "$CONFIG_WRITTEN" -eq 1 ]; then
    # Se escribe a un temporal y de ahi se instala, no con `{ ... } > "$CONFIG_FILE"`.
    # Dos razones: `install_if_changed` respeta --dry-run y compara contenido, y una
    # redireccion trivial sobreescribe siempre. Un dry-run que escribe el archivo
    # real es peor que no tener dry-run.
    CONFIG_TMP=$(mktemp)
    {
        cat <<EOF
# $CONFIG_FILE
# Escrito por deploy/install.sh. root:root 600.
# No tiene secretos: por eso puede vivir fuera del .env del sitio.
# Se reescribe solo con confirmacion, y con --configure o --check de
# webcmp-deploy. Ver deploy/README-deploy.md.
APP_DIR=$APP_DIR
DEPLOY_USER=$SERVICE_USER
GUNICORN_UNIT=$GUNICORN_UNIT
HUEY_UNIT=$HUEY_UNIT
ENCRYPTION_ENV=$ENCRYPTION_ENV
PYTHON=$VENV_DIR/bin/python
PIP=$VENV_DIR/bin/pip
PIP_CACHE_DIR=$PIP_CACHE_DIR
MPLCONFIGDIR=$MPLCONFIGDIR
PUBLIC_HOSTNAME=$EXTERNAL_HOSTNAME
PROXY_MODE=$PROXY_MODE
EOF
        if [ "$PROXY_MODE" = external ]; then
            # El health check va al socket: es el mismo camino que usa el proxy
            # externo, sin el TLS de por medio y sin depender de que el proxy
            # este arriba. Con el default (443 en 127.0.0.1) este deploy falla
            # por construccion en esta topologia.
            cat <<EOF
HEALTHCHECK_URL=http://localhost/
HEALTHCHECK_UNIX_SOCKET=$GUNICORN_SOCKET
HEALTHCHECK_HOST_HEADER=$EXTERNAL_HOSTNAME
EOF
        else
            cat <<EOF
# Sin HEALTHCHECK_UNIX_SOCKET: el health check entra a 127.0.0.1:$HTTPS_PORT con
# el SNI de $EXTERNAL_HOSTNAME y atraviesa Nginx, TLS y el socket.
HEALTHCHECK_URL=https://$EXTERNAL_HOSTNAME/
HEALTHCHECK_RESOLVE=$EXTERNAL_HOSTNAME:$HTTPS_PORT:127.0.0.1
EOF
            if [ -n "$HEALTHCHECK_INSECURE_VALUE" ]; then
                cat <<EOF
# El certificado es autofirmado. Con esto el health check deja de verificar el
# TLS: detecta menos, y es lo unico que detecta un certificado vencido.
# NUNCA en produccion real.
HEALTHCHECK_INSECURE=$HEALTHCHECK_INSECURE_VALUE
EOF
            fi
        fi
    } > "$CONFIG_TMP"
    install_if_changed "$CONFIG_TMP" "$CONFIG_FILE" 0600 root root
    rm -f "$CONFIG_TMP"
    echo "  escrito."
fi

# --- C.11 Andamiaje de deploy automatico ---------------------------------

# El andamiaje que el README anterior hacia a mano: usuario de despliegue,
# keypair, sudoers validado y webcmp-deploy en /usr/local/sbin.
setup_deploy_scaffold() {
    local tmp pubkey

    log "Andamiaje de deploy automatico (usuario $DEPLOY_LOGIN_USER)"

    if id "$DEPLOY_LOGIN_USER" >/dev/null 2>&1; then
        echo "  el usuario $DEPLOY_LOGIN_USER ya existe."
    else
        # -m: home propio, porque la clave publica que hay que copiar a GitHub
        # vive ahi y el operador no tiene por que hacer sudo cat de un 600. NO es
        # el usuario de servicio: este tiene shell y sudo acotado, aquel tiene
        # nologin y ninguna capacidad.
        run useradd --create-home --shell /bin/bash "$DEPLOY_LOGIN_USER"
        echo "  creado con shell /bin/bash."
    fi

    # La clave NUNCA se regenera si ya existe: quien la tiene publicada en GitHub
    # como secret dejaria de poder conectarse, y el sintoma (workflow en rojo por
    # "Permission denied (publickey)") no dice "rotaron la clave del servidor".
    if [ -f "$DEPLOY_SSH_KEY" ]; then
        echo "  $DEPLOY_SSH_KEY ya existe (NO se regenera)."
    else
        run ssh-keygen -t ed25519 -N '' -C "$DEPLOY_LOGIN_USER@$(hostname -s)" \
            -f "$DEPLOY_SSH_KEY" \
            || die "No se pudo generar el keypair en $DEPLOY_SSH_KEY."
        echo "  keypair ed25519 generado en $DEPLOY_SSH_KEY."
    fi
    # La privada la lee ssh como el usuario de despliegue, asi que su dueno es ese
    # usuario y el modo 600. No se usa install_if_changed porque el origen y el
    # destino son el mismo archivo y `install` se niega ("are the same file").
    if [ "$(stat -c '%U:%G %a' "$DEPLOY_SSH_KEY")" != "$DEPLOY_LOGIN_USER:$DEPLOY_LOGIN_USER 600" ]; then
        run chown "$DEPLOY_LOGIN_USER:$DEPLOY_LOGIN_USER" "$DEPLOY_SSH_KEY"
        run chmod 0600 "$DEPLOY_SSH_KEY"
    fi
    run chown "$DEPLOY_LOGIN_USER:$DEPLOY_LOGIN_USER" "$DEPLOY_SSH_KEY.pub" 2>/dev/null || true
    run chmod 0644 "$DEPLOY_SSH_KEY.pub" 2>/dev/null || true

    # El script de deploy va a /usr/local/sbin, propiedad de root, y NO a
    # $APP_DIR/deploy/deploy.sh: el checkout lo escribe $SERVICE_USER, y un
    # sudoers que apunte ahi es una escalada trivial (basta editar el archivo).
    if [ -f "$APP_DIR/deploy/deploy.sh" ] || need_checkout 'se instalaria webcmp-deploy desde deploy/deploy.sh'; then
        install_if_changed "$APP_DIR/deploy/deploy.sh" "$SCRIPT_PATH" 0755 root root
    fi

    # El sudoers se renderiza y SE VALIDA antes de instalarse. Un sudoers invalido
    # hace que sudo descarte el archivo entero con "garbage at end of line", y el
    # deploy falla con un "command not allowed" que parece de configuracion de CI.
    if [ -f "$APP_DIR/deploy/sudoers/webcmp-deploy" ] \
        || need_checkout 'el sudoers se renderizaria desde deploy/sudoers/webcmp-deploy'
    then
        tmp=$(mktemp)
        render_template "$APP_DIR/deploy/sudoers/webcmp-deploy" "$tmp" \
            "/usr/local/sbin/webcmp-deploy<>$SCRIPT_PATH" \
            "deploy ALL=(root)<>$DEPLOY_LOGIN_USER ALL=(root)" \
            || { rm -f "$tmp"; die "No se pudo renderizar el sudoers."; }
        visudo -c -f "$tmp" >/dev/null 2>&1 \
            || { visudo -c -f "$tmp"; rm -f "$tmp"; die "El sudoers renderizado no es valido: no se instalo."; }
        install_if_changed "$tmp" "$DEPLOY_SUDOERS" 0440 root root
        rm -f "$tmp"
        echo "  sudoers en $DEPLOY_SUDOERS, validado con visudo -c."
    fi

    pubkey='(en un dry-run todavia no hay clave: se imprime cuando se genere de verdad)'
    [ -f "$DEPLOY_SSH_KEY.pub" ] && pubkey=$(cat "$DEPLOY_SSH_KEY.pub")
    cat <<EOF

  Clave publica del usuario de despliegue. Copiarla al secret
  DEPLOY_SSH_KEY de GitHub (Settings > Environments > production):

$pubkey

  Si se pega con DEPLOY_HOST, DEPLOY_USER y DEPLOY_SSH_KNOWN_HOSTS, el workflow
  puede conectarse. Ver deploy/README-deploy.md.
EOF
}

if [ "$SKIP_DEPLOY_SCAFFOLD" -eq 1 ]; then
    log "Andamiaje de deploy automatico: omitido (--skip-deploy-scaffold)"
else
    setup_deploy_scaffold
fi

# --- C.12 Arranque de los servicios --------------------------------------

if [ -n "$PENDING_CHANGES" ]; then
    log "Unidades systemd"
    warn "No se arrancan $GUNICORN_UNIT ni $HUEY_UNIT: el .env esta incompleto."
    warn "Cuando se completen los valores:"
    printf '  sudo systemctl enable --now %s %s\n' "$GUNICORN_UNIT" "$HUEY_UNIT" >&2
else
    log "Arrancando $GUNICORN_UNIT y $HUEY_UNIT"
    run systemctl enable --now "$GUNICORN_UNIT"
    run systemctl enable --now "$HUEY_UNIT"
    sleep 2
    run systemctl is-active --quiet "$GUNICORN_UNIT" || warn "$GUNICORN_UNIT quedo inactivo (journalctl -u $GUNICORN_UNIT)."
    run systemctl is-active --quiet "$HUEY_UNIT" || warn "$HUEY_UNIT quedo inactivo (journalctl -u $HUEY_UNIT)."
    if [ "$PROXY_MODE" = nginx-local ]; then
        run systemctl restart nginx
        run systemctl is-active --quiet nginx || warn "nginx quedo inactivo (journalctl -u nginx)."
    fi
fi

# --- C.13 Resumen --------------------------------------------------------

echo
if [ "$DRY_RUN" -eq 1 ]; then
    echo "dry-run: no se cambio nada."
else
    echo "Instalado. Que cambio: $([ "$CHANGED" -eq 1 ] && echo 'si, algo' || echo 'nada, ya estaba')"
fi

if [ "$DRY_RUN" -eq 0 ] && [ "$INTERACTIVE" -eq 1 ] && [ "${#ANSWER_SOURCES[@]}" -gt 0 ]; then
    echo
    echo "Respuestas (los secretos van enmascarados):"
    printf '  %s\n' "${ANSWER_SOURCES[@]}"
fi

if [ "$DRY_RUN" -eq 1 ]; then
    exit 0
fi

cat <<EOF

  ======================================================================
  QUE FALTA (esta parte NO la automatiza ningun script)
  ======================================================================

  1. Secrets de GitHub (Settings > Environments > production):

       DEPLOY_HOST              IP o hostname de este servidor
       DEPLOY_USER              $DEPLOY_LOGIN_USER
       DEPLOY_SSH_KEY           contenido de $DEPLOY_SSH_KEY.pub
       DEPLOY_SSH_KNOWN_HOSTS   una linea, con el puerto si no es 22:

           ssh-keyscan -p 22 -H <host> 2>/dev/null | sed 's/^/|1 h=|/' > known_hosts

     A mano, DESPUES de un deploy de prueba:

           ssh-keyscan -H <host> 2>/dev/null | ssh-keygen -lf -

     Comparar ese fingerprint con el del del servidor. Un \`ssh-keyscan\` sin
     verificar devuelve lo que conteste ese puerto, incluido el de un atacante.

  2. Verificar el sitio y el deploy:

       sudo $SCRIPT_PATH --check
       sudo $SCRIPT_PATH \$(git -C $APP_DIR rev-parse HEAD)

     El rollback automatico no se conoce hasta que se lo vio funcionar una vez:
     probalo desplegando un commit anterior y confirmando que el sitio vuelve.

  3. Archivos que quedaron con material de clave:

       $ENV_FILE              (600 $SERVICE_USER)   SECRET_KEY cifrada, DB_PASS
       $ENCRYPTION_ENV        (600 root)             ENCRYPTION_KEY
       $CONFIG_FILE           (600 root)             sin secretos
EOF
