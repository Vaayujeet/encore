"""Constants required for GLPi"""

from django.db.models import IntegerChoices, TextChoices

REQUESTOR_SOURCE_ID = 8


class TicketState(IntegerChoices):
    """GLPI Ticket State"""

    NEW = 1
    PROCESSING_ASSIGNED = 2
    PROCESSING_PLANNED = 3
    PENDING = 4
    SOLVED = 5
    CLOSED = 6


GLPI_TICKET_SEVERITY_MAP = {
    1: 4,  # Sev1 : Value to pass to GLPI (4)
    2: 3,  # Sev2 : Value to pass to GLPI (3)
    3: 2,  # Sev3 : Value to pass to GLPI (2)
    4: 1,  # Sev4 : Value to pass to GLPI (1)
}


class CustomFieldNames(TextChoices):
    """GLPI Custom Field Names"""

    # Common
    SOME_CUSTOM_FIELD = "mycustomfield"
