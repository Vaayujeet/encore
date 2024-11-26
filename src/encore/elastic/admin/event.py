"""Event Admin Page"""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from ..models import ErrorLog, Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Event Admin Class"""

    list_display = (
        "doc_id",
        "doc_index",
        "api_log",
        "title",
        "level",
        "status",
        "event_type",
        "event_ts",
        "asset_unique_id",
        "asset_type",
        "retry_count",
    )
    list_filter = (
        "created",
        "modified",
        "doc_index",
        "status",
        "event_type",
        "monitor_tool_ip__monitor_tool__name",
    )
    readonly_fields = (
        "id",
        "created",
        "modified",
        "status",
        "status_changed",
        "doc_id",
        "doc_index",
        "level",
        "title",
        "event_ts",
        "event_type",
        "asset_unique_id",
        "asset_type",
        "retry_count",
        "api_log",
        "monitor_tool_ip",
        "extras",
    )
    fields = readonly_fields
    search_fields = (
        "title",
        "asset_unique_id",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        return False


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    """ErrorLog Admin Class"""

    list_display = (
        "event",
        "event_status",
        "error_desc",
        "repeat_count",
        "resolved",
        "created",
        "modified",
    )
    list_filter = (
        "event_status",
        "resolved",
        "created",
        "modified",
    )
    readonly_fields = (
        "id",
        "event",
        "event_status",
        "error_desc",
        "repeat_count",
        "created",
        "modified",
    )
    search_fields = ("error_desc",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        return False
