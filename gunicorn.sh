#!/bin/bash

NAME="webcmp"
DJANGODIR=$(cd `dirname $0` && pwd)

echo "Iniciando ${NAME} en ${DJANGODIR}"

cd $DJANGODIR

exec ${DJANGODIR}/.venv/bin/gunicorn core.wsgi:application --bind django.aceitecmg.alinet.cu:8000 --workers 3

