from unittest.mock import Mock, patch

from stream_api import StreamApiClient


def create_client():
    return StreamApiClient(
        base_url="http://example.com/api",
        endpoints={
            "missions_search": "/v1/missions/search",
            "devices_list": "/v1/devices",
            "stream_start": "/v1/stream/start",
            "stream_stop": "/v1/stream/stop",
            "stream_list": "/v1/stream",
        },
        timeout=30,
    )


@patch("stream_api.requests.request")
def test_resolve_mission_context(mock_request):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [
        {
            "id": 45,
            "missionId": "092240aa-cb6c-4ecf-abb6-be896ccb22fe",
            "siteId": "8dfb48fa-361d-4b32-8a9d-53757a5155b8",
            "companyId": "b933ca65-79b6-425f-a4c2-4c26900e8a6f",
            "missionName": "TestForDrone",
            "missionType": "안전 감시",
            "deviceType": "드론",
            "siteName": "Duy Tan",
            "companyName": "FPT",
        }
    ]
    mock_request.return_value = mock_response

    client = create_client()
    result = client.resolve_mission_context(
        headers={"Authorization": "Bearer test"},
        mission_name="TestForDrone",
    )

    assert result["mission_id"] == "092240aa-cb6c-4ecf-abb6-be896ccb22fe"
    assert result["site_id"] == "8dfb48fa-361d-4b32-8a9d-53757a5155b8"
    assert result["company_id"] == "b933ca65-79b6-425f-a4c2-4c26900e8a6f"
    assert result["mission_name"] == "TestForDrone"
    assert result["site_name"] == "Duy Tan"
    assert result["company_name"] == "FPT"
    assert result["device_type"] == "드론"


@patch("stream_api.requests.request")
def test_resolve_device_context(mock_request):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [
        {
            "id": 38,
            "deviceId": "fd5521cd-dc6d-46f5-809b-fc5f8c653b1f",
            "siteId": "8dfb48fa-361d-4b32-8a9d-53757a5155b8",
            "companyId": "b933ca65-79b6-425f-a4c2-4c26900e8a6f",
            "deviceSn": "9N9CNA900174W7",
            "deviceName": "M4E Display Name",
            "deviceType": "드론",
            "status": "offline",
            "subDeviceInfo": {
                "subDeviceId": "de45e65b-a878-43b9-b47d-006c3bd79fde",
                "sn": "1581F7FVC25A700DF473",
            },
        }
    ]
    mock_request.return_value = mock_response

    client = create_client()
    result = client.resolve_device_context(
        headers={"Authorization": "Bearer test"},
        site_id="8dfb48fa-361d-4b32-8a9d-53757a5155b8",
        company_id="b933ca65-79b6-425f-a4c2-4c26900e8a6f",
        device_name="M4E Display Name",
    )

    assert result["device_id"] == "fd5521cd-dc6d-46f5-809b-fc5f8c653b1f"
    assert result["device_name"] == "M4E Display Name"
    assert result["device_type"] == "드론"
    assert result["device_status"] == "offline"
    assert result["device_sn"] == "9N9CNA900174W7"
    assert result["sub_device_sn"] == "1581F7FVC25A700DF473"
    assert result["sub_device_id"] == "de45e65b-a878-43b9-b47d-006c3bd79fde"


@patch("stream_api.requests.request")
def test_is_device_stream_active_returns_true_for_streaming_status(mock_request):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [
        {
            "deviceId": "fd5521cd-dc6d-46f5-809b-fc5f8c653b1f",
            "status": "streaming",
        }
    ]
    mock_request.return_value = mock_response

    client = create_client()
    active, message, status_code = client.is_device_stream_active(
        headers={"Authorization": "Bearer test"},
        device_id="fd5521cd-dc6d-46f5-809b-fc5f8c653b1f",
    )

    assert active is True
    assert "Matched device" in message
    assert status_code == 200


@patch("stream_api.requests.request")
def test_is_device_stream_active_returns_false_when_not_found(mock_request):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = []
    mock_request.return_value = mock_response

    client = create_client()
    active, message, status_code = client.is_device_stream_active(
        headers={"Authorization": "Bearer test"},
        device_id="fd5521cd-dc6d-46f5-809b-fc5f8c653b1f",
    )

    assert active is False
    assert "No active stream found" in message
    assert status_code == 200