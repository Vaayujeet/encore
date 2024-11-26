"""Celery specific setup for django app"""

import logging
import os

from celery import Celery

# logger
logger = logging.getLogger("correlator")

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "correlator.settings")

app = Celery("correlator")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Used for debug purpose to check if celery is properly setup."""
    logger.info("Request: %s", self.request)


def only_one_task_at_a_time(function=None, key: str = "", timeout_in_seconds: int | None = None):
    """Enforce only one celery task at a time."""

    def _dec(run_func):
        """Decorator."""

        def _caller(celery_task, *args, **kwargs):
            """Caller.
            NOTE: Since we are adding `celery_task`. the `args` or `kwargs` might not work properly.
            """
            from django.conf import settings  # pylint: disable=import-outside-toplevel

            task_id = celery_task.request.id
            ret_value = None
            have_lock = False

            # TODO: Use different locking based on different brokers/dbs
            lock = settings.REDIS_CLIENT.lock(key, timeout=timeout_in_seconds)
            logger.debug("Acquiring lock for Celery Task Key: %s[%s]", key, task_id)
            try:
                have_lock = lock.acquire(blocking=False)
                if have_lock:
                    logger.debug("Acquired lock for Celery Task Key: %s[%s]", key, task_id)
                    ret_value = run_func(*args, **kwargs)
                else:
                    # logging
                    logger.warning("Could not acquire lock for Celery Task Key: %s[%s]", key, task_id)
            finally:
                if have_lock:
                    # NOTE: If the Lock timed out before the run_func finished executing,
                    # below statement will raise redis.exceptions.LockNotOwnedError
                    logger.debug("Releasing lock for Celery Task Key: %s[%s]", key, task_id)
                    lock.release()
                    logger.debug("Released lock for Celery Task Key: %s[%s]", key, task_id)

            return ret_value

        return _caller

    return _dec(function) if function is not None else _dec
