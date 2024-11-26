
# Dockerfile

# The first instruction is what image we want to base our container on
FROM python:3.12

# Allows docker to cache installed dependencies between builds
RUN mkdir -p /mnt/application/encore
RUN mkdir -p /mnt/application/scripts

# PIP install psycopg3
# https://www.psycopg.org/psycopg3/docs/basic/install.html#local-installation
RUN pip install "psycopg[c]"

# PIP install requirements
COPY ./src/requirements.txt /mnt/application/requirements.txt
RUN pip install --no-cache-dir -r /mnt/application/requirements.txt

# Copy Run Celery script
COPY --chown=root:root --chmod=700 /docker/scripts/run_celery.sh /mnt/application/scripts

WORKDIR /mnt/application/encore

# runs the production server
ENTRYPOINT ["bash", "/mnt/application/scripts/run_celery.sh"]
