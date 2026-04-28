from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
from zoneinfo import ZoneInfo
import pandas as pd
import os

UTC = timezone.utc
KST = timezone(timedelta(hours=9))


def build_stream_payload(
    context: Dict[str, Any],
    stream_defaults: Dict[str, Any],
    playback_url: str = ""
) -> Dict[str, Any]:
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


def now_kst() -> datetime:
    return datetime.now(KST)


def iso_utc() -> str:
    return now_utc().isoformat()


def iso_kst() -> str:
    return now_kst().isoformat()


def format_kst(dt: datetime) -> str:
    return dt.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")


def duration_minutes(start_dt: datetime, end_dt: datetime) -> float:
    return round((end_dt - start_dt).total_seconds() / 60, 2)


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

def seconds_to_min_sec(seconds: int | float) -> str:
    seconds = int(seconds)
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}.{remaining_seconds:02d}min ({seconds} sec)"


def duration_min_sec(start_dt, end_dt):
    total_seconds = int((end_dt - start_dt).total_seconds())
    return seconds_to_min_sec(total_seconds)


def duration_difference_min_sec(expected_seconds, actual_seconds):
    diff = actual_seconds - expected_seconds
    sign = "-" if diff < 0 else "+"
    return f"{sign}{seconds_to_min_sec(abs(diff))}"


def format_total_duration(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs:
        parts.append(f"{secs}s")

    return " ".join(parts)

def generate_log_file_path(template: str, selection: dict) -> str:
    kst = ZoneInfo("Asia/Seoul")  # KST timezone
    timestamp = datetime.now(kst).strftime("%Y-%m-%d_%H-%M-%S")

    mission_name = selection.get("mission_name", "unknown").replace(" ", "_")
    device_name = selection.get("device_name", "device").replace(" ", "_")

    return template.format(
        mission_name=mission_name,
        device_name=device_name,
        timestamp=timestamp
    )

def create_reversed_csv(csv_path: str):
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)

    # reverse order (latest first)
    df = df.iloc[::-1]

    reversed_path = csv_path.replace(".csv", "_latest_first.csv")

    df.to_csv(reversed_path, index=False)

    return reversed_path