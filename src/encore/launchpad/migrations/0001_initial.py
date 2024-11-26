# Generated by Django 5.1.1 on 2024-11-04 06:58

import model_utils.fields

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MonitorTool",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "name",
                    models.TextField(
                        help_text="Only letters, numbers, space and hypen. Should not start/end with space.",
                        max_length=200,
                        unique=True,
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Monitor Tool",
                "verbose_name_plural": "Monitor Tools",
            },
        ),
        migrations.CreateModel(
            name="CorrelationRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "event_title",
                    models.TextField(db_index=True, help_text="Use * to set default rule for the monitor tool."),
                ),
                (
                    "parent_child_lookup_required",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="When set, parent event will be looked up for such events.",
                    ),
                ),
                (
                    "wait_time_in_seconds",
                    models.PositiveSmallIntegerField(
                        default=300, help_text="Time (in seconds) to wait before raising a ITSM ticket for this event."
                    ),
                ),
                (
                    "up_event_flag",
                    models.BooleanField(
                        default=True,
                        help_text="Indicates whether an up event is sent for this event or not."
                        + " This field is not used anywhere.",
                    ),
                ),
                (
                    "do_not_create_ticket_flag",
                    models.BooleanField(
                        default=True,
                        help_text="If True, ITSM ticket won't be created for such events."
                        + " Default Flag to use when no match found in Event Level based Sub Rule."
                        + " Check 'Event Level based Sub Rules' section below.",
                    ),
                ),
                ("itsm_assignment_group_uid", models.PositiveSmallIntegerField(blank=True, null=True)),
                (
                    "itsm_severity",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text="Default ITSM Severity to use when no match found in Event Level based Sub Rule."
                        + " Check 'Event Level based Sub Rules' section below.",
                        null=True,
                    ),
                ),
                ("itsm_title", models.TextField(blank=True, null=True)),
                ("itsm_desc", models.TextField(blank=True, null=True)),
                (
                    "monitor_tool",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="correlation_rules",
                        related_query_name="correlatin_rule",
                        to="launchpad.monitortool",
                    ),
                ),
            ],
            options={
                "verbose_name": "Correlation Rule",
                "verbose_name_plural": "Correlation Rules",
            },
        ),
        migrations.CreateModel(
            name="MonitorToolIP",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("ip", models.GenericIPAddressField(primary_key=True, protocol="IPv4", serialize=False)),
                ("region", models.TextField(default="global", max_length=200)),
                (
                    "monitor_tool",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ips",
                        related_query_name="ip",
                        to="launchpad.monitortool",
                    ),
                ),
            ],
            options={
                "verbose_name": "Monitor Tool IP",
                "verbose_name_plural": "Monitor Tool IPs",
            },
        ),
        migrations.CreateModel(
            name="MonitorToolPipelineRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "order_no",
                    models.PositiveSmallIntegerField(
                        default=0,
                        help_text="Order in which the rule should be executed."
                        + " Multiple rules, that are not dependent on each other, can have same order",
                    ),
                ),
                (
                    "rule_type",
                    models.TextField(
                        choices=[
                            ("asset_id", "Asset Unique Id Rule"),
                            ("event_type", "Event Type Rule"),
                            ("set", "Set Rule"),
                            ("grok", "Grok Rule"),
                            ("remove", "Remove Rule"),
                        ],
                        db_index=True,
                        default="set",
                        help_text="Each monitor tool pipeline should have one rule each for 'Asset Unique Id Rule' and"
                        + " 'Event Type Rule'. Other rules can be used multiple times to define other fields"
                        + " (including temporary fields).",
                    ),
                ),
                (
                    "event_type_default",
                    models.TextField(
                        blank=True,
                        choices=[
                            ("up", "Up"),
                            ("down", "Down"),
                            ("neutral", "Neutral"),
                            ("<<missing>>", "Error: Field Not Found"),
                        ],
                        help_text="Defines the default event type for each incoming event.",
                        null=True,
                        verbose_name="Default Event Type",
                    ),
                ),
                (
                    "event_type_field",
                    models.TextField(
                        blank=True,
                        help_text="Original field that will be copied to Event Type.",
                        null=True,
                        verbose_name="From Field Name for Event Type Rule",
                    ),
                ),
                (
                    "event_type_up_values",
                    models.TextField(
                        blank=True,
                        help_text="Comma separated list of values that identify UP Event Type.",
                        null=True,
                        verbose_name="Values for UP Event Type",
                    ),
                ),
                (
                    "event_type_down_values",
                    models.TextField(
                        blank=True,
                        help_text="Comma separated list of values that identify DOWN Event Type.",
                        null=True,
                        verbose_name="Values for DOWN Event Type",
                    ),
                ),
                (
                    "event_type_neutral_values",
                    models.TextField(
                        blank=True,
                        help_text="Comma separated list of values that identify NEUTRAL Event Type.",
                        null=True,
                        verbose_name="Values for NEUTRAL Event Type",
                    ),
                ),
                (
                    "set_field",
                    models.TextField(
                        blank=True,
                        help_text="Check ELK's Set Processor for Ingest Pipeline."
                        + " Supports template snippet (not recommended for Field Name).",
                        null=True,
                        verbose_name="Field Name for Set Rule",
                    ),
                ),
                (
                    "set_value",
                    models.TextField(
                        blank=True,
                        help_text="Check ELK's Set Processor for Ingest Pipeline. Supports template snippet."
                        + " Set Value will be treated as Copy From Field if 'Set Copy From Flag' is enabled"
                        + " [dont use template snippet in such case].",
                        null=True,
                        verbose_name="Value / Copy From",
                    ),
                ),
                (
                    "set_copy_from_flag",
                    models.BooleanField(
                        default=False,
                        help_text="Check ELK's Set Processor for Ingest Pipeline."
                        + " If enabled, Set Value will be treated as Copy From Field."
                        + " Set Value will not support template snippet in that case.",
                        verbose_name="Use Copy From flag",
                    ),
                ),
                (
                    "override_flag",
                    models.BooleanField(
                        default=True,
                        help_text="Check ELK's Set Processor for Ingest Pipeline.",
                        verbose_name="Override flag",
                    ),
                ),
                (
                    "ignore_empty_value_flag",
                    models.BooleanField(
                        default=False,
                        help_text="Check ELK's Set Processor for Ingest Pipeline.",
                        verbose_name="Ignore Empty Value flag",
                    ),
                ),
                (
                    "grok_field",
                    models.TextField(
                        blank=True,
                        help_text="Field to use for grok expression parsing. Check ELK's Grok Processor for Ingest Pipeline.",
                        null=True,
                        verbose_name="Field Name for Grok Rule",
                    ),
                ),
                (
                    "grok_patterns",
                    models.JSONField(
                        blank=True,
                        help_text="An ordered list of grok expression to match and extract named captures with."
                        + " Returns on the first expression in the list that matches."
                        + " Check ELK's Grok Processor for Ingest Pipeline.",
                        null=True,
                        verbose_name="Patterns",
                    ),
                ),
                (
                    "grok_pattern_definitions",
                    models.JSONField(
                        blank=True,
                        help_text="A map of pattern-name and pattern tuples defining custom patterns to be used by the"
                        + " current processor. Patterns matching existing names will override the pre-existing"
                        + " definition. Check ELK's Grok Processor for Ingest Pipeline.",
                        null=True,
                        verbose_name="Pattern Definitions",
                    ),
                ),
                (
                    "remove_field",
                    models.TextField(
                        blank=True,
                        help_text="Check ELK's Remove Processor for Ingest Pipeline."
                        + " Always better to remove fields (esp. temporary ones) that are not required."
                        + " Supports template snippet (not recommended).",
                        null=True,
                        verbose_name="Field to be removed",
                    ),
                ),
                (
                    "ignore_missing_flag",
                    models.BooleanField(
                        default=False,
                        help_text=" Check ELK's Grok / Remove Processor for Ingest Pipeline.",
                        verbose_name="Ignore Missing flag",
                    ),
                ),
                (
                    "if_condition",
                    models.TextField(
                        blank=True,
                        help_text=" Check ELK's Set / Grok / Remove Processor for Ingest Pipeline.",
                        null=True,
                        verbose_name="IF Condition",
                    ),
                ),
                (
                    "ignore_failure_flag",
                    models.BooleanField(
                        default=False,
                        help_text=" Check ELK's Set / Grok / Remove Processor for Ingest Pipeline.",
                        verbose_name="Ignore Failure flag",
                    ),
                ),
                (
                    "monitor_tool",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pipeline_rules",
                        related_query_name="pipeline_rule",
                        to="launchpad.monitortool",
                    ),
                ),
            ],
            options={
                "verbose_name": "Monitor Tool Pipeline Rule",
                "verbose_name_plural": "Monitor Tool Pipeline Rules",
            },
        ),
        migrations.CreateModel(
            name="EventLevelBasedSubRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("event_level", models.TextField(db_index=True)),
                ("itsm_severity", models.PositiveSmallIntegerField()),
                (
                    "do_not_create_ticket_flag",
                    models.BooleanField(
                        default=False, help_text="If True, ITSM ticket won't be created for such event levels"
                    ),
                ),
                (
                    "correlation_rule",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="event_level_based_sub_rules",
                        related_query_name="event_level_based_sub_rule",
                        to="launchpad.correlationrule",
                    ),
                ),
            ],
            options={
                "verbose_name": "Event Level based Sub Rule",
                "verbose_name_plural": "Event Level based Sub Rules",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("correlation_rule", "event_level"), name="unique_event_level_based_sub_rule"
                    )
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="correlationrule",
            constraint=models.UniqueConstraint(fields=("monitor_tool", "event_title"), name="unique_correlation_rule"),
        ),
    ]
