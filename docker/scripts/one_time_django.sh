# Execute below commands in the django container first time it is started and then restart the container.
# Later, update the ELASTIC_CERT_FINGERPRINT variable in correlator->settings->elastic.py->if ELASTIC_CONTAINER: block

cd /mnt/application/encore

python manage.py migrate

export DJANGO_SUPERUSER_PASSWORD="correlator"
python manage.py createsuperuser --username correlator --email admin@encore.com --noinput

python manage.py shell_plus <<EOF
s = Site.objects.first()
s.domain = "localhost"
s.save()
EOF