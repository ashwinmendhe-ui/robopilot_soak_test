import time


def test_stream_start_stop_flow(stream_client, auth_headers, auth_session, test_config):
    selection = test_config["selection"]
    stream_defaults = test_config["stream_defaults"]

    mission_ctx = stream_client.resolve_mission_context(
        headers=auth_headers,
        mission_name=selection["mission_name"],
        company_name=selection.get("company_name"),
        site_name=selection.get("site_name"),
    )

    device_ctx = stream_client.resolve_device_context(
        headers=auth_headers,
        site_id=mission_ctx["site_id"],
        company_id=mission_ctx["company_id"],
        device_name=selection["device_name"],
    )

    context = {
        **mission_ctx,
        **device_ctx,
        "user_id": auth_session.user_id,
        "user_email": auth_session.email,
        "username": auth_session.username,
    }

    start_payload = {
        "deviceSn": context["device_sn"],
        "urlType": stream_defaults["url_type"],
        "videoId": stream_defaults["video_id"],
        "videoQuality": stream_defaults["video_quality"],
        "videoType": stream_defaults["video_type"],
        "missionId": context["mission_id"],
        "playbackUrl": "",
    }

    start_response = stream_client.start_stream(auth_headers, start_payload)
    start_response.raise_for_status()

    start_json = start_response.json()
    start_data = stream_client.parse_start_stream_response(start_json)

    assert start_json["code"] == 0
    assert start_data["stream_id"] == context["device_sn"]
    assert start_data["session_id"]
    assert start_data["can_stop"] is True

    status_ok = False
    last_status_json = None

    for _ in range(test_config["test"]["start_check_retries"]):
        status_response = stream_client.get_stream_status(auth_headers, context["device_sn"])
        status_response.raise_for_status()

        last_status_json = status_response.json()
        is_streaming = stream_client.parse_stream_status_response(last_status_json)

        if is_streaming is True:
            status_ok = True
            break

        time.sleep(test_config["test"]["check_interval_seconds"])

    assert status_ok is True, f"Stream did not become active: {last_status_json}"

    time.sleep(30)

    stop_payload = {
        "deviceSn": context["device_sn"],
        "urlType": stream_defaults["url_type"],
        "videoId": stream_defaults["video_id"],
        "videoQuality": stream_defaults["video_quality"],
        "videoType": stream_defaults["video_type"],
        "missionId": context["mission_id"],
        "playbackUrl": "",
    }

    stop_response = stream_client.stop_stream(auth_headers, stop_payload)
    stop_response.raise_for_status()
    assert stop_response.status_code == 200

    stop_ok = False
    last_status_json = None

    for _ in range(test_config["test"]["stop_check_retries"]):
        status_response = stream_client.get_stream_status(auth_headers, context["device_sn"])
        status_response.raise_for_status()

        last_status_json = status_response.json()
        is_streaming = stream_client.parse_stream_status_response(last_status_json)

        if is_streaming is False:
            stop_ok = True
            break

        time.sleep(test_config["test"]["check_interval_seconds"])

    assert stop_ok is True, f"Stream did not stop correctly: {last_status_json}"