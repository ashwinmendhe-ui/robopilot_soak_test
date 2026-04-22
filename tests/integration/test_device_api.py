def test_device_lookup_returns_expected_device(stream_client, auth_headers, test_config):
    selection = test_config["selection"]

    mission_ctx = stream_client.resolve_mission_context(
        headers=auth_headers,
        mission_name=selection["mission_name"],
        company_name=selection.get("company_name"),
        site_name=selection.get("site_name"),
    )

    result = stream_client.resolve_device_context(
        headers=auth_headers,
        site_id=mission_ctx["site_id"],
        company_id=mission_ctx["company_id"],
        device_name=selection["device_name"],
    )

    # Generic assertions
    assert result["device_name"] == selection["device_name"]
    assert result["device_status"] in {"offline", "online", "streaming", "active", "working"}

    # Strict assertions per scenario
    if selection["device_name"] == "Unitree GO2":
        assert result["device_id"] == "73791841-98dd-4fbf-9c58-0b6c6e213443"
        assert result["device_sn"] == "go2-001"
        assert result["sub_device_sn"] == ""

    elif selection["device_name"] == "DJI M4E":
        assert result["device_id"] == "fd5521cd-dc6d-46f5-809b-fc5f8c653b1f"
        assert result["device_sn"] == "9N9CNA900174W7"
        assert result["sub_device_sn"] == "1581F7FVC25A700DF473"