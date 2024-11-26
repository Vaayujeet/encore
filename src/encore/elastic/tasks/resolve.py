"""Task to Resolve Event in ELK"""

import logging

from django.utils import timezone

from elastic.constants import EventExtrasKey, EventStatus, EventType, FieldNames, ResolvingAction
from elastic.models import ApiLog, Event
from elastic.utils import CorrelatorElastic
from .common import correlator_task

logger = logging.getLogger("correlator.elastic.tasks.resolve")


@correlator_task(
    name="ResolveEvent",
    model="elastic.ApiLog",
    key_value_field="api_log",
    valid_start_status={ApiLog.Status.NEW},
)
def resolve_event(*, api_log: int | ApiLog):
    """Task to Resolve the event whose ITSM was manually closed"""

    if not isinstance(api_log, ApiLog):
        return

    itsm_ticket_id = api_log.task_data[FieldNames.ITSM_TICKET]
    resolve_timestamp = api_log.created

    logger.debug("[ApiLog: %s]: Finding Alerted Event with ITSM [%s]", api_log.pk, itsm_ticket_id)
    filter_query = {
        FieldNames.EVENT_STATUS: EventStatus.ALERTED,
        FieldNames.EVENT_TYPE: EventType.DOWN,
        f"extras__{EventExtrasKey.TICKET_ID}": itsm_ticket_id,
    }
    try:
        event = Event.objects.get(**filter_query)
    except (Event.DoesNotExist, Event.MultipleObjectsReturned) as e:
        if isinstance(e, Event.DoesNotExist):
            logger.error("[ApiLog: %s]: Failed to find Alerted Event with ITSM [%s]", api_log.pk, itsm_ticket_id)
        else:
            logger.error("[ApiLog: %s]: Found multiple Alerted Events with ITSM [%s]", api_log.pk, itsm_ticket_id)
        api_log.status = ApiLog.Status.FAILED
        api_log.failure_reason = str(e)
        api_log.save()
        return
    logger.debug("[ApiLog: %s]: Found Alerted Event [%s] with ITSM [%s]", api_log.pk, event.pk, itsm_ticket_id)

    # NOTE: Since we are not locking Event row, we cannot update Event. The only way to pass this message
    # is by updating the Elastiic Event.
    es = CorrelatorElastic()
    doc = {
        FieldNames.RESOLVING_ACTION: ResolvingAction.MANUAL,
        FieldNames.LAST_UPDATE_TS: timezone.now(),
        FieldNames.MANUAL_RESOLVE_TS: resolve_timestamp,
    }
    try:
        es.update(index=event.doc_index, id=event.doc_id, doc=doc)
    except Exception as e:
        logger.error(
            "[ApiLog: %s]: Failed to Manually Resolve Alerted Event [%s] with ITSM [%s]",
            api_log.pk,
            event.pk,
            itsm_ticket_id,
        )
        api_log.status = ApiLog.Status.FAILED
        api_log.failure_reason = str(e)
        api_log.save()
        return
    api_log.status = ApiLog.Status.COMPLETED
    api_log.save()
    logger.info(
        "[ApiLog: %s]: Manually Resolved Alerted Event [%s] with ITSM [%s]", api_log.pk, event.pk, itsm_ticket_id
    )
