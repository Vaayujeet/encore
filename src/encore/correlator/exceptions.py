"""Correlator Exceptions"""


class CorrelatorProcessException(Exception):
    """Correlator Process Exception"""

    def __init__(self, message) -> None:
        self.message = message
