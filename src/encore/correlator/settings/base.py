"""Basic Settings"""

from pydantic_settings import BaseSettings


class BasicSettings(BaseSettings):
    """Base Settings class
    Will use values from env variables else the default values.
    """

    ELASTIC_CONTAINER: bool = False
    GLPI_CONTAINER: bool = False


base_settings = BasicSettings()

ELASTIC_CONTAINER = base_settings.ELASTIC_CONTAINER
GLPI_CONTAINER = base_settings.GLPI_CONTAINER

SHELL_PLUS_IMPORTS = [
    "from elastic.constants import EventType, EventStatus, ACTIVE_EVENT_STATUS, COMPLETE_EVENT_STATUS,"
    + " NON_ACTIVE_EVENT_STATUS, NON_COMPLETE_EVENT_STATUS, ResolvingAction, FieldNames, EventExtrasKey",
    "from elastic.utils import CorrelatorElastic, SearchResponseType",
    """
    from elastic.tasks import (
        process_alerted_event,
        process_creating_ticket_event,
        ingest_event,
        process_new_down_event,
        process_new_up_event,
        purge_db_events_and_apilogs,
        purge_event_indices,
        resolve_event,
        process_resolving_event,
        process_suppressed_event,
    )
    """,
    "from elastic.tasks.common import task_handler",
    "from glpi.utils import get_glpi_session, kill_glpi_session, get_ticket, add_comment",
]
