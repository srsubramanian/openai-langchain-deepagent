# openai-langchain-deepagent

A Python project demonstrating LangChain DeepAgents with OpenAI integration.

## About

This project showcases the [LangChain DeepAgents](https://docs.langchain.com/oss/python/deepagents/overview) library, which enables building autonomous agents capable of:

- **Complex Task Planning**: Break down tasks into manageable steps with built-in planning tools
- **File System Management**: Handle large contexts using filesystem tools (read, write, edit files)
- **Subagent Spawning**: Create specialized agents for complex, multi-step workflows
- **OpenAI Integration**: Powered by OpenAI's GPT models

The project uses [uv](https://github.com/astral-sh/uv) for fast dependency management.

## Prerequisites

- Python 3.11 or higher (required by deepagents)
- uv (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [OpenAI API key](https://platform.openai.com/api-keys)

## Installation

1. Clone this repository
2. Set up your API keys:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
```

3. Install dependencies with uv:

```bash
# Option 1: Quick install (recommended)
uv sync

# Option 2: Manual install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
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

### Using DeepAgents

Run the example demonstrating DeepAgent capabilities:

```bash
uv run python examples/basic_agent.py
```

Or use DeepAgents in your own code:

```python
from openai_langchain_deepagent.agent import create_agent, run_agent_task

# Quick usage
result = run_agent_task("Write a Python function to sort a list")
print(result)

# Advanced usage with custom configuration
agent = create_agent(model="gpt-4o", temperature=0.5)
response = agent.invoke({"messages": [{"role": "user", "content": "Your task here"}]})
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
│       ├── main.py          # Main entry point
│       └── agent.py         # DeepAgent implementation
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_agent.py        # DeepAgent tests
├── examples/
│   └── basic_agent.py       # Example usage
├── .env.example             # Example environment variables
├── pyproject.toml           # Project configuration
└── README.md
```

## Features

### DeepAgent Capabilities

This project demonstrates:

1. **Planning**: Agents can break down complex tasks into steps
2. **File Operations**: Read, write, and edit files for context management
3. **OpenAI Integration**: Leverages GPT-4o and other OpenAI models
4. **Extensible**: Easy to add custom tools and capabilities

### Key Components

- `agent.py`: Core DeepAgent implementation with provider abstraction
- `examples/basic_agent.py`: Demonstrates common use cases
- Comprehensive test suite with mocking for CI/CD

## Configuration

### Environment Variables

Set the following in your `.env` file:

```bash
# OpenAI API Key (required)
OPENAI_API_KEY=your_key_here
```

### Supported Models

You can use any OpenAI model:
- `gpt-4o` (default, recommended)
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

Pass the model parameter when creating an agent:
```python
agent = create_agent(model="gpt-4-turbo")
```

## Learn More

- [LangChain DeepAgents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [DeepAgents GitHub Repository](https://github.com/langchain-ai/deepagents)
- [LangChain Documentation](https://python.langchain.com/)

## License

MIT
