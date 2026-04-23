from stream_api import StreamApiClient


def test_parse_start_stream_response():
    data = {
        "code": 0,
        "message": "success",
        "data": {
            "streamId": "go2-001",
            "sessionId": "44d37d4a-084d-40b9-b1a2-4eec74eb4f35",
            "viewerCount": 1,
            "startTime": "2026-04-17 14:21:14",
            "canStop": True,
            "isSendHeartBeat": True,
        },
    }

    result = StreamApiClient.parse_start_stream_response(data)

    assert result["stream_id"] == "go2-001"
    assert result["session_id"] == "44d37d4a-084d-40b9-b1a2-4eec74eb4f35"
    assert result["viewer_count"] == 1
    assert result["start_time"] == "2026-04-17 14:21:14"
    assert result["can_stop"] is True
    assert result["is_send_heartbeat"] is True


def test_parse_stop_stream_response():
    data = {
        "deviceSn": "go2-001",
        "playbackUrl": "https://example.com/index.m3u8",
        "siteName": "힐스테이트 도안2단지",
        "deviceName": "Unitree GO2",
        "missionName": "TestforGO2",
        "userName": "sysadmin",
        "startTime": "2026-04-17 14:21:44",
        "endTime": "2026-04-17 14:22:06",
        "totalTime": "00:00:22",
        "labelCounts": {
            "Person": 8
        },
        "bookmarks": [
            {
                "duration": "00:00:02",
                "label": "Person",
                "mdisplay": "14:21:47",
                "m": 1776403307142,
                "s": "segment_001_00001.ts",
                "o": 600
            }
        ]
    }

    result = StreamApiClient.parse_stop_stream_response(data)

    assert result["device_sn"] == "go2-001"
    assert result["playback_url"] == "https://example.com/index.m3u8"
    assert result["site_name"] == "힐스테이트 도안2단지"
    assert result["device_name"] == "Unitree GO2"
    assert result["mission_name"] == "TestforGO2"
    assert result["user_name"] == "sysadmin"
    assert result["start_time"] == "2026-04-17 14:21:44"
    assert result["end_time"] == "2026-04-17 14:22:06"
    assert result["total_time"] == "00:00:22"
    assert result["label_counts"]["Person"] == 8
    assert len(result["bookmarks"]) == 1