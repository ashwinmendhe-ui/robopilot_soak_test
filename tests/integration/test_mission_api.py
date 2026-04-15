def test_mission_search_returns_expected_context(stream_client, auth_headers, test_config):
    mission_name = test_config["selection"]["mission_name"]

    result = stream_client.resolve_mission_context(
        headers=auth_headers,
        mission_name=mission_name,
    )

    assert result["mission_name"] == "TestForDrone"
    assert result["company_name"] == "FPT"
    assert result["site_name"] == "Duy Tan"
    assert result["mission_id"] == "092240aa-cb6c-4ecf-abb6-be896ccb22fe"
    assert result["site_id"] == "8dfb48fa-361d-4b32-8a9d-53757a5155b8"
    assert result["company_id"] == "b933ca65-79b6-425f-a4c2-4c26900e8a6f"