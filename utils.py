from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict


UTC = timezone.utc


def load_config(path: str = "config.json") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def ensure_parent_dir(file_path: str) -> None:
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)


def now_utc() -> datetime:
    return datetime.now(UTC)


def iso_now() -> str:
    return now_utc().isoformat()


def random_wait_seconds(min_seconds: int, max_seconds: int) -> int:
    return random.randint(min_seconds, max_seconds)


def should_refresh_token(token_created_at: datetime, refresh_after_hours: int) -> bool:
    return now_utc() >= token_created_at + timedelta(hours=refresh_after_hours)