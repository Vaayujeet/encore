#!/bin/sh
celery -A correlator flower &
tail -f /dev/null
