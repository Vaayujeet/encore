"""GLPI Settings"""

from pydantic_settings import BaseSettings


class GLPISettings(BaseSettings):
    """GLPI Settings class
    Will use values from env variables else the default values.
    """

    GLPI_HOST: str = "http://glpi:80"
    GLPI_BASE_URL: str = f"{GLPI_HOST}/apirest.php"
    GLPI_APP_TOKEN: str = "app-token is required"
    GLPI_API_TOKEN: str = "user-api-token is required"

    GLPI_TIMEOUT_IN_SECONDS: int = 300


GLPI_settings = GLPISettings()

GLPI_HOST = GLPI_settings.GLPI_HOST
GLPI_BASE_URL = GLPI_settings.GLPI_BASE_URL

GLPI_APP_TOKEN = GLPI_settings.GLPI_APP_TOKEN
GLPI_API_TOKEN = GLPI_settings.GLPI_API_TOKEN

GLPI_TIMEOUT_IN_SECONDS = GLPI_settings.GLPI_TIMEOUT_IN_SECONDS

GLPI_INIT_SESSION_URL = f"{GLPI_BASE_URL}/initSession"
GLPI_KILL_SESSION_URL = f"{GLPI_BASE_URL}/killSession"
GLPI_TICKET_URL = f"{GLPI_BASE_URL}/Ticket"
GLPI_TICKET_COMMENT_URL = GLPI_TICKET_URL + "/{}/ITILFollowup"
