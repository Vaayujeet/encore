"""Manage ELK Events Index Template"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from elastic.constants import EVENT_INDEX_RE
from elastic.utils import CorrelatorElastic

logger = logging.getLogger("correlator.elastic.update_index_template")


class Command(BaseCommand):
    """Create / Update Events Index Template Command"""

    def __init__(self) -> None:
        super().__init__()
        self.es = CorrelatorElastic()

    def handle(self, *args, **options) -> str | None:
        # Update version, whenever the Events Index Template definition is updated.
        version = 1

        logger.info("Updating Events Index Template [version: %s].", version)
        self.es.indices.put_index_template(
            name="correlator-events",
            index_patterns=EVENT_INDEX_RE,
            version=version,
            template={
                "settings": {
                    "index": {
                        "number_of_replicas": settings.EVENTS_INDEX_REPLICAS,
                        "mapping": {"total_fields": {"limit": settings.EVENTS_TOTAL_FIELDS_LIMIT}},
                    }
                },
            },
        )
        logger.info("Updated Events Index Template [version: %s].", version)
