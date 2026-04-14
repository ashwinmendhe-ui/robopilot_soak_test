from __future__ import annotations

import time
from datetime import timedelta
from typing import Any, Dict, Tuple

import requests

from auth import AuthClient
from logger_util import SoakLogger
from stream_api import StreamApiClient
from utils import iso_now, load_config, now_utc, random_wait_seconds, should_refresh_token


def build_stream_payload(selection: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adjust this payload to exactly match your backend's expected request body.
    Current structure is based on the IDs you said will be preselected.
    """
    return {
        "companyId": selection["company_id"],
        "siteId": selection["site_id"],
        "missionId": selection["mission_id"],
        "deviceId": selection["device_id"],
    }


def write_result(
    soak_logger: SoakLogger,
    selection: Dict[str, Any],
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
            "device_name": selection.get("device_name", ""),
            "device_id": selection.get("device_id", ""),
            "company_id": selection.get("company_id", ""),
            "site_id": selection.get("site_id", ""),
            "mission_id": selection.get("mission_id", ""),
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
    auth_cfg = config["auth"]
    test_cfg = config["test"]
    selection = config["selection"]
    log_cfg = config["logging"]

    soak_logger = SoakLogger(txt_path=log_cfg["txt_path"], csv_path=log_cfg["csv_path"])
    auth_client = AuthClient(
        base_url=base_url,
        email=auth_cfg["email"],
        password=auth_cfg["password"],
        timeout=test_cfg["request_timeout_seconds"],
    )
    stream_client = StreamApiClient(base_url=base_url, timeout=test_cfg["request_timeout_seconds"])

    soak_logger.info("Starting ROBOPILOT soak test script")
    auth_client.login()
    soak_logger.info("Initial login successful")

    end_time = now_utc() + timedelta(days=test_cfg["duration_days"])
    cycle_no = 0

    while now_utc() < end_time:
        cycle_no += 1
        token_refreshed = "no"

        try:
            if auth_client.session is None:
                auth_client.login()
                token_refreshed = "yes"
            elif should_refresh_token(auth_client.session.token_created_at, auth_cfg["refresh_after_hours"]):
                auth_client.login()
                token_refreshed = "yes"
                soak_logger.info("Bearer token refreshed")

            headers = auth_client.get_auth_header()
            payload = build_stream_payload(selection)

            soak_logger.info(f"Cycle {cycle_no}: sending start stream request")
            start_response = stream_client.start_stream(headers=headers, payload=payload)
            start_response.raise_for_status()
            write_result(
                soak_logger,
                selection,
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
                device_id=selection["device_id"],
                should_be_active=True,
                retries=test_cfg["start_check_retries"],
                interval_seconds=test_cfg["check_interval_seconds"],
            )
            write_result(
                soak_logger,
                selection,
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
                selection,
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
                device_id=selection["device_id"],
                should_be_active=False,
                retries=test_cfg["stop_check_retries"],
                interval_seconds=test_cfg["check_interval_seconds"],
            )
            write_result(
                soak_logger,
                selection,
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
                selection,
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
                selection,
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