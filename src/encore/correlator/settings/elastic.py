"""Elastic Settings"""

from pydantic_settings import BaseSettings


class ElasticSettings(BaseSettings):
    """Elastic Settings class
    Will use values from env variables else the default values.
    """

    ELASTIC_HOST: str = "https://es01:9200"
    ELASTIC_USER: str = "elastic"
    ELASTIC_PASSWORD: str = "correlator"
    ELASTIC_CERT_FINGERPRINT: str = "CopyElasticSearchCertificateFingerprint"
    USE_ELASTIC_CERT: bool = False
    USE_ELASTIC_AUTH: bool = False

    ELASTIC_TIMEOUT_IN_SECONDS: int = 300

    EVENTS_INDEX_REPLICAS: int = 1
    EVENTS_TOTAL_FIELDS_LIMIT: int = 1000


elastic_settings = ElasticSettings()

ELASTIC_HOST = elastic_settings.ELASTIC_HOST.split(",")
ELASTIC_USER = elastic_settings.ELASTIC_USER
ELASTIC_PASSWORD = elastic_settings.ELASTIC_PASSWORD
ELASTIC_CERT_FINGERPRINT = elastic_settings.ELASTIC_CERT_FINGERPRINT
USE_ELASTIC_CERT = elastic_settings.USE_ELASTIC_CERT
USE_ELASTIC_AUTH = elastic_settings.USE_ELASTIC_AUTH

ELASTIC_TIMEOUT_IN_SECONDS = elastic_settings.ELASTIC_TIMEOUT_IN_SECONDS

EVENTS_INDEX_REPLICAS = elastic_settings.EVENTS_INDEX_REPLICAS
EVENTS_TOTAL_FIELDS_LIMIT = elastic_settings.EVENTS_TOTAL_FIELDS_LIMIT

ASSET_MAPPING_INDEX_NAME = "ecorr-asset-mapping"
ASSET_MAPPING_POLICY = "ecorr-asset-mapping-policy"
MAIN_PIPELINE = "event-pipeline"
MONITOR_TOOL_PIPELINE_SUFFIX = "-event-pipeline"
DEFAULT_TOOL_NAME = "Default Tool"
DEFAULT_TOOL_PIPELINE = DEFAULT_TOOL_NAME.lower().replace(" ", "-") + MONITOR_TOOL_PIPELINE_SUFFIX
