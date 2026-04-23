from __future__ import annotations

import sys
import time
from datetime import timedelta

from auth import AuthClient
from logger_util import SoakLogger
from stream_api import StreamApiClient
from utils import (
    build_stream_payload,
    duration_minutes,
    format_kst,
    iso_kst,
    iso_utc,
    load_config,
    now_kst,
    now_utc,
    pick_duration,
    should_refresh_token,
)


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


def main() -> None:
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    config = load_config(config_path)

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

    logger.write_session_separator(
        timestamp_utc=iso_utc(),
        timestamp_kst=iso_kst(),
        message=f"New soak test session started with config: {config_path}",
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

    logger.info(f"🚀 Starting ROBOPILOT soak test with config: {config_path}")

    session = auth_client.login()
    headers = auth_client.get_auth_header()

    context = resolve_context(stream_client, headers, selection, session)

    logger.info(
        f"Resolved → Company: {context['company_name']} | "
        f"Site: {context['site_name']} | "
        f"Mission: {context['mission_name']} | "
        f"Device: {context['device_name']}"
    )

    end_time = now_utc() + timedelta(days=test_cfg["duration_days"])
    cycle = 0
    stream_active = False

    try:
        while now_utc() < end_time:
            cycle += 1
            token_refreshed = "no"
            work_mode = ""
            work_seconds = ""
            idle_mode = ""
            idle_seconds = ""
            http_status = ""
            session_id = ""
            cycle_start_kst = None
            cycle_end_kst = None

            logger.blank_line()
            logger.info(f"==================== Cycle {cycle} Start ====================")

            try:
                if should_refresh_token(session.token_created_at, auth_cfg["refresh_after_hours"]):
                    session = auth_client.login()
                    headers = auth_client.get_auth_header()
                    context = resolve_context(stream_client, headers, selection, session)
                    token_refreshed = "yes"
                    logger.info("🔄 Token refreshed")

                cycle_start_kst = now_kst()

                start_payload = build_stream_payload(context, stream_defaults)

                logger.info(f"[Cycle {cycle}] ▶ START stream")
                start_res = stream_client.start_stream(headers, start_payload)
                http_status = start_res.status_code
                start_res.raise_for_status()

                start_json = start_res.json()
                if start_json.get("code") != 0:
                    raise Exception(f"Start failed: {start_json}")

                session_id = start_json["data"]["sessionId"]
                stream_active = True

                logger.info(f"[Cycle {cycle}] ✅ Stream started | session={session_id}")

                work_mode, work_seconds = pick_duration(timing_profiles["working_time"])
                logger.info(f"[Cycle {cycle}] ⏳ Working {work_mode} → {work_seconds}s")
                time.sleep(work_seconds)

                stop_payload = build_stream_payload(context, stream_defaults)

                logger.info(f"[Cycle {cycle}] ⏹ STOP stream")
                stop_res = stream_client.stop_stream(headers, stop_payload)
                http_status = stop_res.status_code
                stop_res.raise_for_status()

                if stop_res.status_code != 200:
                    raise Exception("Stop failed")

                stream_active = False
                cycle_end_kst = now_kst()

                logger.info(f"[Cycle {cycle}] ✅ Stream stopped")

                idle_mode, idle_seconds = pick_duration(timing_profiles["idle_time"])
                logger.info(f"[Cycle {cycle}] 💤 Idle {idle_mode} → {idle_seconds}s")

                logger.write_csv(
                    {
                        "timestamp_utc": iso_utc(),
                        "timestamp_kst": iso_kst(),
                        "cycle_no": cycle,
                        "company_name": context["company_name"],
                        "site_name": context["site_name"],
                        "mission_name": context["mission_name"],
                        "device_name": context["device_name"],
                        "action": "cycle_complete",
                        "result": "success",
                        "http_status": http_status,
                        "start_time_kst": format_kst(cycle_start_kst) if cycle_start_kst else "",
                        "end_time_kst": format_kst(cycle_end_kst) if cycle_end_kst else "",
                        "duration_minutes": duration_minutes(cycle_start_kst, cycle_end_kst)
                        if cycle_start_kst and cycle_end_kst else "",
                        "working_mode": work_mode,
                        "working_seconds": work_seconds,
                        "idle_mode": idle_mode,
                        "idle_seconds": idle_seconds,
                        "token_refreshed": token_refreshed,
                        "message": f"Cycle completed successfully | session={session_id}",
                        "error_details": "",
                    }
                )

                logger.info(f"==================== Cycle {cycle} End ====================")
                time.sleep(idle_seconds)

            except Exception as e:
                logger.error(f"[Cycle {cycle}] ❌ Error: {e}")

                logger.write_csv(
                    {
                        "timestamp_utc": iso_utc(),
                        "timestamp_kst": iso_kst(),
                        "cycle_no": cycle,
                        "company_name": context.get("company_name", ""),
                        "site_name": context.get("site_name", ""),
                        "mission_name": context.get("mission_name", ""),
                        "device_name": context.get("device_name", ""),
                        "action": "cycle_error",
                        "result": "failure",
                        "http_status": http_status,
                        "start_time_kst": format_kst(cycle_start_kst) if cycle_start_kst else "",
                        "end_time_kst": format_kst(now_kst()) if cycle_start_kst else "",
                        "duration_minutes": duration_minutes(cycle_start_kst, now_kst())
                        if cycle_start_kst else "",
                        "working_mode": work_mode,
                        "working_seconds": work_seconds,
                        "idle_mode": idle_mode,
                        "idle_seconds": idle_seconds,
                        "token_refreshed": token_refreshed,
                        "message": str(e),
                        "error_details": repr(e),
                    }
                )

                logger.info(f"==================== Cycle {cycle} End With Error ====================")
                time.sleep(10)

    except KeyboardInterrupt:
        logger.info("🛑 Manual stop received (Ctrl+C)")

        if stream_active:
            try:
                logger.info("⚠️ Stopping active stream before exit...")
                stop_payload = build_stream_payload(context, stream_defaults)
                stream_client.stop_stream(headers, stop_payload)
                logger.info("✅ Stream stopped during shutdown")
            except Exception as e:
                logger.error(f"Failed to stop stream during shutdown: {e}")

    logger.info("✅ Soak test completed")


if __name__ == "__main__":
    main()