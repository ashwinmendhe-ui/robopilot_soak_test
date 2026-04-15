from __future__ import annotations

import time
from datetime import timedelta
from typing import Any, Dict, Tuple

import requests

from auth import AuthClient
from logger_util import SoakLogger
from stream_api import StreamApiClient
from utils import iso_now, load_config, now_utc, random_wait_seconds, should_refresh_token


def resolve_runtime_context(
    stream_client,
    headers,
    selection,
    user_id,
    user_email,
    username,
):
    mission_ctx = stream_client.resolve_mission_context(headers, selection["mission_name"])

    # ✅ Validation check
    if selection.get("company_name") and mission_ctx["company_name"].lower() != selection["company_name"].lower():
        raise ValueError(f"Company mismatch: config={selection['company_name']} API={mission_ctx['company_name']}")

    if selection.get("site_name") and mission_ctx["site_name"].lower() != selection["site_name"].lower():
        raise ValueError(f"Site mismatch: config={selection['site_name']} API={mission_ctx['site_name']}")

    device_ctx = stream_client.resolve_device_context(
        headers=headers,
        site_id=mission_ctx["site_id"],
        company_id=mission_ctx["company_id"],
        device_name=selection["device_name"],
    )

    return {
        **mission_ctx,
        **device_ctx,
        "user_id": user_id,
        "user_email": user_email,
        "username": username,
    }


def build_stream_payload(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update this payload once backend confirms exact request body.
    """
    return {
        "companyId": context["company_id"],
        "siteId": context["site_id"],
        "missionId": context["mission_id"],
        "deviceId": context["device_id"],
        "userId": context["user_id"],
    }


def write_result(
    soak_logger: SoakLogger,
    context: Dict[str, Any],
    cycle_no: int,
    action: str,
    result: str,
    http_status: Any,
    wait_seconds: Any,
    token_refreshed: str,
    message: str,
    error_details: str = "",
) -> None:
    soak_logger.write_csv(
        {
            "timestamp": iso_now(),
            "cycle_no": cycle_no,
            "device_name": context.get("device_name", ""),
            "device_id": context.get("device_id", ""),
            "company_id": context.get("company_id", ""),
            "site_id": context.get("site_id", ""),
            "mission_id": context.get("mission_id", ""),
            "company_name": context.get("company_name", ""),
            "site_name": context.get("site_name", ""),
            "action": action,
            "result": result,
            "http_status": http_status,
            "wait_seconds": wait_seconds,
            "token_refreshed": token_refreshed,
            "message": message,
            "error_details": error_details,
        }
    )


def verify_stream_state(
    stream_client: StreamApiClient,
    headers: Dict[str, str],
    device_id: str,
    should_be_active: bool,
    retries: int,
    interval_seconds: int,
) -> Tuple[bool, str, Any]:
    last_message = ""
    last_status = ""

    for _ in range(retries):
        try:
            active, message, status_code = stream_client.is_device_stream_active(headers, device_id)
            last_message = message
            last_status = status_code

            if active == should_be_active:
                return True, message, status_code
        except Exception as exc:
            last_message = str(exc)

        time.sleep(interval_seconds)

    expected = "active" if should_be_active else "stopped"
    return False, f"Stream did not become {expected}. Last status: {last_message}", last_status


def main() -> None:
    config = load_config()

    base_url = config["base_url"]
    endpoints = config["endpoints"]
    auth_cfg = config["auth"]
    selection = config["selection"]
    test_cfg = config["test"]
    log_cfg = config["logging"]

    soak_logger = SoakLogger(
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

    soak_logger.info("Starting ROBOPILOT soak test script")

    session = auth_client.login()
    headers = auth_client.get_auth_header()

    runtime_context = resolve_runtime_context(
        stream_client=stream_client,
        headers=headers,
        selection=selection,
        user_id=session.user_id,
        user_email=session.email,
        username=session.username,
    )

    soak_logger.info(
        "Resolved context: "
        f"company={runtime_context['company_name']} ({runtime_context['company_id']}), "
        f"site={runtime_context['site_name']} ({runtime_context['site_id']}), "
        f"mission={runtime_context['mission_name']} ({runtime_context['mission_id']}), "
        f"device={runtime_context['device_name']} ({runtime_context['device_id']}), "
        f"user={runtime_context['user_email']} ({runtime_context['user_id']})"
    )

    end_time = now_utc() + timedelta(days=test_cfg["duration_days"])
    cycle_no = 0

    while now_utc() < end_time:
        cycle_no += 1
        token_refreshed = "no"

        try:
            if auth_client.session is None:
                session = auth_client.login()
                token_refreshed = "yes"
            elif should_refresh_token(auth_client.session.token_created_at, auth_cfg["refresh_after_hours"]):
                session = auth_client.login()
                token_refreshed = "yes"
                soak_logger.info("Bearer token refreshed")
            else:
                session = auth_client.session

            headers = auth_client.get_auth_header()
            runtime_context["user_id"] = session.user_id
            runtime_context["user_email"] = session.email
            runtime_context["username"] = session.username

            payload = build_stream_payload(runtime_context)

            soak_logger.info(f"Cycle {cycle_no}: sending start stream request")
            start_response = stream_client.start_stream(headers=headers, payload=payload)
            start_response.raise_for_status()

            write_result(
                soak_logger,
                runtime_context,
                cycle_no,
                action="start_request",
                result="success",
                http_status=start_response.status_code,
                wait_seconds="",
                token_refreshed=token_refreshed,
                message="Start stream API request successful",
            )

            ok, message, status_code = verify_stream_state(
                stream_client=stream_client,
                headers=headers,
                device_id=runtime_context["device_id"],
                should_be_active=True,
                retries=test_cfg["start_check_retries"],
                interval_seconds=test_cfg["check_interval_seconds"],
            )

            write_result(
                soak_logger,
                runtime_context,
                cycle_no,
                action="start_verify",
                result="success" if ok else "failure",
                http_status=status_code,
                wait_seconds="",
                token_refreshed=token_refreshed,
                message=message,
            )

            wait_seconds = random_wait_seconds(
                test_cfg["min_wait_seconds"],
                test_cfg["max_wait_seconds"],
            )
            soak_logger.info(f"Cycle {cycle_no}: waiting {wait_seconds} seconds before stop")
            time.sleep(wait_seconds)

            soak_logger.info(f"Cycle {cycle_no}: sending stop stream request")
            stop_response = stream_client.stop_stream(headers=headers, payload=payload)
            stop_response.raise_for_status()

            write_result(
                soak_logger,
                runtime_context,
                cycle_no,
                action="stop_request",
                result="success",
                http_status=stop_response.status_code,
                wait_seconds=wait_seconds,
                token_refreshed=token_refreshed,
                message="Stop stream API request successful",
            )

            ok, message, status_code = verify_stream_state(
                stream_client=stream_client,
                headers=headers,
                device_id=runtime_context["device_id"],
                should_be_active=False,
                retries=test_cfg["stop_check_retries"],
                interval_seconds=test_cfg["check_interval_seconds"],
            )

            write_result(
                soak_logger,
                runtime_context,
                cycle_no,
                action="stop_verify",
                result="success" if ok else "failure",
                http_status=status_code,
                wait_seconds="",
                token_refreshed=token_refreshed,
                message=message,
            )

        except requests.HTTPError as exc:
            response = exc.response
            status_code = response.status_code if response is not None else ""
            body = response.text if response is not None else ""
            error_message = f"HTTP error in cycle {cycle_no}: {exc}"
            soak_logger.error(error_message)

            write_result(
                soak_logger,
                runtime_context,
                cycle_no,
                action="cycle_error",
                result="failure",
                http_status=status_code,
                wait_seconds="",
                token_refreshed=token_refreshed,
                message=error_message,
                error_details=body,
            )
            time.sleep(10)

        except Exception as exc:
            error_message = f"Unexpected error in cycle {cycle_no}: {exc}"
            soak_logger.error(error_message)

            write_result(
                soak_logger,
                runtime_context,
                cycle_no,
                action="cycle_error",
                result="failure",
                http_status="",
                wait_seconds="",
                token_refreshed=token_refreshed,
                message=error_message,
                error_details=str(exc),
            )
            time.sleep(10)

    soak_logger.info("Soak test duration completed")


if __name__ == "__main__":
    main()