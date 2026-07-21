#!/bin/bash
NAME="webcmp-huey"
DJANGODIR=$(cd `dirname $0` && pwd)
LOGDIR=${DJANGODIR}/logs/huey.log
export DJANGO_SETTINGS_MODULE=config.settings

cd $DJANGODIR

${DJANGODIR}/.venv/bin/huey_consumer config.huey.huey \
  --logfile=$LOGDIR \
  --verbose
