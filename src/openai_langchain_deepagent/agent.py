"""DeepAgent implementation using LangChain DeepAgents library with OpenAI."""

import os
import sqlite3
from typing import Any, Optional

from deepagents import create_deep_agent
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver

from .instrumentation import setup_phoenix_instrumentation

# Load environment variables
load_dotenv()

# Set up Phoenix instrumentation for observability
setup_phoenix_instrumentation()


def create_agent(
    model: Optional[str] = None,
    temperature: float = 0.7,
    enable_checkpointing: Optional[bool] = None,
    checkpoint_db_path: Optional[str] = None,
) -> Any:
    """
    Create a DeepAgent with OpenAI.

    Args:
        model: Specific model name. If None, uses default: gpt-4o
        temperature: Temperature for the model (0.0-1.0)
        enable_checkpointing: Enable conversation memory via checkpointing.
                            If None, reads from ENABLE_CHECKPOINTING env var (default: False)
        checkpoint_db_path: Path to SQLite checkpoint database.
                           If None, reads from CHECKPOINT_DB_PATH env var (default: checkpoints.db)

    Returns:
        Configured deep agent instance

    Raises:
        ValueError: If OPENAI_API_KEY is missing
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in your .env file or environment."
        )

    llm = ChatOpenAI(
        model=model or "gpt-4o",
        temperature=temperature,
        api_key=api_key,
    )

    # Determine if checkpointing should be enabled
    if enable_checkpointing is None:
        enable_checkpointing = os.getenv("ENABLE_CHECKPOINTING", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    # Create checkpointer if enabled
    checkpointer = None
    if enable_checkpointing:
        db_path = checkpoint_db_path or os.getenv(
            "CHECKPOINT_DB_PATH", "checkpoints.db"
        )
        # Create SQLite connection with thread safety disabled for LangGraph
        conn = sqlite3.connect(db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        print(f"✓ Checkpointing enabled: {db_path}")

    # Create and return the deep agent
    return create_deep_agent(model=llm, checkpointer=checkpointer)


def run_agent_task(task: str, model: Optional[str] = None) -> dict:
    """
    Run a task with a DeepAgent using OpenAI.

    Args:
        task: The task description for the agent to execute
        model: Optional specific model to use (default: gpt-4o)

    Returns:
        Dictionary containing the agent's response and execution details

    Example:
        >>> result = run_agent_task("Write a hello world function in Python")
        >>> print(result['output'])
    """
    agent = create_agent(model=model)

    # Execute the task
    result = agent.invoke({"messages": [{"role": "user", "content": task}]})

    return result


def create_agent_with_session_memory(
    model: Optional[str] = None,
    temperature: float = 0.7,
    checkpoint_db_path: Optional[str] = None,
) -> Any:
    """
    Create a DeepAgent with session memory (checkpointing always enabled).

    This is a convenience function for Layer 1 session memory that ensures
    checkpointing is enabled.

    Args:
        model: Specific model name. If None, uses default: gpt-4o
        temperature: Temperature for the model (0.0-1.0)
        checkpoint_db_path: Path to SQLite checkpoint database.
                           If None, reads from CHECKPOINT_DB_PATH env var (default: checkpoints.db)

    Returns:
        Configured deep agent instance with checkpointing enabled

    Example:
        >>> agent = create_agent_with_session_memory()
        >>> # Agent is now ready for session-based conversations
    """
    return create_agent(
        model=model,
        temperature=temperature,
        enable_checkpointing=True,
        checkpoint_db_path=checkpoint_db_path,
    )


def start_merchant_session(
    advisor_id: str,
    merchant_id: str,
    merchant_name: Optional[str] = None,
    segment: Optional[str] = None,
    model: Optional[str] = None,
    checkpoint_db_path: Optional[str] = None,
):
    """
    Start a new single-merchant session with memory.

    Creates a new session state, initializes an agent with checkpointing,
    and returns everything needed to run queries.

    Args:
        advisor_id: ID of the advisor starting the session
        merchant_id: Merchant ID for this session
        merchant_name: Optional merchant name
        segment: Optional segment ("small_business", "mid_market", "enterprise")
        model: Optional specific model to use (default: gpt-4o)
        checkpoint_db_path: Optional checkpoint database path

    Returns:
        Tuple of (agent, thread_id, session_state)

    Example:
        >>> agent, thread_id, state = start_merchant_session(
        ...     advisor_id="adv_001",
        ...     merchant_id="mch_789456",
        ...     merchant_name="TechRetail",
        ...     segment="mid_market"
        ... )
        >>> # Now ready to run queries with this session
    """
    from datetime import datetime, timezone

    from .session_manager import initialize_session_state

    # Initialize session state
    session_state = initialize_session_state(
        advisor_id=advisor_id,
        merchant_id=merchant_id,
        merchant_name=merchant_name,
        segment=segment,
    )

    # Create agent with session memory
    agent = create_agent_with_session_memory(
        model=model, checkpoint_db_path=checkpoint_db_path
    )

    # Generate thread_id: merchant_{merchant_id}_{YYYYMMDD_HHMMSS}
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    # Normalize merchant_id
    normalized_merchant_id = (
        merchant_id if merchant_id.startswith("mch_") else f"mch_{merchant_id}"
    )
    thread_id = f"merchant_{normalized_merchant_id}_{timestamp}"

    return agent, thread_id, session_state


def run_query_in_session(
    agent: Any,
    thread_id: str,
    session_state,
    query: str,
):
    """
    Run a query within an existing merchant session.

    Executes the query, updates session state, and returns both response and updated state.

    Args:
        agent: The DeepAgent instance
        thread_id: Thread ID for this session
        session_state: Current session state
        query: User query to execute

    Returns:
        Tuple of (response_text, updated_session_state)

    Example:
        >>> response, state = run_query_in_session(
        ...     agent=agent,
        ...     thread_id=thread_id,
        ...     session_state=state,
        ...     query="What is the merchant's decline rate?"
        ... )
        >>> print(response)
    """
    from .session_manager import increment_query_count

    # Update query count and timestamp
    updated_state = increment_query_count(session_state)

    # Execute query with thread_id for memory
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [{"role": "user", "content": query}]}, config)

    # Extract response
    response_text = result["messages"][-1].content if result.get("messages") else ""

    return response_text, updated_state


if __name__ == "__main__":
    # Example usage
    example_task = "Create a simple Python function that adds two numbers"

    print(f"Running task: {example_task}\n")
    print("=" * 60)

    result = run_agent_task(example_task)

    print("\nAgent Response:")
    print("=" * 60)
    print(result.get("output", result))
