def test_mission_search_returns_expected_context(stream_client, auth_headers, test_config):
    selection = test_config["selection"]

    result = stream_client.resolve_mission_context(
        headers=auth_headers,
        mission_name=selection["mission_name"],
        company_name=selection.get("company_name"),
        site_name=selection.get("site_name"),
    )

    # Basic assertions (generic, works for any config)
    assert result["mission_name"] == selection["mission_name"]
    assert result["company_name"] == selection["company_name"]
    assert result["site_name"] == selection["site_name"]

    # Optional strict assertions (only if you want fixed validation)
    if selection["mission_name"] == "TestForDrone":
        assert result["mission_id"] == "2e74c669-4c42-47d7-a29c-386edd1c1e21"
        assert result["site_id"] == "dbc139ff-98b9-47db-9171-f5fe8351d1df"
        assert result["company_id"] == "9c9bae60-f42c-42d2-a5dc-c2066c0f9d6c"

    elif selection["mission_name"] == "TestforGO2":
        assert result["mission_id"] == "7dc50d8e-b328-4342-95eb-57e1c35ef7c4"
        assert result["site_id"] == "dbc139ff-98b9-47db-9171-f5fe8351d1df"
        assert result["company_id"] == "9c9bae60-f42c-42d2-a5dc-c2066c0f9d6c"