
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from heidi_cli.server import validate_run_id, app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_validate_run_id_valid():
    validate_run_id("valid-id")
    validate_run_id("valid_id")
    validate_run_id("valid.id")
    validate_run_id("12345678")
    validate_run_id("123-abc_ABC.xyz")

def test_validate_run_id_invalid():
    with pytest.raises(HTTPException) as excinfo:
        validate_run_id("invalid/id")
    assert excinfo.value.status_code == 400

    with pytest.raises(HTTPException) as excinfo:
        validate_run_id("invalid\\id")
    assert excinfo.value.status_code == 400

    with pytest.raises(HTTPException) as excinfo:
        validate_run_id("..")
    assert excinfo.value.status_code == 400

    with pytest.raises(HTTPException) as excinfo:
        validate_run_id("../sensitive")
    assert excinfo.value.status_code == 400

    with pytest.raises(HTTPException) as excinfo:
        validate_run_id("sensitive/..")
    assert excinfo.value.status_code == 400

    with pytest.raises(HTTPException) as excinfo:
        validate_run_id("")
    assert excinfo.value.status_code == 400

    with pytest.raises(HTTPException) as excinfo:
        validate_run_id("a" * 65)
    assert excinfo.value.status_code == 400

    with pytest.raises(HTTPException) as excinfo:
        validate_run_id("invalid char!")
    assert excinfo.value.status_code == 400

def test_api_rejection_of_invalid_id():
    # We mock _require_api_key to bypass auth
    with patch("heidi_cli.server._require_api_key"):
        # Test with characters that are invalid but don't cause path normalization issues in TestClient

        response = client.get("/runs/invalid_char!")
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid run_id"

        long_id = "a" * 65
        response = client.get(f"/runs/{long_id}")
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid run_id"

        # Test cancel endpoint
        response = client.post(f"/runs/{long_id}/cancel")
        assert response.status_code == 400

        # Test stream endpoint
        response = client.get(f"/runs/{long_id}/stream")
        assert response.status_code == 400
