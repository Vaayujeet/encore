"""Correlation Rule Models"""

import typing as t
from dataclasses import dataclass

from model_utils.models import TimeStampedModel

from django.db import models


@dataclass
class ItsmSettings:
    """ITSM Settings"""

    # TODO: Can we add fields dynamically using model fields

    itsm_assignment_group_uid: int
    itsm_severity: int
    itsm_title: str
    itsm_desc: str

    def __init__(self, **kwargs):
        self.itsm_assignment_group_uid = kwargs.get("itsm_assignment_group_uid")
        self.itsm_severity = kwargs.get("itsm_severity")
        self.itsm_title = kwargs.get("itsm_title")
        self.itsm_desc = kwargs.get("itsm_desc")


class CorrelationRule(TimeStampedModel):
    """Correlation Rule Model"""

    monitor_tool = models.ForeignKey(
        "MonitorTool",
        on_delete=models.PROTECT,
        related_name="correlation_rules",
        related_query_name="correlatin_rule",
    )
    event_title = models.TextField(db_index=True, help_text="Use * to set default rule for the monitor tool.")

    parent_child_lookup_required = models.BooleanField(
        default=True, db_index=True, help_text="When set, parent event will be looked up for such events."
    )
    wait_time_in_seconds = models.PositiveSmallIntegerField(
        default=150, help_text="Time (in seconds) to wait before raising a ITSM ticket for this event."
    )
    up_event_flag = models.BooleanField(
        default=True,
        help_text="Indicates whether an up event is sent for this event or not. This field is not used anywhere.",
    )
    do_not_create_ticket_flag = models.BooleanField(
        default=True,
        help_text="If True, ITSM ticket won't be created for such events."
        + " Default Flag to use when no match found in Event Level based Sub Rule."
        + " Check 'Event Level based Sub Rules' section below.",
    )

    # Fields used for ITSM ticket
    itsm_assignment_group_uid = models.PositiveSmallIntegerField(null=True, blank=True)
    itsm_severity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Default ITSM Severity to use when no match found in Event Level based Sub Rule."
        + " Check 'Event Level based Sub Rules' section below.",
    )
    itsm_title = models.TextField(null=True, blank=True)
    itsm_desc = models.TextField(null=True, blank=True)

    class Meta:
        """Meta"""

        constraints = [models.UniqueConstraint(fields=["monitor_tool", "event_title"], name="unique_correlation_rule")]
        verbose_name = "Correlation Rule"
        verbose_name_plural = "Correlation Rules"

    def __str__(self) -> str:
        return f"{self.monitor_tool.name}: {self.event_title}"

    def __repr__(self) -> str:
        return f"{self.monitor_tool.name}: {self.event_title}"

    def level_sub_rule(self, level) -> t.Optional["EventLevelBasedSubRule"]:
        """EventLevelBasedSubRule for given level"""
        try:
            return self.event_level_based_sub_rules.get(event_level=level)
        except EventLevelBasedSubRule.DoesNotExist:
            return None

    def itsm_settings(self, level=None) -> ItsmSettings:
        """ITSM Settings"""
        _sett = ItsmSettings(**self.__dict__)
        if level and (level_rule := self.level_sub_rule(level)):
            _sett.itsm_severity = level_rule.itsm_severity
        return _sett


class EventLevelBasedSubRule(TimeStampedModel):
    """Correlation - Event Level based Sub Rule Table"""

    correlation_rule = models.ForeignKey(
        CorrelationRule,
        on_delete=models.CASCADE,
        related_name="event_level_based_sub_rules",
        related_query_name="event_level_based_sub_rule",
    )
    event_level = models.TextField(db_index=True)
    itsm_severity = models.PositiveSmallIntegerField()
    do_not_create_ticket_flag = models.BooleanField(
        default=False, help_text="If True, ITSM ticket won't be created for such event levels"
    )

    class Meta:
        """Meta"""

        constraints = [
            models.UniqueConstraint(
                fields=["correlation_rule", "event_level"], name="unique_event_level_based_sub_rule"
            )
        ]
        verbose_name = "Event Level based Sub Rule"
        verbose_name_plural = "Event Level based Sub Rules"

    def __str__(self) -> str:
        return f"{self.correlation_rule}: {self.event_level}"

    def __repr__(self) -> str:
        return f"{self.correlation_rule}: {self.event_level}"


# ##### Functions useful for exporting and comparing rules.
# TODO: High Priority: Make changes to remove default rule

CORRELATION_RULE_FIELDS = [
    "default_rule",
    "monitor_tool__name",
    "event_title",
    "parent_child_lookup_required",
    "wait_time_in_seconds",
    "up_event_flag",
    "do_not_create_ticket_flag",
    "itsm_assignment_group_uid",
    "itsm_severity",
    "itsm_title",
    "itsm_desc",
]

EVENT_LEVEL_BASED_SUB_RULE_FIELDS = [
    "event_level",
    "itsm_severity",
    "do_not_create_ticket_flag",
]


def get_rules():
    """Get Rules List

    Returns:
        rules => {
            "1": {
                field_name: field_value,
                ...,
                EventLevelBasedSubRule: <sub_rules>
            } | None --> Default Rule
            "0": {
                "Monitor Tool Name": {
                    "Event Title": {
                        field_name: field_value,
                        ...,
                        EventLevelBasedSubRule: <sub_rules>
                    }, --> Monitor Tool / Event Title specific Rule
                    ...
                },
                ...
            }
        }
        where <sub_rules> => {
            "Event Level": {
                field_name: field_value,
                ...,
            }, --> Correlation Rule / Event Level specific Sub Rule
            ...
        }
    """
    rules = {"1": None, "0": {}}
    for rule in CorrelationRule.objects.prefetch_related().all().order_by("monitor_tool__name", "event_title"):
        rule_dict = {k: getattr(rule, k) for k in CORRELATION_RULE_FIELDS}
        rule_dict[EventLevelBasedSubRule.__name__] = {
            sub_rule.event_level: {k: getattr(sub_rule, k) for k in EVENT_LEVEL_BASED_SUB_RULE_FIELDS}
            for sub_rule in rule.event_level_based_sub_rules.all()
        }
        if rule_dict["default_rule"]:
            rules["1"] = rule_dict
        else:
            monitor_tool__name = rule_dict["monitor_tool__name"]
            event_title = rule_dict["event_title"]
            if monitor_tool__name not in rules["0"]:
                rules["0"][monitor_tool__name] = {}
            rules["0"][monitor_tool__name][event_title] = rule_dict
    return rules


def _compare_rule_by_field(old_rule: t.Dict[str, t.Any], new_rule: t.Dict[str, t.Any], field_list: t.List[str]) -> bool:
    """Return True if all field values match else return False"""
    for field_name in field_list:
        if old_rule[field_name] != new_rule[field_name]:
            return False
    return True


def _is_acd_sub_rule(sub_rule_summary):
    return len(sub_rule_summary["a"]) + len(sub_rule_summary["c"]) + len(sub_rule_summary["d"])


def _compare_default_rule(
    old_default_rule: t.Dict[str, t.Any] | None, new_default_rule: t.Dict[str, t.Any] | None
) -> t.Tuple[str, t.Dict[str, t.List[str]] | None]:
    if old_default_rule and new_default_rule:
        event_level_sub_rule_summary = compare_event_level_sub_rules(
            old_default_rule[EventLevelBasedSubRule.__name__], new_default_rule[EventLevelBasedSubRule.__name__]
        )
        if _compare_rule_by_field(old_default_rule, new_default_rule, CORRELATION_RULE_FIELDS):
            return "m", event_level_sub_rule_summary  # match with event_level sub rule summary
        else:
            return "c", event_level_sub_rule_summary  # change with event_level sub rule summary
    elif old_default_rule and not new_default_rule:
        return "d", None  # delete
    elif not old_default_rule and new_default_rule:
        return "a", None  # add
    else:
        return "n", None  # Do Nothing, both old and new default rule does not exist


def compare_rules(old_rules: t.Dict[str, t.Any], new_rules: t.Dict[str, t.Any]):
    """Return Comparison Summary for Correlation Rules with Sub Rules Summary"""

    summary: t.Dict[
        int,
        t.Tuple[str, t.Dict[str, t.List[str]] | None]
        | t.Dict[str, t.List[t.Tuple[str, str]] | t.Dict[t.Tuple[str, str], t.Dict[str, t.List[str]] | None]],
    ] = {
        1: _compare_default_rule(old_rules["1"], new_rules["1"]),  # --> Default Rule action
        0: {  # --> Other Rules action
            "a": [],  # add correlation rule for given monitor_tool / event_title
            "d": [],  # delete correlation rule for given monitor_tool / event_title
            "c": {},  # change correlation rule for given monitor_tool / event_title with event_level sub rule summary
            "m": {},  # match correlation rule for given monitor_tool / event_title with event_level sub rule summary
        },
    }

    old_monitor_tools = old_rules["0"].keys()
    new_monitor_tools = new_rules["0"].keys()

    monitor_tools_to_add = new_monitor_tools - old_monitor_tools
    for monitor_tool in monitor_tools_to_add:
        for event_title in new_rules["0"][monitor_tool]:
            summary[0]["a"].append((monitor_tool, event_title))

    monitor_tools_to_delete = old_monitor_tools - new_monitor_tools
    for monitor_tool in monitor_tools_to_delete:
        for event_title in old_rules["0"][monitor_tool]:
            summary[0]["d"].append((monitor_tool, event_title))

    common_monitor_tools = old_monitor_tools & new_monitor_tools
    for monitor_tool in common_monitor_tools:
        old_event_titles = old_rules["0"][monitor_tool].keys()
        new_event_titles = new_rules["0"][monitor_tool].keys()

        for event_title in new_event_titles - old_event_titles:
            summary[0]["a"].append((monitor_tool, event_title))

        for event_title in old_event_titles - new_event_titles:
            summary[0]["d"].append((monitor_tool, event_title))

        for event_title in old_event_titles & new_event_titles:
            event_level_sub_rule_summary = compare_event_level_sub_rules(
                old_rules["0"][monitor_tool][event_title][EventLevelBasedSubRule.__name__],
                new_rules["0"][monitor_tool][event_title][EventLevelBasedSubRule.__name__],
            )
            if _compare_rule_by_field(
                old_rules["0"][monitor_tool][event_title],
                new_rules["0"][monitor_tool][event_title],
                CORRELATION_RULE_FIELDS,
            ):
                if event_level_sub_rule_summary:
                    summary[0]["m"][(monitor_tool, event_title)] = event_level_sub_rule_summary
            else:
                summary[0]["c"][(monitor_tool, event_title)] = event_level_sub_rule_summary

    return summary


def compare_event_level_sub_rules(
    old_event_level_sub_rules: t.Dict[str, t.Any], new_event_level_sub_rules: t.Dict[str, t.Any]
) -> t.Dict[str, t.List[str]] | None:
    """Return Comparison Summary for Event Level Sub Rules"""
    old_event_levels = old_event_level_sub_rules.keys()
    new_event_levels = new_event_level_sub_rules.keys()
    common_event_levels = old_event_levels & new_event_levels
    summary: t.Dict[str, t.List[str]] = {
        "a": list(new_event_levels - old_event_levels),  # add
        "d": list(old_event_levels - new_event_levels),  # delete
        "c": [],  # change
        # "m": [],  # match
    }
    for event_level in common_event_levels:
        if _compare_rule_by_field(
            old_event_level_sub_rules[event_level],
            new_event_level_sub_rules[event_level],
            EVENT_LEVEL_BASED_SUB_RULE_FIELDS,
        ):
            pass
            # summary["m"].append(event_level)
        else:
            summary["c"].append(event_level)
    return summary if _is_acd_sub_rule(summary) else None
