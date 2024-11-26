"""Task to process Alerted Event."""

import logging

from django.utils import timezone

from elastic.constants import EventExtrasKey, EventStatus, EventType, FieldNames, ResolvingAction
from elastic.models import Event
from elastic.tasks.common import correlator_task
from elastic.utils import CorrelatorElastic

logger = logging.getLogger("correlator.elastic.tasks.alerted")


@correlator_task(
    name="AlertedDownEvent",
    model="elastic.Event",
    key_value_field="event",
    valid_start_status={EventStatus.ALERTED},
    valid_start_types={EventType.DOWN},
    logger=logger,
)
def process_alerted_event(event: int | Event):
    """Logic to process Alerted Down event."""

    if not isinstance(event, Event):
        return

    es = CorrelatorElastic()

    if not (elk_event := event.elastic_event):
        event.report_error("Elastic Event Does not Exist [Task: AlertedDownEvent]")
        return
    elk_event_src = elk_event["_source"]

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
        # Mark Down Events as Resolving [Close Ticket].
        logger.debug("Moving Linked Down Event to Resolving [Close Ticket]: %s", event.doc_id)
        doc = {
            FieldNames.EVENT_STATUS: EventStatus.RESOLVING,
            FieldNames.RESOLVING_ACTION: ResolvingAction.CLOSE_TICKET,
            FieldNames.LAST_UPDATE_TS: timezone.now(),
        }
        try:
            es.update(index=event.doc_index, id=event.doc_id, doc=doc)
        except Exception as e:
            event.report_error(
                f"Failed to Move Linked Down Event to Resolving [Close Ticket] [Task: AlertedDownEvent]. Reason: {e}"
            )
            logger.error(
                "Failed to Move Linked Down Event to Resolving [Close Ticket]: %s [Reason: %s]", event.doc_id, e
            )
            return
        event.status = EventStatus.RESOLVING
        event.retry_count = 0
        event.save()
        logger.info("Moved Linked Down Event to Resolving [Close Ticket]: %s", event.doc_id)
        return

    logger.debug("Retry Down Event: %s", event.doc_id)
    event.retry_count += 1
    event.save()
