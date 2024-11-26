"""Event Model"""

import typing as t

from model_utils.fields import StatusField
from model_utils.models import StatusModel, TimeStampedModel

from django.db import models

from correlator.exceptions import CorrelatorProcessException
from elastic.constants import EventStatus, EventType
from elastic.utils import CorrelatorElastic
from launchpad.models import CorrelationRule, ItsmSettings, MonitorTool


class Event(TimeStampedModel, StatusModel):
    """Event Model"""

    api_log = models.OneToOneField("ApiLog", on_delete=models.PROTECT)
    monitor_tool_ip = models.ForeignKey(
        "launchpad.MonitorToolIP",
        on_delete=models.PROTECT,
        related_name="events",
        related_query_name="event",
    )

    # Elastic id/index
    doc_id = models.TextField()
    doc_index = models.TextField()

    STATUS = EventStatus.choices
    level = models.TextField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    event_ts = models.DateTimeField()
    event_type = models.TextField(choices=EventType.choices, db_index=True)

    asset_unique_id = models.TextField(null=True, blank=True)
    asset_type = models.TextField(null=True, blank=True)

    retry_count = models.PositiveIntegerField()

    extras = models.JSONField(default=dict)

    class Meta:
        """Meta"""

        verbose_name = "Event"
        verbose_name_plural = "Events"
        indexes = [models.Index(fields=["status"])]

    def __str__(self) -> str:
        return f"[{self.doc_index}]{self.doc_id}"

    def __repr__(self) -> str:
        return f"[{self.doc_index}]{self.doc_id}"

    @property
    def monitor_tool(self) -> MonitorTool | None:
        """Monitor Tool"""
        return self.monitor_tool_ip.monitor_tool

    @property
    def elastic_event(self):
        """Event stored in ELK"""

        es = CorrelatorElastic()
        return es.get_event(event_index=self.doc_index, event_id=self.doc_id)

    @property
    def correlation_rule(self) -> CorrelationRule | None:
        """Correlation Rule applicable"""
        if not self.monitor_tool:
            return None
        try:
            return CorrelationRule.objects.get(monitor_tool=self.monitor_tool, event_title=self.title)
        except (CorrelationRule.DoesNotExist, CorrelationRule.MultipleObjectsReturned):
            try:
                return CorrelationRule.objects.get(monitor_tool=self.monitor_tool, alert_title="*")
            except CorrelationRule.DoesNotExist:
                return None

    @property
    def parent_child_lookup_required(self) -> bool:
        """Parent Child Lookup Required Indicator"""
        if rule := self.correlation_rule:
            return rule.parent_child_lookup_required
        return CorrelationRule._meta.get_field("parent_child_lookup_required").default

    @property
    def wait_time_in_seconds(self) -> int:
        """Time (Seconds) to Wait before creating a ITSM Ticket"""
        if rule := self.correlation_rule:
            return rule.wait_time_in_seconds
        return CorrelationRule._meta.get_field("wait_time_in_seconds").default

    @property
    def do_not_create_ticket_flag(self) -> bool:
        """Do Not Create Ticket Flag"""
        if rule := self.correlation_rule:
            if level_rule := rule.level_sub_rule(self.level):
                return level_rule.do_not_create_ticket_flag
            return rule.do_not_create_ticket_flag
        return True

    @property
    def itsm_settings(self) -> t.Optional[ItsmSettings]:
        """ITSM Settings"""
        if rule := self.correlation_rule:
            return rule.itsm_settings(self.level)
        return None

    def report_error(self, error_desc, incr_flag=True, check_repeat_count=True):
        """Add Error Log if it does not exist or update the repeat count"""
        err, created = ErrorLog.objects.get_or_create(event=self, event_status=self.status, error_desc=error_desc)
        if not created:
            err.repeat_count += 1
            err.resolved = False
            err.save()
        if incr_flag:
            self.retry_count += 1
            self.save()
        if check_repeat_count and err.repeat_count > 10:
            raise CorrelatorProcessException(f"Event [{self.pk}][{self.status}] failing with Error: {error_desc}")


class ErrorLog(TimeStampedModel):
    """Event Error Log Model"""

    event = models.ForeignKey(
        "elastic.Event",
        on_delete=models.CASCADE,
        related_name="errors",
        related_query_name="error",
    )
    STATUS = EventStatus.choices
    event_status = StatusField()
    error_desc = models.TextField()
    repeat_count = models.PositiveIntegerField(default=1)
    resolved = models.BooleanField(default=False)

    class Meta:
        """Meta"""

        verbose_name = "Error Log"
        verbose_name_plural = "Error Logs"
        constraints = [models.UniqueConstraint(fields=["event", "event_status", "error_desc"], name="unique_error_log")]

    def __str__(self) -> str:
        return f"{self.event}[{self.event_status}] -> {self.error_desc[:15]}"

    def __repr__(self) -> str:
        return f"{self.event}[{self.event_status}] -> {self.error_desc[:15]}"
