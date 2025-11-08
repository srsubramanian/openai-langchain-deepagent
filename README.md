# openai-langchain-deepagent

A Python starter project using uv for fast dependency management.

## About

This is a modern Python project template that uses [uv](https://github.com/astral-sh/uv) for dependency management and packaging.

## Prerequisites

- Python 3.8 or higher
- uv (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Installation

1. Clone this repository
2. Install dependencies with uv:

```bash
# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the project in development mode
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"
```

## Usage

### Quick Run with uv

The fastest way to run the project (no installation needed):

```bash
uv run python -m openai_langchain_deepagent.main
```

### Traditional Run

After installing the project, run the main module:

```bash
python -m openai_langchain_deepagent.main
```

### Import in Your Code

Or import in your Python code:

```python
from openai_langchain_deepagent.main import hello

print(hello("World"))
```

## Development

### Running Tests

```bash
# Run tests with pytest (using uv)
uv run pytest

# Run tests with coverage
uv run pytest --cov=openai_langchain_deepagent
```

### Code Formatting

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check code
ruff check .

# Format code
ruff format .
```

## Project Structure

```
.
├── src/
│   └── openai_langchain_deepagent/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── pyproject.toml
└── README.md
```

## License

MIT
