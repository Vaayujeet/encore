"""SNMP Utility Classes and Functions
"""

import logging

from pyasn1.codec.ber import decoder
from pysnmp.proto import api, rfc1905
from pysnmp.smi import builder, compiler, rfc1902, view
from pysnmp.smi.error import SmiError

from django.conf import settings

logger = logging.getLogger("correlator.snmp")

KEY_TRANSLATE_MAP = str.maketrans(" :.", "_" * 3)


class SnmpObjectType(rfc1902.ObjectType):
    """Extends the rfc1902.ObjectType"""

    def __init__(self, objectIdentity, objectSyntax=rfc1905.unSpecified):
        super().__init__(objectIdentity, objectSyntax)

    def key_value(self):
        """Returns the Object as a dictionary"""
        if self._ObjectType__state & self.stClean:  # pylint: disable=no-member
            return (
                self._ObjectType__args[0].prettyPrint(),  # pylint: disable=no-member
                self._ObjectType__args[1].prettyPrint(),  # pylint: disable=no-member
            )

        raise SmiError(f"{self.__class__.__name__} object not fully initialized")


def get_mib_view_controller():
    """Loads MIB files and returns the MIB View Controller

    Returns:
        _type_: _description_
    """

    logger.debug("Loading MIB Modules")
    mib_builder = builder.MibBuilder()

    # Add MIB directories using DirMibSource
    mib_sources = mib_builder.getMibSources()
    if settings.MIB_SOURCE_DIRECTORY:
        mib_sources += (builder.DirMibSource(settings.MIB_SOURCE_DIRECTORY),)
    logger.debug("MIB Source Directory: %s", str(mib_sources))

    mib_builder.setMibSources(*mib_sources)
    mib_view_controller = view.MibViewController(mib_builder)
    compiler.addMibCompiler(mib_builder, sources=["file://."])

    # Pre-load MIB modules that define objects we receive in TRAPs
    mib_builder.loadModules(*settings.MIB_MODULES_TO_LOAD)
    logger.info("Loaded MIB Modules: %s", str(mib_builder.mibSymbols.keys()))

    return mib_view_controller


def decode_trap_message(address, raw_trap_message, view_controller):
    """Decode SNMP Traps and return the variable binds"""

    var_binds_dict = {}
    while raw_trap_message:
        var_binds = None
        msg_version = int(api.decodeMessageVersion(raw_trap_message))
        if msg_version in api.protoModules:
            p_mod = api.protoModules[msg_version]
        else:
            logger.error("Unsupported SNMP version %s received from %s", msg_version, address)
            # TODO: Log error somewhere
            return var_binds_dict
        req_msg, raw_trap_message = decoder.decode(
            raw_trap_message,
            asn1Spec=p_mod.Message(),
        )

        req_pdu = p_mod.apiMessage.getPDU(req_msg)
        if req_pdu.isSameTypeWith(p_mod.TrapPDU()):
            if msg_version == api.protoVersion1:
                # logger.info("Enterprise: %s", p_mod.apiTrapPDU.getEnterprise(req_pdu).prettyPrint())
                # logger.info("Agent Address: %s", p_mod.apiTrapPDU.getAgentAddr(req_pdu).prettyPrint())
                # logger.info("Generic Trap: %s", p_mod.apiTrapPDU.getGenericTrap(req_pdu).prettyPrint())
                # logger.info("Specific Trap: %s", p_mod.apiTrapPDU.getSpecificTrap(req_pdu).prettyPrint())
                # logger.info("Uptime: %s", p_mod.apiTrapPDU.getTimeStamp(req_pdu).prettyPrint())
                var_binds = p_mod.apiTrapPDU.getVarBinds(req_pdu)
            else:
                var_binds = p_mod.apiPDU.getVarBinds(req_pdu)

            # INFO: https://www.pysnmp.com/pysnmp/examples/smi/manager/browsing-mib-tree
            for var in var_binds:
                key, val = (
                    SnmpObjectType(rfc1902.ObjectIdentity(var[0]), var[1]).resolveWithMib(view_controller).key_value()
                )
                var_binds_dict[key.translate(KEY_TRANSLATE_MAP)] = val

    return var_binds_dict
