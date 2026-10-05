#!/bin/bash
# Worker de Huey para DESARROLLO. En produccion lo corre webcmp-huey.service (systemd),
# que no usa este script.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CONSUMER="${REPO_DIR}/.venv/bin/huey_consumer"
LOGFILE="${REPO_DIR}/logs/huey.log"

mkdir -p "$(dirname "$LOGFILE")"

if [ ! -x "$CONSUMER" ]; then
  echo "No encuentro $CONSUMER." >&2
  echo "El venv no esta instalado. Corré 'make setup' o 'pip install -r requirements/dev.txt'." >&2
  exit 1
fi

export DJANGO_SETTINGS_MODULE=config.settings
cd "$REPO_DIR"

# `config.huey_consumer_entry`, no `config.huey`: ese módulo es el que corre
# `django.setup()`, y sin él el TaskRegistry queda vacío y el worker no procesa
# nada. Ver el docstring del módulo.
exec "$CONSUMER" config.huey_consumer_entry.huey \
  --logfile="$LOGFILE" \
  --verbose
