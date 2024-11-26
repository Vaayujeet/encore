"""SNMP Listener Command
"""

import logging
import typing as t

from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.carrier.asyncio.dispatch import AsyncioDispatcher

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.transaction import atomic, on_commit

from elastic.models import ApiLog
from elastic.tasks import ingest_event
from snmp.utils import KEY_TRANSLATE_MAP, decode_trap_message, get_mib_view_controller

logger = logging.getLogger("correlator.snmp")
view_controller = get_mib_view_controller()

CSV_FIELDS: t.Dict[str, t.Tuple[str, str]] = {"FIELD_NAME": (";", ":")}


def callback_func(unused_transport_dispatcher, unused_transport_domain, transport_address, whole_msg):
    """Callback Function that process SNMP Traps and send event to Elastic"""

    remote_ip = transport_address[0]
    event_method = ApiLog.LogMethods.SNMP

    logger.info("New Event from %s [%s]", remote_ip, event_method)

    event_data = decode_trap_message(remote_ip, whole_msg, view_controller)
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
        on_commit(lambda: ingest_event.delay(api_log=api_log.pk))


class Command(BaseCommand):
    """Export Correlation Rules Command"""

    def handle(self, *args, **options) -> str | None:
        logger.info("Starting SNMP Listener for %s:%s: ", settings.SNMP_HOST, settings.SNMP_PORT)

        transport_dispatcher = AsyncioDispatcher()
        transport_dispatcher.registerRecvCbFun(callback_func)

        # UDP/IPv4
        transport_dispatcher.registerTransport(
            udp.domainName, udp.UdpTransport().openServerMode((settings.SNMP_HOST, settings.SNMP_PORT))
        )
        transport_dispatcher.jobStarted(1)

        try:
            # Dispatcher will never finish as job#1 never reaches zero
            logger.info("Dispatched SNMP Listener for %s:%s: ", settings.SNMP_HOST, settings.SNMP_PORT)
            transport_dispatcher.runDispatcher()
        except Exception as e:
            logger.error("SNMP Listener for %s:%s: raised %s", settings.SNMP_HOST, settings.SNMP_PORT, str(e))
            transport_dispatcher.closeDispatcher()
            raise
