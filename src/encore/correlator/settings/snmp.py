"""SNMP Settings"""

from typing import Optional

from pydantic_settings import BaseSettings


class SnmpSettings(BaseSettings):
    """SNMP Settings class
    Will use values from env variables else the default values.
    """

    SNMP_HOST: str = "localhost"
    SNMP_PORT: int = 162

    MIB_MODULES: str = ",".join(
        [
            "SNMP-COMMUNITY-MIB",
            "SNMP-FRAMEWORK-MIB",
            "SNMPv2-CONF",
            "SNMPv2-MIB",
            "SNMPv2-SMI",
            "SNMPv2-TC",
        ]
    )
    MIB_SOURCE_DIRECTORY: Optional[str] = None


snmp_settings = SnmpSettings()

SNMP_HOST = snmp_settings.SNMP_HOST
SNMP_PORT = snmp_settings.SNMP_PORT
MIB_MODULES_TO_LOAD = snmp_settings.MIB_MODULES.split(",")
MIB_SOURCE_DIRECTORY = snmp_settings.MIB_SOURCE_DIRECTORY
