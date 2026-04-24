from __future__ import annotations

import csv
import logging
from typing import Any, Dict

from utils import ensure_parent_dir


CSV_FIELDS = [
    "cycle_no",
    "expected_cycle_time",
    "actual_cycle_time",
    "time_difference",
    "start_time_kst",
    "end_time_kst",
    "company_name",
    "site_name",
    "mission_name",
    "device_name",
    "action",
    "result",
    "http_status",
    "working_mode",
    "working_seconds",
    "idle_mode",
    "idle_seconds",
    "token_refreshed",
    "message",
    "error_details",
    "timestamp_utc",
]


class SoakLogger:
    def __init__(self, txt_path: str, csv_path: str) -> None:
        ensure_parent_dir(txt_path)
        ensure_parent_dir(csv_path)

        self.txt_path = txt_path
        self.csv_path = csv_path

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(message)s",
            handlers=[
                logging.FileHandler(txt_path, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("soak_test")
        self._init_csv()

    def _init_csv(self) -> None:
        try:
            with open(self.csv_path, "x", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
                writer.writeheader()
        except FileExistsError:
            pass

    def info(self, message: str) -> None:
        self.logger.info(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def blank_line(self) -> None:
        self.logger.info("")

    def write_csv(self, row: Dict[str, Any]) -> None:
        normalized = {field: row.get(field, "") for field in CSV_FIELDS}
        with open(self.csv_path, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
            writer.writerow(normalized)

    def write_session_separator(self, timestamp_utc: str, message: str) -> None:
        self.write_csv(
            {
                "action": "SESSION_START",
                "result": "info",
                "message": message,
                "timestamp_utc": timestamp_utc,
            }
        )