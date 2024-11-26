"""Monitor Tool Admin Pages"""

from django.contrib import admin

from ..forms import MonitorToolForm, MonitorToolIPForm, MonitorToolPipelineRuleForm
from ..models import MonitorTool, MonitorToolIP, MonitorToolPipelineRule


class MonitorToolIPInline(admin.TabularInline):
    """Monitor Tool IP Admin Inline Page"""

    model = MonitorToolIP
    form = MonitorToolIPForm
    extra = 1


class MonitorToolPipelineRuleInline(admin.StackedInline):
    """Monitor Tool IP Admin Inline Page"""

    model = MonitorToolPipelineRule
    form = MonitorToolPipelineRuleForm
    extra = 1


@admin.register(MonitorTool)
class MonitorToolAdmin(admin.ModelAdmin):
    """Monitor Tool Admin Page"""

    form = MonitorToolForm

    list_display = (
        "name",
        "created",
    )

    readonly_fields = ("created",)

    fieldsets = [
        (None, {"fields": ["name", "created"]}),
        # ("Lookup Fields", {"fields": ["monitor_tool_name", "alert_title"]}),
    ]

    inlines = [MonitorToolIPInline, MonitorToolPipelineRuleInline]


@admin.register(MonitorToolIP)
class MonitorToolIPAdmin(admin.ModelAdmin):
    """Monitor Tool Admin Page"""

    form = MonitorToolIPForm

    list_display = (
        "ip",
        "monitor_tool",
        "region",
        "created",
        "modified",
    )

    list_filter = (
        "monitor_tool",
        "region",
    )

    readonly_fields = (
        "created",
        "modified",
    )

    fields = list_display


@admin.register(MonitorToolPipelineRule)
class MonitorToolPipelineRuleAdmin(admin.ModelAdmin):
    """Monitor Tool Admin Page"""

    form = MonitorToolPipelineRuleForm

    list_display = (
        "monitor_tool",
        "order_no",
        "rule_type",
        "created",
        "modified",
    )

    list_filter = (
        "monitor_tool",
        "rule_type",
    )

    readonly_fields = (
        "created",
        "modified",
    )

    # fields = list_display
