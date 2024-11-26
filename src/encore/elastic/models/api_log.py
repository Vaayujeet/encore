"""API Log Model"""

from typing import Any, Optional

from model_utils.models import StatusModel, TimeStampedModel

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from elastic.constants import EVENT_ID_DATETIME_FORMAT, EVENT_INDEX_PREFIX, INDEX_DATE_SUFFIX_FORMAT
from launchpad.models.monitor_tool import MonitorToolIP


class ApiLog(TimeStampedModel, StatusModel):
    """API Log Model"""

    remote_ip = models.GenericIPAddressField(protocol="IPv4", db_index=True)

    class LogMethods(models.TextChoices):
        """Api Log Method Choices"""

        GET = "get"
        POST = "post"
        PUT = "put"
        SNMP = "snmp"  # UDP

        @classmethod
        def valid_event_methods(cls):
            """Returns set of methods which are valid for TaskType EVENT"""
            return {cls.POST, cls.PUT, cls.SNMP}

    method = models.TextField(choices=LogMethods.choices, default=LogMethods.GET, db_index=True)

    class TaskType(models.TextChoices):
        """Api Log Task Choices"""

        EVENT = "event"
        RESOLVE = "resolve"

    task = models.TextField(choices=TaskType.choices, default=TaskType.EVENT, db_index=True)
    task_data = models.JSONField(encoder=DjangoJSONEncoder)

    class Status(models.TextChoices):
        """Api Log Status Choices"""

        NEW = "new"
        IN_PROGRESS = "in_progress"
        FAILED = "failed"
        COMPLETED = "completed"

    STATUS = Status.choices
    failure_reason = models.TextField(blank=True, default="")

    class Meta:
        """Meta"""

        verbose_name = "Api Log"
        verbose_name_plural = "Api Logs"
        indexes = [models.Index(fields=["status"])]

    def __str__(self) -> str:
        return f"{self.monitor_tool if self.monitor_tool else self.remote_ip}[{self.task}][{self.method}]"

    def __repr__(self) -> str:
        return f"{self.monitor_tool if self.monitor_tool else self.remote_ip}[{self.task}][{self.method}]"

    @property
    def event_id(self) -> Optional[str]:
        """Event ID"""
        if self.task == ApiLog.TaskType.EVENT:
            return f"{settings.ENVIRONMENT}::{self.remote_ip}::{self.created.strftime(EVENT_ID_DATETIME_FORMAT)}"
        return None

    @property
    def event_index(self) -> Optional[str]:
        """Event Index Suffix"""
        if self.task == ApiLog.TaskType.EVENT:
            return f"{EVENT_INDEX_PREFIX}-{self.created.strftime(INDEX_DATE_SUFFIX_FORMAT)}"
        return None

    @property
    def monitor_tool_ip(self) -> Optional[MonitorToolIP]:
        """Monitor Tool IP"""
        if self.task == ApiLog.TaskType.EVENT and self.method in ApiLog.LogMethods.valid_event_methods():
            return MonitorToolIP.objects.get(ip=self.remote_ip)
        return None

    @property
    def monitor_tool(self):
        """Monitor Tool"""
        return self.monitor_tool_ip.monitor_tool if self.monitor_tool_ip else None

    @property
    def monitor_tool_name(self):
        """Monitor Tool Name"""
        return self.monitor_tool.name if self.monitor_tool else None

    @property
    def monitor_tool_pipeline_name(self):
        """Monitor Tool Pipeline Name"""
        return self.monitor_tool.pipeline_name if self.monitor_tool else settings.DEFAULT_TOOL_PIPELINE

    def save(self, *args: Any, **kwargs: Any) -> None:
        if (
            not self.pk
            and self.task == ApiLog.TaskType.EVENT
            and self.method in ApiLog.LogMethods.valid_event_methods()
        ):
            MonitorToolIP.objects.get_or_create(ip=self.remote_ip)
        return super().save(*args, **kwargs)
