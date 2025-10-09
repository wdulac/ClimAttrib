#!/bin/bash

WORKDIR="../src/"
APPLICATION="utils.tasks"
LOGLEVEL="INFO"

# Not sure how to stop gracefully... `pkill -f "celery"` ?
celery --workdir $WORKDIR -A $APPLICATION worker --loglevel=$LOGLEVEL --concurrency=1 --pool=solo --hostname=worker1@%h --without-heartbeat &
celery --workdir $WORKDIR -A $APPLICATION worker --loglevel=$LOGLEVEL --concurrency=1 --pool=solo --hostname=worker2@%h --without-heartbeat &
