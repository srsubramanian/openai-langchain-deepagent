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
- Docker and Docker Compose (optional, for Phoenix observability)

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

## Conversation Memory (Checkpointing)

This project supports **conversation memory** via LangGraph checkpointing, allowing agents to remember context across multiple queries in the same session.

### Enabling Checkpointing

Enable checkpointing in your `.env` file:

```bash
ENABLE_CHECKPOINTING=true
CHECKPOINT_DB_PATH=checkpoints.db  # Optional, defaults to checkpoints.db
```

Or enable it programmatically:

```python
from openai_langchain_deepagent.agent import create_agent

# Create agent with checkpointing enabled
agent = create_agent(enable_checkpointing=True)
```

### Using Conversation Sessions

Use a `thread_id` to maintain conversation context:

```python
import uuid

# Create a unique session ID
thread_id = f"user-{uuid.uuid4().hex[:8]}"
config = {"configurable": {"thread_id": thread_id}}

# First query
result1 = agent.invoke(
    {"messages": [{"role": "user", "content": "I'm planning a trip to Paris"}]},
    config=config
)

# Agent remembers the previous context!
result2 = agent.invoke(
    {"messages": [{"role": "user", "content": "What should I pack?"}]},
    config=config
)
```

### Running the Memory Demo

Run the conversation memory example:

```bash
uv run python examples/conversation_with_memory.py
```

This demonstrates a multi-turn conversation where the agent remembers context from previous queries.

### Managing Sessions

Use session utilities to manage conversation history:

```python
from openai_langchain_deepagent.session_utils import (
    list_active_sessions,
    get_session_info,
    clear_session,
)

# List all active sessions
sessions = list_active_sessions()
print(f"Active sessions: {sessions}")

# Get session information
info = get_session_info("user-abc123")
print(f"Session has {info['checkpoint_count']} checkpoints")

# Clear a specific session
clear_session("user-abc123")
```

### Checkpoint Persistence

- Checkpoints are stored in SQLite database (default: `checkpoints.db`)
- Sessions persist across agent restarts
- Different `thread_id` values create isolated conversations
- Each checkpoint includes full conversation state

## Layer 1 Session Memory (Single-Merchant Conversations)

This project implements **Layer 1 Session Memory**, a merchant-focused conversation memory system where each session is dedicated to ONE merchant with intelligent state management, caching, and tracking.

### Overview

Layer 1 provides:
- **Single-merchant sessions**: One session = one merchant conversation
- **Smart caching**: TTL-based caching for profiles, metrics, transactions, alerts
- **Conversation tracking**: Topics discussed, recommendations, pending questions
- **Session metadata**: Query counts, advisor notes, timestamps
- **Merchant validation**: Ensure queries are about the correct merchant

### Key Concepts

**Session State Structure:**
```python
SessionState = {
    # LangGraph messages (conversation history)
    "messages": [...],

    # Session metadata
    "session_id": "ses_20250109_143022_abc123de",
    "advisor_id": "adv_001",
    "started_at": "2025-01-09T14:30:22.123456+00:00",
    "last_activity_at": "2025-01-09T14:35:45.789012+00:00",

    # Merchant context (SINGLE merchant per session)
    "merchant_id": "mch_789456",
    "merchant_name": "TechRetail",
    "segment": "mid_market",  # small_business, mid_market, enterprise

    # Session metrics
    "total_queries": 5,

    # Smart caching (with TTL)
    "cached_data": {"profile": {...}, "metrics": {...}},
    "cached_at": {"profile": "2025-01-09T14:30:00Z", ...},

    # Conversation tracking
    "topics_discussed": ["decline_rates", "transaction_volume"],
    "recommendations": [{...}],
    "pending_questions": ["What is the refund rate?"],
    "advisor_notes": [{"note": "...", "timestamp": "..."}],

    # Working data (scratch space)
    "working_data": {}
}
```

**Cache TTL Configuration:**
- Profile data: 30 minutes (1800 seconds)
- Metrics: 5 minutes (300 seconds)
- Transactions: 1 minute (60 seconds)
- Alerts: 30 seconds

### Basic Usage

```python
from openai_langchain_deepagent.agent import (
    start_merchant_session,
    run_query_in_session,
)
from openai_langchain_deepagent.session_manager import add_topic, add_recommendation
from openai_langchain_deepagent.session_inspector import print_session_state

# Start a session for a merchant
agent, thread_id, state = start_merchant_session(
    advisor_id="adv_001",
    merchant_id="789456",  # Auto-normalized to mch_789456
    merchant_name="TechRetail",
    segment="mid_market"
)

# Run queries with conversation memory
response, state = run_query_in_session(
    agent=agent,
    thread_id=thread_id,
    session_state=state,
    query="What can you tell me about this merchant's decline rate?"
)

# Track topics and add recommendations
state = add_topic(state, "decline_rates")
state = add_recommendation(
    state=state,
    recommendation_type="decline_optimization",
    priority="high",
    description="Review fraud filter settings",
    expected_impact="Reduce false positives by 15-20%"
)

# Inspect session state
print_session_state(state, detailed=True)
```

### Running the Demo

Run the single-merchant session demo:

```bash
uv run python examples/single_merchant_session_demo.py
```

This demonstrates:
- Starting a merchant session
- Running multiple queries with memory
- Adding topics and recommendations
- Merchant ID validation
- Inspecting and exporting session data

### Session Management Functions

**Core functions in `session_manager.py`:**

- `initialize_session_state()` - Create new session with unique ID
- `extract_merchant_id()` - Extract merchant ID from text with regex
- `increment_query_count()` - Update query count and timestamp
- `cache_data()` / `get_cached_data()` - Smart caching with TTL
- `add_topic()` - Add discussion topic (no duplicates)
- `add_recommendation()` - Add recommendation with priority
- `add_pending_question()` - Track unanswered questions
- `add_advisor_note()` - Add timestamped advisor note
- `get_session_summary()` - Get session metrics
- `validate_merchant_match()` - Validate merchant ID

**Session inspection functions:**

- `print_session_state()` - Print formatted session info
- `export_session_summary()` - Export JSON-serializable summary

### Session ID Formats

- **Session ID**: `ses_YYYYMMDD_HHMMSS_{8char_uuid}`
  - Example: `ses_20250109_143022_abc123de`

- **Thread ID**: `merchant_{merchant_id}_{YYYYMMDD_HHMMSS}`
  - Example: `merchant_mch_789456_20250109_143022`

- **Merchant ID**: Always normalized to `mch_XXXXXX` format
  - Input: `789456` → Output: `mch_789456`
  - Input: `mch_789456` → Output: `mch_789456`

### Merchant Validation

Ensure queries are about the correct merchant:

```python
from openai_langchain_deepagent.session_manager import validate_merchant_match

# Validate merchant ID matches session
is_valid = validate_merchant_match(state, "mch_789456")
if not is_valid:
    print("Warning: Query is about a different merchant!")
```

### Testing

Run Layer 1 session memory tests:

```bash
# Run all session memory tests
uv run pytest tests/test_session_memory.py -v

# Run specific test
uv run pytest tests/test_session_memory.py::TestSessionManager::test_cache_expiration -v
```

### Phoenix Tracing for Sessions

Layer 1 Session Memory includes **automatic Phoenix tracing** for complete observability of multi-turn sessions.

**What gets traced:**

1. **Session Metadata** (on every span):
   - `session.id` - Unique session identifier
   - `session.thread_id` - LangGraph thread ID
   - `session.advisor_id` - Advisor running the session
   - `merchant.id`, `merchant.name`, `merchant.segment` - Merchant context
   - `session.query_number` - Query sequence number

2. **Session State Snapshots** (before/after each query):
   - `session.total_queries` - Total queries in session
   - `session.duration_seconds` - Session duration
   - `session.topics_count` - Number of topics discussed
   - `session.topics` - List of topics
   - `session.recommendations_count` - Number of recommendations
   - `session.cached_data_types` - What's in cache
   - `cache_age_{data_type}` - Age of each cached item

3. **Cache Performance** (on cache lookups):
   - `cache.data_type` - Type of data being accessed
   - `cache.hit` - true/false
   - `cache.miss_reason` - "not_found" or "expired"
   - `cache.age_seconds` - Age of cached data
   - `cache.ttl_seconds` - TTL for this data type

**Running the Phoenix tracing demo:**

```bash
# Start Phoenix
docker compose up -d

# Run the tracing demo
uv run python examples/session_with_phoenix_tracing.py

# Open Phoenix UI
open http://localhost:6006
```

**Viewing traces in Phoenix:**

```python
# Filter by session ID to see all queries
session.id = "ses_20250109_143022_abc123de"

# Find sessions with recommendations
session.recommendations_count > 0

# Analyze cache performance
cache.hit = false

# Group by merchant
merchant.id = "mch_789456"
```

**Timeline view in Phoenix:**

```
14:30:00 - merchant_query [Query 1]
  ├─ 📸 session_snapshot_before (queries=0, topics=[])
  ├─ 🤖 LLM Call
  └─ 📸 session_snapshot_after (queries=1, topics=[])

14:32:15 - merchant_query [Query 2]
  ├─ 📸 session_snapshot_before (queries=1, topics=["decline_rates"])
  ├─ 💾 cache_lookup (profile: HIT, age=135s)
  ├─ 🤖 LLM Call
  └─ 📸 session_snapshot_after (queries=2, recommendations=1)

14:35:42 - merchant_query [Query 3]
  ├─ 📸 session_snapshot_before (queries=2, topics=["decline_rates", "volume"])
  ├─ 💾 cache_lookup (profile: HIT, age=342s)
  ├─ 💾 cache_lookup (transactions: MISS, expired)
  ├─ 🤖 LLM Call
  └─ 📸 session_snapshot_after (queries=3)
```

## Phoenix Observability

This project includes **automatic Phoenix instrumentation** for observability and tracing of your DeepAgent executions.

### Starting Phoenix

Start the Phoenix service using Docker Compose:

```bash
# Start Phoenix in the background
docker compose up -d

# View logs
docker compose logs -f phoenix

# Check status
docker compose ps
```

Phoenix will be available at:
- **UI**: http://localhost:6006
- **OTLP gRPC**: localhost:4317
- **Prometheus metrics**: http://localhost:9090

### Using Phoenix with DeepAgents

**Phoenix instrumentation is enabled by default!** When you run your agent examples, traces are automatically sent to Phoenix at http://localhost:6006.

```bash
# Start Phoenix first
docker compose up -d

# Run your agent (traces will automatically appear in Phoenix UI)
uv run python examples/basic_agent.py

# Open Phoenix UI to see traces
open http://localhost:6006
```

You'll see detailed traces including:
- LLM requests and responses
- Token usage and costs
- Latency metrics
- Agent tool calls
- Complete execution flows

### Configuration

Control Phoenix instrumentation via environment variables in your `.env` file:

```bash
# Enable/disable Phoenix (default: true)
PHOENIX_ENABLED=true

# Phoenix endpoint (default: http://localhost:4317)
PHOENIX_ENDPOINT=http://localhost:4317
```

To disable Phoenix instrumentation:
```bash
# In your .env file
PHOENIX_ENABLED=false
```

### Data Persistence

Phoenix data is automatically persisted using a Docker volume named `phoenix-data`. This means:
- Your traces and metrics survive container restarts
- Data persists even when you stop and start the container
- You can safely restart or upgrade Phoenix without losing data

To view volume information:
```bash
# List volumes
docker volume ls

# Inspect the Phoenix volume
docker volume inspect openai-langchain-deepagent_phoenix-data
```

### Stopping Phoenix

```bash
# Stop Phoenix (data is preserved)
docker compose down

# Stop and remove volumes (⚠️ deletes all Phoenix data)
docker compose down -v
```

### Backing Up Phoenix Data

To backup your Phoenix data:
```bash
# Create a backup directory
mkdir -p backups

# Backup Phoenix data
docker run --rm -v openai-langchain-deepagent_phoenix-data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/phoenix-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
```

To restore from backup:
```bash
# Restore Phoenix data
docker run --rm -v openai-langchain-deepagent_phoenix-data:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/phoenix-backup-YYYYMMDD-HHMMSS.tar.gz -C /data
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
│       ├── main.py              # Main entry point
│       ├── agent.py             # DeepAgent implementation with session functions
│       ├── instrumentation.py   # Phoenix observability setup
│       ├── session_utils.py     # Session/checkpoint management utilities
│       ├── state.py             # Layer 1: SessionState TypedDict definitions
│       ├── session_manager.py   # Layer 1: Core session management functions
│       └── session_inspector.py # Layer 1: Session inspection utilities
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   ├── test_agent.py            # DeepAgent tests
│   ├── test_checkpointing.py    # Checkpointing tests
│   └── test_session_memory.py   # Layer 1: Session memory tests
├── examples/
│   ├── basic_agent.py                    # Basic agent example
│   ├── conversation_with_memory.py       # Conversation memory demo
│   └── single_merchant_session_demo.py   # Layer 1: Single-merchant session demo
├── .env.example                 # Example environment variables
├── docker-compose.yml           # Phoenix observability service
├── pyproject.toml               # Project configuration
├── checkpoints.db               # SQLite checkpoint database (created at runtime)
└── README.md
```

## Built-in Middleware

All agents created with `create_agent()` automatically include the following middleware:

### TodoListMiddleware (Task Planning)
- **Tool**: `write_todos`
- **Purpose**: Helps agents plan and track multi-step tasks
- **Usage**: The agent automatically uses this tool to break down complex tasks into manageable steps
- **States**: `pending`, `in_progress`, `completed`

### FilesystemMiddleware (File Operations)
- **Tools**: `write_file`, `read_file`, `edit_file`, `ls`, `glob_search`, `grep_search`
- **Purpose**: Enables agents to work with files for context management
- **Use Cases**: Reading code, writing reports, managing large contexts

### SubAgentMiddleware (Specialized Agents)
- **Tool**: `call_subagent`
- **Purpose**: Spawn specialized sub-agents for complex, multi-step workflows
- **Use Cases**: Delegating specialized tasks to focused agents

### Using TodoListMiddleware

Run the demo to see the TodoListMiddleware in action:

```bash
uv run python examples/todo_middleware_demo.py
```

The agent will automatically use the `write_todos` tool to plan complex tasks:

```python
from openai_langchain_deepagent.agent import create_agent

agent = create_agent()

# Give the agent a complex task
result = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Create a Python data analysis pipeline with visualization"
    }]
})

# The agent will use write_todos to break down the task into steps
```

### Custom Middleware

To add your own middleware:

```python
from openai_langchain_deepagent.agent import create_agent_with_custom_middleware
from langchain.agents.middleware import LoggingMiddleware

agent = create_agent_with_custom_middleware(
    middleware=[LoggingMiddleware()],
    system_prompt="You are a specialized data analysis assistant"
)
```

## Features

### DeepAgent Capabilities

This project demonstrates:

1. **Planning**: Agents can break down complex tasks into steps (TodoListMiddleware)
2. **File Operations**: Read, write, and edit files for context management (FilesystemMiddleware)
3. **Subagent Spawning**: Create specialized agents for complex workflows (SubAgentMiddleware)
4. **OpenAI Integration**: Leverages GPT-4o and other OpenAI models
5. **Conversation Memory**: LangGraph checkpointing for persistent conversations
6. **Layer 1 Session Memory**: Single-merchant sessions with smart caching and tracking
7. **Phoenix Observability**: Automatic LLM tracing and monitoring
8. **Extensible**: Easy to add custom tools and middleware

### Key Components

- `agent.py`: Core DeepAgent implementation with session functions
- `session_manager.py`: Layer 1 session state management with caching
- `session_inspector.py`: Session inspection and export utilities
- `examples/single_merchant_session_demo.py`: Complete Layer 1 demo
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
