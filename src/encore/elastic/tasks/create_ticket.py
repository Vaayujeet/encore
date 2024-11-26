"""Task to process Event in Creating Ticket status"""

import logging

from django.utils import timezone

from elastic.constants import EventExtrasKey, EventStatus, EventType, FieldNames, ResolvingAction
from elastic.models import Event
from elastic.tasks.common import correlator_task
from elastic.utils import CorrelatorElastic
from glpi.constants import GLPI_TICKET_SEVERITY_MAP
from glpi.utils import GLPIException, create_ticket, get_glpi_session, kill_glpi_session

logger = logging.getLogger("correlator.elastic.tasks.create_ticket")


class DefaultNA(dict):
    """If a key is missing in a dict, return "N/A" value."""

    def __missing__(self, key):
        return "N/A"


@correlator_task(
    name="CreateTicketEvent",
    model="elastic.Event",
    key_value_field="event",
    valid_start_status={EventStatus.CREATING_TICKET},
    valid_start_types={EventType.DOWN},
    logger=logger,
)
def process_creating_ticket_event(event: int | Event):
    """Logic to process Event in Creating Ticket status."""

    if not isinstance(event, Event):
        return

    es = CorrelatorElastic()

    if not (elk_event := event.elastic_event):
        event.report_error("Elastic Event Does not Exist [Task: CreateTicketEvent]")
        return
    elk_event_src = elk_event["_source"]

    # Is Linked?
    if FieldNames.LINKED_EVENT in elk_event_src and elk_event_src[FieldNames.LINKED_EVENT]:
        # Mark Down Events as Resolving
        logger.debug("Moving Linked Down Event to Resolving: %s", event.doc_id)
        doc = {
            FieldNames.EVENT_STATUS: EventStatus.RESOLVING,
            FieldNames.RESOLVING_ACTION: ResolvingAction.NEW,
            FieldNames.LAST_UPDATE_TS: timezone.now(),
        }
        try:
            es.update(index=event.doc_index, id=event.doc_id, doc=doc)
        except Exception as e:
            event.report_error(f"Failed to Move Linked Down Event to Resolving [Task: CreateTicketEvent]. Reason: {e}")
            logger.error("Failed to Move Linked Down Event to Resolving: %s [Reason: %s]", event.doc_id, e)
            return
        event.status = EventStatus.RESOLVING
        event.retry_count = 0
        event.save()
        logger.info("Moved Linked Down Event to Resolving: %s", event.doc_id)
        return

    if event.extras.get(EventExtrasKey.TICKET_ID, None):
        logger.debug("Already Created Ticket: %s [%s]", event.doc_id, event.extras[EventExtrasKey.TICKET_ID])
    elif event.do_not_create_ticket_flag:
        logger.debug("Do not Create Ticket: %s", event.doc_id)
        event.extras[EventExtrasKey.TICKET_ID] = 0
        event.extras[EventExtrasKey.TICKET_COMMENT_ASSET_IS_DOWN] = True
    else:
        logger.debug("Creating Ticket: %s", event.doc_id)
        itsm_settings = event.itsm_settings
        itsm_title = (
            itsm_settings.itsm_title.format_map(DefaultNA(**elk_event_src))
            if itsm_settings.itsm_title and itsm_settings.itsm_title.strip()
            else elk_event_src[FieldNames.EVENT_TITLE]
        )
        itsm_description = (
            itsm_settings.itsm_desc.format_map(DefaultNA(**elk_event_src))
            if itsm_settings.itsm_desc and itsm_settings.itsm_desc.strip()
            else elk_event_src[FieldNames.EVENT_DESC]
        )

        try:
            glpi_session = get_glpi_session()
            event.extras[EventExtrasKey.TICKET_ID] = create_ticket(
                session=glpi_session,
                title=itsm_title,
                desc=itsm_description,
                assigned_group_id=itsm_settings.itsm_assignment_group_uid,
                severity=GLPI_TICKET_SEVERITY_MAP[
                    itsm_settings.itsm_severity if itsm_settings.itsm_severity in {1, 2, 3, 4} else 4
                ],
                my_custom_field=es.get_nested_field_value(elk_event, "itsm_settings.my.custom.field"),
            )
            kill_glpi_session(glpi_session)
        except GLPIException as e:
            event.report_error(f"Failed to Create Ticket Event [Task: NewDownEvent]. Reason: {e}")
            logger.error("Failed to Create Ticket Event: %s [Reason: %s]", event.doc_id, e)
            return
        event.extras[EventExtrasKey.TICKET_COMMENT_ASSET_IS_DOWN] = True
        logger.debug("Created Ticket: %s [%s]", event.doc_id, event.extras[EventExtrasKey.TICKET_ID])

    # Update ITSM
    # Mark Events as Alerted
    doc = {
        FieldNames.ITSM_TICKET: event.extras[EventExtrasKey.TICKET_ID],
        FieldNames.EVENT_STATUS: EventStatus.ALERTED,
        FieldNames.LAST_UPDATE_TS: timezone.now(),
    }
    try:
        es.update(index=event.doc_index, id=event.doc_id, doc=doc)
    except Exception as e:
        event.report_error(f"Failed to Move Down Event to Alerted [Task: NewDownEvent]. Reason: {e}")
        logger.error("Failed to Move Down Event to Alerted: %s [Reason: %s]", event.doc_id, e)
        return
    event.status = EventStatus.ALERTED
    event.retry_count = 0
    event.save()
    logger.debug("Moved Down Event to Alerted: %s", event.doc_id)
