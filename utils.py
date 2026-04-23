from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


UTC = timezone.utc

def build_stream_payload(context: Dict[str, Any], stream_defaults: Dict[str, Any], playback_url: str = "") -> Dict[str, Any]:
    return {
        "deviceSn": context["device_sn"],
        "urlType": stream_defaults["url_type"],
        "videoId": stream_defaults["video_id"],
        "videoQuality": stream_defaults["video_quality"],
        "videoType": stream_defaults["video_type"],
        "missionId": context["mission_id"],
        "playbackUrl": playback_url,
    }


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


def pick_duration(profile: Dict[str, int]) -> Tuple[str, int]:
    mode = random.choice(["short", "long"])

    if mode == "short":
        seconds = random.randint(
            profile["short_min_seconds"],
            profile["short_max_seconds"],
        )
    else:
        seconds = random.randint(
            profile["long_min_seconds"],
            profile["long_max_seconds"],
        )

    return mode, seconds