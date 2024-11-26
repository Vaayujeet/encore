"""Task to process Event in Resolving status"""

import logging

from django.utils import timezone

from elastic.constants import EventExtrasKey, EventStatus, EventType, FieldNames, ResolvingAction
from elastic.models import Event
from elastic.tasks.common import (
    all_immediate_active_child_events_are_set_as_new,
    all_immediate_child_events_are_resolved,
    all_immediate_child_events_are_resolved_manually,
    correlator_task,
    itsm_activity,
)
from elastic.utils import CorrelatorElastic
from glpi.utils import GLPIException, add_comment, close_ticket, get_glpi_session, kill_glpi_session

logger = logging.getLogger("correlator.elastic.tasks.resolving")


@correlator_task(
    name="ResolvingEvent",
    model="elastic.Event",
    key_value_field="event",
    valid_start_status={EventStatus.RESOLVING},
    valid_start_types={EventType.DOWN},
    logger=logger,
)
def process_resolving_event(event: int | Event):
    """Logic to process Event in Resolving status."""

    if not isinstance(event, Event):
        return

    es = CorrelatorElastic()

    if not (elk_event := event.elastic_event):
        event.report_error("Elastic Event Does not Exist [Task: ResolvingEvent]")
        return
    elk_event_src = elk_event["_source"]

    if elk_event_src[FieldNames.RESOLVING_ACTION] in (ResolvingAction.CLOSE_TICKET, ResolvingAction.SUPP):
        itsm_activity(event=event, elk_event_src=elk_event_src, logger=logger)
        if event.extras.get(EventExtrasKey.TICKET_COMMENT_ASSET_IS_UP, False) is False:
            logger.debug("ITSM Activity is not complete. Retry Down Event: %s", event.doc_id)
            event.retry_count += 1
            event.save()
            return

        if not all_immediate_child_events_are_resolved(event=event, logger=logger):
            logger.debug("Not all child Events are resolved. Retry Down Event: %s", event.doc_id)
            event.retry_count += 1
            event.save()
            return
    if elk_event_src[FieldNames.RESOLVING_ACTION] == ResolvingAction.NEW:
        if not all_immediate_active_child_events_are_set_as_new(event=event, logger=logger):
            logger.info("Not all child Events are properly processed. Retry Down Event: %s", event.doc_id)
            event.retry_count += 1
            event.save()
            return
    if elk_event_src[FieldNames.RESOLVING_ACTION] == ResolvingAction.MANUAL:
        # INFO: ITSM Activity is ignored in this case.
        if not all_immediate_child_events_are_resolved_manually(
            event=event, manual_resolve_ts=elk_event_src[FieldNames.MANUAL_RESOLVE_TS], logger=logger
        ):
            logger.debug("Not all child Events are (manually) resolved. Retry Down Event: %s", event.doc_id)
            event.retry_count += 1
            event.save()
            return

    if (
        elk_event_src[FieldNames.RESOLVING_ACTION] == ResolvingAction.CLOSE_TICKET
        and elk_event_src[FieldNames.ITSM_TICKET]
    ):
        logger.debug("Closing Ticket [%s]: %s", elk_event_src[FieldNames.ITSM_TICKET], event.doc_id)
        comment = "All assets that report this issue have now Resolved. Closing the Ticket."
        try:
            glpi_session = get_glpi_session()
            add_comment(session=glpi_session, ticket_id=elk_event_src[FieldNames.ITSM_TICKET], comment=comment)
            close_ticket(session=glpi_session, ticket_id=elk_event_src[FieldNames.ITSM_TICKET])
            kill_glpi_session(glpi_session)
        except GLPIException as e:
            event.report_error(f"Failed to Close Ticket [{elk_event_src[FieldNames.ITSM_TICKET]}]. Reason: {e}")
            logger.error(
                "Failed to Close Ticket [%s]: %s [Reason: %s]", elk_event_src[FieldNames.ITSM_TICKET], event.doc_id, e
            )
            event.retry_count += 1
            event.save()
            return
        logger.info("Closed Ticket [%s]: %s", elk_event_src[FieldNames.ITSM_TICKET], event.doc_id)

    # Mark Event as Resolved
    doc = {FieldNames.EVENT_STATUS: EventStatus.RESOLVED, FieldNames.LAST_UPDATE_TS: timezone.now()}
    try:
        es.update(index=event.doc_index, id=event.doc_id, doc=doc)
    except Exception as e:
        event.report_error(f"Failed to Resolve Event [Task: ResolvingEvent]. Reason: {e}")
        logger.error("Failed to Resolve Event: %s [Reason: %s]", event.doc_id, e)
        return
    event.status = EventStatus.RESOLVED
    event.save()
    logger.info("Resolved Event: %s", event.doc_id)
