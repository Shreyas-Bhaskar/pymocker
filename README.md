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
- **Record + Replay mode** for capturing real API responses and replaying them
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

## Record + Replay Mode

pyapimocker can record real API responses and replay them later, perfect for:
- Capturing real API behavior for testing
- Creating reproducible test environments
- Working offline with recorded responses

### Usage

Start the server in record mode:

```bash
pyapimocker start mock_config.yaml --record --proxy-base-url https://api.example.com
```

- First request to an unmatched endpoint will proxy to the real API and record the response
- Subsequent requests will serve the recorded response from `recorded_mocks.yaml`
- Recorded responses persist between server restarts

### Example

```bash
# Start server in record mode
pyapimocker start mock_config.yaml --record --proxy-base-url https://jsonplaceholder.typicode.com

# First request - proxies and records
curl http://localhost:8000/posts/1

# Second request - serves recorded response
curl http://localhost:8000/posts/1
```

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
- `--record`: Enable record mode
- `--proxy-base-url`: Base URL for proxying in record mode

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
git clone https://github.com/shreyasbhaskar/pyapimocker.git
cd pyapimocker

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Find process using port
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **Invalid YAML/JSON config**
   - Use a YAML validator to check your config
   - Ensure all required fields are present

3. **Record mode not working**
   - Check if `--proxy-base-url` is set
   - Verify network connectivity to target API
   - Check `recorded_mocks.yaml` permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT 