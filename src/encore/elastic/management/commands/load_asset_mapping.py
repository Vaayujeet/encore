"""Load Asset Mapping to ELK"""

import json
import logging

from django.core.management.base import BaseCommand, CommandParser

from elastic.utils import CorrelatorElastic

logger = logging.getLogger("correlator.elastic.load_asset_mapping")


class Command(BaseCommand):
    """Load Asset Mapping Command"""

    def __init__(self) -> None:
        super().__init__()
        self.es = CorrelatorElastic()

    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("-e", "--enrich", action="store_true", help="Execute Enrich Policy")
        parser.add_argument("file", help="Full Path of Asset Mapping JSON File")

    def handle(self, *args, **options) -> str | None:
        file_path = options["file"]
        enrich = options["enrich"]

        logger.info("Loading Asset Mapping from %s", file_path)
        with open(file_path, encoding="utf-8") as f:
            asset_map_json = json.load(f)

        self.es.load_asset_mapping(asset_map_json, enrich)
        logger.info("Loaded Asset Mapping from %s", file_path)
