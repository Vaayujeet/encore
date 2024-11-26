"""Constants required for Elasticsearch"""

from django.db.models import TextChoices

EVENT_INDEX_PREFIX = "events"
EVENT_INDEX_RE = f"{EVENT_INDEX_PREFIX}-*"
EVENT_ID_DATETIME_FORMAT = "%Y%m%d%H%M%S%f"
INDEX_DATE_SUFFIX_FORMAT = "%Y%m%d"


class EventType(TextChoices):
    """Event Type"""

    UP = "up"  # Event informing Asset is up and running
    DOWN = "down"  # Event informing Asset is down (or probably some issue - e.g. disk usage above threshold limit)
    NEUTRAL = "neutral"  # Event that provide additional info about the Asset
    ERROR_FIELD_NOT_FOUND = (
        "<<missing>>",
        "Error: Field Not Found",
    )  # OTHERS = basically all other values will fall under this EventType


class EventStatus(TextChoices):
    """Event Status"""

    # Active Status
    NEW = "new"
    SUPPRESSED = "suppressed"
    CREATING_TICKET = "creating_ticket"
    ALERTED = "alerted"

    # Transition Status
    RESOLVING = "resolving"  # Child Events may not have Resolved.

    # Completed Status
    RESOLVED = "resolved"
    DEDUPED = "deduped"
    ERROR = "error"


ACTIVE_EVENT_STATUS = {
    EventStatus.NEW,
    EventStatus.SUPPRESSED,
    EventStatus.CREATING_TICKET,
    EventStatus.ALERTED,
}

COMPLETE_EVENT_STATUS = {
    EventStatus.RESOLVED,
    EventStatus.DEDUPED,
    EventStatus.ERROR,
}

NON_ACTIVE_EVENT_STATUS = set(EventStatus) - ACTIVE_EVENT_STATUS
NON_COMPLETE_EVENT_STATUS = set(EventStatus) - COMPLETE_EVENT_STATUS


class ResolvingAction(TextChoices):
    """Resolving Action"""

    # Below Conditions should be met before current Event is RESOLVED

    NEW = "new"  # All Active Child Events should be moved to NEW
    SUPP = "supp"  # All Active Child Events should be RESOLVED
    MANUAL = "manual"  # All Active Child Events should be (manually) RESOLVED
    CLOSE_TICKET = "close_ticket"  # All Active Child Events should be RESOLVED + ITSM is Closed


class FieldNames(TextChoices):
    """Field Names used in Elastic"""

    # INFO: [Main-Rule] => Main Event Pipeline will define this field with appropriate values.
    # INFO: [Tool-Rule] => User SHOULD define MonitorToolPipelineRule to extract this information.
    # INFO: [Optional] => User may or may not define MonitorToolPipelineRule to extract this information.
    # INFO: [Process] => Correlator process will maintain this field.
    # INFO: [Missing-Invalid] => Event will move to Error status if field is missing or has Invalid value.

    # # Event Info
    # EVENT_ID = "_id"
    # ~~ [Optional] Description that can be used for ITSM description
    EVENT_DESC = "event_desc"
    # ~~ [Process] Actual event info received by the correlator is stored in this field as json
    EVENT_DETAILS = "event_details"
    # ~~ [Optional] Severity e.g. warning/critical/ok. If present can be used to apply EventLevelBasedSubRule
    EVENT_LEVEL = "event_level"
    # ~~ [Main-Rule] See above Event Status class
    EVENT_STATUS = "status"
    # ~~ [Tool-Rule][Missing-Invalid] Title / Name - Used to lookup Correlation Rule. Used for dedupe logic.
    EVENT_TITLE = "event_title"
    # ~~ [Tool-Rule][Main-Rule] # Actual TimeStamp the event was created/raised by the source asset/monitor tool
    #     If Tool-Rule does not define this field, Main-Rule will define this field using RECEIVED_TS
    EVENT_TS = "event_ts"
    # ~~ [Tool-Rule][Missing-Invalid] # up/down below/above threshold
    EVENT_TYPE = "event_type"

    # # Asset Info
    # ~~ [Tool-Rule][Missing-Invalid]
    ASSET_UNIQUE_ID = "asset_unique_id"
    # ~~ [Main-Rule] Asset Type/Region and Parent Info is extracted from Asset Mapping
    ASSET_TYPE = "asset_type"  # Hardware (e.g. Server, Router) or Software (e.g. Application)
    ASSET_REGION = "asset_region"
    # TODO: accomodate assets with multiple parents
    PARENT_ASSET_UNIQUE_ID = "parent_asset_unique_id"
    PARENT_ASSET_TYPE = "parent_asset_type"

    # # Common Configuration Item Info
    # ~~ [Optional]
    APPLICATION_NAME = "appl_name"
    HOST_IP = "host_ip"
    HOST_NAME = "host_name"
    HOST_TYPE = "host_type"

    # # Meta Fields [Process]
    TOOL_IP = "monitor_tool_ip"
    TOOL_NAME = "monitor_tool_name"  # [Main-Rule] Defaults to "Default Tool"
    METHOD = "method"  # how event was reported (API-POST or SNMP)
    RECEIVED_TS = "received_ts"  # TimeStamp the event was received by the correlator
    LAST_UPDATE_TS = "last_update_ts"
    MANUAL_RESOLVE_TS = "manual_resolve_ts"
    ERROR_REASON = "error_reason"
    RESOLVING_ACTION = "resolving_action"
    SUPP_TO_NEW = "supp_to_new"  # Indicates that this SUPPRESSED Event needs to be moved to NEW status
    # # Interconnection Link Info [Process]
    INITIAL_EVENT = "initial_event_id"
    INITIAL_EVENT_INDEX = "initial_event_index"
    PARENT_EVENT = "parent_event_id"
    PARENT_EVENT_INDEX = "parent_event_index"
    LINKED_EVENT = "linked_event_id"
    LINKED_EVENT_INDEX = "linked_event_index"
    ITSM_TICKET = "itsm_ticket"


class EventExtrasKey(TextChoices):
    """Keys in Extras field of Event Model"""

    TICKET_ID = "ticket_id"
    TICKET_COMMENT_ASSET_IS_DOWN = "asset_down_comment"  # A comment was added to ticket that the Asset is Down
    TICKET_COMMENT_ASSET_IS_UP = "asset_up_comment"  # A comment was added to ticket that the Asset is Up
