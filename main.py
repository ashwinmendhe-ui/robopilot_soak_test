from __future__ import annotations

import time
from datetime import timedelta
from typing import Any, Dict

from auth import AuthClient
from logger_util import SoakLogger
from stream_api import StreamApiClient
from utils import (
    iso_now,
    load_config,
    now_utc,
    pick_duration,
    should_refresh_token,
)


def build_stream_payload(context: Dict[str, Any], stream_defaults: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "deviceSn": context["device_sn"],
        "urlType": stream_defaults["url_type"],
        "videoId": stream_defaults["video_id"],
        "videoQuality": stream_defaults["video_quality"],
        "videoType": stream_defaults["video_type"],
        "missionId": context["mission_id"],
        "playbackUrl": "",
    }


def resolve_context(stream_client, headers, selection, auth_session):
    mission_ctx = stream_client.resolve_mission_context(
        headers=headers,
        mission_name=selection["mission_name"],
        company_name=selection.get("company_name"),
        site_name=selection.get("site_name"),
    )

    device_ctx = stream_client.resolve_device_context(
        headers=headers,
        site_id=mission_ctx["site_id"],
        company_id=mission_ctx["company_id"],
        device_name=selection["device_name"],
    )

    return {
        **mission_ctx,
        **device_ctx,
        "user_id": auth_session.user_id,
        "user_email": auth_session.email,
        "username": auth_session.username,
    }


def main():
    config = load_config("config.json")

    base_url = config["base_url"]
    endpoints = config["endpoints"]
    auth_cfg = config["auth"]
    selection = config["selection"]
    test_cfg = config["test"]
    timing_profiles = config["timing_profiles"]
    stream_defaults = config["stream_defaults"]
    log_cfg = config["logging"]

    logger = SoakLogger(
        txt_path=log_cfg["txt_path"],
        csv_path=log_cfg["csv_path"],
    )

    auth_client = AuthClient(
        base_url=base_url,
        login_endpoint=endpoints["login"],
        email=auth_cfg["email"],
        password=auth_cfg["password"],
        timeout=test_cfg["request_timeout_seconds"],
    )

    stream_client = StreamApiClient(
        base_url=base_url,
        endpoints=endpoints,
        timeout=test_cfg["request_timeout_seconds"],
    )

    logger.info("🚀 Starting ROBOPILOT soak test")

    session = auth_client.login()
    headers = auth_client.get_auth_header()

    context = resolve_context(stream_client, headers, selection, session)

    logger.info(
        f"Resolved → Mission: {context['mission_name']} | Device: {context['device_name']}"
    )

    end_time = now_utc() + timedelta(days=test_cfg["duration_days"])
    cycle = 0

    while now_utc() < end_time:
        cycle += 1
        token_refreshed = "no"

        try:
            # 🔁 Token refresh
            if should_refresh_token(session.token_created_at, auth_cfg["refresh_after_hours"]):
                session = auth_client.login()
                headers = auth_client.get_auth_header()
                token_refreshed = "yes"
                logger.info("🔄 Token refreshed")

            # 🚀 START STREAM
            start_payload = build_stream_payload(context, stream_defaults)

            logger.info(f"[Cycle {cycle}] ▶ START stream")
            start_res = stream_client.start_stream(headers, start_payload)
            start_res.raise_for_status()

            start_json = start_res.json()

            if start_json.get("code") != 0:
                raise Exception(f"Start failed: {start_json}")

            session_id = start_json["data"]["sessionId"]

            logger.info(f"[Cycle {cycle}] ✅ Stream started | session={session_id}")

            # ⏱ WORKING TIME
            work_mode, work_seconds = pick_duration(timing_profiles["working_time"])
            logger.info(f"[Cycle {cycle}] ⏳ Working {work_mode} → {work_seconds}s")
            time.sleep(work_seconds)

            # 🛑 STOP STREAM
            stop_payload = build_stream_payload(context, stream_defaults)

            logger.info(f"[Cycle {cycle}] ⏹ STOP stream")
            stop_res = stream_client.stop_stream(headers, stop_payload)
            stop_res.raise_for_status()

            if stop_res.status_code != 200:
                raise Exception("Stop failed")

            logger.info(f"[Cycle {cycle}] ✅ Stream stopped")

            # 💤 IDLE TIME
            idle_mode, idle_seconds = pick_duration(timing_profiles["idle_time"])
            logger.info(f"[Cycle {cycle}] 💤 Idle {idle_mode} → {idle_seconds}s")

            # 📊 LOG CSV
            logger.write_csv(
                {
                    "timestamp": iso_now(),
                    "cycle_no": cycle,
                    "company_name": context["company_name"],
                    "site_name": context["site_name"],
                    "mission_name": context["mission_name"],
                    "device_name": context["device_name"],
                    "action": "cycle_complete",
                    "result": "success",
                    "working_mode": work_mode,
                    "working_seconds": work_seconds,
                    "idle_mode": idle_mode,
                    "idle_seconds": idle_seconds,
                    "token_refreshed": token_refreshed,
                }
            )

            time.sleep(idle_seconds)

        except Exception as e:
            logger.error(f"[Cycle {cycle}] ❌ Error: {e}")

            logger.write_csv(
                {
                    "timestamp": iso_now(),
                    "cycle_no": cycle,
                    "company_name": context.get("company_name", ""),
                    "site_name": context.get("site_name", ""),
                    "mission_name": context.get("mission_name", ""),
                    "device_name": context.get("device_name", ""),
                    "action": "cycle_error",
                    "result": "failure",
                    "message": str(e),
                }
            )

            time.sleep(10)

    logger.info("✅ Soak test completed")


if __name__ == "__main__":
    main()