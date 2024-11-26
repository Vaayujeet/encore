"""Celery Settings"""

import redis
from pydantic_settings import BaseSettings


class CelerySettings(BaseSettings):
    """Celery Settings class
    Will use values from env variables else the default values.
    """

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB_NO: int = 0


celery_settings = CelerySettings()

REDIS_CLIENT = redis.Redis(
    host=celery_settings.REDIS_HOST, port=celery_settings.REDIS_PORT, db=celery_settings.REDIS_DB_NO
)

CELERY_BROKER_URL = f"redis://{celery_settings.REDIS_HOST}:{celery_settings.REDIS_PORT}/{celery_settings.REDIS_DB_NO}"
# Check https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html#extensions
CELERY_RESULT_BACKEND = (
    f"redis://{celery_settings.REDIS_HOST}:{celery_settings.REDIS_PORT}/{celery_settings.REDIS_DB_NO}"
)

# Celery Beat Scheduler
# Check https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html#using-custom-scheduler-classes
CELERY_BEAT_SCHEDULER = "correlator.celery_utils.CorrelatorScheduler"

CELERY_BEAT_MAX_LOOP_INTERVAL = 10
CELERY_BEAT_SYNC_EVERY = 1

CELERY_TASK_IGNORE_RESULT = True

# TODO: https://docs.celeryq.dev/en/stable/userguide/daemonizing.html

task_routes = {
    "elastic.tasks.ingest_event": {"queue": "api_requests"},
}
