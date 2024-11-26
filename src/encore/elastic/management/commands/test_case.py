"""Execute Test Cases"""

import json
import logging
from pathlib import Path
from time import sleep

import requests

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandParser

from elastic.constants import FieldNames
from elastic.utils import CorrelatorElastic
from launchpad.models import CorrelationRule, MonitorToolIP

logger = logging.getLogger("correlator.elastic.test_case")


class Command(BaseCommand):
    """Test Case Command"""

    def __init__(self) -> None:
        super().__init__()
        self.es = CorrelatorElastic()
        _test_case_data_dir = Path(__file__).resolve().parent.joinpath("test_case_data")
        self.TEST_CASE_ASSET_MAPPING_FILE = _test_case_data_dir.joinpath("TEST_CASE_ASSET_MAPPING.json")
        self.TEST_CASE_EVENTS_FILE = _test_case_data_dir.joinpath("TEST_CASE_EVENTS.json")

    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument("case", help="Test case to execute")
        parser.add_argument("-s", "--setup", action="store_true", help="Perform Setup (required for the first time)")

    def handle(self, *args, **options) -> str | None:
        _case = options["case"].upper()
        _setup = options["setup"]

        if settings.ENVIRONMENT != "dev":
            logger.error("Cannot execute test cases in environment %s [!= dev]", settings.ENVIRONMENT)
            return

        logger.info("Environment: %s", settings.ENVIRONMENT)
        if _setup:
            self.setup()
        else:
            logger.info("Make sure setup is done before executing any testcase.")

        self.test_case(_case)

    def setup(self):
        """Setup required for test cases"""
        logger.info("Starting Setup for Test Case")
        call_command("load_asset_mapping", self.TEST_CASE_ASSET_MAPPING_FILE)
        call_command("update_elk_pipelines")

        mip: MonitorToolIP | None = None
        try:
            mip = MonitorToolIP.objects.get(ip="127.0.0.1")
        except MonitorToolIP.DoesNotExist:
            pass
        if mip and mip.monitor_tool:
            if mip.monitor_tool.pipeline_name != settings.DEFAULT_TOOL_PIPELINE:
                logger.info("*" * 30)
                logger.info("    IP: 127.0.0.1 is mapped to Monitor Tool: %s", mip.monitor_tool.name)
                logger.info(
                    "    If `%s` pipeline is not simialr to `%s` pipeline, test cases will fail.",
                    mip.monitor_tool.pipeline_name,
                    settings.DEFAULT_TOOL_PIPELINE,
                )
                logger.info("    In that case, un-map IP: 127.0.0.1 from Monitor Tool: %s", mip.monitor_tool.name)
                logger.info("    You can revert the changes after running the testcase.")
                logger.info("    [NOTE: Ingestion Pipeline definition can be checked in Kibana ")
                logger.info("    (http://localhost:5601/app/management/ingest/ingest_pipelines).]")
                logger.info("    [NOTE: IP: 127.0.0.1 mapping can be checked in Correlator Admin Page ")
                logger.info("    (http://localhost:8000/admin/launchpad/monitortoolip/127.0.0.1/change/).]")
                logger.info("*" * 30)
                _input = input("  --> Do you want to Exit (Y) or continue with test case (Press any other key)?")
                if _input.upper() != "Y":
                    CorrelationRule.objects.get_or_create(
                        monitor_tool=mip.monitor_tool,
                        event_title="TESTCASE",
                        defaults={"wait_time_in_seconds": 150},
                    )

    def test_case(self, test_case_id="UCA"):
        """Test Case"""

        with open(self.TEST_CASE_EVENTS_FILE, encoding="utf-8") as f:
            TEST_CASE_EVENTS = json.load(f)  # pylint: disable=invalid-name

        if test_case_id not in TEST_CASE_EVENTS:
            print(f"Invalid Test Case {test_case_id}")
            return

        local_base_url = "http://localhost:8000"

        print(f"Test Case {test_case_id} - Starting")
        print(TEST_CASE_EVENTS[test_case_id][0])
        print("-" * 30)

        for event in TEST_CASE_EVENTS[test_case_id][1:]:
            # host_name, title, status, level, desc
            data = {
                FieldNames.ASSET_UNIQUE_ID: event[0],
                FieldNames.EVENT_TITLE: event[1],
                FieldNames.EVENT_TYPE: event[2],
                FieldNames.EVENT_LEVEL: event[3],
                FieldNames.EVENT_DESC: event[4],
            }
            wait_sec = event[5]
            msg = event[6] if len(event) > 6 else ""

            print(f"Logging Event: {data}")
            r = requests.post(f"{local_base_url}/event/", json=data, timeout=300)
            if r.status_code == 202:
                print(f"Logged Event {data}. Waiting for {abs(wait_sec)} secs.")
            else:
                print(f"Failed to log event {data}.")
                exit(1)
            if wait_sec:
                print(f"Waiting for {abs(wait_sec)} seconds")
                sleep(abs(wait_sec))
            if wait_sec < 0:
                input(msg if msg else "Press Enter to continue...")

        print("-" * 30)
        print(TEST_CASE_EVENTS[test_case_id][0])

        print(f"Test Case {test_case_id} - Complete")
