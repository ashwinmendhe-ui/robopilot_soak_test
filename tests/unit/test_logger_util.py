import csv

from logger_util import SoakLogger


def test_logger_creates_csv_file_with_header(tmp_path):
    txt_path = tmp_path / "logs" / "soak_test.log"
    csv_path = tmp_path / "logs" / "soak_test_results.csv"

    logger = SoakLogger(txt_path=str(txt_path), csv_path=str(csv_path))

    assert txt_path.parent.exists()
    assert csv_path.exists()

    with open(csv_path, "r", encoding="utf-8") as file:
        header = file.readline().strip()

    assert "timestamp" in header
    assert "cycle_no" in header
    assert "device_id" in header


def test_logger_appends_csv_row(tmp_path):
    txt_path = tmp_path / "logs" / "soak_test.log"
    csv_path = tmp_path / "logs" / "soak_test_results.csv"

    logger = SoakLogger(txt_path=str(txt_path), csv_path=str(csv_path))

    logger.write_csv(
        {
            "timestamp": "2026-04-15T10:00:00Z",
            "cycle_no": 1,
            "device_name": "M4E Display Name",
            "device_id": "fd5521cd-dc6d-46f5-809b-fc5f8c653b1f",
            "company_id": "b933ca65-79b6-425f-a4c2-4c26900e8a6f",
            "site_id": "8dfb48fa-361d-4b32-8a9d-53757a5155b8",
            "mission_id": "092240aa-cb6c-4ecf-abb6-be896ccb22fe",
            "action": "start_request",
            "result": "success",
            "http_status": 200,
            "wait_seconds": "",
            "token_refreshed": "no",
            "message": "Start stream API request successful",
            "error_details": "",
        }
    )

    with open(csv_path, "r", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["cycle_no"] == "1"
    assert rows[0]["device_name"] == "M4E Display Name"
    assert rows[0]["result"] == "success"