import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
import httpx
import yaml

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
            },
            {
                "path": "/user-type",
                "method": "GET",
                "switch": {
                    "param": "user_type",
                    "param_type": "query",
                    "cases": {
                        "admin": {
                            "status": 200,
                            "body": {"role": "admin"}
                        },
                        "guest": {
                            "status": 200,
                            "body": {"role": "guest"}
                        }
                    },
                    "default": {
                        "status": 404,
                        "body": {"error": "User type not found"}
                    }
                }
            }
        ]
    }
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
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


def test_switch_cases(client):
    # Test admin case
    response = client.get("/user-type?user_type=admin")
    assert response.status_code == 200
    assert response.json() == {"role": "admin"}

    # Test guest case
    response = client.get("/user-type?user_type=guest")
    assert response.status_code == 200
    assert response.json() == {"role": "guest"}

    # Test default case
    response = client.get("/user-type?user_type=unknown")
    assert response.status_code == 404
    assert response.json() == {"error": "User type not found"}


@pytest.mark.asyncio
async def test_record_replay(tmp_path):
    # Create a test config
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
        yaml.dump(config, f)

    # Start server in record mode
    server = MockServer(
        str(config_path),
        record_mode=True,
        proxy_base_url="https://httpbin.org"
    )
    client = TestClient(server.app)

    # First request should proxy and record
    response = client.get("/get")
    assert response.status_code == 200
    assert "origin" in response.json()

    # Check if recorded_mocks.yaml was created
    mock_file = Path("recorded_mocks.yaml")
    assert mock_file.exists()
    
    # Second request should replay recorded response
    response = client.get("/get")
    assert response.status_code == 200
    assert "origin" in response.json()

    # Cleanup
    mock_file.unlink(missing_ok=True)


def test_invalid_config(tmp_path):
    # Create an invalid config file
    config_path = tmp_path / "invalid_config.yaml"
    with open(config_path, "w") as f:
        f.write("invalid: yaml: content: [")
    
    # Server should handle invalid config gracefully
    with pytest.raises(Exception):
        MockServer(str(config_path))


def test_file_not_found(tmp_path):
    # Create a config with non-existent file reference
    config = {
        "routes": [
            {
                "path": "/test",
                "method": "GET",
                "response": {
                    "status": 200,
                    "file": "nonexistent.json"
                }
            }
        ]
    }
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    
    server = MockServer(str(config_path))
    client = TestClient(server.app)
    
    # Should handle missing file gracefully
    response = client.get("/test")
    assert response.status_code == 500
    assert "error" in response.json() 