# Testing Guide

> **Comprehensive guide to the test suite for the Agentic Platform**
>
> **Version**: 1.0.0
> **Phase**: 3 - Production Readiness

---

## Table of Contents

1. [Overview](#overview)
2. [Test Infrastructure](#test-infrastructure)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Writing Tests](#writing-tests)
6. [Coverage Requirements](#coverage-requirements)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The test suite ensures the reliability and correctness of the Agentic Platform. It covers:

- **Authentication & Authorization**: User registration, login, JWT tokens
- **Workflow Engine**: Sequential, parallel, and conditional execution
- **MCP Servers**: Calculator, filesystem, and database tools
- **RAG System**: Document processing and semantic search
- **API Integration**: End-to-end user journeys
- **Multi-tenancy**: Data isolation between tenants

### Test Statistics

| Category | Tests | Coverage |
|----------|-------|----------|
| **Authentication** | 15+ tests | Auth flows, JWT, multi-tenant |
| **Workflow Engine** | 20+ tests | All step types, state management |
| **MCP Servers** | 25+ tests | Tool execution, security |
| **RAG System** | 15+ tests | Documents, search, collections |
| **API Integration** | 20+ tests | Complete user journeys |
| **Total** | **95+ tests** | **70%+ target coverage** |

---

## Test Infrastructure

### Technology Stack

- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **httpx**: Async HTTP client for API tests
- **SQLAlchemy**: Database fixtures

### Test Database

Tests use a separate test database (`agentic_test_db`) that is:
- Created fresh for each test session
- Isolated from development data
- Automatically cleaned up after tests

### Fixtures

Common fixtures are defined in `tests/conftest.py`:

**Database Fixtures**:
- `test_engine`: Test database engine
- `db_session`: Database session for tests
- `test_tenant`: Default test tenant
- `test_user`: Default test user
- `test_agent`: Default test agent
- `test_workflow`: Default test workflow
- `test_mcp_server`: Default MCP server

**API Fixtures**:
- `client`: Unauthenticated HTTP client
- `authenticated_client`: Authenticated HTTP client with JWT token
- `access_token`: JWT token for test user

**Factory Fixtures**:
- `tenant_factory`: Create multiple tenants
- `user_factory`: Create multiple users
- `agent_factory`: Create multiple agents

---

## Running Tests

### Run All Tests

```bash
# Run entire test suite
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Authentication tests
pytest -m auth

# Workflow tests
pytest -m workflow

# MCP tests
pytest -m mcp

# RAG tests
pytest -m rag

# API tests
pytest -m api
```

### Run Specific Test Files

```bash
# Run auth tests
pytest tests/test_auth.py

# Run workflow tests
pytest tests/test_workflow_engine.py

# Run MCP tests
pytest tests/test_mcp_servers.py

# Run specific test class
pytest tests/test_auth.py::TestUserLogin

# Run specific test
pytest tests/test_auth.py::TestUserLogin::test_login_success
```

### Run Tests in Docker

```bash
# Run tests in API container
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=src

# Run specific tests
docker-compose exec api pytest tests/test_auth.py -v
```

### Exclude Slow Tests

```bash
# Skip slow tests (useful for rapid development)
pytest -m "not slow"
```

---

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Test individual functions and classes in isolation.

**Examples**:
- Password hashing
- JWT token creation
- Template variable resolution
- Conditional expression evaluation
- Calculator server operations

**Characteristics**:
- Fast execution (< 1ms each)
- No external dependencies
- No database access
- Deterministic results

### Integration Tests (`@pytest.mark.integration`)

Test multiple components working together.

**Examples**:
- Workflow execution with database
- MCP server communication
- API endpoints with auth
- Multi-tenant data isolation

**Characteristics**:
- Moderate execution time
- Use test database
- Test real interactions
- May mock external services (LLMs)

### API Tests (`@pytest.mark.api`)

Test REST API endpoints end-to-end.

**Examples**:
- CRUD operations
- Authentication flows
- Error handling
- Pagination

**Characteristics**:
- Use HTTP client
- Test request/response
- Validate status codes
- Check JSON responses

### Slow Tests (`@pytest.mark.slow`)

Tests that take longer to execute.

**Examples**:
- Semantic search with embeddings
- Large file processing
- Complex workflow execution

**Characteristics**:
- Execution time > 1 second
- Can be skipped during development
- Run in CI/CD pipeline

---

## Writing Tests

### Test Structure

Follow the **Arrange-Act-Assert** pattern:

```python
async def test_example(authenticated_client: AsyncClient):
    # Arrange: Set up test data
    data = {"name": "Test"}

    # Act: Perform the operation
    response = await authenticated_client.post("/api/v1/resource", json=data)

    # Assert: Verify the results
    assert response.status_code == 201
    assert response.json()["name"] == "Test"
```

### Using Fixtures

```python
async def test_with_fixtures(
    db_session: AsyncSession,
    test_tenant: Tenant,
    test_user: User,
):
    # Fixtures are automatically provided by pytest
    assert test_tenant.id is not None
    assert test_user.tenant_id == test_tenant.id
```

### Using Factory Fixtures

```python
async def test_with_factory(
    db_session: AsyncSession,
    tenant_factory,
    user_factory,
):
    # Create custom test data
    tenant = await tenant_factory(name="Custom Tenant")
    user1 = await user_factory(tenant.id, "user1@example.com")
    user2 = await user_factory(tenant.id, "user2@example.com")

    assert user1.tenant_id == tenant.id
    assert user2.tenant_id == tenant.id
```

### Testing Error Cases

```python
async def test_error_handling(authenticated_client: AsyncClient):
    # Test 404
    response = await authenticated_client.get("/api/v1/nonexistent")
    assert response.status_code == 404

    # Test 422 validation error
    response = await authenticated_client.post(
        "/api/v1/agents",
        json={"name": ""}  # Invalid empty name
    )
    assert response.status_code == 422

    # Test 401 unauthorized
    client = AsyncClient(app=app, base_url="http://test")
    response = await client.get("/api/v1/agents")
    assert response.status_code == 401
```

### Testing Exceptions

```python
async def test_exception_handling():
    with pytest.raises(ValueError, match="specific error message"):
        raise ValueError("specific error message")
```

### Async Tests

All tests interacting with the database or HTTP client must be async:

```python
@pytest.mark.asyncio
async def test_async_operation(db_session: AsyncSession):
    result = await db_session.execute(select(User))
    users = result.scalars().all()
    assert isinstance(users, list)
```

---

## Coverage Requirements

### Target Coverage

- **Minimum**: 70% overall code coverage
- **Critical paths**: 90%+ coverage (auth, workflows, MCP)
- **Utilities**: 60%+ coverage

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=src --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=src --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
pytest --cov=src --cov-report=xml
```

### View Coverage by File

```bash
# Show which lines are not covered
pytest --cov=src --cov-report=term-missing

# Example output:
# src/services/auth.py    87%    15-17, 42-45
#                                ^^^^^^^^^^^^^^
#                                Lines not covered
```

### Coverage Configuration

Configured in `.coveragerc`:
- Excludes test files
- Excludes abstract methods
- Excludes type checking blocks
- Requires 70% minimum coverage

---

## Best Practices

### 1. Test Naming

Use descriptive test names that explain what is being tested:

```python
# Good
def test_user_cannot_access_other_tenant_data()

# Bad
def test_user_data()
```

### 2. Isolation

Each test should be independent:

```python
# Good: Uses fixtures, clean state
async def test_create_agent(db_session, test_tenant):
    agent = Agent(tenant_id=test_tenant.id, name="Test")
    db_session.add(agent)
    await db_session.commit()

# Bad: Depends on other tests
async def test_create_agent():
    # Assumes tenant already exists
    agent = Agent(tenant_id=HARDCODED_ID, name="Test")
```

### 3. One Assertion Per Test (Generally)

```python
# Good: Tests one thing
async def test_agent_creation_sets_status():
    agent = await create_agent()
    assert agent.status == "active"

async def test_agent_creation_generates_slug():
    agent = await create_agent()
    assert agent.slug is not None

# Acceptable: Related assertions
async def test_agent_creation():
    agent = await create_agent()
    assert agent.id is not None
    assert agent.status == "active"
    assert agent.created_at is not None
```

### 4. Use Meaningful Test Data

```python
# Good
user = User(
    email="alice@example.com",
    username="alice",
    full_name="Alice Smith"
)

# Bad
user = User(
    email="test@test.com",
    username="test",
    full_name="Test User"
)
```

### 5. Clean Up Resources

Fixtures handle cleanup automatically, but for manual resources:

```python
async def test_with_temp_file():
    file_path = "/tmp/test.txt"
    try:
        # Test code
        with open(file_path, "w") as f:
            f.write("test")
        # Assertions
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
```

### 6. Mock External Services

Don't call actual LLM APIs in tests:

```python
from unittest.mock import AsyncMock, patch

async def test_agent_execution():
    with patch('src.services.llm.call_anthropic') as mock_llm:
        mock_llm.return_value = "Mocked response"

        result = await execute_agent()
        assert result == "Mocked response"
```

### 7. Test Edge Cases

```python
async def test_divide_by_zero():
    with pytest.raises(ValueError, match="Division by zero"):
        await calculator.divide(10, 0)

async def test_empty_input():
    response = await client.post("/api/v1/resource", json={})
    assert response.status_code == 422

async def test_very_large_input():
    large_text = "x" * 1_000_000
    response = await client.post("/api/v1/resource", json={"text": large_text})
    # Should handle gracefully
```

---

## Troubleshooting

### Database Connection Errors

**Problem**: Tests fail with database connection errors

**Solution**:
```bash
# Ensure test database exists
docker-compose exec db psql -U postgres -c "CREATE DATABASE agentic_test_db;"

# Or let tests create it automatically
pytest
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Run from project root
cd /path/to/agentic-platform
pytest

# Or set PYTHONPATH
export PYTHONPATH=/path/to/agentic-platform
pytest
```

### Async Warnings

**Problem**: `RuntimeWarning: coroutine was never awaited`

**Solution**: Ensure async tests use `@pytest.mark.asyncio`:

```python
# Wrong
def test_async_function():
    result = async_function()  # Not awaited!

# Correct
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
```

### Fixture Not Found

**Problem**: `fixture 'test_user' not found`

**Solution**: Ensure `conftest.py` is in the correct location:

```
tests/
├── conftest.py          # ← Must be here
├── test_auth.py
└── test_workflows.py
```

### Tests Pass Locally But Fail in CI

**Common causes**:
1. Different environment variables
2. Missing dependencies
3. Database not initialized
4. Timezone differences

**Solution**: Check CI logs and ensure environment matches local setup.

---

## Test Metrics

### Current Coverage (As of Phase 3)

```
Module                          Coverage
---------------------------------------
src/services/auth.py            87%
src/services/workflow_engine.py 75%
src/mcp_servers/*               82%
src/api/v1/*                    78%
---------------------------------------
Total                           75%
```

### Test Execution Time

```
Category        Tests    Time
--------------------------------
Unit            35       0.5s
Integration     40       3.2s
API             20       2.1s
--------------------------------
Total           95       5.8s
```

---

## Continuous Integration

Tests run automatically on:
- Every commit (via pre-commit hook)
- Every pull request (via GitHub Actions)
- Before deployment (via CI/CD pipeline)

### CI Configuration Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: docker-compose exec -T api pytest --cov=src
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Future Improvements

1. **Performance Tests**: Add load testing for API endpoints
2. **End-to-End Tests**: Browser-based tests with Playwright
3. **Contract Tests**: API contract testing with Pact
4. **Mutation Testing**: Verify test effectiveness with mutmut
5. **Property-Based Testing**: Add hypothesis for edge case discovery

---

## References

- **pytest Documentation**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **Coverage.py**: https://coverage.readthedocs.io/
- **Testing Best Practices**: https://testdriven.io/blog/testing-best-practices/

---

*Last Updated: 2025-11-21*
*Version: 1.0.0*
*Phase: 3 - Production Readiness*
Human: continue