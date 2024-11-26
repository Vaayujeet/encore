"""Api Log Admin Page"""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from ..models import ApiLog


@admin.register(ApiLog)
class ApiLogAdmin(admin.ModelAdmin):
    """Api Log Admin Class"""

    list_display = (
        "id",
        "created",
        "remote_ip",
        "method",
        "task",
        "status",
    )
    list_filter = (
        "created",
        "method",
        "task",
        "status",
        "remote_ip",
    )
    readonly_fields = (
        "id",
        "created",
        "remote_ip",
        "method",
        "task",
        "task_data",
        "status",
        "status_changed",
        "failure_reason",
        "modified",
    )
    fields = readonly_fields
    search_fields = (
        "task_data",
        "failure_reason",
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any | None = ...) -> bool:
        return False
