#!/usr/bin/env bash
# Instala en el servidor el andamiaje del despliegue por workflow. Se corre UNA
# vez por servidor; despues el deploy es automatico.
#
#   sudo ./deploy/install.sh              # instala
#   sudo ./deploy/install.sh --dry-run    # muestra que haria, sin tocar nada
#
# Que instala, y por que en este orden:
#   1. usuario de despliegue + su keypair SSH
#   2. webcmp-deploy en /usr/local/sbin (FUERA del checkout, por seguridad)
#   3. /etc/webcmp/deploy.env (la config; NO se pisa si ya existe)
#   4. sudoers acotado a UN comando, validado ANTES de instalarlo
#   5. www-data en el grupo webcmp, para que Nginx toque el socket de Gunicorn
#
# Es idempotente: correrlo dos veces no cambia nada y no rompe lo que ya esta
# armado. Eso importa por dos motivos. Uno practico: el README de este repo tiene
# pasos que no funcionan como estan escritos (ver deploy/README-deploy.md), asi que
# es probable que alguien tenga que correr esto mas de una vez. El otro, de fondo:
# cada paso que regenera un secreto o pisa una config editada a mano convierte un
# reintento en un incidente.
#
# Lo que este script NO hace, a proposito: generar el .env, crear el venv, instalar
# los prerrequisitos de sistema, ni tocar Nginx o los certificados. Son cosas que
# dependen del dominio real y del estado del servidor, y automatizarlas a ciega
# deja mas basura que las que recoge. El procedimiento esta en
# deploy/README-deploy.md, secciones "Prerrequisitos de sistema" e
# "Instalacion en el servidor".

set -Eeuo pipefail

# Sin `readonly X=$(...)`: la declaracion y la asignacion en una sola linea
# esconde el codigo de salida del comando substitutions, asi que un `cd` que
# fallara pasaria por alto y REPO_DIR quedaria vacio, con lo que todos los
# `install` de abajo escriben donde no es.
REPO_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
readonly REPO_DIR

# Valores por defecto. Todos overridables por variable de entorno, para no tener
# que editar el script en un servidor con otro layout.
DEPLOY_LOGIN_USER=${DEPLOY_LOGIN_USER:-deploy}
SERVICE_USER=${SERVICE_USER:-webcmp}
SCRIPT_PATH=${SCRIPT_PATH:-/usr/local/sbin/webcmp-deploy}
CONFIG_DIR=${CONFIG_DIR:-/etc/webcmp}
CONFIG_FILE=${CONFIG_FILE:-$CONFIG_DIR/deploy.env}
PIP_CACHE_DIR=${PIP_CACHE_DIR:-/var/cache/webcmp-pip}

DRY_RUN=0
CHANGED=0

log()  { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mAVISO:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

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
    sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

# Sin argumentos instala. El uso se imprime solo con -h/--help: hacer que la
# invocacion mas comun del script caiga en la ayuda es la forma de que nadie lo
# use para lo que sirve.
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run|-n) DRY_RUN=1 ;;
        -h|--help)    usage 0 ;;
        *)            die "Opcion desconocida: $1 (--help para el uso)." ;;
    esac
    shift
done

# --------------------------------------------------------------------------
# Preflight
# --------------------------------------------------------------------------

[ "$(id -u)" -eq 0 ] || die "Hay que correrlo como root (sudo)."

for f in deploy/deploy.sh deploy/deploy.env.example deploy/sudoers/webcmp-deploy; do
    [ -f "$REPO_DIR/$f" ] || die "Falta $REPO_DIR/$f: corelo desde un checkout del repo."
done

command -v visudo >/dev/null 2>&1 || die "visudo no esta instalado (paquete sudo)."
command -v useradd >/dev/null 2>&1 || die "useradd no esta instalado (paquete passwd)."

[ "$DRY_RUN" -eq 1 ] || [ -d "$REPO_DIR/.git" ] \
    || warn "$REPO_DIR no parece un checkout de git; se instala igual."

# --------------------------------------------------------------------------
# 1. Usuario de despliegue
# --------------------------------------------------------------------------

log "Usuario de despliegue: $DEPLOY_LOGIN_USER"

if id "$DEPLOY_LOGIN_USER" >/dev/null 2>&1; then
    echo "  ya existe (shell: $(getent passwd "$DEPLOY_LOGIN_USER" | cut -d: -f7))"
else
    # -m y NO -r: este usuario tiene shell y su keypair SSH privada vive en su
    # home. El usuario de servicio (webcmp) es el contrario, y por eso NO se usa
    # aqui: si el deploy se pusiera en manos de webcmp, quien puede tocar el
    # checkout podria tambien loguearse en el servidor.
    run useradd -m -s /bin/bash "$DEPLOY_LOGIN_USER"
    # El home se relee del passwd y no se hardcodea: /home/<user> es lo que
    # instala useradd -m en un Linux comun, pero no esta garantizado, y un
    # mensaje que dice "en /home/deploy" cuando el archivo quedo en otro lado
    # manda a debuggear la ruta equivocada.
    if home=$(getent passwd "$DEPLOY_LOGIN_USER" | cut -d: -f6) && [ -n "$home" ]; then
        echo "  creado con home en $home"
    else
        echo "  creado"
    fi
fi

ensure_dir "/home/$DEPLOY_LOGIN_USER/.ssh" 0700 "$DEPLOY_LOGIN_USER" "$DEPLOY_LOGIN_USER"

sshkey="/home/$DEPLOY_LOGIN_USER/.ssh/id_ed25519"
if [ -f "$sshkey" ]; then
    # Regenerarla invalidaria el secret DEPLOY_SSH_KEY de GitHub al instante, y
    # el rollback a mano del paso siguiente no lo arregla. Solo se avisa.
    warn "Ya existe $sshkey; se conserva. Si se regenera, hay que volver a"
    warn "publicar la clave publica como secret DEPLOY_SSH_KEY."
else
    # Generada COMO el usuario de despliegue, no como root. Corriendo como root
    # el keypair queda en root:root y el usuario despues no puede ni leerlo ni
    # rotarlo sin sudo, que es lo contrario de lo que un directorio 0700 en su
    # home promises. Solo se publica la .pub, asi que el bug es invisible hasta
    # que alguien quiere cambiar la clave.
    # -N "" : sin passphrase, porque el workflow no tiene forma de tipearla.
    run_sh "sudo -u '$DEPLOY_LOGIN_USER' ssh-keygen -q -t ed25519 -C 'github-actions-deploy' -N '' -f '$sshkey'"
    echo "  clave publica para GitHub: $sshkey.pub"
fi

# --------------------------------------------------------------------------
# 2. El script, FUERA del checkout
# --------------------------------------------------------------------------

log "Script de deploy en $SCRIPT_PATH"

# El padre primero. `install` no crea directorios intermedios: si SCRIPT_PATH
# apunta a algo cuyo padre no existe, install aborta con "No such file or
# directory" y, como el usuario de despliegue ya se creo en el punto 1, deja el
# servidor a medio instalar. En los defaults (/usr/local/sbin, /etc/webcmp) esto
# no se ve porque ambos existen de antemano; se ve apenas alguien cambia la ruta.
ensure_dir "$(dirname "$SCRIPT_PATH")" 0755 root root

# Root y 0755, no ejecutable por webcmp. Si el script viviera en el checkout, que
# es escribible por el usuario de servicio, editarlo seria obtener root con el
# sudoers del punto 4. Ver el comentario de deploy/sudoers/webcmp-deploy.
install_if_changed "$REPO_DIR/deploy/deploy.sh" "$SCRIPT_PATH" 0755

bash -n "$REPO_DIR/deploy/deploy.sh" \
    || die "deploy.sh tiene error de sintaxis; no se instalo nada de este punto."
echo "  sintaxis OK"

# --------------------------------------------------------------------------
# 3. Config
# --------------------------------------------------------------------------

log "Config en $CONFIG_FILE"

# El directorio sale del archivo, no de una variable aparte: si alguien pasa
# CONFIG_FILE=/tmp/x.env para probar, crear /etc/webcmp igual seria un efecto
# secundario de una prueba.
ensure_dir "$(dirname "$CONFIG_FILE")" 0755 root root

if [ -f "$CONFIG_FILE" ]; then
    # NO se sobreescribe. Esta config se edita a mano (PUBLIC_HOSTNAME sobre
    # todo) y pisarla en un reintento deja el health check pegado al host
    # equivocado: el deploy falla aunque el sitio este perfecto.
    warn "$CONFIG_FILE ya existe; se conserva. Revisar PUBLIC_HOSTNAME."
    grep -E '^[A-Z_]+=' "$CONFIG_FILE" 2>/dev/null | sed 's/^/  /' || true
else
    install_if_changed "$REPO_DIR/deploy/deploy.env.example" "$CONFIG_FILE" 0600
    cat <<EOF

  Ahora hay que editarlo, como root:

      sudo nano $CONFIG_FILE

  Lo unico que no tiene default correcto es PUBLIC_HOSTNAME: tiene que coincidir
  con el \`server_name\` de Nginx y con el EXTERNAL_HOSTNAME del .env del sitio.
  Con un nombre distinto, el health check entra a 127.0.0.1:443 con un SNI que
  no corresponde al certificado y el deploy falla aunque el sitio ande bien.
EOF
fi

# Cache de pip. Sin esto, cada deploy vuelve a descargar todas las dependencias
# desde PyPI: `webcmp` es cuenta de sistema sin home, asi que pip no encuentra
# donde escribir ~/.cache. Ver la nota de PIP_CACHE_DIR en deploy.env.example.
ensure_dir "$PIP_CACHE_DIR" 0700 "$SERVICE_USER" "$SERVICE_USER"
echo "  cache de pip en $PIP_CACHE_DIR (0700 $SERVICE_USER)"

# --------------------------------------------------------------------------
# 4. Sudoers
# --------------------------------------------------------------------------

log "Sudoers para $DEPLOY_LOGIN_USER"

# El archivo del repo tiene el usuario escrito a mano, no con una variable: sudo
# no expande nada. Con un DEPLOY_LOGIN_USER distinto de `deploy` el archivo
# instala igual (es identico byte a byte, asi que install_if_changed lo saltea) y
# el resultado es un usuario de despliegue sin sudo, que se descubre en el
# primer deploy con un "command not allowed" que no habla de sudoers.
if ! grep -qE "^[[:space:]]*${DEPLOY_LOGIN_USER}[[:space:]]+ALL=" "$REPO_DIR/deploy/sudoers/webcmp-deploy"; then
    warn "deploy/sudoers/webcmp-deploy no concede sudo a '$DEPLOY_LOGIN_USER'."
    warn "El archivo tiene el usuario escrito a mano (sudo no expande variables)."
    warn "Editar $REPO_DIR/deploy/sudoers/webcmp-deploy y cambiar las dos lineas"
    warn "finales por '$DEPLOY_LOGIN_USER ALL=(root) NOPASSWD: ...', o dejar"
    warn "DEPLOY_LOGIN_USER=deploy y usar el nombre que el repo ya tiene."
    [ "$DRY_RUN" -eq 1 ] || die "No se instalo el sudoers: no serviria de nada."
fi

# Se valida el ARCHIVO fuente antes de copiarlo. Si /etc/sudoers.d/webcmp-deploy
# esta roto, sudo descarta el archivo entero: el deploy queda sin sudo y el
# error que aparece ("command not allowed") no menciona para nada el sudoers.
if visudo -c -f "$REPO_DIR/deploy/sudoers/webcmp-deploy" >/dev/null 2>&1; then
    echo "  el archivo del repo es valido"
    install_if_changed "$REPO_DIR/deploy/sudoers/webcmp-deploy" \
        /etc/sudoers.d/webcmp-deploy 0440
    # Re-validar sobre el archivo INSTALADO, no sobre el del repo: lo que importa
    # es lo que va a leer sudo.
    if visudo -c >/dev/null 2>&1; then
        echo "  sudoers global OK"
    else
        die "visudo -c falla con el archivo ya instalado. Se dejo puesto para
     poder diagnosticar; sudo lo va a descartar hasta arreglarlo.
     Revisar: sudo visudo -c"
    fi
else
    visudo -c -f "$REPO_DIR/deploy/sudoers/webcmp-deploy" || true
    die "El sudoers del repo es invalido; NO se instalo (visudo -c -f para ver el error)."
fi

# --------------------------------------------------------------------------
# 5. www-data en el grupo webcmp
# --------------------------------------------------------------------------

log "Permisos del socket de Gunicorn"

if id -nG www-data 2>/dev/null | tr ' ' '\n' | grep -qx "$SERVICE_USER"; then
    echo "  www-data ya esta en el grupo $SERVICE_USER"
elif [ "$DRY_RUN" -eq 1 ]; then
    printf '  [dry-run] usermod -aG %s www-data\n' "$SERVICE_USER"
else
    # El socket de Gunicorn sale 0770 webcmp:webcmp, asi que sin esto Nginx no
    # llega a tocarlo y cada respuesta es 502 con "Permission denied" en el log,
    # que parece un problema de permisos que no lo es.
    run usermod -aG "$SERVICE_USER" www-data
    # restart y NO reload: los grupos supplemental se leen al crear los workers,
    # asi que un reload deja los workers viejos con la lista anterior.
    log "Reiniciando Nginx para que tome el grupo nuevo"
    run systemctl restart nginx
    echo "  www-data ahora puede tocar el socket"
fi

# --------------------------------------------------------------------------
# Resumen
# --------------------------------------------------------------------------

echo
if [ "$DRY_RUN" -eq 1 ]; then
    echo "dry-run: no se cambio nada."
else
    echo "Instalado. Que cambio: $([ "$CHANGED" -eq 1 ] && echo 'si, algo' || echo 'nada, ya estaba')"
fi

cat <<EOF

Falta (no lo hace este script):

  - El .env del sitio. Se genera como root, porque no puede escribir
    /etc/webcmp/encryption.env, y despues hay que devolverle el .env a
    $SERVICE_USER. Ver deploy/README-deploy.md, "Un paso del README del
    proyecto que no funciona como esta escrito".
  - EXTERNAL_HOSTNAME, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS y
    CORS_ALLOWED_ORIGINS con el dominio real. El generador escribe
    EXTERNAL_HOSTNAME=cmw.insmet.cu y no tiene flag para cambiarlo; si queda
    asi, el sitio responde DisallowedHost a cada peticion.
  - Nginx (vhost + certificado) y las unidades systemd de deploy/systemd/.
  - Los prerrequisitos de sistema: build-essential, libpango1.0-dev,
    redis-server y los demas de la tabla del README.

Secrets de GitHub (Settings > Environments > production):

  DEPLOY_HOST              IP o hostname de este servidor
  DEPLOY_USER              $DEPLOY_LOGIN_USER
  DEPLOY_SSH_KEY           contenido de $sshkey.pub
  DEPLOY_SSH_KNOWN_HOSTS   una linea, con el puerto si no es 22:

      ssh-keyscan -p 22 -H <host> 2>/dev/null | sed 's/^/|1 h=|/' > known_hosts

  A mano, DESPUES de un deploy de prueba:

      ssh-keyscan -H <host> 2>/dev/null | ssh-keygen -lf -

  Comparar ese fingerprint con el del servidor. Un \`ssh-keyscan\` sin
  verificar devuelve lo que conteste ese puerto, incluido el de un atacante.

Probar el deploy antes de tocar los secrets:

  sudo $SCRIPT_PATH \$(git -C $REPO_DIR rev-parse HEAD)
EOF
