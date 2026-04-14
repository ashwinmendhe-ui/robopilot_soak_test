from __future__ import annotations

import csv
import logging
from typing import Dict, Any

from utils import ensure_parent_dir


CSV_FIELDS = [
    "timestamp",
    "cycle_no",
    "device_name",
    "device_id",
    "company_id",
    "site_id",
    "mission_id",
    "action",
    "result",
    "http_status",
    "wait_seconds",
    "token_refreshed",
    "message",
    "error_details",
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
            writer.writerow(normalized)