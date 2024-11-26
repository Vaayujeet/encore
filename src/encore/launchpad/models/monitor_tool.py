"""Monitor Tool Models"""

import typing as t

from model_utils.models import TimeStampedModel

from django.conf import settings
from django.db import models

from elastic.constants import EventType, FieldNames


class MonitorTool(models.Model):
    """Monitor Tool Class"""

    name = models.TextField(
        max_length=200,
        unique=True,
        help_text="Only letters, numbers, space and hypen. Should not start/end with space.",
    )
    created = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        """Meta"""

        verbose_name = "Monitor Tool"
        verbose_name_plural = "Monitor Tools"

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"{self.name}"

    @property
    def name_identifier(self):
        """Monitor Tool Name Identifier"""
        return self.name.lower().replace(" ", "-")

    @property
    def pipeline_name(self) -> str:
        """Pipeline Name"""
        return self.name_identifier + settings.MONITOR_TOOL_PIPELINE_SUFFIX


class MonitorToolIP(TimeStampedModel):
    """Monitor Tool IPs Class"""

    ip = models.GenericIPAddressField(protocol="IPv4", primary_key=True)
    monitor_tool = models.ForeignKey(
        MonitorTool,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ips",
        related_query_name="ip",
    )
    region = models.TextField(max_length=200, default="global")

    class Meta:
        """Meta"""

        verbose_name = "Monitor Tool IP"
        verbose_name_plural = "Monitor Tool IPs"

    def __str__(self) -> str:
        return f"{self.monitor_tool.name if self.monitor_tool else '--'}: {self.region} [{self.ip}]"

    def __repr__(self) -> str:
        return f"{self.monitor_tool.name if self.monitor_tool else '--'}: {self.region} [{self.ip}]"


class MonitorToolPipelineRule(TimeStampedModel):
    """Monitor Tool Pipeline Rule Class"""

    monitor_tool = models.ForeignKey(
        MonitorTool,
        on_delete=models.PROTECT,
        related_name="pipeline_rules",
        related_query_name="pipeline_rule",
    )
    order_no = models.PositiveSmallIntegerField(
        default=0,
        help_text="Order in which the rule should be executed. Multiple rules, "
        + "that are not dependent on each other, can have same order",
    )

    class RuleType(models.TextChoices):
        """Rule Type Choices"""

        ASSET_UNIQUE_ID_RULE = "asset_id"
        EVENT_TYPE_RULE = "event_type"
        SET_RULE = "set"
        GROK_RULE = "grok"
        REMOVE_RULE = "remove"

    rule_type = models.TextField(
        choices=RuleType.choices,
        default=RuleType.SET_RULE,
        db_index=True,
        help_text="Each monitor tool pipeline should have one rule each for "
        + f"'{RuleType.ASSET_UNIQUE_ID_RULE.label}' and '{RuleType.EVENT_TYPE_RULE.label}'."
        + " Other rules can be used multiple times to define other fields (including temporary fields).",
    )

    # Fields used for EVENT_TYPE_RULE
    event_type_default = models.TextField(
        verbose_name="Default Event Type",
        choices=EventType.choices,
        null=True,
        blank=True,
        help_text="Defines the default event type for each incoming event.",
    )
    event_type_field = models.TextField(
        verbose_name=f"From Field Name for {RuleType.EVENT_TYPE_RULE.label}",
        null=True,
        blank=True,
        help_text="Original field that will be copied to Event Type.",
    )
    event_type_up_values = models.TextField(
        verbose_name=f"Values for {EventType.UP.upper()} Event Type",
        null=True,
        blank=True,
        help_text=f"Comma separated list of values that identify {EventType.UP.upper()} Event Type.",
    )
    event_type_down_values = models.TextField(
        verbose_name=f"Values for {EventType.DOWN.upper()} Event Type",
        null=True,
        blank=True,
        help_text=f"Comma separated list of values that identify {EventType.DOWN.upper()} Event Type.",
    )
    event_type_neutral_values = models.TextField(
        verbose_name=f"Values for {EventType.NEUTRAL.upper()} Event Type",
        null=True,
        blank=True,
        help_text=f"Comma separated list of values that identify {EventType.NEUTRAL.upper()} Event Type.",
    )

    # Fields used for SET_RULE and ASSET_UNIQUE_ID_RULE
    set_field = models.TextField(
        verbose_name=f"Field Name for {RuleType.SET_RULE.label}",
        null=True,
        blank=True,
        help_text="Check ELK's Set Processor for Ingest Pipeline."
        + " Supports template snippet (not recommended for Field Name).",
    )
    set_value = models.TextField(
        verbose_name="Value / Copy From",
        null=True,
        blank=True,
        help_text="Check ELK's Set Processor for Ingest Pipeline. Supports template snippet."
        + " Set Value will be treated as Copy From Field if 'Set Copy From Flag' is enabled"
        + " [dont use template snippet in such case].",
    )
    set_copy_from_flag = models.BooleanField(
        verbose_name="Use Copy From flag",
        default=False,
        help_text="Check ELK's Set Processor for Ingest Pipeline."
        + " If enabled, Set Value will be treated as Copy From Field."
        + " Set Value will not support template snippet in that case.",
    )
    override_flag = models.BooleanField(
        verbose_name="Override flag",
        default=True,
        help_text="Check ELK's Set Processor for Ingest Pipeline.",
    )
    ignore_empty_value_flag = models.BooleanField(
        verbose_name="Ignore Empty Value flag",
        default=False,
        help_text="Check ELK's Set Processor for Ingest Pipeline.",
    )

    # Fields used for GROK_RULE
    grok_field = models.TextField(
        verbose_name=f"Field Name for {RuleType.GROK_RULE.label}",
        null=True,
        blank=True,
        help_text="Field to use for grok expression parsing. Check ELK's Grok Processor for Ingest Pipeline.",
    )
    grok_patterns = models.JSONField(
        verbose_name="Patterns",
        null=True,
        blank=True,
        help_text="An ordered list of grok expression to match and extract named captures with."
        + " Returns on the first expression in the list that matches."
        + " Check ELK's Grok Processor for Ingest Pipeline.",
    )
    grok_pattern_definitions = models.JSONField(
        verbose_name="Pattern Definitions",
        null=True,
        blank=True,
        help_text="A map of pattern-name and pattern tuples defining custom patterns to be used by"
        + " the current processor. Patterns matching existing names will override the pre-existing definition."
        + " Check ELK's Grok Processor for Ingest Pipeline.",
    )

    # Fields used for REMOVE_RULE
    remove_field = models.TextField(
        verbose_name="Field to be removed",
        null=True,
        blank=True,
        help_text="Check ELK's Remove Processor for Ingest Pipeline."
        + " Always better to remove fields (esp. temporary ones) that are not required."
        + " Supports template snippet (not recommended).",
    )

    # Additional Fields for SET_RULE (including ASSET_UNIQUE_ID_RULE), GROK_RULE and REMOVE_RULE.
    ignore_missing_flag = models.BooleanField(
        verbose_name="Ignore Missing flag",
        default=False,
        help_text=" Check ELK's Grok / Remove Processor for Ingest Pipeline.",
    )
    if_condition = models.TextField(
        verbose_name="IF Condition",
        null=True,
        blank=True,
        help_text=" Check ELK's Set / Grok / Remove Processor for Ingest Pipeline.",
    )
    ignore_failure_flag = models.BooleanField(
        verbose_name="Ignore Failure flag",
        default=False,
        help_text=" Check ELK's Set / Grok / Remove Processor for Ingest Pipeline.",
    )

    class Meta:
        """Meta"""

        verbose_name = "Monitor Tool Pipeline Rule"
        verbose_name_plural = "Monitor Tool Pipeline Rules"

    def __str__(self) -> str:
        return f"{self.monitor_tool.name}: {self.rule_type} [{self.order_no}]"

    def __repr__(self) -> str:
        return f"{self.monitor_tool.name}: {self.rule_type} [{self.order_no}]"

    @property
    def ingest_pipeline_rule(self) -> t.Tuple[int, str, t.Dict[str | EventType, t.Any]]:
        """Returns the Pipeline Rule in standard format"""
        rule = None
        if self.rule_type == MonitorToolPipelineRule.RuleType.EVENT_TYPE_RULE:
            # EVENT_TYPE_RULE
            if self.event_type_default:
                rule = {"field": FieldNames.EVENT_TYPE, "value": self.event_type_default}
            else:
                rule = {
                    "field": FieldNames.EVENT_TYPE,
                    "from": self.event_type_field,
                    EventType.DOWN: self.event_type_down_values.split(",") if self.event_type_down_values else None,
                    EventType.UP: self.event_type_up_values.split(",") if self.event_type_up_values else None,
                    EventType.NEUTRAL: (
                        self.event_type_neutral_values.split(",") if self.event_type_neutral_values else None
                    ),
                }

        if (
            self.rule_type == MonitorToolPipelineRule.RuleType.SET_RULE
            or self.rule_type == MonitorToolPipelineRule.RuleType.ASSET_UNIQUE_ID_RULE
        ):
            # SET_RULE or ASSET_UNIQUE_ID_RULE
            rule = {
                "field": (
                    self.set_field
                    if self.rule_type == MonitorToolPipelineRule.RuleType.SET_RULE
                    else FieldNames.ASSET_UNIQUE_ID
                ),
                "override": self.override_flag,
                "ignore_empty_value": self.ignore_empty_value_flag,
                "if": self.if_condition.strip() if self.if_condition.strip() else None,
                "ignore_failure": self.ignore_failure_flag,
            }
            if self.set_copy_from_flag:
                rule["copy_from"] = self.set_value
            else:
                rule["value"] = self.set_value
        if self.rule_type == MonitorToolPipelineRule.RuleType.GROK_RULE:
            # GROK_RULE
            rule = {
                "field": self.grok_field,
                "patterns": self.grok_patterns,
                "pattern_definitions": self.grok_pattern_definitions,
                "ignore_missing": self.ignore_missing_flag,
                "if": self.if_condition.strip() if self.if_condition.strip() else None,
                "ignore_failure": self.ignore_failure_flag,
            }

        if self.rule_type == MonitorToolPipelineRule.RuleType.REMOVE_RULE:
            # REMOVE_RULE
            rule = {
                "field": self.remove_field,
                "ignore_missing": self.ignore_missing_flag,
                "if": self.if_condition.strip() if self.if_condition.strip() else None,
                "ignore_failure": self.ignore_failure_flag,
            }
        if rule:
            rule["tag"] = f"{self.order_no}-{self.rule_type}-{rule['field']}"
        return (self.order_no, self.rule_type, rule)
