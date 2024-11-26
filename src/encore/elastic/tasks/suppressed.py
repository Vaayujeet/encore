"""Task to process Suppressed Event."""

import logging

from django.utils import timezone

from elastic.constants import EventStatus, EventType, FieldNames, ResolvingAction
from elastic.models import Event
from elastic.tasks.common import correlator_task, itsm_activity
from elastic.utils import CorrelatorElastic

logger = logging.getLogger("correlator.elastic.tasks.suppressed")


@correlator_task(
    name="SupressedDownEvent",
    model="elastic.Event",
    key_value_field="event",
    valid_start_status={EventStatus.SUPPRESSED},
    valid_start_types={EventType.DOWN},
    logger=logger,
)
def process_suppressed_event(event: int | Event):
    """Logic to process Supressed Down event."""

    if not isinstance(event, Event):
        return

    es = CorrelatorElastic()

    if not (elk_event := event.elastic_event):
        event.report_error("Elastic Event Does not Exist [Task: SuppressedDownEvent]")
        return
    elk_event_src = elk_event["_source"]

    # Suppressed to New?
    if elk_event_src.get(FieldNames.SUPP_TO_NEW, False):
        logger.debug("Moving Suppressed Event to New status: %s", event.doc_id)
        doc = {
            FieldNames.EVENT_STATUS: EventStatus.NEW,
            FieldNames.SUPP_TO_NEW: False,
            FieldNames.PARENT_EVENT: None,
            FieldNames.PARENT_EVENT_INDEX: None,
            FieldNames.LAST_UPDATE_TS: timezone.now(),
        }
        try:
            es.update(index=event.doc_index, id=event.doc_id, doc=doc)
        except Exception as e:
            event.report_error(f"Failed to Move Suppressed Event to New status. Reason: {e}")
            logger.error("Failed to Move Suppressed Event to New status: %s [Reason: %s]", event.doc_id, e)
            return
        event.status = EventStatus.NEW
        event.retry_count = 0
        event.save()
        logger.debug("Moved Suppressed Event to New status: %s", event.doc_id)
        return

    # Is Manually Resolved?
    if elk_event_src.get(FieldNames.RESOLVING_ACTION, None) == ResolvingAction.MANUAL:
        # Mark Down Event as Manually Resolving.
        logger.debug("Moving Down Event to Manually Resolving: %s", event.doc_id)
        doc = {
            FieldNames.EVENT_STATUS: EventStatus.RESOLVING,
            FieldNames.LAST_UPDATE_TS: timezone.now(),
        }
        try:
            es.update(index=event.doc_index, id=event.doc_id, doc=doc)
        except Exception as e:
            event.report_error(f"Failed to Move Down Event to Manually Resolving [Task: AlertedDownEvent]. Reason: {e}")
            logger.error("Failed to Move Down Event to Manually Resolving: %s [Reason: %s]", event.doc_id, e)
            return
        event.status = EventStatus.RESOLVING
        event.retry_count = 0
        event.save()
        logger.info("Moved Down Event to Manually Resolving: %s", event.doc_id)
        return

    # Is Linked?
    if FieldNames.LINKED_EVENT in elk_event_src and elk_event_src[FieldNames.LINKED_EVENT]:
        # Mark Down Events as Resolving. ITSM Activity will be done in Resolving status.
        logger.debug("Moving Linked Down Event to Resolving: %s", event.doc_id)
        doc = {
            FieldNames.EVENT_STATUS: EventStatus.RESOLVING,
            FieldNames.RESOLVING_ACTION: ResolvingAction.SUPP,
            FieldNames.LAST_UPDATE_TS: timezone.now(),
        }
        try:
            es.update(index=event.doc_index, id=event.doc_id, doc=doc)
        except Exception as e:
            event.report_error(
                f"Failed to Move Linked Down Event to Resolving [Task: SuppressedDownEvent]. Reason: {e}"
            )
            logger.error("Failed to Move Linked Down Event to Resolving: %s [Reason: %s]", event.doc_id, e)
            return
        event.status = EventStatus.RESOLVING
        event.retry_count = 0
        event.save()
        logger.info("Moved Linked Down Event to Resolving: %s", event.doc_id)
        return

    itsm_activity(event=event, elk_event_src=elk_event_src, logger=logger)

    logger.debug("Retry Down Event: %s", event.doc_id)
    event.retry_count += 1
    event.save()
