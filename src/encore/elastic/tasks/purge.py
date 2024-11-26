"""Tasks to purge old data."""

import logging
from datetime import timedelta

from celery import shared_task
from celery.schedules import crontab

from django.utils import timezone

from correlator.celery import only_one_task_at_a_time
from correlator.celery_utils import CorrelatorPeriodicTask
from elastic.constants import COMPLETE_EVENT_STATUS, EVENT_INDEX_RE
from elastic.models import ApiLog, Event
from elastic.utils import CorrelatorElastic

logger = logging.getLogger("correlator.elastic.tasks.purge")


@shared_task(name="PurgeEventsApiLogs", base=CorrelatorPeriodicTask, run_every=crontab(minute=0, hour=2), bind=True)
@only_one_task_at_a_time(key="PurgeEventsApiLogs", timeout_in_seconds=60 * 3)
def purge_db_events_and_apilogs(days: int = 30):
    """Task to remove old Events and Api Logs from Database."""
    logger.info("Purging Events and Api Logs")
    purge_cutoff_ts = timezone.now() - timedelta(days=days)
    e = Event.objects.filter(api_log__created__date__lt=purge_cutoff_ts, status__in=COMPLETE_EVENT_STATUS).delete()
    a = ApiLog.objects.filter(created__date__lt=purge_cutoff_ts, event__id__isnull=True).delete()
    logger.info("Purged Events and Api Logs: [%s], [%s]", e, a)


@shared_task(name="PurgeEventIndices", base=CorrelatorPeriodicTask, run_every=crontab(minute=0, hour=2), bind=True)
@only_one_task_at_a_time(key="PurgeEventIndices", timeout_in_seconds=60 * 3)
def purge_event_indices(days=365):
    """Task to remove old Events from Elastic."""
    es = CorrelatorElastic()
    response = es.indices.get(index=EVENT_INDEX_RE)
    event_indices = list(response.keys())
    for event_index in event_indices:
        if es.event_index_age(event_index, days) and not es.index_has_active_event_document(event_index):
            logger.debug("Deleting Event Index: %s", event_index)
            es.indices.delete(index=event_index)
            logger.info("Deleted Event Index: %s", event_index)
        else:
            logger.debug("Event Index Skipped: %s", event_index)
