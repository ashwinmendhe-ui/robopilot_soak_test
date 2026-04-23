import time


def build_stream_payload(context, stream_defaults):
    return {
        "deviceSn": context["device_sn"],
        "urlType": stream_defaults["url_type"],
        "videoId": stream_defaults["video_id"],
        "videoQuality": stream_defaults["video_quality"],
        "videoType": stream_defaults["video_type"],
        "missionId": context["mission_id"],
        "playbackUrl": ""
    }


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

    start_payload = build_stream_payload(context, stream_defaults)
    start_response = stream_client.start_stream(auth_headers, start_payload)
    start_response.raise_for_status()

    start_json = start_response.json()
    start_data = stream_client.parse_start_stream_response(start_json)

    assert start_json["code"] == 0
    assert start_data["stream_id"] == context["device_sn"]
    assert start_data["session_id"]
    assert start_data["can_stop"] is True

    time.sleep(5)

    stop_payload = build_stream_payload(context, stream_defaults)
    stop_response = stream_client.stop_stream(auth_headers, stop_payload)
    stop_response.raise_for_status()

    assert stop_response.status_code == 200