"""Event Views"""

import json
import logging
import typing as t

from django.db.transaction import atomic, on_commit
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from elastic.models import ApiLog
from elastic.tasks import ingest_event
from elastic.utils import CorrelatorElastic
from snmp.utils import KEY_TRANSLATE_MAP

logger = logging.getLogger("correlator.elastic")

CSV_FIELDS: t.Dict[str, t.Tuple[str, str]] = {"FIELD_NAME": (";", ":")}


# TODO: Remove csrf_exempt
@csrf_exempt
def event(request):
    """Log Event"""

    remote_ip = request.META.get("HTTP_X_FORWARDED_FOR", "127.0.0.1")
    event_method = request.method.lower()

    logger.info("New Event from %s [%s]", remote_ip, event_method)

    event_data = json.loads(request.body or "{}")
    for field_name, (sub_field_sep, kv_sep) in CSV_FIELDS.items():
        if field_name in event_data:
            sub_field_list = event_data[field_name].split(sub_field_sep)
            for sub_field in sub_field_list:
                val_list = sub_field.split(kv_sep)
                event_data[f"{field_name}__{val_list[0].strip().translate(KEY_TRANSLATE_MAP)}"] = kv_sep.join(
                    val_list[1:]
                ).strip()

    with atomic():
        api_log = ApiLog.objects.create(
            remote_ip=remote_ip,
            method=event_method,
            task=ApiLog.TaskType.EVENT,
            task_data=event_data,
        )

        if event_method in ApiLog.LogMethods.valid_event_methods():
            on_commit(lambda: ingest_event.delay(api_log=api_log.pk))
            return HttpResponse(status=202)

        api_log.status = ApiLog.Status.FAILED
        api_log.failure_reason = f"Invalid request method [{event_method}]"
        api_log.save()
    return HttpResponseBadRequest(api_log.failure_reason)


def event_info(_request, event_index, event_id):
    """Retrieve the Event info from Elastic"""
    es = CorrelatorElastic()
    return HttpResponse(json.dumps(es.get_event(event_index, event_id)))
