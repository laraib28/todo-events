# Testing Guide

This directory contains automated and manual tests for the backend API.

## Quick Start

### 1. Install Test Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `httpx` - HTTP client for testing
- `pytest-mock` - Mocking support

### 2. Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_chat.py

# Run specific test
pytest tests/test_chat.py::TestChatEndpoint::test_chat_successful_response

# Run with coverage (if pytest-cov installed)
pytest --cov=app --cov-report=html
```

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures and configuration
├── test_chat.py          # Chat endpoint tests
├── MANUAL_TESTS.md       # Manual curl test cases
└── README.md            # This file
```

## Test Fixtures

Available fixtures (from `conftest.py`):

- `session` - Test database session (in-memory SQLite)
- `client` - FastAPI test client
- `test_user` - Pre-created test user
- `auth_token` - Valid JWT token for test user
- `auth_headers` - Headers with auth cookie
- `test_task` - Pre-created test task
- `conversation_history` - Pre-created conversation history

## Test Categories

### Unit Tests

Tests individual components in isolation with mocked dependencies:

```bash
pytest tests/test_chat.py -m unit
```

### Integration Tests

Tests full request/response cycle with database:

```bash
pytest tests/test_chat.py -m integration
```

## Writing New Tests

Example test structure:

```python
import pytest
from unittest.mock import patch, AsyncMock

def test_my_feature(client, auth_headers):
    """Test description."""
    response = client.post(
        "/api/chat",
        json={"message": "Test"},
        headers=auth_headers
    )
    assert response.status_code == 200
```

## Mocking External Services

### Mock OpenAI Agent

```python
@patch('app.routers.chat.TodoAgent')
def test_with_mocked_agent(mock_agent_class, client, auth_headers):
    # Setup mock
    mock_agent = MagicMock()
    mock_agent.process_message = AsyncMock(return_value={
        "message": "Response",
        "metadata": None
    })
    mock_agent_class.return_value = mock_agent

    # Make request
    response = client.post("/api/chat", ...)

    # Verify
    assert response.status_code == 200
    mock_agent.process_message.assert_called_once()
```

## Manual Testing

For manual testing with curl, see:

```bash
cat tests/MANUAL_TESTS.md
```

Or run the automated script:

```bash
chmod +x tests/test_chat.sh
./tests/test_chat.sh
```

## Continuous Integration

To run tests in CI/CD:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --tb=short
```

## Test Database

Tests use an in-memory SQLite database that is:
- Created fresh for each test session
- Isolated per test function
- Automatically cleaned up after tests

## Debugging Failed Tests

```bash
# Show full stack traces
pytest --tb=long

# Stop at first failure
pytest -x

# Show print statements
pytest -s

# Run specific failing test
pytest tests/test_chat.py::test_name -vv
```

## Common Issues

### Issue: "No module named 'app'"

**Solution**: Run pytest from the `backend` directory:
```bash
cd backend
pytest
```

### Issue: "Database connection error"

**Solution**: Tests use in-memory SQLite, not PostgreSQL. Ensure `conftest.py` is present.

### Issue: "OpenAI API key not found"

**Solution**: Tests mock OpenAI calls. Check `conftest.py` sets `OPENAI_API_KEY` env var.

## Test Coverage

To generate coverage report:

```bash
# Install coverage tool
pip install pytest-cov

# Run tests with coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Performance Testing

For load testing:

```bash
# Install locust
pip install locust

# Run load test (if locustfile.py exists)
locust -f tests/locustfile.py
```

## Next Steps

1. Run existing tests: `pytest`
2. Review test output
3. Check coverage: `pytest --cov=app`
4. Try manual tests: `bash tests/MANUAL_TESTS.md`
5. Write new tests for new features
