# Changelogger

Find `CHANGELOG.md` URLs for npm packages.

## Installation

```bash
# Using uv (recommended)
uv sync

# Or install globally
uv tool install .
```

## Usage

```bash
# Run directly with Python
uv run python changelogger.py <package_name> [package_name2 ...]

# Or if installed as a tool
changelogger <package_name> [package_name2 ...]
```

### Examples

```bash
# Single package
uv run python changelogger.py next-sanity-image

# Multiple packages
uv run python changelogger.py next-sanity-image sanity-plugin-iframe-pane

# Nested package (handled automatically)
uv run python changelogger.py sanity-plugin-iframe-pane
```

## How It Works

This tool uses multiple methods to find the `CHANGELOG.md` URL. It will work through the different methods until it finds a valid `CHANGELOG.md` URL.

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest test_changelogger.py -v

# Run with coverage
uv run pytest test_changelogger.py -v --cov=changelogger
```

## Publishing

To publish a new version of `changelogger` to PyPI:

1. **Build the project**:

This creates the source distribution and wheel in the `dist/` directory.

```bash
uv build
```

2. **Publish to PyPI**:

You will need a PyPI API token.

```bash
uv publish
```

## License

MIT
