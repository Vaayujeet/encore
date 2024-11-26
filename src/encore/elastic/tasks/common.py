"""Common Functions for Elastic Tasks"""

import logging
import typing as t

from celery import shared_task

from django.apps import apps
from django.db import transaction
from django.db.transaction import on_commit
from django.db.utils import OperationalError
from django.utils import timezone

from elastic.constants import EVENT_INDEX_RE, EventExtrasKey, EventStatus, EventType, FieldNames, ResolvingAction
from elastic.models import Event
from elastic.utils import CorrelatorElastic, SearchResponseType
from glpi.utils import GLPIException, add_comment, get_glpi_session, kill_glpi_session

elastic_task_logger = logging.getLogger("correlator.elastic.tasks")


def correlator_task(
    name: str,
    model: str,
    key_value_field: str,
    model_key_field: str = "pk",
    valid_start_status: t.Optional[t.Set[str]] = None,
    valid_start_types: t.Optional[t.Set[str]] = None,
    logger: logging.Logger = elastic_task_logger,
):
    """Create a Correlator Shared Task (decorator)

    NOTE: Do not use this decorator to define PeriodicTasks. Use `CorrelatorPeriodicTask` as the base class
    with `shared_task` decorator to define PeriodicTasks.

    """

    def _dec(run_func):
        """Decorator"""

        @shared_task(name=name, bind=True)
        @transaction.atomic
        def _caller(celery_task, **kwargs):
            """Caller"""
            model_class = apps.get_model(model)
            model_id = kwargs.get(key_value_field)

            logger.debug(
                "[%s][%s]: %s [%s] Starting",
                celery_task.request.id,
                name,
                model_class.__name__,
                model_id,
            )

            model_qs = model_class.objects.select_for_update(nowait=True).filter(**{model_key_field: model_id})

            try:
                if len(model_qs) == 0:
                    logger.error(
                        "[%s][%s]: %s [%s] does not exist.",
                        celery_task.request.id,
                        name,
                        model_class.__name__,
                        model_id,
                    )
                    return
            except OperationalError as e:
                logger.warning(
                    "[%s][%s]: Failed to get lock on %s: %s. Reason: [%s]",
                    celery_task.request.id,
                    name,
                    model_class.__name__,
                    model_id,
                    e,
                )
                if model_class == Event:
                    Event.objects.get(pk=model_id).report_error(f"Failed to get lock [Task: {name}]", incr_flag=False)
                return

            model_ins = model_qs[0]
            if valid_start_status and model_ins.status not in valid_start_status:
                logger.warning(
                    "[%s][%s]: %s [%s] Invalid Status [%s].",
                    celery_task.request.id,
                    name,
                    model_class.__name__,
                    model_id,
                    model_ins.status,
                )
                if model_class == Event:
                    Event.objects.get(pk=model_id).report_error(f"Invalid Status [Task: {name}]", incr_flag=False)
                return
            if valid_start_types and model_ins.event_type not in valid_start_types:
                logger.warning(
                    "[%s][%s]: %s [%s] Invalid Event Type [%s].",
                    celery_task.request.id,
                    name,
                    model_class.__name__,
                    model_id,
                    model_ins.event_type,
                )
                if model_class == Event:
                    Event.objects.get(pk=model_id).report_error(f"Invalid Event Type [Task: {name}]", incr_flag=False)
                return

            kwargs[key_value_field] = model_ins
            run_func(**kwargs)

            if model_class == Event:
                task_handler(model_ins)

            logger.debug(
                "[%s][%s]: %s [%s] Completed",
                celery_task.request.id,
                name,
                model_class.__name__,
                model_id,
            )

        return _caller

    return _dec


def task_handler(event: Event):
    """Handle Task"""
    if event.status == EventStatus.NEW:
        if event.event_type == EventType.DOWN:
            from .new import process_new_down_event  # pylint: disable=import-outside-toplevel

            on_commit(lambda: process_new_down_event.apply_async(kwargs={"event": event.pk}, countdown=10))
            elastic_task_logger.debug("Invoked New Down Event: [%s]", event.pk)
        elif event.event_type == EventType.UP:
            from .new import process_new_up_event  # pylint: disable=import-outside-toplevel

            on_commit(lambda: process_new_up_event.apply_async(kwargs={"event": event.pk}, countdown=10))
            elastic_task_logger.debug("Invoked New Up Event: [%s]", event.pk)
        else:
            elastic_task_logger.debug("Event [%s] is Inactive [%s]", event.pk, event.status)
    elif event.status == EventStatus.ALERTED:
        from .alerted import process_alerted_event  # pylint: disable=import-outside-toplevel

        on_commit(lambda: process_alerted_event.apply_async(kwargs={"event": event.pk}, countdown=30))
        elastic_task_logger.debug("Invoked Alerted Down Event: [%s]", event.pk)
    elif event.status == EventStatus.SUPPRESSED:
        from .suppressed import process_suppressed_event  # pylint: disable=import-outside-toplevel

        countdown = 30 if event.extras.get(EventExtrasKey.TICKET_COMMENT_ASSET_IS_DOWN, False) else 10
        on_commit(lambda: process_suppressed_event.apply_async(kwargs={"event": event.pk}, countdown=countdown))
        elastic_task_logger.debug("Invoked Suppressed Down Event: [%s]", event.pk)
    elif event.status == EventStatus.CREATING_TICKET:
        from .create_ticket import process_creating_ticket_event  # pylint: disable=import-outside-toplevel

        on_commit(lambda: process_creating_ticket_event.apply_async(kwargs={"event": event.pk}, countdown=10))
        elastic_task_logger.debug("Invoked Creating Ticket Down Event: [%s]", event.pk)
    elif event.status == EventStatus.RESOLVING:
        from .resolving import process_resolving_event  # pylint: disable=import-outside-toplevel

        on_commit(lambda: process_resolving_event.apply_async(kwargs={"event": event.pk}, countdown=30))
        elastic_task_logger.debug("Invoked Resolving Ticket Down Event: [%s]", event.pk)
    else:
        elastic_task_logger.debug("Event [%s] is Inactive [%s]", event.pk, event.status)


def itsm_activity(event: Event, elk_event_src, logger=elastic_task_logger):
    """Perform ITSM activity for Suppressed / Resolving(Supp/CloseTicket) Events"""

    es = CorrelatorElastic()
    if event.extras.get(EventExtrasKey.TICKET_ID, None) is None:
        # First get the Ticket ID [not possible for CloseTicket]
        logger.debug(
            "Getting Ticket ID from Parent Event: %s -> %s", event.doc_id, elk_event_src[FieldNames.PARENT_EVENT]
        )
        if not (
            elk_parent_event := es.get_event(
                event_index=elk_event_src[FieldNames.PARENT_EVENT_INDEX],
                event_id=elk_event_src[FieldNames.PARENT_EVENT],
            )
        ):
            event.report_error(f"Parent Event [{elk_event_src[FieldNames.PARENT_EVENT]}] Does not Exist.")
            logger.error("Parent Event Does not Exist: %s -> %s", event.doc_id, elk_event_src[FieldNames.PARENT_EVENT])
            return

        if elk_parent_event["_source"].get(FieldNames.ITSM_TICKET, None) is None:
            logger.debug(
                "Parent Event does not have Ticket: %s -> %s", event.doc_id, elk_event_src[FieldNames.PARENT_EVENT]
            )
            return

        event.extras[EventExtrasKey.TICKET_ID] = elk_parent_event["_source"][FieldNames.ITSM_TICKET]
        logger.debug("Got Ticket ID [%s]: %s", event.extras[EventExtrasKey.TICKET_ID], event.doc_id)

    # We have the Ticket ID
    if elk_event_src.get(FieldNames.ITSM_TICKET, None) is None:
        # Ticket ID is not updated in Elastic for this event. Do it. [not possible for CloseTicket]
        logger.debug("Updating Ticket ID in Elastic: %s", event.doc_id)
        doc = {
            FieldNames.ITSM_TICKET: event.extras[EventExtrasKey.TICKET_ID],
            FieldNames.LAST_UPDATE_TS: timezone.now(),
        }
        try:
            es.update(index=event.doc_index, id=event.doc_id, doc=doc)
        except Exception as e:
            event.report_error(f"Failed to Update Ticket ID in Elastic. Reason: {e}")
            logger.error("Failed to Update Ticket ID in Elastic: %s [Reason: %s]", event.doc_id, e)
            return
        logger.debug("Updated Ticket ID [%s] in Elastic: %s", event.extras[EventExtrasKey.TICKET_ID], event.doc_id)

    # Ticket ID is updated in Elastic. Now, child events can fetch the Ticket ID.
    if not event.extras[EventExtrasKey.TICKET_ID]:
        event.extras[EventExtrasKey.TICKET_COMMENT_ASSET_IS_DOWN] = True
        if event.status == EventStatus.RESOLVING:
            event.extras[EventExtrasKey.TICKET_COMMENT_ASSET_IS_UP] = True
        logger.debug("Do Not Create Ticket Flag is Set: %s", event.doc_id)
        return

    comment = None
    if event.extras.get(EventExtrasKey.TICKET_COMMENT_ASSET_IS_DOWN, False) is False:
        # Whether status is Suppressed or Resolving, add the Down comment.
        # This is always Child Asset. For Topmost Parent Asset, Down comment is added at ticket creation.
        comment = f"Child Asset `{event.asset_unique_id}` has reported similar issue at {event.event_ts}."

    if (
        event.status == EventStatus.RESOLVING
        and event.extras.get(EventExtrasKey.TICKET_COMMENT_ASSET_IS_UP, False) is False
    ):
        # Add appropriate Up comment
        if elk_event_src[FieldNames.RESOLVING_ACTION] == ResolvingAction.CLOSE_TICKET:
            # Topmost Asset that reported this issue has resolved. Down comment was added at ticket creation.
            comment = f"Asset `{event.asset_unique_id}` which reported this issue is now Resolved."
        elif event.extras.get(EventExtrasKey.TICKET_COMMENT_ASSET_IS_DOWN, False) is False:
            # For this Child Asset, append the Up comment.
            comment += " but it is now Resolved."
        else:
            # For this Child Asset, add only the Up comment
            comment = f"Child Asset `{event.asset_unique_id}` which had reported similar issue is now Resolved."

    if comment:
        # Add comment in GLPI.
        logger.debug("Adding comment to Ticket [%s]: %s", event.extras[EventExtrasKey.TICKET_ID], event.doc_id)
        try:
            glpi_session = get_glpi_session()
            add_comment(session=glpi_session, ticket_id=event.extras[EventExtrasKey.TICKET_ID], comment=comment)
            kill_glpi_session(glpi_session)
        except GLPIException as e:
            event.report_error(
                f"Failed to Add comment to Ticket [{event.extras[EventExtrasKey.TICKET_ID]}]. Reason: {e}"
            )
            logger.error(
                "Failed to Add comment to Ticket [%s]: %s [Reason: %s]",
                event.extras[EventExtrasKey.TICKET_ID],
                event.doc_id,
                e,
            )
            return
        event.extras[EventExtrasKey.TICKET_COMMENT_ASSET_IS_DOWN] = True
        if event.status == EventStatus.RESOLVING:
            event.extras[EventExtrasKey.TICKET_COMMENT_ASSET_IS_UP] = True
        logger.debug("Added comment to Ticket [%s]: %s", event.extras[EventExtrasKey.TICKET_ID], event.doc_id)


def all_immediate_child_events_are_resolved(event: Event, logger=elastic_task_logger) -> bool:
    """Check if all immediate child events are Resolved. Used by Resolving (Supp/CloseTicket) Events"""
    es = CorrelatorElastic()
    if es.search(
        index=EVENT_INDEX_RE,
        query={
            "bool": {
                "must": [
                    {"term": {f"{FieldNames.EVENT_TYPE}.keyword": EventType.DOWN}},
                    {"term": {f"{FieldNames.PARENT_EVENT}.keyword": event.doc_id}},
                ],
                "should": [
                    {"term": {f"{FieldNames.EVENT_STATUS}.keyword": EventStatus.SUPPRESSED}},
                    {"term": {f"{FieldNames.EVENT_STATUS}.keyword": EventStatus.RESOLVING}},
                ],
                "minimum_should_match": 1,
            }
        },
        source_excludes=FieldNames.EVENT_DETAILS,
        size=1,
        response_type=SearchResponseType.FIRST_HIT,
    ):
        logger.debug("Active Child Event present: %s", event.doc_id)
        return False
    return True


def all_immediate_child_events_are_resolved_manually(
    event: Event,
    manual_resolve_ts,
    logger=elastic_task_logger,
) -> bool:
    """Check if all immediate child events are Resolved. Manually Resolve them if they are yet not Resolved.
    Used by Resolving (Manual) Events
    """
    es = CorrelatorElastic()
    ret_value = True
    for elk_child_event in es.search(
        index=EVENT_INDEX_RE,
        query={
            "bool": {
                "must": [
                    {"term": {f"{FieldNames.EVENT_TYPE}.keyword": EventType.DOWN}},
                    {"term": {f"{FieldNames.PARENT_EVENT}.keyword": event.doc_id}},
                ],
                "should": [
                    {"term": {f"{FieldNames.EVENT_STATUS}.keyword": EventStatus.SUPPRESSED}},
                    {"term": {f"{FieldNames.EVENT_STATUS}.keyword": EventStatus.RESOLVING}},
                ],
                "minimum_should_match": 1,
            }
        },
        source_excludes=FieldNames.EVENT_DETAILS,
        response_type=SearchResponseType.HIT_LIST,
    ):
        if elk_child_event["_source"].get(FieldNames.RESOLVING_ACTION, None) != ResolvingAction.MANUAL:
            # Set Resolving Action to MANUAL
            logger.debug("Setting Resolving Action to MANUAL [%s]: %s", elk_child_event["_id"], event.doc_id)
            doc = {
                FieldNames.RESOLVING_ACTION: ResolvingAction.MANUAL,
                FieldNames.LAST_UPDATE_TS: timezone.now(),
                FieldNames.MANUAL_RESOLVE_TS: manual_resolve_ts,
            }
            try:
                es.update(index=elk_child_event["_index"], id=elk_child_event["_id"], doc=doc)
            except Exception as e:
                event.report_error(f"Failed to Set Resolving Action to MANUAL. Reason: {e}")
                logger.error(
                    "Failed to Set Resolving Action to MANUAL [%s]: %s [Reason: %s]",
                    elk_child_event["_id"],
                    event.doc_id,
                    e,
                )
                ret_value = False
            else:
                logger.debug("Done Setting Resolving Action to MANUAL [%s]: %s", elk_child_event["_id"], event.doc_id)
    return ret_value


def all_immediate_active_child_events_are_set_as_new(event: Event, logger=elastic_task_logger) -> bool:
    """Move all immediate active child Events to appropriate status and return appropriate boolean response.
    Suppressed child Events are moved to NEW status
    Resolving (Supp) child Events are moved to Resolving (New) status
    """

    es = CorrelatorElastic()
    ret_value = True
    for elk_child_event in es.search(
        index=EVENT_INDEX_RE,
        query={
            "bool": {
                "must": [
                    {"match": {f"{FieldNames.EVENT_TYPE}.keyword": EventType.DOWN}},
                    {"match": {f"{FieldNames.PARENT_EVENT}.keyword": event.doc_id}},
                ],
                "should": [
                    {"term": {f"{FieldNames.EVENT_STATUS}.keyword": EventStatus.SUPPRESSED}},
                    {"term": {f"{FieldNames.EVENT_STATUS}.keyword": EventStatus.RESOLVING}},
                ],
                "minimum_should_match": 1,
            }
        },
        source_excludes=FieldNames.EVENT_DETAILS,
        response_type=SearchResponseType.HIT_LIST,
    ):
        if elk_child_event["_source"][FieldNames.EVENT_STATUS] == EventStatus.SUPPRESSED:
            # Initiate Move it to NEW. This way it will get ALERTED as required.
            logger.debug("Initiating move to New status [%s]: %s", elk_child_event["_id"], event.doc_id)
            doc = {FieldNames.SUPP_TO_NEW: True, FieldNames.LAST_UPDATE_TS: timezone.now()}
            try:
                es.update(index=elk_child_event["_index"], id=elk_child_event["_id"], doc=doc)
            except Exception as e:
                event.report_error(f"Failed to Initiate move to New status. Reason: {e}")
                logger.error(
                    "Failed to Initiate move to New status [%s]: %s [Reason: %s]",
                    elk_child_event["_id"],
                    event.doc_id,
                    e,
                )
                ret_value = False
            else:
                logger.debug("Initiated move to New status [%s]: %s", elk_child_event["_id"], event.doc_id)
        if elk_child_event["_source"][FieldNames.EVENT_STATUS] == EventStatus.RESOLVING:
            # Set Resolving Action to NEW
            logger.debug("Setting Resolving Action to NEW [%s]: %s", elk_child_event["_id"], event.doc_id)
            doc = {FieldNames.RESOLVING_ACTION: ResolvingAction.NEW, FieldNames.LAST_UPDATE_TS: timezone.now()}
            try:
                es.update(index=elk_child_event["_index"], id=elk_child_event["_id"], doc=doc)
            except Exception as e:
                event.report_error(f"Failed to Set Resolving Action to NEW. Reason: {e}")
                logger.error(
                    "Failed to Set Resolving Action to NEW [%s]: %s [Reason: %s]",
                    elk_child_event["_id"],
                    event.doc_id,
                    e,
                )
                ret_value = False
            else:
                logger.debug("Done Setting Resolving Action to NEW [%s]: %s", elk_child_event["_id"], event.doc_id)
    return ret_value
