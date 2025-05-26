# pyapimocker

A lightweight, config-driven mock API server designed specifically for Python teams. It allows you to quickly define and run mock APIs using simple YAML or JSON configuration files, without requiring Node.js or other non-Python dependencies.

## Features

- **Config-driven setup** using YAML or JSON
- **Lightweight CLI** for spinning up mock servers fast
- **Flexible routes** with support for:
  - Static responses (file or inline body)
  - Status codes
  - Latency simulation
  - Switchable responses based on query, body, or header values
- **Proxy passthrough** for mixed setups where some routes hit real APIs
- **Integration-friendly** with pytest fixtures for testing

## Installation

```bash
pip install pyapimocker
```

## Quick Start

1. Create a YAML configuration file:

```yaml
# mock_config.yaml
routes:
  - path: /users
    method: GET
    response:
      status: 200
      body:
        users:
          - id: 1
            name: "John Doe"
            email: "john@example.com"
          - id: 2
            name: "Jane Smith"
            email: "jane@example.com"
```

2. Start the mock server:

```bash
pyapimocker start mock_config.yaml
```

3. Access your mock API at http://localhost:8000/users

## Configuration Format

The configuration file supports the following structure:

```yaml
# Global headers applied to all responses
global_headers:
  Access-Control-Allow-Origin: "*"
  Content-Type: application/json

# Base path prefix for all routes (optional)
base_path: /api/v1

# Route definitions
routes:
  # Simple GET endpoint with static response
  - path: /users
    method: GET
    response:
      status: 200
      body:
        users: []
      headers:
        Cache-Control: "max-age=3600"
      delay: 500  # Add 500ms delay

  # Dynamic response based on query parameter
  - path: /users/{id}
    method: GET
    switch:
      param: id
      cases:
        "1":
          status: 200
          body:
            id: 1
            name: "John Doe"
        "2":
          status: 200
          body:
            id: 2
            name: "Jane Smith"
      default:
        status: 404
        body:
          error: "User not found"

  # Response with file reference
  - path: /products
    method: GET
    response:
      status: 200
      file: "products.json"

  # Proxy passthrough to real API
  - path: /weather
    method: GET
    proxy: "https://api.weather.example.com/current"
```

## CLI Options

```
pyapimocker start [CONFIG_PATH] [OPTIONS]
```

Options:
- `--port, -p`: Port to run the mock server on (default: 8000)
- `--host, -h`: Host to bind the server to (default: 0.0.0.0)
- `--verbose, -v`: Enable verbose output

## Testing Integration

pyapimocker can be used as a pytest fixture:

```python
import pytest
from fastapi.testclient import TestClient
from pyapimocker.server import MockServer

@pytest.fixture
def client(config_file):
    server = MockServer(config_file)
    return TestClient(server.app)

def test_my_api(client):
    response = client.get("/my-endpoint")
    assert response.status_code == 200
```

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/pyapimocker.git
cd pyapimocker

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT 