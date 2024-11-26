"""Resolve View"""

import json
import logging

from django.db.transaction import atomic, on_commit
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from elastic.constants import FieldNames
from elastic.models import ApiLog
from elastic.tasks import resolve_event

logger = logging.getLogger("correlator.elastic")


# TODO: Remove csrf_exempt
@csrf_exempt
def resolve(request):
    """Manual Resolve Event"""

    remote_ip = request.META.get("HTTP_X_FORWARDED_FOR", "127.0.0.1")
    resolve_method = request.method.lower()

    logger.info("Resolve Event from %s [%s]", remote_ip, resolve_method)

    resolve_data = json.loads(request.body or "{}")
    with atomic():
        api_log = ApiLog.objects.create(
            remote_ip=remote_ip,
            method=resolve_method,
            task=ApiLog.TaskType.RESOLVE,
            task_data=resolve_data,
        )

        if resolve_method != "post":
            api_log.status = ApiLog.Status.FAILED
            api_log.failure_reason = f"Invalid request method [{resolve_method}]"
            api_log.save()
            return HttpResponseBadRequest(f"Invalid request method [{resolve_method}]")

        if FieldNames.ITSM_TICKET not in resolve_data:
            api_log.status = ApiLog.Status.FAILED
            api_log.failure_reason = f"Missing {FieldNames.ITSM_TICKET}"
            api_log.save()
            return HttpResponseBadRequest(f"Missing {FieldNames.ITSM_TICKET}")

    on_commit(lambda: resolve_event.delay(api_log=api_log.pk))
    return HttpResponse(status=200)  # NOTE: Ideally it should be 202, but GLPI needs 200
