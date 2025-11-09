# OpenAI LangChain Agent Project - Context for Claude

## Project Overview

**Purpose**: A Python project demonstrating LangChain Agents with OpenAI integration, featuring Layer 1 Session Memory for single-merchant conversations and Phoenix observability.

**Package Manager**: UV (modern, fast alternative to pip)

**Python Version**: 3.11+

**Key Technologies**:
- LangChain (standard agents framework)
- LangGraph (ReAct agents with checkpointing/memory)
- OpenAI GPT-4o
- Phoenix (Arize Phoenix for LLM observability)
- SQLite (checkpoints and Phoenix data)
- OpenTelemetry (tracing)

---

## Project Evolution

### Session 1: Foundation
1. Created UV Python starter project
2. Set default git branch to `main`
3. Added LangChain integration with OpenAI (initially used DeepAgents)

### Session 2: Fixes and Refinements (Historical - DeepAgents era)
- Updated Python requirement to 3.11
- Removed Anthropic/Claude support (OpenAI only)

### Session 3: Phoenix Observability
- Added Docker Compose with Phoenix service
- Automatic OpenTelemetry instrumentation for LangChain
- Fixed Phoenix data persistence (volume at `/data` with `PHOENIX_WORKING_DIR`)

### Session 4: LangGraph Checkpointing
- Added conversation memory with SQLiteSaver
- Fixed: Use `SqliteSaver(conn)` directly, not `SqliteSaver.from_conn_string()` (context manager issue)
- Created session utilities and examples

### Session 5: Layer 1 Session Memory (Main Feature)
- Implemented complete merchant-focused conversation system
- Session state with topics, recommendations, caching, notes
- Smart caching with TTL (profile: 30m, metrics: 5m, transactions: 1m, alerts: 30s)
- Session inspector and export utilities

### Session 6: Phoenix Tracing Integration
- Added session metadata to all spans
- Session state snapshots (before/after each query)
- Cache performance tracking (hit/miss, age, TTL)
- Message content in spans

### Session 7: Debugging "Undefined" Messages
- Issue: Messages show as "undefined" in Phoenix when filtering by `session.id = "ses_..."`
- Messages DO work when filtering by `thread_id = "merchant_..."`
- Created troubleshooting guides and debug scripts
- Last 4 debugging commits were removed (per user request)

### Session 8: Simplified Session Management
- Removed dual-ID system (ses_ session ID) to simplify architecture
- Now using only thread_id (merchant_...) as single session identifier
- Retained all Layer 1 features (topics, recommendations, caching, notes)
- Updated all code, tests, examples, and documentation
- Resolves Phoenix message visibility issues by using only thread_id

### Session 9: Migration to Standard LangChain Agents
- Migrated from DeepAgents to standard LangChain agents
- Now using `create_react_agent` from LangGraph's prebuilt agents
- Added tools support (default: Calculator tool)
- Updated dependencies: removed `deepagents`, added `langchain` and `langgraph`
- All session memory features remain intact
- Compatible with same invoke interface and checkpointing
- Updated all examples, tests, and documentation

---

## Architecture

### Core Components

**1. Agent (`agent.py`)**
- `create_agent()` - Main factory function with optional checkpointing
- `create_agent_with_session_memory()` - Convenience wrapper (checkpointing always on)
- `start_merchant_session()` - Initialize merchant session with state
- `run_query_in_session()` - Execute query with Phoenix tracing
- `run_agent_task()` - Simple task execution without sessions

**2. Session Manager (`session_manager.py`)**

Key Functions:
- `initialize_session_state(advisor_id, merchant_id, ...)` → SessionState
- `extract_merchant_id(text)` → str | None (regex extraction)
- `increment_query_count(state)` → SessionState
- `cache_data(state, data_type, data)` → SessionState
- `get_cached_data(state, data_type, config)` → dict | None (with Phoenix tracing)
- `add_topic(state, topic)` → SessionState (normalized, no duplicates)
- `add_recommendation(state, type, priority, description, impact)` → SessionState
- `add_pending_question(state, question)` → SessionState
- `add_advisor_note(state, note)` → SessionState
- `get_session_summary(state)` → Dict
- `validate_merchant_match(state, merchant_id)` → bool
- `create_session_snapshot(state)` → Dict (for Phoenix tracing)

Constants:
- `DEFAULT_CACHE_CONFIG` with TTL values

**3. Session Inspector (`session_inspector.py`)**
- `print_session_state(state, detailed=False)` - Formatted console output
- `export_session_summary(state)` → Dict - JSON-serializable export

**4. State (`state.py`)**
- `SessionState` TypedDict with 16 fields
- `CacheConfig` TypedDict for TTL settings

**5. Instrumentation (`instrumentation.py`)**
- `setup_phoenix_instrumentation()` - Auto-called on import
- Configures OpenTelemetry OTLP exporter
- Instruments LangChain with `skip_dep_check=True`

**6. Session Utils (`session_utils.py`)**
- Checkpoint database utilities
- `get_session_history()`, `list_active_sessions()`, `clear_session()`, etc.

---

## Key Concepts

### Session Identifier (Thread ID)

Sessions are identified by a single **Thread ID**:
- Format: `merchant_{merchant_id}_{YYYYMMDD_HHMMSS}`
- Example: `merchant_mch_789456_20251109_121606`
- Purpose:
  - LangGraph conversation memory (checkpoints.db)
  - Phoenix tracing and observability
  - Session management and analytics
- Used in:
  - `agent.invoke(messages, config={"thread_id": thread_id})`
  - Phoenix span attribute: `session.thread_id`

### Session State Structure

```python
SessionState = {
    # LangGraph messages
    "messages": List[BaseMessage],

    # Session metadata (uses thread_id as identifier)
    "advisor_id": "adv_001",
    "started_at": "2025-01-09T14:30:22.123456+00:00",  # ISO 8601 UTC
    "last_activity_at": "2025-01-09T14:35:45.789012+00:00",

    # Merchant context (ONE merchant per session)
    "merchant_id": "mch_789456",  # Always normalized with mch_ prefix
    "merchant_name": "TechRetail",
    "segment": "mid_market",  # small_business | mid_market | enterprise

    # Session metrics
    "total_queries": 5,

    # Smart caching (TTL-based)
    "cached_data": {"profile": {...}, "metrics": {...}},
    "cached_at": {"profile": "2025-01-09T14:30:00Z", ...},

    # Conversation tracking
    "topics_discussed": ["decline_rates", "transaction_volume"],
    "recommendations": [
        {
            "type": "decline_optimization",
            "priority": "high",
            "description": "Review fraud filter settings",
            "expected_impact": "Reduce false positives by 15-20%",
            "created_at": "2025-01-09T14:32:00Z"
        }
    ],
    "pending_questions": ["What is the refund rate?"],
    "advisor_notes": [
        {"note": "...", "timestamp": "2025-01-09T14:35:00Z"}
    ],

    # Working data (scratch space)
    "working_data": {}
}
```

### Cache TTL Configuration

```python
DEFAULT_CACHE_CONFIG = {
    "profile_ttl_seconds": 1800,      # 30 minutes
    "metrics_ttl_seconds": 300,       # 5 minutes
    "transactions_ttl_seconds": 60,   # 1 minute
    "alerts_ttl_seconds": 30,         # 30 seconds
}
```

### Phoenix Tracing

**What Gets Traced on `merchant_query` Spans:**

1. **Session Metadata** (attributes):
   - session.thread_id, session.advisor_id
   - merchant.id, merchant.name, merchant.segment
   - session.query_number

2. **Message Content** (attributes):
   - input.value (user query)
   - output.value (AI response)
   - input.mime_type, output.mime_type

3. **Session Snapshots** (events):
   - session_snapshot_before (before query execution)
   - session_snapshot_after (after query execution)
   - Contains: total_queries, duration, topics, recommendations, cache state

4. **Cache Lookups** (separate `cache_lookup` spans):
   - cache.data_type, cache.hit (true/false)
   - cache.miss_reason ("not_found" or "expired")
   - cache.age_seconds, cache.ttl_seconds

---

## Important Implementation Details

### 1. SqliteSaver Usage

**WRONG** ❌:
```python
checkpointer = SqliteSaver.from_conn_string("sqlite:///db.db")
# Returns context manager, not checkpointer!
```

**CORRECT** ✅:
```python
conn = sqlite3.connect(db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn)
```

### 2. LangGraph ReAct Agent

Using LangGraph's prebuilt `create_react_agent`:
```python
from langgraph.prebuilt import create_react_agent

# Create agent with LLM, tools, and optional checkpointer
agent = create_react_agent(llm, tools, checkpointer=checkpointer)
```

The agent is a compiled LangGraph graph that works with the same invoke interface.

### 3. Merchant ID Normalization

Always normalize to `mch_` prefix:
```python
if not merchant_id.startswith("mch_"):
    merchant_id = f"mch_{merchant_id}"
```

### 4. Timestamps

Always use ISO 8601 UTC:
```python
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).isoformat()
```

### 5. Functional State Updates

All session manager functions return updated state (immutable pattern):
```python
updated_state = add_topic(state, "decline_rates")
updated_state = add_recommendation(updated_state, ...)
```

### 6. Phoenix Instrumentation

LangChain instrumentation happens automatically on import:
```python
# In instrumentation.py - runs when module loads
setup_phoenix_instrumentation()
```

To disable:
```bash
PHOENIX_ENABLED=false
```

---

## Known Issues

### ✅ Resolved: Phoenix Message Visibility

**Previous Issue**: Messages showed as "undefined" in Phoenix Sessions view when filtering by `session.id = "ses_..."`

**Resolution**: Simplified architecture to use only `thread_id` as session identifier. The dual-ID system (ses_ + merchant_) has been removed.

**Current State**:
- Sessions identified by `thread_id` only (format: `merchant_{merchant_id}_{timestamp}`)
- Phoenix filtering works correctly: `session.thread_id = "merchant_..."`
- Message attributes (input.value, output.value) display correctly
- All Layer 1 features retained (topics, recommendations, caching, notes)

---

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Checkpointing (optional)
ENABLE_CHECKPOINTING=true           # default: false
CHECKPOINT_DB_PATH=checkpoints.db   # default: checkpoints.db

# Phoenix (optional)
PHOENIX_ENABLED=true                       # default: true
PHOENIX_ENDPOINT=http://localhost:4317    # default: http://localhost:4317
```

---

## Running the Project

### Setup
```bash
# Clone and enter directory
cd openai-langchain-deepagent

# Create .env file
cp .env.example .env
# Edit .env and add OPENAI_API_KEY

# Install dependencies
uv sync

# Install dev dependencies (pytest, ruff)
uv sync --extra dev

# Start Phoenix
docker compose up -d
```

### Run Examples
```bash
# Basic agent
uv run python examples/basic_agent.py

# Checkpointing demo
uv run python examples/conversation_with_memory.py

# Layer 1 session memory demo
uv run python examples/single_merchant_session_demo.py

# Phoenix tracing demo (4 queries)
uv run python examples/session_with_phoenix_tracing.py
```

### Run Tests
```bash
# All tests
uv run pytest -v

# Specific test file
uv run pytest tests/test_session_memory.py -v

# Specific test
uv run pytest tests/test_session_memory.py::TestSessionManager::test_cache_expiration -v
```

### View Phoenix
```bash
# Open Phoenix UI
open http://localhost:6006

# Filter by thread ID (session identifier)
session.thread_id = "merchant_mch_789456_20251109_143022"

# Or filter by merchant ID
merchant.id = "mch_789456"

# Or filter by advisor ID
session.advisor_id = "adv_001"
```

---

## Code Patterns

### Starting a Session
```python
from openai_langchain_deepagent.agent import start_merchant_session

agent, thread_id, state = start_merchant_session(
    advisor_id="adv_001",
    merchant_id="789456",  # Auto-normalized to mch_789456
    merchant_name="TechRetail",
    segment="mid_market"
)
```

### Running Queries
```python
from openai_langchain_deepagent.agent import run_query_in_session

response, state = run_query_in_session(
    agent=agent,
    thread_id=thread_id,
    session_state=state,
    query="What is the decline rate?"
)
```

### Managing Session State
```python
from openai_langchain_deepagent.session_manager import (
    add_topic, add_recommendation, cache_data, get_cached_data
)

# Add topic
state = add_topic(state, "decline_rates")

# Cache data
state = cache_data(state, "profile", {"name": "TechRetail"})

# Retrieve cached data
profile = get_cached_data(state, "profile")  # Returns data or None if expired

# Add recommendation
state = add_recommendation(
    state=state,
    recommendation_type="optimization",
    priority="high",
    description="Review settings",
    expected_impact="15% improvement"
)
```

### Inspecting Sessions
```python
from openai_langchain_deepagent.session_inspector import (
    print_session_state, export_session_summary
)

# Print to console
print_session_state(state, detailed=True)

# Export to JSON
summary = export_session_summary(state)
import json
print(json.dumps(summary, indent=2))
```

---

## Testing Patterns

### Mocking Checkpointing
```python
from unittest.mock import MagicMock, patch

@patch("sqlite3.connect")
@patch("openai_langchain_deepagent.agent.SqliteSaver")
def test_checkpointing(mock_saver, mock_connect):
    mock_connect.return_value = MagicMock()
    mock_saver.return_value = MagicMock()

    agent = create_agent(enable_checkpointing=True)
    # Test...
```

### Testing Cache Expiration
```python
import time

state = cache_data(state, "test", {"data": "value"})

# Immediate retrieval - should hit
data = get_cached_data(state, "test", {"test_ttl_seconds": 1})
assert data is not None

# Wait for expiration
time.sleep(1.1)

# Should miss (expired)
data = get_cached_data(state, "test", {"test_ttl_seconds": 1})
assert data is None
```

---

## Directory Structure

```
.
├── src/openai_langchain_deepagent/
│   ├── agent.py                 # Core agent + session functions
│   ├── instrumentation.py       # Phoenix auto-setup
│   ├── session_manager.py       # Layer 1 core (11 functions)
│   ├── session_inspector.py     # Inspection utilities
│   ├── session_utils.py         # Checkpoint utilities
│   ├── state.py                 # TypedDict definitions
│   └── main.py                  # Entry point
│
├── examples/
│   ├── basic_agent.py
│   ├── conversation_with_memory.py
│   ├── single_merchant_session_demo.py
│   ├── session_with_phoenix_tracing.py
│   ├── phoenix_message_troubleshooting.py
│   ├── phoenix_session_id_guide.md
│   └── debug_phoenix_attributes.py
│
├── tests/
│   ├── test_agent.py
│   ├── test_checkpointing.py
│   └── test_session_memory.py
│
├── .env.example
├── .gitignore
├── docker-compose.yml           # Phoenix service
├── pyproject.toml
└── README.md
```

---

## Git Branch

- **Active Branch**: `claude/create-uv-python-sta-011CUvfQSdayosdQZsBpvUpL`
- **Main Branch**: `main`
- Always develop and push to the claude/* branch

---

## Tips for Future Sessions

1. **Single Session Identifier**: Sessions use only `thread_id` (format: `merchant_{merchant_id}_{timestamp}`). The dual-ID system has been removed for simplicity.

2. **Always Pull First**: User may have made changes locally
   ```bash
   git pull origin claude/create-uv-python-sta-011CUvfQSdayosdQZsBpvUpL
   ```

3. **Test After Changes**: Run test suite to ensure nothing broke
   ```bash
   uv run pytest -v
   ```

4. **Phoenix Must Be Running**: For tracing demos to work
   ```bash
   docker compose up -d
   ```

5. **Session State is Immutable**: Always return new state from functions, don't modify in place

6. **Check .env Setup**: User needs OPENAI_API_KEY set for examples to work

---

## Recent Changes to Be Aware Of

- **Session 9 (Current)**: Migrated to standard LangChain Agents
  - Replaced `deepagents` with `langchain` and `langgraph`
  - Now using `create_react_agent` from LangGraph's prebuilt
  - Added tools support (default: Calculator)
  - All session memory features intact
  - Same invoke interface and checkpointing
- **Session 8**: Removed dual-ID system (ses_ session ID)
  - Now using only `thread_id` as session identifier
  - Session state TypedDict no longer has `session_id` field
  - Phoenix tracing uses `session.thread_id` instead of `session.id`

---

## Contact & Resources

- [LangChain Agents Docs](https://docs.langchain.com/oss/python/langchain/agents)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Phoenix Documentation](https://docs.arize.com/phoenix)
- [OpenInference Semantic Conventions](https://github.com/Arize-ai/openinference)

---

**Last Updated**: 2025-01-09 (Session 9: Migration to standard LangChain Agents)
**Status**: Production-ready
