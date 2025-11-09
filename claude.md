# Claude Development Log

This document tracks changes and improvements made by Claude to the openai-langchain-deepagent project.

## 2025-01-09: Fix Checkpointer Configuration Error

### Issue
The `run_agent_task()` function was failing with a configuration error when checkpointing was enabled via the `ENABLE_CHECKPOINTING` environment variable:

```
ValueError: Checkpointer requires one or more of the following 'configurable' keys: thread_id, checkpoint_ns, checkpoint_id
```

### Root Cause
The `run_agent_task()` function was:
1. Creating an agent that inherited the `ENABLE_CHECKPOINTING` environment variable setting
2. Invoking the agent without providing a required `thread_id` in the config parameter
3. LangGraph checkpointing requires a `thread_id` to maintain conversation state

### Solution
Modified `run_agent_task()` in `src/openai_langchain_deepagent/agent.py:101` to explicitly disable checkpointing:

```python
# Explicitly disable checkpointing for this simple API
# Users wanting session memory should use start_merchant_session()
agent = create_agent(model=model, enable_checkpointing=False)
```

### Rationale
This design decision makes sense because:

1. **`run_agent_task()` is a simple, stateless API** designed for one-off tasks
2. **No thread ID management** - The function doesn't manage thread IDs or session state
3. **Clear separation of concerns** - Users who need session memory should use the proper session-based API:
   - `start_merchant_session()` - Initialize a session with proper thread ID
   - `run_query_in_session()` - Run queries with memory and session state

### Changes Made
- Updated `run_agent_task()` to explicitly pass `enable_checkpointing=False` to `create_agent()`
- Enhanced the docstring to clarify that it's for stateless, one-off tasks
- Added inline comments explaining the design decision and pointing users to session-based APIs for memory

### Files Modified
- `src/openai_langchain_deepagent/agent.py`

### Testing
Verified the fix by running:
```bash
uv run python examples/basic_agent.py
```

The checkpointer configuration error no longer occurs. The function now correctly creates a stateless agent that doesn't require thread ID configuration.

### Additional Work
Added `uv.lock` to the repository for reproducible package installations across environments.

### Commits
1. `0eb33ae` - Fix checkpointer configuration error in run_agent_task
2. `878a3a2` - Add uv.lock for reproducible package installations

### Related Documentation
For users who need conversation memory and session management, refer to:
- README.md sections:
  - "Conversation Memory (Checkpointing)"
  - "Layer 1 Session Memory (Single-Merchant Conversations)"
- Examples:
  - `examples/conversation_with_memory.py`
  - `examples/single_merchant_session_demo.py`

---

## 2025-01-09: Document and Enhance TodoListMiddleware Support

### Context
User requested documentation about TodoListMiddleware referenced at https://docs.langchain.com/oss/python/langchain/middleware#to-do-list

### Discovery
Through research and inspection of the `deepagents` library, discovered that **TodoListMiddleware is already automatically included** when using `create_deep_agent()`. The project was already using this middleware without explicitly documenting it.

### What is TodoListMiddleware?
TodoListMiddleware is one of three middleware components automatically attached to deep agents:

1. **TodoListMiddleware**: Provides `write_todos` tool for task planning
   - Helps agents break down complex tasks into manageable steps
   - Manages tasks with three states: `pending`, `in_progress`, `completed`
   - Automatically used by the agent when tackling multi-step tasks

2. **FilesystemMiddleware**: File operations for context management
   - Tools: `write_file`, `read_file`, `edit_file`, `ls`, `glob_search`, `grep_search`
   - Enables agents to work with files for reading code, writing reports, etc.

3. **SubAgentMiddleware**: Spawning specialized sub-agents
   - Tool: `call_subagent`
   - Allows agents to delegate tasks to specialized sub-agents

### Changes Made

#### 1. Documentation Updates
- Enhanced `create_agent()` docstring to document all three middleware components
- Added inline comment noting that middleware is automatically included
- Updated README with comprehensive "Built-in Middleware" section
- Documented each middleware's purpose, tools, and use cases

#### 2. New Functionality
Created `create_agent_with_custom_middleware()` function for advanced use cases:
```python
def create_agent_with_custom_middleware(
    model: Optional[str] = None,
    temperature: float = 0.7,
    middleware: Optional[list] = None,
    system_prompt: Optional[str] = None,
    enable_checkpointing: Optional[bool] = None,
    checkpoint_db_path: Optional[str] = None,
) -> Any:
```

This allows users to add custom middleware while retaining all default middleware functionality.

#### 3. Example Code
Created `examples/todo_middleware_demo.py` to demonstrate:
- That `write_todos` tool is automatically available
- How the agent uses the tool for complex, multi-step tasks
- How to inspect available tools in a deep agent

#### 4. Package Exports
Updated `src/openai_langchain_deepagent/__init__.py` to export:
- `create_agent`
- `create_agent_with_custom_middleware` (new)
- `create_agent_with_session_memory`
- `run_agent_task`
- `run_query_in_session`
- `start_merchant_session`

### Files Modified
- `src/openai_langchain_deepagent/agent.py`
  - Updated docstrings
  - Added `create_agent_with_custom_middleware()` function
- `src/openai_langchain_deepagent/__init__.py`
  - Added exports for public API
- `README.md`
  - Added "Built-in Middleware" section
  - Updated "Features" section to highlight middleware
- `examples/todo_middleware_demo.py` (new)
  - Demo of TodoListMiddleware in action

### Key Insights

1. **Already Enabled**: The project was already using TodoListMiddleware through `create_deep_agent()` but it wasn't documented
2. **Automatic Behavior**: Agents automatically use `write_todos` when appropriate for complex tasks
3. **Three Middleware Types**: TodoList, Filesystem, and SubAgent middleware all work together
4. **Extensible**: Users can add custom middleware without losing default functionality

### Testing
Can be tested with:
```bash
uv run python examples/todo_middleware_demo.py
```

### Commit
`acdaa25` - Add TodoListMiddleware documentation and custom middleware support

### Benefits
- Users now understand what middleware is included by default
- Clear documentation of available tools and their purposes
- Path for advanced users to add custom middleware
- Example code showing the feature in action
