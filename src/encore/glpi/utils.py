"""GLPI Utils"""

import json
import logging
import typing as t

import requests

from django.conf import settings

from glpi.constants import REQUESTOR_SOURCE_ID, CustomFieldNames, TicketState

logger = logging.getLogger("correlator.glpi")

CONTENT_TYPE = "application/json"


class GLPIException(Exception):
    """GLPI Exception"""

    def __init__(self, message, status_code) -> None:
        self.message = message
        self.status_code = status_code


# TODO: Can we convert this to something like CorrelatorElastic


def _get_session_header(session: str) -> t.Dict[str, str]:
    return {"Session-Token": session, "Content-Type": CONTENT_TYPE, "App-Token": settings.GLPI_APP_TOKEN}


def get_glpi_session():
    """Get Session Token"""
    logger.debug("Starting a session on GLPI Host %s", settings.GLPI_HOST)
    response = requests.get(
        settings.GLPI_INIT_SESSION_URL,
        headers={
            "Content-Type": CONTENT_TYPE,
            "App-Token": settings.GLPI_APP_TOKEN,
            "Authorization": f"user_token {settings.GLPI_API_TOKEN}",
        },
        timeout=settings.GLPI_TIMEOUT_IN_SECONDS,
    )
    if response.status_code == 200:
        logger.debug("Session started on GLPI Host %s", settings.GLPI_HOST)
        return response.json().get("session_token")
    else:
        raise GLPIException(f"Failed to start a session on GLPI Host {settings.GLPI_HOST}", response.status_code)


def kill_glpi_session(session: str):
    """Kill Session Token"""
    logger.debug("Killing session on GLPI Host %s", settings.GLPI_HOST)
    response = requests.get(
        settings.GLPI_KILL_SESSION_URL,
        headers=_get_session_header(session),
        timeout=settings.GLPI_TIMEOUT_IN_SECONDS,
    )
    if response.status_code == 200:
        logger.debug("Session killed on GLPI Host %s", settings.GLPI_HOST)
    else:
        raise GLPIException(f"Failed to kill the session on GLPI Host {settings.GLPI_HOST}", response.status_code)


def create_ticket(
    session: str,
    title: str,
    desc: str,
    assigned_group_id: t.Optional[int] = None,
    severity: t.Optional[int] = None,
    my_custom_field: t.Optional[str] = None,
):
    """Create GLPI Ticket"""

    logger.debug("Creating ticket %s on GLPI Host %s", title, settings.GLPI_HOST)

    ticket_data = {
        "input": {
            "name": title,
            "content": desc,
            "status": TicketState.NEW,
            "_groups_id_assign": assigned_group_id,
            "requesttypes_id": REQUESTOR_SOURCE_ID,
            "priority": severity,
            CustomFieldNames.SOME_CUSTOM_FIELD: my_custom_field,
        }
    }

    response = requests.post(
        settings.GLPI_TICKET_URL,
        headers=_get_session_header(session),
        data=json.dumps(ticket_data),
        timeout=settings.GLPI_TIMEOUT_IN_SECONDS,
    )

    if response.status_code == 201:
        ticket_id = response.json().get("id")
        logger.debug("Created ticket [#%s] %s on GLPI Host %s", ticket_id, title, settings.GLPI_HOST)
        return ticket_id
    else:
        raise GLPIException(f"Failed to create ticket {title} on GLPI Host {settings.GLPI_HOST}", response.status_code)


def get_ticket(session: str, ticket_id: int):
    """Create GLPI Ticket"""

    logger.debug("Getting ticket %s from GLPI Host %s", ticket_id, settings.GLPI_HOST)

    response = requests.get(
        f"{settings.GLPI_TICKET_URL}/{ticket_id}",
        headers=_get_session_header(session),
        timeout=settings.GLPI_TIMEOUT_IN_SECONDS,
    )

    if response.status_code == 200:
        logger.debug("Got ticket %s from GLPI Host %s", ticket_id, settings.GLPI_HOST)
        return response.json()
    else:
        raise GLPIException(
            f"Failed to get ticket {ticket_id} from GLPI Host {settings.GLPI_HOST}", response.status_code
        )


def update_ticket(
    session: str,
    ticket_id: int,
    desc: t.Optional[str] = None,
    status: t.Optional[TicketState] = None,
    assigned_group_id: t.Optional[int] = None,
):
    """Update GLPI Ticket Description / Status / Assigned Group"""

    logger.debug("Updating ticket %s on GLPI Host %s", ticket_id, settings.GLPI_HOST)

    update_data: t.Dict[str, t.Dict[str, str | int]] = {"input": {}}
    if desc:
        update_data["input"]["content"] = desc
    if status:
        update_data["input"]["status"] = status
    if assigned_group_id:
        update_data["input"]["_groups_id_assign"] = assigned_group_id

    response = requests.put(
        f"{settings.GLPI_TICKET_URL}/{ticket_id}",
        headers=_get_session_header(session),
        data=json.dumps(update_data),
        timeout=settings.GLPI_TIMEOUT_IN_SECONDS,
    )

    if response.status_code == 200:
        logger.debug("Updated ticket %s on GLPI Host %s", ticket_id, settings.GLPI_HOST)
    else:
        raise GLPIException(
            f"Failed to update ticket {ticket_id} from GLPI Host {settings.GLPI_HOST}", response.status_code
        )


def add_comment(session: str, ticket_id: int, comment: str):
    """Add comment to GLPI Ticket"""

    logger.debug("Adding comment to ticket %s on GLPI Host %s", ticket_id, settings.GLPI_HOST)

    comment_data = {"input": {"items_id": ticket_id, "itemtype": "Ticket", "content": comment}}

    response = requests.post(
        settings.GLPI_TICKET_COMMENT_URL.format(ticket_id),
        headers=_get_session_header(session),
        data=json.dumps(comment_data),
        timeout=settings.GLPI_TIMEOUT_IN_SECONDS,
    )

    if response.status_code == 201:
        logger.debug("Added comment to ticket %s on GLPI Host %s", ticket_id, settings.GLPI_HOST)
    else:
        raise GLPIException(
            f"Failed to add comment to ticket {ticket_id} from GLPI Host {settings.GLPI_HOST}", response.status_code
        )


def close_ticket(session: str, ticket_id: int):
    """Solve GLPI Ticket."""

    logger.debug("Closing ticket %s on GLPI Host %s", ticket_id, settings.GLPI_HOST)

    response = requests.put(
        f"{settings.GLPI_TICKET_URL}/{ticket_id}",
        headers=_get_session_header(session),
        data=json.dumps({"input": {"status": TicketState.SOLVED}}),
        timeout=settings.GLPI_TIMEOUT_IN_SECONDS,
    )

    if response.status_code == 200:
        logger.debug("Closed ticket %s on GLPI Host %s", ticket_id, settings.GLPI_HOST)
    else:
        raise GLPIException(
            f"Failed to close ticket {ticket_id} from GLPI Host {settings.GLPI_HOST}", response.status_code
        )
