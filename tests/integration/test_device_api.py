def test_device_lookup_returns_expected_device(stream_client, auth_headers, test_config):
    mission_ctx = stream_client.resolve_mission_context(
        headers=auth_headers,
        mission_name=test_config["selection"]["mission_name"],
    )

    result = stream_client.resolve_device_context(
        headers=auth_headers,
        site_id=mission_ctx["site_id"],
        company_id=mission_ctx["company_id"],
        device_name=test_config["selection"]["device_name"],
    )

    assert result["device_name"] == "M4E Display Name"
    assert result["device_id"] == "fd5521cd-dc6d-46f5-809b-fc5f8c653b1f"
    assert result["device_status"] in {"offline", "online", "streaming", "active"}
    assert result["device_sn"] == "9N9CNA900174W7"
    assert result["sub_device_sn"] == "1581F7FVC25A700DF473"