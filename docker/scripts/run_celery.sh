#!/bin/sh
celery -A correlator beat -l info &
celery -A correlator worker -l info &
python manage.py runserver 0.0.0.0:8000 &
python manage.py start_snmp_listener &
tail -f /dev/null
