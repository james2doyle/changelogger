# AGENTS.md - Guidance for AI Coding Agents

This file provides context and guidelines for AI coding agents working in the
changelogger repository.

## Project Overview

Changelogger is a Python 3.12 CLI tool that finds CHANGELOG.md URLs for npm
packages. It uses multiple methods: checking unpkg.com, parsing npm view bugs
URLs, using npm repo for monorepo packages, and falling back to GitHub compare
URLs for locally installed outdated packages.

**Architecture**: Single-module design with `changelogger.py` (main source) and
`test_changelogger.py` (test suite).

## Build/Lint/Test Commands

This project uses `uv` as the package manager. All commands should be prefixed
with `uv run` when running in the project environment.

```bash
# Install dependencies
uv sync

# Run the tool
uv run python changelogger.py <package_name>
uv run python changelogger.py -v <package_name>  # verbose

# Run all tests
uv run pytest test_changelogger.py -v

# Run a single test class
uv run pytest test_changelogger.py::TestCheckUrlExists -v

# Run a single test method
uv run pytest test_changelogger.py::TestCheckUrlExists::test_url_exists_returns_true -v

# Run tests matching a pattern
uv run pytest test_changelogger.py -v -k "test_parse"

# Type checking
uv run basedpyright changelogger.py

# Linting
uv run ruff check changelogger.py
uv run ruff check --fix changelogger.py  # auto-fix

# Build and publish
uv build
uv publish
```

## Code Style Guidelines

### Import Organization

Organize imports in three groups, each alphabetized:
1. Standard library imports
2. Third-party imports  
3. Local imports

```python
import argparse
import json
import subprocess
from urllib.parse import urlparse

import requests
from packageurl import PackageURL

from changelogger import find_changelog  # in tests
```

### Type Annotations

- Use full type annotations on ALL functions including return types
- Use modern Python 3.12+ union syntax: `str | None` (not `Optional[str]`)

```python
def parse_github_url(url: str) -> tuple[str, str, str | None]: ...
def check_url_exists(url: str) -> bool: ...
def setup_logging(verbose: bool) -> None: ...
```

### Naming Conventions

| Element    | Convention           | Example                          |
|------------|----------------------|----------------------------------|
| Functions  | snake_case           | `find_changelog`, `check_url_exists` |
| Variables  | snake_case           | `package_name`, `bugs_url`       |
| Constants  | SCREAMING_SNAKE_CASE | `REQUEST_TIMEOUT`, `DEFAULT_BRANCHES` |
| Classes    | PascalCase           | `TestCheckUrlExists`             |
| Logger     | Module-level         | `logger = logging.getLogger(__name__)` |

### Docstrings

Use Google-style docstrings with Args, Returns, and Raises sections:

```python
def check_url_exists(url: str) -> bool:
    """
    Check if a URL exists by sending a HEAD request.

    Args:
        url: The URL to check.

    Returns:
        True if the URL returns a 200 status code, False otherwise.
    """
```

### Error Handling

- Use try/except blocks with specific exception types
- Return `None` for expected failure cases rather than raising exceptions
- Log errors at DEBUG level with context using f-strings

```python
try:
    result = subprocess.run(...)
except subprocess.TimeoutExpired:
    logger.debug("npm view command timed out")
    return None
except json.JSONDecodeError as e:
    logger.debug(f"Failed to parse npm view output: {e}")
    return None
```

### Logging

- Use module-level logger: `logger = logging.getLogger(__name__)`
- Log to stderr (stdout is for program output)
- Debug level for tracing, Warning level for user-facing issues

### Test Style

- Use pytest with class-based test organization
- Test classes: `Test<FunctionName>` (e.g., `TestCheckUrlExists`)
- Test methods: `test_<scenario>` (e.g., `test_url_exists_returns_true`)
- Each test should have a docstring describing what it tests
- Mock at the module level: `patch("changelogger.requests.head")`

```python
class TestCheckUrlExists:
    """Tests for check_url_exists function."""

    def test_url_exists_returns_true(self) -> None:
        """Test that a 200 response returns True."""
        with patch("changelogger.requests.head") as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            result = check_url_exists("https://example.com/file.md")
            assert result is True
```

### Formatting

- Indentation: 4 spaces
- Quotes: Double quotes for strings
- Trailing commas: Use in multi-line structures

## Configuration

| File              | Purpose                                |
|-------------------|----------------------------------------|
| `pyproject.toml`  | Project config, dependencies, tool settings |
| `.python-version` | Python version specification (3.12)    |
| `uv.lock`         | Dependency lock file                   |

Type checking uses basedpyright in `standard` mode (configured in pyproject.toml).

## AI Integration

See @SKILL.md for a detailed guide on using `changelogger` to assist with npm
package upgrades.
