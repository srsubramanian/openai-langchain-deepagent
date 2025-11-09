"""Example demonstrating conversation memory with checkpointing."""

import uuid

from openai_langchain_deepagent.agent import create_agent
from openai_langchain_deepagent.session_utils import (
    get_session_info,
    list_active_sessions,
)


def main():
    """Run a multi-turn conversation demonstrating memory."""
    print("=" * 70)
    print("Conversation with Memory - LangChain Agent Checkpointing Demo")
    print("=" * 70)

    # Create agent with checkpointing enabled
    agent = create_agent(enable_checkpointing=True)

    # Generate a unique thread ID for this conversation
    thread_id = f"conversation-{uuid.uuid4().hex[:8]}"
    print(f"\n🔑 Session ID: {thread_id}")
    print("=" * 70)

    # Configuration for this thread/session
    config = {"configurable": {"thread_id": thread_id}}

    # Multi-turn conversation demonstrating memory
    conversation = [
        "I'm planning a trip to Paris next month.",
        "What should I pack?",
        "Where was I planning to go again?",  # Tests memory
    ]

    print("\n📝 Starting conversation...\n")

    for i, query in enumerate(conversation, 1):
        print(f"User (Turn {i}): {query}")

        # Invoke agent with thread configuration
        result = agent.invoke(
            {"messages": [{"role": "user", "content": query}]}, config=config
        )

        # Extract response
        response = result.get("messages", [])[-1].content if result.get("messages") else str(result)

        print(f"Agent: {response}")
        print("-" * 70)

    # Display session information
    print("\n📊 Session Information:")
    print("=" * 70)

    session_info = get_session_info(thread_id)
    if session_info:
        print(f"Thread ID: {session_info['thread_id']}")
        print(f"Total Checkpoints: {session_info['checkpoint_count']}")
        print(f"First Checkpoint ID: {session_info['first_checkpoint']}")
        print(f"Last Checkpoint ID: {session_info['last_checkpoint']}")
    else:
        print("No session info found")

    # List all active sessions
    print("\n🗂️  All Active Sessions:")
    print("=" * 70)
    sessions = list_active_sessions()
    for session in sessions:
        info = get_session_info(session)
        print(f"  • {session} ({info['checkpoint_count'] if info else 0} checkpoints)")

    print("\n✅ Demo complete!")
    print(f"Session data persisted in checkpoints.db under thread_id: {thread_id}")
    print("\nTo continue this conversation later, use the same thread_id:")
    print(f'  config = {{"configurable": {{"thread_id": "{thread_id}"}}}}')


if __name__ == "__main__":
    main()
