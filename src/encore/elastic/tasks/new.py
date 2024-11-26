"""Task to process New Event."""

import logging

from django.utils import timezone

from elastic.constants import (
    ACTIVE_EVENT_STATUS,
    EVENT_INDEX_RE,
    EventExtrasKey,
    EventStatus,
    EventType,
    FieldNames,
    ResolvingAction,
)
from elastic.models import Event
from elastic.tasks.common import correlator_task
from elastic.utils import CorrelatorElastic, SearchResponseType

logger = logging.getLogger("correlator.elastic.tasks.new")


@correlator_task(
    name="NewUpEvent",
    model="elastic.Event",
    key_value_field="event",
    valid_start_status={EventStatus.NEW},
    valid_start_types={EventType.UP},
    logger=logger,
)
def process_new_up_event(event: int | Event):
    """Logic to process New Up event."""

    if not isinstance(event, Event):
        return

    es = CorrelatorElastic()

    if not (elk_event := event.elastic_event):
        event.report_error("Elastic Event Does not Exist [Task: NewUpEvent]")
        return
    elk_event_src = elk_event["_source"]

    logger.debug("Finding Active Down Event: %s", event.doc_id)
    search_query = {
        "bool": {
            "must_not": {"exists": {"field": FieldNames.LINKED_EVENT}},
            "must": [
                {"term": {f"{FieldNames.EVENT_TYPE}.keyword": EventType.DOWN}},
                {"range": {FieldNames.EVENT_TS: {"lte": elk_event_src[FieldNames.EVENT_TS]}}},
                {"term": {f"{FieldNames.TOOL_NAME}.keyword": elk_event_src[FieldNames.TOOL_NAME]}},
                {"term": {f"{FieldNames.EVENT_TITLE}.keyword": elk_event_src[FieldNames.EVENT_TITLE]}},
                {
                    "term": {
                        f"{FieldNames.ASSET_UNIQUE_ID}.keyword": {
                            "value": elk_event_src[FieldNames.ASSET_UNIQUE_ID],
                            "case_insensitive": True,
                        }
                    }
                },
            ],
            "should": [{"term": {f"{FieldNames.EVENT_STATUS}.keyword": _estatus}} for _estatus in ACTIVE_EVENT_STATUS],
            "minimum_should_match": 1,
        }
    }
    elk_down_events = es.search(
        index=EVENT_INDEX_RE,
        query=search_query,
        sort=[{FieldNames.EVENT_TS: {"order": "desc"}}],
        size=1000,
        response_type=SearchResponseType.HIT_LIST,
    )

    if elk_down_events:
        # Link Up and Down Events
        # Mark Up Event as Resolved

        logger.debug("Found Active Down Event: %s -> %s", event.doc_id, elk_down_events[0]["_id"])
        _update_ts = timezone.now()
        down_doc = {
            FieldNames.LINKED_EVENT: event.doc_id,
            FieldNames.LINKED_EVENT_INDEX: event.doc_index,
            FieldNames.LAST_UPDATE_TS: _update_ts,
        }

        up_doc = {
            FieldNames.LINKED_EVENT: elk_down_events[0]["_id"],
            FieldNames.LINKED_EVENT_INDEX: elk_down_events[0]["_index"],
            FieldNames.EVENT_STATUS: EventStatus.RESOLVED,
            FieldNames.LAST_UPDATE_TS: _update_ts,
        }

        try:
            # First Update the UP Event in Elastic
            es.update(index=event.doc_index, id=event.doc_id, doc=up_doc)
            # Then Update the latest Down Event in Elastic
            es.update(index=elk_down_events[0]["_index"], id=elk_down_events[0]["_id"], doc=down_doc)
        except Exception as e:
            event.report_error(f"Failed to Link Event [Task: NewUpEvent]. Reason: {e}")
            logger.error("Failed to Link Event: %s -> %s [Reason: %s]", event.doc_id, elk_down_events[0]["_id"], e)
            return

        # Now Update rest of the Down Events (if any) in Elastic
        ops = []
        for elk_down_event in elk_down_events[1:]:
            ops.extend(
                [
                    {"update": {"_index": elk_down_event["_index"], "_id": elk_down_event["_id"]}},
                    {"doc": down_doc},
                ]
            )
        if ops:
            try:
                es.bulk(operations=ops)
            except Exception as e:
                event.report_error(
                    f"Failed to Link Additional Events [Task: NewUpEvent]. Reason: {e}",
                    incr_flag=False,
                    check_repeat_count=False,
                )
                logger.warning(
                    "Failed to Link Additional Events: %s -> %s [Reason: %s]",
                    event.doc_id,
                    elk_down_events[0]["_id"],
                    e,
                )

        # Finally Update the Up Event in Postgres
        event.status = EventStatus.RESOLVED
        event.save()
        logger.info("Linked and Resolved Up Event: %s -> %s", event.doc_id, elk_down_events[0]["_id"])
    else:
        if event.retry_count:  # is >0
            logger.warning("Failed to find Active Down Event: %s", event.doc_id)
            doc = {
                FieldNames.EVENT_STATUS: EventStatus.ERROR,
                FieldNames.ERROR_REASON: "Missing Down Event",
                FieldNames.LAST_UPDATE_TS: timezone.now(),
            }
            try:
                # Mark Up Event as Error[Missing Down Event]
                es.update(index=event.doc_index, id=event.doc_id, doc=doc)
            except Exception as e:
                event.report_error(f"Failed to Un-Resolved Up Event [Task: NewUpEvent]. Reason: {e}")
                logger.error("Failed to Un-Resolved Up Event: %s [Reason: %s]", event.doc_id, e)
                return
            event.status = EventStatus.ERROR
            logger.debug("Un-Resolved Up Event: %s", event.doc_id)
        else:
            logger.debug("Retry Up Event: %s", event.doc_id)
            event.retry_count += 1
        event.save()


@correlator_task(
    name="NewDownEvent",
    model="elastic.Event",
    key_value_field="event",
    valid_start_status={EventStatus.NEW},
    valid_start_types={EventType.DOWN},
    logger=logger,
)
def process_new_down_event(event: int | Event):
    """Logic to process New Down event."""

    if not isinstance(event, Event):
        return

    es = CorrelatorElastic()

    if not (elk_event := event.elastic_event):
        event.report_error("Elastic Event Does not Exist [Task: NewDownEvent]")
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
            event.report_error(f"Failed to Move Linked Down Event to Resolving [Task: NewDownEvent]. Reason: {e}")
            logger.error("Failed to Move Linked Down Event to Resolving: %s [Reason: %s]", event.doc_id, e)
            return
        event.status = EventStatus.RESOLVING
        event.retry_count = 0
        event.save()
        logger.info("Moved Linked Down Event to Resolving: %s", event.doc_id)
        return

    # Is Duplicate?
    # TODO: Can dedup be done at the time of ingestion?
    if event.retry_count < 3 and (elk_initial_event := _get_elk_initial_event(es, elk_event)):
        # Link Initial Event
        # Mark Down Events as Deduped
        logger.debug("Linking Initial and Deduping Down Event: %s -> %s", event.doc_id, elk_initial_event["_id"])
        doc = {
            FieldNames.INITIAL_EVENT: elk_initial_event["_id"],
            FieldNames.INITIAL_EVENT_INDEX: elk_initial_event["_index"],
            FieldNames.EVENT_STATUS: EventStatus.DEDUPED,
            FieldNames.LAST_UPDATE_TS: timezone.now(),
        }
        try:
            es.update(index=event.doc_index, id=event.doc_id, doc=doc)
        except Exception as e:
            event.report_error(
                f"Failed to Link Initial and Dedup Down Event [{elk_initial_event["_id"]}]"
                + f"[Task: NewDownEvent]. Reason: {e}"
            )
            logger.error(
                "Failed to Link Initial and Dedup Down Event: %s -> %s [Reason: %s]",
                event.doc_id,
                elk_initial_event["_id"],
                e,
            )
            return
        event.status = EventStatus.DEDUPED
        event.save()
        logger.info("Linked Initial and Deduped Down Event: %s -> %s", event.doc_id, elk_initial_event["_id"])
        return

    elk_parent_down_event = None
    if (
        # Parent-Child Lookup is Required
        event.parent_child_lookup_required
        # Asset has a valid Parent defined in Asset Mapping
        and FieldNames.PARENT_ASSET_UNIQUE_ID in elk_event_src
        and elk_event_src[FieldNames.PARENT_ASSET_UNIQUE_ID]
    ):
        logger.debug("Finding Active Parent Down Event: %s", event.doc_id)
        search_query = {
            "bool": {
                "must_not": {"exists": {"field": FieldNames.LINKED_EVENT}},
                "must": [
                    {"term": {f"{FieldNames.EVENT_TYPE}.keyword": EventType.DOWN}},
                    {"term": {f"{FieldNames.TOOL_NAME}.keyword": elk_event_src[FieldNames.TOOL_NAME]}},
                    {"term": {f"{FieldNames.EVENT_TITLE}.keyword": elk_event_src[FieldNames.EVENT_TITLE]}},
                    {
                        "term": {
                            f"{FieldNames.ASSET_UNIQUE_ID}.keyword": {
                                "value": elk_event_src[FieldNames.PARENT_ASSET_UNIQUE_ID],
                                "case_insensitive": True,
                            }
                        }
                    },
                ],
                "should": [
                    {"term": {f"{FieldNames.EVENT_STATUS}.keyword": _estatus}} for _estatus in ACTIVE_EVENT_STATUS
                ],
                "minimum_should_match": 1,
            }
        }

        elk_parent_down_event = es.search(
            index=EVENT_INDEX_RE,
            query=search_query,
            sort=[{FieldNames.EVENT_TS: {"order": "asc"}}],
            response_type=SearchResponseType.FIRST_HIT,
        )

    if elk_parent_down_event:
        logger.debug("Found Active Parent Down Event: %s -> %s", event.doc_id, elk_parent_down_event["_id"])
        # Link Parent Event
        # Mark Down Events as Suppressed
        doc = {
            FieldNames.PARENT_EVENT: elk_parent_down_event["_id"],
            FieldNames.PARENT_EVENT_INDEX: elk_parent_down_event["_index"],
            FieldNames.EVENT_STATUS: EventStatus.SUPPRESSED,
            FieldNames.LAST_UPDATE_TS: timezone.now(),
        }
        # Copy ITSM Ticket Info if available
        if FieldNames.ITSM_TICKET in elk_parent_down_event["_source"]:
            doc[FieldNames.ITSM_TICKET] = elk_parent_down_event["_source"][FieldNames.ITSM_TICKET]

        try:
            es.update(index=event.doc_index, id=event.doc_id, doc=doc)
        except Exception as e:
            event.report_error(
                f"Failed to Link Parent and Suppress Down Event [{elk_parent_down_event["_id"]}]"
                + f"[Task: NewDownEvent]. Reason: {e}"
            )
            logger.error(
                "Failed to Link Parent and Suppress Down Event: %s -> %s [Reason: %s]",
                event.doc_id,
                elk_parent_down_event["_id"],
                e,
            )
            return
        event.status = EventStatus.SUPPRESSED
        if FieldNames.ITSM_TICKET in elk_parent_down_event["_source"]:
            event.extras[EventExtrasKey.TICKET_ID] = elk_parent_down_event["_source"][FieldNames.ITSM_TICKET]
        event.retry_count = 0
        event.save()
        logger.info("Linked Parent and Suppressed Down Event: %s -> %s", event.doc_id, elk_parent_down_event["_id"])
    else:
        # Either Parent Child Lookup is not required OR
        # Asset does not have a valid Parent defined in Asset Mapping OR
        # NO Active Down event received for Parent Asset

        # Check wait time before creating a ticket
        if (timezone.now() - event.event_ts).total_seconds() > event.wait_time_in_seconds:
            logger.debug("Moving Down Event to Creating Ticket: %s", event.doc_id)
            doc = {FieldNames.EVENT_STATUS: EventStatus.CREATING_TICKET, FieldNames.LAST_UPDATE_TS: timezone.now()}
            try:
                # Mark Down Event as Creating Ticket
                es.update(index=event.doc_index, id=event.doc_id, doc=doc)
            except Exception as e:
                event.report_error(f"Failed to Move Down Event to Creating Ticket [Task: NewDownEvent]. Reason: {e}")
                logger.error("Failed to Move Down Event to Creating Ticket: %s [Reason: %s]", event.doc_id, e)
                return
            event.status = EventStatus.CREATING_TICKET
            event.retry_count = 0
            logger.debug("Moved Down Event to Creating Ticket: %s", event.doc_id)
        else:
            logger.debug("Retry Down Event: %s", event.doc_id)
            event.retry_count += 1
        event.save()


# Helper Functions used in process_new_down_event - Start


def _get_elk_initial_event(es: CorrelatorElastic, elk_event):
    elk_event_src = elk_event["_source"]
    logger.debug("Finding Active Initial Down Event: %s", elk_event["_id"])
    search_query = {
        "bool": {
            "must_not": {"exists": {"field": FieldNames.LINKED_EVENT}},
            "must": [
                {"term": {f"{FieldNames.EVENT_TYPE}.keyword": EventType.DOWN}},
                {"range": {FieldNames.EVENT_TS: {"lte": elk_event_src[FieldNames.EVENT_TS]}}},
                {"term": {f"{FieldNames.TOOL_NAME}.keyword": elk_event_src[FieldNames.TOOL_NAME]}},
                {"term": {f"{FieldNames.EVENT_TITLE}.keyword": elk_event_src[FieldNames.EVENT_TITLE]}},
                {
                    "term": {
                        f"{FieldNames.ASSET_UNIQUE_ID}.keyword": {
                            "value": elk_event_src[FieldNames.ASSET_UNIQUE_ID],
                            "case_insensitive": True,
                        }
                    }
                },
            ],
            "should": [{"term": {f"{FieldNames.EVENT_STATUS}.keyword": _estatus}} for _estatus in ACTIVE_EVENT_STATUS],
            "minimum_should_match": 1,
        }
    }

    if elk_initial_event := es.search(
        index=EVENT_INDEX_RE,
        query=search_query,
        sort=[{FieldNames.EVENT_TS: {"order": "asc"}}],
        response_type=SearchResponseType.FIRST_HIT,
    ):
        if elk_initial_event["_id"] != elk_event["_id"]:
            logger.debug("Found Active Initial Down Event: %s --> %s", elk_event["_id"], elk_initial_event["_id"])
            return elk_initial_event
    logger.debug("Could not find Active Initial Down Event: %s", elk_event["_id"])
    return None


# Helper Functions used in process_new_down_event - End


# def _process_new_neutral_events(es: Elasticsearch, draft_neutral_event):
#     """Logic to process New Neutral event."""

#     logger.info("Processing New Neutral Event: %s", draft_neutral_event["_id"])

#     if not (fair_neutral_event := get_corresponding_fair_event(es, draft_neutral_event, "Process New Neutral Events")):
#         # Failed to extract corresponding Fair Event
#         return

#     # TODO: Process Neutral Events
#     # Mark Neutral Events as UnProcessed for now.
#     doc = {FieldNames.EVENT_STATUS: EventStatus.UNPROCESSED, FieldNames.LAST_UPDATE_TS: timezone.now()}
#     es.bulk(
#         operations=[
#             {"update": {"_index": fair_neutral_event["_index"], "_id": fair_neutral_event["_id"]}},
#             {"doc": doc},
#             {"update": {"_index": draft_neutral_event["_index"], "_id": draft_neutral_event["_id"]}},
#             {"doc": doc},
#         ]
#     )
#     logger.info("Processed New Neutral Event: %s", fair_neutral_event["_id"])
