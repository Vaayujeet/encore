"""Correlation Rule Admin Pages"""

from django.contrib import admin

from ..forms import CorrelationRuleForm, EventLevelBasedSubRuleForm
from ..models import CorrelationRule, EventLevelBasedSubRule


class EventLevelBasedSubRuleInline(admin.TabularInline):
    """Correlation - Event Level based Sub Rule Inline Page"""

    model = EventLevelBasedSubRule
    form = EventLevelBasedSubRuleForm
    extra = 1


@admin.register(CorrelationRule)
class CorrelationRuleAdmin(admin.ModelAdmin):
    """Correlation Rule Admin Page"""

    form = CorrelationRuleForm

    list_display = (
        "id",
        "monitor_tool__name",
        "event_title",
        "parent_child_lookup_required",
        "wait_time_in_seconds",
        "up_event_flag",
        "do_not_create_ticket_flag",
        "itsm_assignment_group_uid",
        "itsm_severity",
    )

    list_filter = (
        "monitor_tool__name",
        "parent_child_lookup_required",
        "up_event_flag",
        "do_not_create_ticket_flag",
        "itsm_assignment_group_uid",
        "itsm_severity",
    )

    readonly_fields = (
        "id",
        "created",
        "modified",
    )

    fieldsets = [
        ("Lookup Fields", {"fields": ["monitor_tool", "event_title"]}),
        (
            "Rule Settings",
            {
                "fields": [
                    "parent_child_lookup_required",
                    "wait_time_in_seconds",
                    "up_event_flag",
                    "do_not_create_ticket_flag",
                ]
            },
        ),
        (
            "ITSM Settings for the Rule",
            {
                "fields": [
                    "itsm_assignment_group_uid",
                    "itsm_severity",
                    "itsm_title",
                    "itsm_desc",
                ]
            },
        ),
        ("Audit Fields", {"fields": ["id", "created", "modified"]}),
    ]

    inlines = [EventLevelBasedSubRuleInline]


@admin.register(EventLevelBasedSubRule)
class EventLevelBasedSubRuleAdmin(admin.ModelAdmin):
    """Correlation - Event Level based Sub Rule Admin Page"""

    list_display = (
        "id",
        "correlation_rule",
        "event_level",
        "do_not_create_ticket_flag",
        "itsm_severity",
    )
    list_filter = (
        "correlation_rule__monitor_tool__name",
        "event_level",
    )
    readonly_fields = (
        "id",
        "created",
        "modified",
    )
    fields = (
        "id",
        "correlation_rule",
        "event_level",
        "do_not_create_ticket_flag",
        "itsm_severity",
        "created",
        "modified",
    )
