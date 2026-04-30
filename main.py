from __future__ import annotations

import os
import sys
import time
from datetime import timedelta
from auth import AuthClient
from logger_util import SoakLogger
from stream_api import StreamApiClient
from utils import (
    build_stream_payload,
    duration_difference_min_sec,
    duration_min_sec,
    duration_minutes,
    format_kst,
    format_total_duration,
    generate_log_file_path,
    iso_utc,
    load_config,
    now_kst,
    now_utc,
    pick_duration,
    seconds_to_min_sec,
    should_refresh_token,
    create_reversed_csv
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


def verify_streaming_state(
    stream_client,
    headers,
    device_sn: str,
    expected_state: bool,
    retries: int,
    interval_seconds: int,
):
    last_response = None

    for _ in range(retries):
        response = stream_client.get_stream_status(headers, device_sn)
        response.raise_for_status()

        status_json = response.json()
        last_response = status_json

        actual_state = stream_client.parse_stream_status_response(status_json)

        if actual_state == expected_state:
            return True, status_json

        time.sleep(interval_seconds)

    return False, last_response


def monitor_stream_during_working_time(
    stream_client,
    headers,
    device_sn: str,
    cycle: int,
    work_seconds: int,
    check_interval_seconds: int,
    logger: SoakLogger,
    false_confirm_retries: int = 3,
    false_confirm_interval_seconds: int = 3,
):
    remaining_seconds = work_seconds

    while remaining_seconds > 0:
        sleep_seconds = min(check_interval_seconds, remaining_seconds)

        logger.info(
            f"[Cycle {cycle}] ⏳ Stream working... next status check in "
            f"{sleep_seconds} sec"
        )

        time.sleep(sleep_seconds)
        remaining_seconds -= sleep_seconds

        logger.info(f"[Cycle {cycle}] 🔍 Mid-stream status check")

        response = stream_client.get_stream_status(headers, device_sn)
        response.raise_for_status()

        status_json = response.json()
        is_streaming = stream_client.parse_stream_status_response(status_json)

        if not is_streaming:
            max_possible_retries = remaining_seconds // false_confirm_interval_seconds
            effective_retries = min(false_confirm_retries, max_possible_retries)

            if effective_retries <= 0:
                effective_retries = 1
            logger.warning(
                f"[Cycle {cycle}] ⚠️ Stream status returned false. "
                f"Confirming with {effective_retries} more checks..."
            )

            confirmed_stopped = True

            for confirm_attempt in range(1, effective_retries + 1):
                time.sleep(false_confirm_interval_seconds)

                remaining_seconds -= false_confirm_interval_seconds
                remaining_seconds = max(0, remaining_seconds)

                confirm_response = stream_client.get_stream_status(headers, device_sn)
                confirm_response.raise_for_status()

                confirm_json = confirm_response.json()
                confirm_streaming = stream_client.parse_stream_status_response(confirm_json)

                if confirm_streaming:
                    confirmed_stopped = False
                    logger.info(
                        f"[Cycle {cycle}] ✅ Stream recovered during confirmation "
                        f"(attempt {confirm_attempt}/{effective_retries})"
                    )
                    break

                logger.warning(
                    f"[Cycle {cycle}] ⚠️ Stream still false "
                    f"(confirm {confirm_attempt}/{effective_retries})"
                )

            if confirmed_stopped:
                raise Exception(
                    f"Stream stopped unexpectedly during working period "
                    f"after {effective_retries + 1} consecutive false checks: {status_json}"
                )

        logger.info(
            f"[Cycle {cycle}] ✅ Mid-stream status confirmed active "
            f"({seconds_to_min_sec(remaining_seconds)} remaining)"
        )

def build_duration_fields(cycle_start_kst, cycle_end_kst, expected_seconds):
    if not cycle_start_kst or not cycle_end_kst:
        return {
            "expected_cycle_time": seconds_to_min_sec(expected_seconds) if expected_seconds else "",
            "actual_cycle_time": "",
            "time_difference": "",
            "start_time_kst": "",
            "end_time_kst": "",
            "duration_minutes": "",
        }

    actual_seconds = int((cycle_end_kst - cycle_start_kst).total_seconds())

    return {
        "expected_cycle_time": seconds_to_min_sec(expected_seconds) if expected_seconds else "",
        "actual_cycle_time": duration_min_sec(cycle_start_kst, cycle_end_kst),
        "time_difference": duration_difference_min_sec(expected_seconds, actual_seconds)
        if expected_seconds
        else "",
        "start_time_kst": format_kst(cycle_start_kst),
        "end_time_kst": format_kst(cycle_end_kst),
        "duration_minutes": duration_minutes(cycle_start_kst, cycle_end_kst),
    }



def stop_stream_safely(
    stream_client,
    headers,
    context,
    stream_defaults,
    logger: SoakLogger,
    cycle: int | str,
    pre_stop_buffer_seconds: int = 0,
    reason: str = "normal",
    playback_url: str = "",
):
    if pre_stop_buffer_seconds > 0:
        logger.info(
            f"[Cycle {cycle}] ⏳ Waiting {pre_stop_buffer_seconds} sec before STOP "
            f"to allow backend processing | reason={reason}"
        )
        time.sleep(pre_stop_buffer_seconds)

    stop_payload = build_stream_payload(
        context=context,
        stream_defaults=stream_defaults,
        playback_url=playback_url,
    )

    logger.info(f"[Cycle {cycle}] ⏹ STOP stream | reason={reason}")
    logger.info(f"[Cycle {cycle}] STOP payload: {stop_payload}")

    stop_res = stream_client.stop_stream(headers, stop_payload)
    stop_res.raise_for_status()

    if stop_res.status_code != 200:
        raise Exception("Stop failed")

    logger.info(f"[Cycle {cycle}] STOP status code: {stop_res.status_code}")
    logger.info(f"[Cycle {cycle}] STOP content-type: {stop_res.headers.get('Content-Type')}")
    logger.info(f"[Cycle {cycle}] STOP raw response: {stop_res.text}")

    try:
        stop_json = stop_res.json()
        logger.info(f"[Cycle {cycle}] STOP API response JSON: {stop_json}")

        if not stop_json or "playbackUrl" not in stop_json:
            logger.warning(f"[Cycle {cycle}] ⚠️ STOP response JSON has no playbackUrl")

    except Exception as json_error:
        logger.warning(
            f"[Cycle {cycle}] ⚠️ STOP response is not JSON. json_error={json_error}"
        )

    logger.info(f"[Cycle {cycle}] ✅ Stream stopped")
    return stop_res

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
    pre_stop_buffer_seconds = int(test_cfg.get("pre_stop_buffer_seconds", 0))

    csv_path = generate_log_file_path(log_cfg["csv_path"], selection)
    txt_path = generate_log_file_path(log_cfg["txt_path"], selection)

    logger = SoakLogger(
        txt_path=txt_path,
        csv_path=csv_path,
    )
    logger.info(f"📄 CSV log file: {csv_path}")
    logger.info(f"📄 TXT log file: {txt_path}")

    logger.write_session_separator(
        timestamp_utc=iso_utc(),
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

    duration_cfg = test_cfg.get("duration", {})

    total_test_seconds = (
        duration_cfg.get("days", 0) * 86400
        + duration_cfg.get("hours", 0) * 3600
        + duration_cfg.get("minutes", 0) * 60
    )

    # Safety buffer for START/STOP/status API calls.
    cycle_buffer_seconds = int(test_cfg.get("cycle_buffer_seconds", 30))

    logger.info(f"🚀 Starting ROBOPILOT soak test with config: {config_path}")
    logger.info(
        f"🕒 Total soak test duration: "
        f"{format_total_duration(total_test_seconds)} "
        f"({seconds_to_min_sec(total_test_seconds)})"
    )

    session = auth_client.login()
    headers = auth_client.get_auth_header()

    context = resolve_context(stream_client, headers, selection, session)

    logger.info(
        f"Resolved → Company: {context['company_name']} | "
        f"Site: {context['site_name']} | "
        f"Mission: {context['mission_name']} | "
        f"Device: {context['device_name']} | "
        f"Device SN: {context['device_sn']}"
    )

    end_time = now_utc() + timedelta(seconds=total_test_seconds)
    cycle = 0
    stream_active = False

    cycle_start_kst = None
    work_mode = ""
    work_seconds = 0
    idle_mode = ""
    idle_seconds = ""
    http_status = ""
    token_refreshed = "no"
    session_id = ""
    playback_url = ""

    try:
        while now_utc() < end_time:
            remaining_test_seconds = int((end_time - now_utc()).total_seconds())
            available_work_seconds = remaining_test_seconds - cycle_buffer_seconds

            if available_work_seconds <= 0:
                logger.info(
                    "✅ Not enough remaining soak time for next cycle. Ending test."
                )
                break

            cycle += 1
            token_refreshed = "no"
            work_mode = ""
            work_seconds = 0
            idle_mode = ""
            idle_seconds = ""
            http_status = ""
            session_id = ""
            cycle_start_kst = None
            cycle_end_kst = None

            work_mode, work_seconds = pick_duration(timing_profiles["working_time"])

            if work_seconds > available_work_seconds:
                logger.info(
                    f"[Cycle {cycle}] ⚠️ Selected working time "
                    f"{seconds_to_min_sec(work_seconds)} is greater than remaining "
                    f"available soak time {seconds_to_min_sec(available_work_seconds)}. "
                    f"Adjusting working time."
                )
                work_seconds = available_work_seconds
                work_mode = "adjusted"

            logger.blank_line()
            logger.info(
                f"==================== Cycle {cycle} Start | "
                f"{seconds_to_min_sec(work_seconds)} ===================="
            )

            try:
                if should_refresh_token(
                    session.token_created_at,
                    auth_cfg["refresh_after_hours"],
                ):
                    session = auth_client.login()
                    headers = auth_client.get_auth_header()
                    context = resolve_context(stream_client, headers, selection, session)
                    token_refreshed = "yes"
                    logger.info("🔄 Token refreshed")

                # start_payload = build_stream_payload(context, stream_defaults)
                playback_folder = now_kst().strftime("%Y-%m-%d_%H-%M-%S")
                playback_url = (
                    f"{config['cloudfront_base_url']}/streams/"
                    f"{context['device_sn']}/{playback_folder}/index.m3u8"
                )

                start_payload = build_stream_payload(
                    context=context,
                    stream_defaults=stream_defaults,
                    playback_url=""
                )

                logger.info(f"[Cycle {cycle}] ▶ START stream")
                logger.info(f"365 [Cycle {cycle}] START payload: {start_payload}")
                start_res = stream_client.start_stream(headers, start_payload)
                http_status = start_res.status_code
                start_res.raise_for_status()

                start_json = start_res.json()
                logger.info(f"[Cycle {cycle}] START API response: {start_json}")
                start_playback_url = start_json.get("data", {}).get("playbackUrl", "")
                if start_playback_url:
                    playback_url = start_playback_url
                if start_json.get("code") != 0:
                    raise Exception(f"Start failed: {start_json}")

                session_id = start_json["data"]["sessionId"]
                stream_active = True

                logger.info(f"[Cycle {cycle}] ✅ Stream started | session={session_id}")
                logger.info(f"[Cycle {cycle}] 🔍 Checking stream status after START")

                start_status_ok, start_status_json = verify_streaming_state(
                    stream_client=stream_client,
                    headers=headers,
                    device_sn=context["device_sn"],
                    expected_state=True,
                    retries=test_cfg["start_check_retries"],
                    interval_seconds=test_cfg["check_interval_seconds"],
                )

                if not start_status_ok:
                    raise Exception(
                        f"Stream did not become active after start: {start_status_json}"
                    )

                logger.info(f"[Cycle {cycle}] ✅ Stream status confirmed active")

                cycle_start_kst = now_kst()

                logger.info(
                    f"[Cycle {cycle}] ⏳ Working {work_mode} → "
                    f"{seconds_to_min_sec(work_seconds)}"
                )

                monitor_stream_during_working_time(
                    stream_client=stream_client,
                    headers=headers,
                    device_sn=context["device_sn"],
                    cycle=cycle,
                    work_seconds=work_seconds,
                    check_interval_seconds=test_cfg["mid_stream_check_interval_seconds"],
                    logger=logger,
                    false_confirm_retries=test_cfg.get("false_confirm_retries", 5),
                    false_confirm_interval_seconds=test_cfg.get("false_confirm_interval_seconds", 3),
                )

                cycle_end_kst = now_kst()

                stop_res = stop_stream_safely(
                    stream_client=stream_client,
                    headers=headers,
                    context=context,
                    stream_defaults=stream_defaults,
                    logger=logger,
                    cycle=cycle,
                    pre_stop_buffer_seconds=pre_stop_buffer_seconds,
                    reason="cycle_complete",
                    playback_url=playback_url,
                )

                http_status = stop_res.status_code
                stream_active = False
                logger.info(f"[Cycle {cycle}] 🔍 Checking stream status after STOP")

                stop_status_ok, stop_status_json = verify_streaming_state(
                    stream_client=stream_client,
                    headers=headers,
                    device_sn=context["device_sn"],
                    expected_state=False,
                    retries=test_cfg["stop_check_retries"],
                    interval_seconds=test_cfg["check_interval_seconds"],
                )

                if not stop_status_ok:
                    raise Exception(f"Stream did not stop correctly: {stop_status_json}")

                logger.info(f"[Cycle {cycle}] ✅ Stream status confirmed stopped")

                idle_mode, idle_seconds = pick_duration(timing_profiles["idle_time"])

                remaining_after_cycle = int((end_time - now_utc()).total_seconds())

                if idle_seconds > remaining_after_cycle:
                    logger.info(
                        f"[Cycle {cycle}] ⚠️ Selected idle time "
                        f"{seconds_to_min_sec(idle_seconds)} is greater than remaining "
                        f"soak time {seconds_to_min_sec(remaining_after_cycle)}. "
                        f"Adjusting idle time."
                    )
                    idle_seconds = max(0, remaining_after_cycle)
                    idle_mode = "adjusted"

                logger.info(
                    f"[Cycle {cycle}] 💤 Idle {idle_mode} → "
                    f"{seconds_to_min_sec(idle_seconds)}"
                )

                duration_fields = build_duration_fields(
                    cycle_start_kst=cycle_start_kst,
                    cycle_end_kst=cycle_end_kst,
                    expected_seconds=int(work_seconds),
                )

                logger.write_csv(
                    {
                        "cycle_no": cycle,
                        **duration_fields,
                        "company_name": context["company_name"],
                        "site_name": context["site_name"],
                        "mission_name": context["mission_name"],
                        "device_name": context["device_name"],
                        "action": "cycle_complete",
                        "result": "success",
                        "http_status": http_status,
                        "working_mode": work_mode,
                        "working_seconds": work_seconds,
                        "idle_mode": idle_mode,
                        "idle_seconds": idle_seconds,
                        "token_refreshed": token_refreshed,
                        "message": f"Cycle completed successfully | session={session_id}",
                        "error_details": "",
                        "timestamp_utc": iso_utc(),
                    }
                )

                logger.info(f"==================== Cycle {cycle} End ====================")

                if idle_seconds > 0:
                    time.sleep(idle_seconds)

            except Exception as e:
                logger.error(f"[Cycle {cycle}] ❌ Error: {e}")

                error_end_kst = now_kst()

                if stream_active:
                    try:
                        logger.info(
                            f"[Cycle {cycle}] ⚠️ Attempting to stop active stream after error..."
                        )
                        stop_res = stop_stream_safely(
                            stream_client=stream_client,
                            headers=headers,
                            context=context,
                            stream_defaults=stream_defaults,
                            logger=logger,
                            cycle=cycle,
                            pre_stop_buffer_seconds=pre_stop_buffer_seconds,
                            reason="cycle_error_cleanup",
                            playback_url=playback_url,
                        )

                        http_status = stop_res.status_code
                        stream_active = False
                        logger.info(f"[Cycle {cycle}] ✅ Stream stopped after error")
                    except Exception as stop_error:
                        logger.error(
                            f"[Cycle {cycle}] ❌ Failed to stop stream after error: {stop_error}"
                        )

                duration_fields = build_duration_fields(
                    cycle_start_kst=cycle_start_kst,
                    cycle_end_kst=error_end_kst,
                    expected_seconds=int(work_seconds) if work_seconds else 0,
                )

                logger.write_csv(
                    {
                        "cycle_no": cycle,
                        **duration_fields,
                        "company_name": context.get("company_name", ""),
                        "site_name": context.get("site_name", ""),
                        "mission_name": context.get("mission_name", ""),
                        "device_name": context.get("device_name", ""),
                        "action": "cycle_error",
                        "result": "failure",
                        "http_status": http_status,
                        "working_mode": work_mode,
                        "working_seconds": work_seconds,
                        "idle_mode": idle_mode,
                        "idle_seconds": idle_seconds,
                        "token_refreshed": token_refreshed,
                        "message": str(e),
                        "error_details": repr(e),
                        "timestamp_utc": iso_utc(),
                    }
                )

                logger.info(f"==================== Cycle {cycle} End With Error ====================")

                remaining_after_error = int((end_time - now_utc()).total_seconds())
                if remaining_after_error > 10:
                    time.sleep(10)

    except KeyboardInterrupt:
        logger.info("🛑 Manual stop received (Ctrl+C)")

        interrupt_end_kst = now_kst()

        if stream_active:
            try:
                logger.info("⚠️ Stopping active stream before exit...")
                stop_res = stop_stream_safely(
                    stream_client=stream_client,
                    headers=headers,
                    context=context,
                    stream_defaults=stream_defaults,
                    logger=logger,
                    cycle=cycle,
                    pre_stop_buffer_seconds=pre_stop_buffer_seconds,
                    reason="manual_stop",
                    playback_url=playback_url,
                )

                http_status = stop_res.status_code
                stream_active = False
                logger.info("✅ Stream stopped during shutdown")
            except Exception as e:
                logger.error(f"Failed to stop stream during shutdown: {e}")

        duration_fields = build_duration_fields(
            cycle_start_kst=cycle_start_kst,
            cycle_end_kst=interrupt_end_kst,
            expected_seconds=int(work_seconds) if work_seconds else 0,
        )

        logger.write_csv(
            {
                "cycle_no": cycle,
                **duration_fields,
                "company_name": context.get("company_name", ""),
                "site_name": context.get("site_name", ""),
                "mission_name": context.get("mission_name", ""),
                "device_name": context.get("device_name", ""),
                "action": "manual_stop",
                "result": "stopped",
                "http_status": http_status,
                "working_mode": work_mode,
                "working_seconds": work_seconds,
                "idle_mode": idle_mode,
                "idle_seconds": idle_seconds,
                "token_refreshed": token_refreshed,
                "message": "Manual stop received (Ctrl+C)",
                "error_details": "",
                "timestamp_utc": iso_utc(),
            }
        )

    try:
        reversed_path = create_reversed_csv(csv_path)
        if reversed_path:
            logger.info(f"📄 Reversed CSV created: {reversed_path}")
            try:
                os.remove(csv_path)
                logger.info(f"🗑️ Original CSV deleted: {csv_path}")
            except Exception as e:
                logger.error(f"Failed to delete original CSV: {e}")
    except Exception as e:
        logger.error(f"Failed to create reversed CSV: {e}")

    logger.info("✅ Soak test completed")


if __name__ == "__main__":
    main()