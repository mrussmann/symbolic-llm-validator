# Contributing Guide

Thank you for your interest in contributing to Logic-Guard-Layer! This guide will help you get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Documentation](#documentation)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Prioritize community benefit

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or personal attacks
- Publishing private information
- Unprofessional conduct

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- OpenRouter API key (for running LLM-dependent tests)

### Setup

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/logic-guard-layer.git
cd logic-guard-layer

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL/logic-guard-layer.git

# 4. Create virtual environment
python -m venv venv
source venv/bin/activate

# 5. Install in development mode
pip install -e ".[dev]"

# 6. Set up pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# 7. Verify setup
pytest
```

---

## Development Workflow

### Branch Naming

Use descriptive branch names:

```
feature/add-new-constraint
bugfix/fix-parser-error
docs/update-api-reference
refactor/improve-error-handling
test/add-integration-tests
```

### Workflow

1. **Sync with upstream**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make changes**
   - Write code
   - Add tests
   - Update documentation

4. **Test locally**
   ```bash
   pytest -v
   ruff check src/
   mypy src/
   ```

5. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature
   # Open PR on GitHub
   ```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(parser): add support for English input text
fix(reasoner): handle None values in pressure check
docs: update API reference with new endpoints
test(corrector): add cycle detection tests
```

---

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black default)
- Imports: sorted with isort
- Docstrings: Google style
- Type hints: Required for public APIs

### Tools

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Type checking
mypy src/

# All checks
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

### Configuration

`pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

### Code Examples

#### Good

```python
from typing import Optional

from logic_guard_layer.models.responses import Violation, ViolationType


def check_value_range(
    value: Optional[float],
    min_val: float,
    max_val: float,
    property_name: str,
) -> Optional[Violation]:
    """
    Check if a value is within the specified range.

    Args:
        value: The value to check (None values pass)
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        property_name: Name of the property being checked

    Returns:
        Violation if value is out of range, None otherwise
    """
    if value is None:
        return None

    if value < min_val or value > max_val:
        return Violation(
            type=ViolationType.RANGE_ERROR,
            constraint=f"{min_val} <= {property_name} <= {max_val}",
            message=f"{property_name} ({value}) is out of range [{min_val}, {max_val}]",
            property_name=property_name,
            actual_value=value,
            expected_value=f"[{min_val}, {max_val}]",
        )

    return None
```

#### Avoid

```python
# Missing type hints
def check_value(val, min, max, name):
    if val == None:  # Use 'is None'
        return None
    if val < min or val > max:
        return Violation(type = ViolationType.RANGE_ERROR,  # Spaces around =
            constraint=f"{min} <= {name} <= {max}",message=f"{name} out of range",  # Missing space
            property_name=name, actual_value=val, expected_value=f"[{min}, {max}]")  # Long line
    return None
```

---

## Testing Requirements

### Test Coverage

- New features must include tests
- Bug fixes should include regression tests
- Maintain >80% code coverage

### Test Structure

```python
"""Tests for new_module."""

import pytest
from logic_guard_layer.new_module import NewClass


class TestNewClass:
    """Tests for NewClass."""

    def test_basic_functionality(self):
        """Test basic usage."""
        obj = NewClass()
        result = obj.method()
        assert result == expected

    def test_edge_cases(self):
        """Test edge case handling."""
        obj = NewClass()
        result = obj.method(edge_value)
        assert result is None

    def test_error_handling(self):
        """Test error conditions."""
        obj = NewClass()
        with pytest.raises(ValueError):
            obj.method(invalid_value)

    @pytest.mark.asyncio
    async def test_async_method(self):
        """Test async functionality."""
        obj = NewClass()
        result = await obj.async_method()
        assert result is not None
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=logic_guard_layer --cov-report=term-missing

# Run specific tests
pytest tests/test_new_module.py -v
```

---

## Pull Request Process

### Before Submitting

1. **Tests pass**
   ```bash
   pytest -v
   ```

2. **Code is formatted**
   ```bash
   black src/ tests/
   ruff check src/ tests/
   ```

3. **Documentation updated**
   - Docstrings for new functions
   - README if needed
   - API docs for new endpoints

4. **Changelog entry** (if applicable)

### PR Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

1. Automated checks must pass
2. At least one maintainer review
3. All comments addressed
4. Squash and merge (typically)

---

## Issue Guidelines

### Bug Reports

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Call function with '...'
2. Pass parameter '...'
3. See error

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11]
- Package version: [e.g., 1.0.0]

**Additional context**
Any other relevant information.
```

### Feature Requests

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
What you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
Any other relevant information.
```

---

## Documentation

### Docstring Format

Use Google style docstrings:

```python
def function(param1: str, param2: int = 10) -> dict:
    """
    Short description of function.

    Longer description if needed. Can span
    multiple lines.

    Args:
        param1: Description of param1
        param2: Description of param2. Defaults to 10.

    Returns:
        Description of return value.

    Raises:
        ValueError: If param1 is empty.
        TypeError: If param2 is not an integer.

    Example:
        >>> result = function("test", 20)
        >>> print(result)
        {'key': 'value'}
    """
```

### Documentation Updates

When to update docs:
- New features → Update relevant docs
- API changes → Update API reference
- Configuration → Update config docs
- Breaking changes → Update migration guide

### Building Docs

```bash
# If using Sphinx or MkDocs (future)
cd docs
make html
```

---

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- README acknowledgments

Thank you for contributing!
