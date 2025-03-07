#!/bin/bash

NAME="webcmp"
DJANGODIR=$(cd `dirname $0` && pwd)
SOCKFILE=/tmp/gunicorn-webcmp.sock
LOGDIR=${DJANGODIR}/logs/gunicorn.log
USER=root
GROUP=root
NUM_WORKERS=5
DJANGO_WSGI_MODULE=core.wsgi

export http_proxy=http://10.1.107.5:3128
export https_proxy=http://10.1.107.5:3128

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
