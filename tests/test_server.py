import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pyapimocker.server import MockServer


@pytest.fixture
def config_file(tmp_path):
    config = {
        "routes": [
            {
                "path": "/test",
                "method": "GET",
                "response": {
                    "status": 200,
                    "body": {"message": "Hello, World!"},
                },
            }
        ]
    }
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        json.dump(config, f)
    return str(config_path)


@pytest.fixture
def client(config_file):
    server = MockServer(config_file)
    return TestClient(server.app)


def test_simple_get(client):
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


def test_not_found(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404 