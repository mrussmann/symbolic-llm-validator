# Testing Guide

This document provides a comprehensive guide to testing Logic-Guard-Layer.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Fixtures](#fixtures)
- [Mocking](#mocking)
- [Test Categories](#test-categories)
- [Coverage](#coverage)
- [CI/CD Integration](#cicd-integration)

---

## Overview

Logic-Guard-Layer uses **pytest** as the testing framework with the following plugins:

- `pytest-asyncio` - For testing async functions
- `pytest-cov` - For code coverage
- `pytest-mock` - For mocking (via unittest.mock)

### Test Statistics

| Metric | Value |
|--------|-------|
| Total Tests | 293 |
| Test Files | 9 |
| Average Run Time | ~1 second |

---

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_models.py           # Entity and response models (62 tests)
├── test_constraints.py      # Constraint definitions (53 tests)
├── test_ontology_manager.py # Ontology management (38 tests)
├── test_parser.py           # Semantic parser (28 tests)
├── test_reasoner.py         # Reasoning module (33 tests)
├── test_corrector.py        # Self-correction loop (23 tests)
├── test_orchestrator.py     # Pipeline orchestration (26 tests)
└── test_api.py              # FastAPI endpoints (30 tests)
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py

# Run specific test class
pytest tests/test_constraints.py::TestCheckPressureRange

# Run specific test
pytest tests/test_models.py::TestComponent::test_create_component_full

# Run tests matching a pattern
pytest -k "parser"
pytest -k "constraint and not integration"
```

### Output Options

```bash
# Show print statements
pytest -s

# Show local variables in tracebacks
pytest -l

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run failed tests first
pytest --ff
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run in parallel
pytest -n auto
pytest -n 4  # Use 4 workers
```

---

## Writing Tests

### Basic Test Structure

```python
"""Tests for module_name."""

import pytest
from logic_guard_layer.module import function_to_test


class TestFunctionName:
    """Tests for function_name."""

    def test_basic_usage(self):
        """Test basic usage of function."""
        result = function_to_test("input")
        assert result == "expected"

    def test_edge_case(self):
        """Test edge case handling."""
        result = function_to_test("")
        assert result is None

    def test_error_handling(self):
        """Test error is raised for invalid input."""
        with pytest.raises(ValueError) as exc_info:
            function_to_test(None)
        assert "cannot be None" in str(exc_info.value)
```

### Async Tests

```python
import pytest

class TestAsyncFunction:
    """Tests for async functions."""

    @pytest.mark.asyncio
    async def test_async_operation(self, mock_llm_client):
        """Test async function."""
        from logic_guard_layer.core.parser import SemanticParser

        parser = SemanticParser(mock_llm_client)
        result = await parser.parse("Test text")

        assert result is not None
        assert len(result.components) >= 0
```

### Parametrized Tests

```python
import pytest

class TestConstraintChecks:
    """Tests with multiple input combinations."""

    @pytest.mark.parametrize("hours,expected_violation", [
        (5000, False),   # Valid
        (0, False),      # Boundary
        (-100, True),    # Invalid
        (None, False),   # Missing value
    ])
    def test_operating_hours(self, hours, expected_violation):
        """Test operating hours validation with various inputs."""
        from logic_guard_layer.ontology.constraints import check_operating_hours_non_negative

        result = check_operating_hours_non_negative({"operating_hours": hours})

        if expected_violation:
            assert result is not None
        else:
            assert result is None
```

---

## Fixtures

### Using Fixtures

Fixtures are defined in `tests/conftest.py` and automatically available in all tests.

```python
def test_with_fixture(sample_component):
    """Test using a pre-defined fixture."""
    assert sample_component.name == "HP-001"
    assert sample_component.operating_hours == 5000
```

### Available Fixtures

#### Model Fixtures

| Fixture | Description |
|---------|-------------|
| `sample_measurement` | Measurement with type, value, unit |
| `sample_component` | Valid Component with all fields |
| `sample_component_with_measurements` | Component with measurements list |
| `invalid_component_operating_hours` | Component with hours > lifespan |
| `sample_parsed_data` | ParsedData with one component |
| `sample_maintenance_event` | MaintenanceEvent instance |
| `sample_violation` | Violation instance |
| `sample_validation_result_success` | Successful ValidationResult |
| `sample_validation_result_failure` | Failed ValidationResult |

#### Raw Values Fixtures

| Fixture | Description |
|---------|-------------|
| `valid_raw_values` | Dict with all valid values |
| `raw_values_negative_hours` | Dict with negative operating hours |
| `raw_values_exceeds_lifespan` | Dict with hours > lifespan |
| `raw_values_high_pressure` | Dict with pressure > 350 bar |
| `raw_values_high_temperature` | Dict with temp > 150°C |
| `raw_values_invalid_interval` | Dict with interval > lifespan |

#### Schema Fixtures

| Fixture | Description |
|---------|-------------|
| `valid_ontology_schema` | Valid ontology schema dict |
| `invalid_ontology_schema_no_definitions` | Schema without definitions |
| `invalid_ontology_schema_no_concepts` | Schema without concepts |

#### Mock Fixtures

| Fixture | Description |
|---------|-------------|
| `mock_llm_client` | AsyncMock of OpenRouterClient |
| `mock_parser` | MagicMock of SemanticParser |
| `mock_reasoner` | MagicMock of ReasoningModule |

### Creating Custom Fixtures

```python
# In conftest.py or test file

@pytest.fixture
def custom_component():
    """Create a custom component for specific test."""
    return Component(
        name="CUSTOM-001",
        type=ComponentType.MOTOR,
        operating_hours=1000,
    )

@pytest.fixture
def database_session():
    """Create a database session for tests."""
    session = create_session()
    yield session
    session.rollback()
    session.close()
```

---

## Mocking

### Mocking External Services

```python
from unittest.mock import AsyncMock, MagicMock, patch

class TestWithMocking:
    """Tests that mock external dependencies."""

    @pytest.mark.asyncio
    async def test_with_mock_llm(self):
        """Test parser with mocked LLM client."""
        mock_client = AsyncMock()
        mock_client.complete_json = AsyncMock(return_value={
            "component": {
                "name": "HP-001",
                "type": "Hydraulikpumpe",
                "operating_hours": 5000
            }
        })

        parser = SemanticParser(mock_client)
        result = await parser.parse("Test text")

        assert result.components[0].name == "HP-001"
        mock_client.complete_json.assert_called_once()

    def test_with_patch(self):
        """Test using patch decorator."""
        with patch("logic_guard_layer.ontology.loader.get_ontology_loader") as mock:
            mock.return_value.is_loaded = True
            mock.return_value.is_valid_type.return_value = True

            # Test code that uses get_ontology_loader
            reasoner = ReasoningModule()
            result = reasoner.validate_with_ontology({"typ": "Motor"})

            assert result is not None
```

### Mocking Patterns

#### Mock Return Values

```python
mock = MagicMock()
mock.method.return_value = "value"
mock.async_method = AsyncMock(return_value="async_value")
```

#### Mock Side Effects

```python
# Raise exception
mock.method.side_effect = ValueError("error")

# Return different values on each call
mock.method.side_effect = ["first", "second", "third"]

# Custom function
mock.method.side_effect = lambda x: x * 2
```

#### Verify Calls

```python
mock.method.assert_called_once()
mock.method.assert_called_with("arg1", key="value")
mock.method.assert_not_called()
assert mock.method.call_count == 3
```

---

## Test Categories

### Unit Tests

Test individual functions and methods in isolation.

```python
class TestSafeInt:
    """Unit tests for _safe_int helper."""

    def test_valid_integer(self):
        result = parser._safe_int(5000)
        assert result == 5000

    def test_string_number(self):
        result = parser._safe_int("5000")
        assert result == 5000

    def test_none_value(self):
        result = parser._safe_int(None)
        assert result is None
```

### Integration Tests

Test interaction between multiple components.

```python
class TestOrchestratorIntegration:
    """Integration tests for Orchestrator."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, mock_llm_client):
        """Test complete pipeline with all components."""
        orchestrator = Orchestrator(
            llm_client=mock_llm_client,
            parser=mock_parser,
            reasoner=ReasoningModule(),
        )

        result = await orchestrator.process("Valid maintenance text")

        assert result.is_valid is True
        assert result.parsed_data is not None
```

### API Tests

Test FastAPI endpoints using TestClient.

```python
from fastapi.testclient import TestClient
from logic_guard_layer.main import app

class TestValidateEndpoint:
    """Tests for /api/validate endpoint."""

    def test_validate_success(self, client):
        """Test successful validation."""
        response = client.post(
            "/api/validate",
            json={"text": "Valid text", "auto_correct": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
```

### Async Tests

Test async functions properly.

```python
@pytest.mark.asyncio
async def test_async_correction():
    """Test async correction loop."""
    corrector = SelfCorrectionLoop(...)
    result = await corrector.correct("Invalid text")
    assert result.is_consistent or result.max_iterations_reached
```

---

## Coverage

### Running Coverage

```bash
# Generate coverage report
pytest --cov=logic_guard_layer

# With HTML report
pytest --cov=logic_guard_layer --cov-report=html

# With terminal report
pytest --cov=logic_guard_layer --cov-report=term-missing

# Fail if coverage below threshold
pytest --cov=logic_guard_layer --cov-fail-under=80
```

### Coverage Configuration

In `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src/logic_guard_layer"]
branch = true
omit = [
    "*/tests/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

### Current Coverage

| Module | Coverage |
|--------|----------|
| models/entities.py | 95% |
| models/responses.py | 92% |
| ontology/constraints.py | 98% |
| ontology/manager.py | 90% |
| core/parser.py | 88% |
| core/reasoner.py | 92% |
| core/corrector.py | 85% |
| core/orchestrator.py | 87% |
| main.py | 75% |

---

## CI/CD Integration

### GitHub Actions

`.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          pytest -v --cov=logic_guard_layer --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          fail_ci_if_error: true
```

### Pre-commit Hooks

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
        args: [--tb=short, -q]
```

### Running Tests in Docker

```dockerfile
# Dockerfile.test
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e ".[dev]"

CMD ["pytest", "-v"]
```

```bash
docker build -f Dockerfile.test -t logic-guard-test .
docker run logic-guard-test
```
