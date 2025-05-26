# Advanced Usage Guide for pyapimocker

## Table of Contents
- [Detailed Configuration Examples](#detailed-configuration-examples)
- [Advanced CLI Options](#advanced-cli-options)
- [CI/CD Integration Tips](#cicd-integration-tips)
- [Pytest & Custom Fixture Setups](#pytest--custom-fixture-setups)
- [Contribution Guidelines](#contribution-guidelines)
- [Architecture Overview](#architecture-overview)

---

## Detailed Configuration Examples

### 1. Dynamic Switches (Query, Path, Header, Body)
```yaml
routes:
  - path: /user-type
    method: GET
    switch:
      param: user_type
      param_type: query
      cases:
        admin:
          status: 200
          body: { role: "admin" }
        guest:
          status: 200
          body: { role: "guest" }
      default:
        status: 404
        body: { error: "User type not found" }

  - path: /users/{id}
    method: GET
    switch:
      param: id
      param_type: path
      cases:
        "1":
          status: 200
          body: { id: 1, name: "John Doe" }
      default:
        status: 404
        body: { error: "User not found" }

  - path: /header-match
    method: GET
    switch:
      param: X-Role
      param_type: header
      cases:
        admin:
          status: 200
          body: { message: "Header matched admin" }
      default:
        status: 403
        body: { error: "Forbidden" }

  - path: /body-match
    method: POST
    switch:
      param: type
      param_type: body
      cases:
        foo:
          status: 200
          body: { message: "Type is foo" }
      default:
        status: 400
        body: { error: "Invalid type" }
```

### 2. File-based and Jinja2/Faker Dynamic Responses
```yaml
routes:
  - path: /products
    method: GET
    response:
      status: 200
      file: "products.json"

  - path: /greet
    method: GET
    response:
      status: 200
      body:
        message: "Hello, {{ faker.name() }}!"
```

### 3. Proxy and Record/Replay
```yaml
routes:
  - path: /external
    method: GET
    proxy: "https://api.example.com/data"

# Start in record mode to capture real API responses
# pyapimocker start config.yaml --record --proxy-base-url https://api.example.com
```

### 4. Global Headers, Delays, and Base Path
```yaml
global_headers:
  Access-Control-Allow-Origin: "*"
  X-Powered-By: "pyapimocker"
base_path: /api/v2
routes:
  - path: /delayed
    method: GET
    response:
      status: 200
      body: { ok: true }
      delay: 1000  # 1 second
```

---

## Advanced CLI Options

- `--port, -p`: Set server port (default: 8000)
- `--host, -h`: Set server host (default: 0.0.0.0)
- `--verbose, -v`: Enable verbose logging
- `--record`: Enable record mode (proxy and record unknown requests)
- `--proxy-base-url`: Set base URL for proxying in record mode
- `--reload`: (If supported) Enable auto-reload for development

**Example:**
```bash
pyapimocker start config.yaml --port 9000 --host 127.0.0.1 --verbose --record --proxy-base-url https://api.example.com
```

---

## CI/CD Integration Tips

### 1. Run as a Background Service
```yaml
# .github/workflows/test.yml
- name: Start Mock API Server
  run: |
    nohup pyapimocker start config.yaml --port 9000 &
    sleep 2  # Wait for server to start
```

### 2. Use in Docker
**Dockerfile**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install .
EXPOSE 8000
CMD ["pyapimocker", "start", "config.yaml"]
```

### 3. Integration with Test Suites
- Start the server before running integration tests
- Use `pytest` or your preferred test runner
- Clean up (kill the server) after tests

---

## Pytest & Custom Fixture Setups

### 1. Basic Pytest Fixture
```python
import pytest
from fastapi.testclient import TestClient
from pyapimocker.server import MockServer

@pytest.fixture(scope="session")
def client():
    server = MockServer("tests/test_config.yaml")
    return TestClient(server.app)

def test_example(client):
    resp = client.get("/users")
    assert resp.status_code == 200
```

### 2. Customizing per-test
```python
@pytest.fixture
def custom_client(tmp_path):
    config = { ... }  # dynamically build config
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    server = MockServer(str(config_path))
    return TestClient(server.app)
```

### 3. Using Record/Replay in Tests
```python
@pytest.fixture(scope="session")
def record_client():
    server = MockServer("tests/test_config.yaml", record_mode=True, proxy_base_url="https://httpbin.org")
    return TestClient(server.app)
```

---

## Contribution Guidelines

1. **Fork the repository** and create a feature branch
2. **Write clear, tested code** (use `pytest` for tests)
3. **Format code** with `black` and `isort`
4. **Document your changes** in README or advanced_usage.md
5. **Open a Pull Request** with a clear description
6. **Participate in code review** and address feedback

---

## Architecture Overview

- **CLI Entrypoint**: `pyapimocker.cli:main` parses args and starts the server
- **Server Core**: `MockServer` class in `pyapimocker.server`
  - Loads config (YAML/JSON)
  - Registers routes, switch logic, proxy, and record/replay
  - Handles static, dynamic, and proxied responses
  - Supports Jinja2/Faker templating
- **Models**: Pydantic models in `pyapimocker.models` for config validation
- **Testing**: Uses `pytest` and `fastapi.testclient`
- **Extensibility**: Add new response types, plugins, or CLI options as needed

---

## Tips & Best Practices
- Use switch cases for dynamic mocks
- Leverage record/replay for integration tests
- Use global headers for CORS and content-type
- Keep configs modular and DRY
- Contribute improvements and report issues on GitHub

---

For more, see the main README or open an issue/discussion on the repository! 