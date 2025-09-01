#!/bin/bash

WRKDIR='../'
CONF_FILE='redis.conf'

cd $WRKDIR

redis-server $CONF_FILE