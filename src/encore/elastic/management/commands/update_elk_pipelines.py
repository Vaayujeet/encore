"""Manage ELK Ingest Pipelines and Enrich Policies"""

import logging

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandParser
from django.db.models.query import QuerySet

from elastic.constants import EventStatus, EventType, FieldNames
from elastic.utils import CorrelatorElastic
from launchpad.models import MonitorTool, MonitorToolPipelineRule

logger = logging.getLogger("correlator.elastic.update_elk_pipelines")


class Command(BaseCommand):
    """Manage ELK Ingest Pipelines and Enrich Policies Command"""

    def __init__(self) -> None:
        super().__init__()
        self.es = CorrelatorElastic()

    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("-m", "--monitor-tool", help="Update pipeline for monitor tool.")

    def handle(self, *args, **options) -> str | None:
        # TODO: Make use of the monitor_tool arg
        # _monitor_tool = options["monitor_tool"]

        logger.info("Started Manage ELK Pipelines process")

        # Create latest Enrich Policy definition if it does not exist.
        for enrich_policy_name in self.es.enrich_policy_definitions:
            self.es.create_enrich_policy(enrich_policy_name)

        # Create/Update pipelines
        create_default_tool_pipeline = True
        for monitor_tool in MonitorTool.objects.all():
            if monitor_tool.pipeline_name == settings.DEFAULT_TOOL_PIPELINE:
                create_default_tool_pipeline = False
                if monitor_tool.pipeline_rules.count() == 0:
                    self.create_update_default_tool_event_pipeline()
                    continue
            self.create_update_tool_event_pipeline(monitor_tool)
        if create_default_tool_pipeline:
            self.create_update_default_tool_event_pipeline()
        self.create_update_main_event_pipeline()

        # Delete old Enrich Policy definitions if they exist.
        for enrich_policy_name in self.es.enrich_policy_definitions:
            self.es.delete_old_enrich_policy(enrich_policy_name)

        # Create/Update Index Template
        call_command("update_index_template")

        logger.info("Completed Manage ELK Pipelines process")

    def create_update_tool_event_pipeline(self, monitor_tool: MonitorTool):
        """Create/Update Mapping Tool Event pipeline using rules which is used to extract certain fields"""
        processors = []
        add_event_type_rule = True
        rules: QuerySet[MonitorToolPipelineRule] = monitor_tool.pipeline_rules.order_by("order_no")
        for rule in rules:
            _order_no, rule_type, rule_def = rule.ingest_pipeline_rule
            if rule_type in (
                MonitorToolPipelineRule.RuleType.ASSET_UNIQUE_ID_RULE,
                MonitorToolPipelineRule.RuleType.SET_RULE,
                MonitorToolPipelineRule.RuleType.GROK_RULE,
                MonitorToolPipelineRule.RuleType.REMOVE_RULE,
            ):
                if rule_type == MonitorToolPipelineRule.RuleType.ASSET_UNIQUE_ID_RULE:
                    rule_type = MonitorToolPipelineRule.RuleType.SET_RULE
                processors.append({rule_type: rule_def})
                continue

            if rule_type == MonitorToolPipelineRule.RuleType.EVENT_TYPE_RULE:
                add_event_type_rule = False
                if "value" in rule_def:
                    processors.append({"set": rule_def})
                else:  # if "from" in rule_def
                    processors.append(
                        {
                            "lowercase": {
                                "field": rule_def["from"],
                                "target_field": FieldNames.EVENT_TYPE,
                                "tag": f"{rule_def["tag"]}-lowercase",
                                "on_failure": [
                                    {
                                        "set": {
                                            "field": FieldNames.EVENT_TYPE,
                                            "value": EventType.ERROR_FIELD_NOT_FOUND,
                                            "tag": f"{rule_def["tag"]}-{EventType.ERROR_FIELD_NOT_FOUND}",
                                        }
                                    }
                                ],
                            }
                        }
                    )

                    for event_type in [EventType.DOWN, EventType.UP, EventType.NEUTRAL]:
                        if event_type in rule_def and rule_def[event_type]:
                            _condition = f"ctx['{FieldNames.EVENT_TYPE}'] == '{rule_def[event_type][0].lower()}'"
                            for value in rule_def[event_type][1:]:
                                _condition += f" || ctx['{FieldNames.EVENT_TYPE}'] == '{value.lower()}'"
                            processors.append(
                                {
                                    "set": {
                                        "field": FieldNames.EVENT_TYPE,
                                        "value": event_type,
                                        "if": _condition,
                                        "tag": f"{rule_def["tag"]}-{event_type}",
                                    }
                                }
                            )

        if add_event_type_rule:
            processors.append(
                {
                    "lowercase": {
                        "field": f"{FieldNames.EVENT_DETAILS}.{FieldNames.EVENT_TYPE}",
                        "target_field": FieldNames.EVENT_TYPE,
                        "tag": f"set-{FieldNames.EVENT_TYPE}-lowercase",
                        "on_failure": [
                            {
                                "set": {
                                    "field": FieldNames.EVENT_TYPE,
                                    "value": EventType.ERROR_FIELD_NOT_FOUND,
                                    "tag": f"set-{FieldNames.EVENT_TYPE}-as-{EventType.ERROR_FIELD_NOT_FOUND}",
                                }
                            }
                        ],
                    }
                }
            )
        self.es.ingest.put_pipeline(id=monitor_tool.pipeline_name, processors=processors)
        logger.info("Created/Updated %s", monitor_tool.pipeline_name)

    def create_update_default_tool_event_pipeline(self):
        """Create/Update a Default Mapping Tool Event pipeline"""
        processors = [
            {
                "set": {
                    "field": FieldNames.TOOL_NAME,
                    "value": settings.DEFAULT_TOOL_NAME,
                    "if": f"ctx['{FieldNames.TOOL_NAME}'] == null",
                    "tag": f"set-{FieldNames.TOOL_NAME}",
                }
            },
            {
                "set": {
                    "field": FieldNames.ASSET_UNIQUE_ID,
                    "copy_from": f"{FieldNames.EVENT_DETAILS}.{FieldNames.ASSET_UNIQUE_ID}",
                    "ignore_empty_value": True,
                    "if": f"ctx['{FieldNames.EVENT_DETAILS}'].containsKey('{FieldNames.ASSET_UNIQUE_ID}')",
                    "tag": f"set-{FieldNames.ASSET_UNIQUE_ID}",
                }
            },
            {
                "set": {
                    "field": FieldNames.EVENT_DESC,
                    "copy_from": f"{FieldNames.EVENT_DETAILS}.{FieldNames.EVENT_DESC}",
                    "ignore_empty_value": True,
                    "if": f"ctx['{FieldNames.EVENT_DETAILS}'].containsKey('{FieldNames.EVENT_DESC}')",
                    "tag": f"set-{FieldNames.EVENT_DESC}",
                }
            },
            {
                "set": {
                    "field": FieldNames.EVENT_LEVEL,
                    "copy_from": f"{FieldNames.EVENT_DETAILS}.{FieldNames.EVENT_LEVEL}",
                    "ignore_empty_value": True,
                    "if": f"ctx['{FieldNames.EVENT_DETAILS}'].containsKey('{FieldNames.EVENT_LEVEL}')",
                    "tag": f"set-{FieldNames.EVENT_LEVEL}",
                }
            },
            {
                "set": {
                    "field": FieldNames.EVENT_TITLE,
                    "copy_from": f"{FieldNames.EVENT_DETAILS}.{FieldNames.EVENT_TITLE}",
                    "ignore_empty_value": True,
                    "if": f"ctx['{FieldNames.EVENT_DETAILS}'].containsKey('{FieldNames.EVENT_TITLE}')",
                    "tag": f"set-{FieldNames.EVENT_TITLE}",
                }
            },
            {
                # TODO: Use Date Processor
                "set": {
                    "field": FieldNames.EVENT_TS,
                    "copy_from": f"{FieldNames.EVENT_DETAILS}.{FieldNames.EVENT_TS}",
                    "ignore_empty_value": True,
                    "if": f"ctx['{FieldNames.EVENT_DETAILS}'].containsKey('{FieldNames.EVENT_TS}')",
                    "tag": f"set-{FieldNames.EVENT_TS}",
                }
            },
            {
                "lowercase": {
                    "field": f"{FieldNames.EVENT_DETAILS}.{FieldNames.EVENT_TYPE}",
                    "target_field": FieldNames.EVENT_TYPE,
                    "tag": f"set-{FieldNames.EVENT_TYPE}-lowercase",
                    "on_failure": [
                        {
                            "set": {
                                "field": FieldNames.EVENT_TYPE,
                                "value": EventType.ERROR_FIELD_NOT_FOUND,
                                "tag": f"set-{FieldNames.EVENT_TYPE}-as-{EventType.ERROR_FIELD_NOT_FOUND}",
                            }
                        }
                    ],
                }
            },
        ]
        self.es.ingest.put_pipeline(id=settings.DEFAULT_TOOL_PIPELINE, processors=processors)
        logger.info("Created/Updated %s", settings.DEFAULT_TOOL_PIPELINE)

    def create_update_main_event_pipeline(self):
        """Create/Update a Event pipeline which is used to ingest Events into Events Index"""
        processors = [
            # Monitor Tool Pipeline
            {
                "pipeline": {
                    "name": tool.pipeline_name,
                    "if": f"ctx.{FieldNames.TOOL_NAME} == '{tool.name}'",
                    "tag": f"pipeline-{tool.pipeline_name}",
                }
            }
            for tool in MonitorTool.objects.all()
        ]

        processors.extend(
            [
                # Default Monitor Tool Pipeline
                {
                    "pipeline": {
                        "name": settings.DEFAULT_TOOL_PIPELINE,
                        "if": f"ctx['{FieldNames.TOOL_NAME}'] == null",
                        "tag": f"pipeline-{settings.DEFAULT_TOOL_PIPELINE}",
                    }
                },
                # Enrich with Asset Mapping Data
                {
                    "enrich": {
                        "field": FieldNames.ASSET_UNIQUE_ID,
                        "policy_name": self.es.latest_enrich_policy_name(settings.ASSET_MAPPING_POLICY),
                        "target_field": "asset",
                        "if": f"ctx.containsKey('{FieldNames.ASSET_UNIQUE_ID}')"
                        + f" && ctx['{FieldNames.ASSET_UNIQUE_ID}'] != null",
                        "tag": "enrich-asset",
                    }
                },
                {
                    "set": {
                        "field": FieldNames.ASSET_TYPE,
                        "copy_from": f"asset.{FieldNames.ASSET_TYPE}",
                        "override": False,
                        "ignore_empty_value": True,
                        "if": "ctx.containsKey('asset')",
                        "tag": f"set-{FieldNames.ASSET_TYPE}-from-asset",
                    }
                },
                {
                    "set": {
                        "field": FieldNames.ASSET_REGION,
                        "copy_from": f"asset.{FieldNames.ASSET_REGION}",
                        "override": False,
                        "ignore_empty_value": True,
                        "if": "ctx.containsKey('asset')",
                        "tag": f"set-{FieldNames.ASSET_REGION}-from-asset",
                    }
                },
                {
                    "set": {
                        "field": FieldNames.PARENT_ASSET_UNIQUE_ID,
                        "copy_from": f"asset.{FieldNames.PARENT_ASSET_UNIQUE_ID}",
                        "if": "ctx.containsKey('asset')",
                        "tag": f"set-{FieldNames.PARENT_ASSET_UNIQUE_ID}-from-asset",
                    }
                },
                {
                    "set": {
                        "field": FieldNames.PARENT_ASSET_TYPE,
                        "copy_from": f"asset.{FieldNames.PARENT_ASSET_TYPE}",
                        "if": "ctx.containsKey('asset')",
                        "tag": f"set-{FieldNames.PARENT_ASSET_TYPE}-from-asset",
                    }
                },
                {"remove": {"field": "asset", "ignore_missing": True, "tag": "remove-asset"}},
                # Initiate required fields
                {
                    "set": {
                        "field": FieldNames.INITIAL_EVENT,
                        "copy_from": "_id",
                        "tag": f"set-{FieldNames.INITIAL_EVENT}-from-id",
                    }
                },
                {
                    "set": {
                        "field": FieldNames.INITIAL_EVENT_INDEX,
                        "copy_from": "_index",
                        "tag": f"set-{FieldNames.INITIAL_EVENT_INDEX}-from-index",
                    }
                },
                {
                    "set": {
                        "field": FieldNames.EVENT_TYPE,
                        "value": EventType.ERROR_FIELD_NOT_FOUND,
                        "if": f"!ctx.containsKey('{FieldNames.EVENT_TYPE}')",
                        "tag": f"set-{FieldNames.EVENT_TYPE}-as-{EventType.ERROR_FIELD_NOT_FOUND}",
                    }
                },
                {
                    "set": {
                        "field": FieldNames.EVENT_STATUS,
                        "value": EventStatus.NEW,
                        "tag": f"set-{FieldNames.EVENT_STATUS}-as-{EventStatus.NEW}",
                    }
                },
                # Check required Fields: ASSET_UNIQUE_ID / EVENT_TITLE / EVENT_TYPE
                {
                    "append": {
                        "field": FieldNames.ERROR_REASON,
                        "value": f"{FieldNames.ASSET_UNIQUE_ID} is missing.",
                        "if": f"!ctx.containsKey('{FieldNames.ASSET_UNIQUE_ID}') || "
                        + f"ctx['{FieldNames.ASSET_UNIQUE_ID}'] == null",
                        "tag": f"append-{FieldNames.ERROR_REASON}-{FieldNames.ASSET_UNIQUE_ID}",
                    }
                },
                {
                    "append": {
                        "field": FieldNames.ERROR_REASON,
                        "value": f"{FieldNames.EVENT_TITLE} is missing.",
                        "if": f"!ctx.containsKey('{FieldNames.EVENT_TITLE}') || "
                        + f"ctx['{FieldNames.EVENT_TITLE}'] == null",
                        "tag": f"append-{FieldNames.ERROR_REASON}-{FieldNames.EVENT_TITLE}",
                    }
                },
                {
                    "append": {
                        "field": FieldNames.ERROR_REASON,
                        "value": f"{FieldNames.EVENT_TYPE} is missing/invalid.",
                        "if": f"ctx['{FieldNames.EVENT_TYPE}'] != '{EventType.DOWN}' && "
                        + f"    ctx['{FieldNames.EVENT_TYPE}'] != '{EventType.UP}' && "
                        + f"    ctx['{FieldNames.EVENT_TYPE}'] != '{EventType.NEUTRAL}'",
                        "tag": f"append-{FieldNames.ERROR_REASON}-{FieldNames.EVENT_TYPE}",
                    }
                },
                {
                    "join": {
                        "field": FieldNames.ERROR_REASON,
                        "separator": " ",
                        "if": f"ctx.containsKey('{FieldNames.ERROR_REASON}')",
                        "tag": f"join-{FieldNames.ERROR_REASON}",
                    }
                },
                {
                    "set": {
                        "field": FieldNames.EVENT_STATUS,
                        "value": EventStatus.ERROR,
                        "if": f"ctx.containsKey('{FieldNames.ERROR_REASON}')",
                        "tag": f"set-{FieldNames.EVENT_STATUS}-as-{EventStatus.ERROR}",
                    }
                },
                {
                    "set": {
                        "field": FieldNames.EVENT_TS,
                        "copy_from": FieldNames.RECEIVED_TS,
                        "if": f"!ctx.containsKey('{FieldNames.EVENT_TS}')",
                        "tag": f"set-{FieldNames.EVENT_TS}-using-{FieldNames.RECEIVED_TS}",
                    }
                },
                {"set": {"field": FieldNames.LAST_UPDATE_TS, "copy_from": "_ingest.timestamp"}},
            ]
        )

        self.es.ingest.put_pipeline(id=settings.MAIN_PIPELINE, processors=processors)
        logger.info("Created/Updated %s", settings.MAIN_PIPELINE)
