from utils import build_stream_payload

def test_build_stream_payload():
    context = {
        "device_sn": "go2-001",
        "mission_id": "7dc50d8e-b328-4342-95eb-57e1c35ef7c4",
    }

    stream_defaults = {
        "url_type": 1,
        "video_quality": 0,
        "video_type": "zoom",
        "video_id": {
            "droneSn": "1581F7FVC25A700DF473",
            "payloadIndex": {
                "type": 99,
                "subType": 0,
                "position": 0
            },
            "videoType": "normal"
        }
    }

    result = build_stream_payload(context, stream_defaults, playback_url="")

    assert result["deviceSn"] == "go2-001"
    assert result["missionId"] == "7dc50d8e-b328-4342-95eb-57e1c35ef7c4"
    assert result["urlType"] == 1
    assert result["videoQuality"] == 0
    assert result["videoType"] == "zoom"
    assert result["videoId"]["droneSn"] == "1581F7FVC25A700DF473"
    assert result["playbackUrl"] == ""