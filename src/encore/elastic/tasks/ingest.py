"""Task to Ingest Event to ELK"""

import logging

from django.conf import settings

from elastic.constants import FieldNames
from elastic.models import ApiLog, Event
from elastic.utils import CorrelatorElastic
from .common import correlator_task, task_handler

logger = logging.getLogger("correlator.elastic.tasks.ingest")


@correlator_task(
    name="IngestEvent",
    model="elastic.ApiLog",
    key_value_field="api_log",
    valid_start_status={ApiLog.Status.NEW},
)
def ingest_event(*, api_log: int | ApiLog):
    """Task to Ingest the Event"""

    if not isinstance(api_log, ApiLog):
        return

    event_json = {
        FieldNames.EVENT_DETAILS: api_log.task_data,
        FieldNames.TOOL_IP: api_log.remote_ip,
        FieldNames.TOOL_NAME: api_log.monitor_tool_name,
        FieldNames.METHOD: api_log.method,
        FieldNames.RECEIVED_TS: api_log.created,
    }

    event_id = api_log.event_id
    event_index = api_log.event_index

    es = CorrelatorElastic()
    logger.debug("[ApiLog: %s] %s [%s]: Ingesting", api_log.pk, event_id, event_index)
    try:
        es.index(
            index=event_index,
            id=event_id,
            pipeline=settings.MAIN_PIPELINE,
            document=event_json,
            op_type="create",
        )
    except Exception as e:
        logger.error("[ApiLog: %s] %s [%s]: Failed to Ingest", api_log.pk, event_id, event_index)
        api_log.status = ApiLog.Status.FAILED
        api_log.failure_reason = str(e)
        api_log.save()
        return

    logger.info("[ApiLog: %s] %s [%s]: Ingested", api_log.pk, event_id, event_index)
    elk_event = es.get_event(event_index=event_index, event_id=event_id)
    elk_event_src = elk_event["_source"]
    event = Event.objects.create(
        api_log=api_log,
        monitor_tool_ip=api_log.monitor_tool_ip,
        doc_id=event_id,
        doc_index=event_index,
        status=elk_event_src[FieldNames.EVENT_STATUS],
        level=elk_event_src[FieldNames.EVENT_LEVEL] if FieldNames.EVENT_LEVEL in elk_event_src else None,
        title=elk_event_src[FieldNames.EVENT_TITLE] if FieldNames.EVENT_TITLE in elk_event_src else None,
        event_ts=elk_event_src[FieldNames.EVENT_TS],
        event_type=elk_event_src[FieldNames.EVENT_TYPE],
        asset_unique_id=(
            elk_event_src[FieldNames.ASSET_UNIQUE_ID] if FieldNames.ASSET_UNIQUE_ID in elk_event_src else None
        ),
        asset_type=(elk_event_src[FieldNames.ASSET_TYPE] if FieldNames.ASSET_TYPE in elk_event_src else None),
        retry_count=0,
    )
    api_log.status = ApiLog.Status.COMPLETED
    api_log.save()
    logger.debug("[ApiLog: %s] %s [%s]: Event [%s] Saved", api_log.pk, event_id, event_index, event.pk)
    task_handler(event)
