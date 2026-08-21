#!/bin/bash
NAME="webcmp"
DJANGODIR=$(cd `dirname $0` && pwd)
SOCKFILE=/tmp/gunicorn-webcmp.sock
LOGDIR=${DJANGODIR}/logs/gunicorn.log
# El usuario del servicio NO debe ser root. El usuario dedicado (p.ej. webcmp)
# debe ser el propietario del venv, media/, staticfiles/ y logs/ para poder
# escribir el socket y servir estáticos.
USER=${GUNICORN_USER:-webcmp}
GROUP=${GUNICORN_GROUP:-webcmp}
NUM_WORKERS=5
DJANGO_WSGI_MODULE=config.wsgi

rm -frv $SOCKFILE

echo $DJANGODIR

cd $DJANGODIR

exec ${DJANGODIR}/.venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=$LOGDIR
